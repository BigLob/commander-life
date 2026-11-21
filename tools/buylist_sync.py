#!/usr/bin/env python3
"""Copies every deck finalized in theme/review.html into buylist.txt, so the hand-kept log matches the live buy list.

    python3 tools/buylist_sync.py

Reads tables/t7q2xm4k-theme/<slug>/fin from the shared table for each deck in theme/index.json and appends a line per
card not already logged for that deck: date | card (Commander-legal) | any printing, about $X | proxy or real |
deck | to get (<kinds>, yes|maybe). Every card in the theme lists is Commander-legal (theme_picks.py and
theme_extras.py search legal:commander). A reopened deck has no fin; lines already in the log stay (edit by hand).
"""
import datetime, json, os, re, urllib.request
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DB = 'https://commander-life-39708-default-rtdb.firebaseio.com/tables/t7q2xm4k-theme'
LOG = os.path.join(ROOT, 'buylist.txt')

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as r:
        return json.load(r)

def main():
    log = open(LOG, encoding='utf-8').read()
    have = set()
    for line in log.splitlines():
        p = [x.strip() for x in line.split('|')]
        if len(p) >= 6: have.add((re.sub(r'\s*\(.*$', '', p[1]), p[4]))
    add = []
    for d in json.load(open(os.path.join(ROOT, 'theme', 'index.json'))):
        F = get(f'{DB}/{d["slug"]}/fin.json')
        if not F: continue
        day = datetime.datetime.fromtimestamp(F['at'] / 1000).strftime('%Y-%m-%d')
        rows = [x for x in F['cards'].values() if (x['n'], d['name']) not in have]
        if not rows: continue
        rows.sort(key=lambda x: (x['a'] != 'y', x['n']))
        add.append(f'\n# {d["name"]}: finalized in theme/review.html on {day} (yes first, then maybe)')
        for x in rows:
            price = f', about ${x["usd"]:.2f}' if x.get('usd') else ''
            add.append(f'{day} | {x["n"]} (Commander-legal) | any printing{price} | proxy or real | {d["name"]} | '
                       f'to get ({", ".join(k.lower() for k in x.get("k", []))}, {"yes" if x["a"] == "y" else "maybe"})')
        print(f'{d["name"]}: {len(rows)} new')
    if add:
        open(LOG, 'a', encoding='utf-8').write(('' if log.endswith('\n') else '\n') + '\n'.join(add) + '\n')
    else:
        print('nothing new')

if __name__ == '__main__':
    main()
