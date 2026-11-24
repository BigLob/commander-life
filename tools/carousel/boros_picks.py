"""Two carousels per commander the user marked Fav on boros/ (read from the shared table, tables/t7q2xm4k-picks/commander-life_boros; SELECT below):
  boros/<slug>-deck.html   the way brews/ collects cards: EDHREC's average deck, 100 cards, with each card's EDHREC share and synergy (brew-template.html)
  boros/<slug>-more.html   the way adds/ collects cards: the next most-played cards EDHREC has for the commander that are NOT in the average deck (cuts-template.html)
Run from the repo root:  python3 tools/carousel/boros_picks.py
"""
import manacost
import html, json, os, re, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from brew import get, cheapest
OUT = os.path.join(ROOT, 'boros')
SELECT = ['Mabel, Heir to Cragflame', 'Firesong and Sunspeaker']  # Fav marks on boros/ (Nov 23, 2026); Thorin was benched
MORE = 30
EDH = 'https://json.edhrec.com/pages'

def slug(n): return re.sub(r'[^a-z0-9]+', '-', n.lower().replace("'", '')).strip('-')

def cards(names):
    found = {}
    for i in range(0, len(names), 75):
        r = get('https://api.scryfall.com/cards/collection', json.dumps({'identifiers': [{'name': n} for n in names[i:i + 75]]}).encode())
        for c in r['data']: found[c['name']] = found[c['name'].split(' // ')[0]] = c
        time.sleep(0.15)
    return found

def rec(n, c, q=1, k=None):
    faces = c.get('card_faces') or []
    iu = c.get('image_uris') or faces[0]['image_uris']
    colors = c.get('colors', faces[0].get('colors', []) if faces else [])
    r = {'n': n, 'p': cheapest(n), 'q': q, 's': c['set'].upper(), 't': c['type_line'], 'i': iu['normal'], 'm': int(c.get('cmc', 0)),
         'c': ''.join(x for x in 'WUBRG' if x in colors), 'k': k or [], 'u': c['scryfall_uri'].split('?')[0]}
    if c['legalities'].get('commander') != 'legal': r['note'] = 'Not Commander-legal'  # house rule: always flagged
    if len(faces) > 1 and not c.get('image_uris'): r['b'] = faces[1]['image_uris']['normal']
    return r

