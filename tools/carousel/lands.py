"""Build lands/index.html: every Commander-legal nonbasic land (plus unreleased ones from the current
year, such as the Star Trek planets), shown as one card per category (40), then one card per cycle.

Card data, EDHREC rank and images come from Scryfall. Price is the cheapest paper printing (nonfoil,
else foil). Each land is put in one category by its type line and rules text (`cat()`); the
categories and their families are what the page's Category filter and the primer use. Lands in our
precons (read from the built decks/*.html pages) get an "Ours" tab.
Run from the repo root:  python3 tools/carousel/lands.py
"""
import collections, glob, html, json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
OUT = os.path.join(ROOT, 'lands')
UA = {'User-Agent': 'commander-life/1.0', 'Accept': 'application/json'}
Q = 't:land -t:basic game:paper (legal:commander OR year>=2026) -is:funny -banned:commander'

# family -> categories, in the order the filter lists them
FAMILIES = [
    ('Untapped duals', ['Original duals', 'Fetch lands', 'Shock lands', 'Pathways', 'Bond lands', 'Check lands',
                        'Fast lands', 'Slow lands', 'Battle lands', 'Snarls', 'Pain lands', 'Filter lands',
                        'Horizon lands', 'Other untapped duals']),
    ('Tapped fixing', ['Surveil lands', 'Tri-lands & triomes', 'Typed tapped duals', 'Cycling duals',
                       'Tribal lands', 'Scry lands', 'Gain lands', 'Thriving lands', 'Tapped duals', 'Gates', 'Bounce lands',
                       'Budget fetches']),
    ('Any color', ['Any-color lands']),
    ('Ramp', ['Ramp lands']),
    ('Utility', ['Channel lands', 'Creature lands', 'Card-draw lands', 'Token makers', 'Land removal',
                 'Graveyard hate', 'Artifact lands', 'Sagas & town lands', 'Mono-color utility', 'Colorless utility']),
    ('Spell lands', ['Spell lands (MDFC)', 'Flip lands']),
]
BASICS = ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest']

# one line per category: what every land in it does (shown on its card)
DESC = {
    'Original duals': 'Two basic types, no drawback. The best duals ever printed.',
    'Fetch lands': 'Pay 1 life and sacrifice: fetch a land of either basic type, untapped.',
    'Shock lands': 'Two basic types. Pay 2 life or it enters tapped.',
    'Pathways': 'Untapped. Pick one of its two colors as you play it.',
    'Bond lands': 'Untapped with two or more opponents, so always in Commander.',
    'Check lands': 'Untapped if you control a land of either basic type.',
    'Fast lands': 'Untapped if you control two or fewer other lands.',
    'Slow lands': 'Untapped if you control two or more other lands.',
    'Battle lands': 'Two basic types. Untapped once you have two basics out.',
    'Snarls': 'Untapped if you reveal a matching basic from your hand.',
    'Pain lands': 'Untapped. Colorless is free, colored mana costs 1 damage.',
    'Filter lands': 'Turn one mana into two of its colors, in any mix.',
    'Horizon lands': 'Pay 1 life per colored mana; sacrifice later to draw a card.',
    'Other untapped duals': 'Two colors without entering tapped, each with a catch.',
    'Surveil lands': 'Enter tapped. Two basic types and surveil 1.',
    'Tri-lands & triomes': 'Enter tapped, three colors. Triomes add basic types and cycling.',
    'Typed tapped duals': 'Enter tapped. Two basic types, so fetches find them.',
    'Cycling duals': 'Enter tapped. Two basic types and cycling {2}.',
    'Tribal lands': 'Untapped if you reveal a card of its creature type.',
    'Scry lands': 'Enter tapped, scry 1.',
    'Gain lands': 'Enter tapped, gain 1 life.',
    'Thriving lands': 'Enter tapped. One fixed color plus one you choose.',
    'Tapped duals': 'Enter tapped, two colors, some with a small bonus.',
    'Gates': 'Enter tapped, two colors. Count for Gate cards.',
    'Bounce lands': 'Enter tapped and return a land; tap for two mana.',
    'Budget fetches': 'Sacrifice to fetch a basic. Slow but cheap.',
    'Any-color lands': 'Make any color, some with a cost or condition.',
    'Ramp lands': 'Make extra mana under some condition.',
    'Channel lands': 'A land you can discard as a spell instead.',
    'Creature lands': 'Become a creature.',
    'Card-draw lands': 'Draw, cycle, scry or surveil from a land slot.',
    'Token makers': 'Make tokens.',
    'Land removal': 'Destroy lands.',
    'Graveyard hate': 'Exile graveyards.',
    'Artifact lands': 'Lands that are also artifacts.',
    'Sagas & town lands': 'Saga lands and towns with a spell attached.',
    'Mono-color utility': 'One color plus a special ability.',
    'Colorless utility': 'Colorless mana plus a special ability.',
    'Spell lands (MDFC)': 'A spell on the front, a land on the back.',
    'Flip lands': 'A card that transforms into a land.',
}

