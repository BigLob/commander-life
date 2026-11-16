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
            m = re.search(r'\$\s?([\d,]+\.\d\d)', text)
            price = m.group(1).replace(',', '') if m else ''
        stock_html = re.search(r'class="[^"]*(?:stock|inventory)[^"]*"[^>]*>(.*?)</(?:div|span|p)>', block, re.S | re.I)
        in_stock, label, count = parse_stock(_text(stock_html.group(1)) if stock_html else text)
        if not name:
            continue
        out.append({'key': sku or href or name, 'name': name, 'sku': sku, 'price': price,
                    'url': href, 'in_stock': in_stock, 'stock': label, 'count': count})
    return out


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

def diff(state, url, products, now=None):
    """Merges this page's products into the state and returns the alerts. A URL seen for the
    first time only records a baseline, so starting the monitor (or adding a URL) never pushes
    a flood. Products missing from a page are left alone: pages paginate and reorder."""
    now = now or dt.datetime.now().isoformat(timespec='seconds')
    known = state['products']
    baseline = url not in state['baselined']
    alerts = []
    for p in products:
        old = known.get(p['key'])
        rec = dict(p, last_seen=now, first_seen=old['first_seen'] if old else now)
        if not baseline:
            if old is None:
                alerts.append(('new_in_stock' if p['in_stock'] else 'new_listing', p))
            elif p['in_stock'] and not old.get('in_stock'):
                alerts.append(('restock', p))
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

def push(cfg, title, message, click=None, priority=3, tags=None):
    print(f'[{dt.datetime.now():%a %H:%M}] {title}: {message}')
    topic = cfg.get('ntfy_topic')
    if not topic:
        return
    body = {'topic': topic, 'title': title, 'message': message, 'priority': priority}
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
    head = {'restock': 'Back in stock', 'new_in_stock': 'New and in stock',
            'new_listing': 'New listing (not in stock yet)'}[kind]
    price = f'${p["price"]}' if p['price'] else 'no price'
    lines = [p['name'], f'{price} · {p["stock"]} · {cfg.get("store_name", "store " + str(cfg["store_id"]))}']
    note = legality_note(p['name'])
    if note:
        lines.append(note)
    return f'MTG: {head}', '\n'.join(lines)


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

def poll(cfg, state, debug=False, fetch=fetch_pages):
    urls = watch_urls(cfg)
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
        products = [p for p in products if wanted(p, cfg)]
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
             'restocks and new listings from now on.', priority=2)
    for kind, p in dedupe(alerts):
        if kind == 'new_listing' and not cfg.get('alert_new_listings', True):
            continue
        title, msg = alert_text(kind, p, cfg)
        push(cfg, title, msg, click=p['url'] or None,
             priority=4 if kind != 'new_listing' else 3, tags=['black_joker'])
    save_state(state)
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


def poll_micro_center(cfg, state, debug=False, manual=False):
    if not cfg.get('microcenter_enabled', True):
        return
    if not manual and time.time() < state.get('mc_skip_until', 0):
        print(f'  Micro Center: backing off after a block, next try {dt.datetime.fromtimestamp(state["mc_skip_until"]):%H:%M}')
        return
    try:
        poll(cfg, state, debug=debug)
    except ImportError:
        print('  Micro Center skipped: Playwright isn\'t installed (pip install playwright, then playwright install chromium)')
        return
    except Exception as e:
        print(f'  Micro Center check failed: {e}')
        return
    state['mc_skip_until'] = time.time() + backoff(state.get('blocked_streak', 0))


def poll_secret_lair(cfg, state, getter=secretlair.get):
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
        title, msg = secretlair.alert_text(kind, p)
        note = legality_note(p['name'])
        push(cfg, title, msg + (f'\n{note}' if note else ''), click=p['url'],
             priority=3 if kind == 'announced' else 4, tags=['crystal_ball'])
    save_state(state)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--once', action='store_true', help='poll once and exit')
    ap.add_argument('--test', action='store_true', help='send a test push and exit')
    ap.add_argument('--debug', action='store_true', help='save fetched HTML and screenshots to debug/')
    a = ap.parse_args(argv)
    cfg = load_config()
    if a.test:
        push(cfg, 'Micro Center monitor test', f'Pushes work. Watching {cfg.get("store_name")} '
             f'(storeid {cfg["store_id"]}) and Secret Lair.', click=watch_urls(cfg)[0], tags=['white_check_mark'])
        return
    while True:
        state = load_state()
        print(f'[{dt.datetime.now():%a %Y-%m-%d %H:%M}] checking')
        poll_micro_center(cfg, state, debug=a.debug, manual=a.once)  # a run by hand never waits out the back-off
        poll_secret_lair(cfg, state)
        if a.once:
            return
        wait = next_wait(dt.datetime.now(), secretlair.next_start(state, time.time()))
        print(f'  next poll in {wait / 60:.0f} min')
        time.sleep(wait)


if __name__ == '__main__':
    sys.exit(main())
