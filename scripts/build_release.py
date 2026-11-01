"""Build repeatable Windows ZIPs. No user recordings included in releases."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from canva_studio.core import VERSION
from canva_studio.updater import allowed_file

def build():
    os.chdir(ROOT)
    out=ROOT/'dist';stage=ROOT/'build/package/SKST_Canva_Studio';stage.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--onedir','--windowed','--name','SKST Canva Studio','--distpath',str(out/'exe'),'--workpath',str(ROOT/'build/pyinstaller'),'--specpath',str(ROOT/'build'),'--add-data',str(ROOT/'HUONG_DAN.txt')+';.','--add-data',str(ROOT/'canva_studio/transcribe_worker.py')+';canva_studio',str(ROOT/'launch.py')],check=True)
    shutil.copytree(out/'exe/SKST Canva Studio',stage,dirs_exist_ok=True)
    shutil.copytree(ROOT/'extension',stage/'TienIch_Canva',dirs_exist_ok=True)
    shutil.copy2(ROOT/'HUONG_DAN.txt',stage/'HUONG_DAN.txt')
    (stage/'Mau_DungThu').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'examples/Danh_sach_canh.json',stage/'Mau_DungThu/Danh_sach_canh.json')
    (stage/'version.json').write_text(json.dumps(dict(version=VERSION,layout='onedir',portable=True),indent=2),encoding='utf8')
    if os.environ.get('SKST_FFMPEG_DIR'):
        tools=Path(os.environ['SKST_FFMPEG_DIR']);(stage/'CongCu').mkdir(exist_ok=True)
        for name in ['ffmpeg.exe','ffprobe.exe']:shutil.copy2(tools/'bin'/name,stage/'CongCu'/name)
        licenses=stage/'GiayPhep';licenses.mkdir(exist_ok=True)
        for name in ['LICENSE','README.txt']:
            if (tools/name).exists():shutil.copy2(tools/name,licenses/('FFmpeg-'+name))
    (stage/'GiayPhep').mkdir(exist_ok=True)
    pylicense=Path(sys.base_prefix)/'LICENSE.txt'
    if pylicense.exists():shutil.copy2(pylicense,stage/'GiayPhep/Python.txt')
    tklicense=Path(sys.base_prefix)/'tcl/tk8.6/license.terms'
    if tklicense.exists():shutil.copy2(tklicense,stage/'GiayPhep/Tcl-Tk.txt')
    smoke=stage/'Data';env=os.environ.copy();env.pop('SKST_DATA_DIR',None);env['SKST_PORT']='18778'
    subprocess.run([str(stage/'SKST Canva Studio.exe'),'--self-test'],env=env,check=True,timeout=45)
    report=json.loads((smoke/'self-test.json').read_text(encoding='utf8'))
    assert report['pairing_code_visible'] and report['pairing_copy_ok'] and report['update_button']
    assert Path(report['portable_data']).resolve()==smoke.resolve()
    assert Path(report['portable_temp']).resolve()==(smoke/'Temp').resolve()
    assert not report['runtime_extracts_to_temp']
    releases=[]
    for kind in ['Windows','Update']:
        target=out/f'SKST_Canva_Studio_{kind}.zip'
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(stage.rglob('*')):
                if not p.is_file():continue
                rel=p.relative_to(stage).as_posix()
                if rel.startswith('Data/'):continue
                if kind=='Update' and not (rel in ['SKST Canva Studio.exe','HUONG_DAN.txt','version.json'] or rel.startswith(('TienIch_Canva/','_internal/'))):continue
                if kind=='Update' and not allowed_file(rel):raise ValueError('Unexpected update runtime file: '+rel)
                z.write(p,('SKST_Canva_Studio/' if kind=='Windows' else '')+rel)
        with zipfile.ZipFile(target) as z:assert z.testzip() is None
        releases.append(target)
    (out/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name for p in releases)+'\n',encoding='utf8')
    print('Built version',VERSION)

if __name__=='__main__':build()
