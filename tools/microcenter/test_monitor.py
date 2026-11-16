"""Tests for the parser, filters, diff and scheduling. Run: python -m unittest test_monitor.py
No network and no Playwright needed: the fetch is faked."""
import datetime as dt
import json
import os
import unittest

import monitor as m
import secretlair as sl

FIX = os.path.join(os.path.dirname(__file__), 'fixtures')
CFG = json.load(open(os.path.join(os.path.dirname(__file__), 'config.example.json')))
CFG['ntfy_topic'] = ''  # never push from tests


def page(name):
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


class Parse(unittest.TestCase):
    def test_products(self):
        ps = {p['sku']: p for p in m.parse_products(page('search.html'))}
        self.assertEqual(len(ps), 5)
        marvel = ps['050575']  # the real page's layout: an empty "stock" element before the count
        self.assertEqual((marvel['in_stock'], marvel['stock'], marvel['count']), (True, '16 in stock', 16))
        box = ps['123451']
        self.assertEqual(box['name'], 'Wizards of the Coast Magic: The Gathering Foundations Play Booster Box')
        self.assertEqual(box['price'], '139.99')
        self.assertTrue(box['in_stock'])
        self.assertEqual(box['count'], 8)
        self.assertTrue(box['url'].startswith('https://www.microcenter.com/product/690001/'))
        self.assertFalse(ps['123452']['in_stock'])
        self.assertEqual(ps['123452']['stock'], 'Sold out')
        sleeves = ps['123453']  # no data-* attributes: name and price from the text
        self.assertEqual(sleeves['name'], 'Ultra Pro Magic: The Gathering Sleeves 100ct')
        self.assertEqual(sleeves['price'], '11.99')
        self.assertEqual(sleeves['stock'], '25+ in stock')
        self.assertTrue(ps['123454']['in_stock'])

    def test_challenge(self):
        self.assertTrue(m.is_challenge(page('challenge.html')))
        self.assertFalse(m.is_challenge(page('search.html')))
        self.assertEqual(m.parse_products(page('challenge.html')), [])

    def test_stock_words(self):
        self.assertEqual(m.parse_stock('IN STOCK')[:2], (True, 'In stock'))
        self.assertFalse(m.parse_stock('Pre-Order')[0])
        self.assertFalse(m.parse_stock('Out of stock')[0])


class Filters(unittest.TestCase):
    def test_wanted(self):
        names = [p['name'] for p in m.parse_products(page('search.html')) if m.wanted(p, CFG)]
        self.assertNotIn('Ultra Pro Magic: The Gathering Sleeves 100ct', names)
        self.assertEqual(len(names), 4)
        self.assertFalse(m.wanted({'name': 'Pokemon Scarlet Booster'}, CFG))

    def test_legality(self):
        self.assertIn('not Commander-legal', m.legality_note('Magic Unfinity Draft Booster'))
        self.assertIn('not released', m.legality_note('MTG Lorwyn Pre-Order Bundle'))
        self.assertEqual(m.legality_note('MTG Foundations Play Booster Box'), '')

    def test_store_id(self):
        cfg = dict(CFG, store_id=155, watch_urls=['https://x/s?Ntt=a&storeid=131', 'https://x/s?Ntt=b',
                                                   'https://x/s?storeid={storeid}'])
        self.assertTrue(all('storeid=155' in u and 'storeid=131' not in u for u in m.watch_urls(cfg)))


class Diff(unittest.TestCase):
    def prods(self):
        return [p for p in m.parse_products(page('search.html')) if m.wanted(p, CFG)]

    def test_baseline_then_changes(self):
        st = {'products': {}, 'baselined': [], 'last_block_alert': 0}
        alerts, base = m.diff(st, 'u', self.prods())
        self.assertTrue(base)
        self.assertEqual(alerts, [])
        # Same page again: nothing new.
        self.assertEqual(m.diff(st, 'u', self.prods())[0], [])
        # The Borg deck comes back in stock, a new box appears, the booster box sells out.
        ps = self.prods()
        borg = next(p for p in ps if p['sku'] == '123452')
        borg.update(in_stock=True, stock='3 in stock')
        next(p for p in ps if p['sku'] == '123451').update(in_stock=False, stock='Sold out')
        ps.append(dict(ps[0], key='999', sku='999', name='MTG Avatar Collector Booster Box', in_stock=True))
        ps.append(dict(ps[0], key='998', sku='998', name='MTG Spider-Man Bundle', in_stock=False))
        kinds = {p['sku']: k for k, p in m.diff(st, 'u', ps)[0]}
        self.assertEqual(kinds, {'123452': 'restock', '999': 'new_in_stock', '998': 'new_listing'})
        # And it doesn't repeat on the next poll.
        self.assertEqual(m.diff(st, 'u', ps)[0], [])
        # Booster box back: one restock alert.
        ps[0].update(in_stock=True)
        self.assertEqual([k for k, _ in m.diff(st, 'u', ps)[0]], ['restock'])

    def test_new_url_baselines_alone(self):
        st = {'products': {}, 'baselined': [], 'last_block_alert': 0}
        m.diff(st, 'u1', self.prods()[:1])
        alerts, base = m.diff(st, 'u2', self.prods())
        self.assertTrue(base)
        self.assertEqual(alerts, [])

    def test_dedupe(self):
        p = self.prods()[0]
        self.assertEqual(len(m.dedupe([('restock', p), ('restock', p)])), 1)


