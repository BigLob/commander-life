#!/usr/bin/env python3
"""Adds three more lists to each theme/<slug>.json, for theme/review.html's Tutors, Game Changers and Wincons tabs
(the user's ask, Nov 21, 2026):

  tutors  every Commander-legal tutor in the deck's colors that isn't in the box: a card that searches your own
          library for a nonland card (to hand, top, battlefield or graveyard; transmute counts). Not counted: land
          searches (fetches, ramp), cards that only find copies of themselves, searches an opponent makes (Path to
          Exile), and wishes (outside the game). A tutor for one creature type is kept only when that type is in the
          deck's theme tests (Zombie tutors for the Zombie decks, Dragon tutors for Atarka).
  gcs     every Game Changer in the colors that isn't in the box (Bracket 3 allows 3 in the deck).
  wins    every alternate win condition in the colors that isn't in the box (Scryfall's alternate-win-condition tag,
          the same cards as wincons/).

Each list is ordered by the share of EDHREC's decks for the commander that play the card, then by EDHREC's overall
rank. A card that passes the deck's theme tests (THEMES in theme_picks.py) is marked on theme.

    python3 tools/carousel/theme_extras.py [slug ...]      (default: every deck with a theme/<slug>.json)

theme_picks.py runs it for its deck after writing the JSON, so a rerun there keeps the tabs.
Downloads are cached in $THEME_EXTRAS_CACHE (default /tmp/theme-extras); delete it to fetch fresh.
"""
import glob, json, os, re, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from theme_picks import THEMES, get, oracle, typeline, front

CACHE = os.environ.get('THEME_EXTRAS_CACHE', '/tmp/theme-extras')
_types = None

def cached(name, fetch):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, re.sub(r'[^\w.-]+', '_', name) + '.json')
    if not os.path.exists(p): json.dump(fetch(), open(p, 'w'))
    return json.load(open(p))

def search(q):
    def f():
        out, url = [], 'https://api.scryfall.com/cards/search?' + urllib.parse.urlencode({'q': q, 'order': 'edhrec', 'unique': 'cards'})
        while url:
            try: d = get(url)
            except Exception: return out   # Scryfall answers 404 when nothing matches
            out += d['data']; url = d.get('next_page'); time.sleep(0.12)
        return out
    return cached('sf-' + q, f)

def creature_types():
    global _types
    if _types is None:
        _types = sorted(cached('creature-types', lambda: get('https://api.scryfall.com/catalog/creature-types')['data']), key=len, reverse=True)
    return _types

# "search your library [and/or graveyard] for <what>" up to the end of the noun phrase.
SEARCH = re.compile(r'search your library(?: and(?:/or)? (?:your )?graveyard)?(?: and(?:/or)? outside the game)? for ([^.;]*?)(?:,|\band (?:put|reveal|exile|cast)|\bput|\breveal|\bexile|\.|$)')
WHERE = [('onto the battlefield', 'onto the battlefield'), ('into your graveyard', 'to the graveyard'), ('on top', 'to the top of the library'),
         ('into your hand', 'to hand'), ('exile', 'to exile')]

def tutor(c, theme_text):
    """None, or a short line of what the card finds and where it puts it."""
    o = oracle(c).lower().replace('\n', ' ')
    if 'Land' in typeline(c).split(' // ')[0] and 'Saga' not in typeline(c) and not re.search(r'search your library for (?:an? |up to )?(?:artifact|creature|card|equipment|enchantment|instant|sorcery)', o):
        return None   # lands that only fetch lands
    hits = []
    for m in SEARCH.finditer(o):
        what = m.group(1).strip()
        if not what or re.search(r'\bnamed\b|\bland\b|\blands\b|\bbasic\b|\bforest|\bisland|\bswamp|\bmountain|\bplains|\bgates?\b|\bdeserts?\b|\bcaves?\b|\bshrines?\b|\btowns?\b', what):
            continue
        if re.search(r'(?:with the same name|card with that name)', what): continue
        # A tutor for one creature type only counts in a deck whose theme is that type.
        ts = [t for t in creature_types() if re.search(r'\b' + re.escape(t.lower()) + r's?\b', what)]
        if ts and not any(re.search(r'\b' + re.escape(t.lower()), theme_text) for t in ts): continue
        tail = o[m.end(1):m.end(1) + 160]
        dest = next((d for k, d in WHERE if k in tail), 'to hand')
        hits.append((what, dest))
    if not hits: return None
    what, dest = hits[0]
    what = re.sub(r'\s+', ' ', what)
    if len(what) > 70: what = what[:67].rsplit(' ', 1)[0] + '…'
    return f'Finds {what}, {dest}'

