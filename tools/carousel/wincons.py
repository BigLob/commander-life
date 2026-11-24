"""Build wincons/index.html: every Commander-legal card Scryfall tags as an alternate win condition (otag:alternate-win-condition:
"you win the game", "target player loses the game", and the odd ones like Hidetsugu's Second Rite), most-played (EDHREC rank) first,
with color buttons (All, W, U, B, R, G, Multicolor, Colorless). Same carousel as cuts/ (cuts-template.html), caption swapped.
Not-legal cards are left out (house rule: legal only on pages of cards to play); the page names them.
Run from the repo root:  python3 tools/carousel/wincons.py
"""
import manacost
import datetime, html, json, os, re, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import get, record
OUT = os.path.join(ROOT, 'wincons')
Q = 'otag:alternate-win-condition'

def search(q):
    out, url = [], 'https://api.scryfall.com/cards/search?' + urllib.parse.urlencode({'q': q, 'order': 'edhrec', 'unique': 'cards'})
    while url:
        d = json.loads(get(url)); out += d['data']; url = d.get('next_page')
    return out

def oracle(c):
    return ' // '.join(f.get('oracle_text', '') for f in c.get('card_faces', [])) if c.get('card_faces') and not c.get('oracle_text') else c.get('oracle_text', '')

def gist(c):
    """The sentence(s) that win or lose the game, so each card says why it is here."""
    t = oracle(c).replace('\n', ' ')
    s = [x.strip() for x in re.split(r'(?<=[.)])\s+', t) if re.search(r'win the game|wins the game|loses the game|lose the game', x)]
    return ' '.join(s)[:260]

def main():
    today = datetime.date.today()
    cards = search(Q + ' legal:commander')
    skipped = [c['name'] for c in search(Q + ' -legal:commander')]
    ALL = []
    for c in cards:
        r = record(1, c)
        r.update(k=c.get('keywords', []), r=len(ALL) + 1, x=0, o=gist(c),
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
        ALL.append(r)
    n = len(ALL)
    srcs = (f'<p><b>Source:</b> Scryfall, read {today:%b} {today.day}, {today.year}: every Commander-legal card carrying its Oracle tag <i>alternate-win-condition</i> '
            f'(cards that win the game or make a player lose it outright), in EDHREC\'s popularity order. Damage, poison and commander damage are the normal ways to win and are not listed. '
            f'Left out because they are not Commander-legal: {html.escape(", ".join(skipped)) or "none"}.</p>')
    cfg = {'slug': 'wincons', 'deck': 'Win conditions', 'set': 'Commander-legal', 'cmd': '', 'alt': '', 'decks': n,
           'edh': 'https://scryfall.com/search?q=' + urllib.parse.quote(Q + ' legal:commander'), 'srcs': srcs,
           'sub': f'{n} Commander-legal win-the-game cards · most played first'}
    t = open(os.path.join(HERE, 'cuts-template.html'), encoding='utf-8').read()
    t, k = re.subn(r"function why\(c\)\{return `.*?`\}",
        lambda m: "function why(c){return `<p class=\"cite\"><b>#${c.r} of " + str(n) + "</b> · ${c.o}<br><a href=\"${c.u}\" target=\"_blank\" rel=\"noopener\">card text</a></p>`}", t, count=1, flags=re.S)
    assert k == 1
    # color buttons: a row of toggles that drives the same filter as the Color select
    row = ('<div class="seg" id="colseg">' + ''.join(f'<button data-c="{v}" data-l="{l}" aria-pressed="{str(v == "").lower()}">{l}</button>' for v, l in
           [('', 'All'), ('W', 'White'), ('U', 'Blue'), ('B', 'Black'), ('R', 'Red'), ('G', 'Green'), ('M', 'Multicolor'), ('C', 'Colorless')]) + '</div>\n')
    anchor = '<div class="bar">'
    assert anchor in t
    t = t.replace(anchor, row + anchor, 1)
    # the buttons set the same filter as the Color select; each shows how many cards it would leave in the open tab
    paint = ("function paintCol(){document.querySelectorAll('#colseg button').forEach(b=>{const v=b.dataset.c,m=c=>!v||(v=='M'?c.c.length>1:v=='C'?!c.c.length:c.c.includes(v));"
             "b.setAttribute('aria-pressed',v==F.col);b.innerHTML=b.dataset.l+'<span class=\"ct\">'+view(tab).filter(m).length+'</span>'})}\n"
             "document.getElementById('colseg').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;F.col=b.dataset.c;$('f-col').value=F.col;render()});\n")
    old = "function render(keep){D=sortFilter(view(tab));fit();"
    assert old in t
    t = t.replace(old, paint + old + "paintCol();", 1)
    t = (t.replace('__TITLE__', 'Win conditions').replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(manacost.fill(ALL), ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(t)
    print(n, 'skipped', skipped)

main()
