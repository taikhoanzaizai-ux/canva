"""Script headings, time-preserving title cards, and concrete visual search intent."""
import copy,difflib,re,unicodedata,zipfile
from xml.etree.ElementTree import ParseError
from .core import describe,norm,repair_tiny_scenes

# Ordered rules: specific food/preparation and symptoms beat broad organ terms.
RULES=[
 ('mạch máu|lòng mạch|tuần hoàn|hồng cầu|dòng máu|máu lưu thông',['máu lưu thông trong mạch máu','hồng cầu trong động mạch','blood flow red blood cells artery'],['blood','artery','vessel','circulation','máu','mạch'],[]),
 ('đường ruột|đường duật|ruột|dạ dày|niêm mạc|niềm mạng|hệ vi sinh|hẹp vi sinh|tiêu hóa',['hệ tiêu hóa dạ dày đường ruột','niêm mạc ruột hệ vi sinh','digestive system stomach intestines microbiome'],['stomach','intestine','digestive','gut','microbiome','dạ dày','ruột','tiêu hóa'],[]),
 ('đường huyết|tiểu đường|insulin',['đo đường huyết','máy đo đường huyết','blood glucose test glucometer diabetes'],['glucose','diabetes','glucometer','insulin','blood sugar','đường huyết'],[]),
 ('gan|thải độc gan',['gan trong cơ thể','mô phỏng gan thải độc','liver anatomy detoxification'],['liver','gan'],[]),
 ('thận|kinh thận',['thận trong cơ thể','thận lọc máu','kidney anatomy filtration'],['kidney','renal','thận'],[]),
 ('trái tim|tim mạch|nhịp tim',['tim đập','cấu tạo tim mạch','heart anatomy heartbeat'],['heart','cardiac','tim'],[]),
 ('nước chanh|nước tranh|vỏ tranh|vỏ chanh|vỏ quýt|vỏ quyết|chanh|quýt',['tay vắt chanh pha nước','tay gọt vỏ quýt cam','hands squeezing lemon peeling citrus'],['lemon','lime','citrus','orange','chanh','quýt'],['hands','squeeze','peel','drink','tay','vắt','gọt','uống']),
 ('rau xanh|thực phẩm màu xanh|thực phẩm màu săng|màu xanh vị chua',['người sơ chế rau xanh trong bếp','tay rửa rau xanh làm salad','hands washing green vegetables salad'],['vegetable','greens','salad','rau'],['wash','prepare','eat','rửa','sơ chế','ăn']),
 ('thảo dược|trà thảo mộc',['người pha trà thảo mộc','tay pha trà thảo dược','person preparing herbal tea'],['herbal','tea','herb','trà','thảo dược'],['brew','prepar','drink','pha','uống']),
 ('quý vị thân mến|quý vị và các bạn|kính thưa|chào mừng|thưa quý vị',['bác sĩ nói chuyện trước máy quay','người dẫn chương trình sức khỏe','doctor presenter speaking camera'],['doctor','presenter','host','bác sĩ'],['talk','speak','giới thiệu','nói']),
 ('ô nhiễm|khói bụi|khói bội|không khí bẩn',['người đeo khẩu trang đi ngoài đường ô nhiễm','người đeo khẩu trang giữa xe cộ','person wearing mask city pollution traffic'],['mask','pollution','khẩu trang','ô nhiễm'],['wear','city','traffic','đeo','đường']),
 ('kính chào|xin chào|chương trình|sống khỏe|sống tốt',['người dẫn chương trình sức khỏe','bác sĩ giới thiệu sức khỏe trước máy quay','doctor presenter speaking camera'],['presenter','host','doctor','bác sĩ'],['talk','speak','giới thiệu','nói']),
 ('cánh bướm|cánh bướng|bương bướng|ngồi xếp chân|baddha|konasana|bắt đa',['người tập yoga tư thế cánh bướm','người ngồi giãn cơ hông','butterfly pose baddha konasana'],['butterfly','baddha','bound angle','cánh bướm','seated','sitting'],['yoga','stretch','giãn','ngồi']),
 ('hối hả|hối hạ|bận rộn|áp lực|thách thức',['người trung niên bận rộn làm việc','người làm việc căng thẳng tại bàn','middle aged person busy working desk'],['work','desk','office','làm việc','bàn'],['busy','work','stress','bận','căng thẳng','làm việc']),
 ('đu đủ xanh|đu đủ|papaya',['tay gọt đu đủ xanh','tay cắt đu đủ xanh nấu ăn','hands cutting green papaya'],['papaya','đu đủ'],['hands','cut','peel','prepare','cooking','tay','gọt','cắt','nấu']),
 ('đầy hơi|chướng bụng|đau bụng|tiêu hóa',['người lớn tuổi đầy hơi chướng bụng','người ôm bụng khó tiêu','senior stomach discomfort bloating'],['stomach','abdomen','belly','bụng'],['pain','discomfort','bloating','đau','khó chịu']),
 ('đau khớp|xương khớp|sưng viêm|đầu gối',['người cao tuổi xoa đầu gối đau','bác sĩ khám khớp gối','senior knee pain massage'],['knee','joint','đầu gối','khớp'],['pain','massage','doctor','đau','xoa','bác sĩ']),
 ('đường huyết|tiểu đường',['người cao tuổi đo đường huyết tại nhà','tay dùng máy đo đường huyết','senior checking blood glucose'],['glucose','diabetes','blood sugar','đường huyết'],['test','monitor','checking','đo']),
 ('rửa|sơ chế|cắt miếng|gọt vỏ',['tay rửa rau củ sơ chế','tay gọt cắt rau củ trong bếp','hands washing chopping vegetables'],['vegetable','food','rau','củ'],['wash','cut','peel','chop','rửa','gọt','cắt']),
 ('nồi hầm|hầm|đun|nấu|món ăn',['người nấu ăn tại nhà','tay khuấy nồi canh trên bếp','hands cooking soup pot'],['cooking','soup','pot','nấu','canh','nồi'],['hands','stir','prepare','tay','khuấy']),
 ('ngủ|mất ngủ|giấc ngủ',['người cao tuổi ngủ trên giường','người cao tuổi mất ngủ ban đêm','senior sleeping insomnia in bed'],['sleep','bed','ngủ','giường'],['senior','elderly','cao tuổi']),
 ('gan|thận|lòng mạch|thải độc|thanh lọc|nhiễm độc|nhiễm động|cơ quan|tạng',['bác sĩ tư vấn kết quả khám cho người cao tuổi','người cao tuổi khám sức khỏe','doctor explaining health results to elderly patient'],['doctor','patient','bác sĩ','bệnh nhân'],['explain','consult','examination','tư vấn','khám']),
 ('làn da|lão hóa|da mặt',['phụ nữ lớn tuổi chăm sóc da mặt','người phụ nữ soi gương chăm sóc da','mature woman skincare face mirror'],['skin','face','da','mặt'],['care','mirror','cream','chăm sóc','gương']),
]

