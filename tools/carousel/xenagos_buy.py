"""Build xenagos-to-buy.html: a carousel of only the Xenagos deck cards we don't have yet.

The 50 spells bought from TCGplayer on Oct 28, 2026 all arrived (checked Nov 10), so what's left is
the 16 spells below and the 34 lands. Card names come from xenagos.html's deck list; card data and
image links from Scryfall. Price is the cheapest paper printing, since these are to buy.
Run from the repo root:  python3 tools/carousel/xenagos_buy.py
"""
import html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make import scryfall, record, cheapest  # same card records as the precon carousels

SPELLS = ['Emrakul, the Promised End', 'Aggravated Assault', 'Lurking Predators', 'World at War',
          'Wurmcoil Engine', 'Savage Beating', 'Horn of Greed', 'Timesifter', 'Collective Voyage',
          'Malignus', 'Temple Bell', 'Lotus Cobra', 'Strionic Resonator', 'Overabundance',
          'New Frontiers', 'Mass Hysteria']
LANDS = ['Command Tower', 'Exotic Orchard', 'Cinder Glade', 'Rugged Highlands', 'Gruul Turf',
         'Evolving Wilds', 'Terramorphic Expanse', 'Ash Barrens', 'Myriad Landscape', 'Kessig Wolf Run',
         "Rogue's Passage", 'Havenwood Battleground', 'Mosswort Bridge', 'Crystal Vein',
         'Temple of the False God', 'Haunted Fengraf']
BASICS = [(9, 'Forest'), (9, 'Mountain')]

lst = [(1, {'name': n}, n) for n in SPELLS + LANDS] + [(q, {'name': n}, n) for q, n in BASICS]
ALL = []
for qty, c in scryfall(lst):
    r = record(qty, c)
    low = cheapest(r['n'])
    if low is not None: r['p'] = low
    ALL.append(r)
rank = lambda r: 2 if 'Basic Land' in r['t'] else 1 if 'Land' in r['t'] else 0
ALL.sort(key=lambda r: (rank(r), -(r['p'] or 0)))

total = sum(r['q'] for r in ALL)
price = sum((r['p'] or 0) * r['q'] for r in ALL)
cfg = {'slug': 'xenagos-buy', 'deck': 'Xenagos: still to buy',
       'set': f'{len(SPELLS)} spells, {len(LANDS)} nonbasic lands, 18 basics · cheapest printings',
       'cmd': 'Xenagos, God of Revels', 'alt': None}
t = open(os.path.join(HERE, 'template.html')).read()
t = (t.replace('__TITLE__', 'Xenagos To Buy')
      .replace('href="./">‹ All decks', 'href="xenagos.html">‹ Xenagos deck')
      .replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
      .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
open(os.path.join(HERE, '..', '..', 'xenagos-to-buy.html'), 'w').write(t)
print(f'{total} cards, ${price:.2f}, not legal: {[r["n"] for r in ALL if r.get("note")]}')
