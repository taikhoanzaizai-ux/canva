"""Local planning, input parsing and durable project state. No Canva private API."""
from __future__ import annotations
import difflib, json, math, os, re, unicodedata, zipfile
from pathlib import Path
from xml.etree import ElementTree

VERSION = '0.2.8'

def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFD', str(text).lower().replace('đ','d')) if unicodedata.category(c) != 'Mn')

# Vietnamese searches first; English fallback for anatomical footage.
TOPICS = [
 ('thức dậy|tỉnh giấc', ['người cao tuổi thức dậy buổi sáng','thức dậy trên giường'], ['wake','morning','bed'], ['ballet','baby']),
 ('chân nặng|bước chân|đôi chân', ['người cao tuổi đau chân','chân nặng mỏi'], ['leg','calf','senior'], ['ballet','baby']),
 ('thắt lưng|lưng ê|đau lưng', ['người cao tuổi đau lưng','đau thắt lưng'], ['back pain','elderly','senior'], ['gym']),
 ('lờ đờ|mệt mỏi|mệt', ['người cao tuổi mệt mỏi','dụi mắt mệt mỏi'], ['tired','elderly','eyes'], []),
 ('ngủ|bảy tám|bảy, tám', ['người cao tuổi ngủ','ngủ ngon trên giường'], ['sleep','bed','elderly'], ['baby']),
 ('thuốc|thực phẩm chức năng', ['người cao tuổi uống thuốc','đọc nhãn thuốc'], ['medicine','pills','elderly'], []),
 ('tắc nghẽn|tắc mạch|tắc động mạch|ứ đọng|huyết khối', ['tắc nghẽn mạch máu','huyết khối tĩnh mạch','blood clot vein'], ['blood','clot','vein','artery'], []),
 ('máu|tuần hoàn|tĩnh mạch', ['tuần hoàn máu','hồng cầu trong mạch máu','red blood cells'], ['blood','vein','circulation'], []),
 ('nội tạng|gan|dạ dày', ['nội tạng cơ thể người','mô phỏng nội tạng'], ['organ','anatomy','body'], []),
 ('tim|trái tim', ['trái tim cơ thể người','mô phỏng tim đập','human heart'], ['heart','cardio'], []),
 ('thận|tàng tinh|cốt tủy', ['thận cơ thể người','mô phỏng thận','human kidney'], ['kidney','renal'], []),
 ('nhón gót|kiễng|nhịp nhón|đầu ngón', ['nhón gót chân','bài tập nâng gót chân','calf raises'], ['heel','tiptoe','barefoot','activewear'], ['ballet','ballerina','baby','child']),
 ('bắp chân|cơ bắp|co thắt', ['cơ bắp chân','giải phẫu cơ bắp chân','gastrocnemius'], ['calf','gastrocnemius','muscle'], []),
 ('gân gót|kéo căng', ['gân gót chân','giãn cơ bắp chân','achilles anatomy'], ['achilles','stretch','calf'], []),
 ('dũng tuyền|lòng bàn chân|huyệt', ['xoa bóp lòng bàn chân','bấm huyệt bàn chân'], ['foot','massage','feet'], []),
 ('hít|thở|hít vào', ['hít thở sâu dưỡng sinh','người cao tuổi hít thở'], ['breath','senior','relax'], []),
 ('hạ gót|chạm đất', ['bàn chân chạm sàn','bàn chân đứng trên sàn'], ['feet','floor','barefoot'], ['ballet']),
 ('đứng thẳng|hai chân|hai tay', ['người cao tuổi tập dưỡng sinh','đứng tập thái cực quyền'], ['senior','tai chi','standing'], []),
 ('động tác|tập tại nhà|tập ngay tại nhà|không cần dụng cụ', ['người cao tuổi tập thể dục tại nhà','người cao tuổi tập dưỡng sinh','senior home exercise'], ['senior','elderly','exercise','stretch'], ['baby','ballet']),
 ('nghiên cứu|khoa học|đại học', ['nhà khoa học nghiên cứu y học','phòng thí nghiệm y học'], ['scientist','research','laboratory'], []),
 ('buổi sáng|bình minh|mỗi sáng', ['bình minh buổi sáng','ánh nắng buổi sáng'], ['sunrise','morning'], []),
 ('đi bộ|nâng đỡ|ngày dài', ['người cao tuổi đi bộ','vợ chồng cao tuổi đi dạo'], ['walking','elderly','senior'], []),
 ('ấm|râm ran|đầu gối', ['xoa bóp bắp chân','chăm sóc đôi chân'], ['calf','massage','leg'], []),
]