def rule_for(text):
    t=unicodedata.normalize('NFC',text).casefold()
    for pattern,queries,subjects,actions in RULES:
        if any(re.search(r'(?<!\w)'+re.escape(w)+r'(?!\w)',t) for w in pattern.split('|')):return queries,subjects,actions
    return None

def sentence_context(scenes,index):
    """Comma cuts are editing boundaries, not separate semantic sentences."""
    left=index
    while left>0 and index-left<8:
        if re.search(r'[.!?…]\s*$',scenes[left-1].get('text','')):break
        left-=1
    right=index
    while right+1<len(scenes) and right-index<8:
        if re.search(r'[.!?…]\s*$',scenes[right].get('text','')):break
        right+=1
    return ' '.join(s.get('text','') for s in scenes[left:right+1])

def refine_queries(scenes,preserve_before=0):
    for i,scene in enumerate(scenes):
        if scene['id']<=preserve_before or scene.get('kind')=='title':continue
        # Respect manually edited query lists; generated fallback is explicitly review=True.
        generated=scene.get('queries')==describe(scene.get('text',''))['queries'] or any(scene.get('queries')==r[1] for r in RULES)
        if scene.get('manual_queries') or (not scene.get('review') and not generated):continue
        direct=rule_for(scene.get('text',''))
        context=scene.get('section_title','')+' '+sentence_context(scenes,i)
        rule=direct or rule_for(context)
        if not rule:
            for nearby in reversed(scenes[max(0,i-6):i]):
                rule=rule_for(nearby.get('text',''))
                if rule:break
        if rule:
            queries,subjects,actions=rule
            scene.update(queries=list(queries),positive=subjects+actions,subjects=subjects,actions=actions,review=False,query_basis='câu lời đọc' if direct else 'mục/câu liền kề',requires_review=False)
        else:
            base=describe(scene.get('text',''))
            # Do not accept an elderly/home match alone as proof of relevance.
            subjects=[w for w in base['positive'] if norm(w) not in {'senior','elderly','home','cao tuoi'}]
            if subjects:scene.update(subjects=subjects,query_basis='chủ đề cụ thể',requires_review=False)
            else:
                phrase=' '.join(scene.get('text','').strip(' ,.!?').split()[:10])
                scene.update(queries=[phrase,' '.join(phrase.split()[:5])],positive=phrase.split(),subjects=[],actions=[],review=False,requires_review=False,query_basis='từ khóa câu lời đọc')
        scene.update(allow_all_media=True,real_people_only=False,negative=[])
    return scenes

