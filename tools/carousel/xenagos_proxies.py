"""Build xenagos-proxies.html: the Xenagos still-to-buy cards as print-and-cut proxies, 9 per US
Letter page at real card size (2.5 x 3.5 in), with cut marks. Basics are left out (we have plenty).
Reads the cards from xenagos-to-buy.html, so run xenagos_buy.py first. Images are Scryfall's
'large' scans (672 x 936, about 270 dpi at card size), loaded from Scryfall's CDN.
The PDF copy (xenagos-proxies.pdf) is printed from this page with Playwright, Letter size, no margins.
Print at 100% / Actual size, not Fit to page, or the cards come out small.
Run from the repo root:  python3 tools/carousel/xenagos_proxies.py
"""
import html, json, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
src = open(os.path.join(ROOT, 'xenagos-to-buy.html')).read()
ALL, _ = json.JSONDecoder().raw_decode(src, re.search(r'const ALL=', src).end())
board = re.search(r'<!-- app-board-link.*?</script>', src, re.S).group(0)

cards = []
for c in ALL:
    if 'Basic' in c['t']: continue
    cards += [c['i'].replace('/normal/', '/large/')] * c['q']
    if c.get('b'): cards.append(c['b'].replace('/normal/', '/large/'))  # a double-faced card's back as its own proxy
pages = [cards[i:i + 9] for i in range(0, len(cards), 9)]
body = ''.join('<section class="pg">' + ''.join(f'<img src="{html.escape(u)}" alt="">' for u in p) + '</section>' for p in pages)

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Xenagos Proxies</title>
{board}
<style>
/* 3 x 3 cards of 2.5 x 3.5 in fill 7.5 x 10.5 in, centred on Letter: 0.5 in sides, 0.25 in top and bottom.
   Cards touch, so one straight cut along each grey line separates them. */
@page{{size:letter;margin:0}}
html{{background:#ccc}}body{{margin:0}}
.pg{{width:8.5in;height:11in;box-sizing:border-box;padding:.25in .5in;background:#fff;margin:16px auto;
  display:grid;grid-template-columns:repeat(3,2.5in);grid-template-rows:repeat(3,3.5in);align-content:start;
  outline:0 solid;position:relative;break-after:page}}
.pg img{{width:2.5in;height:3.5in;display:block;outline:.5px solid #999;outline-offset:-.25px}}
@media print{{html{{background:#fff}}.pg{{margin:0}}.pg:last-child{{break-after:auto}}a[href="/commander-life/"]{{display:none!important}}}}
</style></head><body>{body}</body></html>
'''
open(os.path.join(ROOT, 'xenagos-proxies.html'), 'w').write(page)
print(len(cards), 'proxies on', len(pages), 'pages')