def build(cmd):
    s = slug(cmd.split(' // ')[0]); edh_page = f'https://edhrec.com/commanders/{s}'
    page = get(f'{EDH}/commanders/{s}.json')['container']['json_dict']
    decks = page['card']['num_decks']
    stats = {}
    for l in page['cardlists']:
        for v in l['cardviews']: stats.setdefault(v['name'], (v['num_decks'] / v['potential_decks'], v['synergy']))
    avg = get(f'{EDH}/average-decks/{s}.json')['deck']
    lst = [(avg['commander'][0], 1, 'Commander')] + [(n, q, t) for t, cs in avg['cards'].items() for n, q in cs]
    assert sum(q for _, q, _ in lst) == 100, sum(q for _, q, _ in lst)
    inavg = {n for n, _, _ in lst}
    # more options: everything on the commander page that isn't in the average deck, most played first (no basics)
    opts = {}
    for l in page['cardlists']:
        if l['tag'] in ('newcards', 'highliftcards'): continue
        for v in l['cardviews']:
            if v['name'] not in inavg and v['name'] not in ('Plains', 'Mountain'): opts[v['name']] = v
    top = sorted(opts.values(), key=lambda v: -v['num_decks'] / v['potential_decks'])[:MORE]
    found = cards([n for n, _, _ in lst] + [v['name'] for v in top])
    ALL = []
    for n, q, t in lst:
        r = rec(n, found[n], q, [t]); st = stats.get(n)
        r['e'] = [round(st[0], 3), round(st[1], 3)] if st else [1, 0] if t == 'Commander' else None
        if r['e'] is None: del r['e']
        ALL.append(r)
    order = ['Commander', 'Creature', 'Instant', 'Sorcery', 'Artifact', 'Enchantment', 'Planeswalker', 'Battle', 'Land']
    ALL.sort(key=lambda r: (order.index(r['k'][0]) if r['k'][0] in order else 99, -(r['e'][0] if 'e' in r else 0)))
    total = sum((r['p'] or 0) * r['q'] for r in ALL)
    nm = cmd.split(',')[0]
    srcs = (f'<p><b>The list</b> is <a href="https://edhrec.com/average-decks/{s}" target="_blank" rel="noopener">EDHREC\'s average {html.escape(nm)} deck</a>: '
            f'the cards played most across the {decks:,} {html.escape(nm)} decks EDHREC has (pulled {time.strftime("%b %-d %Y")}), 100 cards. '
            f'Same way as the <a href="../brews/camellia-lenn.html">brews</a>, but here the label under each card is its type, not a hand-written role.</p>'
            f'<p><b>Under each card</b>: EDHREC\'s share of {html.escape(nm)} decks that play it, and synergy (how much more often it is played here than in other Boros decks; near 0% is a generic staple). '
            f'<a href="{s}-more.html">More options</a> lists the next most-played cards that are not in this list.</p><p><b>Prices</b> are the cheapest paper printing on Scryfall.</p>')
    cfg = {'slug': f'boros-{s}-deck', 'deck': f'{nm}: average deck', 'set': '', 'cmd': lst[0][0], 'alt': None, 'decks': decks, 'edh': edh_page, 'srcs': srcs,
           'sub': f'100 cards · ${total:,.0f} in singles · from {decks:,} decks on EDHREC'}
    t = open(os.path.join(HERE, 'brew-template.html'), encoding='utf-8').read()
    t = (t.replace('__TITLE__', html.escape(cfg['deck'])).replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(manacost.fill(ALL), ensure_ascii=False, separators=(',', ':'))))
    open(os.path.join(OUT, f'{s}-deck.html'), 'w', encoding='utf-8', newline='\n').write(t)
    # the options carousel
    MO = []
    for v in top:
        r = rec(v['name'], found[v['name']], 1, [v['name'] and next(l['header'] for l in page['cardlists'] if v in l['cardviews'])])
        r.update(r=len(MO) + 1, x=0, sh=round(100 * v['num_decks'] / v['potential_decks']), sy=round(100 * v['synergy']))
        MO.append(r)
    cfg2 = {'slug': f'boros-{s}-more', 'deck': f'{nm}: more options', 'set': '', 'cmd': lst[0][0], 'alt': '', 'decks': decks, 'edh': edh_page,
            'srcs': (f'<p><b>Source:</b> EDHREC\'s <a href="{edh_page}" target="_blank" rel="noopener">{html.escape(nm)} page</a>, pulled {time.strftime("%b %-d %Y")}: the {MORE} most-played cards '
                     f'(share of {decks:,} decks) that are not in the <a href="{s}-deck.html">average deck</a>. Basic lands left out.</p>'),
            'sub': f'The {MORE} most-played cards not in the average deck · {decks:,} decks on EDHREC'}
    t = open(os.path.join(HERE, 'cuts-template.html'), encoding='utf-8').read()
    old = "<b>#${c.r} most cut</b> · cut from ${pct(c.x)} of ${CFG.decks.toLocaleString('en-US')} decks"
    assert old in t
    t = t.replace(old, "<b>#${c.r} of " + str(MORE) + "</b> · in ${c.sh}% of decks · synergy ${c.sy>0?'+':''}${c.sy}%")
    t = (t.replace('__TITLE__', html.escape(cfg2['deck'])).replace('/*CFG*/null', json.dumps(cfg2, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(manacost.fill(MO), ensure_ascii=False, separators=(',', ':'))))
    open(os.path.join(OUT, f'{s}-more.html'), 'w', encoding='utf-8', newline='\n').write(t)
    print(s, len(ALL), f'${total:.0f}', 'no price', [r['n'] for r in ALL + MO if r['p'] is None], [r['n'] for r in MO][:5])
    return s, nm

if __name__ == '__main__':
    for c in SELECT: build(c)