def headings(script):
    result=[]
    for line in script.splitlines():
        line=line.strip()
        m=re.match(r'^(?:(?:lợi ích(?: số)?|động tác|bài tập|mục|phần|bước)\s+)?(?P<number>\d{1,2}|[a-zA-Z])[.):]\s+(?P<title>.+)$',line,re.I)
        if m and 2<=len(m['title'].split())<=30 and len(line)<=220:result.append(dict(label=m['number'],title=line,body=m['title']))
    return result

def timed_headings(segments,script):
    candidates=headings(script)
    if not candidates:
        candidates=headings('\n'.join(s.get('text','').strip() for s in segments))
        names=['một','hai','ba','bốn','năm','sáu','bảy','tám','chín','mười']
        expected=1
        for index,segment in enumerate(segments):
            m=re.match(r'^(?:mục\s+|phần\s+)?('+ '|'.join(names)+r')[.,:]\s*(.*)$',segment.get('text','').strip(),re.I)
            if not m:continue
            number=names.index(m[1].lower())+1
            if number!=expected:continue
            title=m[2].strip() or (segments[index+1].get('text','').strip() if index+1<len(segments) else '')
            title=title.split('.')[0].strip()
            if 2<=len(title.split())<=30:
                candidates.append(dict(label=str(number),title=str(number)+'. '+title,body=title));expected+=1
    words=[]
    for s in segments:
        ws=s.get('words') or []
        if ws:words.extend(ws)
        else:
            tokens=s.get('text','').split();step=(s['end']-s['start'])/max(1,len(tokens))
            words.extend(dict(word=t,start=s['start']+i*step,end=s['start']+(i+1)*step) for i,t in enumerate(tokens))
    clean=lambda s:re.sub(r'[^a-z0-9]','',norm(s))
    spoken=[clean(w.get('word',w.get('text',''))) for w in words];cursor=0;found=[]
    for heading in candidates:
        tokens=[clean(t) for t in heading['body'].split()];tokens=[t for t in tokens if t][:14]
        if len(tokens)<2:continue
        best=None
        for i in range(cursor,len(words)-len(tokens)+1):
            window=spoken[i:i+len(tokens)]
            ratio=difflib.SequenceMatcher(None,tokens,window,autojunk=False).ratio()
            names={'1':'mot','2':'hai','3':'ba','4':'bon','5':'nam','6':'sau','7':'bay','8':'tam','9':'chin','10':'muoi'}
            preceding=spoken[max(cursor,i-3):i]
            numbered=heading['label'] in preceding or names.get(heading['label'],'!') in preceding
            confidence=ratio+(.08 if numbered else 0)
            if ratio>=.78 and (best is None or confidence>best[0]):best=(confidence,i)
            if ratio==1 and numbered:break
        if not best:continue
        _,i=best;a=float(words[i]['start']);b=float(words[min(len(words)-1,i+len(tokens)-1)]['end'])
        found.append(dict(**heading,start=a,end=b));cursor=i+len(tokens)
    return found

