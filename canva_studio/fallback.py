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
    key=hashlib.sha256((str(scene.get('source_start',scene['start']))+scene['text']+str(scene['duration'])+str(scene.get('error_card',{}).get('message',''))+'png-v1').encode()).hexdigest()[:20]
    if scene.get('fallback_path') and Path(scene['fallback_path']).is_file() and (not scene.get('error_card') or Path(scene['fallback_path']).suffix=='.png'):return dict(done=True)
    if key in jobs:return jobs[key]
    status=jobs[key]=dict(pending=True)
    folder=engine.folder/'Projects'/'Media'/key
    try:settings=json.loads((engine.folder/'settings.json').read_text(encoding='utf8'))
    except (OSError,ValueError):settings={}
    ffmpeg=settings.get('ffmpeg') or str(application_dir()/'CongCu/ffmpeg.exe')
    used=list(engine.state.get('used',[]))
    def work():
        try:
            error=scene.get('error_card')
            path,source,diagnostics=(None,None,[]) if error else prepare_external(scene,used,folder,ffmpeg)
            if path is None:
                caption=(f"LỖI CẢNH {scene['id']} — {error.get('start',scene['start']):.2f} giây\n{error['message'][:220]}\nLời đọc: {scene['text'][:140]}") if error else scene['text']
                card=dict(kind='title',title_text=caption,duration=scene['duration'],error_card=bool(error),still_image=bool(error))
                render_titles(dict(scenes=[card]),ffmpeg,folder)
                path=Path(card['title_path']);source=dict(id='designed:'+key,provider='SKST',kind='error_card' if error else 'text_card',title=caption)
            with engine.lock:
                scene.update(fallback_path=str(path),fallback_source=source,fallback_diagnostics=diagnostics)
                status.clear();status['done']=True;engine.save()
        except Exception as exc:
            status.clear();status['error']='Chưa tạo được tư liệu dự phòng: '+str(exc)[:250]
    threading.Thread(target=work,daemon=True).start()
    return status
