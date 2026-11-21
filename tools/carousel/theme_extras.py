#!/usr/bin/env python3
"""Adds three more lists to each theme/<slug>.json, for theme/review.html's Tutors, Game Changers and Wincons tabs
(the user's ask, Nov 21, 2026):

  tutors  every Commander-legal tutor in the deck's colors that isn't in the box: a card that searches your own
          library for a nonland card (to hand, top, battlefield or graveyard; transmute counts). Not counted: land
          searches (fetches, ramp), cards that only find copies of themselves, searches an opponent makes (Path to
          Exile), and wishes (outside the game). A tutor for one creature type is kept only when that type is in the
          deck's theme tests (Zombie tutors for the Zombie decks, Dragon tutors for Atarka).
  gcs     every Game Changer in the colors that isn't in the box (Bracket 3 allows 3 in the deck).
  wins    every alternate win condition in the colors (Scryfall's alternate-win-condition tag, as on wincons/), each
          with its condition in a few words (WIN below), plus the 40 most-played finishers (FIN: overruns, extra
          combats, team double strike or unblockable, drain or burn to each opponent, life-loss engines).

Each list is ordered by the share of EDHREC's decks for the commander that play the card, then by EDHREC's overall
rank. A card that passes the deck's theme tests (THEMES in theme_picks.py) is marked on theme.

    python3 tools/carousel/theme_extras.py [slug ...]      (default: every deck with a theme/<slug>.json)

theme_picks.py runs it for its deck after writing the JSON, so a rerun there keeps the tabs.
Downloads are cached in $THEME_EXTRAS_CACHE (default /tmp/theme-extras); delete it to fetch fresh.
"""
import glob, json, os, re, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from theme_picks import THEMES, get, oracle, typeline, front

CACHE = os.environ.get('THEME_EXTRAS_CACHE', '/tmp/theme-extras')
_types = None

def cached(name, fetch):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, re.sub(r'[^\w.-]+', '_', name) + '.json')
    if not os.path.exists(p): json.dump(fetch(), open(p, 'w'))
    return json.load(open(p))

def search(q):
    def f():
        out, url = [], 'https://api.scryfall.com/cards/search?' + urllib.parse.urlencode({'q': q, 'order': 'edhrec', 'unique': 'cards'})
        while url:
            try: d = get(url)
            except Exception: return out   # Scryfall answers 404 when nothing matches
            out += d['data']; url = d.get('next_page'); time.sleep(0.12)
        return out
    return cached('sf-' + q, f)

def creature_types():
    global _types
    if _types is None:
        _types = sorted(cached('creature-types', lambda: get('https://api.scryfall.com/catalog/creature-types')['data']), key=len, reverse=True)
    return _types

# "search your library [and/or graveyard] for <what>" up to the end of the noun phrase.
SEARCH = re.compile(r'search your library(?: and(?:/or)? (?:your )?graveyard)?(?: and(?:/or)? outside the game)? for ([^.;]*?)(?:,|\band (?:put|reveal|exile|cast)|\bput|\breveal|\bexile|\.|$)')
WHERE = [('onto the battlefield', 'battlefield'), ('into your graveyard', 'graveyard'), ('on top', 'top of library'),
         ('into your hand', 'hand'), ('exile', 'exile')]

def tutor(c, theme_text):
    """None, or a short line of what the card finds and where it puts it."""
    o = oracle(c).lower().replace('\n', ' ')
    if 'Land' in typeline(c).split(' // ')[0] and 'Saga' not in typeline(c) and not re.search(r'search your library for (?:an? |up to )?(?:artifact|creature|card|equipment|enchantment|instant|sorcery)', o):
        return None   # lands that only fetch lands
    hits = []
    for m in SEARCH.finditer(o):
        what = m.group(1).strip()
        if not what or re.search(r'\bnamed\b|\bland\b|\blands\b|\bbasic\b|\bforest|\bisland|\bswamp|\bmountain|\bplains|\bgates?\b|\bdeserts?\b|\bcaves?\b|\bshrines?\b|\btowns?\b', what):
            continue
        if re.search(r'(?:with the same name|card with that name)', what): continue
        # A tutor for one creature type only counts in a deck whose theme is that type.
        ts = [t for t in creature_types() if re.search(r'\b' + re.escape(t.lower()) + r's?\b', what)]
        if ts and not any(re.search(r'\b' + re.escape(t.lower()), theme_text) for t in ts): continue
        tail = o[m.end(1):m.end(1) + 160]
        dest = next((d for k, d in WHERE if k in tail), 'hand')
        hits.append((what, dest))
    if not hits: return None
    what, dest = hits[0]
    return short(what) + ' → ' + dest

