# Make an offline copy of a carousel page: download every Scryfall image and inline it as a WebP data URI.
# Needed for the claude.ai artifact, whose page can't load images from other sites.
import re,sys,io,base64,urllib.request,concurrent.futures as cf
from PIL import Image
src,out=sys.argv[1],sys.argv[2]
t=open(src).read()
urls=sorted(set(re.findall(r'https://cards\.scryfall\.io/normal/[^"]+',t)))
def conv(u):
    req=urllib.request.Request(u,headers={'User-Agent':'commander-life/1.0'})
    im=Image.open(io.BytesIO(urllib.request.urlopen(req,timeout=60).read())).convert('RGB')
    b=io.BytesIO();im.save(b,'WEBP',quality=72);return u,'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
with cf.ThreadPoolExecutor(6) as ex:
    for u,d in ex.map(conv,urls): t=t.replace(u,d)
open(out,'w').write(t);print(len(urls),'images',len(t)//1024,'KB')
