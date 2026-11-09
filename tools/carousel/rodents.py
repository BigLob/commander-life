"""Build rodents/index.html: every Magic card (and token) with a rat, mouse, squirrel or other rodent
in its creature type, name, rules text, flavor text or art.

Each search runs on Scryfall twice: once for each card's default printing (what the page shows), once
for every printing (flavor text and art differ between printings, and the price is the cheapest
matching paper printing). Art matches come from Scryfall Tagger's art tags (art:rat and so on), which
the community keeps; a printing whose art shows a rodent but was never tagged won't be found.
Run from the repo root:  python3 tools/carousel/rodents.py      (RODENTS_CACHE=<file> reuses the download)
"""
import collections, json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'rodents')
UA = {'User-Agent': 'commander-life/1.0', 'Accept': 'application/json'}

# Rodents only: rabbits, hedgehogs, moles, shrews, otters and the like aren't rodents and are left out.
TYPES = ['Rat', 'Mouse', 'Squirrel', 'Hamster', 'Beaver', 'Porcupine', 'Capybara']
ART = ['rat', 'mouse', 'squirrel', 'hamster', 'beaver', 'porcupine', 'capybara', 'chinchilla', 'gerbil', 'gopher', 'wererat']
WORDS = (r"\b(rats?|rat's|ratfolk|wererats?|ratcatchers?|ratlings?|rodents?|mouse|mice|mousers?|squirrels?|hamsters?|beavers?|"
         r"porcupines?|chipmunks?|capybaras?|gerbils?|marmots?|lemmings?|voles?|gophers?|chinchillas?|muskrats?|dormice|dormouse)\b")
# what each matched word or tag counts as, for the page's tabs: R rats, M mice, S squirrels, O other rodents
KIND = [(r'rat|ratfolk|ratcatcher|ratling|rodent', 'R'), (r'mouse|mice|mouser|dormouse|dormice', 'M'), (r'squirrel|chipmunk', 'S')]
EXTRA = ' include:extras -layout:art_series -st:memorabilia'
# Scryfall times out on one long regex, so each field is searched with three shorter ones
CHUNKS = [r'\b(rats?|ratfolk|wererats?|ratcatchers?|ratlings?|rodents?)\b',
          r'\b(mouse|mice|mousers?|squirrels?|hamsters?|beavers?|porcupines?|chipmunks?)\b',
          r'\b(capybaras?|gerbils?|marmots?|lemmings?|voles?|gophers?|chinchillas?|muskrats?|dormice|dormouse)\b']
SEARCHES = ([('T', f't:{t}') for t in TYPES] + [(w, f'{f}:/{x}/') for w, f in (('N', 'name'), ('X', 'o'), ('F', 'ft')) for x in CHUNKS]
            + [('A', f'art:{a}') for a in ART])

def get(url):
    for i in range(5):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read())
        except urllib.error.HTTPError as e:
            if e.code == 404: return {'data': []}  # no matches
            if e.code == 400: raise  # a bad query won't get better
            if i == 4: raise
            time.sleep(2 ** i)
        except Exception:
            if i == 4: raise
            time.sleep(2 ** i)

def search(q, extra=''):
    url, out = f'https://api.scryfall.com/cards/search?q={urllib.parse.quote(q + EXTRA)}{extra}', []
    while url:
        r = get(url)
        out += r['data']
        url = r.get('next_page')
        time.sleep(0.11)
    return out

def oid(c): return c.get('oracle_id') or c['card_faces'][0]['oracle_id']
def faces(c): return c.get('card_faces') or [c]
def kind_of(word):
    w = word.lower()
    return next((k for p, k in KIND if re.search(p, w)), 'O')

def fetch():
    cache = os.environ.get('RODENTS_CACHE')
    if cache and os.path.exists(cache): return json.load(open(cache))
    res = []
    for why, q in SEARCHES:
        tag = q.split(':', 1)[1] if why == 'A' else None
        res.append([why, tag, search(q, '&order=edhrec'), search(q, '&unique=prints&order=released')])
        print(q, len(res[-1][2]), 'cards', len(res[-1][3]), 'prints', flush=True)
    if cache: json.dump(res, open(cache, 'w'))
    return res

