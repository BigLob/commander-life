"""Build decks/tokens.html: every token, copy effect, emblem and game marker each of our precons uses.

Reads the decklists the same way make.py does (MTGJSON or Wizards' article), plus the Archenemy: Nicol
Bolas deck and its 20 schemes, and our own Xenagos group hug deck (from xenagos.html's Deck tab). A card's tokens come from Scryfall's `all_parts` (component "token"),
each fetched for its exact stats. Scryfall's generic "Copy" helper and copy effects it doesn't link
(replicate, populate, "create a token that's a copy") go in a separate Copies list, since those tokens
are whatever they copy. Every card whose text mentions a token was read by hand in Nov 2026; the
overrides below are what that review turned up.
Run from the repo root:  python3 tools/carousel/tokens.py   (TOKENS_CACHE=<file> reuses the download)
"""
import html, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make

OUT = os.path.join(HERE, '..', '..', 'decks', 'tokens.html')
AE = ('archenemy-nicol-bolas', 'Archenemy: Nicol Bolas', 'Archenemy: Nicol Bolas (2017)', None, None, ('mtgjson', 'ArchenemyNicolBolas_E01'))
XEN = ('xenagos', 'Xenagos, the Party Hugger', 'Our own group hug deck (Xenagos, God of Revels)', None, None, ('xenagos',))
DECKS = make.DECKS + [AE, XEN]

def xenagos_list():
    """The 100 cards in xenagos.html's Deck tab (its ALL list; SUG, the suggestions, isn't the deck)."""
    s = open(os.path.join(HERE, '..', '..', 'xenagos.html')).read()
    i = s.index('const ALL=') + len('const ALL=')
    return [(r.get('q', 1), {'name': r['n']}, r['n']) for r in json.JSONDecoder().raw_decode(s[i:])[0]]
COLORS = {'W': 'white', 'U': 'blue', 'B': 'black', 'R': 'red', 'G': 'green'}

# Scryfall's Star Trek Tribble token is colorless, but both cards that make it say "white Tribble".
FIX_COLORS = {'Tribble': ['W']}
# Who gets the token, when it isn't you.
WHO = {'Pongify': 'for the creature\'s controller', 'Beast Within': 'for the permanent\'s controller',
       'Generous Gift': 'for the permanent\'s controller', 'Skyclave Apparition': 'for the exiled card\'s owner',
       'Koloth, Tribble Hunter': 'every player gets two', 'Shadrix Silverquill': 'any player you pick',
       'Combat Calligrapher': 'whoever attacks your opponent', 'Fractured Identity': 'every other player gets one',
       'Terastodon': 'for each destroyed permanent\'s controller', 'Rite of the Raging Storm': 'every player gets one each upkeep',
       'Dual Nature': 'every player, for each of their creatures'}
# Copy effects that Scryfall doesn't link to the Copy helper.
COPY_TEXT = re.compile(r"replicate|populate|token that's a copy|tokens that are copies|token copy|copy becomes a token|copies become tokens", re.I)
# Embalm and eternalize tokens are listed by Scryfall under the card's own name: they belong with Copies too.

def text(c):
    return ' // '.join(f.get('oracle_text', '') for f in c['card_faces']) if c.get('card_faces') else c.get('oracle_text', '')

def load():
    cache = os.environ.get('TOKENS_CACHE')
    if cache and os.path.exists(cache):
        return json.load(open(cache))
    decks, toks = {}, {}
    for d in DECKS:
        lst = xenagos_list() if d is XEN else make.decklist(d[5])
        if d is AE:  # make.decklist reads only commander + main deck; the schemes make tokens too
            ae = json.loads(make.get('https://mtgjson.com/api/v5/decks/ArchenemyNicolBolas_E01.json'))['data']
            lst += [(1, {'name': s['name']}, s['name']) for s in ae['schemes']]
        decks[d[0]] = make.scryfall(lst)
        print(d[0], sum(q for q, _ in decks[d[0]]), flush=True)
    for cs in decks.values():
        for q, c in cs:
            for p in c.get('all_parts', []):
                if p['component'] == 'token' and p['id'] not in toks:
                    toks[p['id']] = json.loads(make.get(p['uri'])); time.sleep(0.1)
    data = {'decks': decks, 'tokens': toks}
    if cache: json.dump(data, open(cache, 'w'))
    return data

def img(t):
    iu = t.get('image_uris') or t['card_faces'][0]['image_uris']
    return iu['normal']

def stats(t):
    """'2/2 black Zombie creature, decayed', in plain words."""
    cols = FIX_COLORS.get(t['name'], t.get('colors', []))
    col = ' and '.join(COLORS[c] for c in 'WUBRG' if c in cols) or 'colorless'
    types = t['type_line'].replace('Token ', '')
    sup, _, sub = types.partition(' — ')
    sup = sup.lower()
    leg = 'legendary ' if sup.startswith('legendary ') else ''
    sup = sup.removeprefix('legendary ')
    pt = f"{t['power']}/{t['toughness']} " if 'power' in t else ''
    pt = pt.replace('*/*', 'X/X')
    return f'{pt}{col} {leg}{sub + " " if sub else ""}{sup}'

def abil(t):
    o = re.sub(r'\s*\([^)]*\)', '', t.get('oracle_text', '')).strip()  # drop reminder text
    o = re.sub(r'\bthis (token|creature|artifact)\b', lambda m: 'It' if m.start() == 0 or o[m.start() - 2] in '.\n' else 'it', o, flags=re.I)
    return o.replace('\n', '; ')

