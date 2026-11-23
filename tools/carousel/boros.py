"""Build boros/index.html: the 25 most-played red-white (Boros) commanders on EDHREC, each with a short gameplay synopsis.
EDHREC's boros page (json.edhrec.com/pages/commanders/boros.json) gives the ranking and deck counts; Scryfall gives the card data.
Only Commander-legal cards whose own color identity is exactly red-white (Ardenn alone is mono-white: it is a partner pairing). Synopses are hand-written (SYN).
Same carousel as squirrels/ (cuts-template.html, caption swapped). Run from the repo root:  python3 tools/carousel/boros.py
"""
import datetime, html, json, os, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import get, record
OUT = os.path.join(ROOT, 'boros')
N = 25
SYN = {
 'Arabella, Abandoned Doll': 'Go-wide with small creatures. Every attack drains each opponent and heals you for the number of power-2-or-less creatures you control. Cheap tokens, weenies and anthems make the drain huge.',
 'Ragost, Deft Gastronaut': 'Artifact and Food sacrifice. Every artifact is a Food, so you sacrifice them for 3 life each and Ragost pings everyone for 3 per Food. Gaining life untaps Ragost for more activations.',
 'Lightning, Army of One': 'Voltron. A cheap first-strike, trample, lifelink body that doubles all damage to a player it connects with, so equipment and pump turn into fast kills.',
 'Winota, Joiner of Forces': 'Non-Human attackers (usually tokens) cheat in Humans attacking and indestructible, such as Angel of Sanctions or Hero of Bladehold style bombs. Turn after turn it snowballs.',
 'Feather, the Redeemed': 'Spellslinger Voltron. Targeted instants and sorceries return to hand each end step, so cheap protection, pump and auras get recast over and over.',
 'Lorehold, the Historian': 'Flying haste dragon that gives every instant and sorcery miracle {2}. Loot each opponent upkeep to find a big spell, then cast it for two mana.',
 'Quintorius, History Chaser': 'Graveyard planeswalker commander. Cards leaving your graveyard make 3/2 Spirits, so flashback, escape, and rummaging build an army that gains double strike.',
 'The Jolly Balloon Man': 'Clone-and-attack. Each turn it makes a hasty flying 1/1 copy of your best creature, so enters-the-battlefield and attack triggers fire again and again.',
 "Thorin, King of Durin's Folk": 'Dwarves and treasure. Each Dwarf entering makes a Treasure, and Dwarves get +1/+0 per artifact token, so mana and a growing aggressive board come together.',
 'Mabel, Heir to Cragflame': 'Mice tribal with equipment. Mabel pumps your Mice and hands you a free hasty, trampling Cragflame, so you go wide and fast.',
 'Nahiri, Forged in Fury': 'Equipment attack engine. It costs less per Equipment and each equipped attacker exiles a card to play, even casting Equipment free. Lots of card advantage in combat.',
 'Nelly Borca, Impulsive Accuser': 'Politics and goad. It suspects a creature, goads everything suspected, and draws cards for you and whoever hits your opponents, so the table fights itself.',
 'Bre of Clan Stoutarm': 'Lifegain engine. Gain life, then at end step flip cards off the top and cast a spell up to that many mana value for free, or keep the card. Bigger gains hit harder.',
 'General Ferrous Rokiric': 'Gold-card matters. Every multicolored spell makes a 4/4 Golem, and hexproof from monocolored shields the General. Fill the deck with Boros and gold cards.',
 'Anim Pakal, Thousandth Moon': 'Counters and tokens. Each attack grows Anim Pakal and makes that many attacking Gnomes, so non-Gnome attackers snowball the board quickly.',
 'Sami, Wildcat Captain': 'Artifact cost reduction. Every spell gets cheaper for each artifact you have, so you chain big spells and artifacts while hitting with a double-strike body.',
 'Aurelia, the Warleader': 'The classic Boros extra-combat commander. Flying, haste and vigilance, with an untap and a second combat each turn. Big attackers, anthems and Voltron pieces end games fast.',
 'Taii Wakeen, Perfect Shot': 'Noncombat damage and pingers. It draws when you kill creatures with spell damage and pumps all noncombat damage with X, so burn, fling and damage-doublers do the work.',
 "Otharri, Suns' Glory": 'Experience-counter recursion. Each attack makes more and more 2/2 Rebels attacking, and it comes back from the graveyard by tapping a Rebel.',
 'Osgir, the Reconstructor': 'Artifact recursion. Exile artifacts from your graveyard to make two copies, sacrifice artifacts to pump creatures, and replay your best equipment and rocks.',
 'Firesong and Sunspeaker': 'Lifegain burn. Red instants and sorceries gain lifelink and white lifegain spells deal 3 damage to a target, so removal and burn double as drain.',
 'Bruenor Battlehammer': 'Equipment Voltron. Each attached Equipment gives +2/+0 and the first equip each turn is free, so you move gear around freely.',
 'Kolodin, Triumph Caster': 'Vehicles and Mounts. They get haste, Vehicles become creatures on entering, and Mounts are saddled, giving you a fast, aggressive artifact deck.',
 'Iroh, Tea Master': 'Group-hug politics. It gives permanents to opponents on purpose, makes Ally tokens that grow for each permanent you own that they control, and rewards stealing effects.',
 'Brion Stoutarm': 'Sacrifice and fling. A lifelink body that sacrifices creatures to throw their power at a player or planeswalker, ending the game with big or recurring creatures.',
}

