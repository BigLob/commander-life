"""One-off (Nov 24, 2026): put each card's mana cost, right-aligned, on its name line in every carousel
already built, without rebuilding them (several need caches that only live on the desktop PC). Safe to
rerun: pages already patched are skipped, cards that already have 'mc' keep it. New builds get the
cost from the templates and builders directly.

    MANACOST_CACHE=<file> python3 tools/carousel/add_mana_costs.py
"""
import glob, html as H, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import manacost

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
T = lambda p: os.path.join(ROOT, p)
CAR = os.path.join(ROOT, 'tools', 'carousel')

# Client-rendered carousels (template.html, cuts-, brew-, rodents-template and their pages).
PR = re.compile(r'<span class="pr">\$\{money\((\w)\.p\)\}')
CSS_PR = 'figcaption .pr{display:flex;flex-direction:column;align-items:flex-end}\n' + manacost.CSS_MC
# theme/review.html and theme/final.html.
NM = '<span class="nm">${E(x.n)}</span>'
CSS_NL = ('.nl{display:flex;justify-content:space-between;align-items:flex-start;gap:6px}'
          '.nl .mc{font-size:.86rem;height:1.2em}\n') + manacost.CSS_MC
# Python-built pages: theme/<slug>.html and decks/angles.html.
AC = re.compile(r'<figcaption><a class="c" href="([^"]*)" target="_blank" rel="noopener">([^<]*)</a>')
CSS_STATIC = ('.ct .nl{display:flex;justify-content:space-between;align-items:flex-start;gap:4px;flex:1 1 100%;min-width:0}'
              '.ct .nl .mc{font-size:.76rem}body.noimg .ct .nl{flex:0 1 auto}body.noimg .ct .mc{display:none}\n') + manacost.CSS_MC

ARR = re.compile(r'const (ALL|SUG)=(?=\[)')


def arrays(t):
    """(start, end, list) for each const ALL=[...] / SUG=[...] in a page."""
    out = []
    for m in ARR.finditer(t):
        v, end = json.JSONDecoder().raw_decode(t, m.end())
        out.append((m.end(), end, v))
    return out


def add_css(t, css):
    i = t.index('</style>')
    return t[:i] + css + t[i:]


def add_js(t, anchor):
    i = t.index(anchor)
    return t[:i] + manacost.JS + t[i:]


def main():
    client = [p for p in glob.glob(T('**/*.html'), recursive=True)
              if '/tools/' not in p and PR.search(open(p).read())]
    tpls = [os.path.join(CAR, f) for f in ('template.html', 'cuts-template.html', 'brew-template.html', 'rodents-template.html')]
    theme_json = [p for p in glob.glob(T('theme/*.json')) if not p.endswith(('-combos.json', '-review.json', 'index.json'))]
    static = [p for p in glob.glob(T('theme/*.html')) if not p.endswith(('review.html', 'final.html'))] + [T('decks/angles.html')]

    names = set()
    for p in client:
        for _, _, v in arrays(open(p).read()):
            names |= {c['n'] for c in v}
    trees = {p: json.load(open(p)) for p in theme_json}
    for p, d in trees.items():
        manacost.fill_tree(d)  # looks up as it goes
    for p in static:
        names |= {H.unescape(m.group(2)) for m in AC.finditer(open(p).read())}
    manacost.prefetch(names)
    print('names', len(names), 'not found', len(manacost.NOT_FOUND))

    for p in client + tpls:
        t = open(p).read()
        if 'function manaCost' in t:
            continue
        for a, b, v in reversed(arrays(t)):
            t = t[:a] + json.dumps(manacost.fill(v), ensure_ascii=False, separators=(',', ':')) + t[b:]
        t = PR.sub(lambda m: f'<span class="pr">${{manaCost({m[1]}.mc)}}${{money({m[1]}.p)}}', t)
        t = add_js(t, 'const money=')
        t = add_css(t, CSS_PR)
        open(p, 'w').write(t)
    for p in (T('theme/review.html'), T('theme/final.html')):
        t = open(p).read()
        if 'function manaCost' in t:
            continue
        assert NM in t, p
        t = t.replace(NM, '<span class="nl">' + NM + '${manaCost(x.mc)}</span>')
        t = add_js(t, 'function tile(')
        t = add_css(t, CSS_NL)
        open(p, 'w').write(t)
    for p, d in trees.items():
        json.dump(d, open(p, 'w'), separators=(',', ':'))
    for p in static + [os.path.join(CAR, 'theme-picks-template.html'), os.path.join(CAR, 'angles-template.html')]:
        t = open(p).read()
        if '.ct .nl{' in t:
            continue
        t = AC.sub(lambda m: f'<figcaption><span class="nl"><a class="c" href="{m[1]}" target="_blank" rel="noopener">{m[2]}</a>'
                             f'{manacost.html(manacost.get(H.unescape(m[2])))}</span>', t)
        t = add_css(t, CSS_STATIC)
        open(p, 'w').write(t)
    if manacost.NOT_FOUND:
        print('no Scryfall match:', sorted(manacost.NOT_FOUND))


if __name__ == '__main__':
    main()
