#!/usr/bin/env python3
"""Builds theme/<slug>.html: 15 adds and 15 cuts that push a precon toward the direction we chose for it, plus the
next-best options for each, for the user to pick from. The rules are in theme/method.md; this script is them.

    python3 tools/carousel/theme_picks.py <slug> <cache dir>

The cache dir holds (fetched once, then reused; delete a file to fetch it again):
  decks.json   Archidekt decks for the commander, from tools/carousel/archidekt.py
  cards.json   every Commander-legal paper card in the deck's color identity, from Scryfall's search
  edhrec-*.json, src-*.txt   EDHREC pages and the written sources' article text

In short:
  1. The theme is a set of card tests (THEMES below: regexes over Scryfall's rules text and type line), written from
     the direction and the commander's text. A card that passes none is off-theme.
  2. Candidates: every card in the colors that isn't in the box, is Commander-legal and isn't a basic land.
  3. Evidence, kept apart and shown: Archidekt share among the decks built in this direction (the third of the
     commander's decks with the most on-theme cards), EDHREC's theme page share, and the written sources that add it.
  4. On-theme cards rank by data (mean of the two shares) plus 3 points per source. Off-theme cards (interaction,
     ramp, staples) are allowed but never sought: one gets in only if direction decks play it at least as much as
     the 15th on-theme pick and at least two sources add it.
  5. Bracket 3: at most 3 Game Changers in the finished 100 (box included); Commander Spellbook's combo search and
     bracket estimate run on the finished 100, and a card that makes an early two-card infinite, mass land denial
     or extra-turn chain is dropped and the next option moves up. Power is never a reason to rank a card higher.
  6. Cuts: box cards ranked by how often direction decks leave them out, then EDHREC's cut share; on-theme box cards
     and the commander are kept. A land picked replaces a land cut, so the land count holds.
"""
import html, json, os, re, statistics, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'}

# A test is (role, label, rules-text regex or None, type-line regex or None); a card takes the first test it passes.
# '~' stands for the card's own name. Roles: engine (pays off or multiplies the theme), piece (the theme's fuel),
# support (helps the theme run: recursion, tutors, attach effects, other enchantments for Killian), and off (none).
THEMES = {
 'silverquill-influence': {
  'cmd': 'Killian, Decisive Mentor', 'id': 'wb', 'direction': 'All-in Auras',
  'edhrec_theme': 'auras',
  'why': 'Killian goads whenever an enchantment of ours enters and draws when a creature with our Aura attacks, so the '
         'deck wants many cheap Auras, cards that pay off casting them, and ways to get them back.',
  'tests': [
   ('engine', 'Pays off casting or entering enchantments', r'whenever (?:you cast|an?|another|one or more)[^.]{0,40}?\b(?:aura|enchantment)', None),
   ('engine', 'Makes Auras or enchantments cheaper', r'(?:aura|enchantment)[^.]{0,30}spells? you cast cost|spend this mana only to cast[^.]*(?:aura|enchantment)', None),
   ('engine', 'Pays off enchanted creatures', r'(?:creatures?|permanents?) you control (?:that are|that\'s) enchanted|enchanted by (?:an|one or more|two or more) auras?|for each aura|auras? attached to', None),
   ('engine', 'Scales with enchantments you control', r'(?:for each|number of)[^.]{0,30}enchantments? you control', None),
   ('piece', 'Aura that comes back', r'return (?:it|~|this aura) to (?:its owner\'s|your) hand', r'\bAura\b'),
   ('piece', 'Aura', None, r'\bAura\b'),
   ('piece', 'Makes Role or enchantment tokens', r'create[^.]{0,40}\b(?:role|enchantment)\b', None),
   ('support', 'Gets Auras or enchantments back or finds them', r'(?:aura|enchantment) cards?(?: with[^.]*)? (?:from|in) your (?:graveyard|library)|search your library for an? (?:aura|enchantment)', None),
   ('support', 'Moves or attaches Auras', r'attach (?:target |an? )?aura', None),
   ('support', 'Other enchantment (triggers Killian)', None, r'\bEnchantment\b'),
  ],
  'sources': {   # written sources we can re-read here; videos and Moxfield lists need the desktop app (see method.md)
   'edh-sq': ('EDHREC upgrade guide', 'https://edhrec.com/guides/silverquill-influence-precon-upgrade-guide'),
   'ds-sq': ('Draftsim upgrade guide', 'https://draftsim.com/silverquill-influence-upgrade-guide/'),
   'gf-sq': ('MTGGoldfish article', 'https://www.mtggoldfish.com/articles/silverquill-influence-precon-upgrade'),
   'fs-sq': ('Flipside Gaming budget guide', 'https://flipsidegaming.com/blogs/magic-blog/table-for-four-silverquill-influence-budget-upgrade-guide'),
   'lab-sq': ('EDHLAB guide', 'https://blog.edhlab.gg/debate-prep-silverquill-influence-precon-upgrade-guide'),
   'cz738': ('Command Zone #738 list', 'archidekt:21970344'),
  },
 },
}
# Commander Spellbook's estimate-bracket tags. They only read combos, Game Changers, land denial and extra turns.
TAG = {'E': 'Exhibition (no combos)', 'C': 'Core', 'O': 'Oddball', 'P': 'Powerful', 'S': 'Spicy', 'R': 'Ruthless'}
ROLE_NAME = {'engine': 'Engines and payoffs', 'piece': 'Auras and theme pieces', 'support': 'Support', 'off': 'Off-theme'}