def get(url):
    for i in range(4):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except Exception:
            if i == 3: raise
            time.sleep(2 ** i)

def search(q, extra=''):
    url, out = f'https://api.scryfall.com/cards/search?q={urllib.parse.quote(q)}{extra}', []
    while url:
        r = get(url)
        out += r['data']
        url = r.get('next_page')
        time.sleep(0.11)
    return out

def text(c):
    if c.get('oracle_text') is not None: return c['oracle_text']
    return '\n//\n'.join(f.get('oracle_text', '') for f in c.get('card_faces', []))

def front(c):
    return c['card_faces'][0] if c.get('card_faces') else c

def basic_types(t):
    sub = t.split(' // ')[0].split('—')
    return [b for b in BASICS if len(sub) > 1 and re.search(r'\b' + b + r'\b', sub[1])]

def cat(c):
    """One category per land. Order matters: the first rule that fits wins."""
    o, t, n, lo = text(c), c['type_line'], c['name'], text(c).lower()
    ft, bt = front(c)['type_line'], basic_types(c['type_line'])
    pm = set(c.get('produced_mana', [])) - {'C'}
    ci = c['color_identity']
    if c['layout'] == 'modal_dfc':
        return 'Pathways' if 'Land' in ft and 'Land' in c['card_faces'][1]['type_line'] else 'Spell lands (MDFC)'
    if c['layout'] in ('transform', 'meld') and 'Land' not in ft: return 'Flip lands'
    if c['layout'] in ('adventure', 'saga'): return 'Sagas & town lands'
    if 'Gate' in t.split('—')[-1]: return 'Gates'
    if 'pay 1 life, sacrifice' in lo and 'search your library for' in lo: return 'Fetch lands'
    if 'sacrifice' in lo and (re.search(r'search your library for (a|up to two) basic land', lo)
                              or ('search your library for a' in lo and 'land card' in lo and 'artifact' not in lo)):
        return 'Budget fetches'
    if len(bt) >= 3: return 'Tri-lands & triomes'
    if len(bt) == 2:
        if 'pay 2 life' in lo: return 'Shock lands'
        if not o.strip() or (o.startswith('(') and '\n' not in o): return 'Original duals'
        if 'surveil 1' in lo: return 'Surveil lands'
        if 'two or more basic lands' in lo: return 'Battle lands'
        if 'cycling' in lo: return 'Cycling duals'
        return 'Typed tapped duals'
    if 'two or fewer other lands' in lo: return 'Fast lands'
    if 'two or more other lands' in lo: return 'Slow lands'
    if 'two or more opponents' in lo: return 'Bond lands'
    if re.search(r'unless you control an? (plains|island|swamp|mountain|forest) or an? ', lo): return 'Check lands'
    if 'reveal a' in lo and 'card from your hand' in lo and 'enters tapped' in lo:
        return 'Snarls' if re.search(r'reveal an? (plains|island|swamp|mountain|forest)', lo) else 'Tribal lands'
    if 'pay 1 life: add' in lo and 'sacrifice' in lo and 'draw a card' in lo: return 'Horizon lands'
    if 'deals 1 damage to you' in lo and len(pm) <= 3 and 'enters tapped' not in lo: return 'Pain lands'
    if re.search(r'\{(\w)/(\w)\}, \{t\}: add', lo): return 'Filter lands'
    if 'return a land you control to its owner' in lo: return 'Bounce lands'
    if re.search(r'becomes? an? .*creature', lo): return 'Creature lands'
    if len(pm) == 3 and 'enters tapped' in lo and len(ci) == 3: return 'Tri-lands & triomes'
    if 'Artifact' in t: return 'Artifact lands'
    if 'scry 1' in lo and 'enters tapped' in lo: return 'Scry lands'
    if 'you gain 1 life' in lo and 'enters tapped' in lo and len(ci) == 2: return 'Gain lands'
    if 'thriving' in n.lower() or 'choose a color other than' in lo: return 'Thriving lands'
    if 'channel' in lo: return 'Channel lands'
    if len(pm) >= 4 or 'any color' in lo or 'any type' in lo: return 'Any-color lands'
    if len(ci) == 2 and len(pm) == 2 and 'enters tapped' in lo: return 'Tapped duals'
    if len(pm) == 2 and len(ci) == 2: return 'Other untapped duals'
    if re.search(r'add \{c\}\{c\}|add \{[wubrg]\}\{[wubrg]\}|add three|for each', lo): return 'Ramp lands'
    if re.search(r'destroy target (nonbasic )?land', lo): return 'Land removal'
    if 'graveyard' in lo and 'exile' in lo and any(x in lo for x in ('target player', 'all graveyards', 'each opponent', 'target card from a graveyard')):
        return 'Graveyard hate'
    if re.search(r'create[^.]*token', lo): return 'Token makers'
    if any(x in lo for x in ('draw a card', 'draw two', 'hideaway', 'surveil', 'look at the top')): return 'Card-draw lands'
    return 'Mono-color utility' if len(pm) == 1 else 'Colorless utility'

