#!/usr/bin/env python3
"""Writes sounds/tonight.json: which turn-button clips to favor tonight.

  python3 tools/sounds/tonight.py [--share 0.3] [--mute TERM ...] TERM [TERM ...]
  python3 tools/sounds/tonight.py --clear

A TERM is a deck we own (DECKS below, e.g. "borg", "revival trance"), a clip group from
clips.json ("Star Trek", "Doom"), or any word found in a clip's file name, quote or note.
Matching clips are BOOSTED to --share of turn-button taps (default 0.3); --mute removes clips
the same way. index.html reads the file on load and whenever a phone comes back to the app.
Prints how many clips each term found; a term with none means that deck has no clips yet.
"""
import argparse, json, os, re, datetime
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
# Deck name (lowercase) -> clip groups. Universes Beyond decks first; others have no theme clips.
TREK = ['Star Trek']
DECKS = {
    'we are the borg': TREK, 'borg': TREK, 'landing party': TREK, 'federation fleet': TREK,
    'klingon fury': TREK, 'star trek': TREK,
    'revival trance': ['Final Fantasy'], 'final fantasy': ['Final Fantasy'],
}

def resolve(term, clips):
    t = term.lower().strip()
    groups = DECKS.get(t) or [g for g in {c.get('grp') for c in clips} if g and g.lower() == t]
    if groups:
        return [c['f'] for c in clips if c.get('grp') in groups]
    rx = re.compile(re.escape(t))
    return [c['f'] for c in clips if rx.search(' '.join(str(c.get(k, '')) for k in ('f', 'quote', 'note', 'who', 'grp')).lower())]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('terms', nargs='*')
    ap.add_argument('--share', type=float, default=0.3)
    ap.add_argument('--mute', nargs='*', default=[])
    ap.add_argument('--clear', action='store_true')
    a = ap.parse_args()
    clips = json.load(open(os.path.join(ROOT, 'sounds/clips.json')))
    # pool file names: root clips are 'name', long/ ones 'long/name' (as in TURN_POOLS)
    name = lambda c: ('long/' if c.get('pool') == 'long' and os.path.exists(os.path.join(ROOT, 'sounds/long', c['f'] + '.mp3')) else '') + c['f']
    byf = {c['f']: name(c) for c in clips}
    out = {'updated': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'), 'decks': [], 'share': 0, 'boost': [], 'mute': []}
    if not a.clear:
        out['decks'], out['share'] = a.terms, a.share
        for t in a.terms:
            f = resolve(t, clips); print(f'{t}: {len(f)} clips' + ('  (NONE: no clips yet)' if not f else ''))
            out['boost'] += [byf[x] for x in f]
        for t in a.mute:
            f = resolve(t, clips); print(f'mute {t}: {len(f)} clips')
            out['mute'] += [byf[x] for x in f]
        out['boost'] = sorted(set(out['boost']) - set(out['mute'])); out['mute'] = sorted(set(out['mute']))
        if not out['boost']: out['share'] = 0
    json.dump(out, open(os.path.join(ROOT, 'sounds/tonight.json'), 'w'), indent=1)
    print(f"boost {len(out['boost'])} clips to {out['share']:.0%} of taps, mute {len(out['mute'])}")
main()
