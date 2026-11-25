"""Build sisko-proxies.html: cards picked for the Captain Benjamin Sisko deck as print-and-cut
proxies, 9 per US Letter page at real card size (2.5 x 3.5 in), grey cut lines, blank backs.
The user prints double-sided (flip on long edge), so every card page is followed by an empty page:
that way card page 2 doesn't land on the back of card page 1.
Images are Scryfall's 'large' scans (672 x 936, about 270 dpi at card size), loaded from Scryfall's CDN.
The PDF copy (sisko-proxies.pdf) is printed from this page with Playwright, Letter size, no margins.
Print at 100% / Actual size, not Fit to page.
Run from the repo root:  python3 tools/carousel/sisko_proxies.py
"""
import html, json, os, re, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
# Nov 25, 2026: the first 9 (Kirk, Picard, Academy Instructor, Gala Greeters, Felidar Retreat, Impossible
# Choice, Test of Priorities, Cryptic Command, Resistance Is Futile) were replaced by this second batch.
CARDS = ["Ni'Var Science Academy", 'Q Continuum', 'Deanna Troi, Psychic Counsel', 'Captain Kathryn Janeway']

req = urllib.request.Request('https://api.scryfall.com/cards/collection',
                             json.dumps({'identifiers': [{'name': n} for n in CARDS]}).encode(),
                             {'Content-Type': 'application/json', 'Accept': 'application/json',
                              'User-Agent': 'commander-life/1.0'})
got = json.load(urllib.request.urlopen(req))
assert not got['not_found'], got['not_found']
by = {c['name']: c for c in got['data']}
for n in CARDS:  # the user's rule: mark anything not Commander-legal
    if by[n]['legalities']['commander'] != 'legal': print('NOT Commander-legal:', n)
urls = [by[n]['image_uris']['large'] for n in CARDS]

src = open(os.path.join(ROOT, 'xenagos-proxies.html')).read()
board = re.search(r'<!-- app-board-link.*?</script>', src, re.S).group(0)

pages = [urls[i:i + 9] for i in range(0, len(urls), 9)]
body = ''.join('<section class="pg">' + ''.join(f'<img src="{html.escape(u)}" alt="">' for u in p) +
               '</section><section class="pg back"></section>' for p in pages)

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sisko Proxies</title>
{board}
<style>
/* 3 x 3 cards of 2.5 x 3.5 in fill 7.5 x 10.5 in, centred on Letter: 0.5 in sides, 0.25 in top and bottom.
   Cards touch, so one straight cut along each grey line separates them. Back pages stay empty. */
@page{{size:letter;margin:0}}
html{{background:#ccc}}body{{margin:0}}
.pg{{width:8.5in;height:11in;box-sizing:border-box;padding:.25in .5in;background:#fff;margin:16px auto;
  display:grid;grid-template-columns:repeat(3,2.5in);grid-template-rows:repeat(3,3.5in);align-content:start;
  position:relative;break-after:page}}
.pg img{{width:2.5in;height:3.5in;display:block;outline:.5px solid #999;outline-offset:-.25px}}
@media screen{{.pg.back{{display:none}}}}
@media print{{html{{background:#fff}}.pg{{margin:0}}.pg:last-child{{break-after:auto}}a[href="/commander-life/"]{{display:none!important}}}}
</style></head><body>{body}</body></html>
'''
with open(os.path.join(ROOT, 'sisko-proxies.html'), 'w', encoding='utf-8') as f:
    f.write(page)
print(len(urls), 'proxies on', len(pages), 'card pages,', 2 * len(pages), 'PDF pages')