def short(what):
    """'a creature card with mana value 1 or less' -> 'Creature, MV ≤1'."""
    w = re.sub(r'\s+', ' ', what)
    w = re.sub(r'\b(?:a|an|any|any number of|up to)\b ', '', w)
    w = re.sub(r'\bcards?\b ?', '', w).strip(' ,')
    w = re.sub(r'with mana value (\S+) or less', r'MV ≤\1', w)
    w = re.sub(r'with mana value (\S+) or greater', r'MV ≥\1', w)
    w = re.sub(r'with mana value less than or equal to', 'MV ≤', w)
    w = re.sub(r'with mana value equal to', 'MV =', w).replace('with mana value', 'MV').replace('mana value', 'MV')
    w = w.replace('with the same MV as this', 'same MV (transmute)').replace(' and/or ', '/').replace(' or ', '/')
    w = w or 'any card'
    if len(w) > 34: w = w[:33].rsplit(' ', 1)[0] + '…'
    return w[0].upper() + w[1:]

# Each alternate wincon's condition in a few words (read off the card, Nov 21, 2026). A new one falls back to the
# card's own win sentence until it's added here.
WIN = {
 'Angel of Destiny': 'Life 15+ over start: attacked players lose', 'Approach of the Second Sun': 'Cast it twice',
 'Atemsis, All-Seeing': '6 different MVs in hand, combat hit', "Azor's Elocutors": '5 filibuster counters',
 'Barren Glory': 'Nothing else in play, empty hand', 'Battle of Wits': '200+ cards in library',
 'Biovisionary': '4 Biovisionaries', 'Celestial Convergence': 'Highest life when counters run out',
 'Central Elevator': '8 unlocked Room doors', 'Chance Encounter': '10 luck counters (won coin flips)',
 'Darksteel Reactor': '20 charge counters (one a turn)', 'Doctor Doom, Unrivaled': 'Empty library',
 'Epic Struggle': '20+ creatures', 'Etrata, the Silencer': '3 hit counters on a player\'s cards',
 'Faithbound Judge': '3 judgment counters', 'Fblthp, Impossibly Lost': 'Empty library',
 'Felidar Sovereign': '40+ life', "Frodo, Sauron's Bane": 'Combat hit after leveling up (needs the Ring)',
 'Gallifrey Stands': '13 Doctors', 'Goblin Bomb': '5 fuse counters (coin flips)', 'Halo Fountain': 'Untap 15 creatures, WWWWW',
 'Happily Ever After': '5 colors, 6 card types, life at start', 'Hedron Alignment': 'Copies in exile, hand, yard and play',
 'Helix Pinnacle': '100 tower counters', 'Hellkite Tyrant': '20+ artifacts', 'Hidetsugu Consumes All': '10 damage to one player in a turn',
 "Hidetsugu's Second Rite": 'A player at exactly 10 life', 'Inferno of the Star Mounts': 'Pump to 20 power: 20 damage',
 'Jace, Wielder of Mysteries': 'Draw from empty library', 'Knuckles the Echidna': '30+ artifacts',
 'Laboratory Maniac': 'Draw from empty library', "Liliana's Contract": '4 different Demons', 'Luck Bobblehead': 'Roll 6 seven times',
 "Maze's End": '10 different Gates', 'Mechanized Production': '8 copies of one artifact', 'Mirrodin Besieged': '15 artifacts in yard (Phyrexians mode)',
 'Mortal Combat': '20 creatures in yard', 'Near-Death Experience': 'Exactly 1 life', 'Peace in Our Time': '12 peace counters',
 'Phage the Untouchable': 'Combat hit (must be cast from hand)', 'Ramses, Assassin Lord': 'Assassin attacks a player who then loses',
 'Revel in Riches': '10 Treasures', 'Simic Ascendancy': '20 growth counters', 'Strixhaven Stadium': '10 point counters',
 'Summon: Primal Odin': 'Combat hit in chapter II', 'Test of Endurance': '50+ life', "Thassa's Oracle": 'Devotion ≥ library (empty it)',
 'The Deck of Many Things': 'A creature it reanimates dies', 'The Millennium Calendar': '1,000 time counters: opponents lose 1,000',
 'Triskaidekaphile': 'Exactly 13 cards in hand', 'Triskaidekaphobia': 'Players at exactly 13 life lose',
 'Twenty-Toed Toad': '20 counters or 20 cards in hand', 'Vorpal Sword': 'Combat hit after BBB5',
 'Vraska the Unseen': '−7 Assassins: combat hit', 'Vraska, Golgari Queen': '−9 emblem: combat hit',
 'Vraska, Scheming Gorgon': '−10: any damage this turn', 'Zenos yae Galvus': 'The chosen player loses',
}

