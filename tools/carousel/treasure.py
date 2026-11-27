"""Build treasure/index.html: the 25 most-played Treasure commanders on EDHREC, each with a short gameplay synopsis.
EDHREC's Treasure tag page (json.edhrec.com/pages/tags/treasure.json) lists only its top 24 commanders, so the color pages linked from it
(/tags/treasure/mono-red and so on, 32 of them) are merged too; each commander's count is the number of its decks EDHREC tags Treasure.
Only Commander-legal cards. Synopses are hand-written (SYN): add one for any new entrant. Same carousel as boros/ (cuts-template.html).
Run from the repo root:  python3 tools/carousel/treasure.py
"""
import manacost
import datetime, html, json, os, sys, urllib.parse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import get, record
OUT = os.path.join(ROOT, 'treasure')
N = 25
SYN = {
 'Mr. House, President and CEO': 'Dice and Treasure. Rolls of 4 or more make 3/3 Robots, 6 or more add a Treasure, and Treasure mana spent on his ability adds dice. Dice-roll payoffs and Treasure makers feed each other.',
 'Magda, Brazen Outlaw': 'Dwarf typal. Every Dwarf that taps (attacking, crewing) makes a Treasure, and five Treasures tutor an artifact or Dragon straight onto the battlefield.',
 'Prosper, Tome-Bound': 'Exile-play value. Each end step gives you a card to play from exile, and every card played from exile makes a Treasure, so impulse draw ramps you as it draws.',
 'Evereth, Viceroy of Plunder': 'Artifact and Treasure sacrifice. Feed Treasures and creatures to a flyer that grows and gains lifelink, and when it dies it hits each opponent for its power.',
 'Vihaan, Goldwaker': 'Outlaws with Treasure armies. Outlaws get vigilance and haste, and each combat your Treasures can become 3/3 attackers, so piling up Treasure is piling up an army.',
 'Edward Kenway': 'Pirates, Assassins and Vehicles. Each tapped one makes a Treasure at end step, and Vehicles that connect steal the top card of the defender\'s library.',
 'Korvold, Fae-Cursed King': 'Sacrifice engine. Each permanent you sacrifice grows Korvold and draws a card, so Treasures, Food and Clues turn into cards and a huge flyer.',
 "Ognis, the Dragon's Lash": 'Haste aggro. Every hasty attacker makes a tapped Treasure, so a deck of haste creatures and haste-granters ramps while it beats down.',
 'Olivia, Opulent Outlaw': 'Outlaw aggro. Outlaws that connect make a Treasure, and two Treasures put two +1/+1 counters on your whole team. A lifelink flyer leads it.',
 'Ziatora, the Incinerator': 'Fling and ramp. Each end step sacrifice a creature to deal its power to any target and make three Treasures. Big or token-making creatures fuel it.',
 'Admiral Brass, Unsinkable': 'Pirate reanimator. Mill Pirates, then each combat return one as a hasty 4/4. Treasure-making Pirates keep the mana flowing.',
 'Vazi, Keen Negotiator': 'Group-hug Treasure. Hand opponents Treasures, and each time they spend Treasure mana you draw a card and put a counter on a creature.',
 'Roxanne, Starfall Savant': 'Artifact-token ramp. Each attack or entry makes a Meteorite that shocks something, and every artifact token you tap for mana makes double, Treasures included.',
 'Rev, Tithe Extractor': 'Steal-and-ramp. Hitting a player makes a Treasure and exiles their top card for you to cast, with a deathtouch attacker to make blocks bad.',
 'Jolene, the Plunder Queen': 'Treasure doubler and politics. Anyone attacking your opponents gets a Treasure, you make one extra whenever you make any, and five Treasures grow Jolene.',
 'Admiral Beckett Brass': 'Pirate typal. Pirates get +1/+1, and if three of them hit one player in a turn you steal one of that player\'s nonland permanents.',
 'Don Andres, the Renegade': 'Theft. Stolen creatures become 2/2-bigger deathtouch, menace Pirates, and casting opponents\' noncreature spells makes two Treasures each.',
 'Galazeth Prismari': 'Artifact spellslinger. Every artifact taps for any color for instants and sorceries, so Treasures and rocks double as spell mana.',
 'Juri, Master of the Revue': 'Aristocrats. Every sacrifice grows Juri, and when it dies it throws its power at any target. Treasures are cheap sacrifice fodder.',
 "Thorin, King of Durin's Folk": 'Dwarves and Treasure. Each Dwarf entering makes a Treasure, and Dwarves get +1/+0 per artifact token, so mana and a growing aggressive board come together.',
 'Jan Jansen, Chaos Crafter': 'Artifact loop. Sacrifice artifact creatures for two Treasures and noncreature artifacts for two Constructs, trading one into the other.',
 'Rashmi and Ragavan': 'Free spells from opponents. Your first spell each turn exiles an opponent\'s top card and makes a Treasure; cast it free if it\'s cheaper than your artifact count.',
 'Shadow the Hedgehog': 'Haste and artifact mana. Hasty creatures dying draw cards, and any spell paid with artifact mana (Treasures) gets split second.',
 'Malik, Grim Manipulator': 'Edicts. Every creature an opponent sacrifices makes you a Treasure, so forced-sacrifice effects remove threats and ramp you.',
 'Smaug the Impenetrable': 'Self-damage Treasure. An indestructible hasty flyer that makes a Treasure per point of noncombat damage dealt to it, so pingers and wipes like Blasphemous Act pay out.',
}

