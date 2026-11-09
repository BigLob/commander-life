"""Build the soundboard from sounds/clips.json and tools/sounds/soundboard-template.html.

    python3 tools/sounds/make_soundboard.py             writes sounds/soundboard.html (plays the files in sounds/)
    python3 tools/sounds/make_soundboard.py OUT.html    also writes OUT.html with every clip embedded, for the
                                                        claude.ai artifact (artifacts can't load outside files)

Kinds: pres, every clip in the Presidents group. To add a kind, add it to KINDS here and a button
with data-k="<kind>" to the template. Run from the repo root.
"""
import base64, json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(here, '..', '..', 'sounds')
clips = json.load(open(os.path.join(root, 'clips.json')))
KINDS = {'pres': lambda c: c.get('grp') == 'Presidents'}
kinds = {k: [{'f': c['f'], 'q': c.get('quote', ''), 'w': c.get('who', '')} for c in clips if test(c)] for k, test in KINDS.items()}
files = sorted({c['f'] for v in kinds.values() for c in v})
tpl = open(os.path.join(here, 'soundboard-template.html')).read()
def page(src):
    return tpl.replace('/*KINDS*/{}', json.dumps(kinds, ensure_ascii=False, separators=(',', ':'))).replace(
        '/*SRC*/{}', json.dumps(src, separators=(',', ':')))
head = '<!doctype html>\n<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
open(os.path.join(root, 'soundboard.html'), 'w').write(head + page({f: f + '.mp3' for f in files}))
if len(sys.argv) > 1:
    emb = {f: 'data:audio/mpeg;base64,' + base64.b64encode(open(os.path.join(root, f + '.mp3'), 'rb').read()).decode() for f in files}
    open(sys.argv[1], 'w').write(page(emb))
print(', '.join(f'{k} {len(v)}' for k, v in kinds.items()), 'clips')
