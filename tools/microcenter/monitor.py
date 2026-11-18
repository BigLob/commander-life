#!/usr/bin/env python3
"""Micro Center MTG restock monitor, plus Secret Lair drops from Wizards' store (secretlair.py).
Runs on a home PC, pushes to a phone through ntfy.sh.

Why a home PC: microcenter.com sits behind a Cloudflare bot check that blocks cloud IPs.
A home connection in a real Chrome profile usually passes. We never try to beat the check:
if it shows, we back off and say so (one push per hour at most).

Usage:
  python monitor.py            loop forever (5 min Thursday noon to Friday 11 AM, 30-60 min otherwise)
  python monitor.py --once     one poll, then exit (for Task Scheduler)
  python monitor.py --test     send a test push and exit
  python monitor.py --debug    also save each page's HTML and a screenshot to debug/
"""
import argparse
import datetime as dt
import html
import json
import os
import random
import re
import secrets
import sys
import time
import urllib.request

import secretlair

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, 'config.json')
EXAMPLE = os.path.join(HERE, 'config.example.json')
STATE = os.path.join(HERE, 'state.json')
PROFILE = os.path.join(HERE, 'profile')
DEBUG_DIR = os.path.join(HERE, 'debug')

PARSER_VERSION = 2              # bump when parsing changes, so the next run re-baselines quietly
BLOCK_ALERT_EVERY = 3600       # seconds between "blocked by Cloudflare" pushes
CHALLENGE_MARKS = ('just a moment', 'cf-chl', 'challenge-platform', 'attention required',
                   'checking your browser', 'cf-turnstile')


# ---------- config and state ----------

def load_config(path=CONFIG):
    """config.json is local (gitignored). The first run copies the example and picks a random
    ntfy topic, since anyone who knows a topic name can read and send to it."""
    if not os.path.exists(path):
        with open(EXAMPLE, encoding='utf-8') as f:
            cfg = json.load(f)
        cfg['ntfy_topic'] = 'mc-mtg-' + secrets.token_hex(6)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
        print(f'Made {path} with ntfy topic {cfg["ntfy_topic"]}. Subscribe to it in the ntfy app.')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def watch_urls(cfg):
    """Watch URLs may hold {storeid}; every URL also gets storeid set, so a pasted link
    from another store can't silently watch the wrong one."""
    out = []
    for u in cfg['watch_urls']:
        u = u.replace('{storeid}', str(cfg['store_id']))
        if 'storeid=' in u:
            u = re.sub(r'storeid=\d*', f'storeid={cfg["store_id"]}', u)
        else:
            u += ('&' if '?' in u else '?') + f'storeid={cfg["store_id"]}'
        out.append(u)
    return out


def load_state(path=STATE):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return {'products': {}, 'baselined': [], 'last_block_alert': 0, 'blocked_streak': 0}


def save_state(state, path=STATE):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


# ---------- parsing ----------

def is_challenge(page_html):
    head = page_html[:20000].lower()
    if 'product_wrapper' in head:
        return False
    return any(m in head for m in CHALLENGE_MARKS)


def _text(s):
    s = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', s, flags=re.S | re.I)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


def _attr(block, name):
    m = re.search(rf'{name}\s*=\s*"([^"]*)"', block, re.I) or re.search(rf"{name}\s*=\s*'([^']*)'", block, re.I)
    return html.unescape(m.group(1)).strip() if m else ''


def parse_stock(text):
    """Returns (in_stock, label, count). Micro Center prints things like '8 NEW IN STOCK',
    '25+ NEW IN STOCK', 'SOLD OUT', 'LIMITED AVAILABILITY' or 'IN STOCK'."""
    t = text.upper()
    if 'SOLD OUT' in t or 'OUT OF STOCK' in t or 'NOT AVAILABLE' in t:
        return False, 'Sold out', 0
    m = re.search(r'(\d+)\+?\s*(?:NEW\s+|OPEN BOX\s+)?IN STOCK', t)
    if m:
        plus = '+' if re.search(r'\d+\+', t) else ''
        return True, f'{m.group(1)}{plus} in stock', int(m.group(1))
    if 'LIMITED AVAILABILITY' in t:
        return True, 'Limited availability', None
    if 'IN STOCK' in t:
        return True, 'In stock', None
    if 'PRE-ORDER' in t or 'PREORDER' in t or 'COMING SOON' in t:
        return False, 'Pre-order / coming soon', 0
    return False, 'Unknown', None


