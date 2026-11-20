#!/usr/bin/env python3
"""Adds the picks-sync snippet to every page that keeps Fav/Bench/Trash marks in localStorage, and to the templates that build them,
so the user's selections reach the shared table (tables/t7q2xm4k-picks/<page path>) where Claude can read them. The marks used to live
in one browser only, which made "take my favorites" impossible. Idempotent (marker 'picks-sync'). New carousel templates must carry it.
Run from the repo root:  python3 tools/add_sync.py
"""
import os, re
SNIP = ('<script>/*picks-sync: back up fav/bench/trash marks to the shared table; see tools/add_sync.py*/'
        '(function(){try{var B="https://commander-life-39708-default-rtdb.firebaseio.com/tables/t7q2xm4k-picks/"'
        '+location.pathname.replace(/[^A-Za-z0-9_-]+/g,"_").replace(/^_+|_+$/g,"")+".json",R=/(favs|marks)$/,t;'
        'function snap(){var o={},i,k,v;for(i=0;i<localStorage.length;i++){k=localStorage.key(i);'
        'if(R.test(k)){v=localStorage.getItem(k);o[k]=v}}return o}'
        'function has(o){for(var k in o)if(o[k]&&o[k].length>2)return 1;return 0}'
        'function push(force){clearTimeout(t);t=setTimeout(function(){try{var o=snap();if(!force&&!has(o))return;o.at=Date.now();'
        'fetch(B,{method:"PATCH",headers:{"Content-Type":"application/json"},keepalive:true,body:JSON.stringify(o)}).catch(function(){})}catch(e){}},400)}'
        'var si=Storage.prototype.setItem,ri=Storage.prototype.removeItem;'
        'Storage.prototype.setItem=function(k){si.apply(this,arguments);if(this===localStorage&&R.test(k))push(1)};'
        'Storage.prototype.removeItem=function(k){ri.apply(this,arguments);if(this===localStorage&&R.test(k))push(1)};'
        'push(0)}catch(e){}})()</script>')
n = 0
for d, _, fs in os.walk('.'):
    if '.git' in d.split(os.sep) or 'node_modules' in d: continue
    for f in fs:
        if not f.endswith('.html'): continue
        p = os.path.join(d, f)
        s = open(p, encoding='utf-8').read()
        if 'picks-sync' in s or "favs" not in s or 'localStorage' not in s: continue
        if p.startswith('./theme') or p in ('./index.html', './archenemy.html'): continue
        m = re.search(r'</title>', s)
        if not m: print('no title', p); continue
        s = s[:m.end()] + '\n' + SNIP + s[m.end():]
        open(p, 'w', encoding='utf-8', newline='\n').write(s); n += 1
print(n, 'pages patched')
