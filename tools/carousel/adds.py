"""Build adds/<slug>.html: the 20 cards players most often ADD to a precon (EDHREC's "Cards to Add" + "Lands to Add").
Same carousel as cuts/ (cuts-template.html with the caption line swapped). Card data comes from Scryfall.
Run from the repo root:  python3 tools/carousel/adds.py [slug]   (default living-energy)
"""
import datetime, html, json, os, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import DECKS, get, scryfall, record
TOP = 20
slug = sys.argv[1] if len(sys.argv) > 1 else 'living-energy'
name, product, cmd, alt = next(d[1:5] for d in DECKS if d[0] == slug)
page = f'https://edhrec.com/precon/{slug}'
d = json.loads(get(f'https://json.edhrec.com/pages/precon/{slug}.json'))
decks = {c['value']: c['count'] for c in d['precon_commander_counts']}[cmd]
L = {l['tag']: l['cardviews'] for l in d['container']['json_dict']['cardlists']}
adds = sorted((c for t in ('cardstoadd', 'landstoadd') for c in L[t]), key=lambda c: -c['num_decks'])[:TOP]
cards = scryfall([(1, {'name': c['name']}, c['name']) for c in adds])
ALL = []
for rank, (a, (_, c)) in enumerate(zip(adds, cards), 1):
    r = record(1, c)
    r.update(k=['Land'] if 'Land' in c['type_line'] else ['Spell'], r=rank, x=round(a['num_decks'] / a['potential_decks'], 3),
             u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
    r['k'] = r['k'] + c.get('keywords', [])
    ALL.append(r)
today = datetime.date.today()
srcs = (f'<p><b>Source:</b> <a href="{page}" target="_blank" rel="noopener">EDHREC, {html.escape(name)} precon page</a>, read {today:%b %-d, %Y}. '
        f'{decks:,} decks on deck sites started from this precon with {html.escape(cmd)} as commander; its "Cards to Add" and "Lands to Add" lists give the share of them playing each card that is <i>not</i> in the box. '
        f'Top {TOP} of both lists merged, by that share. Card data and prices from Scryfall.</p>')
cfg = {'slug': 'adds-' + slug, 'deck': name + ': most added', 'set': product, 'cmd': cmd, 'alt': alt, 'decks': decks, 'edh': page, 'srcs': srcs,
       'sub': f'{html.escape(product)} · <b>{html.escape(cmd)}</b> · {TOP} most added of {decks:,} decks on EDHREC · <a href="../decks/{slug}.html">full deck ›</a>'}
t = open(os.path.join(HERE, 'cuts-template.html')).read()
t = t.replace('<b>#${c.r} most cut</b> · cut from ${pct(c.x)}', '<b>#${c.r} most added</b> · added to ${pct(c.x)}')
t = (t.replace('__TITLE__', html.escape(name + ': most added')).replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
      .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
os.makedirs(os.path.join(ROOT, 'adds'), exist_ok=True)
open(os.path.join(ROOT, 'adds', slug + '.html'), 'w').write(t)
for c in ALL: print(c['r'], c['n'], f"{c['x']:.0%}", c['t'], c['m'], c['c'], c['p'], c.get('note', ''), flush=True)