def main():
    res = fetch()
    default, prints, why, kinds, art_ok = {}, collections.defaultdict(dict), collections.defaultdict(set), collections.defaultdict(set), collections.defaultdict(set)
    for w, tag, cards, ps in res:
        for c in cards: default.setdefault(oid(c), c)
        for p in ps:
            o = oid(p)
            prints[o][p['id']] = p
            why[o].add(w)
            if w == 'A':
                art_ok[o].add(p['id']); kinds[o].add(kind_of(tag))
    ALL = []
    for o, c in default.items():
        if c['name'].startswith('A-'): continue  # Arena's rebalanced copies of a card already listed
        if c['name'].endswith(' Checklist'): continue  # a set's checklist card lists names, it isn't a rodent card
        ps = list(prints[o].values())
        # words that matched, for the tab (a type match is in the type line, names/text/flavor in their words)
        for p in ps:
            for f in faces(p):
                for fld in ('type_line', 'name', 'oracle_text', 'flavor_text'):
                    s = f.get(fld) or (p.get(fld) if fld != 'flavor_text' else None) or ''
                    if fld == 'type_line':
                        sub = s.split('—', 1)[1] if '—' in s else ''
                        for t in TYPES:
                            if re.search(r'\b' + t + r'\b', sub): kinds[o].add(kind_of(t))
                    else:
                        for m in re.finditer(WORDS, s, re.I): kinds[o].add(kind_of(m.group(1)))
        flav = [f.get('flavor_text') for p in ps for f in faces(p) if f.get('flavor_text') and re.search(WORDS, f['flavor_text'], re.I)]
        # show an art-tagged printing when the art is why it's here and the default printing isn't one
        show = c
        if 'A' in why[o] and c['id'] not in art_ok[o] and not why[o] & {'T', 'N', 'X'}:
            show = next((p for p in ps if p['id'] in art_ok[o] and not p.get('digital')), None) or next(p for p in ps if p['id'] in art_ok[o])
        fs = faces(show)
        iu = show.get('image_uris') or fs[0].get('image_uris')
        if not iu: continue
        cheap = [float(p['prices'].get('usd') or p['prices'].get('usd_foil')) for p in ps
                 if p['prices'].get('usd') or p['prices'].get('usd_foil')]
        colors = c.get('colors') if c.get('colors') is not None else fs[0].get('colors', [])
        r = {'n': c['name'], 't': c['type_line'], 's': show['set'].upper(), 'y': show['released_at'][:4], 'i': iu['normal'],
             'p': min(cheap) if cheap else None, 'r': c.get('edhrec_rank'), 'c': ''.join(x for x in 'WUBRG' if x in colors),
             'a': ''.join(k for k in 'RMSO' if k in kinds[o]) or 'O', 'w': ''.join(k for k in 'TNXFA' if k in why[o])}
        if len(fs) > 1 and not show.get('image_uris') and fs[1].get('image_uris'): r['b'] = fs[1]['image_uris']['normal']
        if c.get('layout') in ('token', 'double_faced_token') or 'Token' in c['type_line']: r['k'] = 1
        if all(p.get('digital') for p in ps): r['d'] = 1
        if flav and 'F' in r['w']: r['f'] = flav[0]
        # other printings whose art is tagged with a rodent, one per illustration, for the art chips
        seen, arts = {show.get('illustration_id')}, []
        for p in ps:
            if p['id'] in art_ok[o] and p.get('illustration_id') not in seen and (p.get('image_uris') or faces(p)[0].get('image_uris')):
                seen.add(p.get('illustration_id'))
                arts.append([(p.get('image_uris') or faces(p)[0]['image_uris'])['normal'], p['set'].upper(), p['released_at'][:4]])
        if arts: r['x'] = arts
        ALL.append(r)
    ALL.sort(key=lambda r: (r.get('k', 0), r['r'] or 1e9, r['n']))
    t = open(os.path.join(HERE, 'rodents-template.html')).read()
    t = t.replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':')))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w').write(t)
    cnt = collections.Counter(k for r in ALL for k in r['a'])
    print(len(ALL), 'entries,', sum(1 for r in ALL if r.get('k')), 'tokens;', dict(cnt), dict(collections.Counter(k for r in ALL for k in r['w'])))

if __name__ == '__main__':
    main()