def main():
    today = datetime.date.today()
    page = json.loads(get('https://json.edhrec.com/pages/tags/treasure.json'))
    def tops(p):
        return [c for cl in p['container']['json_dict']['cardlists'] if cl.get('header') == 'Top Commanders' for c in cl['cardviews']]
    decks = {}
    def add(cs):
        for c in cs:
            n = c['name']
            decks[n] = max(decks.get(n, 0), c['num_decks'])
    add(tops(page))
    for u in [i['url'] for g in page['related_info'] for i in g['items']]:
        try: add(tops(json.loads(get('https://json.edhrec.com/pages' + u + '.json'))))
        except Exception as e: print('skip', u, e)
    names = [n for n, _ in sorted(decks.items(), key=lambda x: -x[1])][:N + 15]
    cards = {}
    for i in range(0, len(names), 75):
        r = subprocess.run(['curl', '-s', '-X', 'POST', '-H', 'Content-Type: application/json',
                            '-d', json.dumps({'identifiers': [{'name': n.split(' // ')[0]} for n in names[i:i+75]]}),
                            'https://api.scryfall.com/cards/collection'], capture_output=True, text=True)
        for c in json.loads(r.stdout)['data']: cards[c['name'].split(' // ')[0]] = c
    ALL, skipped = [], []
    for n in names:
        c = cards[n.split(' // ')[0]]
        if c['legalities']['commander'] != 'legal' or ' // ' in n:   # ' // ' is a partner pairing, not one commander
            skipped.append(n); continue
        if len(ALL) == N: break
        r = record(1, c)
        r.update(k=c.get('keywords', []), r=len(ALL) + 1, x=0, d=decks[n], y=SYN[c['name'].split(' // ')[0]],
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
        ALL.append(r)
    srcs = (f'<p><b>Source:</b> EDHREC\'s Treasure theme page and its color pages, read {today:%b} {today.day}, {today.year}: ranked by the number of decks '
            f'EDHREC tags Treasure for each commander. Card data from Scryfall. Left out: {html.escape(", ".join(skipped)) or "none"} '
            f'(partner pairings or not Commander-legal). The gameplay lines are our own summaries of each card\'s text.</p>')
    cfg = {'slug': 'treasure', 'deck': 'Top 25 Treasure commanders', 'set': 'Commander-legal', 'cmd': 'Any', 'alt': '', 'decks': N,
           'edh': 'https://edhrec.com/tags/treasure', 'srcs': srcs,
           'sub': f'The {N} most-played Treasure commanders · with how each plays'}
    t = open(os.path.join(HERE, 'cuts-template.html'), encoding='utf-8').read()
    old = "<b>#${c.r} most cut</b> · cut from ${pct(c.x)} of ${CFG.decks.toLocaleString('en-US')} decks"
    assert old in t
    t = t.replace(old, "<b>#${c.r} of " + str(N) + "</b> · ${c.d.toLocaleString('en-US')} Treasure decks</p><p class=\"cite\" style=\"text-transform:none;letter-spacing:0\">${c.y}")
    t = (t.replace('__TITLE__', 'Top 25 Treasure commanders').replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(manacost.fill(ALL), ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(t)
    print(len(ALL), [c['n'] for c in ALL], 'skipped', skipped)

main()
