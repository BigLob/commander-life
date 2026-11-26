"""Build sisko-proxies.html: cards picked for the Captain Benjamin Sisko deck as print-and-cut proxies, 9 per
US Letter page at real card size (2.5 x 3.5 in), blank backs.

Low-ink black-and-white format (the user's ask, Nov 26, 2026): no colored frame, nothing filled in; the art
only (outlined, no frame) under the name line.
Each card keeps all its information as text: name, mana cost, type line, rules text, flavor text, power and
toughness (or loyalty), and the set and collector number. Mana symbols are drawn as small outlined circles
with their letter or number ({T} as the tap arrow). The thin grey card outline is the cut line.
Rules text is shrunk card by card until it fits (fitAll() in the page), before the PDF is printed.

The user prints double-sided (flip on long edge), so every card page is followed by an empty page: card page
2 doesn't land on the back of card page 1.
The PDF copy (sisko-proxies.pdf) is printed from this page with Playwright, Letter size, no margins, with the
repo served over http so fonts/ loads (file:// blocks the fonts). Print at 100% / Actual size, not Fit to page.
Run from the repo root:  python3 tools/carousel/sisko_proxies.py
"""
import html, json, os, re, sys, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
# The card's art (Scryfall art_crop, no frame) sits under the name line: the user asked for the art back in,
# Nov 26, 2026, after seeing the text-only sheet. --no-art builds the text-only sheet (sisko-proxies-text.html).
ART = '--no-art' not in sys.argv
OUTNAME = 'sisko-proxies.html' if ART else 'sisko-proxies-text.html'
# Nov 25, 2026: the first 9 (Kirk, Picard, Academy Instructor, Gala Greeters, Felidar Retreat, Impossible
# Choice, Test of Priorities, Cryptic Command, Resistance Is Futile) were replaced by the second batch (first 4).
# Nov 26, 2026: the ramp picks added: 4 cheap creatures and 5 mana rocks.
CARDS = ["Ni'Var Science Academy", 'Q Continuum', 'Deanna Troi, Psychic Counsel', 'Captain Kathryn Janeway',
         'Birds of Paradise', 'Bloom Tender', 'Gala Greeters', 'Paradise Druid',
         'Sol Ring', 'Arcane Signet', 'Chromatic Lantern', 'Fellwar Stone', 'Timeless Lotus']

req = urllib.request.Request('https://api.scryfall.com/cards/collection',
                             json.dumps({'identifiers': [{'name': n} for n in CARDS]}).encode(),
                             {'Content-Type': 'application/json', 'Accept': 'application/json',
                              'User-Agent': 'commander-life/1.0'})
got = json.load(urllib.request.urlopen(req))
assert not got['not_found'], got['not_found']
by = {c['name']: c for c in got['data']}

def sym(s):
    """One {X} symbol as an outlined circle: no fill, so no ink beyond its line."""
    t = s[1:-1]
    if t == 'T': return '<span class="ms t">&#x21B7;</span>'
    if t == 'Q': return '<span class="ms t">&#x21B6;</span>'
    return f'<span class="ms{" w" if len(t) > 1 else ""}">{html.escape(t)}</span>'

def symtext(s):
    out, last = [], 0
    for m in re.finditer(r'\{[^}]+\}', s):
        out.append(html.escape(s[last:m.start()])); out.append(sym(m.group(0))); last = m.end()
    out.append(html.escape(s[last:]))
    return ''.join(out)

def rules(t):
    # reminder text in parentheses is italic, as printed
    paras = []
    for line in t.split('\n'):
        h = symtext(line)
        h = re.sub(r'\(([^()]*)\)', r'<i>(\1)</i>', h)
        paras.append(f'<p>{h}</p>')
    return ''.join(paras)

def face(f, c):
    """One face's card body (the whole card for single-faced cards)."""
    name, cost, typ = f['name'], f.get('mana_cost', ''), f['type_line']
    txt, flav = f.get('oracle_text', ''), f.get('flavor_text', '')
    pt = f"{f['power']}/{f['toughness']}" if 'power' in f else f.get('loyalty', '')
    body = rules(txt) + (f'<p class="fl">{html.escape(flav)}</p>' if flav else '')
    iu = f.get('image_uris') or c.get('image_uris') or {}
    art = f'<div class="art"><img src="{html.escape(iu["art_crop"])}" alt=""></div>' if ART and iu.get('art_crop') else ''
    return (f'<div class="card"><div class="hd"><span class="nm">{html.escape(name)}</span><span class="mc">{symtext(cost)}</span></div>{art}'
            f'<div class="ty">{html.escape(typ)}</div><div class="tx"><div class="in">{body}</div></div>'
            f'<div class="ft"><span class="set">{c["set"].upper()} {html.escape(c["collector_number"])}</span>'
            f'{f"<span class=pt>{html.escape(pt)}</span>" if pt else ""}</div></div>')

cards = []
for n in CARDS:
    c = by[n]
    if c['legalities']['commander'] != 'legal': print('NOT Commander-legal:', n)  # the user's rule
    faces = c.get('card_faces') if not c.get('oracle_text') else None
    if faces:  # double-faced: each face is its own proxy (none in the list today)
        cards += [face(f, c) for f in faces]
    else:
        cards.append(face(c, c))