def build(data):
    D, T = data['decks'], data['tokens']
    sections, nav, every = [], [], {}
    for slug, name, product, cmd, alt, _ in DECKS:
        cs = D[slug]
        toks, copies, emblems, marks = {}, [], [], []
        seen = set()
        for q, c in cs:
            n = c['name']
            if n in seen: continue
            seen.add(n)
            t = text(c)
            parts = [T[p['id']] for p in c.get('all_parts', []) if p['component'] == 'token']
            is_copy = any(p['name'] in ('Copy', n) for p in parts) or bool(COPY_TEXT.search(t))
            for p in parts:
                if p['name'] in ('Copy', n): continue  # copy helper / embalm-eternalize copy
                key = (p['name'], p.get('power'), p.get('toughness'), tuple(FIX_COLORS.get(p['name'], p.get('colors', []))), p['type_line'], abil(p))
                e = toks.setdefault(key, {'t': p, 'by': []})
                e['by'].append((n, WHO.get(n)))
            if is_copy:
                how = ('Embalm' if 'Embalm' in t else 'Eternalize' if 'Eternalize' in t else 'Encore' if 'Encore' in t else
                       'Squad' if 'Squad' in t else 'Myriad' if 'myriad' in t else 'Replicate' if 'eplicate' in t else 'Populate' if 'Populate' in t else '')
                copies.append((n, how, WHO.get(n)))
            m = re.search(r'emblem with "([^"]+)"(?: and "([^"]+)")?', t)
            if m:
                who = 'target opponent gets it' if 'opponent gets an emblem' in t else 'you get it'
                emblems.append((n, [x for x in m.groups() if x], who))
            if 'monarch' in t.lower(): marks.append(('Monarch', n))
            if '{E}' in t: marks.append(('Energy', n))
        rows = []
        for e in sorted(toks.values(), key=lambda e: (-len(e['by']), e['t']['name'])):
            t = e['t']
            by = ', '.join(html.escape(b) + (f' <i>({html.escape(w)})</i>' if w else '') for b, w in e['by'])
            ab = abil(t)
            rows.append(f'''<li class="tok"><a href="{t['scryfall_uri']}" target="_blank" rel="noopener"><img src="{img(t)}" alt="{html.escape(t['name'])} token" loading="lazy" referrerpolicy="no-referrer"></a><div><b>{html.escape(t['name'])}</b><span class="st">{html.escape(stats(t))}</span>{f'<span class="ab">{html.escape(ab)}</span>' if ab else ''}<span class="by"><em>{len(e['by'])} card{'s' if len(e['by']) > 1 else ''}:</em> {by}</span></div></li>''')
            every.setdefault(t['name'] + ' · ' + stats(t), set()).add(name)
        extra = []
        if copies:
            extra.append('<h3>Copy tokens</h3><p class="note">No fixed token: each is a copy of something. A Copy helper card, a spare card or a die on a proxy works.</p><ul class="plain">' +
                         ''.join(f'<li>{html.escape(n)}{f" <i>({how})</i>" if how else ""}{f" <i>({html.escape(w)})</i>" if w else ""}</li>' for n, how, w in copies) + '</ul>')
        if emblems:
            extra.append('<h3>Emblems</h3><ul class="plain">' + ''.join(f'<li>{html.escape(n)} ({html.escape(w)}): ' + ' and '.join(f'“{html.escape(y)}”' for y in x) + '</li>' for n, x, w in emblems) + '</ul>')
        if marks:
            by = {}
            for k, n in marks: by.setdefault(k, []).append(n)
            words = {'Monarch': 'The Monarch card (not a token, but worth having)', 'Energy': 'Energy counters (not tokens: keep count with a die)'}
            extra.append('<h3>Also keep track of</h3><ul class="plain">' + ''.join(f'<li>{words[k]}: <i>{len(v)} card{"s" if len(v) > 1 else ""}</i>{": " + html.escape(", ".join(v)) if k == "Monarch" else ""}</li>' for k, v in by.items()) + '</ul>')
        sub = f'{html.escape(product)}' + (f' · {html.escape(cmd)}' if cmd else '')
        count = f'{len(toks)} token{"s" if len(toks) != 1 else ""}' + (f', {len(copies)} copy effect{"s" if len(copies) != 1 else ""}' if copies else '')
        body = f'<ul class="toks">{"".join(rows)}</ul>' if rows else '<p class="note">No tokens.</p>'
        sections.append(f'<section id="{slug}"><h2>{html.escape(name)}</h2><p class="sub">{sub}<br><span class="ct">{count}</span></p>{body}{"".join(extra)}</section>')
        nav.append(f'<a href="#{slug}">{html.escape(name)}</a>')
    shared = sorted(((k, v) for k, v in every.items() if len(v) > 1), key=lambda kv: (-len(kv[1]), kv[0]))
    shared_html = '<ul class="plain">' + ''.join(f'<li><b>{html.escape(k.split(" · ")[0])}</b> <span class="st">{html.escape(k.split(" · ")[1])}</span>: <i>{len(v)} decks</i> ({html.escape(", ".join(sorted(v)))})</li>' for k, v in shared) + '</ul>'
    page = open(os.path.join(HERE, 'tokens-template.html')).read()
    page = page.replace('<!--NAV-->', ''.join(nav)).replace('<!--DECKS-->', ''.join(sections)).replace('<!--SHARED-->', shared_html)
    open(OUT, 'w').write(page)
    print('wrote', OUT)

if __name__ == '__main__':
    build(load())