# Finishers: cards that end a game in a turn or two. The first test a card passes names it. Overruns need +2 or more,
# +X or trample, so small team pumps don't count.
FIN = [
 ('Extra combat', r'additional combat phase'),
 ('Overrun', r'creatures you control[^.]{0,30}\bgets? \+(?:x|[2-9]|\d\d)/\+(?:x|\d+)[^.]*until end of turn|creatures you control[^.]{0,30}trample[^.]{0,30}until end of turn'),
 ('Team double strike', r'creatures you control (?:gain|have)[^.]{0,40}double strike'),
 ('Team unblockable', r"creatures you control (?:gain|have)[^.]{0,30}can't be blocked"),
 ('Drain each opponent', r'each opponent loses (?:x|life equal to|that much|half)|each opponent loses \w+ life for each'),
 ('Burn each opponent', r'(?:deals|deal) (?:x|damage equal to|that much)[^.]{0,60}to each opponent|to each opponent equal to'),
 ('Life-loss engine', r'whenever you gain life, (?:target|each) opponent loses|whenever an opponent loses life, you gain'),
]
FIN_N = 40

def finisher(c):
    o = oracle(c).lower()
    return next((l for l, r in FIN if re.search(r, o)), None)

# What a Game Changer does, in a word: the first that fits.
GC_JOB = [('Wincon', r'win the game'), ('Tutor', r'search your library for'), ('Extra turn', r'extra turn'),
          ('Counterspell', r'counter target'), ('Removal', r'destroy|exile (?:target|all|each)|return (?:all|each|target)|(?:each|target) (?:player|opponent) sacrifices|deals \d+ damage to (?:any|target)'),
          ('Fast mana', r'add \{|add (?:one|two|three) mana|add mana|treasure'), ('Card draw', r'draw|look at the top|into your hand'),
          ('Protection', r'hexproof|indestructible|phase out|protection from'), ('Stax', r"can't|don't untap|cost[s]? \{\d\} more|more to cast|lose all abilities|that player sacrifices")]
def gc_job(c):
    o = oracle(c).lower()
    if 'Land' in typeline(c).split(' // ')[0]:
        return 'Land: ' + ('tokens' if 'create' in o else 'protection' if 'prevent all' in o else 'stax' if 'pay {1}' in o else 'fast mana')
    return next((l for l, r in GC_JOB if re.search(r, o)), re.sub(r'Legendary |Snow ', '', typeline(c).split(' — ')[0]))

def gist(c):
    t = oracle(c).replace('\n', ' ').replace('~', front(c['name']))
    s = [x.strip() for x in re.split(r'(?<=[.)])\s+', t) if re.search(r'wins? the game|loses? the game', x)]
    s = ' '.join(s) or t   # The Millennium Calendar: "each opponent loses 1,000 life"
    return s if len(s) <= 180 else s[:177].rsplit(' ', 1)[0] + '…'

