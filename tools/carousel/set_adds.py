"""Build setadds/<slug>.html: the 10 cards from a precon's release set (the main set that came out with it)
that players most often add to it, plus setadds/index.html.

Why the commander page and not the precon page: EDHREC's precon page only lists about 60 adds, so a set filter leaves
two or three. Its commander page lists about 250 cards (everything played in at least ~5% of that commander's decks),
so the set's cards that matter show up there. Cards already in the precon are left out. Reprints in the set count
(a shockland opened in a Star Trek booster is still from the set). The Starter Commander Decks (2022) came out with no
main set, so they have no page.
Same carousel as cuts/ and adds/ (cuts-template.html with the caption line swapped). Card data comes from Scryfall.
Run from the repo root:  python3 tools/carousel/set_adds.py
"""
import manacost
import datetime, html, json, os, re, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import DECKS, PREORDER, get, scryfall, record
TOP = 10
# precon product -> (Scryfall code, name) of the main set released alongside it
SETS = {'Star Trek Commander (2026)': ('trk', 'Star Trek'),
        'Secrets of Strixhaven Commander (2026)': ('sos', 'Secrets of Strixhaven'),
        'Aetherdrift Commander (2025)': ('dft', 'Aetherdrift'),
        'Final Fantasy Commander (2025)': ('fin', 'Final Fantasy')}
OUT = os.path.join(ROOT, 'setadds')
_names = {}

def set_names(code):
    """Every card name with a paper printing in the set."""
    if code not in _names:
        s, u = set(), 'https://api.scryfall.com/cards/search?q=' + urllib.parse.quote(f'e:{code} game:paper') + '&unique=cards'
        while u:
            d = json.loads(get(u)); s |= {c['name'] for c in d['data']}; u = d.get('next_page'); time.sleep(0.12)
        _names[code] = s
    return _names[code]

def edh_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower().replace("'", '').replace(',', '')).strip('-')

def precon_cards(slug):
    t = open(os.path.join(ROOT, 'decks', slug + '.html')).read()
    return {c['n'] for c in json.loads(re.search(r'const ALL=(\[.*?\]);\n', t).group(1))}

