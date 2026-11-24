"""Build squirrels/index.html: every Commander-legal legendary Squirrel whose color identity is black, green or both
(Scryfall: t:legendary t:squirrel id<=bg legal:commander), most-played (EDHREC rank) first, for picking a squirrel commander.
Not-legal ones (Un/Alchemy) are left out, and so is anything in the Squirreled Away box or picked to add to it (exclude.py); the page names them. Same carousel as cuts/ (cuts-template.html, caption swapped).
Run from the repo root:  python3 tools/carousel/squirrels.py
"""
import datetime, html, json, os, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import get, record
from exclude import sa_names
OUT = os.path.join(ROOT, 'squirrels')

def search(q):
    out, url = [], 'https://api.scryfall.com/cards/search?' + urllib.parse.urlencode({'q': q, 'order': 'edhrec', 'unique': 'cards'})
    while url:
        d = json.loads(get(url)); out += d['data']; url = d.get('next_page')
    return out

def main():
    today = datetime.date.today()
    cards = search('t:legendary t:squirrel id<=bg legal:commander')
    skipped = [c['name'] for c in search('t:legendary t:squirrel id<=bg -legal:commander')]
    box, picked = sa_names()
    out = [c['name'] for c in cards if c['name'].split(' // ')[0] in box | picked]
    cards = [c for c in cards if c['name'].split(' // ')[0] not in box | picked]
    ALL = []
    for c in cards:
        r = record(1, c)
        r.update(k=['Squirrel'] + c.get('keywords', []), r=len(ALL) + 1, x=0,
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
        ALL.append(r)
    n = len(ALL)
    srcs = (f'<p><b>Source:</b> Scryfall, read {today:%b} {today.day}, {today.year}: legendary creatures with the Squirrel type, color identity black, green or both, '
            f'Commander-legal, in EDHREC\'s popularity order. Left out because they are not Commander-legal: {html.escape(", ".join(skipped)) or "none"}. Left out because they are already in the Squirreled Away box or picked to add to it: {html.escape(", ".join(out)) or "none"}.</p>')
    cfg = {'slug': 'squirrels', 'deck': 'Legendary Squirrels (B/G)', 'set': 'Commander-legal', 'cmd': 'Any', 'alt': '', 'decks': n,
           'edh': 'https://scryfall.com/search?q=' + urllib.parse.quote('t:legendary t:squirrel id<=bg legal:commander'), 'srcs': srcs,
           'sub': f'{n} legendary Squirrels in black, green or both · most played first'}
    t = open(os.path.join(HERE, 'cuts-template.html'), encoding='utf-8').read()
    old = "<b>#${c.r} most cut</b> · cut from ${pct(c.x)} of ${CFG.decks.toLocaleString('en-US')} decks"
    assert old in t
    t = t.replace(old, "<b>#${c.r} of " + str(n) + "</b> · ${c.t}")
    t = (t.replace('__TITLE__', 'Legendary Squirrels').replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(t)
    print(n, [c['n'] for c in ALL], 'skipped', skipped, 'excluded', out)

main()
