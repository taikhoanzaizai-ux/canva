"""Prepare licensed public media, or a factual text card, without blocking heartbeat."""
import hashlib,json,threading
from pathlib import Path
from .core import atomic_json
from .editorial import render_titles
from .free_media import prepare_external
from .storage import application_dir

def begin_fallback(engine,scene):
    jobs=getattr(engine,'asset_jobs',None)
    if jobs is None:engine.asset_jobs={};jobs=engine.asset_jobs
    key=hashlib.sha256((str(scene.get('source_start',scene['start']))+scene['text']+str(scene['duration'])).encode()).hexdigest()[:20]
    if scene.get('fallback_path') and Path(scene['fallback_path']).is_file():return dict(done=True)
    if key in jobs:return jobs[key]
    status=jobs[key]=dict(pending=True)
    folder=engine.folder/'Projects'/'Media'/key
    try:settings=json.loads((engine.folder/'settings.json').read_text(encoding='utf8'))
    except (OSError,ValueError):settings={}
    ffmpeg=settings.get('ffmpeg') or str(application_dir()/'CongCu/ffmpeg.exe')
    used=list(engine.state.get('used',[]))
    def work():
        try:
            path,source,diagnostics=prepare_external(scene,used,folder,ffmpeg)
            if path is None:
                card=dict(kind='title',title_text=scene['text'],duration=scene['duration'])
                render_titles(dict(scenes=[card]),ffmpeg,folder)
                path=Path(card['title_path']);source=dict(id='designed:'+key,provider='SKST',kind='text_card',title=scene['text'])
            with engine.lock:
                scene.update(fallback_path=str(path),fallback_source=source,fallback_diagnostics=diagnostics)
                status.clear();status['done']=True;engine.save()
        except Exception as exc:
            status.clear();status['error']='Chưa tạo được tư liệu dự phòng: '+str(exc)[:250]
    threading.Thread(target=work,daemon=True).start()
    return status
