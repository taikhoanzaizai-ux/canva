"""Local planning, input parsing and durable project state. No Canva private API."""
from __future__ import annotations
import difflib, json, math, os, re, unicodedata, zipfile
from pathlib import Path
from xml.etree import ElementTree

VERSION = '0.14.10'

def project_title(name,part_index=0):
    name=' '.join(str(name or '').split())
    if len(name)>180:raise ValueError('Tên dự án tối đa 180 ký tự.')
    if type(part_index) is not int or part_index<0:raise ValueError('Số phần không hợp lệ.')
    return (name if part_index==0 else f'{name}.{part_index+1}') if name else ''

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

def topic_description(text):
    # Vietnamese accents distinguish thân/thận/thần and tác/tắc. Keep them.
    t = unicodedata.normalize('NFC', str(text)).casefold()
    for pattern, queries, positive, negative in TOPICS:
        if any(re.search(r'(?<!\w)'+re.escape(unicodedata.normalize('NFC',p).casefold())+r'(?!\w)',t) for p in pattern.split('|')):
            return dict(queries=queries, positive=positive, negative=negative, review=False)
    words = re.sub(r'[^\w\s]', ' ', text).split()
    return dict(queries=[' '.join(words[:10]) or 'người cao tuổi dưỡng sinh'], positive=['senior','elderly'], negative=['baby','ballet'], review=True)

REAL_NEGATIVE=['animation','animated','cartoon','illustration','3d','render','cgi','graphic','neon','rainbow','question mark','skeleton','anatomy','hoạt hình','minh họa','mô phỏng','ballet','baby','child']

def describe(text):
    desc=topic_description(text)
    t=unicodedata.normalize('NFC',str(text)).casefold()
    replacements=[
      ('tắc nghẽn|tắc mạch|ứ đọng|huyết khối|máu|tuần hoàn|tĩnh mạch', ['người cao tuổi xoa bóp chân','bác sĩ khám chân bệnh nhân cao tuổi','senior leg massage'],['leg','calf','massage','doctor','patient']),
      ('tim|trái tim', ['bác sĩ khám tim người cao tuổi','người cao tuổi kiểm tra sức khỏe','doctor senior heart examination'],['doctor','patient','chest','examination']),
      ('thận|nội tạng|gan|dạ dày', ['bác sĩ tư vấn sức khỏe người cao tuổi','người cao tuổi khám sức khỏe','doctor consulting elderly patient'],['doctor','patient','consult','examination']),
      ('bắp chân|cơ bắp|gân gót', ['người cao tuổi giãn cơ bắp chân','xoa bóp bắp chân người thật','senior calf stretch'],['calf','leg','stretch','massage']),
      ('khoa học|nghiên cứu|đại học', ['bác sĩ tư vấn người cao tuổi','bác sĩ nghiên cứu y khoa','doctor medical consultation'],['doctor','research','consult']),
      ('buổi sáng|bình minh', ['người cao tuổi bên cửa sổ buổi sáng','người cao tuổi tập thể dục sáng','senior morning exercise'],['morning','senior','exercise']),
    ]
    for pattern,queries,positive in replacements:
        if any(re.search(r'(?<!\w)'+re.escape(w)+r'(?!\w)',t) for w in pattern.split('|')):
            desc=dict(queries=queries,positive=positive,negative=[],review=False);break
    if desc['review']:
        desc=dict(queries=['người cao tuổi sinh hoạt tại nhà','người cao tuổi chăm sóc sức khỏe','senior healthy lifestyle at home'],positive=['senior','elderly','home'],negative=[],review=True)
    translations={'leg':'chân','calf':'bắp chân','doctor':'bác sĩ','patient':'bệnh nhân','massage':'xoa bóp','stretch':'giãn cơ','exercise':'tập thể dục','heel':'gót chân','breath':'hít thở','sleep':'ngủ','wake':'thức dậy','morning':'buổi sáng','walking':'đi bộ','senior':'cao tuổi','elderly':'cao tuổi','back pain':'đau lưng','tired':'mệt mỏi'}
    desc['positive']=list(dict.fromkeys(desc['positive']+[translations[w] for w in desc['positive'] if w in translations]))
    desc['negative']=[]
    desc['real_people_only']=False
    desc['allow_all_media']=True
    return desc


