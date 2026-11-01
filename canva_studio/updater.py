"""GitHub Releases updater. Fixed repository, verified assets, reversible file swap."""
from __future__ import annotations
import ctypes, hashlib, json, os, re, shutil, stat, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path, PurePosixPath

REPOSITORY='taikhoanzaizai-ux/canva'
API=f'https://api.github.com/repos/{REPOSITORY}/releases/latest'
ASSET_NAME='SKST_Canva_Studio_Update.zip'
EXE_NAME='SKST Canva Studio.exe'
MAX_DOWNLOAD=180*1024*1024

def version_tuple(value):
    m=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:-beta)?',str(value))
    if not m:raise ValueError('Số phiên bản GitHub không hợp lệ.')
    return tuple(map(int,m.groups()))

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        parsed=urllib.parse.urlsplit(newurl)
        if parsed.scheme!='https' or parsed.hostname not in {'github.com','api.github.com','release-assets.githubusercontent.com','objects.githubusercontent.com','github-releases.githubusercontent.com'}:
            raise ValueError('Địa chỉ tải cập nhật không thuộc GitHub.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def request(url):
    return urllib.request.build_opener(SafeRedirect()).open(urllib.request.Request(url,headers={'User-Agent':'SKST-Canva-Studio-Updater','Accept':'application/vnd.github+json'}),timeout=35)

def select_release(release,current):
    if release.get('draft') or release.get('prerelease'):return None
    tag=release.get('tag_name','')
    if version_tuple(tag)<=version_tuple(current):return None
    asset=next((a for a in release.get('assets',[]) if a.get('name')==ASSET_NAME and a.get('state')=='uploaded'),None)
    if not asset:raise ValueError('Bản mới đang được đóng gói. Hãy kiểm tra lại sau vài phút.')
    url=asset.get('browser_download_url','')
    expected=f'https://github.com/{REPOSITORY}/releases/download/{tag}/'
    if url!=expected+ASSET_NAME:raise ValueError('Đường dẫn bản cập nhật không hợp lệ.')
    digest=asset.get('digest','')
    if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}',digest):raise ValueError('GitHub chưa cung cấp mã kiểm tra tệp. Chưa thể cập nhật tự động.')
    size=int(asset.get('size',0))
    if not 0<size<=MAX_DOWNLOAD:raise ValueError('Kích thước cập nhật không hợp lệ.')
    return dict(version=tag.lstrip('v'),tag=tag,url=url,sha256=digest[7:].lower(),size=size,notes=str(release.get('body',''))[:6000])

def check_latest(current):
    try:
        with request(API) as response:
            raw=response.read(2*1024*1024+1)
            if len(raw)>2*1024*1024:raise ValueError('Thông tin bản phát hành quá lớn.')
            release=json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code==404:raise ValueError('GitHub chưa có bản phát hành. Mã nguồn đã lưu chưa đồng nghĩa có bản cài mới.') from e
        if e.code==403:raise ValueError('GitHub đang giới hạn số lần kiểm tra. Thử lại sau.') from e
        raise
    return select_release(release,current)

