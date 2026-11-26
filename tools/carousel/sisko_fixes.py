"""Build sisko/fixes.html: 50 cards to shore up the Captain Benjamin Sisko deck's two weak spots
(the user, Nov 26, 2026: low mana ramp, and open to flyers), every one of them modal, so each cast or
trigger is a dilemma Sisko counts toward his end-step Officers.

How the 50 were picked: Scryfall's Commander-legal paper cards with modes (bulleted "choose one /
two / one or more / up to", escalate, entwine, spree), about 780, were sorted by what a mode does:
ramp (land search, land drops, mana, Treasure) or flyer defense (reach, a flying blocker, damage or
destroy aimed at flyers). From those, the 50 below were picked by hand, cards that do both first,
then by how much each fixes and how cheap it is, with EDHREC's Sisko page (json.edhrec.com/pages/
commanders/captain-benjamin-sisko.json) as the play share. Hand-kept (PICKS) because "best" is a call.
Left out: the cards already picked for the deck (both Nov 25 proxy sheets, SKIP), and Kozilek's
Command (needs {C}{C}). Same carousel as boros/ (cuts-template.html, caption swapped).
Run from the repo root:  python3 tools/carousel/sisko_fixes.py
"""
import manacost
import datetime, html, json, os, subprocess, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import get, record
OUT = os.path.join(ROOT, 'sisko')
R, F = 'Ramp', 'Flyer defense'
# (name, roles, why) in rank order. Roles go in the Kind filter.
PICKS = [
 ("Kura, the Boundless Sky", [R, F, 'Flying'], 'A 4/4 flying deathtouch wall that kills any flyer it blocks. When it dies, fetch three lands to hand or make a huge Spirit.'),
 ("Black Market Connections", [R], 'Treasure every turn, and a dilemma every turn: choose one or more of Treasure, card, 3/2 body. The most-played ramp in Sisko decks.'),
 ("Nylea's Intervention", [R, F], 'Ramp or wrath: X lands to hand, or twice X damage to every flyer (your Officers have no wings).'),
 ("Archdruid's Charm", [R, F], 'Instant: a land onto the battlefield, or a +1/+1 counter and the creature bites a flyer, or exile an artifact or enchantment.'),
 ("Pick Your Poison", [F], 'One mana: each opponent sacrifices a flyer. Dodges hexproof and ward. Artifact and enchantment modes when the air is clear.'),
 ("Atarka's Command", [R, F, 'Reach'], 'Choose two: drop an extra land, give your whole team +1/+1 and reach, burn each opponent for 3, or stop lifegain.'),
 ("Elder Gargaroth", [F, 'Reach'], 'A 6/6 reach, vigilance blocker. Every block or attack is a dilemma: a 3/3 Beast, 3 life or a card.'),
 ("Konstrari Charm", [R, F], 'Two mana: 6 damage to a flyer, or add {C}{C}{C} for a big turn, or +2 counters and trample.'),
 ("Galadriel, Light of Valinor", [R], 'Every creature you make (Officers too) adds {G}{G}{G}, grows the team or draws. Up to three dilemmas a turn.'),
 ("Pawpatch Formation", [F], 'Instant, two mana: destroy a flyer, or an enchantment, or draw a card and make a Food.'),
 ("Prismari Command", [R, F], 'Choose two: Treasure, 2 damage to a flyer or face, loot two, destroy an artifact. Usually Treasure plus kill.'),
 ("Austere Command", [F], 'Wrath the big stuff: creatures with mana value 4 or more die, your 1/1 Officers (tokens, value 0) live. Add artifacts or enchantments.'),
 ("Bushwhack", [R, F], 'One mana: a basic land to hand, or fight a flyer with your biggest creature.'),
 ("Silverback Elder", [R], 'Every creature spell is a dilemma: a land from the top five onto the battlefield, kill an artifact or enchantment, or 4 life.'),
 ("Atsushi, the Blazing Sky", [R, F, 'Flying'], 'A 4/4 flying blocker. When it dies, three Treasures or two cards to play.'),
 ("Melkotian Adjudicator", [F, 'Flying'], 'Star Trek. Flying, vigilance, and a +1/+1 counter every time you face a dilemma: a blocker that keeps up with their dragons.'),
 ("Gruul Charm", [F], 'Two mana: 3 damage to each flyer and only flyers, so your board stays. Or your ground team can\'t be blocked by ground creatures.'),
 ("Titania's Command", [R], 'Choose two: two lands onto the battlefield, two 2/2 Bears, counters on the team, or exile a graveyard.'),
 ("Dreamshackle Geist", [F, 'Flying'], 'A flyer that taps their best flyer every combat or locks it down next turn. A dilemma on each of your turns.'),
 ("Take Down", [F], 'One mana: 4 damage to a flyer, or 1 to every flyer (Birds, Spirits, Thopters).'),
 ("Journey of Discovery", [R], 'Two basics to hand, or two extra land drops this turn. Entwine for both.'),
 ("Ao, the Dawn Sky", [F, 'Flying'], 'A 5/4 flying, vigilance blocker. When it dies, put cheap permanents onto the battlefield or two counters on everything.'),
 ("Reap and Sow", [R], 'Any land, not just a basic, onto the battlefield untapped. Entwine to also kill a land.'),
 ("Titan of Industry", [F, 'Reach'], 'A 7/7 reach blocker. Choose two: a 4/4 Rhino, a shield counter, 5 life, or kill an artifact or enchantment.'),
 ("Return from the Wilds", [R], 'Choose two: a basic onto the battlefield, a 1/1 Human, a Food.'),
 ("Set Phasers to . . .", [F], 'Star Trek, one mana: stun their flyer, or 3 damage to an attacking creature.'),
 ("Jeska's Will", [R], 'With Sisko out, choose both: a pile of red mana and three cards to play. A Game Changer.'),
 ("Collective Effort", [F], 'Destroy a creature with power 4 or more (most dragons), an enchantment, and counters on your team. Escalate by tapping Officers.'),
 ("Dance of the Tumbleweeds", [R], 'Spree: a basic onto the battlefield untapped, an X/X Elemental, or both.'),
 ("Unforgiving Aim", [F], 'Destroy a flyer, or an enchantment, or make a 2/2 Elf.'),
 ("Evolution Charm", [R, F], 'Instant: a basic to hand, a creature back from the graveyard, or give a blocker flying.'),
 ("Hawkeye, Master Marksman", [F, 'Reach'], 'Two-mana reach, first strike: blocks a flyer and hits first. Pay to choose up to three modes when it taps.'),
 ("Culber and Stamets, Star-Crossed", [R], 'Star Trek. A 4-mana body that refunds two mana of any one color, or puts a counter on a creature.'),
 ("Warg Tactics", [F], 'Destroy a flyer, or protect and pump your own creature.'),
 ("Emerald Charm", [R, F], 'One mana: untap a land or rock, or a flyer loses flying, or destroy an enchantment.'),
 ("Aether Channeler", [F, 'Flying'], 'A 1/1 flying Bird blocker, a bounce, or a card.'),
 ("Charming Scoundrel", [R], 'Two-mana haste: a Treasure, a Wicked Role or a rummage.'),
 ("Glorious Decay", [F], '4 damage to a flyer, or kill an artifact, or exile a graveyard card and draw.'),
 ("Thirsting Roots", [R], 'One mana: a basic to hand, or proliferate.'),
 ("Junji, the Midnight Sky", [F, 'Flying'], 'A 5/5 flying, menace blocker. When it dies, reanimate a creature or make each opponent discard two.'),
 ("Plundering Barbarian", [R], 'A Treasure, or destroy an artifact.'),
 ("Shredded Sails", [F], '4 damage to a flyer, or kill an artifact, or cycle it.'),
 ("You Happen On a Glade", [R], 'Two basics to hand, or a permanent back from the graveyard.'),
 ("Sarkhan's Resolve", [F], 'Destroy a flyer, or +3/+3 in combat.'),
 ("Saurian Symbiote", [F, 'Reach'], 'A reach blocker that comes with a counter or a 1/1 Saproling.'),
 ("Choose Your Weapon", [F], '5 damage to a flyer, or double a creature\'s power and toughness.'),
 ("Open the Omenpaths", [R], 'Four mana in two colors for creatures or enchantments, or +1/+0 to your team.'),
 ("Clan Defiance", [F], 'X damage to a flyer, a ground creature and a player, any or all of them.'),
 ("Momo, Playful Pet", [F, 'Flying'], 'A one-mana flying, vigilance chump blocker. When it leaves, a Food, a counter or scry 2.'),
 ("Glamermite", [F, 'Flying'], 'Flash flyer: tap their attacking flyer, or untap your own blocker.'),
]
SKIP = ["Ni'Var Science Academy", 'Q Continuum', 'Deanna Troi, Psychic Counsel', 'Captain Kathryn Janeway',
        'Captain James T. Kirk', 'Captain Jean-Luc Picard', 'Academy Instructor', 'Gala Greeters', 'Felidar Retreat',
        'Impossible Choice', 'Test of Priorities', 'Cryptic Command', 'Resistance Is Futile']