class Rebaseline(unittest.TestCase):
    def test_unknown_never_alerts(self):
        st = {'products': {}, 'baselined': []}
        ps = [p for p in m.parse_products(page('search.html')) if m.wanted(p, CFG)]
        m.diff(st, 'u', [dict(p, in_stock=False, stock='Unknown') for p in ps])
        self.assertEqual(m.diff(st, 'u', ps)[0], [])

    def test_old_parser_state_rebaselines(self):
        st = {'products': {}, 'baselined': [u for u in m.watch_urls(CFG)], 'last_block_alert': 0}
        sent = Poll.run_poll(Poll(), [page('search.html')], st)
        self.assertTrue(sent and all('started' in t for t, _ in sent))
        self.assertEqual(st['parser'], m.PARSER_VERSION)


class Poll(unittest.TestCase):
    def run_poll(self, pages, st):
        sent = []
        orig = m.push
        m.push = lambda cfg, title, msg, **k: sent.append((title, msg))
        orig_save = m.save_state
        m.save_state = lambda s: None
        try:
            m.poll(CFG, st, fetch=lambda urls, cfg, debug: {u: pages[i % len(pages)] for i, u in enumerate(urls)})
        finally:
            m.push, m.save_state = orig, orig_save
        return sent

    def test_blocked_pushes_once_an_hour(self):
        st = {'products': {}, 'baselined': [], 'last_block_alert': 0}
        sent = self.run_poll([page('challenge.html')], st)
        self.assertEqual(len(sent), 1)
        self.assertIn('blocked', sent[0][0])
        self.assertEqual(self.run_poll([page('challenge.html')], st), [])
        self.assertEqual(st['blocked_streak'], 2)

    def test_first_run_says_baseline(self):
        st = {'products': {}, 'baselined': [], 'last_block_alert': 0}
        sent = self.run_poll([page('search.html')], st)
        self.assertTrue(all('started' in t for t, _ in sent))
        self.assertEqual(self.run_poll([page('search.html')], st), [])


class Schedule(unittest.TestCase):
    def test_waits(self):
        # Nov 19 2026 is a Thursday, Nov 20 a Friday.
        for t in [(19, 12, 0), (19, 23, 30), (20, 3, 0), (20, 10, 0), (20, 10, 59)]:
            self.assertLess(m.next_wait(dt.datetime(2026, 11, *t)), 400, t)
        for t in [(18, 10, 0), (20, 11, 0), (21, 15, 0), (16, 9, 0)]:
            self.assertGreaterEqual(m.next_wait(dt.datetime(2026, 11, *t)), 1800, t)
        self.assertLess(m.next_wait(dt.datetime(2026, 11, 19, 11, 50)), 700)  # wakes for the window

    def test_wakes_for_secret_lair_sale(self):
        now = dt.datetime(2026, 11, 16, 10, 50)  # Monday, outside the window
        self.assertLess(m.next_wait(now, wake_at=now.timestamp() + 600), 700)
        self.assertGreaterEqual(m.next_wait(now, wake_at=now.timestamp() + 86400), 1800)

    def test_backoff(self):
        self.assertEqual([m.backoff(n) for n in range(5)], [0, 1800, 3600, 7200, 7200])


def sl_getter(url):
    if url == sl.HOME:
        return page('secretlair-home.html')
    return page('secretlair-feed.json')