def parse_products(page_html, base='https://www.microcenter.com'):
    """One dict per product on a Micro Center search or category page. Each result is an
    <li class="product_wrapper">; we read its data-* attributes first (the most stable part
    of the markup) and fall back to the visible text."""
    starts = [m.start() for m in re.finditer(r'<li[^>]*class="[^"]*product_wrapper', page_html, re.I)]
    out = []
    for i, s in enumerate(starts):
        block = page_html[s:starts[i + 1] if i + 1 < len(starts) else len(page_html)]
        text = _text(block)
        name = _attr(block, 'data-name')
        href = ''
        m = re.search(r'href="(/product/[^"]+)"', block)
        if m:
            href = base + html.unescape(m.group(1))
            if not name:
                a = re.search(r'<a[^>]*href="/product/[^"]+"[^>]*>(.*?)</a>', block, re.S)
                name = _text(a.group(1)) if a else ''
        m = re.search(r'SKU:?\s*(\d{4,})', text, re.I)
        sku = m.group(1) if m else _attr(block, 'data-id')
        price = _attr(block, 'data-price')
        if not price:
            # The real page shows "Original price $159.99 Save $90.00 Our price $ 69.99".
            m = re.search(r'Our price\s*\$\s?([\d,]+\.\d\d)', text) or re.search(r'\$\s?([\d,]+\.\d\d)', text)
            price = m.group(1).replace(',', '') if m else ''
        stock_html = re.search(r'class="[^"]*(?:stock|inventory)[^"]*"[^>]*>(.*?)</(?:div|span|p)>', block, re.S | re.I)
        in_stock, label, count = parse_stock(_text(stock_html.group(1)) if stock_html else text)
        if label == 'Unknown':
            # The real page (Nov 16, 2026) has other elements whose class says "stock", and the
            # wording sits in the result's text: "16 IN STOCK at Dallas Store - Buy In Store".
            in_stock, label, count = parse_stock(text)
        if not name:
            continue
        # "16 IN STOCK at Dallas Store", "SOLD OUT at Dallas Store": which store the stock is for.
        m = re.search(r'(?:IN STOCK|SOLD OUT|LIMITED AVAILABILITY|OUT OF STOCK)\s+at\s+(.+?)\s+Store\b', text, re.I)
        where = m.group(1).strip() if m else ''
        # "Original price $159.99 Save $90.00 Our price $ 69.99": the store's own markdown.
        m = re.search(r'Original price\s*\$\s?([\d,]+\.\d\d)', text, re.I)
        orig = m.group(1).replace(',', '') if m else ''
        out.append({'key': sku or href or name, 'name': name, 'sku': sku, 'price': price,
                    'url': href, 'in_stock': in_stock, 'stock': label, 'count': count,
                    'where': where, 'orig': orig})
    return out


def store_city(cfg):
    """'Micro Center Dallas' -> 'dallas', the word the page uses in 'IN STOCK at Dallas Store'."""
    return (cfg.get('store_city') or cfg.get('store_name', '').replace('Micro Center', '')).strip().lower()


def at_my_store(p, cfg):
    """Only stock at the user's store counts (Dallas, the only store they care about). The
    search page is already set to that store, but if a result ever names another store's
    stock, read it as not in stock here."""
    city = store_city(cfg)
    if p['in_stock'] and p.get('where') and city and city not in p['where'].lower():
        return dict(p, in_stock=False, stock=f'{p["stock"]} at {p["where"]}, not {city.title()}')
    return p


# ---------- filters and notes ----------

def wanted(p, cfg):
    name = p['name'].lower()
    inc = [k.lower() for k in cfg.get('include', [])]
    exc = [k.lower() for k in cfg.get('exclude', [])]
    if inc and not any(k in name for k in inc):
        return False
    return not any(k in name for k in exc)


UN_SETS = ('unfinity', 'unstable', 'unglued', 'unhinged', 'unsanctioned', 'unknown event', 'playtest')


