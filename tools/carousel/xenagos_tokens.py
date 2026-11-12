"""Build xenagos-tokens.html: every token the Xenagos group hug deck makes, as print-and-cut cards,
9 per US Letter page at real card size (2.5 x 3.5 in), same layout as xenagos-proxies.html.
The PDF copy (xenagos-tokens.pdf) is printed from this page with Playwright, Letter size, no margins.
Print at 100% / Actual size, not Fit to page.

How many of each (worked out from the deck, Nov 2026; see decks/tokens.html for who makes what):
- Eldrazi Spawn 14: Rapacious One makes one per combat damage. Xenagos doubles it to 10 power with
  trample, and the deck has extra combats (Relentless Assault, Seize the Day, Aggravated Assault) and
  double strike (Savage Beating), so 10 or more in one turn is normal. Three Rise of the Eldrazi arts.
- Plant 14: Avenger of Zendikar makes one per land you control, and this deck ramps hard.
- Copy 8: Dual Nature gives every player a copy of each nontoken creature that enters; Blade of
  Selves makes 2 at a 4-player table. Lay a Copy card under a spare card or proxy of what it copies.
- Elephant 3: Terastodon destroys up to three, one Elephant for each permanent's controller.
- Lightning Rager 2: Rite of the Raging Storm gives one to each player in their upkeep and it dies at
  the end step, so one is out at a time; a second for Strionic Resonator copying the trigger.
- Beast 1 (Beast Within), Wurm with deathtouch 1 and Wurm with lifelink 1 (Wurmcoil Engine), and
  Garruk, Caller of Beasts' emblem 1.
That's 45 cards, five full pages.
Run from the repo root:  python3 tools/carousel/xenagos_tokens.py
"""
import html, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
CDN = 'https://cards.scryfall.io/large/front/'
SPAWN = [CDN + 'e/0/e0e3826c-3c85-4910-bd6c-04894ea328d0.jpg', CDN + '3/5/35fb1a3d-3f1a-45ba-a643-1dca435c77de.jpg',
         CDN + 'd/0/d0da4f8d-cce9-4d08-8d11-792e0b2af7d0.jpg']  # troe 1a, 1b, 1c
TOKENS = [  # (name, count, image), in the order they print
    ('Eldrazi Spawn', 14, None),
    ('Plant', 14, CDN + '3/d/3db07715-d315-4361-8af5-ce68d20e6c08.jpg'),
    ('Copy', 8, CDN + '4/5/45364163-62b7-4641-b2c9-c2e46d61335c.jpg'),
    ('Elephant', 3, CDN + '2/8/2853ba8b-650e-49e3-ab12-86b76e02743b.jpg'),
    ('Lightning Rager', 2, CDN + '8/2/8292126c-a7b4-40d3-8a08-f15dd871207d.jpg'),
    ('Beast', 1, CDN + 'c/a/ca8e8a9a-d673-4644-9eec-f4f549307d9b.jpg'),
    ('Wurm (deathtouch)', 1, CDN + 'b/6/b68e816f-f9ac-435b-ad0b-ceedbe72447a.jpg'),
    ('Wurm (lifelink)', 1, CDN + 'a/6/a6ee0db9-ac89-4ab6-ac2e-8a7527d9ecbd.jpg'),
    ('Garruk, Caller of Beasts emblem', 1, CDN + 'd/1/d16429cb-9b00-4411-9ffc-252b38ad0b8c.jpg'),
]

cards = []
for name, n, url in TOKENS:
    cards += [(name, url or SPAWN[i % 3]) for i in range(n)]
pages = [cards[i:i + 9] for i in range(0, len(cards), 9)]
body = ''.join('<section class="pg">' + ''.join(f'<img src="{html.escape(u)}" alt="{html.escape(n)} token">' for n, u in p) + '</section>' for p in pages)
board = re.search(r'<!-- app-board-link.*?</script>', open(os.path.join(ROOT, 'xenagos-proxies.html')).read(), re.S).group(0)

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Xenagos Tokens</title>
{board}
<style>
/* Same sheet as xenagos-proxies.html: 3 x 3 cards of 2.5 x 3.5 in, centred on Letter, one cut along each grey line. */
@page{{size:letter;margin:0}}
html{{background:#ccc}}body{{margin:0}}
.pg{{width:8.5in;height:11in;box-sizing:border-box;padding:.25in .5in;background:#fff;margin:16px auto;
  display:grid;grid-template-columns:repeat(3,2.5in);grid-template-rows:repeat(3,3.5in);align-content:start;break-after:page}}
.pg img{{width:2.5in;height:3.5in;display:block;outline:.5px solid #999;outline-offset:-.25px}}
@media print{{html{{background:#fff}}.pg{{margin:0}}.pg:last-child{{break-after:auto}}a[href="/commander-life/"]{{display:none!important}}}}
</style></head><body>{body}</body></html>
'''
open(os.path.join(ROOT, 'xenagos-tokens.html'), 'w').write(page)
print(len(cards), 'tokens on', len(pages), 'pages')
