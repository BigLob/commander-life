"""Tests for the parser, filters, diff and scheduling. Run: python -m unittest test_monitor.py
No network and no Playwright needed: the fetch is faked."""
import datetime as dt
import json
import os
import unittest

import monitor as m

FIX = os.path.join(os.path.dirname(__file__), 'fixtures')
CFG = json.load(open(os.path.join(os.path.dirname(__file__), 'config.example.json')))
CFG['ntfy_topic'] = ''  # never push from tests


def page(name):
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


class Parse(unittest.TestCase):
    def test_products(self):
        ps = {p['sku']: p for p in m.parse_products(page('search.html'))}
        self.assertEqual(len(ps), 4)
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
        self.assertEqual(len(names), 3)
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
        fri = dt.datetime(2026, 11, 20, 10, 0)  # a Friday
        self.assertLess(m.next_wait(fri, 0), 400)
        self.assertGreaterEqual(m.next_wait(dt.datetime(2026, 11, 18, 10, 0), 0), 1800)
        before = dt.datetime(2026, 11, 20, 9, 40)
        self.assertLess(m.next_wait(before, 0), 400)  # wakes for the window
        self.assertGreaterEqual(m.next_wait(fri, 3), 7200)


if __name__ == '__main__':
    unittest.main()