def legality_note(name):
    """CLAUDE.md: call out anything that isn't Commander-legal. Sealed product is almost
    always fine; Un-sets and playtest cards aren't, and unreleased product isn't out yet."""
    n = name.lower()
    if any(u in n for u in UN_SETS):
        return 'Heads up: Un-set / playtest product, mostly not Commander-legal.'
    if 'pre-order' in n or 'preorder' in n or 'pre order' in n:
        return 'Pre-order: not released yet, so not Commander-legal until it is out.'
    return ''


# ---------- diff ----------

def price_num(s):
    try:
        return float(str(s).replace(',', '').replace('$', '').strip())
    except (TypeError, ValueError):
        return None


def price_drop(old, p):
    """The old price when this one is lower (only drops, never rises: the user's ask), else None."""
    was, now = price_num((old or {}).get('price')), price_num(p.get('price'))
    return was if was and now and now < was - 0.005 else None


def diff(state, url, products, now=None):
    """Merges this page's products into the state and returns the alerts. A URL seen for the
    first time only records a baseline, so starting the monitor (or adding a URL) never pushes
    a flood. Products missing from a page are left alone: pages paginate and reorder.
    Only products in stock at the store alert (the user's rule, Nov 18, 2026: a price drop on
    something sold out at Dallas, or a new listing that isn't in stock, is noise). Their price
    is still recorded, so a later restock at the lower price says what it was."""
    now = now or dt.datetime.now().isoformat(timespec='seconds')
    known = state['products']
    baseline = url not in state['baselined']
    alerts = []
    for p in products:
        old = known.get(p['key'])
        rec = dict(p, last_seen=now, first_seen=old['first_seen'] if old else now)
        if old and not p['in_stock'] and price_drop(old, p):
            # Sold out and cheaper: no push now, but keep the higher price to quote on restock.
            rec['was'] = max(old.get('was') or 0, price_num(old['price']))
        elif old and not p['in_stock'] and old.get('was'):
            rec['was'] = old['was']
        if not baseline and p['in_stock']:
            if old is None:
                alerts.append(('new_in_stock', p))
            else:
                was = price_drop(old, p) or (old.get('was') if not old.get('in_stock') else None)
                if was and price_num(p['price']) and price_num(p['price']) < was - 0.005:
                    p = dict(p, was=was)  # a restock at a lower price says so in one line
                if not old.get('in_stock') and old.get('stock') != 'Unknown':
                    alerts.append(('restock', p))
                elif p.get('was'):
                    alerts.append(('price_drop', p))
        known[p['key']] = rec
    if baseline:
        state['baselined'].append(url)
    return alerts, baseline


def dedupe(alerts):
    seen, out = set(), []
    for kind, p in alerts:
        if p['key'] not in seen:
            seen.add(p['key'])
            out.append((kind, p))
    return out


# ---------- notifications ----------