def get(url, data=None, raw=False):
    for i in range(4):
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                         headers={**UA, 'Accept': 'text/html,*/*' if raw else 'application/json', **({'Content-Type': 'application/json'} if data else {})})
            with urllib.request.urlopen(req, timeout=60) as r:
                b = r.read()
                return b.decode('utf-8', 'ignore') if raw else json.loads(b)
        except Exception:
            if i == 3: raise
            time.sleep(2 * (i + 1))

def cached(path, fetch):
    if not os.path.exists(path):
        v = fetch(); json.dump(v, open(path, 'w'))
    return json.load(open(path))

def oracle(c):
    t = c.get('oracle_text') or ' // '.join(f.get('oracle_text', '') for f in c.get('card_faces', []))
    for nm in [c['name']] + [f['name'] for f in c.get('card_faces', [])]:
        t = t.replace(nm, '~')
    return t
def typeline(c): return c.get('type_line') or ' // '.join(f['type_line'] for f in c['card_faces'])
def front(n): return n.split(' // ')[0]

def article_text(page):
    """The article's words: scripts and styles out, the <article> element if the page has one (sidebars list other
    cards), tags stripped."""
    s = re.sub(r'(?is)<(script|style|noscript|nav|footer|aside)[^>]*>.*?</\1>', ' ', page)
    m = re.search(r'(?is)<article\b.*?</article>', s)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(0) if m else s)))