def gist(c):
    t = oracle(c).replace('\n', ' ').replace('~', front(c['name']))
    s = [x.strip() for x in re.split(r'(?<=[.)])\s+', t) if re.search(r'wins? the game|loses? the game', x)]
    s = ' '.join(s) or t   # The Millennium Calendar: "each opponent loses 1,000 life"
    return s if len(s) <= 180 else s[:177].rsplit(' ', 1)[0] + '…'

def run(slug):
    T = THEMES[slug]; path = os.path.join(ROOT, 'theme', slug + '.json')
    J = json.load(open(path))
    h = open(os.path.join(ROOT, 'decks', T.get('precon', slug) + '.html')).read()
    box = {front(c['n']) for c in json.loads(re.search(r'const ALL=(\[.*?\]);\n', h, re.S).group(1))}
    cslug = re.sub(r'[^a-z0-9]+', '-', T['cmd'].lower().replace("'", '')).strip('-')
    cp = cached('edhrec-' + cslug, lambda: get(f'https://json.edhrec.com/pages/commanders/{cslug}.json'))
    ed = {}
    for l in cp['container']['json_dict']['cardlists']:
        for c in l['cardviews']:
            if c.get('potential_decks'): ed[front(c['name'])] = c['num_decks'] / c['potential_decks']
    edn = cp['container']['json_dict'].get('card', {}).get('num_decks', 0)
    theme_text = ' '.join((ot or '') + ' ' + (tt or '') for _, _, ot, tt in T['tests']).lower() + ' ' + T['direction'].lower()
    def role(c):
        o, t = oracle(c).lower(), typeline(c)
        for r, label, ot, tt in T['tests']:
            if (ot is None or re.search(ot, o)) and (tt is None or re.search(tt, t)): return label
        return None
    picked = {x['n'] for x in J['adds'] if x.get('top')}
    base = f'id<={T["id"]} legal:commander game:paper'

    def rows(cards, job):
        out = []
        for c in cards:
            n = front(c['name'])
            if n in box or 'Basic' in typeline(c): continue
            j = job(c)
            if j is None: continue
            iu = c.get('image_uris') or c['card_faces'][0]['image_uris']
            p = c.get('prices') or {}
            usd = p.get('usd') or p.get('usd_foil')
            th = role(c)
            out.append({'n': n, 'img': iu['normal'], 'url': c['scryfall_uri'].split('?')[0], 'job': j, 'e': round(ed.get(n, 0), 3),
                        'rank': c.get('edhrec_rank') or 10 ** 6, 'gc': bool(c.get('game_changer')), 'usd': float(usd) if usd else None,
                        'theme': th, 'pick': n in picked})
        out.sort(key=lambda x: (-x['e'], x['rank']))
        for x in out: del x['rank']
        return out

    J['tutors'] = rows(search(base + ' (o:"search your library" or o:transmute)'), lambda c: tutor(c, theme_text))
    J['gcs'] = rows(search(base + ' is:gamechanger'), lambda c: typeline(c).replace(' — ', ': '))
    J['wins'] = rows(search(base + ' otag:alternate-win-condition'), gist)
    J['box_tutors'] = sorted(front(c['name']) for c in search(base + ' (o:"search your library" or o:transmute)')
                             if front(c['name']) in box and tutor(c, theme_text))
    J['box_gcs'] = sorted(front(c['name']) for c in search(base + ' is:gamechanger') if front(c['name']) in box)
    J['box_wins'] = sorted(front(c['name']) for c in search(base + ' otag:alternate-win-condition') if front(c['name']) in box)
    J['cedn'] = edn
    json.dump(J, open(path, 'w'), separators=(',', ':'))
    print(f'{slug}: {len(J["tutors"])} tutors, {len(J["gcs"])} Game Changers, {len(J["wins"])} wincons '
          f'(box: {len(J["box_tutors"])}, {len(J["box_gcs"])}, {len(J["box_wins"])}; EDHREC {edn:,} decks)')

if __name__ == '__main__':
    slugs = sys.argv[1:] or sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'theme', '*.json'))
                                   if os.path.basename(p)[:-5] in THEMES)
    for s in slugs: run(s)
