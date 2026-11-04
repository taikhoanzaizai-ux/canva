"""Public Pexels/Pixabay pages only; no API key, ad links, or access-barrier bypass."""
import hashlib,html,json,re,subprocess,os,time,urllib.error,urllib.parse,urllib.request
from html.parser import HTMLParser
from pathlib import Path
from .core import norm

SITES={
 'pexels':dict(host='www.pexels.com',license='https://www.pexels.com/license/',video='https://www.pexels.com/search/videos/{query}/',image='https://www.pexels.com/search/{query}/',cdn={'videos.pexels.com','images.pexels.com'}),
 'pixabay':dict(host='pixabay.com',license='https://pixabay.com/service/license-summary/',video='https://pixabay.com/videos/search/{query}/',image='https://pixabay.com/images/search/{query}/',cdn={'cdn.pixabay.com'})}

def valid_page(url,provider,kind):
    u=urllib.parse.urlsplit(url);site=SITES[provider]
    if u.scheme!='https' or u.hostname!=site['host'] or u.username or u.password:return False
    path=u.path
    if '/search/' in path or path.endswith('/videos/') or path.endswith('/images/'):return False
    return bool(re.fullmatch(r'/(?:[a-z]{2}-[a-z]{2}/)?video/[^/]+-\d+/?',path) if provider=='pexels' and kind=='video' else re.fullmatch(r'/(?:[a-z]{2}-[a-z]{2}/)?photo/[^/]+-\d+/?',path) if provider=='pexels' else re.fullmatch(r'/(?:[a-z]{2}/)?videos/[^/]+-\d+/?',path) if kind=='video' else re.fullmatch(r'/(?:[a-z]{2}/)?photos/[^/]+-\d+/?',path))

def allowed_url(url):
    u=urllib.parse.urlsplit(url)
    allowed={s['host'] for s in SITES.values()}|set.union(*(s['cdn'] for s in SITES.values()))
    return u.scheme=='https' and u.hostname in allowed and not u.username and not u.password

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed_url(newurl):raise ValueError('Bỏ qua chuyển hướng quảng cáo/website ngoài nguồn miễn phí.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch(url,limit=3*1024*1024):
    if not allowed_url(url):raise ValueError('Nguồn tải không được phép.')
    request=urllib.request.Request(url,headers={'User-Agent':'SKST-Canva-Studio/0.5 (public media search)'})
    with urllib.request.build_opener(SafeRedirect()).open(request,timeout=10) as response:
        data=response.read(limit+1)
        if len(data)>limit:raise ValueError('Tư liệu vượt giới hạn tải.')
        return data

class Page(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.jsonld=[];self.ld=False;self.buffer=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href') and 'sponsored' not in (a.get('rel','')+' '+a.get('class','')).lower():self.links.append(a['href'])
        if tag=='script' and a.get('type')=='application/ld+json':self.ld=True;self.buffer=''
    def handle_data(self,data):
        if self.ld:self.buffer+=data
    def handle_endtag(self,tag):
        if tag=='script' and self.ld:
            try:self.jsonld.append(json.loads(self.buffer))
            except ValueError:pass
            self.ld=False

def objects(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():yield from objects(child)
    elif isinstance(value,list):
        for child in value:yield from objects(child)

def extract_asset(markup,page_url,provider,kind):
    if not valid_page(page_url,provider,kind):return None
    parser=Page();parser.feed(markup)
    for obj in objects(parser.jsonld):
        types=obj.get('@type',[]);types=[types] if isinstance(types,str) else types
        if ('VideoObject' if kind=='video' else 'ImageObject') not in types:continue
        url=obj.get('contentUrl','')
        if not isinstance(url,str):continue
        u=urllib.parse.urlsplit(url)
        if u.scheme!='https' or u.hostname not in SITES[provider]['cdn'] or u.username or u.password:continue
        title=html.unescape(str(obj.get('name',obj.get('caption',''))))
        if not title:continue
        author=obj.get('author',{});author=author.get('name','') if isinstance(author,dict) else str(author)
        return dict(id=provider+':'+page_url.rstrip('/').split('/')[-1],title=title,url=url,page=page_url,author=author,license=SITES[provider]['license'],provider=provider,kind=kind)
    return None

def relevant(asset,scene):
    text=norm(asset['title'])
    if any(norm(w) in text for w in scene.get('negative',[])):return False
    if not scene.get('allow_all_media') and not re.search(r'\b(man|woman|people|person|doctor|patient|senior|elderly|hands|feet|male|female)\b',text):return False
    subjects=scene.get('subjects') or [w for w in scene.get('positive',[]) if norm(w) not in {'senior','elderly','home','cao tuoi'}]
    return bool(subjects) and any(re.search(r'(?<!\w)'+re.escape(norm(w))+r'(?:s|es)?(?!\w)',text) for w in subjects) and (scene.get('topic_only') or not scene.get('actions') or any(norm(w) in text for w in scene['actions']))

def prepare_external(scene,used,folder,ffmpeg):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);diagnostics=[];blocked=set()
    deadline=time.monotonic()+60
    english=[w for w in scene.get('subjects',[]) if w.isascii()][:1 if scene.get('topic_only') else 2]
    query=' '.join(english) or scene.get('queries',['health'])[0]
    # Native video libraries first, then photos. Sponsored destinations never qualify.
    for kind in ['video','image']:
        for provider,site in SITES.items():
            if time.monotonic()>=deadline:return None,None,diagnostics+[dict(message='Hết thời gian tìm nguồn ngoài; chuyển ảnh báo lỗi/dự phòng.')]
            if provider in blocked:continue
            search=site[kind].format(query=urllib.parse.quote(query))
            try:
                parser=Page();parser.feed(fetch(search).decode('utf8','replace'))
                links=list(dict.fromkeys(urllib.parse.urljoin(search,u) for u in parser.links))
                for page_url in [u for u in links if valid_page(u,provider,kind)][:6]:
                    if time.monotonic()>=deadline:return None,None,diagnostics
                    asset=extract_asset(fetch(page_url).decode('utf8','replace'),page_url,provider,kind)
                    if not asset or asset['id'] in used or not relevant(asset,scene):continue
                    raw=fetch(asset['url'],30*1024*1024);key=hashlib.sha256(raw).hexdigest()[:16]
                    suffix='.mp4' if kind=='video' else '.jpg';source=folder/(key+suffix);source.write_bytes(raw)
                    target=folder/f'SKST_media_{key}.mp4'
                    command=[str(ffmpeg),'-v','error','-y']+(['-loop','1'] if kind=='image' else [])+['-i',str(source.resolve()),'-t',str(scene['duration']),'-vf','scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1','-an','-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p',str(target.resolve())]
                    subprocess.run(command,check=True,capture_output=True,timeout=max(1,min(30,deadline-time.monotonic())),creationflags=0x08000000 if os.name=='nt' else 0)
                    from .batches import probe_duration
                    if probe_duration(ffmpeg,target)<scene['duration']-.05:continue
                    return target,asset,diagnostics
            except urllib.error.HTTPError as exc:
                diagnostics.append(dict(provider=provider,status=exc.code,message='Nguồn từ chối truy cập tự động; không thử vượt chặn.'))
                if exc.code in (401,403,429):blocked.add(provider);continue
            except (OSError,ValueError,subprocess.SubprocessError) as exc:
                diagnostics.append(dict(provider=provider,message=type(exc).__name__))
    return None,None,diagnostics