def build(slug, name, product, cmd, alt, src, today):
    code, setname = SETS[product]
    page = f'https://edhrec.com/commanders/{edh_slug(cmd)}'
    d = json.loads(get(f'https://json.edhrec.com/pages/commanders/{edh_slug(cmd)}.json'))
    seen = {}
    for l in d['container']['json_dict']['cardlists']:
        for c in l['cardviews']: seen.setdefault(c['name'], c)
    own, inset = precon_cards(slug), set_names(code)
    pool = sorted((c for n, c in seen.items() if n in inset and n not in own), key=lambda c: -c['num_decks'] / c['potential_decks'])
    cards = scryfall([(1, {'name': c['name'], 'set': code}, c['name']) for c in pool])  # the set's own printing
    ALL, illegal = [], []
    for a, (_, c) in zip(pool, cards):
        if c.get('legalities', {}).get('commander') != 'legal':  # house rule: cards meant to be played are legal ones only
            illegal.append(c['name']); continue
        if len(ALL) == TOP: break
        r = record(1, c)
        r.update(k=['Land' if 'Land' in c['type_line'] else 'Spell'] + c.get('keywords', []), r=len(ALL) + 1,
                 x=round(a['num_decks'] / a['potential_decks'], 3), d=a['potential_decks'],
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
        ALL.append(r)
    decks = max((c['potential_decks'] for c in seen.values()), default=0)
    soon = PREORDER.get(product)
    srcs = (f'<p><b>Source:</b> <a href="{page}" target="_blank" rel="noopener">EDHREC, {html.escape(cmd)} commander page</a>, read {today:%b %-d, %Y}. '
            f'It lists every card played in at least about 5% of the {decks:,} {html.escape(cmd)} decks EDHREC has found on deck sites (built from the precon or not). '
            f'Kept: cards with a printing in {html.escape(setname)} (Scryfall set {code.upper()}, reprints included) that are not in the precon, sorted by the share of decks playing them, top {TOP}. '
            f'The share under each card is out of the decks that could play it (the right colors). Card data and prices from Scryfall, shown in their {html.escape(setname)} printing.</p>'
            + (f'<p><b>Only {len(ALL)}:</b> no other {html.escape(setname)} card is played in enough {html.escape(cmd)} decks for EDHREC to list it.</p>' if len(ALL) < TOP else '')
            + (f'<p><b>Left out, not Commander-legal:</b> {html.escape(", ".join(illegal))}.</p>' if illegal else '')
            + (f'<p><b>Just out</b> ({soon.split(", ")[1]}): most decks were built from the announced list, so the numbers will shift.</p>' if soon else ''))
    cfg = {'slug': 'setadds-' + slug, 'deck': f'{name}: top {setname} adds', 'set': product, 'cmd': cmd, 'alt': alt, 'decks': decks, 'edh': page, 'srcs': srcs,
           'sub': f'{html.escape(product)} · <b>{html.escape(cmd)}</b> · the {len(ALL)} {html.escape(setname)} cards most added · <a href="../decks/{slug}.html">full deck ›</a>'}
    t = open(os.path.join(HERE, 'cuts-template.html')).read()
    old_why = '<b>#${c.r} most cut</b> · cut from ${pct(c.x)} of ${CFG.decks.toLocaleString(\'en-US\')} decks'
    assert old_why in t
    t = t.replace(old_why, '<b>#${c.r} from ' + html.escape(setname) + '</b> · in ${pct(c.x)} of ${c.d.toLocaleString(\'en-US\')} decks')
    t = t.replace('>Most cut first<', '>Most played first<')
    t = (t.replace('__TITLE__', html.escape(f'{name}: top {setname} adds')).replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(manacost.fill(ALL), ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, slug + '.html'), 'w').write(t)
    print(slug, setname, len(ALL), ', '.join(f'{c["n"]} {c["x"]:.0%}' for c in ALL), ('| illegal: ' + ', '.join(illegal)) if illegal else '', flush=True)
    time.sleep(0.5)
    return {'slug': slug, 'name': name, 'product': product, 'setname': setname, 'n': len(ALL), 'top': ALL[0]['n'], 'topx': ALL[0]['x'], 'img': ALL[0]['i']}

def index(meta):
    groups = {}
    for d in DECKS:
        if d[0] in meta: groups.setdefault(d[2], []).append(meta[d[0]])
    sec = []
    for product, ds in groups.items():
        cards = ''.join(f'''<a class="deck" href="{d['slug']}.html"><img src="{d['img']}" alt="{html.escape(d['top'])}" loading="lazy" referrerpolicy="no-referrer"><span class="nm">{html.escape(d['name'])}</span><small>Top: {html.escape(d['top'])} ({round(d['topx'] * 100)}%)</small><small class="pr">{d['n']} cards from {html.escape(d['setname'])}</small></a>''' for d in ds)
        tag = f'<span class="tag">{PREORDER[product]}</span>' if product in PREORDER else ''
        sec.append(f'<section><h2>{html.escape(product)} · from {html.escape(SETS[product][1])}{tag}</h2><div class="grid">{cards}</div></section>')
    page = (open(os.path.join(HERE, 'index-template.html')).read()
            .replace('<title>Our Precons</title>', '<title>Top Release-Set Adds</title>')
            .replace('<h1>Our precons</h1>', '<h1>Top adds from each precon\'s set</h1>')
            .replace('<p class="sub">Tap a deck to swipe through its 100 cards. Fav, Bench and Trash marks stay on this phone.</p>',
                     f'<p class="sub">The {TOP} cards from the set each precon came out with that players most often add to it (EDHREC). The Starter decks (2022) had no set of their own, so they aren\'t here.</p>')
            .replace('<!--DECKS-->', ''.join(sec)))
    open(os.path.join(OUT, 'index.html'), 'w').write(page)

if __name__ == '__main__':
    today = datetime.date.today()
    meta = {}
    for d in DECKS:
        if d[2] in SETS: meta[d[0]] = build(*d, today)
    index(meta)
