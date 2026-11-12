"""Build xenagos-tokens-bw.html: the Xenagos tokens as black-and-white, ink-light fold-over cards (no art, one
simple line icon each) for a b/w printer. Each token is one 3.5 x 5 in strip: the back panel on top (turned
upside down), a dashed fold line, the front panel below. Cut round the grey outline, fold on the dashes, put
in a sleeve. 4 per US Letter page, printed single-sided, so no duplex alignment. Print at 100%.
Counts (the user's, Nov 2026): Eldrazi Spawn 5 (backed by Plant), Elephant 3, Lightning Rager 2, Wurm (deathtouch),
Wurm (lifelink), Beast and Garruk emblem 1 each, all backed by Copy: 14 cards, 4 pages.
Colour is a corner letter (G, R, C) and the icon, never ink. The PDF is printed with Playwright, Letter, no margins.
Run from the repo root:  python3 tools/carousel/tokens_bw.py
"""
import html, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
S = 'fill="none" stroke="#000" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    'spawn': f'<path {S} d="M50 50 m0 0 a5 5 0 0 1 10 0 a12 12 0 0 1 -24 0 a20 20 0 0 1 40 0 a28 28 0 0 1 -56 0 a36 36 0 0 1 72 0"/>',
    'plant': f'<g {S}><path d="M50 90 V45"/><path d="M50 60 C20 60 14 36 18 24 C40 24 50 40 50 60Z"/><path d="M50 48 C80 48 86 24 82 12 C60 12 50 28 50 48Z"/><path d="M30 90 H70"/></g>',
    'elephant': f'<g {S}><path d="M26 40 C26 24 42 18 58 18 C78 18 92 30 92 50 V82 H79 V66 H62 V82 H49 V64 C36 64 28 56 26 46"/><path d="M26 40 C14 42 12 62 16 76 C18 84 28 84 28 76"/><path d="M52 36 C64 36 66 56 54 58 C46 58 42 44 52 36Z"/><path d="M30 56 C24 62 26 68 32 66"/></g><circle cx="38" cy="34" r="2.5" fill="#000"/>',
    'rager': f'<path {S} d="M58 8 L24 56 H46 L38 92 L76 40 H54 Z"/>',
    'beast': f'<g {S}><path d="M50 52 C34 52 26 70 32 78 C38 86 46 80 50 80 C54 80 62 86 68 78 C74 70 66 52 50 52Z"/><ellipse cx="22" cy="46" rx="7" ry="10"/><ellipse cx="38" cy="28" rx="7" ry="10"/><ellipse cx="62" cy="28" rx="7" ry="10"/><ellipse cx="78" cy="46" rx="7" ry="10"/></g>',
    'wurm': f'<g {S}><path d="M16 74 C16 46 44 66 50 46 C56 26 84 40 84 24"/><circle cx="84" cy="22" r="7"/><path d="M30 64 l-4 -8 M46 56 l-2 -8 M62 38 l4 -6"/></g>',
    'skull': f'<g {S}><path d="M20 50 C20 20 80 20 80 50 C80 62 72 66 70 70 V82 H30 V70 C28 66 20 62 20 50Z"/><circle cx="38" cy="52" r="6"/><circle cx="62" cy="52" r="6"/><path d="M44 82 V72 M56 82 V72"/></g>',
    'heart': f'<path {S} d="M50 86 C10 58 16 22 36 22 C44 22 48 28 50 32 C52 28 56 22 64 22 C84 22 90 58 50 86Z"/>',
    'emblem': f'<g {S}><path d="M50 8 L86 28 V72 L50 92 L14 72 V28 Z"/><path d="M50 30 V70 M30 50 H70"/></g>',
    'copy': f'<g {S}><rect x="12" y="12" width="52" height="52" rx="4"/><rect x="36" y="36" width="52" height="52" rx="4" fill="#fff"/></g>',
}
def icon(*names, rot=0):
    if len(names) == 2:  # wurm + keyword badge
        return (f'<svg viewBox="0 0 100 100"><g transform="translate(2 -4) scale(.96)">{ICONS[names[0]]}</g>'
                f'<g transform="translate(54 50) scale(.46)">{ICONS[names[1]]}</g></svg>')
    return f'<svg viewBox="0 0 100 100"><g transform="rotate({rot} 50 50)">{ICONS[names[0]]}</g></svg>'