src = open(os.path.join(ROOT, 'xenagos-proxies.html'), encoding='utf-8').read()
board = re.search(r'<!-- app-board-link.*?</script>', src, re.S).group(0)

pages = [cards[i:i + 9] for i in range(0, len(cards), 9)]
body = ''.join('<section class="pg">' + ''.join(p) + '</section><section class="pg back"></section>' for p in pages)

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sisko Proxies</title>
{board}
<style>
@font-face{{font-family:"Matrix";src:url(fonts/Matrix-Bold.woff) format("woff");font-weight:100 900;unicode-range:U+20-7E,U+2212}}
@font-face{{font-family:"MPlantin";src:url(fonts/Mplantin-text.woff) format("woff");font-weight:100 900;unicode-range:U+20-7E,U+A1-A3,U+A5,U+A7-AB,U+AE,U+B1,U+B4-B6,U+B8,U+BA-BB,U+BF-CF,U+D1,U+D3-D6,U+D8-DC,U+DF-EF,U+F1-F6,U+F8-FC,U+FF,U+131,U+152-153,U+178,U+192,U+2013-2014,U+2018-2019,U+201C-201E,U+2020-2022,U+2026,U+2030,U+2039-203A,U+2122}}
/* 3 x 3 cards of 2.5 x 3.5 in fill 7.5 x 10.5 in, centred on Letter: 0.5 in sides, 0.25 in top and bottom.
   Cards touch, so one straight cut along each grey line separates them. Back pages stay empty.
   Low ink: black text on white, hairlines only, no fills, no art. */
@page{{size:letter;margin:0}}
html{{background:#ccc}}body{{margin:0;color:#000}}
.pg{{width:8.5in;height:11in;box-sizing:border-box;padding:.25in .5in;background:#fff;margin:16px auto;
  display:grid;grid-template-columns:repeat(3,2.5in);grid-template-rows:repeat(3,3.5in);align-content:start;
  position:relative;break-after:page}}
.card{{width:2.5in;height:3.5in;box-sizing:border-box;outline:.5px solid #999;outline-offset:-.25px;
  padding:.14in .15in .1in;display:flex;flex-direction:column;font-family:MPlantin,Georgia,serif;overflow:hidden}}
.hd{{display:flex;justify-content:space-between;align-items:center;gap:4px;border-bottom:.6px solid #000;padding-bottom:3px}}
.nm{{font-family:Matrix,Georgia,serif;font-weight:700;font-size:10.5pt;line-height:1.1}}
.mc{{display:flex;gap:1px;flex:none}}
.art{{height:1.32in;margin-top:4px;flex:none;overflow:hidden;outline:.4px solid #000}}/* art in greyscale (the user: "black and white scale still") */
.art img{{width:100%;height:100%;object-fit:cover;display:block;filter:grayscale(1)}}
.ty{{font-family:Matrix,Georgia,serif;font-weight:700;font-size:8.5pt;padding:3px 0;border-bottom:.6px solid #000}}
.tx{{flex:1;min-height:0;padding-top:5px;display:flex;flex-direction:column;justify-content:center}}
.tx .in{{font-size:var(--fs,9pt);line-height:1.2}}
.tx p{{margin:0 0 .35em}}
.tx p.fl{{font-style:italic;border-top:.4px solid #888;padding-top:.3em;margin-top:.45em}}
.ft{{display:flex;justify-content:space-between;align-items:flex-end;font-size:6.5pt;color:#555;padding-top:3px}}
.pt{{font-family:Matrix,Georgia,serif;font-weight:700;font-size:10pt;color:#000;border:.6px solid #000;border-radius:3px;padding:0 5px}}
.ms{{display:inline-flex;align-items:center;justify-content:center;min-width:1.35em;height:1.35em;border:.7px solid #000;
  border-radius:50%;font-family:Arial,Helvetica,sans-serif;font-weight:700;font-size:.8em;line-height:1;vertical-align:.05em;box-sizing:border-box;padding:0 .12em;margin:0 .04em}}
.ms.w{{border-radius:.7em}}.ms.t{{font-size:.9em;font-weight:400}}
.hd .ms{{font-size:7.5pt}}
@media screen{{.pg.back{{display:none}}}}
@media print{{html{{background:#fff}}.pg{{margin:0}}.pg:last-child{{break-after:auto}}a[href="/commander-life/"]{{display:none!important}}}}
</style></head><body>{body}
<script>
/* shrink each card's rules text until it fits its box (10.5pt down to 5.5pt) */
function fitAll(){{document.querySelectorAll('.tx').forEach(b=>{{const i=b.firstElementChild;let s=10.5;
 i.style.setProperty('--fs',s+'pt');while(i.scrollHeight>b.clientHeight-5&&s>5.5){{s-=.25;i.style.setProperty('--fs',s+'pt')}}}});document.body.dataset.fit=1}}
(document.fonts?document.fonts.ready:Promise.resolve()).then(fitAll);
</script></body></html>
'''
with open(os.path.join(ROOT, OUTNAME), 'w', encoding='utf-8') as f:
    f.write(page)
print(len(cards), 'proxies on', len(pages), 'card pages,', 2 * len(pages), 'PDF pages')
