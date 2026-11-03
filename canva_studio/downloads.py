"""Verify the completed Canva MP4 locally; never open or upload the recording."""
import json,math,os,subprocess
from pathlib import Path

def verify_download(filename,ffmpeg,expected):
    path=Path(filename)
    if not path.is_absolute() or path.suffix.lower()!='.mp4' or not path.is_file() or path.stat().st_size==0:
        raise ValueError('Không thấy tệp MP4 đã tải hoàn tất trên máy.')
    probe=Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')
    try:
        result=subprocess.run([str(probe),'-v','error','-show_entries','stream=codec_type,width,height:format=duration','-of','json',str(path)],capture_output=True,check=True,timeout=15,creationflags=0x08000000 if os.name=='nt' else 0)
        info=json.loads(result.stdout)
        videos=[s for s in info.get('streams',[]) if s.get('codec_type')=='video']
        audio=any(s.get('codec_type')=='audio' for s in info.get('streams',[]))
        duration=float(info.get('format',{}).get('duration',0))
        if not videos or not audio or not math.isfinite(duration) or abs(duration-expected)>.5:raise ValueError('MP4 thiếu hình/âm thanh hoặc thời lượng chưa khớp phần dựng.')
    except (OSError,subprocess.SubprocessError,json.JSONDecodeError,TypeError) as exc:
        raise ValueError('Chưa đọc được tệp MP4 đã tải; chưa đánh dấu hoàn tất.') from exc
    return dict(path=str(path),duration=duration)
