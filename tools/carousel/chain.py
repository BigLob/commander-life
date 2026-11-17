#!/usr/bin/env python3
"""Builds decks/chain.html: Silverquill Influence's "chain" of adds. Start from the precon, then add the card most
Killian decks on Archidekt play (that the precon doesn't have), then the card most of THOSE decks play, and so on,
with the runners-up at each step to branch to. Needs a scratch dir with decks.json (Archidekt decks, see fetch below)
and info.json (Scryfall type, legality, image per card); pass it as argv[1]. The page does the counting in the browser,
so every alternate can be followed."""
import json,re,sys,collections,os
S=sys.argv[1]; R=os.path.dirname(os.path.abspath(__file__))+'/../..'
D=json.load(open(S+'/decks.json')); info=json.load(open(S+'/info.json'))
html=open(R+'/decks/silverquill-influence.html').read()
pre={c['n'] for c in json.loads(re.search(r'const ALL=(\[.*?\]);\n',html,re.S).group(1))}
seen=set(); U=[]
for d in D:
    if 'Killian, Decisive Mentor' not in d['cards'] or not 85<=len(d['cards'])<=110: continue
    k=tuple(d['cards'])
    if k in seen: continue
    seen.add(k); U.append(d)
def land(n): return 'Land' in info[n]['t']
rows=[]
for d in U:
    adds=[c for c in d['cards'] if c not in pre and c in info and 'Basic' not in info[c]['t'] and not land(c) and info[c]['l']=='legal']
    ench=sum('Enchantment' in info[c]['t'] for c in adds)
    rows.append((adds,ench))
cnt=collections.Counter(c for a,_ in rows for c in a)
names=sorted(n for n,c in cnt.items() if c>=5)
ix={n:i for i,n in enumerate(names)}
cards=[[n,info[n]['i'],info[n]['m'],info[n]['t'].split(' — ')[0],int(info[n]['gc'])] for n in names]
decks=[[ix[c] for c in a if c in ix]+[-1,e] for a,e in rows]  # last two: marker, enchantment count
decks=[[x for x in d[:-2]]+[d[-1]] for d in decks]  # cards..., enchantment count last
out=open(R+'/tools/carousel/chain-template.html').read()
out=out.replace('__CARDS__',json.dumps(cards,ensure_ascii=False,separators=(',',':'))).replace('__DECKS__',json.dumps(decks,separators=(',',':'))).replace('__N__',str(len(U)))
open(R+'/decks/chain.html','w').write(out)
print(len(U),'decks,',len(names),'cards')