def main():
    today = datetime.date.today()
    top = json.loads(get('https://json.edhrec.com/pages/commanders/boros.json'))['container']['json_dict']['cardlists'][0]['cardviews']
    decks = {c['name'].split(' // ')[0]: c['num_decks'] for c in top}
    names = list(decks)
    body = {'identifiers': [{'name': n} for n in names]}
    import subprocess
    cards = {}
    for i in range(0, len(names), 75):
        r = subprocess.run(['curl', '-s', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps({'identifiers': body['identifiers'][i:i+75]}),
                            'https://api.scryfall.com/cards/collection'], capture_output=True, text=True)
        for c in json.loads(r.stdout)['data']: cards[c['name'].split(' // ')[0]] = c
    ALL, skipped = [], []
    for n in names:
        c = cards[n]
        if c['legalities']['commander'] != 'legal' or sorted(c['color_identity']) != ['R', 'W']:
            skipped.append(n); continue
        if len(ALL) == N: break
        r = record(1, c)
        r.update(k=c.get('keywords', []), r=len(ALL) + 1, x=0, d=decks[n], y=SYN[n],
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
        ALL.append(r)
    srcs = (f'<p><b>Source:</b> EDHREC\'s Boros commanders page, read {today:%b} {today.day}, {today.year}: ranked by the number of decks built around each commander. '
            f'Card data from Scryfall. Left out: {html.escape(", ".join(skipped)) or "none"} (mono-white on its own or not Commander-legal). The gameplay lines are our own summaries of each card\'s text.</p>')
    cfg = {'slug': 'boros', 'deck': 'Top 25 Boros commanders', 'set': 'Commander-legal', 'cmd': 'Any', 'alt': '', 'decks': N,
           'edh': 'https://edhrec.com/commanders/boros', 'srcs': srcs,
           'sub': f'The {N} most-played red-white commanders · with how each plays'}
    t = open(os.path.join(HERE, 'cuts-template.html'), encoding='utf-8').read()
    old = "<b>#${c.r} most cut</b> · cut from ${pct(c.x)} of ${CFG.decks.toLocaleString('en-US')} decks"
    assert old in t
    t = t.replace(old, "<b>#${c.r} of " + str(N) + "</b> · ${c.d.toLocaleString('en-US')} decks</p><p class=\"cite\" style=\"text-transform:none;letter-spacing:0\">${c.y}")
    t = (t.replace('__TITLE__', 'Top 25 Boros commanders').replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(t)
    print(len(ALL), [c['n'] for c in ALL], 'skipped', skipped)

main()