def push(cfg, title, message, click=None, priority=3, tags=None, delay=None, sequence_id=None, quiet=False,
         actions=None):
    if not quiet:
        print(f'[{dt.datetime.now():%a %H:%M}] {title}: {message}')
    topic = cfg.get('ntfy_topic')
    if not topic:
        return
    body = {'topic': topic, 'title': title, 'message': message, 'priority': priority}
    if actions:
        body['actions'] = actions          # buttons under the notification (ntfy allows 3)
    if delay:
        body['delay'] = delay            # ntfy holds it and delivers it then (10 s to 3 days)
    if sequence_id:
        body['sequence_id'] = sequence_id  # a later message with the same id replaces a held one
    if click:
        body['click'] = click
    if tags:
        body['tags'] = tags
    req = urllib.request.Request(cfg.get('ntfy_server', 'https://ntfy.sh').rstrip('/') + '/',
                                 data=json.dumps(body).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:  # a failed push must never stop the monitor
        print(f'  ntfy push failed: {e}')


def alert_text(kind, p, cfg):
    head = {'restock': 'Back in stock', 'new_in_stock': 'New and in stock', 'price_drop': 'Price drop'}[kind]
    price = f'${p["price"]}' if p['price'] else 'no price'
    if p.get('was'):
        price += f' (was ${p["was"]:.2f}, {p["was"] - price_num(p["price"]):.2f} off)'
    lines = [p['name'], f'{price} · {p["stock"]} · {cfg.get("store_name", "store " + str(cfg["store_id"]))}']
    note = legality_note(p['name'])
    if note:
        lines.append(note)
    return f'MTG: {head}', '\n'.join(lines)


# ---------- one summary push per check ----------
# The user found one push per product hard to read (eight "Price drop" pushes in one minute on
# Nov 18, 2026), so each check gathers its alerts and sends one push listing them by section.

SECTIONS = [  # key, heading in the push, words in the title (one, many)
    ('stock', 'In stock at {store}', ('in stock', 'in stock')),
    ('drop', 'Price drops at {store}', ('price drop', 'price drops')),
    ('sl_sale', 'Secret Lair on sale now', ('Secret Lair on sale', 'Secret Lair on sale')),
    ('sl_coming', 'Secret Lair coming soon', ('Secret Lair announced', 'Secret Lair announced')),
    ('sl_drop', 'Secret Lair price drops', ('Secret Lair price drop', 'Secret Lair price drops')),
]
MAX_BYTES = 3800        # ntfy cuts a message at 4,096 bytes


def short_name(name):
    """'Wizards of the Coast Magic: The Gathering - TMNT (Commander Deck)' -> 'TMNT (Commander Deck)'."""
    n = re.sub(r'^(?:Wizards of the Coast\s+)?(?:Magic:? The Gathering|MTG)\s*[-:–]?\s*', '', name.strip(), flags=re.I)
    return n or name


def _money(x):
    return f'${price_num(x):.2f}' if price_num(x) else 'no price'


def mc_item(kind, p):
    """One Micro Center alert as (section, line, url, priority)."""
    bits = [_money(p['price'])]
    if p.get('was'):
        bits[0] += f' (was ${p["was"]:.2f})'
    elif price_num(p.get('orig')) and price_num(p['price']) and price_num(p['orig']) > price_num(p['price']):
        bits[0] += f' (list ${price_num(p["orig"]):.2f})'
    bits.append(p['stock'].lower() if p['stock'][0].isdigit() else p['stock'])
    if kind == 'restock':
        bits.append('back')
    elif kind == 'new_in_stock':
        bits.append('new')
    note = legality_note(p['name'])
    line = f'• {short_name(p["name"])}: ' + ', '.join(bits) + (f'\n  {note}' if note else '')
    return ('drop' if kind == 'price_drop' else 'stock', line, p.get('url') or '', 3 if kind == 'price_drop' else 4)


def sl_item(kind, p):
    """One Secret Lair alert as (section, line, url, priority)."""
    price = _money(p.get('price'))
    if p.get('was'):
        price += f' (was ${p["was"]:.2f})'
    line = f'• {short_name(p["name"])}: {price}'
    if kind == 'announced' and p.get('start'):
        line += ', on sale ' + dt.datetime.fromtimestamp(p['start']).strftime('%a %b %d, %I:%M %p').replace(' 0', ' ')
    note = legality_note(p['name'])
    if note:
        line += f'\n  {note}'
    sec = {'announced': 'sl_coming', 'price_drop': 'sl_drop'}.get(kind, 'sl_sale')
    return sec, line, p.get('url') or '', 3 if kind in ('announced', 'price_drop') else 4


def digest(items, cfg):
    """(title, message, click, priority, actions) for one push listing every item, or None."""
    if not items:
        return None
    store = cfg.get('store_name', 'Micro Center').replace('Micro Center', '').strip() or 'the store'
    groups = [(k, head.format(store=store), words, [i for i in items if i[0] == k]) for k, head, words in SECTIONS]
    groups = [g for g in groups if g[3]]
    title = 'MTG: ' + ', '.join(f'{len(g[3])} {g[2][len(g[3]) > 1]}' for g in groups)
    parts, size, left = [], 0, len(items)
    for _, head, _, its in groups:
        block = [f'{head}:']
        for it in its:
            if size + len(it[1].encode()) > MAX_BYTES:
                break
            block.append(it[1])
            size += len(it[1].encode()) + 1
            left -= 1
        if len(block) > 1:
            parts.append('\n'.join(block))
    msg = '\n\n'.join(parts) + (f'\n\n…and {left} more (see monitor.log)' if left else '')
    urls = [i[2] for i in items if i[2]]
    if len(items) == 1:
        click = urls[0] if urls else None
    elif all(i[0] in ('stock', 'drop') for i in items):
        click = watch_urls(cfg)[0] if cfg.get('watch_urls') else None
    else:
        click = 'https://secretlair.wizards.com/us/' if all(i[0].startswith('sl_') for i in items) else None
    actions = []
    if len(items) > 1:  # a button for each of the first three, so one tap opens that product
        for it in (it for g in groups for it in g[3]):  # in the order the message lists them
            if it[2] and len(actions) < 3:
                label = re.sub(r'^• ', '', it[1].split(':')[0])
                actions.append({'action': 'view', 'label': label[:22] + ('…' if len(label) > 22 else ''), 'url': it[2]})
    return title, msg, click, max(i[3] for i in items), actions


def send_digest(cfg, items):
    d = digest(items, cfg)
    if d:
        title, msg, click, pri, actions = d
        push(cfg, title, msg, click=click, priority=pri, tags=['black_joker'], actions=actions or None)


# ---------- fetching ----------

def fetch_pages(urls, cfg, debug=False):
    """Returns {url: html}. One persistent profile so Cloudflare's cookie survives between runs."""
    from playwright.sync_api import sync_playwright  # imported here so tests run without it
    print('  Micro Center: starting the browser...', flush=True)
    pages = {}
    with sync_playwright() as pw:
        opts = dict(user_data_dir=PROFILE, headless=cfg.get('headless', True),
                    viewport={'width': 1366, 'height': 900}, locale='en-US',
                    timezone_id=cfg.get('timezone', 'America/Chicago'))
        if not opts['headless'] and cfg.get('offscreen', True):
            # A real window passes Cloudflare more often than headless, but nobody wants it
            # popping up every 5 minutes: open it far off-screen. "offscreen": false shows it
            # (to click a check by hand).
            opts['args'] = ['--window-position=-32000,-32000']
        try:
            ctx = pw.chromium.launch_persistent_context(channel=cfg.get('channel', 'chrome'), **opts)
        except Exception:
            ctx = pw.chromium.launch_persistent_context(**opts)  # bundled Chromium if Chrome isn't installed
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        if not opts['headless'] and cfg.get('offscreen', True):
            # Chrome can ignore --window-position (it remembers where the profile's window was),
            # so also minimize the window to the taskbar through the DevTools protocol.
            try:
                cdp = ctx.new_cdp_session(page)
                wid = cdp.send('Browser.getWindowForTarget')['windowId']
                cdp.send('Browser.setWindowBounds', {'windowId': wid, 'bounds': {'windowState': 'minimized'}})
            except Exception as e:
                print(f'  (could not minimize the window: {e})')
        for i, url in enumerate(urls):
            if i:
                time.sleep(random.uniform(3, 8))
            print(f'  Micro Center: loading page {i + 1} of {len(urls)}...', flush=True)
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                # Cloudflare's check can pass by itself in a real browser after a few seconds.
                # With a visible window, give a person time to click Cloudflare's check.
                for n in range(6 if cfg.get('headless', True) else 24):
                    if not is_challenge(page.content()):
                        break
                    if n == 0:
                        print('  Cloudflare check showing, waiting ' + ('up to 30 s for it to pass...' if cfg.get('headless', True)
                              else 'up to 2 min: click the check in the Chrome window if it asks...'), flush=True)
                    time.sleep(5)
                try:
                    page.wait_for_selector('li.product_wrapper', timeout=10000)
                except Exception:
                    pass
                time.sleep(random.uniform(1, 3))
                pages[url] = page.content()
            except Exception as e:
                print(f'  fetch failed for {url}: {e}')
                pages[url] = ''
            if debug:
                os.makedirs(DEBUG_DIR, exist_ok=True)
                stamp = f'{dt.datetime.now():%Y%m%d-%H%M%S}-{i}'
                with open(os.path.join(DEBUG_DIR, stamp + '.html'), 'w', encoding='utf-8') as f:
                    f.write(pages[url])
                try:
                    page.screenshot(path=os.path.join(DEBUG_DIR, stamp + '.png'), full_page=True)
                except Exception:
                    pass
                print(f'  saved debug/{stamp}.html and .png')
        ctx.close()
    return pages


# ---------- one poll ----------

def poll(cfg, state, debug=False, fetch=fetch_pages, items=None):
    """One Micro Center check. Alerts go into items (the check's summary push); without a list
    to fill, it sends its own summary."""
    own = items is None
    items = [] if own else items
    urls = watch_urls(cfg)
    if state.get('parser') != PARSER_VERSION:
        # What was saved was read by an older parser (v1 read every stock as Unknown), so
        # comparing against it would push a false alert for everything. Start a new baseline.
        state['baselined'] = []
        state['parser'] = PARSER_VERSION
    pages = fetch(urls, cfg, debug)
    alerts, blocked, baselined = [], 0, []
    for url in urls:
        body = pages.get(url, '')
        if not body or is_challenge(body):
            blocked += 1
            continue
        products = parse_products(body)
        if not products:
            print(f'  0 products parsed from {url} (run with --debug and send the files if this keeps up)')
            continue
        products = [at_my_store(p, cfg) for p in products if wanted(p, cfg)]
        found, was_base = diff(state, url, products)
        if was_base:
            baselined.append((url, len(products)))
        alerts += found
        print(f'  {len(products)} products, {sum(p["in_stock"] for p in products)} in stock: {url}')

    if blocked:
        state['blocked_streak'] = state.get('blocked_streak', 0) + 1
        if time.time() - state.get('last_block_alert', 0) > BLOCK_ALERT_EVERY:
            state['last_block_alert'] = time.time()
            push(cfg, 'Micro Center monitor blocked',
                 f'Cloudflare blocked {blocked} of {len(urls)} pages. Backing off. If it keeps up, set '
                 '"headless": false in config.json and solve the check once in the window.', priority=2)
    else:
        state['blocked_streak'] = 0

    for url, n in baselined:
        push(cfg, 'Micro Center monitor started', f'Baseline recorded: {n} products. You\'ll hear about '
             'restocks and price drops at the store from now on.', priority=2)
    for kind, p in dedupe(alerts):
        if kind == 'price_drop' and not cfg.get('alert_price_drops', True):
            continue
        items.append(mc_item(kind, p))
    save_state(state)
    if own:
        send_digest(cfg, items)
    return blocked


def in_window(now):
    """The closely watched stretch: Thursday noon through Friday 11 AM (the user's pick;
    Micro Center says restocks go live Fridays at 10 AM, and the site can update earlier)."""
    wd, t = now.weekday(), now.hour * 60 + now.minute
    return (wd == 3 and t >= 12 * 60) or (wd == 4 and t < 11 * 60)


def window_start(now):
    """The next Thursday noon at or after now."""
    days = (3 - now.weekday()) % 7
    start = (now + dt.timedelta(days=days)).replace(hour=12, minute=0, second=0, microsecond=0)
    return start if start >= now else start + dt.timedelta(days=7)


def next_wait(now, wake_at=None):
    """5 min from Thursday noon to Friday 11 AM, 30-60 min otherwise. Never sleeps through
    the window's start, or through wake_at (a Secret Lair sale start, as a timestamp)."""
    if in_window(now):
        return 300 + random.uniform(-20, 40)
    wait = min(random.uniform(1800, 3600), (window_start(now) - now).total_seconds() + random.uniform(0, 30))
    if wake_at:
        wait = min(wait, max(60, wake_at - now.timestamp() + random.uniform(20, 60)))
    return wait


def backoff(streak):
    """While Cloudflare blocks Micro Center, skip it for longer each time (30 min, 1 h, then 2 h)
    instead of knocking harder. Secret Lair keeps its own schedule meanwhile."""
    return min(7200, 1800 * 2 ** (streak - 1)) if streak else 0


def poll_micro_center(cfg, state, debug=False, manual=False, items=None):
    if not cfg.get('microcenter_enabled', True):
        return
    if not manual and time.time() < state.get('mc_skip_until', 0):
        print(f'  Micro Center: backing off after a block, next try {dt.datetime.fromtimestamp(state["mc_skip_until"]):%H:%M}')
        return
    try:
        poll(cfg, state, debug=debug, items=items)
    except ImportError:
        print('  Micro Center skipped: Playwright isn\'t installed (pip install playwright, then playwright install chromium)')
        return
    except Exception as e:
        print(f'  Micro Center check failed: {e}')
        return
    state['mc_skip_until'] = time.time() + backoff(state.get('blocked_streak', 0))


def poll_secret_lair(cfg, state, getter=secretlair.get, items=None):
    own = items is None
    items = [] if own else items
    sc = cfg.get('secret_lair', {})
    if not sc.get('enabled', True):
        return
    sl = state.setdefault('sl', {})
    full = time.time() - sl.get('last_full', 0) > sc.get('full_scan_hours', 24) * 3600
    print('  Secret Lair: reading the store' + (' and its whole catalog (about a minute)...' if full else '...'), flush=True)
    try:
        products, feeds = secretlair.fetch_products(state, full=full, getter=getter)
    except Exception as e:
        print(f'  Secret Lair check failed: {e}')
        if time.time() - sl.get('last_fail_alert', 0) > 6 * 3600 and sl.get('fails', 0) >= 2:
            sl['last_fail_alert'] = time.time()
            push(cfg, 'Secret Lair check failing', f'Couldn\'t read the Secret Lair store: {e}', priority=2)
        sl['fails'] = sl.get('fails', 0) + 1
        save_state(state)
        return
    sl['fails'] = 0
    if full:
        sl['last_full'] = time.time()
    exc = [k.lower() for k in sc.get('exclude', [])]
    products = [p for p in products if not any(k in p['name'].lower() for k in exc)]
    alerts, baseline = secretlair.diff(state, products)
    counts = {k: sum(p['status'] == k for p in products) for k in ('on_sale', 'coming', 'sold_out')}
    print(f'  Secret Lair: {len(products)} products from {len(feeds)} home-page rows{" + full catalog" if full else ""}: '
          f'{counts["on_sale"]} on sale, {counts["coming"]} coming, {counts["sold_out"]} sold out')
    if baseline:
        push(cfg, 'Secret Lair monitor started', f'Baseline recorded: {len(products)} products. You\'ll hear about '
             'new drops and sales starting from now on.', priority=2)
    for kind, p in alerts:
        if kind == 'price_drop' and not cfg.get('alert_price_drops', True):
            continue
        items.append(sl_item(kind, p))
    save_state(state)
    if own:
        send_digest(cfg, items)


def check_debug():
    """Prints what the parser read from the newest saved Micro Center page, plus the raw text
    of its first few results, so a wrong stock or price reading can be fixed from a paste."""
    import glob
    files = [f for f in sorted(glob.glob(os.path.join(DEBUG_DIR, '*.html')))
             if 'product_wrapper' in open(f, encoding='utf-8', errors='replace').read()]
    if not files:
        print('No saved Micro Center page with products in debug/. Run: python monitor.py --once --debug')
        return
    page_html = open(files[-1], encoding='utf-8', errors='replace').read()
    ps = parse_products(page_html)
    print(f'{os.path.basename(files[-1])}: {len(ps)} products, {sum(p["in_stock"] for p in ps)} read as in stock')
    for p in ps[:6]:
        print(f'  {p["name"][:60]} | {p["stock"]} | ${p["price"]} | SKU {p["sku"]}')
    starts = [m.start() for m in re.finditer(r'<li[^>]*class="[^"]*product_wrapper', page_html, re.I)]
    for i, st in enumerate(starts[:3]):
        block = page_html[st:starts[i + 1] if i + 1 < len(starts) else st + 20000]
        print(f'--- raw text of result {i + 1} ---')
        print(_text(block)[:600])
        print('--- classes in it ---')
        print(' '.join(sorted(set(re.findall(r'class="([^"]+)"', block))))[:600])


LOG = os.path.join(HERE, 'monitor.log')


def log_to_file_if_hidden():
    """Under pythonw (the Startup shortcut) there's no console and print() goes nowhere, so
    write the same lines to monitor.log, so you can see each check. Starts over past 1 MB."""
    if sys.stdout is not None:
        return
    try:
        mode = 'w' if os.path.exists(LOG) and os.path.getsize(LOG) > 1_000_000 else 'a'
        sys.stdout = sys.stderr = open(LOG, mode, encoding='utf-8', buffering=1)
    except OSError:
        pass


WATCHDOG_ID = 'monitor-watchdog'
WATCHDOG_GAP = 20 * 60         # in the window, warn after 20 min without a check (4 missed)
NTFY_MAX_DELAY = 3 * 86400 - 600


def watchdog_due(now):
    """When the "monitor went quiet" warning should go off if no check replaces it first.
    In the Thursday-Friday window: 20 minutes from now. Outside it: 20 minutes into the next
    window, so a PC that's asleep when the window starts gets noticed; but ntfy holds messages
    3 days at most, so a window further off than that gets a 3-days-quiet warning instead."""
    if in_window(now + dt.timedelta(seconds=WATCHDOG_GAP)):
        return now + dt.timedelta(seconds=WATCHDOG_GAP), True
    nxt = window_start(now) + dt.timedelta(seconds=WATCHDOG_GAP)
    if (nxt - now).total_seconds() <= NTFY_MAX_DELAY:
        return nxt, True
    return now + dt.timedelta(seconds=NTFY_MAX_DELAY), False


def arm_watchdog(cfg, now=None):
    """A dead man's switch on ntfy's server: after every check, hand ntfy a warning to deliver
    later, replacing the one before (same sequence id). While checks keep coming it never
    arrives; if the PC is off, asleep or signed out, ntfy delivers it, which a sleeping PC
    couldn't do itself. (ntfy.sh's cancel didn't stop a held message in a test on Nov 16,
    2026, so it's always replaced, never cancelled.)"""
    if not cfg.get('watchdog', True):
        return
    now = now or dt.datetime.now()
    due, window = watchdog_due(now)
    # Each warning gets its own delivery second: in a test, two held messages with the same
    # sequence id sent close together were both delivered instead of one replacing the other.
    due += dt.timedelta(seconds=random.randint(0, 240))
    last = now.strftime('%a %I:%M %p').replace(' 0', ' ')
    if window:
        title, msg, pri = ('Restock monitor isn\'t checking',
                           f'No check since {last}, during the Thursday noon to Friday 11 AM window. '
                           'Is the PC asleep, off or signed out?', 4)
    else:
        title, msg, pri = ('Restock monitor quiet for 3 days', f'No check since {last}. '
                           'Is the PC off, asleep or signed out?', 3)
    push(cfg, title, msg, priority=pri, tags=['warning'], delay=str(int(due.timestamp())),
         sequence_id=WATCHDOG_ID, quiet=True)
    print(f'  watchdog: warns at {due:%a %H:%M} unless the next check comes first')


def sleep_until(target, step=30):
    """Sleep in short steps so a PC waking from sleep checks right away. Python's sleep
    doesn't count time the PC spent asleep, so one long sleep could add an hour after waking."""
    while True:
        left = target - time.time()
        if left <= 0:
            return 'due'
        before = time.time()
        time.sleep(min(step, left))
        if time.time() - before > step + 90:
            print(f'[{dt.datetime.now():%a %H:%M}] woke from sleep, checking now')
            return 'woke'


def main(argv=None):
    log_to_file_if_hidden()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--once', action='store_true', help='poll once and exit')
    ap.add_argument('--test', action='store_true', help='send a test push and exit')
    ap.add_argument('--debug', action='store_true', help='save fetched HTML and screenshots to debug/')
    ap.add_argument('--check', action='store_true', help='show what was read from the newest saved debug page')
    a = ap.parse_args(argv)
    if a.check:
        return check_debug()
    cfg = load_config()
    if a.test:
        push(cfg, 'Micro Center monitor test', f'Pushes work. Watching {cfg.get("store_name")} '
             f'(storeid {cfg["store_id"]}) and Secret Lair.', click=watch_urls(cfg)[0], tags=['white_check_mark'])
        return
    while True:
        state = load_state()
        print(f'[{dt.datetime.now():%a %Y-%m-%d %H:%M}] checking')
        items = []  # every alert from this check, sent as one push
        poll_micro_center(cfg, state, debug=a.debug, manual=a.once, items=items)  # a run by hand never waits out the back-off
        poll_secret_lair(cfg, state, items=items)
        send_digest(cfg, items)
        if a.once:
            return
        arm_watchdog(cfg)
        wait = next_wait(dt.datetime.now(), secretlair.next_start(state, time.time()))
        print(f'  next poll in {wait / 60:.0f} min')
        sleep_until(time.time() + wait)


if __name__ == '__main__':
    sys.exit(main())