def cycle(c):
    """Lands with the same rules text once their name, colors, basic types and creature type are blanked
    out are one cycle (the ten shocks, the five Thriving lands); the page shows a cycle as one card."""
    o, t = text(c), c['type_line'].split(' // ')[0]
    names = {c['name'], c['name'].split(' // ')[0], c['name'].split(',')[0]}
    for f in c.get('card_faces', []): names |= {f['name'], f['name'].split(',')[0]}
    for n in sorted(names, key=len, reverse=True): o = o.replace(n, '~')
    o = re.sub(r'\([^)]*\)', '', o)
    o = re.sub(r'\{[WUBRG]\}', '{M}', o)
    o = re.sub(r'\{[WUBRG]/[WUBRG]\}', '{M/M}', o)
    o = re.sub(r'\b(Plains|Islands?|Swamps?|Mountains?|Forests?)\b', 'BASIC', o)
    o = re.sub(r'\b(white|blue|black|red|green)\b', 'COLOR', o)
    o = re.sub(r'\b(Soldier|Merfolk|Giant|Goblin|Faerie|Elf|Elemental|Treefolk|Kithkin|Dragon|Wizard)s?\b', 'TRIBE', o)
    o = re.sub(r'\s+', ' ', o).strip()
    t = re.sub(r'\b(Plains|Island|Swamp|Mountain|Forest)\b', 'BASIC', t)
    if 'BASIC' not in t: t = re.sub(r'—.*', '— SUB', t)
    return t + '|' + o

