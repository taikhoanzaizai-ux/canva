"""Verified portable CPU recognition; no Python installation or voice upload."""
import hashlib,json,os,re,shutil,stat,subprocess,tempfile,urllib.parse,urllib.request,zipfile
from pathlib import Path,PurePosixPath
from .storage import application_dir
from .core import atomic_json

RUNTIME_URL='https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.4/whisper-bin-x64.zip'
RUNTIME_SHA='74f973345cb52ef5ba3ec9e7e7af8e48cc8c71722d1528603b80588a11f82e3e'
MODEL_URL='https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin'
MODEL_SHA='60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe'
FILES={'whisper-cli.exe','whisper.dll','ggml.dll','ggml-base.dll','ggml-cpu.dll'}
VC_FILES=('msvcp140.dll','vcruntime140.dll','vcruntime140_1.dll','vcomp140.dll')
NO_WINDOW=0x08000000 if os.name=='nt' else 0

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,url):
        u=urllib.parse.urlsplit(url)
        if u.scheme!='https' or u.username or u.password or not (u.hostname in {'github.com','release-assets.githubusercontent.com','objects.githubusercontent.com','huggingface.co','cdn-lfs.huggingface.co','cdn-lfs-us-1.hf.co','cas-bridge.xethub.hf.co','us.aws.cdn.hf.co'}):raise ValueError('Nguồn tải bộ nhận diện không hợp lệ.')
        return super().redirect_request(req,fp,code,msg,headers,url)

def download(url,path,sha,maximum,progress=lambda *_:None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_file() and digest(path)==sha:return path
    part=path.with_suffix(path.suffix+'.part');count=0;h=hashlib.sha256()
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'SKST-Portable-Recognizer/0.8'})
        with urllib.request.build_opener(Redirect()).open(req,timeout=45) as response,part.open('wb') as out:
            total=int(response.headers.get('Content-Length',0))
            if total>maximum:raise ValueError('Tệp bộ nhận diện lớn hơn giới hạn.')
            while True:
                block=response.read(256*1024)
                if not block:break
                count+=len(block)
                if count>maximum:raise ValueError('Tệp bộ nhận diện vượt giới hạn.')
                out.write(block);h.update(block);progress(count,total)
        if h.hexdigest()!=sha:raise ValueError('Tệp nhận diện không khớp SHA-256; chưa cài đặt. Hãy thử lại.')
        os.replace(part,path);return path
    finally:
        part.unlink(missing_ok=True)

def extract_runtime(archive,destination):
    if digest(archive)!=RUNTIME_SHA:raise ValueError('Gói nhận diện chưa được xác minh.')
    with zipfile.ZipFile(archive) as z:
        selected={};total=0
        for entry in z.infolist():
            name=entry.filename;p=PurePosixPath(name)
            if '\\' in name or ':' in name or p.is_absolute() or '..' in p.parts or stat.S_ISLNK(entry.external_attr>>16):raise ValueError('Đường dẫn gói nhận diện không an toàn.')
            total+=entry.file_size
            if total>100*1024*1024:raise ValueError('Gói nhận diện giải nén quá lớn.')
            if p.name in FILES:
                if name!='Release/'+p.name or p.name in selected:raise ValueError('Tệp nhận diện trùng/khác thư mục.')
                selected[p.name]=entry
        if set(selected)!=FILES:raise ValueError('Gói nhận diện thiếu thành phần.')
        Path(destination).mkdir(parents=True,exist_ok=True)
        for name,entry in selected.items():
            with z.open(entry) as src,(Path(destination)/name).open('wb') as dst:shutil.copyfileobj(src,dst)

def paths(data):
    folder=Path(data)/'Tools'/'WhisperCpp-v1.8.4'
    return folder/'whisper-cli.exe',Path(data)/'Models'/'ggml-base.bin'