def allowed_file(relative):
    p=PurePosixPath(relative)
    if p.as_posix()!=relative or '\\' in relative or ':' in relative or p.is_absolute() or not p.parts or any(x in ('..','.') or x.endswith(('.', ' ')) for x in p.parts):return False
    if any(re.match(r'(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)',x) for x in p.parts):return False
    if len(p.parts)==1:return p.name in {EXE_NAME,'HUONG_DAN.txt','version.json'}
    if p.parts[0]=='_internal':
        # Runtime files only. Explicitly reject every traversal component before
        # checking the small set of runtime folders and binary names.
        parts=relative.split('/')
        if any(part in ('','..','.') for part in parts) or '\\' in relative or ':' in relative:return False
        if len(parts)==2:
            return p.name in {'base_library.zip','HUONG_DAN.txt','tcl86t.dll','tk86t.dll','ucrtbase.dll'} or bool(re.fullmatch(r'(?:python3\d{1,2}|api-ms-win-[a-z0-9-]+|VCRUNTIME140(?:_1)?|libcrypto[-_a-z0-9]*|libssl[-_a-z0-9]*|libffi[-_a-z0-9]*)\.dll',p.name,re.I)) or bool(re.fullmatch(r'[a-zA-Z0-9_]+\.pyd',p.name))
        if parts[1]=='canva_studio':return relative=='_internal/canva_studio/transcribe_worker.py'
        if parts[1]=='_tcl_data' and len(parts)>3 and parts[2]=='tzdata':
            return all(re.fullmatch(r'[A-Za-z0-9_+.-]+',part) and part not in {'.','..'} for part in parts[3:])
        return parts[1] in {'_tcl_data','_tk_data','tcl8'} and (p.name in {'tclIndex','README'} or p.suffix.lower() in {'.tcl','.tm','.enc','.msg','.txt','.terms','.gif','.png','.xbm','.xpm','.eps'})
    return p.parts[0]=='TienIch_Canva' and len(p.parts)==2 and p.name in {'manifest.json','adapter.js','content.js','background.js','popup.html','popup.js'}

def extract_verified(archive,destination,expected_digest):
    archive=Path(archive);destination=Path(destination).resolve()
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest!=expected_digest:raise ValueError('Tệp cập nhật tải về không khớp mã SHA-256. Chưa thay đổi ứng dụng.')
    with zipfile.ZipFile(archive) as z:
        names=set();total=0
        for entry in z.infolist():
            if entry.is_dir():continue
            if not allowed_file(entry.filename):raise ValueError('Gói cập nhật chứa đường dẫn không được phép.')
            key=entry.filename.casefold()
            if key in names:raise ValueError('Gói cập nhật chứa tệp trùng tên.')
            names.add(key);total+=entry.file_size
            mode=entry.external_attr>>16
            if stat.S_ISLNK(mode) or entry.file_size>MAX_DOWNLOAD or total>250*1024*1024:raise ValueError('Gói cập nhật không hợp lệ.')
        if EXE_NAME.casefold() not in names or 'version.json' not in names:raise ValueError('Gói cập nhật thiếu ứng dụng hoặc phiên bản.')
        destination.mkdir(parents=True,exist_ok=True)
        for entry in z.infolist():
            if entry.is_dir():continue
            target=(destination/entry.filename).resolve()
            if not target.is_relative_to(destination):raise ValueError('Đường dẫn cập nhật vượt thư mục đích.')
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(entry) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
    return destination

def download_update(release,folder,progress=lambda *_:None):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    archive=folder/'update.zip';count=0;h=hashlib.sha256()
    with request(release['url']) as response,archive.open('wb') as out:
        while True:
            block=response.read(256*1024)
            if not block:break
            count+=len(block)
            if count>MAX_DOWNLOAD or count>release['size']:raise ValueError('Tệp tải về lớn hơn thông tin trên GitHub.')
            out.write(block);h.update(block);progress(count,release['size'])
    if count!=release['size'] or h.hexdigest()!=release['sha256']:raise ValueError('Tải cập nhật chưa đầy đủ hoặc mã kiểm tra không khớp.')
    staged=extract_verified(archive,folder/'files',release['sha256'])
    version=json.loads((staged/'version.json').read_text(encoding='utf8'))
    if version.get('version')!=release['version']:raise ValueError('Phiên bản trong gói không khớp GitHub.')
    return staged