def add_title_cards(plan,segments,script,timing_offset=0):
    titles=timed_headings(segments,script);source=plan.get('source_start',0);end=plan['duration']
    windows=[]
    for title in titles:
        a=round(title['start']+timing_offset-source,3)
        if not 0<=a<end-.25:continue
        b=round(min(end,a+3.0),3)
        boundaries=[s['start'] for s in plan['scenes']]+[end]
        for boundary in boundaries:
            if abs(a-boundary)<.15:a=boundary
            if abs(b-boundary)<.15:b=boundary
        if windows and a<windows[-1]['end']:continue
        windows.append(dict(start=a,end=b,title=title['title']))
    points={0,end}
    for scene in plan['scenes']:points.update([scene['start'],round(scene['start']+scene['duration'],3)])
    for title in windows:
        points={p for p in points if not title['start']<p<title['end']};points.update([title['start'],title['end']])
    ordered=sorted(round(p,3) for p in points);points=[]
    for point in ordered:
        if points and point-points[-1]<.1:
            if point==round(end,3):points[-1]=point
            continue
        points.append(point)
    rows=[];section=''
    for a,b in zip(points,points[1:]):
        if b-a<.001:continue
        title=next((t for t in windows if t['start']<=a<t['end']),None)
        original=next((s for s in plan['scenes'] if s['start']-.001<=a<s['start']+s['duration']-.001),plan['scenes'][-1])
        row=copy.deepcopy(original)
        if title:
            section=title['title'];row.update(kind='title',title_text=section,text=section,queries=['[Tiêu đề] '+section],review=False)
        row.update(id=len(rows)+1,start=round(a,3),duration=round(b-a,3),source_start=round(source+a,3),section_title=section)
        rows.append(row)
    repair_tiny_scenes(rows)
    plan['scenes']=refine_queries(rows);plan['title_count']=len(windows)
    return plan


def render_titles(plan,ffmpeg,folder,font=None):
    import hashlib,os,subprocess,textwrap
    from pathlib import Path
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    font=Path(font or Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/arialbd.ttf')
    if not font.is_file():raise ValueError('Thiếu phông chữ tạo tiêu đề.')
    escaped_font=font.resolve().as_posix().replace(':',r'\:')
    for scene in plan['scenes']:
        if scene.get('kind')!='title':continue
        title=scene['title_text'];key=hashlib.sha256((title+str(scene['duration'])).encode()).hexdigest()[:16]
        textfile=folder/f'title-{key}.txt';video=folder/(f'SKST_error_{key}.png' if scene.get('still_image') else f'SKST_title_{key}.mp4')
        textfile.write_text('\n'.join(line for paragraph in title.splitlines() for line in textwrap.wrap(paragraph,width=52 if scene.get('error_card') else 38)),encoding='utf8')
        size=48 if scene.get('error_card') else 72
        filters=f"drawtext=fontfile='{escaped_font}':textfile='{textfile.name}':fontsize={size}:fontcolor=white:line_spacing=18:x=(w-text_w)/2:y=(h-text_h)/2,fade=t=in:st=0:d=0.2"
        output=['-frames:v','1'] if scene.get('still_image') else ['-t',str(scene['duration']),'-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p']
        if scene.get('still_image'):filters=filters.split(',fade=')[0]
        subprocess.run([str(ffmpeg),'-v','error','-y','-f','lavfi','-i','color=c=black:s=1920x1080:r=30','-vf',filters,*output,str(video.resolve())],cwd=folder,check=True,capture_output=True,creationflags=0x08000000 if os.name=='nt' else 0)
        scene['title_path']=str(video.resolve())
    return plan


def neighboring_script(voice):
    from pathlib import Path
    candidates=list(Path(voice).parent.glob('*.docx'))
    return candidates[0] if len(candidates)==1 else None


def repair_scene_texts(state):
    """Restore pending captions from the sole neighboring script, never retime scenes."""
    from pathlib import Path
    from .core import read_script,load_transcript,align_script
    source=state.get('original_voice')
    if not source:return 0
    script=neighboring_script(source)
    transcript=Path(state.get('voice','')).parent/'transcript.json'
    if not script or not transcript.is_file():return 0
    try:
        segments,aligned=align_script(load_transcript(transcript),read_script(script))
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile,ParseError):return 0
    if not aligned:return 0
    parts=state.get('parts',[]);offset=parts[0].get('source_start',0) if parts else 0
    pending=str(state.get('phase',{}).get('id',''));changed=0
    words=[w for seg in segments for w in seg.get('words',[])]
    for scene in state.get('scenes',[]):
        if scene['id'] in state.get('done',[]) or str(scene['id'])==pending or scene.get('kind')=='title' or scene.get('manual_queries'):continue
        generated=scene.get('review') or scene.get('query_basis') or scene.get('queries')==describe(scene.get('text',''))['queries']
        if not generated:continue
        a=scene.get('source_start',scene['start']);b=a+scene['duration']
        text=' '.join(w['word'] for w in words if a-.03<=float(w['start'])+offset<b-.001).strip()
        if text and text!=scene.get('text'):
            scene.update(text=text,**describe(text));scene.pop('subjects',None);scene.pop('actions',None);scene['requires_review']=False;changed+=1
    return changed
