"""Build xenagos-to-buy-print.html: the Xenagos still-to-buy list as one US Letter (8.5 x 11 in) page
to print and tick off. Reads the cards from xenagos-to-buy.html, so run xenagos_buy.py first.
The PDF copy (xenagos-to-buy.pdf) is printed from this page with Playwright, Letter size.
Run from the repo root:  python3 tools/carousel/xenagos_print.py
"""
import html, json, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
src = open(os.path.join(ROOT, 'xenagos-to-buy.html')).read()
ALL, _ = json.JSONDecoder().raw_decode(src, re.search(r'const ALL=', src).end())
board = re.search(r'<!-- app-board-link.*?</script>', src, re.S).group(0)  # same Board button as every page

def kind(t):
    t = t.split(' — ')[0].replace('Legendary ', '')
    return t.replace('Enchantment Creature', 'Creature').replace('Artifact Creature', 'Creature')

def rows(cards, show_type=True):
    out = []
    for c in cards:
        q = f'{c["q"]}× ' if c['q'] > 1 else ''
        price = f'${c["p"] * c["q"]:.2f}' if c['p'] is not None else 'no price'
        note = f' <em>{html.escape(c["note"])}</em>' if c.get('note') else ''  # house rule: flag non-legal cards
        out.append(f'<tr><td class="bx"></td><td class="nm">{q}{html.escape(c["n"])}{note}</td>'
                   + (f'<td class="ty">{kind(c["t"])}</td><td class="mv">{c["m"]}</td>' if show_type else '')
                   + f'<td class="pr">{price}</td></tr>')
    return ''.join(out)

spells = sorted([c for c in ALL if 'Land' not in c['t']], key=lambda c: (c['m'], c['n']))
lands = sorted([c for c in ALL if 'Land' in c['t'] and 'Basic' not in c['t']], key=lambda c: c['n'])
basics = [c for c in ALL if 'Basic' in c['t']]
tot = lambda cs: sum((c['p'] or 0) * c['q'] for c in cs)

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Xenagos Buy List</title>
{board}
<style>
/* One US Letter page. Black on white so it prints cleanly; the screen view just shows the paper. */
@page{{size:letter;margin:0.5in}}
html{{background:#ddd}}
body{{margin:0;font:10.5pt/1.25 Georgia,'Times New Roman',serif;color:#000}}
.sheet{{background:#fff;width:7.5in;margin:16px auto;padding:0.5in;box-sizing:content-box;box-shadow:0 2px 12px rgba(0,0,0,.2)}}
@media screen and (max-width:9in){{.sheet{{width:auto;margin:0;padding:16px;box-shadow:none}}}}
@media print{{html{{background:#fff}}.sheet{{margin:0;padding:0;width:auto;box-shadow:none}}a[href="/commander-life/"]{{display:none!important}}}}
h1{{font-size:18pt;margin:0}}
.sub{{margin:2px 0 10px;font-size:9.5pt;color:#333}}
h2{{font-size:11.5pt;margin:12px 0 3px;border-bottom:1.5px solid #000;padding-bottom:2px;display:flex;justify-content:space-between}}
h2 span{{font-weight:normal;font-size:10pt}}
table{{width:100%;border-collapse:collapse}}
td{{padding:3px 4px;border-bottom:0.5px solid #bbb;vertical-align:middle}}
td.bx{{width:14px;padding-right:8px}}
td.bx::before{{content:'';display:block;width:11px;height:11px;border:1.2px solid #000}}
td.ty{{width:1.3in;color:#333;font-size:9.5pt}}
td.mv{{width:.35in;text-align:center;color:#333;font-size:9.5pt}}
td.pr{{width:.7in;text-align:right;font-variant-numeric:tabular-nums}}
th{{font:bold 8pt system-ui,sans-serif;text-transform:uppercase;letter-spacing:.04em;color:#555;text-align:left;padding:0 4px 2px}}
th.mv{{text-align:center}}th.pr{{text-align:right}}
em{{color:#b00;font-style:normal;font-size:8.5pt}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:0 .3in}}
.total{{margin-top:12px;border-top:1.5px solid #000;padding-top:5px;display:flex;justify-content:space-between;font-weight:bold}}
.foot{{margin-top:6px;font-size:8.5pt;color:#444}}
</style></head><body><div class="sheet">
<h1>Xenagos, God of Revels: still to buy</h1>
<p class="sub">{sum(c["q"] for c in ALL)} cards for the Party Hugger deck · cheapest paper printing on TCGplayer, via Scryfall, Nov 10, 2026 · all Commander-legal</p>
<h2>Spells <span>{len(spells)} cards · ${tot(spells):.2f}</span></h2>
<table><tr><th></th><th>Card</th><th>Type</th><th class="mv">MV</th><th class="pr">Price</th></tr>{rows(spells)}</table>
<div class="cols">
<div><h2>Nonbasic lands <span>{len(lands)} · ${tot(lands):.2f}</span></h2><table>{rows(lands[:len(lands)//2 + len(lands)%2], False)}</table></div>
<div><h2>&nbsp;<span></span></h2><table>{rows(lands[len(lands)//2 + len(lands)%2:], False)}</table></div>
</div>
<h2>Basic lands <span>{sum(c["q"] for c in basics)} · ${tot(basics):.2f}</span></h2>
<table>{rows(basics, False)}</table>
<div class="total"><span>Total</span><span>${tot(ALL):.2f}</span></div>
<p class="foot">Prices move; check before buying. Live list: biglob.github.io/commander-life/xenagos-to-buy.html</p>
</div></body></html>
'''
open(os.path.join(ROOT, 'xenagos-to-buy-print.html'), 'w').write(page)
print('spells', len(spells), 'lands', len(lands), 'basics', sum(c['q'] for c in basics), f'${tot(ALL):.2f}')
