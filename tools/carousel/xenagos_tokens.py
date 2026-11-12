"""Build xenagos-tokens.html: every token the Xenagos group hug deck makes, as double-sided
print-and-cut cards for clear sleeves, 9 per US Letter sheet at real card size (2.5 x 3.5 in).
Pages alternate front, back, front, back. Each back page is the front mirrored left to right, so
printing on both sides with "flip on long edge" puts each back behind its own front.
The PDF copy (xenagos-tokens.pdf) is printed from this page with Playwright, Letter size, no margins.
Print at 100% / Actual size, not Fit to page.

How many (the user's picks, Nov 2026; a die on one token stands in for big stacks):
Eldrazi Spawn 5, Plant 5, Copy 9, Elephant 3, Lightning Rager 2, Beast 1, Wurm with deathtouch 1,
Wurm with lifelink 1, Garruk emblem 1: 28 faces on 14 cards.
How they pair (each token comes from one card, so two faces only clash when both their cards are out):
- Spawn / Plant x5: Rapacious One and Avenger of Zendikar; when both are out, a die covers the overflow.
- Copy on the back of everything else: Copy comes from Dual Nature or Blade of Selves.
- The two Wurms (both from Wurmcoil Engine) and the three Elephants (Terastodon, possibly to three
  players) sit on separate cards, since they arrive together.
Run from the repo root:  python3 tools/carousel/xenagos_tokens.py
"""
import html, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
CDN = 'https://cards.scryfall.io/large/front/'
IMG = {
    'Plant': CDN + '3/d/3db07715-d315-4361-8af5-ce68d20e6c08.jpg',
    'Copy': CDN + '4/5/45364163-62b7-4641-b2c9-c2e46d61335c.jpg',
    'Elephant': CDN + '2/8/2853ba8b-650e-49e3-ab12-86b76e02743b.jpg',
    'Lightning Rager': CDN + '8/2/8292126c-a7b4-40d3-8a08-f15dd871207d.jpg',
    'Beast': CDN + 'c/a/ca8e8a9a-d673-4644-9eec-f4f549307d9b.jpg',
    'Wurm (deathtouch)': CDN + 'b/6/b68e816f-f9ac-435b-ad0b-ceedbe72447a.jpg',
    'Wurm (lifelink)': CDN + 'a/6/a6ee0db9-ac89-4ab6-ac2e-8a7527d9ecbd.jpg',
    'Garruk, Caller of Beasts emblem': CDN + 'd/1/d16429cb-9b00-4411-9ffc-252b38ad0b8c.jpg',
}
SPAWN = [CDN + 'e/0/e0e3826c-3c85-4910-bd6c-04894ea328d0.jpg', CDN + '3/5/35fb1a3d-3f1a-45ba-a643-1dca435c77de.jpg',
         CDN + 'd/0/d0da4f8d-cce9-4d08-8d11-792e0b2af7d0.jpg']  # Rise of the Eldrazi's three arts

CARDS = ([('Eldrazi Spawn', 'Plant')] * 5 + [('Elephant', 'Copy')] * 3 + [('Lightning Rager', 'Copy')] * 2 +
         [('Wurm (deathtouch)', 'Copy'), ('Wurm (lifelink)', 'Copy'), ('Beast', 'Copy'),
          ('Garruk, Caller of Beasts emblem', 'Copy')])

spawn = 0
def face(name):
    global spawn
    if name == 'Eldrazi Spawn':
        spawn += 1
        return name, SPAWN[(spawn - 1) % 3]
    return name, IMG[name]

def img(f):
    return f'<img src="{html.escape(f[1])}" alt="{html.escape(f[0])} token">' if f else '<i></i>'

sheets = [CARDS[i:i + 9] for i in range(0, len(CARDS), 9)]
body = ''
for n, sheet in enumerate(sheets, 1):
    fronts = [face(a) for a, b in sheet] + [None] * (9 - len(sheet))
    backs = [face(b) for a, b in sheet] + [None] * (9 - len(sheet))
    # Mirror each row of the back: the card in the left column sits behind the right column once flipped.
    backs = [backs[r * 3 + 2 - c] for r in range(3) for c in range(3)]
    body += f'<section class="pg"><b>Sheet {n} front</b>' + ''.join(map(img, fronts)) + '</section>'
    body += f'<section class="pg"><b>Sheet {n} back</b>' + ''.join(map(img, backs)) + '</section>'
board = re.search(r'<!-- app-board-link.*?</script>', open(os.path.join(ROOT, 'xenagos-proxies.html')).read(), re.S).group(0)

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Xenagos Tokens</title>
{board}
<style>
/* 3 x 3 cards of 2.5 x 3.5 in, centred on Letter (0.5 in sides, 0.25 in top and bottom), so the
   margins match on both sides of the sheet and a back lines up with its front. Cut along the grey lines. */
@page{{size:letter;margin:0}}
html{{background:#ccc}}body{{margin:0}}
.pg{{width:8.5in;height:11in;box-sizing:border-box;padding:.25in .5in;background:#fff;margin:16px auto;position:relative;
  display:grid;grid-template-columns:repeat(3,2.5in);grid-template-rows:repeat(3,3.5in);align-content:start;break-after:page}}
.pg img,.pg i{{width:2.5in;height:3.5in;display:block;outline:.5px solid #999;outline-offset:-.25px}}
.pg i{{outline:none}}
.pg b{{position:absolute;left:.5in;bottom:.06in;font:600 8pt system-ui,sans-serif;color:#999}}
@media print{{html{{background:#fff}}.pg{{margin:0}}.pg:last-child{{break-after:auto}}a[href="/commander-life/"]{{display:none!important}}}}
</style></head><body>{body}</body></html>
'''
open(os.path.join(ROOT, 'xenagos-tokens.html'), 'w').write(page)
print(len(CARDS), 'cards,', 2 * len(CARDS), 'faces,', 2 * len(sheets), 'pages')
