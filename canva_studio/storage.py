"""Portable storage: application-owned writes stay beside the executable."""
import hashlib,json,os,shutil,sys,tempfile
from pathlib import Path

def application_dir():
    return Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]

def data_dir(app=None,env=None):
    env=os.environ if env is None else env
    return Path(env['SKST_DATA_DIR']).resolve() if env.get('SKST_DATA_DIR') else (Path(app or application_dir())/'Data').resolve()

def configure_runtime(root=None):
    root=Path(root or data_dir()).resolve()
    temporary=root/'Temp';cache=root/'Cache'
    temporary.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    for name in ['TEMP','TMP','TMPDIR']:os.environ[name]=str(temporary)
    tempfile.tempdir=str(temporary)
    for name,sub in [('XDG_CACHE_HOME',''),('TORCH_HOME','torch'),('HF_HOME','huggingface'),('WHISPER_CACHE','whisper'),('PYTHONPYCACHEPREFIX','pycache')]:
        os.environ[name]=str(cache/sub)
    return root

def remap_paths(value,old,new):
    if isinstance(value,dict):return {k:remap_paths(v,old,new) for k,v in value.items()}
    if isinstance(value,list):return [remap_paths(v,old,new) for v in value]
    if isinstance(value,str):
        a=value.replace('\\','/');prefix=str(old).replace('\\','/').rstrip('/')
        if a.casefold().startswith(prefix.casefold()+'/'):return str(new/Path(a[len(prefix)+1:]))
    return value

def migrate_legacy(target,legacy):
    """Import verified files once without overwriting a portable project."""
    target,legacy=Path(target).resolve(),Path(legacy).resolve()
    if target==legacy or not legacy.is_dir() or (target/'.legacy-imported').exists() or any((target/p).exists() for p in ['settings.json','project.json']):return 0
    files=[]
    for p in legacy.rglob('*'):
        rel=p.relative_to(legacy)
        if rel.parts[0] in ['Updates','Temp','Cache']:continue
        if p.is_symlink():raise ValueError('Dữ liệu cũ có liên kết ngoài thư mục; hãy chuyển thủ công.')
        if p.is_file():files.append((p,rel))
    if not files:return 0
    target.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='migration-',dir=target) as work:
        work=Path(work)
        for src,rel in files:
            dst=work/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
            if hashlib.sha256(src.read_bytes()).digest()!=hashlib.sha256(dst.read_bytes()).digest():raise OSError('Chưa sao chép đủ dữ liệu cũ.')
            if rel.as_posix() in ['settings.json','project.json']:
                value=json.loads(dst.read_text(encoding='utf-8-sig'))
                dst.write_text(json.dumps(remap_paths(value,legacy,target),ensure_ascii=False,indent=2),encoding='utf8')
        ordered=sorted(files,key=lambda item:item[1].as_posix() in ['project.json','settings.json'])
        for _,rel in ordered:
            dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True)
            if not dst.exists():os.replace(work/rel,dst)
        (target/'.legacy-imported').write_text('Imported legacy app data; source preserved.\n',encoding='utf8')
    return len(files)