class SecretLair(unittest.TestCase):
    NOW = dt.datetime(2026, 11, 14, 21, 0, tzinfo=dt.timezone.utc)

    def test_feeds(self):
        self.assertEqual(sl.feed_ids(page('secretlair-home.html')), ['73866', '72135'])

    def test_status(self):
        st = {}
        ps, feeds = sl.fetch_products(st, now=self.NOW, getter=sl_getter)
        by = {p['id']: p for p in ps}
        self.assertEqual(feeds, ['73866', '72135'])
        self.assertEqual(by['1255840']['status'], 'on_sale')
        self.assertEqual(by['1255840']['name'], 'Secret Lair x Star Trek: Assimilation Foil Edition')
        self.assertEqual(by['1255840']['price'], '39.99')
        self.assertEqual(by['1255840']['url'], 'https://secretlair.wizards.com/us/product/1255840')
        self.assertEqual(by['1260001']['status'], 'coming')
        self.assertEqual(by['1260002']['status'], 'sold_out')
        self.assertEqual(by['1260002']['name'], 'Secret Lair: Sold Out Drop')  # <br> stripped
        self.assertEqual(by['1200000']['status'], 'ended')
        # 18:00 Paris on Nov 23 is 17:00 UTC.
        self.assertEqual(by['1260001']['start'], dt.datetime(2026, 11, 23, 17, 0, tzinfo=dt.timezone.utc).timestamp())

    def test_home_page_down_uses_last_feeds(self):
        st = {'sl': {'feeds': ['73866']}}
        def getter(url):
            if url == sl.HOME:
                raise OSError('queue')
            return page('secretlair-feed.json')
        ps, feeds = sl.fetch_products(st, now=self.NOW, getter=getter)
        self.assertEqual(feeds, ['73866'])
        self.assertEqual(len(ps), 4)

    def test_diff(self):
        st = {}
        ps, _ = sl.fetch_products(st, now=self.NOW, getter=sl_getter)
        alerts, base = sl.diff(st, ps)
        self.assertTrue(base)
        self.assertEqual(alerts, [])
        self.assertEqual(sl.next_start(st, self.NOW.timestamp()), ps[1]['start'])
        # A week later: the coming drop is on sale, the sold-out one restocked, a new one announced.
        later = dt.datetime(2026, 11, 23, 17, 5, tzinfo=dt.timezone.utc)
        ps, _ = sl.fetch_products(st, now=later, getter=sl_getter)
        next(p for p in ps if p['id'] == '1260002')['status'] = 'on_sale'
        new = dict(ps[0], key='sl-1270000', id='1270000', name='Secret Lair x New Thing', status='coming')
        kinds = {p['id']: k for k, p in sl.diff(st, ps + [new])[0]}
        self.assertEqual(kinds, {'1260001': 'on_sale', '1260002': 'on_sale', '1270000': 'announced'})
        self.assertEqual(sl.diff(st, ps + [new])[0], [])

    def test_poll_pushes(self):
        sent = []
        orig, orig_save = m.push, m.save_state
        m.push = lambda cfg, title, msg, **k: sent.append(title)
        m.save_state = lambda s: None
        try:
            st = {'sl': {'last_full': 9e12}}
            m.poll_secret_lair(CFG, st, getter=sl_getter)
            self.assertEqual(sent, ['Secret Lair monitor started'])
            st['sl']['products']['sl-1255840']['status'] = 'sold_out'  # restocked by next poll
            sent.clear()
            m.poll_secret_lair(CFG, st, getter=sl_getter)
        finally:
            m.push, m.save_state = orig, orig_save
        self.assertEqual(sent, ['Secret Lair on sale now'])

    def test_announce_text(self):
        p = {'name': 'Secret Lair x Unfinity Thing', 'price': '29.99', 'start': 1795453200.0,
             'url': 'u', 'status': 'coming'}
        title, msg = sl.alert_text('announced', p)
        self.assertEqual(title, 'Secret Lair announced')
        self.assertIn('On sale', msg)
        self.assertIn('not Commander-legal', m.legality_note(p['name']))


class Watchdog(unittest.TestCase):
    def test_due(self):
        d = dt.datetime
        # Thursday 13:00, in the window: 20 minutes.
        self.assertEqual(m.watchdog_due(d(2026, 11, 19, 13, 0)), (d(2026, 11, 19, 13, 20), True))
        # Friday 10:50: 20 minutes ahead is past 11 AM, so next week's window, more than 3 days off.
        due, win = m.watchdog_due(d(2026, 11, 20, 10, 50))
        self.assertFalse(win)
        self.assertEqual(due, d(2026, 11, 20, 10, 50) + dt.timedelta(seconds=m.NTFY_MAX_DELAY))
        # Tuesday 15:00: Thursday 12:20 is under 3 days away.
        self.assertEqual(m.watchdog_due(d(2026, 11, 17, 15, 0)), (d(2026, 11, 19, 12, 20), True))
        # Monday 9:00: Thursday is more than 3 days off.
        self.assertFalse(m.watchdog_due(d(2026, 11, 16, 9, 0))[1])
        # Thursday 11:50, before the window: 12:10.
        self.assertEqual(m.watchdog_due(d(2026, 11, 19, 11, 50)), (d(2026, 11, 19, 12, 10), True))

    def test_arm_sends_a_held_replaceable_message(self):
        sent = []
        orig = m.push
        m.push = lambda cfg, title, msg, **k: sent.append((title, k))
        try:
            m.arm_watchdog(CFG, now=dt.datetime(2026, 11, 19, 13, 0))
        finally:
            m.push = orig
        title, k = sent[0]
        self.assertEqual(k['sequence_id'], m.WATCHDOG_ID)
        base = int(dt.datetime(2026, 11, 19, 13, 20).timestamp())
        self.assertTrue(base <= int(k['delay']) <= base + 240)
        self.assertIn('checking', title)

    def test_sleep_wakes_early_after_pc_sleep(self):
        clock = [1000.0]
        orig_time, orig_sleep = m.time.time, m.time.sleep
        def fake_sleep(sec):
            clock[0] += sec + (3600 if clock[0] == 1000.0 else 0)  # the first nap spans an hour asleep
        m.time.time, m.time.sleep = (lambda: clock[0]), fake_sleep
        try:
            self.assertEqual(m.sleep_until(1000 + 1800), 'woke')
            clock[0] = 5000.0 + 1
            self.assertEqual(m.sleep_until(5000 + 100), 'due')
        finally:
            m.time.time, m.time.sleep = orig_time, orig_sleep


if __name__ == '__main__':
    unittest.main()
