#!/usr/bin/env python3
"""Builds theme/<slug>.html: 15 adds and 15 cuts that push a precon toward the direction we chose for it, plus the
next-best options for each, for the user to pick from. The rules are in theme/method.md; this script is them.

    python3 tools/carousel/theme_picks.py <slug> <cache dir>
    python3 tools/carousel/theme_picks.py --index      (only rewrites theme/index.json)

It writes theme/<slug>.html (the full page), theme/<slug>.json (what theme/review.html shows two at a time) and
theme/index.json (the review page's deck list).

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
  'edhrec_theme': 'auras', 'roles': {'piece': 'Auras and theme pieces'},
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
 'squirreled-away': {
  'cmd': 'Chatterfang, Squirrel General', 'id': 'bg', 'direction': 'All Squirrels with Chatterfang',
  'precon': 'squirreled-away', 'edhrec_theme': 'squirrels', 'roles': {'piece': 'Squirrel makers and Squirrels'},
  'why': 'Chatterfang adds that many Squirrels whenever we make tokens, so every token maker is a Squirrel maker; the deck wants '
         'Squirrels, token makers, Food (sacrificed Food feeds Camellia and forage) and cards that pay off tokens or Squirrels.',
  'tests': [
   ('engine', 'Pays off tokens or Squirrels', r'whenever you (?:create|sacrifice)[^.]{0,30}(?:token|food)|squirrels? you control|for each squirrel|number of squirrels|other squirrels', None),
   ('engine', 'Doubles or adds to tokens', r'would create one or more tokens|twice that many|that many (?:plus|of)', None),
   ('piece', 'Makes Squirrels', r'create[^.]{0,80}squirrel', None),
   ('piece', 'Squirrel', None, r'\bSquirrel\b'),
   ('piece', 'Makes Food', r'create[^.]{0,40}\bfood\b', None),
   ('support', 'Makes other tokens', r'create[^.]{0,80}\btokens?\b', None),
   ('support', 'Sacrifices Food or creatures for value', r'sacrifice (?:a|an|another|one or more)[^.]{0,20}(?:food|creature|artifact)', None),
  ],
  'sources': {
   'tcg-sa': ('TCGplayer upgrade guide (Drew Knapp)', 'https://www.tcgplayer.com/content/article/Squirreled-Away-MTG-Commander-Precon-Deck-Upgrade-Guide/b972815e-c856-49f6-b5ae-6269495d8be5/'),
  },
 },
 'first-flight': {
  'cmd': 'Isperia, Supreme Judge', 'id': 'wu', 'direction': 'Flyers with anthems and cost reducers',
  'edhrec_theme': 'flying', 'roles': {'piece': 'Flyers'},
  'why': 'Isperia draws when creatures attack us, and the box is a flock of fliers; the direction is more and better '
         'flyers, cards that pump them all, and cards that make them cheaper.',
  'tests': [
   ('engine', 'Pumps flyers or your team', r'creatures? you control (?:with flying |that have flying )?(?:get|gets) \+|creatures? with flying you control get \+|other (?:birds?|angels?|spirits?|sphinx(?:es)?|faeries|drakes?|bats?|thopters?|pegasus|griffins?) you control get \+', None),
   ('engine', 'Makes creature spells cheaper', r'creature spells? (?:with flying )?you cast cost|spells? with flying you cast cost', None),
   ('engine', 'Pays off flyers', r'(?:whenever|for each)[^.]{0,40}creatures? (?:you control )?with flying|creatures? you control with flying|(?:creature )?spells? with flying', None),
   ('engine', 'Gives your team flying', r'creatures you control (?:gain|have) flying', None),
   ('piece', 'Flyer', r"(?m)^(?:[a-z' -]+, )*flying(?:,| \(|$)", r'Creature'),
   ('piece', 'Makes flying tokens', r'create[^.]{0,90}with flying', None),
   ('support', 'Gives a creature flying', r'(?:equipped|enchanted|target) creature (?:gains|has|gets [^.]{0,12}and (?:gains|has)) flying', None),
  ],
  'sources': {
   'edh-ff': ('EDHREC upgrade guide (its Archidekt list)', 'archidekt:4465023'),
   'cgb-ff': ('Cardgamebase upgrade guide', 'https://cardgamebase.com/?p=32232'),
   'cr-ff': ('Cards Realm, Upgrading First Flight', 'https://mtg.cardsrealm.com/en-gb/articles/upgrading-precon-commander-first-flight-isperia-supreme-judge'),
  },
 },
 'grave-danger': {
  'cmd': 'Gisa and Geralf', 'id': 'ub', 'direction': 'Value Zombies on a loop',
  'edhrec_theme': 'zombies', 'roles': {'piece': 'Zombies'},
  'why': 'Gisa and Geralf mill four and let us cast a Zombie from the graveyard each turn, so the deck wants Zombies '
         'that are worth casting again, ways to fill the graveyard, and payoffs for Zombies dying and coming back.',
  'tests': [
   ('engine', 'Brings Zombies back or casts them from the graveyard', r'zombie[^.]{0,60}from (?:your|a) graveyard|from (?:your|a) graveyard[^.]{0,60}zombie', None),
   ('engine', 'Zombie lord or payoff', r'zombies? (?:you control )?gets? \+|whenever (?:a|an|another|one or more)(?: other)?(?: nontoken)? zombies?|for each zombie|zombie spells? you cast cost', None),
   ('piece', 'Zombie', None, r'\bZombie\b'),
   ('piece', 'Makes Zombie tokens', r'create[^.]{0,60}\bzombie\b', None),
   ('support', 'Fills the graveyard', r'\bmill\b|\bmills\b|\bsurveil\b', None),
   ('support', 'Returns or casts creatures from the graveyard', r'creature cards? from (?:your|a) graveyard|cast (?:creature )?spells? from your graveyard', None),
  ],
  'sources': {
   'edh-gd': ('EDHREC upgrade guide (its Archidekt list)', 'archidekt:4465276'),
   'cgb-gd': ('Cardgamebase upgrade guide', 'https://cardgamebase.com/?p=32230'),
  },
 },
 'chaos-incarnate': {
  'cmd': 'Kardur, Doomscourge', 'id': 'br', 'direction': 'Goad everything',
  'edhrec_theme': 'forced-combat', 'roles': {'piece': 'Goad and forced attacks'},
  'why': 'Kardur makes every opposing creature attack someone else and drains each time an attacker dies, so the deck '
         'wants more goad, more forced attacks, and payoffs when opponents fight each other.',
  'tests': [
   ('engine', 'Goads or forces every creature', r'goad (?:each|all)|creatures your opponents control attack|each creature (?:your opponents control )?attacks each combat|all creatures attack', None),
   ('engine', 'Pays off creatures attacking or dying', r'whenever (?:an|a) attacking creature dies|whenever a goaded|whenever (?:a|another) (?:creature|player) attacks (?:one of )?your opponents|whenever an opponent attacks (?:another|one of your)|whenever a creature an opponent controls (?:dies|attacks)|attacking creatures? your opponents control', None),
   ('piece', 'Goad or forced attack', r'\bgoad|attacks? each combat if able|must attack', None),
   ('support', 'Keeps attackers off us', r"can't attack you|attack you[^.]{0,40}pays|creatures can't attack you", None),
  ],
  'sources': {
   'edh-ci': ('EDHREC upgrade guide (its Archidekt list)', 'archidekt:4467252'),
   'cr-ci': ('Cards Realm, Upgrading Chaos Incarnate', 'https://mtg.cardsrealm.com/en-ie/articles/upgrading-commander-precon-chaos-incarnate-kardur-doomscourge'),
  },
 },
 'draconic-destruction': {
  'cmd': 'Atarka, World Render', 'id': 'rg', 'direction': 'More and better Dragons, some ramp',
  'edhrec_theme': 'dragons', 'roles': {'piece': 'Dragons', 'support': 'Ramp and support'},
  'why': 'Atarka gives every attacking Dragon double strike, so the deck wants more and better Dragons, payoffs for '
         'Dragons, and the ramp to cast them.',
  'tests': [
   ('engine', 'Dragon payoff or cost reducer', r'dragons? (?:you control )?gets? \+|whenever (?:a|another|one or more) dragons?|for each dragon|dragon spells? (?:you cast )?cost|spend this mana only to cast (?:a )?dragon', None),
   ('piece', 'Dragon', None, r'\bDragon\b'),
   ('piece', 'Makes Dragon tokens', r'create[^.]{0,60}\bdragon\b', None),
   ('support', 'Ramp', r'\{t\}: add|search your library for (?:a|up to \w+|two) (?:basic )?(?:land|forest|mountain)[^.]*(?:onto the battlefield|put)', r'^(?!.*\bLand\b)'),
  ],
  'sources': {
   'edh-dd': ('EDHREC upgrade guide (its Archidekt list)', 'archidekt:4465326'),
   'cgb-dd': ('Cardgamebase upgrade guide', 'https://cardgamebase.com/?p=32233'),
  },
 },
 'token-triumph': {
  'cmd': 'Emmara, Soul of the Accord', 'id': 'gw', 'direction': 'Token doublers and more-token payoffs',
  'edhrec_theme': 'tokens', 'roles': {'piece': 'Token makers', 'support': 'Tappers and anthems'},
  'why': 'Emmara makes a lifelink Soldier whenever she taps, and the box goes wide; the direction is token doublers, '
         'payoffs for making tokens, and ways to tap Emmara more.',
  'tests': [
   ('engine', 'Doubles tokens', r'twice that many[^.]{0,20}tokens|tokens? would be created[^.]*instead|those tokens plus|double the number of[^.]{0,20}tokens|create (?:that many|an additional)[^.]{0,40}token', None),
   ('engine', 'Pays off tokens', r'whenever (?:one or more )?(?:creature )?tokens?[^.]{0,30}(?:enters|you control)|for each (?:creature )?token|creature tokens? you control get \+|\bpopulate\b', None),
   ('piece', 'Makes creature tokens', r'(?<!controller )(?<!player )(?<!opponent )\bcreate[^.]{0,90}creature tokens?', None),   # not Beast Within's gift
   ('support', 'Taps your creatures or pumps the team', r'\bconvoke\b|tap (?:an|two|three|x) untapped creatures? you control|creatures you control get \+', None),
  ],
  'sources': {
   'edh-tt': ('EDHREC upgrade guide (its Archidekt list)', 'archidekt:4469324'),
   'cgb-tt': ('Cardgamebase upgrade guide', 'https://cardgamebase.com/?p=31874'),
  },
 },
 'living-energy': {
  'cmd': 'Saheeli, Radiant Creator', 'id': 'urg', 'direction': 'Big energy',
  'edhrec_theme': 'energy', 'roles': {'engine': 'Energy payoffs and finishers', 'piece': 'Energy makers', 'support': 'Artifacts and support'},
  'why': 'Saheeli gets energy from every artifact or Artificer spell and spends three a turn on a 5/5 copy, so the '
         'direction is more energy coming in and bigger things to spend it on.',
  'tests': [
   ('engine', 'Pays off or doubles energy', r'pay (?:\{e\}){4,}|pay (?:x|any amount of|one or more) \{e\}|for each \{e\}|energy counters? you have|amount of \{e\}|whenever you (?:get|pay) (?:one or more )?\{e\}|get twice that much|\{e\} (?:you have|than you)', None),
   ('piece', 'Makes energy', r'you get (?:\{e\})+|you get (?:x|that much|that many|an amount of|[a-z]+) \{e\}', None),
   ('support', 'Proliferates (adds energy)', r'\bproliferate\b', None),
   ('support', 'Artifact or Artificer (Saheeli gets energy)', None, r'^(?!.*\bLand\b).*(?:Artifact|Artificer)'),
  ],
  'sources': {
   'cz653': ('Command Zone #653 list', 'archidekt:11021591'),
   'edh-le': ('EDHREC upgrade guide', 'https://edhrec.com/articles/living-energy-precon-upgrade-guide-aetherdrift'),
   'ck-le': ('Card Kingdom $50 upgrade', 'https://blog.cardkingdom.com/aetherdrift-living-energy-precon-upgrade/'),
   'ds-le': ('Draftsim upgrade guide', 'https://draftsim.com/living-energy-upgrade-guide/'),
   'gg-le': ('Gathering Games upgrade guide', 'https://gatheringgames.co.uk/community/blog/living-energy-precon-upgrade-guide-mtg-aetherdift-commander-decks'),
  },
 },
 'lorehold-spirit': {
  'cmd': 'Quintorius, History Chaser', 'id': 'rw', 'direction': 'Discard engine',
  'edhrec_theme': 'discard', 'roles': {'engine': 'Discard and graveyard payoffs', 'piece': 'Discard outlets', 'support': 'Graveyard leavers'},
  'why': 'Quintorius makes a 3/2 Spirit whenever cards leave our graveyard and his +1 discards to draw, so the deck wants '
         'to discard every turn (rummage, loot, discard outlets), payoffs for discarding, and cards that then take '
         'cards back out of the graveyard.',
  'tests': [
   ('engine', 'Pays off discarding', r'whenever you discard|whenever (?:a|one or more) (?:other )?cards? (?:is|are) (?:put into your graveyard from your hand|discarded)|whenever you cycle or discard|for each card discarded', None),
   ('engine', 'Pays off cards leaving the graveyard', r'whenever (?:one or more )?(?:other )?(?:nonland )?cards? leaves? your graveyard', None),
   ('piece', 'Rummage or loot (discard and draw)', r'discard (?:a|one|two|three|x|up to \w+|any number of|your hand)[^.]{0,20}cards?(?:[^.]{0,10}), then draw|discard (?:your hand|any number of cards)[^.]{0,20}then draw|draw[^.]{0,40}, then discard|discards? [^.]{0,30}cards?\. (?:if you do, )?draw', None),
   ('piece', 'Discard outlet', r'(?:^|, |\n)discard (?:a|an|two|x)(?: \w+)? cards?(?: at random)?(?:, [^:]{0,30})?:|as an additional cost to cast this spell, discard|\bmadness\b', None),
   ('support', 'Takes cards out of the graveyard (makes a Spirit)', r'(?:exile|return|cast|play)[^.]{0,60}from (?:your|a|target player\'s|each) graveyards?|\b(?:flashback|escape|unearth|jump-start|retrace|disturb|embalm|eternalize|encore)\b', None),
   ('support', 'Cycling (a discard)', r'\bcycling\b', None),
  ],
  'sources': {
   'edh-ls': ('EDHREC upgrade guide', 'https://edhrec.com/articles/lorehold-spirit-precon-upgrade/'),
   'gf-ls': ('MTGGoldfish article', 'https://www.mtggoldfish.com/articles/these-swaps-make-lorehold-spirit-absolutely-busted'),
   'ck-ls': ('Card Kingdom $50 upgrade', 'https://blog.cardkingdom.com/secrets-of-strixhaven-lorehold-spirit-commander-deck-upgrade-guide/'),
   'ds-ls': ('Draftsim upgrade guide', 'https://draftsim.com/lorehold-spirit-upgrade-guide/'),
   'lab-ls': ('EDHLAB guide', 'https://blog.edhlab.gg/reconstructing-white-red-lorehold-spirit-precon-upgrade-guide/'),
   'cz735': ('Command Zone #735 list', 'archidekt:21533404'),
  },
 },
 'eternal-might': {
  'cmd': "Temmet, Naktamun's Will", 'id': 'wub', 'direction': 'Pure Zombie typal',
  'edhrec_theme': 'zombies', 'roles': {'piece': 'Zombies', 'support': 'Typal support'},
  'why': 'Temmet loots on every attack and pumps Zombies on every card drawn, so the direction is all Zombies: more '
         'Zombies, Zombie lords and payoffs, and typal support.',
  'tests': [
   ('engine', 'Zombie lord or payoff', r'zombies? (?:you control )?gets? \+|whenever (?:a|an|another|one or more)(?: other)?(?: nontoken)? zombies?|for each zombie|zombie spells? you cast cost|zombie[^.]{0,60}from (?:your|a) graveyard', None),
   ('piece', 'Zombie', None, r'\bZombie\b'),
   ('piece', 'Makes Zombie tokens', r'create[^.]{0,60}\bzombie\b|\bembalm\b|\beternalize\b', None),
   ('support', 'Typal support (choose a creature type)', r'choose a creature type|chosen type|\bchangeling\b|share a creature type', None),
  ],
  'sources': {
   'cz654': ('Command Zone #654 list', 'archidekt:11039235'),
   'fw': ('Farwater MTG list', 'archidekt:11257428'),
   'ss-em': ('Salubrious Snail list', 'archidekt:11251533'),
   'ck-em': ('Card Kingdom $30 upgrade', 'https://blog.cardkingdom.com/aetherdrift-eternal-might-precon-upgrade-guide/'),
   'ds-em': ('Draftsim upgrade guide', 'https://draftsim.com/eternal-might-upgrade-guide/'),
   'csi-em': ('CoolStuffInc $50 upgrade', 'https://www.coolstuffinc.com/a/briansmith-seo-02122025-aetherdrifts-eternal-might-precon-upgrade-guide'),
   'br-em': ('EDHREC, Bracketeering: Eternal Might', 'https://edhrec.com/articles/bracketeering-eternal-might'),
  },
 },
}
# Commander Spellbook's estimate-bracket tags. They only read combos, Game Changers, land denial and extra turns.
TAG = {'E': 'Exhibition (no combos)', 'C': 'Core', 'O': 'Oddball', 'P': 'Powerful', 'S': 'Spicy', 'R': 'Ruthless'}
ROLE_NAME = {'engine': 'Engines and payoffs', 'piece': 'Theme pieces', 'support': 'Support', 'off': 'Off-theme'}

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
def slow_land(c):
    """Lands the user doesn't want suggested (Nov 22, 2026): shock lands, and lands that always enter tapped (a sentence
    saying it enters tapped with no 'unless' or 'if': guildgates, tri-lands, bounce lands, surveil lands, Field of the
    Dead, Evolving Wilds). Lands that only sometimes enter tapped (check, fast, slow, bond, reveal lands) stay."""
    t = (c.get('oracle_text') or (c.get('card_faces') or [{}])[0].get('oracle_text', '')).replace('enters the battlefield', 'enters')
    if re.search(r"you may pay 2 life\. If you don.t, (?:it|this land) enters tapped", t): return True
    # A land that fetches a land tapped plays the same (Evolving Wilds, Terramorphic Expanse); Fabled Passage untaps it.
    if re.search(r'sacrifice this land: search[^.]*onto the battlefield tapped', t, re.I) and 'untap' not in t: return True
    return any(re.search(r'\benters tapped\b', x) and not re.search(r'\bunless\b|\bif\b|^\s*(?:If|As)\b', x)
               for x in re.split(r'(?<=\.)\s+|\n', t))
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
    RN = {**ROLE_NAME, **T.get('roles', {})}   # a deck can name its own roles ("Flyers" for First Flight)
    P = lambda f: os.path.join(cache, f)
    cslug = re.sub(r'[^a-z0-9]+', '-', T['cmd'].lower().replace("'", '')).strip('-')

    # The box: from the deck carousel make.py built.
    h = open(os.path.join(ROOT, 'decks', T.get('precon', slug) + '.html')).read()
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
    pre = cached(P('edhrec-precon.json'), lambda: get(f'https://json.edhrec.com/pages/precon/{T.get("precon", slug)}.json'))
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
                # A list with an "Adds" pile (the Command Zone's) counts that pile; any other list counts every card
                # in the deck proper, and the box's own cards fall away below.
                if any('Adds' in (c.get('categories') or []) for c in d['cards']):
                    return [c['card']['oracleCard']['name'] for c in d['cards'] if 'Adds' in (c.get('categories') or [])]
                live = {c['name'] for c in d.get('categories', []) if c.get('includedInDeck')}
                return [c['card']['oracleCard']['name'] for c in d['cards'] if not c.get('categories') or any(x in live for x in c['categories'])]
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
    # Lands stay out of the 15 for 15 (the user's call, Nov 17): they get their own version, 10 nonbasic lands in for
    # 10 basics, on-theme lands first (Hall of Heliod's Generosity, Westvale Abbey), then the most played.
    lrows = [x for x in rows if x['land']]; rows = [x for x in rows if not x['land']]
    # No shock lands and no lands that always enter tapped (the user's rule, Nov 22, 2026).
    lrows = [x for x in lrows if not slow_land(cards[x['n']])]

    # THEME_LANDS_ONLY=1 redoes only the land version and keeps the deck's adds and cuts as they are in theme/<slug>.json
    # (their answers are already on the shared table, and fresh Archidekt data would reshuffle them).
    OLD = None
    if os.environ.get('THEME_LANDS_ONLY'):
        OLD = json.load(open(os.path.join(ROOT, 'theme', slug + '.json')))
        byn = {x['n']: x for x in rows}
        old_pick = [byn[x['n']] for x in OLD['adds'] if x['top'] and x['n'] in byn]
        old_out = {x['n'] for x in OLD['cuts'] if x['top']}
    box_gc = sum(bool(cards.get(front(c['n']), {}).get('game_changer')) for c in box)
    on = [x for x in rows if x['role'] != 'off']
    def build(banned):
        """The 15: on-theme cards by score; an off-theme card only if direction decks play it at least as much as the
        15th on-theme card and two sources add it. Game Changers stop at 3 in the whole deck."""
        if OLD: return old_pick
        bar = [x for x in on if x['n'] not in banned][14]['a']
        pool = [x for x in rows if x['n'] not in banned and (x['role'] != 'off' or (x['a'] >= bar and len(x['src']) >= 2))]
        pick, gc = [], box_gc
        for x in pool:
            if x['gc'] and gc >= 3: continue
            pick.append(x); gc += x['gc']
            if len(pick) == 15: break
        return pick

    def lands_for(banned, gc):
        """10 nonbasic lands for 10 basics: on-theme lands that direction decks or sources use (3%+ or a source), by
        score, then the rest by score. Game Changers still stop at 3. Returns the 10 and the next 10."""
        ok = [x for x in lrows if x['n'] not in banned]
        th = [x for x in ok if x['role'] != 'off' and (x['a'] >= 0.03 or x['src'])]
        order = th + [x for x in ok if x not in th]
        pick = []
        for x in order:
            if x['gc'] and gc >= 3: continue
            if len(pick) < 10: pick.append(x); gc += x['gc']
        rest = [x for x in order if x not in pick][:10]
        return pick, rest

    # The basics the 10 lands replace, split by the box's own basic counts.
    basics = [(front(c['n']), c.get('q', 1)) for c in box if 'Basic' in c['t']]
    nb = sum(q for _, q in basics)
    share_b = sorted(((n, 10 * q / nb) for n, q in basics), key=lambda t: -(t[1] % 1))
    bcut = {n: int(v) for n, v in share_b}
    for n, v in share_b[:10 - sum(bcut.values())]: bcut[n] += 1
    bcut = {n: k for n, k in bcut.items() if k}

    # Cuts: box spells (not the commander, not on-theme engine or piece cards) that direction decks most often leave out.
    def cuts_for(pick):
        cand = []
        for c in box:
            n = front(c['n'])
            if n == T['cmd'] or 'Basic' in c['t']: continue
            r = role(cards[n])[0] if n in cards else 'off'
            if r in ('engine', 'piece'): continue
            if 'Land' in c['t'].split(' // ')[0]: continue   # lands are only swapped in the land version
            cand.append({'n': n, 'role': r, 'out': 1 - share(n, dirn), 'ed': edcut.get(n, 0), 'land': 'Land' in c['t'],
                         'img': c['i'].replace('/normal/', '/small/'), 'big': c['i'], 't': c['t'],
                         'url': 'https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{n}"')})
        cand.sort(key=lambda x: (-(x['out'] + x['ed']) / 2))
        return cand[:15], cand[15:25]

    # Bracket check on the finished 100; drop what breaks Bracket 3 and rebuild.
    banned, notes = set(), []
    while True:
        pick = build(banned); cuts, morecuts = cuts_for(pick)
        lpick, lmore = lands_for(banned, box_gc + sum(x['gc'] for x in pick))
        out = old_out if OLD else {x['n'] for x in cuts}
        main = [{'card': c['n'], 'quantity': c.get('q', 1) - bcut.get(front(c['n']), 0)} for c in box
                if front(c['n']) not in out and front(c['n']) != T['cmd'] and c.get('q', 1) > bcut.get(front(c['n']), 0)]
        main += [{'card': x['n'], 'quantity': 1} for x in pick + lpick]
        body = {'main': main, 'commanders': [{'card': T['cmd'], 'quantity': 1}]}
        combos = get('https://backend.commanderspellbook.com/find-my-combos', body)['results']['included']
        est = get('https://backend.commanderspellbook.com/estimate-bracket/', body)
        bad = []
        for cb in combos:
            ns = [u['card']['name'] for u in cb['uses']]
            prods = ' '.join(p['feature']['name'] for p in cb.get('produces', []))
            if len(ns) <= 2 and 'Infinite' in prods:
                bad += [front(n) for n in ns if front(n) in {x['n'] for x in pick + lpick}]
        for c in est.get('cards', []):
            if (c.get('massLandDenial') or c.get('extraTurn')) and front(c['card']['name']) in {x['n'] for x in pick + lpick}:
                bad.append(front(c['card']['name']))
        if not bad: break
        for b in bad:
            banned.add(b); notes.append(f'{b} left out: it breaks Bracket 3 with this deck.')
    gcs = box_gc + sum(x['gc'] for x in pick + lpick)
    btxt = ', '.join(f'{k} {n}' for n, k in bcut.items())
    picked = {x['n'] for x in pick}
    more = {r: [x for x in rows if x['role'] == r and x['n'] not in picked and x['n'] not in banned][:12] for r in RN}

    if OLD:
        lj = lambda x, top: {'n': x['n'], 'img': x['big'], 'url': x['url'], 'job': x['label'], 'role': RN[x['role']], 'a': round(x['a'], 3),
                             'b': round(x['b'], 3), 'src': [T['sources'][k][0] for k in x['src']], 'gc': x['gc'], 'usd': x['usd'],
                             'land': x['land'], 'top': top, 'theme': x['role'] != 'off'}
        OLD['lands'] = [lj(x, True) for x in lpick] + [lj(x, False) for x in lmore]
        json.dump(OLD, open(os.path.join(ROOT, 'theme', slug + '.json'), 'w'), separators=(',', ':'))
        lands_only_html = True
    else: lands_only_html = False

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
    secs = ''.join(f'<h3>{RN[r]} ({len(by(r))})</h3>' + grid(by(r)) for r in RN if by(r))
    moresec = ''.join(f'<details><summary>{RN[r]}: next {len(more[r])}</summary>{grid(more[r])}</details>' for r in RN if more[r])
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
     '__LANDS__': grid(lpick), '__MORELANDS__': grid(lmore), '__BASICS__': E(btxt),
     '__CHECK__': E(f'{gcs} Game Changer{"s" if gcs != 1 else ""} (Bracket 3 allows 3). Commander Spellbook\'s combo-based tag for the finished 100: '
                    f'{TAG.get(est.get("bracketTag"), est.get("bracketTag", "?"))}. Combos it finds: {combos_txt}. ' + ' '.join(notes)),
     '__SOURCES__': srcs, '__N__': str(len(decks)), '__ND__': str(len(dirn)), '__EDN__': f'{edn:,}',
     '__DATE__': time.strftime('%b %-d, %Y'),
    }
    for k, v in rep.items(): tpl = tpl.replace(k, v)
    if lands_only_html:
        # Swap only the land section into the existing page.
        cut = lambda t: re.search(r'(?s)<h2>Land version.*?(?=<h2>Bracket check</h2>)', t)
        page = open(os.path.join(ROOT, 'theme', slug + '.html')).read()
        open(os.path.join(ROOT, 'theme', slug + '.html'), 'w').write(page.replace(cut(page).group(0), cut(tpl).group(0)))
        print('lands:', ', '.join(x['n'] for x in lpick)); print('more:', ', '.join(x['n'] for x in lmore))
        return
    os.makedirs(os.path.join(ROOT, 'theme'), exist_ok=True)
    open(os.path.join(ROOT, 'theme', slug + '.html'), 'w').write(tpl)
    # Review data for theme/review.html: the 15 in rank order then the options by score, the 15 cuts then the rest.
    def add_j(x, top):
        return {'n': x['n'], 'img': x['big'], 'url': x['url'], 'job': x['label'], 'role': RN[x['role']], 'a': round(x['a'], 3),
                'b': round(x['b'], 3), 'src': [T['sources'][k][0] for k in x['src']], 'gc': x['gc'], 'usd': x['usd'],
                'land': x['land'], 'top': top, 'theme': x['role'] != 'off'}
    def cut_j(x, top):
        return {'n': x['n'], 'img': x['big'], 'url': x['url'], 'out': round(x['out'], 3), 'ed': round(x['ed'], 3),
                'land': x['land'], 'top': top}
    opts = sorted((x for r in RN for x in more[r]), key=lambda x: (-x['score'], x['mv']))
    rev = {'slug': slug, 'cmd': T['cmd'], 'direction': T['direction'], 'why': T['why'], 'date': time.strftime('%b %-d, %Y'),
           'n': len(decks), 'nd': len(dirn), 'edn': edn, 'gcs': gcs, 'bracket': TAG.get(est.get('bracketTag'), est.get('bracketTag')),
           'adds': [add_j(x, True) for x in pick] + [add_j(x, False) for x in opts],
           'cuts': [cut_j(x, True) for x in cuts] + [cut_j(x, False) for x in morecuts],
           'lands': [add_j(x, True) for x in lpick] + [add_j(x, False) for x in lmore], 'basics': btxt}
    json.dump(rev, open(os.path.join(ROOT, 'theme', slug + '.json'), 'w'), separators=(',', ':'))
    write_index()
    import theme_extras; theme_extras.run(slug)   # the Tutors, Game Changers and Wincons tabs
    print(f'{len(decks)} decks, {len(dirn)} built this way (>= {cut_at} on-theme); box GCs {box_gc}, final {gcs}; bracket {est.get("bracketTag")}')
    for x in pick: print(f'  + {x["n"]:<38} {x["role"]:<8} a={pct(x["a"]):>4} b={pct(x["b"]):>4} src={len(x["src"])} lift={x["lift"]:.1f}{" GC" if x["gc"] else ""}')
    for x in cuts: print(f'  - {x["n"]:<38} out={pct(x["out"]):>4} ed={pct(x["ed"]):>4}')
    print('  lands for', btxt)
    for x in lpick: print(f'  L {x["n"]:<38} {x["role"]:<8} a={pct(x["a"]):>4} b={pct(x["b"]):>4} src={len(x["src"])}')
    for n in notes: print(' ', n)
    print('  combos:', combos_txt)

# The review page's front screen: every deck we own with the direction the user chose (decks/angles.html, Nov 16,
# 2026), and whether its theme picks are built. A deck with no direction yet says so.
DIRECTIONS = {
 'silverquill-influence': 'All-in Auras', 'living-energy': 'Big energy', 'eternal-might': 'Pure Zombie typal',
 'first-flight': 'Flyers with anthems and cost reducers', 'grave-danger': 'Value Zombies on a loop',
 'chaos-incarnate': 'Goad everything', 'draconic-destruction': 'More and better Dragons, some ramp',
 'token-triumph': 'Token doublers', 'lorehold-spirit': 'Discard engine',
 'squirreled-away': 'All Squirrels with Chatterfang',
}

# The user's queue (Nov 17, 2026): Silverquill, the five Starters, the rest, Revival Trance (Terra and Celes) last.
ORDER = ['silverquill-influence', 'first-flight', 'grave-danger', 'chaos-incarnate', 'draconic-destruction', 'token-triumph',
         'living-energy', 'eternal-might', 'lorehold-spirit', 'borg', 'federation-fleet', 'landing-party', 'klingon-fury',
         'revival-trance', 'revival-trance-celes', 'squirreled-away']

def write_index():
    """theme/index.json: one row per deck in decks/decks.json, ready decks first."""
    decks = json.load(open(os.path.join(ROOT, 'decks', 'decks.json')))
    rows = []
    decks['revival-trance-celes'] = {**decks['revival-trance'], 'name': 'Revival Trance (Celes)', 'cmd': 'Celes, Rune Knight',
                                     'img': 'https://cards.scryfall.io/normal/front/3/0/30584c53-533b-4dc7-b07c-8600164a99b3.jpg?1783906375'}
    decks['revival-trance'] = {**decks['revival-trance'], 'name': 'Revival Trance (Terra)'}
    # We run Chatterfang, the box's other commander, not Hazel.
    decks['squirreled-away'] = {**decks['squirreled-away'], 'name': 'Squirreled Away (Chatterfang)', 'cmd': 'Chatterfang, Squirrel General',
                                'img': 'https://cards.scryfall.io/normal/front/1/7/1785cf85-1ac0-4246-9b89-1a8221a8e1b2.jpg?1783926835'}
    for slug, d in decks.items():
        ready = os.path.exists(os.path.join(ROOT, 'theme', slug + '.json'))
        rows.append({'slug': slug, 'name': d['name'], 'cmd': d['cmd'], 'img': d['img'], 'direction': DIRECTIONS.get(slug),
                     'ready': ready})
    rows.sort(key=lambda r: ORDER.index(r['slug']) if r['slug'] in ORDER else len(ORDER))
    json.dump(rows, open(os.path.join(ROOT, 'theme', 'index.json'), 'w'), indent=0)

if __name__ == '__main__':
    if sys.argv[1:] == ['--index']: write_index()   # just the front screen's list
    else: main()
