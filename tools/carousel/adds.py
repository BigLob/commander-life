"""Build adds/<slug>.html: the 20 cards players most often ADD to a precon (EDHREC's "Cards to Add" + "Lands to Add").
Same carousel as cuts/ (cuts-template.html with the caption line swapped). Card data comes from Scryfall.
Run from the repo root:  python3 tools/carousel/adds.py    (all decks)
"""
import datetime, html, json, os, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import DECKS, PREORDER, get, scryfall, record
TOP = 20
EDH_SLUG = {'borg': 'we-are-the-borg'}
OUT = os.path.join(ROOT, 'adds')

def build(slug, name, product, cmd, alt, src, today):
    es = EDH_SLUG.get(slug, slug)
    page = f'https://edhrec.com/precon/{es}'
    d = json.loads(get(f'https://json.edhrec.com/pages/precon/{es}.json'))
    decks = {c['value']: c['count'] for c in d['precon_commander_counts']}[cmd]
    L = {l['tag']: l['cardviews'] for l in d['container']['json_dict']['cardlists']}
    adds = sorted((c for t in ('cardstoadd', 'landstoadd') for c in L.get(t, [])), key=lambda c: -c['num_decks'])[:TOP]
    cards = scryfall([(1, {'name': c['name']}, c['name']) for c in adds])
    ALL = []
    for rank, (a, (_, c)) in enumerate(zip(adds, cards), 1):
        r = record(1, c)
        r.update(k=['Land' if 'Land' in c['type_line'] else 'Spell'] + c.get('keywords', []), r=rank,
                 x=round(a['num_decks'] / a['potential_decks'], 3),
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
        ALL.append(r)
    soon = PREORDER.get(product)
    srcs = (f'<p><b>Source:</b> <a href="{page}" target="_blank" rel="noopener">EDHREC, {html.escape(name)} precon page</a>, read {today:%b %-d, %Y}. '
            f'{decks:,} decks on deck sites started from this precon with {html.escape(cmd)} as commander; its "Cards to Add" and "Lands to Add" lists give the share of them playing each card that is <i>not</i> in the box. '
            f'Top {TOP} of both lists merged, by that share. Card data and prices from Scryfall.</p>'
            + (f'<p><b>Not out yet</b> ({soon.split(", ")[1]}): built online from the announced list, so the numbers will shift.</p>' if soon else '')
            + (f'<p><b>Small sample:</b> only {decks:,} decks so far, so treat the order as rough.</p>' if decks < 300 else ''))
    cfg = {'slug': 'adds-' + slug, 'deck': name + ': most added', 'set': product, 'cmd': cmd, 'alt': alt, 'decks': decks, 'edh': page, 'srcs': srcs,
           'sub': f'{html.escape(product)} · <b>{html.escape(cmd)}</b> · {TOP} most added of {decks:,} decks on EDHREC · <a href="../decks/{slug}.html">full deck ›</a>'}
    t = open(os.path.join(HERE, 'cuts-template.html')).read()
    t = t.replace('<b>#${c.r} most cut</b> · cut from ${pct(c.x)}', '<b>#${c.r} most added</b> · added to ${pct(c.x)}')
    t = (t.replace('__TITLE__', html.escape(name + ': most added')).replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, slug + '.html'), 'w').write(t)
    print(slug, decks, ', '.join(f'{c["n"]} {c["x"]:.0%}' for c in ALL[:3]), flush=True)
    time.sleep(0.5)
    return {'slug': slug, 'name': name, 'product': product, 'decks': decks, 'top': ALL[0]['n'], 'topx': ALL[0]['x'], 'img': ALL[0]['i']}

def index(meta):
    groups = {}
    for d in DECKS:
        if d[0] in meta: groups.setdefault(d[2], []).append(meta[d[0]])
    sec = []
    for product, ds in groups.items():
        cards = ''.join(f'''<a class="deck" href="{d['slug']}.html"><img src="{d['img']}" alt="{html.escape(d['top'])}" loading="lazy" referrerpolicy="no-referrer"><span class="nm">{html.escape(d['name'])}</span><small>Most added: {html.escape(d['top'])} ({round(d['topx'] * 100)}%)</small><small class="pr">{d['decks']:,} decks on EDHREC</small></a>''' for d in ds)
        tag = f'<span class="tag">{PREORDER[product]}</span>' if product in PREORDER else ''
        sec.append(f'<section><h2>{html.escape(product)}{tag}</h2><div class="grid">{cards}</div></section>')
    page = (open(os.path.join(HERE, 'index-template.html')).read()
            .replace('<title>Our Precons</title>', '<title>Most Added Cards</title>')
            .replace('<h1>Our precons</h1>', '<h1>Most added to our precons</h1>')
            .replace('<p class="sub">Tap a deck to swipe through its 100 cards. Fav, Bench and Trash marks stay on this phone.</p>',
                     f'<p class="sub">The {TOP} cards players most often add to each deck, from EDHREC\'s precon pages. Tap a deck to swipe through them.</p>')
            .replace('<!--DECKS-->', ''.join(sec)))
    open(os.path.join(OUT, 'index.html'), 'w').write(page)

if __name__ == '__main__':
    want = sys.argv[1:]
    today = datetime.date.today()
    meta = {}
    for d in DECKS:
        meta[d[0]] = build(*d, today)
    index(meta)