def install_files(staged,target,backup):
    """Atomic individual replacements, rollback all earlier changes on any failure."""
    staged,target,backup=map(lambda p:Path(p).resolve(),(staged,target,backup))
    files=[p for p in staged.rglob('*') if p.is_file()];changes=[]
    if not files or not (staged/EXE_NAME).is_file():raise ValueError('Không có file ứng dụng để cập nhật.')
    for p in files:
        if not allowed_file(p.relative_to(staged).as_posix()):raise ValueError('Tệp cập nhật không hợp lệ.')
    try:
        for src in files:
            relative=src.relative_to(staged);dst=(target/relative).resolve()
            if not dst.is_relative_to(target):raise ValueError('Đường dẫn đích vượt thư mục ứng dụng.')
            if relative.parts[0]=='_internal' and not dst.is_relative_to((target/'_internal').resolve()):raise ValueError('Đường dẫn thư viện vượt thư mục _internal.')
            dst.parent.mkdir(parents=True,exist_ok=True)
            saved=backup/relative;existed=dst.exists()
            if existed:saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,saved)
            temp=dst.with_name(dst.name+'.skst-new');shutil.copy2(src,temp)
            try:
                deadline=time.time()+10
                while True:
                    try:os.replace(temp,dst);break
                    except PermissionError:
                        if time.time()>=deadline:raise
                        time.sleep(.3)
            finally:
                if temp.exists():temp.unlink()
            changes.append((dst,saved,existed))
    except Exception:
        rollback(changes);raise
    return changes

def rollback(changes):
    for dst,saved,existed in reversed(changes):
        if existed:shutil.copy2(saved,dst)
        elif dst.exists():dst.unlink()

def launch_installer(staged,data_dir,version):
    if not getattr(sys,'frozen',False):raise ValueError('Chức năng cài cập nhật dùng trong bản EXE Windows.')
    folder=Path(staged).parent;helper=folder/'SKST Update Helper.exe'
    shutil.copy2(sys.executable,helper)
    support=Path(sys.executable).parent/'_internal'
    if support.is_dir():shutil.copytree(support,folder/'_internal',dirs_exist_ok=True)
    info=dict(parent_pid=os.getpid(),staged=str(Path(staged).resolve()),target=str(Path(sys.executable).parent),backup=str(folder/'backup'),data_dir=str(data_dir),version=version,health=str(folder/'health.json'))
    manifest=folder/'install.json';manifest.write_text(json.dumps(info),encoding='utf8')
    env=os.environ.copy();env['SKST_DATA_DIR']=str(data_dir);env['PYINSTALLER_RESET_ENVIRONMENT']='1'
    subprocess.Popen([str(helper),'--apply-update',str(manifest)],env=env,creationflags=0x08000000,close_fds=True)

def wait_parent(pid):
    if os.name!='nt':raise RuntimeError('Trình cập nhật này dành cho Windows.')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.OpenProcess(0x00100000,False,pid)
    if handle:
        try:
            if kernel.WaitForSingleObject(handle,45000)!=0:raise RuntimeError('Ứng dụng cũ chưa đóng. Chưa áp dụng cập nhật.')
        finally:kernel.CloseHandle(handle)

def apply_manifest(path):
    path=Path(path);info=json.loads(path.read_text(encoding='utf8'));changes=[];proc=None
    try:
        wait_parent(int(info['parent_pid']))
        changes=install_files(info['staged'],info['target'],info['backup'])
        health=Path(info['health']);health.unlink(missing_ok=True)
        env=os.environ.copy();env['SKST_DATA_DIR']=info['data_dir'];env['SKST_UPDATE_HEALTH']=str(health);env['PYINSTALLER_RESET_ENVIRONMENT']='1'
        proc=subprocess.Popen([str(Path(info['target'])/EXE_NAME)],env=env,close_fds=True)
        deadline=time.time()+35
        while time.time()<deadline:
            if health.exists() and json.loads(health.read_text()).get('version')==info['version']:
                (path.parent/'result.txt').write_text('Đã cập nhật thành công '+info['version'],encoding='utf8');return 0
            if proc.poll() is not None:break
            time.sleep(.4)
        raise RuntimeError('Bản mới chưa khởi động thành công. Đã phục hồi bản trước.')
    except Exception as e:
        if proc and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:pass
        if changes:rollback(changes)
        (path.parent/'result.txt').write_text(str(e),encoding='utf8')
        if changes:
            env=os.environ.copy();env['PYINSTALLER_RESET_ENVIRONMENT']='1'
            subprocess.Popen([str(Path(info['target'])/EXE_NAME)],env=env,close_fds=True)
        return 1