def main():
    slug, cache = sys.argv[1], sys.argv[2]
    T = THEMES[slug]; os.makedirs(cache, exist_ok=True)
    P = lambda f: os.path.join(cache, f)
    cslug = re.sub(r'[^a-z0-9]+', '-', T['cmd'].lower().replace("'", '')).strip('-')

    # The box: from the deck carousel make.py built.
    h = open(os.path.join(ROOT, 'decks', slug + '.html')).read()
    box = json.loads(re.search(r'const ALL=(\[.*?\]);\n', h, re.S).group(1))
    boxnames = {front(c['n']) for c in box}

    # Every card we could add (Scryfall), by front-face name.
    def sf():
        out, url = [], 'https://api.scryfall.com/cards/search?' + urllib.parse.urlencode(
            {'q': f'id<={T["id"]} legal:commander game:paper', 'unique': 'cards'})
        while url:
            d = get(url); out += d['data']; url = d.get('next_page'); time.sleep(0.12)
        return out
    cards = {front(c['name']): c for c in cached(P('cards.json'), sf)}

    def role(c):
        o, t = oracle(c).lower(), typeline(c)
        for r, label, ot, tt in T['tests']:
            if (ot is None or re.search(ot, o)) and (tt is None or re.search(tt, t)):
                return r, label
        return 'off', 'Off-theme'

    # EDHREC: the commander's theme page (share of theme decks) and the precon page (cut shares).
    th = cached(P('edhrec-theme.json'), lambda: get(f'https://json.edhrec.com/pages/commanders/{cslug}/{T["edhrec_theme"]}.json'))
    pre = cached(P('edhrec-precon.json'), lambda: get(f'https://json.edhrec.com/pages/precon/{slug}.json'))
    ed = {}
    for l in th['container']['json_dict']['cardlists']:
        for c in l['cardviews']:
            if c.get('potential_decks'): ed[front(c['name'])] = (c['num_decks'] / c['potential_decks'], c.get('synergy', 0))
    edn = th['container']['json_dict'].get('card', {}).get('num_decks', 0)
    PL = {l['tag']: l['cardviews'] for l in pre['container']['json_dict']['cardlists']}
    edcut = {front(c['name']): c['unpopularity'] for t in ('cardstocut', 'landstocut') for c in PL.get(t, []) if c.get('unpopularity')}

    # Archidekt: real decks with the commander and 98 to 102 cards, exact duplicates dropped.
    seen, decks = set(), []
    for d in json.load(open(P('decks.json'))):
        cs = [front(c) for c in d['cards']]
        if T['cmd'] not in cs or not 98 <= len(cs) <= 102: continue
        k = tuple(sorted(cs))
        if k in seen: continue
        seen.add(k); decks.append(set(cs))
    # "Built in this direction": the third of decks with the most on-theme cards (engine and piece roles, box or not).
    themed = {n for n, c in cards.items() if role(c)[0] in ('engine', 'piece')}
    score_of = [len(d & themed) for d in decks]
    cut_at = sorted(score_of)[len(score_of) * 2 // 3]
    dirn = [d for d, s in zip(decks, score_of) if s >= cut_at]
    rest = [d for d, s in zip(decks, score_of) if s < cut_at]
    def share(n, ds): return sum(n in d for d in ds) / len(ds) if ds else 0

    # Written sources: every card name of ours that the article mentions, longest names first so "Spirit Link"
    # isn't also counted inside "Spirit Link Lich". The Command Zone list is its Archidekt "Adds" pile.
    src = {}
    names = sorted((n for n in cards if len(n) >= 5), key=len, reverse=True)
    for key, (label, url) in T['sources'].items():
        def fetch():
            if url.startswith('archidekt:'):
                d = get('https://archidekt.com/api/decks/' + url.split(':')[1] + '/')
                return [c['card']['oracleCard']['name'] for c in d['cards'] if 'Adds' in (c.get('categories') or [])]
            return article_text(get(url, raw=True))
        v = cached(P(f'src-{key}.json'), fetch)
        if isinstance(v, list): src[key] = {front(n) for n in v}
        else:
            hit = set(); text = v.replace('\u2019', "'").replace('\u2018', "'")   # curly apostrophes, as most sites print them
            for n in names:
                # One-word names are often ordinary words or site menus ("Arena", "Clear"): they count only if they're
                # 6+ letters, not half of a split card, and the word never appears in lower case in the article.
                if ' ' not in n and (len(n) < 6 or cards[n].get('layout') in ('split', 'adventure', 'flip')
                                     or re.search(r'\b' + re.escape(n.lower()) + r'\b', text)): continue
                if re.search(r'(?<![\w\'])' + re.escape(n) + r'(?![\w\'])', text):
                    hit.add(n); text = re.sub(re.escape(n), ' ', text)
            src[key] = hit

    # Score every candidate.
    rows = []
    for n, c in cards.items():
        if n in boxnames or 'Basic' in typeline(c): continue
        r, label = role(c)
        a, (b, syn) = share(n, dirn), ed.get(n, (0, 0))
        ks = [k for k in T['sources'] if n in src[k]]
        if a == 0 and b == 0 and not ks: continue
        lift = a / max(share(n, rest), 0.01)
        iu = c.get('image_uris') or c['card_faces'][0]['image_uris']
        rows.append({'n': n, 'role': r, 'label': label, 'a': a, 'b': b, 'syn': syn, 'src': ks, 'lift': lift,
                     'data': (a + b) / 2, 'score': (a + b) / 2 + 0.03 * len(ks), 'gc': bool(c.get('game_changer')),
                     'land': 'Land' in typeline(c).split(' // ')[0], 'mv': c.get('cmc', 0), 'usd': float((c.get('prices') or {}).get('usd') or 0) or None,
                     'img': iu['small'], 'big': iu['normal'], 'url': c['scryfall_uri'].split('?')[0], 'type': typeline(c)})
    # 'land' reads the front face only: a spell with a land back (Glasswing Grace) counts as a spell.
    rows.sort(key=lambda x: (-x['score'], x['mv']))

    box_gc = sum(bool(cards.get(front(c['n']), {}).get('game_changer')) for c in box)
    on = [x for x in rows if x['role'] != 'off']
    def build(banned):
        """The 15: on-theme cards by score; an off-theme card only if direction decks play it at least as much as the
        15th on-theme card and two sources add it. Game Changers stop at 3 in the whole deck."""
        bar = [x for x in on if x['n'] not in banned][14]['a']
        pool = [x for x in rows if x['n'] not in banned and (x['role'] != 'off' or (x['a'] >= bar and len(x['src']) >= 2))]
        pick, gc = [], box_gc
        for x in pool:
            if x['gc'] and gc >= 3: continue
            pick.append(x); gc += x['gc']
            if len(pick) == 15: break
        return pick

    # Cuts: box cards (not the commander, not on-theme engine or piece cards) that direction decks most often leave out.
    def cuts_for(pick):
        nl = sum(x['land'] for x in pick)
        cand = []
        for c in box:
            n = front(c['n'])
            if n == T['cmd'] or 'Basic' in c['t']: continue
            r = role(cards[n])[0] if n in cards else 'off'
            if r in ('engine', 'piece'): continue
            cand.append({'n': n, 'role': r, 'out': 1 - share(n, dirn), 'ed': edcut.get(n, 0), 'land': 'Land' in c['t'],
                         'img': c['i'].replace('/normal/', '/small/'), 'big': c['i'], 't': c['t'],
                         'url': 'https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{n}"')})
        cand.sort(key=lambda x: (-(x['out'] + x['ed']) / 2))
        spells = [x for x in cand if not x['land']]; lands = [x for x in cand if x['land']]
        return spells[:15 - nl] + lands[:nl], spells[15 - nl:25 - nl] + lands[nl:nl + 4]

    # Bracket check on the finished 100; drop what breaks Bracket 3 and rebuild.
    banned, notes = set(), []
    while True:
        pick = build(banned); cuts, morecuts = cuts_for(pick)
        out = {x['n'] for x in cuts}
        main = [{'card': c['n'], 'quantity': c.get('q', 1)} for c in box if front(c['n']) not in out and front(c['n']) != T['cmd']]
        main += [{'card': x['n'], 'quantity': 1} for x in pick]
        body = {'main': main, 'commanders': [{'card': T['cmd'], 'quantity': 1}]}
        combos = get('https://backend.commanderspellbook.com/find-my-combos', body)['results']['included']
        est = get('https://backend.commanderspellbook.com/estimate-bracket/', body)
        bad = []
        for cb in combos:
            ns = [u['card']['name'] for u in cb['uses']]
            prods = ' '.join(p['feature']['name'] for p in cb.get('produces', []))
            if len(ns) <= 2 and 'Infinite' in prods:
                bad += [front(n) for n in ns if front(n) in {x['n'] for x in pick}]
        for c in est.get('cards', []):
            if (c.get('massLandDenial') or c.get('extraTurn')) and front(c['card']['name']) in {x['n'] for x in pick}:
                bad.append(front(c['card']['name']))
        if not bad: break
        for b in bad:
            banned.add(b); notes.append(f'{b} left out: it breaks Bracket 3 with this deck.')
    gcs = box_gc + sum(x['gc'] for x in pick)
    picked = {x['n'] for x in pick}
    more = {r: [x for x in rows if x['role'] == r and x['n'] not in picked and x['n'] not in banned][:12] for r in ROLE_NAME}

    # Page.
    E = lambda s: html.escape(str(s), quote=True)
    pct = lambda v: f'{round(v * 100)}%'
    def tile(x, kind='add'):
        if kind == 'add':
            cap = (f'<span class="r">{E(x["label"])}</span><span class="m">Built this way {pct(x["a"])} · EDHREC theme {pct(x["b"])}'
                   f'{" · " + str(len(x["src"])) + " source" + ("s" if len(x["src"]) != 1 else "") if x["src"] else ""}</span>'
                   + ('<span class="gc">Game Changer</span>' if x['gc'] else '') + (f'<span class="m">${x["usd"]:.2f}</span>' if x['usd'] else ''))
            z = f'{x["n"]}: {x["label"]}. Played by {pct(x["a"])} of the {len(dirn)} Archidekt decks built this way ({pct(share(x["n"], rest))} of the others), {pct(x["b"])} of EDHREC\'s {edn:,} {T["edhrec_theme"]} decks.' + (' Added by: ' + ', '.join(T['sources'][k][0] for k in x['src']) + '.' if x['src'] else ' No written source adds it.')
        else:
            cap = f'<span class="r">Left out of {pct(x["out"])} of decks built this way</span><span class="m">EDHREC cut {pct(x["ed"])}</span>'
            z = f'{x["n"]}: left out of {pct(x["out"])} of the {len(dirn)} Archidekt decks built this way; EDHREC: cut from {pct(x["ed"])} of decks from this box.'
        return (f'<figure class="ct"><button class="zb" type="button" data-z="{E(x["big"])}" data-s="{E(z)}" aria-label="Zoom {E(x["n"])}">'
                f'<img src="{E(x["img"])}" width="146" height="204" alt="{E(x["n"])}" loading="lazy" decoding="async" referrerpolicy="no-referrer"></button>'
                f'<figcaption><a class="c" href="{E(x["url"])}" target="_blank" rel="noopener">{E(x["n"])}</a>{cap}</figcaption></figure>')
    grid = lambda xs, k='add': '<div class="cards">' + ''.join(tile(x, k) for x in xs) + '</div>'
    by = lambda r: [x for x in pick if x['role'] == r]
    secs = ''.join(f'<h3>{ROLE_NAME[r]} ({len(by(r))})</h3>' + grid(by(r)) for r in ROLE_NAME if by(r))
    moresec = ''.join(f'<details><summary>{ROLE_NAME[r]}: next {len(more[r])}</summary>{grid(more[r])}</details>' for r in ROLE_NAME if more[r])
    combos_txt = ('; '.join(' + '.join(u['card']['name'] for u in cb['uses']) + ' (' + ', '.join(p['feature']['name'] for p in cb.get('produces', [])[:3]) + ')'
                            for cb in combos[:8]) or 'none')
    srcs = ''.join(f'<li><a href="{E(u if not u.startswith("archidekt:") else "https://archidekt.com/decks/" + u.split(":")[1])}">{E(l)}</a>: {len(src[k] - boxnames)} cards named that aren\'t in the box</li>'
                   for k, (l, u) in T['sources'].items())
    usd = sum(x['usd'] or 0 for x in pick)
    tpl = open(os.path.join(HERE, 'theme-picks-template.html')).read()
    rep = {
     '__TITLE__': E(f'{T["direction"]}: 15 in, 15 out'),
     '__DECK__': E(T['cmd'] + ' · ' + slug.replace('-', ' ').title()),
     '__WHY__': E(T['why']),
     '__SUMMARY__': E(f'{len(dirn)} of {len(decks)} Archidekt {T["cmd"].split(",")[0]} decks count as built this way '
                      f'(at least {cut_at} on-theme cards). About ${usd:,.0f} for the 15 at Scryfall\'s listed printing. '
                      f'{gcs} Game Changer{"s" if gcs != 1 else ""} in the finished deck.'),
     '__PICKS__': secs, '__MORE__': moresec,
     '__CUTS__': grid(cuts, 'cut'), '__MORECUTS__': grid(morecuts, 'cut'),
     '__CHECK__': E(f'{gcs} Game Changer{"s" if gcs != 1 else ""} (Bracket 3 allows 3). Commander Spellbook\'s combo-based tag for the finished 100: '
                    f'{TAG.get(est.get("bracketTag"), est.get("bracketTag", "?"))}. Combos it finds: {combos_txt}. ' + ' '.join(notes)),
     '__SOURCES__': srcs, '__N__': str(len(decks)), '__ND__': str(len(dirn)), '__EDN__': f'{edn:,}',
     '__DATE__': time.strftime('%b %-d, %Y'),
    }
    for k, v in rep.items(): tpl = tpl.replace(k, v)
    os.makedirs(os.path.join(ROOT, 'theme'), exist_ok=True)
    open(os.path.join(ROOT, 'theme', slug + '.html'), 'w').write(tpl)
    print(f'{len(decks)} decks, {len(dirn)} built this way (>= {cut_at} on-theme); box GCs {box_gc}, final {gcs}; bracket {est.get("bracketTag")}')
    for x in pick: print(f'  + {x["n"]:<38} {x["role"]:<8} a={pct(x["a"]):>4} b={pct(x["b"]):>4} src={len(x["src"])} lift={x["lift"]:.1f}{" GC" if x["gc"] else ""}')
    for x in cuts: print(f'  - {x["n"]:<38} out={pct(x["out"]):>4} ed={pct(x["ed"]):>4}')
    for n in notes: print(' ', n)
    print('  combos:', combos_txt)

if __name__ == '__main__':
    main()
