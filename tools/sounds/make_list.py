"""Rebuild sounds/index.html, the list of every turn-button clip, sounds/lines.html, every spoken line
with who says it, its occasion (from) and source, and the turn button's pools in
index.html (TURN_POOLS), from sounds/clips.json.

sounds/clips.json holds each clip's file (f, 'long/' prefix for files in sounds/long/), pool,
length (d), kind ('sound', or 'talk' for anything with words), source name and link (src, url),
group (OpenGameArt, Presidents, ...) and, for quotes, the words. This refreshes lengths from the
files, sets each pool from its length (long is over LONG_OVER seconds, whatever the folder), adds any
new file with an unknown source (fill it in by hand, from sounds/CREDITS.md; a new clip's kind is
'talk' if it has a quote, else 'sound', so check it), drops files that are gone, and writes both
pages. Run from the repo root.
"""
import json, os, re, subprocess
LONG_OVER = 3.0
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sounds')
data = {c['f']: c for c in json.load(open(os.path.join(root, 'clips.json')))}
seen = []
for sub in ('', 'long'):
    for f in sorted(os.listdir(os.path.join(root, sub))):
        if not f.endswith('.mp3'): continue
        key = (sub + '/' if sub else '') + f[:-4]
        d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                  os.path.join(root, sub, f)], capture_output=True, text=True).stdout)
        c = data.get(key) or {'f': key, 'src': 'Unknown (add to clips.json)', 'url': '', 'grp': 'OpenGameArt'}
        c.update(d=round(d, 1)); c['pool'] = 'long' if c['d'] > LONG_OVER else 'short'
        c.setdefault('kind', 'talk' if c.get('quote') else 'sound'); seen.append(c)
json.dump(seen, open(os.path.join(root, 'clips.json'), 'w'), indent=0, ensure_ascii=False)
t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'list-template.html')).read()
open(os.path.join(root, 'index.html'), 'w').write(t.replace('/*CLIPS*/[]', json.dumps(seen, ensure_ascii=False, separators=(',', ':'))))
lt = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lines-template.html')).read()
lines = [{k: c[k] for k in ('f', 'd', 'quote', 'who', 'from', 'src', 'url', 'grp', 'note') if c.get(k)} for c in seen if c.get('kind') == 'talk']
open(os.path.join(root, 'lines.html'), 'w').write(lt.replace('/*LINES*/[]', json.dumps(lines, ensure_ascii=False, separators=(',', ':'))))
pools = {p: {k: ' '.join(c['f'] for c in seen if c['pool'] == p and c['kind'] == k) for k in ('sound', 'talk')}
         for p in ('short', 'long')}
page = os.path.join(root, '..', 'index.html')
html = open(page).read()
html, n = re.subn(r'(const TURN_POOLS = /\*POOLS\*/).*?;\n', lambda m: m.group(1) + json.dumps(pools) + ';\n', html, count=1)
assert n == 1, 'TURN_POOLS not found in index.html'
open(page, 'w').write(html)
print(len(seen), 'clips;', ', '.join(f'{p} {k} {len(v.split()) if v else 0}' for p in pools for k, v in pools[p].items()))
