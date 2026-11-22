#!/usr/bin/env python3
"""theme/<slug>-combos.json, the data behind theme/final.html's live benchmarks (the user's ask, Nov 22, 2026).

The final review counts, as the user re-picks cards: tutors in the deck, basics swapped for nonbasic lands, spells
added, Game Changers, and infinite combos with the earliest turn each could go off. The page can't call Commander
Spellbook itself (its API sends no CORS header), so this script asks Spellbook once for every combo it knows whose
cards all sit inside the pool: the box plus every card theme/<slug>.json offers (adds, cuts, lands, tutors, Game
Changers, wincons). Whatever the user ends up picking is a subset of that pool, so any combo in the final deck is in
this list; the page keeps the ones whose pieces are all in the deck as it stands.

Combos that ask for a kind of card (Spellbook's templates, such as "Creature with Persist or Undying") get the pool's
cards that fit it (the template's own Scryfall query, in the deck's colors), so the page can check one is in.

Written per deck:
  box     the box's cards: n, q, mv, land, basic
  info    every offered card not in the box: mv, land
  combos  infinite combos only (a Spellbook result named "Infinite ..."): id, cards [{n, z (zones, B battlefield,
          H hand, G graveyard...), c (must be the commander)}], req [{t (template), q, opts [card names]}],
          prods, mana (mana needed beyond casting the pieces, as Spellbook writes it), mv (its mana value), tag
          (Spellbook's bracket tag)

    python3 tools/carousel/theme_combos.py [slug ...]      (default: every deck with a theme/<slug>.json)

theme_picks.py runs it after theme_extras.py, so a rebuilt deck keeps its combo data. Rerun it for every deck now
and then: Spellbook adds combos.
"""
import glob, json, os, re, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from theme_picks import THEMES, get, typeline, front

SB = 'https://backend.commanderspellbook.com/find-my-combos'

def scry_collection(names):
    """Scryfall card objects by front-face name, 75 per request."""
    out, names = {}, sorted(set(names))
    for i in range(0, len(names), 75):
        d = get('https://api.scryfall.com/cards/collection', {'identifiers': [{'name': n} for n in names[i:i + 75]]})
        for c in d['data']: out[front(c['name'])] = c
        for nf in d.get('not_found', []):   # a front face alone isn't always matched: try the fuzzy name
            try:
                c = get('https://api.scryfall.com/cards/named?' + urllib.parse.urlencode({'fuzzy': nf['name']}))
                out[nf['name']] = c
            except Exception: print('  not on Scryfall:', nf['name'])
            time.sleep(0.1)
        time.sleep(0.12)
    return out

def template_cards(query, ident, pool):
    """Pool cards that fit a Spellbook template: its Scryfall query, in the deck's colors."""
    url = 'https://api.scryfall.com/cards/search?' + urllib.parse.urlencode({'q': f'({query}) id<={ident} legal:commander', 'unique': 'cards'})
    hits = set()
    while url:
        try: d = get(url)
        except Exception: break   # 404: nothing matches
        hits |= {front(c['name']) for c in d['data']}; url = d.get('next_page'); time.sleep(0.12)
    return sorted(hits & pool)

def run(slug):
    J = json.load(open(os.path.join(ROOT, 'theme', slug + '.json')))
    T = THEMES[slug]
    h = open(os.path.join(ROOT, 'decks', T.get('precon', slug) + '.html')).read()
    box = json.loads(re.search(r'const ALL=(\[.*?\]);\n', h, re.S).group(1))
    boxn = {front(c['n']) for c in box}
    offered = {x['n'] for k in ('adds', 'cuts', 'lands', 'tutors', 'gcs', 'wins') for x in J.get(k, [])}
    sf = scry_collection(offered - boxn)
    info = {}
    for n in sorted(offered - boxn):
        c = sf.get(n)
        if not c: continue
        info[n] = {'mv': int(c.get('cmc', 0)), 'land': 'Land' in typeline(c).split(' // ')[0]}
    boxj = [{'n': front(c['n']), 'q': c.get('q', 1), 'mv': int(c.get('m') or 0), 'land': 'Land' in c['t'].split(' // ')[0],
             'basic': 'Basic' in c['t']} for c in box]
    pool = boxn | set(info)
    # Every pool card once (basics too: some combos name a basic type), the commander as commander.
    main = [{'card': n, 'quantity': 1} for n in sorted(pool) if n != J['cmd']]
    res = get(SB, {'main': main, 'commanders': [{'card': J['cmd'], 'quantity': 1}]})['results']['included']
    combos, tcache = [], {}
    for v in res:
        prods = [p['feature']['name'] for p in v.get('produces', [])]
        if not any(p.startswith('Infinite') for p in prods): continue
        req = []
        for r in v.get('requires', []):
            t = r['template']; q = t.get('scryfallQuery') or ''
            if q not in tcache: tcache[q] = template_cards(q, T['id'], pool) if q else []
            req.append({'t': t['name'], 'q': r.get('quantity', 1), 'opts': tcache[q]})
        combos.append({'id': v['id'], 'cards': [{'n': front(u['card']['name']), 'z': ''.join(u.get('zoneLocations') or ['B']),
                                                 'c': bool(u.get('mustBeCommander'))} for u in v['uses']],
                       'req': req, 'prods': prods, 'mana': v.get('manaNeeded') or '', 'mv': v.get('manaValueNeeded') or 0,
                       'tag': v.get('bracketTag') or ''})
    out = {'slug': slug, 'cmd': J['cmd'], 'date': time.strftime('%b %d, %Y').replace(' 0', ' '), 'box': boxj, 'info': info, 'combos': combos}
    json.dump(out, open(os.path.join(ROOT, 'theme', slug + '-combos.json'), 'w'), separators=(',', ':'))
    print(f'{slug}: pool {len(pool)} cards, {len(res)} Spellbook combos, {len(combos)} infinite')

if __name__ == '__main__':
    slugs = sys.argv[1:] or sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'theme', '*.json'))
                                   if re.fullmatch(r'[a-z-]+', os.path.basename(p)[:-5]) and os.path.basename(p) != 'index.json'
                                   and not p.endswith(('-review.json', '-combos.json')))
    for s in slugs: run(s)
