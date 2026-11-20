"""Names to leave off the staples and squirrels carousels (the user's rule, Nov 20, 2026): every card already in the Squirreled Away
box, and every card already picked (yes or maybe) to add to it, which buylist.txt records under "Squirreled Away (Chatterfang)"."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')

def sa_names():
    h = open(os.path.join(ROOT, 'decks', 'squirreled-away.html'), encoding='utf-8').read()
    box = {c['n'].split(' // ')[0] for c in json.loads(re.search(r'const ALL=(\[.*?\]);\n', h, re.S).group(1))}
    picked = set()
    for line in open(os.path.join(ROOT, 'buylist.txt'), encoding='utf-8'):
        p = [x.strip() for x in line.split('|')]
        if len(p) >= 5 and p[4].startswith('Squirreled Away (Chatterfang)'):
            picked.add(re.sub(r'\s*\((?:BG, )?Commander-legal\)$', '', p[1]).split(' (')[0])
    return box, picked