def ensure_recognizer(data,progress=lambda *_:None,runtime_root=None):
    data=Path(data);exe,model=paths(data)
    cache=data/'Downloads'/'Recognizer';temporary=data/'Temp';temporary.mkdir(parents=True,exist_ok=True)
    marker=exe.parent/'verified.json'
    try:
        known=json.loads(marker.read_text(encoding='utf8'))
        ready=bool(known) and all((exe.parent/name).is_file() and digest(exe.parent/name)==sha for name,sha in known.items()) and (FILES|set(VC_FILES)).issubset(known)
    except (OSError,ValueError):ready=False
    if not ready:
        progress('Đang tải bộ nhận diện chạy trên CPU…')
        archive=download(RUNTIME_URL,cache/'whisper.zip',RUNTIME_SHA,10*1024*1024,lambda n,t:progress(f'Tải bộ nhận diện: {n/1048576:.1f}/{t/1048576:.1f} MB'))
        with tempfile.TemporaryDirectory(dir=temporary,prefix='recognizer-') as tmp:
            folder=Path(tmp);extract_runtime(archive,folder)
            root=Path(runtime_root or application_dir()/'_internal')
            for name in VC_FILES:
                source=root/name
                if not source.is_file():raise ValueError('Gói ứng dụng thiếu '+name+'. Tải ZIP Windows đầy đủ bản mới nhất; không tải DLL từ website khác.')
                shutil.copy2(source,folder/name)
            subprocess.run([str(folder/'whisper-cli.exe'),'--help'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True,timeout=20,creationflags=NO_WINDOW)
            exe.parent.mkdir(parents=True,exist_ok=True)
            for file in folder.iterdir():os.replace(file,exe.parent/file.name)
            atomic_json(marker,{file.name:digest(file) for file in exe.parent.iterdir() if file.is_file() and file.name!='verified.json'})
    progress('Đang tải mô hình đa ngôn ngữ (có tiếng Việt), khoảng 148 MB…')
    download(MODEL_URL,model,MODEL_SHA,160*1024*1024,lambda n,t:progress(f'Tải mô hình tiếng Việt: {n/1048576:.1f}/{t/1048576:.1f} MB'))
    progress('Bộ nhận diện đã sẵn sàng. Đang đọc voice trên máy…')
    return exe,model

def command(exe,model,audio,out):
    return [str(exe),'-m',str(model),'-f',str(audio),'-l','vi','-ng','-ojf','-of',str(out)]

def convert_output(source,target):
    raw=json.loads(Path(source).read_text(encoding='utf-8-sig',errors='surrogateescape'));segments=[];last=0
    for row in raw.get('transcription',[]):
        text=row.get('text','').strip();offsets=row.get('offsets',{})
        start=max(last,float(offsets.get('from',0))/1000);end=float(offsets.get('to',0))/1000
        if not text or text.startswith('[_') or end<=start:continue
        text=text.encode('utf8','surrogateescape').decode('utf8','replace')
        groups=[];buffer='';a=start;b=start
        def flush():
            if buffer.strip():groups.append((buffer.encode('utf8','surrogateescape').decode('utf8','replace').strip(),a,b))
        for token in row.get('tokens',[]):
            chunk=token.get('text','')
            if not chunk or chunk.startswith('[_'):continue
            times=token.get('offsets',{})
            if chunk[:1].isspace() and buffer.strip():flush();buffer=''
            if not buffer:a=max(start,float(times.get('from',start*1000))/1000)
            b=min(end,max(a,float(times.get('to',end*1000))/1000));buffer+=chunk
        flush();words=[];at=start
        for word,a,b in groups:
            a=max(at,a);b=min(end,b)
            if b<=a:continue
            words.append(dict(word=word,start=a,end=b));at=b
        segment=dict(start=start,end=end,text=text)
        # Preserve the complete caption if native token timing was incomplete.
        if words and ''.join(w['word'] for w in words)==''.join(text.split()):segment['words']=words
        segments.append(segment);last=end
    if not segments:raise ValueError('Không nhận được lời đọc từ voice. Kiểm tra voice hoặc thử mô hình lớn hơn.')
    atomic_json(target,dict(segments=segments));return segments