#        key               name                 colour type                      rules                                         p/t    icons
T = {
 'spawn':   ('Eldrazi Spawn',  'C', 'Creature — Eldrazi Spawn', 'Sacrifice this creature: Add {C}.', '0/1', ('spawn',)),
 'elephant':('Elephant',       'G', 'Creature — Elephant', '', '3/3', ('elephant',)),
 'rager':   ('Lightning Rager','R', 'Creature — Elemental', 'Haste. Sacrifice this creature at the beginning of the next end step.', '3/1', ('rager',)),
 'wurmd':   ('Wurm',           'C', 'Artifact Creature — Phyrexian Wurm', 'Deathtouch', '3/3', ('wurm', 'skull')),
 'wurml':   ('Wurm',           'C', 'Artifact Creature — Phyrexian Wurm', 'Lifelink', '3/3', ('wurm', 'heart')),
 'beast':   ('Beast',          'G', 'Creature — Beast', '', '3/3', ('beast',)),
 'emblem':  ('Garruk Emblem',  '—', 'Emblem', 'Creatures you control get +3/+3 and have trample.', '', ('emblem',)),
 'plant':   ('Plant',          'G', 'Creature — Plant', '', '0/1', ('plant',)),
 'copy':    ('Copy',           '—', 'Token', '', '', ('copy',)),
}
def panel(key, rot=0, back=False):
    n, c, ty, rules, pt, ic = T[key]
    extra = ''
    return (f'<div class="pn{" bk" if back else ""}"><span class="cl">{c}</span>'
            f'<div class="ic">{icon(*ic, rot=rot)}</div><h2>{html.escape(n)}</h2><p class="ty">{html.escape(ty)}</p>'
            f'<p class="ru">{html.escape(rules)}</p>{extra}'
            + (f'<span class="pt">{pt}</span>' if pt else '') + '</div>')

CARDS = [('spawn', 'plant', i * 120) for i in range(5)] + [('elephant', 'copy', 0)] * 3 + [('rager', 'copy', 0)] * 2 + \
        [(k, 'copy', 0) for k in ('wurmd', 'wurml', 'beast', 'emblem')]
body = ''
for n, i in enumerate(range(0, len(CARDS), 4), 1):
    body += f'<section class="pg"><b>Page {n}: cut on the grey outline, fold on the dashes</b>'
    for j, (f, b, rot) in enumerate(CARDS[i:i + 4]):
        front = panel(f).replace('rotate(0 ', f'rotate({rot} ') if f == 'spawn' else panel(f)
        # Three flat strips (back left, front right: folds with no turning) and one tall strip (back on top, turned
        # 180 degrees so it reads upright once folded) fill a page.
        if j < 3:
            body += f'<div class="cd h" style="grid-row:{j+1}"><div>{panel(b, back=True)}</div><div>{front}</div></div>'
        else:
            body += f'<div class="cd v"><div class="turn">{panel(b, back=True)}</div><div>{front}</div></div>'
    body += '</section>'
board = re.search(r'<!-- app-board-link.*?</script>', open(os.path.join(ROOT, 'xenagos-proxies.html')).read(), re.S).group(0)
page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Xenagos Tokens (black and white)</title>
{board}
<style>
@page{{size:letter;margin:0}}
html{{background:#ccc}}body{{margin:0;font-family:Georgia,serif;color:#000}}
.pg{{width:8.5in;height:11in;box-sizing:border-box;padding:.25in;background:#fff;margin:16px auto;position:relative;
  display:grid;grid-template-columns:5in 2.5in;grid-template-rows:repeat(3,3.5in);column-gap:.5in;align-content:start;break-after:page}}
.pg>b{{position:absolute;left:.25in;bottom:.06in;font:600 8pt system-ui,sans-serif;color:#999}}
.cd{{outline:.5px solid #999;position:relative}}
.cd.h{{grid-column:1;display:grid;grid-template-columns:2.5in 2.5in;width:5in;height:3.5in}}
.cd.v{{grid-column:2;grid-row:1/3;width:2.5in;height:7in;display:grid;grid-template-rows:3.5in 3.5in}}
.cd.h::after{{content:"";position:absolute;top:0;bottom:0;left:2.5in;border-left:1px dashed #999}}
.cd.v::after{{content:"";position:absolute;left:0;right:0;top:3.5in;border-top:1px dashed #999}}
.turn{{transform:rotate(180deg)}}
.pn{{box-sizing:border-box;width:2.5in;height:3.5in;border:3px solid #000;border-radius:12px;padding:.14in;position:relative;
  display:flex;flex-direction:column;background:#fff}}
.pn.bk{{border-style:double;border-width:7px}}
.cl{{position:absolute;top:.12in;right:.12in;width:.34in;height:.34in;border:2px solid #000;border-radius:50%;font:700 12pt/.34in system-ui,sans-serif;text-align:center}}
.ic{{display:flex;justify-content:center;margin-top:.05in}}.ic svg{{width:1.45in;height:1.45in;display:block}}
h2{{margin:.08in 0 0;font:700 19pt/1 Georgia,serif;text-align:center}}
.ty{{margin:.05in 0;font:italic 8.5pt/1.2 Georgia,serif;text-align:center;border-bottom:1.5px solid #000;border-top:1.5px solid #000;padding:.03in 0}}
.ru{{margin:.03in 0 0;font:10pt/1.3 Georgia,serif;text-align:center}}
.pt{{position:absolute;right:.12in;bottom:.12in;border:2.5px solid #000;border-radius:7px;padding:0 .1in;font:700 20pt/1.2 Georgia,serif;background:#fff}}
.lines{{margin-top:.05in}}.lines i{{display:block;border-bottom:1px solid #000;height:.24in}}
@media print{{html{{background:#fff}}.pg{{margin:0}}.pg:last-child{{break-after:auto}}a[href="/commander-life/"]{{display:none!important}}}}
</style></head><body>{body}</body></html>
'''
open(os.path.join(ROOT, 'xenagos-tokens-bw.html'), 'w').write(page)
print(len(CARDS), 'cards,', (len(CARDS) + 3) // 4, 'pages')
