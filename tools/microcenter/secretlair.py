"""Secret Lair drops from Wizards' official store (secretlair.wizards.com), for monitor.py.

No browser needed: the store's pages fill themselves from a public JSON search API
(storesearch.eu.scalefast.com/StoreSearch), the same one its own product rows call. We read:
  1. the home page, for the feed IDs of the rows it shows right now (the current drop, its
     bundles, anything coming soon), with ng-init="init('<feedID>', ...)";
  2. each of those feeds from the API (a few small requests);
  3. once a day, the whole catalog (about 1,100 products, 50 per request), to catch anything
     listed that isn't on the home page.

A product's status isn't in the data; the page works it out from the sale window and stock,
and so do we (sale_status()). Sale times are in Paris time (the store's server zone).
"""
import ast
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request

HOME = 'https://secretlair.wizards.com/us'
API = 'https://storesearch.eu.scalefast.com/StoreSearch'
USER_ID = '10751401'   # the Secret Lair store's account on Scalefast, from the store's own requests
PAGE = 50              # the API's largest page
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'

try:
    from zoneinfo import ZoneInfo
    PARIS = ZoneInfo('Europe/Paris')
except Exception:  # Windows without the tzdata package: CET, an hour off in summer
    PARIS = dt.timezone(dt.timedelta(hours=1))


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


def feed_ids(home_html):
    """Feed IDs of the home page's product rows. '72135|all' is a row of the whole feed."""
    out = []
    for f in re.findall(r"init\('(\d+)(?:\|[a-z]+)?'\s*,\s*'\d+'", home_html):
        if f not in out:
            out.append(f)
    return out


def api_url(offset=0, feed=None):
    q = {'userID': USER_ID, 'locale': 'en_US', 'currency': 'USD', 'sort': 'featured',
         'offset': offset, 'count': PAGE, 'env': 'prod', 'crit': 'ALL'}
    if feed:
        q['filters'] = f'feedID:{feed}'
    return API + '?' + urllib.parse.urlencode(q)


def unwrap(data):
    """The API answers {count, total, products}, or with a feed filter {filters: [{...}]}."""
    if isinstance(data, dict) and 'filters' in data and data['filters']:
        data = data['filters'][0]
    return data.get('products', []), int(data.get('total', 0) or 0)


def _list(v):
    if isinstance(v, str):
        try:
            return ast.literal_eval(v)  # some fields come as Python-style strings
        except Exception:
            return []
    return v or []


def title_of(p):
    titles = {d.get('lang'): d.get('title') for d in _list(p.get('descriptions')) if isinstance(d, dict)}
    t = titles.get('EN') or next(iter(titles.values()), '') or f'Product {p.get("productID")}'
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t)).strip()  # some titles carry <br>


def paris(s):
    if not s or s.startswith('0000'):
        return None
    try:
        return dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S').replace(tzinfo=PARIS)
    except ValueError:
        return None


def sale_status(p, now):
    """'coming' (sale not started), 'on_sale', 'sold_out' or 'ended', as the store's page shows it."""
    fs = p.get('flash_sales') or {}
    start, end = paris(fs.get('start_date')), paris(fs.get('end_date'))
    if start and now < start:
        return 'coming'
    if end and now >= end:
        return 'ended'
    st = p.get('stock') or {}
    try:
        n = int(st.get('stock') or 0)
    except (TypeError, ValueError):
        n = 0
    if n <= 0 and st.get('ostock', 'DENY_PURCHASE') == 'DENY_PURCHASE':
        return 'sold_out'
    return 'on_sale'


def product(p, now):
    prices = (p.get('price_info') or {}).get('prices') or []
    start = paris((p.get('flash_sales') or {}).get('start_date'))
    return {'key': 'sl-' + str(p['productID']), 'id': str(p['productID']), 'name': title_of(p),
            'price': prices[0].get('price', '') if prices else '', 'type': p.get('type', ''),
            'status': sale_status(p, now), 'start': start.timestamp() if start else None,
            'url': f'{HOME}/product/{p["productID"]}'}


def fetch_products(state, full=False, now=None, getter=get):
    """Home-page feeds (and the whole catalog when full). Falls back to the last feed IDs seen
    if the home page doesn't load (Queue-it's waiting room can stand in front of it on drop days)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    sl = state.setdefault('sl', {})
    try:
        feeds = feed_ids(getter(HOME))
        if feeds:
            sl['feeds'] = feeds
    except Exception as e:
        print(f'  Secret Lair home page failed ({e}); using the last feeds seen')
    feeds = sl.get('feeds', [])
    raw = {}
    for f in feeds:
        prods, _ = unwrap(json.loads(getter(api_url(feed=f))))
        for p in prods:
            raw[str(p['productID'])] = p
        time.sleep(0.5)
    if full:
        offset, total = 0, 1
        while offset < total and offset < 5000:
            prods, total = unwrap(json.loads(getter(api_url(offset))))
            if not prods:
                break
            for p in prods:
                raw.setdefault(str(p['productID']), p)
            offset += PAGE
            time.sleep(1)
    return [product(p, now) for p in raw.values()], feeds


def diff(state, products):
    """Alerts: ('announced', p) for a new product not on sale yet, ('new_on_sale', p) for a new one
    already on sale, ('on_sale', p) when a known one goes on sale (sale started, or back from sold
    out). The first run only records a baseline."""
    sl = state.setdefault('sl', {})
    known = sl.setdefault('products', {})
    baseline = not sl.get('baselined')
    alerts = []
    for p in products:
        old = known.get(p['key'])
        if not baseline:
            if old is None:
                if p['status'] == 'coming':
                    alerts.append(('announced', p))
                elif p['status'] == 'on_sale':
                    alerts.append(('new_on_sale', p))
            else:
                was = _was(old, p)
                if was:
                    p = dict(p, was=was)
                if p['status'] == 'on_sale' and old.get('status') != 'on_sale':
                    alerts.append(('on_sale', p))
                elif was and p['status'] in ('on_sale', 'coming'):
                    alerts.append(('price_drop', p))  # drops only, never rises
        known[p['key']] = p
    sl['baselined'] = True
    return alerts, baseline


def _was(old, p):
    try:
        was, now = float(old.get('price') or 0), float(p.get('price') or 0)
    except ValueError:
        return None
    return was if was and now and now < was - 0.005 else None


def next_start(state, now_ts):
    """The soonest sale start among known products still to come, so the loop can wake for it."""
    starts = [p['start'] for p in state.get('sl', {}).get('products', {}).values()
              if p.get('status') == 'coming' and p.get('start') and p['start'] > now_ts]
    return min(starts) if starts else None


def alert_text(kind, p):
    price = f'${p["price"]}' if p['price'] else 'no price'
    when = ''
    if p.get('start'):
        when = dt.datetime.fromtimestamp(p['start']).strftime('%a %b %d, %I:%M %p').replace(' 0', ' ')
    head = {'announced': 'Secret Lair announced', 'new_on_sale': 'Secret Lair on sale now',
            'on_sale': 'Secret Lair on sale now', 'price_drop': 'Secret Lair price drop'}[kind]
    if p.get('was'):
        price += f' (was ${p["was"]:.2f})'
    lines = [p['name'], price]
    if kind == 'announced' and when:
        lines.append(f'On sale {when} (your time)')
    return head, '\n'.join(lines)