def main():
    today = datetime.date.today()
    names = [p[0] for p in PICKS]
    assert len(names) == 50 and len(set(names)) == 50 and not set(names) & set(SKIP), 'need 50 new, unique picks'
    ed = json.loads(get('https://json.edhrec.com/pages/commanders/captain-benjamin-sisko.json'))['container']['json_dict']
    share = {c['name']: c['num_decks'] / c['potential_decks'] for l in ed['cardlists'] for c in l['cardviews'] if c.get('potential_decks')}
    cards = {}
    for i in range(0, len(names), 75):
        r = subprocess.run(['curl', '-s', '-X', 'POST', '-H', 'Content-Type: application/json', '-H', 'Accept: application/json',
                            '-H', 'User-Agent: commander-life/1.0', '-d', json.dumps({'identifiers': [{'name': n} for n in names[i:i+75]]}),
                            'https://api.scryfall.com/cards/collection'], capture_output=True, text=True)
        got = json.loads(r.stdout)
        assert not got['not_found'], got['not_found']
        for c in got['data']: cards[c['name']] = c
    ALL = []
    for i, (n, roles, why) in enumerate(PICKS):
        c = cards[n]
        r = record(1, c)  # flags "Not Commander-legal" itself (house rule); all 50 are legal as of Nov 26, 2026
        if c.get('game_changer'): r['note'] = (r.get('note', '') + ' · ' if r.get('note') else '') + 'Game Changer'
        s = share.get(n)
        r.update(k=roles, r=i + 1, x=0, y=html.escape(why),
                 d=(f'in {round(s * 100)}% of Sisko decks' if s else 'new to Sisko decks on EDHREC'),
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{n}"'))
        ALL.append(r)
    n_both = sum(1 for p in PICKS if R in p[1] and F in p[1])
    srcs = (f'<p><b>What this is:</b> 50 cards for the Captain Benjamin Sisko deck\'s weak spots, low ramp and flyers. Every one is modal, '
            f'so each cast or trigger is a dilemma, and Sisko makes an Officer for each at your end step. {n_both} do both jobs. '
            f'Kind filter: Ramp, Flyer defense, Reach, Flying.</p>'
            f'<p><b>How they were picked:</b> every Commander-legal paper card on Scryfall with modes (choose one, two, one or more, up to; escalate, entwine, spree), '
            f'about 780 cards, sorted by what its modes do: ramp (land search, extra land drops, mana, Treasure) or flyer defense (reach, a flying blocker, '
            f'damage or destroy aimed at flyers). The 50 were then ranked by hand: cards that do both first, then by how much each fixes and how cheap it is. '
            f'The share line is EDHREC\'s Captain Benjamin Sisko page, read {today:%b} {today.day}, {today.year} ({ed["card"]["num_decks"] if "card" in ed else "about 900"} decks). '
            f'The why lines are our own summaries of each card\'s text.</p>'
            f'<p><b>Left out:</b> the cards already picked for the deck ({html.escape(", ".join(SKIP))}), and Kozilek\'s Command (needs {{C}}{{C}}). '
            f'Not modal, so not here: plain ramp like Farseek and Cultivate, and plain reach creatures.</p>')
    cfg = {'slug': 'sisko-fixes', 'deck': 'Sisko: ramp and flyer fixes', 'set': 'Commander-legal', 'cmd': 'Any', 'alt': '', 'decks': 50,
           'edh': 'https://edhrec.com/commanders/captain-benjamin-sisko', 'srcs': srcs,
           'sub': f'50 modal cards (every one a dilemma) for more ramp and flyer defense · {n_both} do both'}
    t = open(os.path.join(HERE, 'cuts-template.html'), encoding='utf-8').read()
    old = "<b>#${c.r} most cut</b> · cut from ${pct(c.x)} of ${CFG.decks.toLocaleString('en-US')} decks"
    assert old in t and 'Most cut first' in t
    t = t.replace(old, "<b>#${c.r} of 50</b> · ${c.k.filter(k=>k=='Ramp'||k=='Flyer defense').join(' + ')} · ${c.d}</p>"
                       "<p class=\"cite\" style=\"text-transform:none;letter-spacing:0\">${c.y}")
    t = t.replace('Most cut first', 'Best first')
    assert 'id="back" href="./"' in t  # sisko/ has no index page: Back goes to the table of contents
    t = t.replace('id="back" href="./"', 'id="back" href="../links.html"')
    t = (t.replace('__TITLE__', 'Sisko Fixes').replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(manacost.fill(ALL), ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'fixes.html'), 'w', encoding='utf-8', newline='\n').write(t)
    bad = [r['n'] for r in ALL if r.get('note', '').startswith('Not')]
    print(len(ALL), 'cards; both:', n_both, '; not legal:', bad, '; GC:', [r['n'] for r in ALL if 'Game Changer' in r.get('note', '')],
          f'; ${sum(r["p"] or 0 for r in ALL):.2f}')

main()
