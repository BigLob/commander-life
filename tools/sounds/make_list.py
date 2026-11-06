"""Rebuild sounds/index.html, the list of every turn-button clip, from sounds/clips.json.

sounds/clips.json holds each clip's file (f, 'long/' prefix for the long pool), pool, length (d),
source name and link (src, url), group (OpenGameArt or Presidents) and, for quotes, the words.
This refreshes lengths from the files, adds any new file with an unknown source (fill it in by hand,
from sounds/CREDITS.md), drops files that are gone, and writes the page. Run from the repo root.
"""
import json, os, subprocess
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sounds')
data = {c['f']: c for c in json.load(open(os.path.join(root, 'clips.json')))}
seen = []
for sub, pool in (('', 'short'), ('long', 'long')):
    for f in sorted(os.listdir(os.path.join(root, sub))):
        if not f.endswith('.mp3'): continue
        key = (sub + '/' if sub else '') + f[:-4]
        d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                  os.path.join(root, sub, f)], capture_output=True, text=True).stdout)
        c = data.get(key) or {'f': key, 'src': 'Unknown (add to clips.json)', 'url': '', 'grp': 'OpenGameArt'}
        c.update(pool=pool, d=round(d, 1)); seen.append(c)
# Which game events (index.html's EVENT_SOUNDS) each clip also plays on, for the event chips.
import re
html = open(os.path.join(root, '..', 'index.html')).read()
ev = re.search(r'const EVENT_SOUNDS = \{(.*?)\n  \};', html, re.S).group(1)
on = {}
for name, lst in re.findall(r"(\w+): '([^']*)'", ev):
    for f in lst.split(): on.setdefault(f, []).append(name)
for c in seen:
    if c['f'] in on: c['ev'] = on[c['f']]
    else: c.pop('ev', None)
json.dump(seen, open(os.path.join(root, 'clips.json'), 'w'), indent=0, ensure_ascii=False)
t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'list-template.html')).read()
open(os.path.join(root, 'index.html'), 'w').write(t.replace('/*CLIPS*/[]', json.dumps(seen, ensure_ascii=False, separators=(',', ':'))))
print(len(seen), 'clips')
