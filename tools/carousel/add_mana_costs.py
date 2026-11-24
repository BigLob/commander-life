"""Put each card's mana cost and price, right-aligned, on its name line in every carousel already built
(the user's ask, Nov 24, 2026, with a screenshot circling the right end of the name line), without
rebuilding the pages (several need caches that only live on the desktop PC). Safe to rerun: a page
already patched is skipped, a card that already has 'mc' keeps it. New builds get the same from the
templates and builders directly.

    MANACOST_CACHE=<file> python3 tools/carousel/add_mana_costs.py
"""
import builtins, functools, glob, html as H, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import manacost

# Pages are UTF-8 whatever the PC's default (a Windows build once wrote cp1252 bytes into one).
open = functools.partial(builtins.open, encoding='utf-8')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
T = lambda p: os.path.join(ROOT, p)
CAR = os.path.join(ROOT, 'tools', 'carousel')
MARK = '/*mana+price*/'

# Client-rendered carousels (template.html, cuts-, brew-, rodents-template and their pages): the price
# column already sits on the name line, so the cost goes in front of the price in that column.
PR = re.compile(r'<span class="pr">\$\{money\((\w)\.p\)\}')
CSS_PR = MARK + 'figcaption .pr{display:flex;align-items:center;gap:6px;align-self:flex-start}' + manacost.CSS_MC

# theme/review.html and theme/final.html: name left, cost and price right (no wrapping: the name wraps).
NL_OLD = "<span class=\"nl\"><span class=\"nm\">${E(x.n)}</span>${$p?`<span class=\"pr\">${$p}</span>`:''}</span>"
NL_NEW = "<span class=\"nl\"><span class=\"nm\">${E(x.n)}</span><span class=\"rt\">${manaCost(x.mc)}${$p?`<span class=\"pr\">${$p}</span>`:''}</span></span>"
CSS_NL = (MARK + '.nl{align-items:flex-start}.nl .rt{display:flex;align-items:center;gap:5px;flex:none}'
          '.nl .mc{font-size:.86rem;height:1.2em}.nl .pr{line-height:1.2}\n' + manacost.CSS_MC)

# Python-built pages, theme/<slug>.html and decks/angles.html. Their tiles are narrow (about 104 px),
# so cost and price drop to a line of their own, still right-aligned, when the name leaves no room.
OLDCAP = re.compile(r'(<figcaption>)(<a class="c" [^>]*>[^<]*</a>)((?:(?!</figcaption>).)*?)<span class="m">(\$[\d,.]+)</span>(</figcaption>)')
BARE = re.compile(r'<figcaption>(<a class="c" [^>]*>[^<]*</a>)')
NL = re.compile(r'<span class="nl">(<a class="c" [^>]*>([^<]*)</a>)((?:<span class="pr">[^<]*</span>)?)</span>')
CSS_STATIC = (MARK + '.ct .nl{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:0 4px;min-width:0}'
              '.ct .nl .rt{display:flex;align-items:center;gap:4px;margin-left:auto}'
              '.ct .nl .pr{font-family:var(--f-mono);font-size:.66rem;color:var(--accent)}.ct .nl .mc{font-size:.74rem}'
              'body.noimg .ct .nl{flex:0 1 auto}body.noimg .ct .mc{display:none}\n' + manacost.CSS_MC)

ARR = re.compile(r'const (ALL|SUG)=(?=\[)')


def arrays(t):
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


def static_caps(t):
    """Name, then cost and price, in one .nl row (moving the price up from the caption's end)."""
    t = OLDCAP.sub(lambda m: f'{m[1]}<span class="nl">{m[2]}<span class="pr">{m[4]}</span></span>{m[3]}{m[5]}', t)
    t = BARE.sub(lambda m: f'<figcaption><span class="nl">{m[1]}</span>', t)
    return NL.sub(lambda m: f'<span class="nl">{m[1]}<span class="rt">{manacost.html(manacost.get(H.unescape(m[2])))}{m[3]}</span></span>', t)


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
    for p in static:
        names |= {H.unescape(m) for m in re.findall(r'<a class="c" [^>]*>([^<]*)</a>', open(p).read())}
    trees = {p: json.load(open(p)) for p in theme_json}
    for d in trees.values():
        manacost.fill_tree(d)
    manacost.prefetch(names)

    for p in client + tpls:
        t = open(p).read()
        if MARK in t:
            continue
        for a, b, v in reversed(arrays(t)):
            t = t[:a] + json.dumps(manacost.fill(v), ensure_ascii=False, separators=(',', ':')) + t[b:]
        t = PR.sub(lambda m: f'<span class="pr">${{manaCost({m[1]}.mc)}}${{money({m[1]}.p)}}', t)
        t = add_js(t, 'const money=')
        open(p, 'w').write(add_css(t, CSS_PR))
    for p in (T('theme/review.html'), T('theme/final.html')):
        t = open(p).read()
        if MARK in t:
            continue
        assert t.count(NL_OLD) == 1, p
        t = add_js(t.replace(NL_OLD, NL_NEW), 'function tile(')
        open(p, 'w').write(add_css(t, CSS_NL))
    for p, d in trees.items():
        json.dump(d, open(p, 'w'), separators=(',', ':'))
    for p in static + [os.path.join(CAR, 'theme-picks-template.html'), os.path.join(CAR, 'angles-template.html')]:
        t = open(p).read()
        if MARK in t:
            continue
        open(p, 'w').write(add_css(static_caps(t), CSS_STATIC))
    print('cards', len(names), 'no Scryfall match:', sorted(manacost.NOT_FOUND) or 'none')


if __name__ == '__main__':
    main()