def split_batches(plan,limit=50):
    """Cut at actual scene boundaries, preserving exact source offsets and final remainder."""
    import copy
    if not 1<=limit<=50:raise ValueError('Mỗi phần tối đa 50 cảnh.')
    scenes=plan['scenes'];parts=[]
    for offset in range(0,len(scenes),limit):
        rows=copy.deepcopy(scenes[offset:offset+limit]);base=rows[0]['start']
        for i,row in enumerate(rows,1):
            row['id']=i;row['start']=round(row['start']-base,3)
        duration=round(rows[-1]['start']+rows[-1]['duration'],3)
        source=round(plan.get('source_start',0)+base,3)
        for row in rows:row['source_start']=round(source+row['start'],3)
        parts.append(dict(scenes=rows,duration=duration,source_start=source,number=len(parts)+1))
    return parts


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
    previous=-1;cleaned=[]
    for index,s in enumerate(segments,1):
        try:s['start'],s['end']=float(s['start']),float(s['end'])
        except (KeyError,TypeError,ValueError):raise ValueError(f'Đoạn lời đọc {index} thiếu mốc thời gian dạng số.') from None
        finite=all(math.isfinite(s[x]) for x in ['start','end'])
        words=s.get('words') or []
        if not isinstance(words,list) or any(not isinstance(w,dict) for w in words):raise ValueError(f'Dữ liệu từ ở đoạn lời đọc {index} không hợp lệ.')
        empty=not str(s.get('text','')).strip() and not any(str(w.get('word',w.get('text',''))).strip() for w in words)
        # Whisper emits empty zero-length markers at pauses. They carry no
        # speech and must neither invalidate the transcript nor move its end.
        if finite and s['start']>=0 and s['end']==s['start'] and empty:continue
        if not finite or s['start']<0 or s['end']<=s['start'] or s['start']<previous-.05:
            raise ValueError(f'Mốc thời gian đoạn lời đọc {index} không hợp lệ hoặc chồng lấn ({s["start"]} → {s["end"]} giây).')
        previous=s['end'];cleaned.append(s)
    if not cleaned: raise ValueError('Không có lời đọc có mốc thời gian.')
    return cleaned

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
        context=text
        if text=='Khoảng nghỉ':
            nearby=next((x['text'] for x in words if x['start']>=a),None)
            context=scenes[-1]['text'] if scenes else (nearby or 'người cao tuổi thư giãn')
        desc=describe(context)
        scenes.append(dict(id=len(scenes)+1,start=round(a-start,3),source_start=round(a,3),duration=round(b-a,3),text=text,**desc))
    return dict(scenes=scenes,duration=round(end-start,3),source_start=start,approximate=approximate)

def repair_tiny_scenes(scenes,completed=()):
    """Borrow only from pending neighbours; preserve IDs, total voice and completed cuts."""
    changed=0
    for i,row in enumerate(scenes):
        if row['id'] in completed or float(row.get('duration',0))>=.1:continue
        if i+1>=len(scenes):continue
        following=scenes[i+1]
        if following['id'] in completed or following.get('kind')=='title':continue
        old=float(row['duration']);borrow=.25-old
        if borrow<=0 or following['duration']-borrow<.25:continue
        row.update(timing_original_duration=old,duration=.25)
        following['start']=round(following['start']+borrow,3)
        following['source_start']=round(following.get('source_start',following['start']-borrow)+borrow,3)
        following['duration']=round(following['duration']-borrow,3);changed+=1
    return changed


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
        if scene.get('manual_queries') or scene.get('keyword_provider'):continue
        text=scene.get('text','');old=legacy_description(text);updated=describe(text)
        if scene.get('queries')==old['queries'] and updated['queries']!=old['queries']:
            scene.update(updated);changed+=1
    return changed
