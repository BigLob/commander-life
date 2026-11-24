"""Build a carousel of the 15 cards most often cut from each precon we own: cuts/<slug>.html plus cuts/index.html.

Source: EDHREC's precon page for the deck (json.edhrec.com/pages/precon/<edhrec slug>.json), whose "Cards to
Cut" and "Lands to Cut" lists give, for each precon card, the share of decks EDHREC matched to this precon (with
its face commander) that no longer play it ("unpopularity"). Both lists are merged and the 15 highest kept, lands
included, since cutting a tapped land is as real a cut as cutting a spell.
Card data (image, price, type, legality note) is reused from decks/<slug>.html, built by make.py, so run that first.
Run from the repo root:  python3 tools/carousel/cuts.py [slug ...]
"""
import datetime, html, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
OUT = os.path.join(ROOT, 'cuts')
sys.path.insert(0, HERE)
from make import DECKS, PREORDER  # same decks, same order, same products

TOP = 15
EDH_SLUG = {'borg': 'we-are-the-borg'}  # where EDHREC's slug differs from ours
UA = {'User-Agent': 'commander-life/1.0', 'Accept': 'application/json'}

def get(url):
    for i in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception:
            if i == 3: raise
            time.sleep(2 ** i)

def deck_cards(slug):
    """The deck page's card records, by name and by front-face name."""
    page = open(os.path.join(ROOT, 'decks', slug + '.html')).read()
    recs = json.loads(re.search(r'const ALL=(\[.*?\]);\n', page).group(1))
    by = {}
    for r in recs:
        by[r['n']] = r
        by[r['n'].split(' // ')[0]] = r
    return by

def build(slug, name, product, cmd, alt, src, today):
    es = EDH_SLUG.get(slug, slug)
    edh_page = f'https://edhrec.com/precon/{es}'
    d = json.loads(get(f'https://json.edhrec.com/pages/precon/{es}.json'))
    counts = {c['value']: c['count'] for c in d.get('precon_commander_counts') or []}
    decks = counts.get(cmd)
    if decks is None: raise SystemExit(f'{slug}: EDHREC has no {cmd} count for this precon: {list(counts)}')
    lists = {l['tag']: l['cardviews'] for l in d['container']['json_dict']['cardlists']}
    cuts = [(c['unpopularity'], c['name'], 'Land' if tag == 'landstocut' else 'Spell')
            for tag in ('cardstocut', 'landstocut') for c in lists.get(tag, [])]
    cuts.sort(key=lambda x: -x[0])
    cards = deck_cards(slug)
    ALL = []
    for rank, (x, n, kind) in enumerate(cuts[:TOP], 1):
        r = cards.get(n) or cards.get(n.split(' // ')[0])
        if r is None: raise SystemExit(f'{slug}: EDHREC cut "{n}" is not on decks/{slug}.html')
        r = dict(r, k=[kind], r=rank, x=round(x, 3),
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{r["n"]}"'))
        ALL.append(r)
    out_of = len(cuts)
    alt_n = counts.get(alt) if alt else None
    soon = PREORDER.get(product)
    srcs = (f'<p><b>Source:</b> <a href="{edh_page}" target="_blank" rel="noopener">EDHREC, {html.escape(name)} precon page</a>, '
            f'read {today:%b %-d, %Y}. EDHREC finds decklists on deck sites (Moxfield, Archidekt and others) that started from this precon '
            f'with {html.escape(cmd)} as commander: {decks:,} of them. Its "Cards to Cut" and "Lands to Cut" lists give, for each card the '
            f'precon came with, the share of those decks that took it out.</p>'
            f'<p><b>How this list was made:</b> both lists merged ({out_of} cards), sorted by that share, top {TOP} kept. Lands count as cuts too. '
            f'The share is under each card ("cut from {round(ALL[0]["x"] * 100)}% of {decks:,} decks"). The cards themselves, prices included, come from '
            f'<a href="../decks/{slug}.html">our {html.escape(name)} carousel</a> (Scryfall).</p>'
            + (f'<p><b>Alt commander:</b> {html.escape(alt)} decks ({alt_n or 0:,} on EDHREC) are counted separately and not in this list.</p>' if alt else '')
            + (f'<p><b>Not out yet</b> ({soon.split(", ")[1]}): these decks were built online from the announced list, so the numbers will shift once people play it.</p>' if soon else '')
            + (f'<p><b>Small sample:</b> only {decks:,} decks so far, so treat the order as rough.</p>' if decks < 300 else ''))
    cfg = {'slug': 'cuts-' + slug, 'deck': name + ': most cut', 'set': product, 'cmd': cmd, 'alt': alt, 'decks': decks,
           'edh': edh_page, 'srcs': srcs,
           'sub': f'{html.escape(product)} · <b>{html.escape(cmd)}</b> · {TOP} most cut of {decks:,} decks on EDHREC · <a href="../decks/{slug}.html">full deck ›</a>'}
    t = open(os.path.join(HERE, 'cuts-template.html')).read()
    t = (t.replace('__TITLE__', html.escape(name + ': most cut')).replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, slug + '.html'), 'w').write(t)
    print(f'{slug}: {decks} decks; ' + ', '.join(f'{c["n"]} {round(c["x"] * 100)}%' for c in ALL), flush=True)
    time.sleep(0.5)
    return {'slug': slug, 'name': name, 'product': product, 'cmd': cmd, 'decks': decks, 'top': ALL[0]['n'], 'topx': ALL[0]['x'],
            'img': ALL[0]['i'], 'edh': edh_page, 'date': f'{today:%Y-%m-%d}'}

def index(meta):
    """cuts/index.html: every deck, grouped by product, each card showing its most-cut card."""
    groups = {}
    for d in DECKS:
        if d[0] in meta: groups.setdefault(d[2], []).append(meta[d[0]])
    sec = []
    for product, ds in groups.items():
        cards = ''.join(f'''<a class="deck" href="{d['slug']}.html"><img src="{d['img']}" alt="{html.escape(d['top'])}" loading="lazy" referrerpolicy="no-referrer"><span class="nm">{html.escape(d['name'])}</span><small>Most cut: {html.escape(d['top'])} ({round(d['topx'] * 100)}%)</small><small class="pr">{d['decks']:,} decks on EDHREC</small></a>''' for d in ds)
        tag = f'<span class="tag">{PREORDER[product]}</span>' if product in PREORDER else ''
        sec.append(f'<section><h2>{html.escape(product)}{tag}</h2><div class="grid">{cards}</div></section>')
    page = (open(os.path.join(HERE, 'index-template.html')).read()
            .replace('<title>Our Precons</title>', '<title>Most Cut Cards</title>')
            .replace('<h1>Our precons</h1>', '<h1>Most cut from our precons</h1>')
            .replace('<p class="sub">Tap a deck to swipe through its 100 cards. Fav, Bench and Trash marks stay on this phone.</p>',
                     f'<p class="sub">The {TOP} cards players most often take out of each deck, from EDHREC\'s precon pages. Tap a deck to swipe through them; each card says how many decks cut it.</p>')
            .replace('<!--DECKS-->', ''.join(sec)))
    open(os.path.join(OUT, 'index.html'), 'w').write(page)

if __name__ == '__main__':
    want = sys.argv[1:]
    today = datetime.date.today()
    meta_path = os.path.join(OUT, 'cuts.json')
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for d in DECKS:
        if not want or d[0] in want:
            meta[d[0]] = build(*d, today)
    os.makedirs(OUT, exist_ok=True)
    json.dump(meta, open(meta_path, 'w'), indent=1, ensure_ascii=False)
    index(meta)
