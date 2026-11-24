"""Build staples/index.html: colorless cards that players add to MANY different precons (Sol Ring, Arcane Signet, Command Tower...),
so they fit any deck we own. Source: EDHREC's precon pages ("Cards to Add" + "Lands to Add", the share of decks from each box that add
the card, which already leaves out cards in that box), for every deck in make.py's DECKS. A card ranks by how many of those precons
list it, then by its average share. Only colorless identity (works in any deck) and Commander-legal cards. Card data from Scryfall.
Same carousel as adds/ (cuts-template.html with the caption line swapped).
Run from the repo root:  python3 tools/carousel/staples.py
"""
import manacost
import datetime, html, json, os, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import DECKS, get, scryfall, record
from exclude import sa_names
EDH_SLUG = {'borg': 'we-are-the-borg'}
TOP = 40
OUT = os.path.join(ROOT, 'staples')

def main():
    today = datetime.date.today()
    seen = {}   # name -> [(precon, share)]
    n_decks = 0
    import re
    slugs = sorted(set(re.findall(r'/precons/([a-z0-9-]+)', get('https://edhrec.com/precons').decode('utf-8', 'ignore') if isinstance(get('https://edhrec.com/precons'), bytes) else get('https://edhrec.com/precons'))))
    for es in slugs:
        try: j = json.loads(get(f'https://json.edhrec.com/pages/precon/{es}.json'))
        except Exception as e: print('skip', es, str(e)[:40]); continue
        L = {l['tag']: l['cardviews'] for l in j['container']['json_dict'].get('cardlists', [])}
        if not L.get('cardstoadd'): continue
        n_decks += 1
        for t in ('cardstoadd', 'landstoadd'):
            for c in L.get(t, []):
                if c.get('potential_decks'):
                    seen.setdefault(c['name'], []).append((es, c['num_decks'] / c['potential_decks']))
        time.sleep(0.3)
    # Keep candidates in 3+ precons, then check Scryfall for colorless identity and legality.
    cand = sorted((n for n, v in seen.items() if len(v) >= 5), key=lambda n: (-len(seen[n]), -sum(s for _, s in seen[n]) / len(seen[n])))
    cards = scryfall([(1, {'name': n}, n) for n in cand])
    box, picked = sa_names()
    ALL = []; dropped = []
    for nm, (_, c) in zip(cand, cards):
        if c.get('color_identity') or c['legalities'].get('commander') != 'legal': continue
        # the user's rules: nothing already in the Squirreled Away box or already picked to add to it, and no land that only
        # makes colorless mana (a land that fetches other lands or can make colored mana stays)
        front = c['name'].split(' // ')[0]
        only_c = 'Land' in c['type_line'] and set(c.get('produced_mana', [])) <= {'C'} and 'search your library' not in (c.get('oracle_text') or '').lower()
        if front in box or front in picked or only_c:
            dropped.append(front + (' (in the box)' if front in box else ' (picked for Squirreled Away)' if front in picked else ' (colorless land)')); continue
        v = seen[nm]
        r = record(1, c)
        r.update(k=['Land' if 'Land' in c['type_line'] else 'Spell'] + c.get('keywords', []), r=len(ALL) + 1,
                 x=round(sum(s for _, s in v) / len(v), 3), pc=len(v),
                 u='https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
        ALL.append(r)
        if len(ALL) == TOP: break
    srcs = (f'<p><b>Source:</b> EDHREC\'s pages for {n_decks} precons (every one on its precons list), read {today:%b} {today.day}, {today.year}. Each lists the cards players most often '
            f'<i>add</i> that are not already in that box, with the share of decks that add them. A card ranks by how many of those precons list it, then by its average share. '
            f'Only cards with no color identity (so they go in any deck) and that are Commander-legal. A card already in a box can\'t show up for that box, so a card that most boxes already include ranks lower than it otherwise would. '
            f'Left out on purpose: lands that only make colorless mana, and anything already in the Squirreled Away box or already picked to add to it. Card data and prices from Scryfall.</p>')
    cfg = {'slug': 'staples', 'deck': 'Colorless staples', 'set': 'Added to many precons', 'cmd': 'Any precon', 'alt': '', 'decks': n_decks,
           'edh': 'https://edhrec.com/precons', 'srcs': srcs,
           'sub': f'Colorless and Commander-legal · {len(ALL)} cards added to the most of {n_decks} precons'}
    t = open(os.path.join(HERE, 'cuts-template.html'), encoding='utf-8').read()
    old = "<b>#${c.r} most cut</b> · cut from ${pct(c.x)} of ${CFG.decks.toLocaleString('en-US')} decks"
    assert old in t
    t = t.replace(old, "<b>#${c.r}</b> · added to ${c.pc} of ${CFG.decks} precons · ${pct(c.x)} of decks on average")
    t = (t.replace('__TITLE__', 'Colorless staples').replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(manacost.fill(ALL), ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(t)
    print('dropped:', dropped); print(len(ALL), 'cards:', ', '.join(f'{c["n"]} ({c["pc"]})' for c in ALL[:12]))

main()
