"""Build treasure/index.html: the 25 most-played Treasure commanders on EDHREC that can run the Star Trek Ferengi Treasure cards,
each with a short gameplay synopsis and a line on how it works with those cards.
The Ferengi Treasure cards (the user's ask, Nov 27, 2026) are Grand Nagus Zek (B), Quark, Humble Proprietor, Rom and Leeta, Unlikely Pair
and Savvy Profiteer (R), so only commanders whose color identity has both black and red are kept (FERENGI_COLORS).
EDHREC's Treasure tag page (json.edhrec.com/pages/tags/treasure.json) lists only its top 24 commanders, so the color pages linked from it
(/tags/treasure/mono-red and so on, 32 of them) are merged too; each commander's count is the number of its decks EDHREC tags Treasure.
Only Commander-legal cards. Synopses (SYN) and Ferengi lines (FER: fit, line) are hand-written: add both for any new entrant. Same carousel as boros/ (cuts-template.html).
Run from the repo root:  python3 tools/carousel/treasure.py
"""
import manacost
import datetime, html, json, os, sys, urllib.parse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import get, record
OUT = os.path.join(ROOT, 'treasure')
N = 25
FERENGI_COLORS = {'B', 'R'}
FERENGI = ('Grand Nagus Zek', 'Quark, Humble Proprietor', 'Rom and Leeta, Unlikely Pair', 'Savvy Profiteer')
# Quark's "You can't sacrifice Treasure tokens" also stops Treasures making mana, so it only suits decks that count Treasures.
# Quark and Savvy Profiteer are Rogues, so they count as outlaws. Zek, Quark and Rom and Leeta are legendary.
FER = {
 'Mr. House, President and CEO': ('Some', 'Zek and Savvy Profiteer make Treasures to spend on extra dice, and Zek grows off the 6s. Keep Quark out: House needs to spend Treasure mana.'),
 'Prosper, Tome-Bound': ('Some', 'Prosper\'s exile plays make a Treasure each, so Zek grows every turn. Quark fights it: Prosper decks spend their Treasures.'),
 'Evereth, Viceroy of Plunder': ('Some', 'Zek and Savvy Profiteer make Treasures to feed Evereth for counters and lifelink. Quark stops that, since Evereth sacrifices them.'),
 'Vihaan, Goldwaker': ('Strong', 'Best fit. Quark makes a Treasure every upkeep and stops you spending them, so Vihaan\'s 3/3 Treasure army only grows. Quark and Savvy Profiteer are Rogues, so they get haste and vigilance, and Zek gets +1/+1 per Treasure.'),
 'Edward Kenway': ('Some', 'Savvy Profiteer makes extra Treasures, and blue card draw turns on Rom and Leeta. Quark gets in the way: Kenway decks spend Treasure on Vehicles.'),
 'Korvold, Fae-Cursed King': ('Good', 'Korvold draws on every sacrifice, so Rom and Leeta make two Treasures most turns, and Zek and Savvy add more fodder. Leave Quark out: Treasures are Korvold\'s cheapest sacrifices.'),
 "Ognis, the Dragon's Lash": ('Some', 'Every hasty attack makes a Treasure that grows Zek. The Ferengi have no haste, so they only add ramp.'),
 'Olivia, Opulent Outlaw': ('Good', 'Quark and Savvy Profiteer are Rogues, so they count as outlaws for Olivia\'s Treasures, and Zek grows off them. Quark stops her two-Treasure team pump.'),
 'Ziatora, the Incinerator': ('Good', 'Three Treasures every end step make Zek huge, and Ziatora\'s sacrifice triggers Zek\'s death Treasure too. With Quark out the Treasures stay as a pile instead of mana.'),
 'Admiral Brass, Unsinkable': ('Some', 'The Ferengi aren\'t Pirates, so they only add Treasures to cast the Pirates with.'),
 'Vazi, Keen Negotiator': ('Strong', 'Quark only stops you sacrificing Treasures: he makes one on every player\'s upkeep, Vazi hands opponents that many, and every time they spend one you draw and grow a creature. Rom and Leeta make two more on your second draw.'),
 'Admiral Beckett Brass': ('Some', 'The Ferengi aren\'t Pirates, so they only ramp you into more Pirates.'),
 'Don Andres, the Renegade': ('Some', 'Casting opponents\' spells makes two Treasures each, so Zek grows. Otherwise the Ferengi are just ramp.'),
 'Juri, Master of the Revue': ('Good', 'Zek makes a Treasure when a creature dies and Juri grows when you sacrifice it, so the two feed each other. Quark stops Juri sacrificing Treasures.'),
 'Jan Jansen, Chaos Crafter': ('Some', 'Jan turns artifact creatures into two Treasures, which Zek counts. Quark stops Jan sacrificing Treasures for Constructs.'),
 'Shadow the Hedgehog': ('Some', 'Treasure mana gives your spells split second, so Zek and Savvy Profiteer help. Quark shuts that off.'),
 'Malik, Grim Manipulator': ('Good', 'Every creature an opponent sacrifices makes a Treasure, and Zek makes one when any creature dies, so edicts pay twice.'),
 'Smaug the Impenetrable': ('Good', 'Wipes and pings on Smaug make piles of Treasures that make Zek huge. Quark keeps the pile on the board if you\'re building to a big Zek.'),
 'Laughing Jasper Flint': ('Good', 'Quark and Savvy Profiteer are Rogues, so each counts as an outlaw and exiles another card from an opponent every upkeep. Quark\'s Treasures can\'t pay for those cards, though.'),
 'Smaug, Wicked Worm': ('Strong', 'Every spell paid with Treasure draws a card, and the second draw each turn makes Rom and Leeta give two more Treasures, so they loop. Zek and Savvy Profiteer add fuel. Leave Quark out.'),
 'The Ur-Dragon': ('Some', 'The Ferengi aren\'t Dragons, so they only ramp into Dragons.'),
 'Dihada, Binder of Wills': ('Good', 'Zek, Quark and Rom and Leeta are legendary, so Dihada\'s -3 finds them, her +2 protects them, and the cards she bins make more Treasures.'),
 "The Balrog, Durin's Bane": ('Some', 'Sacrificed Treasures make the Balrog cheaper, and Zek makes more when creatures die. Quark stops that discount.'),
 'Mahadi, Emporium Master': ('Good', 'Mahadi makes a Treasure for each creature that died, and Zek adds one more, so any wipe or trade pays out. Zek grows off both.'),
 'Magar of the Magic Strings': ('Some', 'Draw spells turn on Rom and Leeta for two Treasures. Otherwise the Ferengi are just ramp.'),
}
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
 'Laughing Jasper Flint': 'Outlaw theft. Each upkeep exile cards off an opponent\'s library equal to your outlaw count and cast them with any mana. Stolen creatures become Mercenaries, so they count too.',
 'Smaug, Wicked Worm': 'Treasure card draw. Enters with a Treasure for each artifact your opponents have, and every spell paid with Treasure mana draws a card.',
 'The Ur-Dragon': 'Five-color Dragons. Dragons cost one less, and each Dragon attack draws cards and drops a permanent from hand for free.',
 'Dihada, Binder of Wills': 'Legends-matter planeswalker. Protects a legend, digs four cards for legends (the rest become Treasures), and ends with taking every nonland permanent for a turn.',
 "The Balrog, Durin's Bane": 'Sacrifice payoff. Costs one less for each permanent sacrificed this turn, can only be blocked by legends, and destroys something when it dies.',
 'Mahadi, Emporium Master': 'Aristocrats ramp. Every creature that died this turn, anyone\'s, makes a Treasure at your end step.',
 'Magar of the Magic Strings': 'Spell recursion. Turns an instant or sorcery in your graveyard into a 3/3 that recasts it free each time it hits a player.',
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
    names = [n for n, _ in sorted(decks.items(), key=lambda x: -x[1])][:N + 150]   # the black-red filter drops most of the list
    cards = {}
    for i in range(0, len(names), 75):
        r = subprocess.run(['curl', '-s', '-X', 'POST', '-H', 'Content-Type: application/json',
                            '-d', json.dumps({'identifiers': [{'name': n.split(' // ')[0]} for n in names[i:i+75]]}),
                            'https://api.scryfall.com/cards/collection'], capture_output=True, text=True)
        for c in json.loads(r.stdout)['data']: cards[c['name'].split(' // ')[0]] = c
    ALL, skipped = [], []
    for n in names:
        c = cards[n.split(' // ')[0]]
        if c['legalities']['commander'] != 'legal' or ' // ' in n or not FERENGI_COLORS <= set(c['color_identity']):   # ' // ' is a partner pairing
            skipped.append(n); continue
        if len(ALL) == N: break
        r = record(1, c)
        nm = c['name'].split(' // ')[0]
        r.update(k=['Ferengi fit: ' + FER[nm][0]], r=len(ALL) + 1, x=0, d=decks[n], y=SYN[nm], f=FER[nm][0], g=FER[nm][1],
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
        ALL.append(r)
    skipped = [n for n in skipped if n.split(' // ')[0] in cards and (' // ' in n or cards[n.split(' // ')[0]]['legalities']['commander'] != 'legal')]
    srcs = (f'<p><b>Only commanders that can run every Ferengi Treasure card:</b> {", ".join(FERENGI)} are black or red, so the list keeps commanders whose colors include both. '
            'Quark stops you sacrificing Treasures (so they make no mana while he is out): he suits decks that count Treasures, not ones that spend them. '
            'Quark and Savvy Profiteer are Rogues (outlaws); Zek, Quark and Rom and Leeta are legendary. Each card says how well it fits (Strong, Good, Some; filter by it under Keyword).</p>'
            f'<p><b>Source:</b> EDHREC\'s Treasure theme page and its color pages, read {today:%b} {today.day}, {today.year}: ranked by the number of decks '
            f'EDHREC tags Treasure for each commander. Card data from Scryfall. Left out: {html.escape(", ".join(skipped)) or "none"} '
            f'(partner pairings or not Commander-legal; commanders without both black and red are left out too). The gameplay lines are our own summaries of each card\'s text.</p>')
    cfg = {'slug': 'treasure', 'deck': 'Top 25 Treasure commanders for the Ferengi', 'set': 'Commander-legal', 'cmd': 'Any', 'alt': '', 'decks': N,
           'edh': 'https://edhrec.com/tags/treasure', 'srcs': srcs,
           'sub': f'The {N} most-played black-red Treasure commanders · how each works with the Ferengi'}
    t = open(os.path.join(HERE, 'cuts-template.html'), encoding='utf-8').read()
    old = "<b>#${c.r} most cut</b> · cut from ${pct(c.x)} of ${CFG.decks.toLocaleString('en-US')} decks"
    assert old in t
    t = t.replace(old, "<b>#${c.r} of " + str(N) + "</b> · ${c.d.toLocaleString('en-US')} Treasure decks</p><p class=\"cite\" style=\"text-transform:none;letter-spacing:0\">${c.y}</p><p class=\"cite\" style=\"text-transform:none;letter-spacing:0\"><b>Ferengi: ${c.f}.</b> ${c.g}")
    t = (t.replace('__TITLE__', 'Treasure commanders for the Ferengi').replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(manacost.fill(ALL), ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(t)
    print(len(ALL), [c['n'] for c in ALL], 'skipped', skipped)

main()
