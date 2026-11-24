"""Mana costs for the carousels' name lines (the user's ask, Nov 24, 2026: every card's cost
right-aligned on its name line).

mana(c) turns a Scryfall card into the cost string the pages show: the card's own mana_cost, or for
a double-faced card its front face's (split cards keep both halves, "{1}{R} // {U}"). Lands and
other cards with no cost give ''.

lookup(names) fetches costs by name through Scryfall's /cards/collection (75 a request), retrying
misses by their front-face name. MANACOST_CACHE=<file> keeps the answers between runs.
"""
import json, os, time, urllib.request


def mana(c):
    if c.get('mana_cost'):
        return c['mana_cost']
    faces = c.get('card_faces') or []
    return faces[0].get('mana_cost', '') if faces else ''


def _post(ids):
    req = urllib.request.Request('https://api.scryfall.com/cards/collection',
                                 data=json.dumps({'identifiers': ids}).encode(),
                                 headers={'User-Agent': 'commander-life/1.0', 'Accept': 'application/json',
                                          'Content-Type': 'application/json'})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception:
            if i == 3:
                raise
            time.sleep(2 * (i + 1))


def lookup(names):
    path = os.environ.get('MANACOST_CACHE')
    cache = {}
    if path and os.path.exists(path):
        cache = json.load(open(path))
    want = sorted({n for n in names if n and n not in cache})
    # Ask by full name first, then by front face for the ones Scryfall's exact match misses ("Fire // Ice").
    for key in (lambda n: n, lambda n: n.split(' // ')[0]):
        for i in range(0, len(want), 75):
            part = want[i:i + 75]
            d = _post([{'name': key(n)} for n in part])
            got = {}
            for c in d.get('data', []):
                got[c['name']] = mana(c)
                for f in c.get('card_faces') or []:
                    got.setdefault(f['name'], mana(c))
            for n in part:
                k = key(n)
                if n in got:
                    cache[n] = got[n]
                elif k in got:
                    cache[n] = got[k]
                else:
                    for full, m in got.items():
                        if full.split(' // ')[0] == k:
                            cache[n] = m
            time.sleep(0.1)
        want = [n for n in want if n not in cache]
        if not want:
            break
    if path:
        json.dump(cache, open(path, 'w'), indent=0, sort_keys=True)
    return cache, want


_MEM = {}
NOT_FOUND = set()


def _need(names):
    miss = sorted({n for n in names if n not in _MEM})
    if miss:
        got, lost = lookup(miss)
        _MEM.update({n: got.get(n, '') for n in miss})
        NOT_FOUND.update(lost)


def fill(cards):
    """Give every card dict in the list an 'mc' (kept if it has one). Returns the list, so a builder can
    write json.dumps(manacost.fill(ALL), ...)."""
    _need(c['n'] for c in cards if 'mc' not in c)
    for c in cards:
        if 'mc' not in c:
            c['mc'] = _MEM.get(c['n'], '')
    return cards


def fill_tree(obj):
    """fill() every card dict (one with 'n' and 'img') anywhere in a theme JSON."""
    found = []
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get('n'), str) and 'img' in o:
                found.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(obj)
    fill(found)
    return obj


def get(name):
    _need([name])
    return _MEM.get(name, '')


def prefetch(names):
    _need(names)


SYM = 'https://svgs.scryfall.io/card-symbols/'


def html(s):
    """The same markup the pages' manaCost() writes, for pages built in Python (theme/<slug>.html, angles)."""
    if not s:
        return ''
    import re
    halves = ['' .join(f'<img src="{SYM}{t[1:-1].replace("/", "")}.svg" alt="{t}" draggable="false">'
                       for t in re.findall(r'\{[^}]+\}', h)) for h in s.split(' // ')]
    return f'<span class="mc" title="{s}">' + '<b>//</b>'.join(halves) + '</span>'


# What gets pasted into the client-rendered pages (add_mana_costs.py puts it in the templates too).
JS = ("// Mana cost as Scryfall's symbols, right-aligned on the name line (the user's ask, Nov 24, 2026).\n"
      "function manaCost(s){return s?'<span class=\"mc\" title=\"'+s+'\">'+s.split(' // ').map(h=>(h.match(/\\{[^}]+\\}/g)||[])"
      ".map(t=>'<img src=\"" + SYM + "'+t.slice(1,-1).replace(/\\//g,'')+'.svg\" alt=\"'+t+'\" draggable=\"false\">').join(''))"
      ".join('<b>//</b>')+'</span>':''}\n")
CSS_MC = ('.mc{display:flex;gap:1px;align-items:center;height:1.25em;flex:none}'
          '.mc img{width:1em;height:1em;display:block}'
          '.mc b{font-weight:400;color:var(--muted);margin:0 2px;font-size:.8em}\n')
