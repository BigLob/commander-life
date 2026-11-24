"""Build emrakul.html: every Magic card with Emrakul in its name, as a deck-style carousel (template.html).
Unlisted on purpose: the user asked for it to stay out of links.html.
Run from the repo root:  python3 tools/carousel/emrakul.py
"""
import html, json, os, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import get, record

def main():
    url = 'https://api.scryfall.com/cards/search?q=' + urllib.parse.quote('name:emrakul include:extras game:paper') + '&unique=cards&order=released'
    cards = []
    while url:
        d = json.loads(get(url)); cards += d['data']; url = d.get('next_page'); time.sleep(0.12)
    ALL = [record(1, c) for c in cards]
    ALL.sort(key=lambda r: (r['n'].startswith('Emrakul,') is False, r['n']))  # Emrakul herself first
    t = open(os.path.join(HERE, 'template.html')).read()
    cfg = {'slug': 'emrakul', 'deck': 'Emrakul', 'set': 'Every card with Emrakul in its name', 'cmd': f'{len(ALL)} cards', 'alt': None}
    t = (t.replace('__TITLE__', 'Emrakul').replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
    t = t.replace('‹ All decks', '‹ Board')
    open(os.path.join(ROOT, 'emrakul.html'), 'w').write(t)
    for r in ALL: print(r['n'], r['p'], r.get('note', ''))

main()
