#!/usr/bin/env python3
"""Downloads every public Archidekt Commander deck for one commander, for theme_picks.py.

    python3 tools/carousel/archidekt.py "Killian, Decisive Mentor" <out.json>

Archidekt's search (/api/decks/v3/?commanderName=...) stops at 1,000 results per ordering, so it is walked
four ways (by update and creation date, each both ways) and the ids merged; decks without the commander are dropped later. Each deck is then read from /api/decks/<id>/. Only cards in
categories that count toward the deck are kept (not Maybeboard, Sideboard or a "Cuts" pile). Output: a list of
{id, name, bracket, updated, cards: [names]}. Re-running resumes: decks already in <out.json> are not fetched again.
Theorycrafted decks are kept (most upgrade lists are); a deck must have 90 to 110 cards to be used later."""
import json, os, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

CMD, OUT = sys.argv[1], sys.argv[2]
UA = {'User-Agent': 'Mozilla/5.0 (commander-life deck research)'}

def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1: raise
            # Archidekt answers 429 when the search is paged too fast (Terra, Nov 23, 2026): wait it out.
            time.sleep(30 * (i + 1) if getattr(e, 'code', None) == 429 else 2 * (i + 1))

def ids():
    found = {}
    for order in ('-updatedAt', 'updatedAt', '-createdAt', 'createdAt'):
        page = 1
        while True:
            q = urllib.parse.urlencode({'commanderName': CMD, 'page': page, 'orderBy': order, 'deckFormat': 3})
            d = get('https://archidekt.com/api/decks/v3/?' + q)
            for r in d['results']: found[r['id']] = r
            if not d.get('next') or not d['results']: break
            page += 1; time.sleep(1)
        print(order, len(found), file=sys.stderr)
    return found

def main():
    have = {d['id']: d for d in json.load(open(OUT))} if os.path.exists(OUT) else {}
    meta = ids()
    todo = [i for i in meta if i not in have]
    print(len(meta), 'decks found,', len(todo), 'to fetch', file=sys.stderr)
    def one(i):
        try: d = get(f'https://archidekt.com/api/decks/{i}/')
        except Exception as e:
            print('skip', i, e, file=sys.stderr); return None
        live = {c['name'] for c in d.get('categories', []) if c.get('includedInDeck')}
        cards = []
        for c in d.get('cards', []):
            cats = c.get('categories') or []
            if cats and not any(x in live for x in cats): continue   # maybeboard, cuts, sideboard
            cards += [c['card']['oracleCard']['name']] * int(c.get('quantity') or 1)
        return {'id': i, 'name': d.get('name'), 'bracket': d.get('edhBracket'), 'updated': d.get('updatedAt'), 'cards': cards}
    # Four at a time: about 7,500 decks for Killian take ~15 minutes this way instead of an hour.
    with ThreadPoolExecutor(4) as ex:
        for n, r in enumerate(ex.map(one, todo)):
            if r: have[r['id']] = r
            if n % 250 == 0:
                json.dump(list(have.values()), open(OUT, 'w')); print(n, '/', len(todo), file=sys.stderr)
    json.dump(list(have.values()), open(OUT, 'w'))
    print(len(have), 'decks saved to', OUT, file=sys.stderr)

main()