def run(slug):
    T = THEMES[slug]; path = os.path.join(ROOT, 'theme', slug + '.json')
    J = json.load(open(path))
    h = open(os.path.join(ROOT, 'decks', T.get('precon', slug) + '.html')).read()
    box = {front(c['n']) for c in json.loads(re.search(r'const ALL=(\[.*?\]);\n', h, re.S).group(1))}
    cslug = re.sub(r'[^a-z0-9]+', '-', T['cmd'].lower().replace("'", '')).strip('-')
    cp = cached('edhrec-' + cslug, lambda: get(f'https://json.edhrec.com/pages/commanders/{cslug}.json'))
    ed = {}
    for l in cp['container']['json_dict']['cardlists']:
        for c in l['cardviews']:
            if c.get('potential_decks'): ed[front(c['name'])] = c['num_decks'] / c['potential_decks']
    edn = cp['container']['json_dict'].get('card', {}).get('num_decks', 0)
    theme_text = ' '.join((ot or '') + ' ' + (tt or '') for _, _, ot, tt in T['tests']).lower() + ' ' + T['direction'].lower()
    def role(c):
        o, t = oracle(c).lower(), typeline(c)
        for r, label, ot, tt in T['tests']:
            if (ot is None or re.search(ot, o)) and (tt is None or re.search(tt, t)): return label
        return None
    picked = {x['n'] for x in J['adds'] if x.get('top')}
    base = f'id<={T["id"]} legal:commander game:paper'

    def rows(cards, job):
        out = []
        for c in cards:
            n = front(c['name'])
            if n in box or 'Basic' in typeline(c): continue
            j = job(c)
            if j is None: continue
            iu = c.get('image_uris') or c['card_faces'][0]['image_uris']
            p = c.get('prices') or {}
            usd = p.get('usd') or p.get('usd_foil')
            th = role(c)
            out.append({'n': n, 'img': iu['normal'], 'url': c['scryfall_uri'].split('?')[0], 'job': j, 'e': round(ed.get(n, 0), 3),
                        'rank': c.get('edhrec_rank') or 10 ** 6, 'gc': bool(c.get('game_changer')), 'usd': float(usd) if usd else None,
                        'theme': th, 'pick': n in picked})
        out.sort(key=lambda x: (-x['e'], x['rank']))
        for x in out: del x['rank']
        return out

    J['tutors'] = rows(search(base + ' (o:"search your library" or o:transmute)'), lambda c: tutor(c, theme_text))
    J['gcs'] = rows(search(base + ' is:gamechanger'), gc_job)
    alt = rows(search(base + ' otag:alternate-win-condition'), lambda c: 'Alt win: ' + WIN.get(front(c['name']), gist(c)))
    altn = {x['n'] for x in alt}
    fin = [x for x in rows(search(base + ' (o:"additional combat" or o:"creatures you control" or o:"each opponent" or o:"opponent loses")'),
                           lambda c: (finisher(c) and 'Finisher: ' + finisher(c))) if x['n'] not in altn][:FIN_N]
    J['wins'] = sorted(alt + fin, key=lambda x: -x['e'])   # stable: within a share, alt wins stay ahead
    J['box_tutors'] = sorted(front(c['name']) for c in search(base + ' (o:"search your library" or o:transmute)')
                             if front(c['name']) in box and tutor(c, theme_text))
    J['box_gcs'] = sorted(front(c['name']) for c in search(base + ' is:gamechanger') if front(c['name']) in box)
    J['box_wins'] = sorted({front(c['name']) for c in search(base + ' otag:alternate-win-condition') if front(c['name']) in box}
                           | {front(c['name']) for c in search(base + ' (o:"additional combat" or o:"creatures you control" or o:"each opponent" or o:"opponent loses")')
                              if front(c['name']) in box and finisher(c)})
    J['cedn'] = edn
    json.dump(J, open(path, 'w'), separators=(',', ':'))
    print(f'{slug}: {len(J["tutors"])} tutors, {len(J["gcs"])} Game Changers, {len(alt)} alt wins + {len(fin)} finishers '
          f'(box: {len(J["box_tutors"])}, {len(J["box_gcs"])}, {len(J["box_wins"])}; EDHREC {edn:,} decks)')

if __name__ == '__main__':
    slugs = sys.argv[1:] or sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'theme', '*.json'))
                                   if os.path.basename(p)[:-5] in THEMES)
    for s in slugs: run(s)