def colors(c):
    """The colors a land helps with, for the Color filter: its color identity, the colors it can tap for,
    and, for a fetch, the basic types it finds (fetches have no color identity of their own)."""
    have = set(c['color_identity']) | set(c.get('produced_mana', []))
    if cat(c) in ('Fetch lands', 'Budget fetches'):
        have |= {k for k, v in zip('WUBRG', BASICS) if re.search(r'\b' + v + r'\b', text(c))}
    return ''.join(x for x in 'WUBRG' if x in have)

def ours():
    """name -> [deck name] for every nonbasic land in our precons, from the built carousel pages."""
    names = {s: json.loads(re.search(r'const CFG=(\{.*?\});', open(f).read()).group(1))['deck']
             for f in glob.glob(os.path.join(ROOT, 'decks', '*.html')) if not f.endswith('index.html')
             for s in [os.path.basename(f)[:-5]]}
    out = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(ROOT, 'decks', '*.html'))):
        if f.endswith('index.html'): continue
        for c in json.loads(re.search(r'const ALL=(\[.*?\]);\n', open(f).read()).group(1)):
            if 'Land' in c['t'] and 'Basic' not in c['t']:
                out[c['n']].append(names[os.path.basename(f)[:-5]])
    return out

def main():
    cache = os.environ.get('LANDS_CACHE')  # a JSON file to reuse Scryfall results while working on the page
    if cache and os.path.exists(cache):
        cards, prints = json.load(open(cache))
    else:
        cards, prints = search(Q, '&order=edhrec'), search(Q, '&unique=prints')
        if cache: json.dump([cards, prints], open(cache, 'w'))
    cheap = {}
    for p in prints:
        oid = p.get('oracle_id') or p['card_faces'][0]['oracle_id']
        v = p['prices'].get('usd') or p['prices'].get('usd_foil')
        if v and (oid not in cheap or float(v) < cheap[oid]): cheap[oid] = float(v)
    mine = ours()
    ALL, cyc = [], {}
    for c in cards:
        faces = c.get('card_faces') or []
        iu = c.get('image_uris') or faces[0]['image_uris']
        oid = c.get('oracle_id') or faces[0]['oracle_id']
        g = cat(c)
        r = {'n': c['name'], 'p': cheap.get(oid), 's': c['set'].upper(), 'i': iu['normal'], 'c': colors(c), 'g': g,
             'y': cyc.setdefault(g + '|' + cycle(c), len(cyc)), 'r': c.get('edhrec_rank')}
        if faces and len(faces) > 1 and not c.get('image_uris') and faces[1].get('image_uris'):
            r['b'] = faces[1]['image_uris']['normal']
        if c['name'] in mine: r['o'] = mine[c['name']]
        if c['legalities']['commander'] != 'legal': r['u'] = 1  # not out yet
        ALL.append(r)
    counts = collections.Counter(r['g'] for r in ALL)
    known = {x for _, cs in FAMILIES for x in cs}
    assert set(counts) <= known, set(counts) - known
    assert set(DESC) == known, set(DESC) ^ known
    fams = [[f, [[x, DESC[x]] for x in cs if counts[x]]] for f, cs in FAMILIES]
    t = open(os.path.join(HERE, 'lands-template.html')).read()
    t = (t.replace('/*FAMS*/[]', json.dumps(fams)).replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w').write(t)
    # a summary for writing the primer: per category, count, median price and the most played
    summ = {}
    for x in known:
        rs = [r for r in ALL if r['g'] == x]
        ps = sorted(r['p'] for r in rs if r['p'])
        summ[x] = {'count': len(rs), 'median': ps[len(ps) // 2] if ps else None,
                   'top': [[r['n'], r['r'], r['p']] for r in rs[:8]]}
    json.dump(summ, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'{len(ALL)} lands, {sum(1 for r in ALL if "o" in r)} in our decks, {len(counts)} categories, {len(cyc)} cycles and single lands')

if __name__ == '__main__':
    main()
