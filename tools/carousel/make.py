"""Build a review carousel page for every precon we own: decks/<slug>.html plus decks/index.html.

Decklists: MTGJSON's deck files (exact printings), or, for decks MTGJSON doesn't have yet (Star Trek,
Nov 2026), Wizards' decklist article. Card data, prices and image links come from Scryfall.
Run from the repo root:  python3 tools/carousel/make.py [slug ...]
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'decks')
UA = {'User-Agent': 'commander-life/1.0', 'Accept': 'application/json'}
ST = 'https://magic.wizards.com/en/news/announcements/star-trek-commander-decklists'

# slug, deck name, product, commander, alt commander, source (MTGJSON file or Wizards deck title)
DECKS = [
    ('borg', 'We Are the Borg', 'Star Trek Commander (2026)', 'The Borg Queen', 'Locutus of Borg', ('wotc', 'We Are the Borg', 'trc')),
    ('federation-fleet', 'Federation Fleet', 'Star Trek Commander (2026)', 'Jean-Luc Picard, Luminary', 'Captain Janeway, Endgame', ('wotc', 'Federation Fleet', 'trc')),
    ('landing-party', 'Landing Party', 'Star Trek Commander (2026)', 'Commander Spock', 'Captain Kirk, Boldly Going', ('wotc', 'Landing Party', 'trc')),
    ('klingon-fury', 'Klingon Fury', 'Star Trek Commander (2026)', 'Worf, Defiant Commander', 'Kor, Cause of Vengeance', ('wotc', 'Klingon Fury', 'trc')),
    ('silverquill-influence', 'Silverquill Influence', 'Secrets of Strixhaven Commander (2026)', 'Killian, Decisive Mentor', 'Scriv, the Obligator', ('mtgjson', 'SilverquillInfluence_SOC')),
    ('lorehold-spirit', 'Lorehold Spirit', 'Secrets of Strixhaven Commander (2026)', 'Quintorius, History Chaser', 'Excava, the Risen Past', ('mtgjson', 'LoreholdSpirit_SOC')),
    ('living-energy', 'Living Energy', 'Aetherdrift Commander (2025)', 'Saheeli, Radiant Creator', 'Pia Nalaar, Chief Mechanic', ('mtgjson', 'LivingEnergy_DRC')),
    ('eternal-might', 'Eternal Might', 'Aetherdrift Commander (2025)', "Temmet, Naktamun's Will", "Hashaton, Scarab's Fist", ('mtgjson', 'EternalMight_DRC')),
    ('revival-trance', 'Revival Trance', 'Final Fantasy Commander (2025)', 'Terra, Herald of Hope', 'Celes, Rune Knight', ('mtgjson', 'RevivalTranceFinalFantasyVi_FIC')),
    ('first-flight', 'First Flight', 'Starter Commander Decks (2022)', 'Isperia, Supreme Judge', None, ('mtgjson', 'FirstFlight_SCD')),
    ('grave-danger', 'Grave Danger', 'Starter Commander Decks (2022)', 'Gisa and Geralf', None, ('mtgjson', 'GraveDanger_SCD')),
    ('chaos-incarnate', 'Chaos Incarnate', 'Starter Commander Decks (2022)', 'Kardur, Doomscourge', None, ('mtgjson', 'ChaosIncarnate_SCD')),
    ('draconic-destruction', 'Draconic Destruction', 'Starter Commander Decks (2022)', 'Atarka, World Render', None, ('mtgjson', 'DraconicDestruction_SCD')),
    ('token-triumph', 'Token Triumph', 'Starter Commander Decks (2022)', 'Emmara, Soul of the Accord', None, ('mtgjson', 'TokenTriumph_SCD')),
]

def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers=dict(UA, **({'Content-Type': 'application/json'} if data else {})))
    for i in range(4):
        try:
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:
            if i == 3: raise
            time.sleep(2 ** i)

_wotc = None
def decklist(src):
    """[(qty, identifier)] where identifier is a Scryfall collection identifier."""
    global _wotc
    if src[0] == 'mtgjson':
        d = json.loads(get(f'https://mtgjson.com/api/v5/decks/{src[1]}.json'))['data']
        return [(c['count'], {'set': c['setCode'].lower(), 'collector_number': c['number']}, c['name'])
                for c in d['commander'] + d['mainBoard']]
    if _wotc is None:
        _wotc = html.unescape(get(ST).decode())
    m = re.search(r'deck-title="%s"[^>]*>(.*?)</deck-list>' % re.escape(src[1]), _wotc, re.S)
    main = re.search(r'<main-deck>(.*?)</main-deck>', m.group(1), re.S).group(1)
    out = []
    for line in filter(None, (l.strip() for l in main.splitlines())):
        q = re.match(r'^(\d+) (.+?)( \[.*\])?$', line)
        qty, name = (int(q.group(1)), q.group(2)) if q else (1, line)
        out.append((qty, {'name': name, 'set': src[2]}, name))
    return out

def scryfall(lst):
    cards = []
    for i in range(0, len(lst), 75):
        chunk = lst[i:i + 75]
        r = json.loads(get('https://api.scryfall.com/cards/collection', json.dumps({'identifiers': [x[1] for x in chunk]}).encode()))
        time.sleep(0.15)
        found = {}
        for c in r['data']:
            found[(c['set'], c['collector_number'])] = c
            found[c['name']] = c
            found[c['name'].split(' // ')[0]] = c
        for qty, ident, name in chunk:
            c = found.get((ident.get('set'), ident.get('collector_number'))) or found.get(name)
            if c is None:  # not in the expected set (a reprint from another set): any printing
                c = json.loads(get('https://api.scryfall.com/cards/named?exact=' + urllib.parse.quote(name)))
                time.sleep(0.15)
            cards.append((qty, c))
    return cards

def cheapest(name):
    q = urllib.parse.quote(f'!"{name}" game:paper')
    try:
        r = json.loads(get(f'https://api.scryfall.com/cards/search?q={q}&unique=prints&order=usd&dir=asc'))
        ps = [float(x['prices']['usd']) for x in r['data'] if x.get('prices', {}).get('usd')]
        return min(ps) if ps else None
    except Exception:
        return None
    finally:
        time.sleep(0.12)

def record(qty, c):
    faces = c.get('card_faces') or []
    iu = c.get('image_uris') or faces[0]['image_uris']
    back = faces[1]['image_uris']['normal'] if len(faces) > 1 and faces[1].get('image_uris') and not c.get('image_uris') else None
    colors = c.get('colors', faces[0].get('colors', []) if faces else [])
    p = c.get('prices', {}).get('usd')
    p = round(float(p), 2) if p else cheapest(c['name'])
    r = {'n': c['name'], 'p': p, 'q': qty, 's': c['set'].upper(), 't': c['type_line'], 'i': iu['normal'],
         'm': int(c.get('cmc', 0)), 'c': ''.join(x for x in 'WUBRG' if x in colors), 'k': c.get('keywords', [])}
    if back: r['b'] = back
    if c.get('legalities', {}).get('commander') != 'legal': r['note'] = 'Not Commander-legal'  # always flagged (house rule)
    return r

def build(slug, name, product, cmd, alt, src):
    lst = decklist(src)
    recs = {}
    for qty, c in scryfall(lst):  # the same card listed twice (e.g. basics from two printings) adds up
        r = record(qty, c)
        if r['n'] in recs: recs[r['n']]['q'] += qty
        else: recs[r['n']] = r
    ALL = list(recs.values())
    total = sum(r['q'] for r in ALL)
    rank = lambda r: 0 if r['n'] == cmd else 1 if r['n'] == alt else 3 if 'Basic Land' in r['t'] else 2 if 'Land' in r['t'] else 1.5
    ALL.sort(key=lambda r: (rank(r), -r['m'], -(r['p'] or 0)))
    t = open(os.path.join(HERE, 'template.html')).read()
    cfg = {'slug': slug, 'deck': name, 'set': product, 'cmd': cmd, 'alt': alt}
    t = (t.replace('__TITLE__', html.escape(name)).replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, slug + '.html'), 'w').write(t)
    missing = [r['n'] for r in ALL if r['p'] is None]
    print(f'{slug}: {total} cards, {len(ALL)} unique, ${sum((r["p"] or 0) * r["q"] for r in ALL):.2f}, no price: {len(missing)}', flush=True)
    return {'slug': slug, 'name': name, 'product': product, 'cmd': cmd, 'alt': alt, 'total': total,
            'price': round(sum((r['p'] or 0) * r['q'] for r in ALL), 2), 'img': next(r['i'] for r in ALL if r['n'] == cmd)}

PREORDER = {'Star Trek Commander (2026)': 'Preordered, out Nov 13'}

def index(meta):
    """decks/index.html: every deck, grouped by product in DECKS order, each linking to its carousel."""
    groups = {}
    for d in DECKS:
        if d[0] in meta: groups.setdefault(d[2], []).append(meta[d[0]])
    sec = []
    for product, ds in groups.items():
        cards = ''.join(f'''<a class="deck" href="{d['slug']}.html"><img src="{d['img']}" alt="{html.escape(d['cmd'])}" loading="lazy" referrerpolicy="no-referrer"><span class="nm">{html.escape(d['name'])}</span><small>{html.escape(d['cmd'])}{' · alt ' + html.escape(d['alt'].split(',')[0]) if d['alt'] else ''}</small><small class="pr">${d['price']:.2f} in singles</small></a>''' for d in ds)
        tag = f'<span class="tag">{PREORDER[product]}</span>' if product in PREORDER else ''
        sec.append(f'<section><h2>{html.escape(product)}{tag}</h2><div class="grid">{cards}</div></section>')
    page = open(os.path.join(HERE, 'index-template.html')).read().replace('<!--DECKS-->', ''.join(sec))
    open(os.path.join(OUT, 'index.html'), 'w').write(page)

if __name__ == '__main__':
    want = sys.argv[1:]
    meta_path = os.path.join(OUT, 'decks.json')
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for d in DECKS:
        if not want or d[0] in want:
            meta[d[0]] = build(*d)
    json.dump(meta, open(meta_path, 'w'), indent=1, ensure_ascii=False)
    index(meta)