def describe(text):
    # Vietnamese accents distinguish thân/thận/thần and tác/tắc. Keep them.
    t = unicodedata.normalize('NFC', str(text)).casefold()
    for pattern, queries, positive, negative in TOPICS:
        if any(re.search(r'(?<!\w)'+re.escape(unicodedata.normalize('NFC',p).casefold())+r'(?!\w)',t) for p in pattern.split('|')):
            return dict(queries=queries, positive=positive, negative=negative, review=False)
    words = re.sub(r'[^\w\s]', ' ', text).split()
    return dict(queries=[' '.join(words[:10]) or 'người cao tuổi dưỡng sinh'], positive=['senior','elderly'], negative=['baby','ballet'], review=True)

def read_script(path):
    p=Path(path)
    if p.suffix.lower()=='.docx':
        with zipfile.ZipFile(p) as z:
            root=ElementTree.fromstring(z.read('word/document.xml'))
        return '\n'.join(''.join(n.itertext()) for n in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
    return p.read_text(encoding='utf-8-sig')

def load_transcript(path):
    p=Path(path)
    if p.suffix.lower()=='.json':
        value=json.loads(p.read_text(encoding='utf-8-sig'))
        segments=value.get('segments',[]) if isinstance(value,dict) else value
        if not isinstance(segments,list): raise ValueError('JSON cần có danh sách segments.')
    else:
        raw=p.read_text(encoding='utf-8-sig').replace('\r','')
        segments=[]
        def sec(t):
            parts=t.replace(',','.').split(':')
            return sum(float(v)*60**i for i,v in enumerate(reversed(parts)))
        for block in re.split(r'\n\s*\n',raw):
            lines=block.strip().splitlines()
            for i,line in enumerate(lines):
                m=re.match(r'([\d:,.]+)\s*-->\s*([\d:,.]+)',line)
                if m: segments.append(dict(start=sec(m[1]),end=sec(m[2]),text=' '.join(lines[i+1:])));break
    previous=-1
    for s in segments:
        s['start'],s['end']=float(s['start']),float(s['end'])
        if not all(math.isfinite(s[x]) for x in ['start','end']) or s['start']<0 or s['end']<=s['start'] or s['start']<previous-.05:
            raise ValueError('Mốc thời gian phụ đề không hợp lệ hoặc chồng lấn.')
        previous=s['end']
    if not segments: raise ValueError('Không có lời đọc có mốc thời gian.')
    return segments

def align_script(segments, script):
    """Restore script spelling at monotonic exact anchors; never invent timestamps.

    The recognizer is still the timing authority. Decline a weak alignment rather
    than silently assigning unrelated script sentences to the audio.
    """
    tokens=re.findall(r'\S+',script)
    words=[dict(w) for s in segments for w in s.get('words',[])]
    if not tokens or len(words)<5:return segments,False
    clean=lambda s:re.sub(r'[^a-z0-9]','',norm(s))
    spoken=[clean(w.get('word','')) for w in words]
    written=[clean(t) for t in tokens]
    blocks=difflib.SequenceMatcher(None,spoken,written,autojunk=False).get_matching_blocks()
    anchors=[(b.a+j,b.b+j) for b in blocks for j in range(b.size)]
    if len(anchors)/max(1,len(words))<.35:return segments,False
    mapped={};
    for i,j in anchors:mapped[j]=(float(words[i]['start']),float(words[i]['end']))
    for (ai,aj),(bi,bj) in zip(anchors,anchors[1:]):
        if bj<=aj+1:continue
        a=float(words[ai]['end']);b=float(words[bi]['start'])
        if b<=a:continue
        step=(b-a)/(bj-aj-1)
        for k in range(aj+1,bj):mapped[k]=(a+(k-aj-1)*step,a+(k-aj)*step)
    result=[]
    for j in sorted(mapped):
        a,b=mapped[j]
        if b>a:result.append(dict(word=tokens[j],start=a,end=b))
    if not result:return segments,False
    # Keep words before/after the covered script window, so voice is never lost.
    first,last=anchors[0][0],anchors[-1][0]
    result=words[:first]+result+words[last+1:]
    return [dict(start=float(words[0]['start']),end=float(words[-1]['end']),text=' '.join(w['word'] for w in result),words=result)],True

def make_plan(segments, start=0, end=None, opening=35, max_seconds=5):
    """Prefer real word boundaries; SRT without word times is explicitly approximate."""
    start=float(start); end=float(end if end is not None else segments[-1]['end'])
    max_seconds=float(max_seconds)
    if not 1<=max_seconds<=5: raise ValueError('Độ dài cảnh phải từ 1 đến 5 giây.')
    if not 0<=start<end: raise ValueError('Điểm kết thúc phải sau điểm bắt đầu.')
    words=[]
    approximate=False
    for s in segments:
        if s['end']<=start or s['start']>=end: continue
        ws=s.get('words') or []
        if not ws:
            approximate=True
            tokens=str(s.get('text','')).split(); d=(s['end']-s['start'])/max(1,len(tokens))
            ws=[dict(word=t,start=s['start']+i*d,end=s['start']+(i+1)*d) for i,t in enumerate(tokens)]
        for w in ws:
            a,b=max(start,float(w['start'])),min(end,float(w['end']))
            if b>a: words.append(dict(text=str(w.get('word',w.get('text',''))).strip(),start=a,end=b))
    if not words: raise ValueError('Không có lời đọc trong khoảng đã chọn.')
    words.sort(key=lambda x:x['start'])
    groups=[]; group=[]; at=start
    for w in words:
        if group and w['end']-at>max_seconds:
            groups.append((at,max(at+.1,min(w['start'],at+max_seconds)),group)); at=groups[-1][1]; group=[]
        # Split long silence rather than creating oversized scenes.
        while w['start']-at>=max_seconds:
            groups.append((at,at+max_seconds,group or [dict(text='Khoảng nghỉ')]))
            at+=max_seconds;group=[]
        group.append(w)
        text=' '.join(x['text'] for x in group)
        punctuation=bool(re.search(r'[,;:.!?…–—]$',w['text']))
        if w['end']-at >= (0.65 if at-start<opening else 3.5) and punctuation:
            groups.append((at,w['end'],group));at=w['end'];group=[]
    if group: groups.append((at,min(end,max(at+.1,words[-1]['end'])),group));at=groups[-1][1]
    while at<end-.001:
        to=min(end,at+max_seconds);groups.append((at,to,[dict(text='Khoảng nghỉ') ]));at=to
    scenes=[]
    for a,b,g in groups:
        if b-a<.05:continue
        text=' '.join(x['text'] for x in g)
        desc=describe(text)
        scenes.append(dict(id=len(scenes)+1,start=round(a-start,3),source_start=round(a,3),duration=round(b-a,3),text=text,**desc))
    return dict(scenes=scenes,duration=round(end-start,3),source_start=start,approximate=approximate)

def atomic_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    with temp.open('w',encoding='utf8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(temp,path)

def valid_canva(url):
    return bool(re.fullmatch(r'https://www\.canva\.com/design/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/edit(?:\?[^\s]*)?',url.strip()))


def legacy_description(text):
    """Recognize generated plans from <=0.2.6, so user edits remain untouched."""
    t=norm(text)
    for pattern,queries,positive,negative in TOPICS:
        if pattern.startswith('động tác|'):continue
        if pattern.startswith('tắc nghẽn|'):pattern='tắc|ứ đọng|huyết khối'
        if any(norm(p) in t for p in pattern.split('|')):
            return dict(queries=queries,positive=positive,negative=negative,review=False)
    words=re.sub(r'[^\w\s]', ' ', text).split()
    return dict(queries=[' '.join(words[:10]) or 'người cao tuổi dưỡng sinh'],positive=['senior','elderly'],negative=['baby','ballet'],review=True)


def repair_pending_keywords(state):
    """Reclassify all old generated topics; never rewrite custom or completed scenes."""
    changed=0
    active=str(state.get('phase',{}).get('id',''))
    for scene in state.get('scenes',[]):
        if scene['id'] in state.get('done',[]) or str(scene['id'])==active:continue
        text=scene.get('text','');old=legacy_description(text);updated=describe(text)
        if scene.get('queries')==old['queries'] and updated['queries']!=old['queries']:
            scene.update(updated);changed+=1
    return changed
