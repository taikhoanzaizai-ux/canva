"""Verify the completed Canva MP4 locally; never open or upload the recording."""
import json,math,os,shutil,subprocess
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

def save_part(download,folder,index):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    path=folder/f'Phan_{index+1:03d}.mp4'
    source=Path(download['path'])
    if source.resolve()!=path.resolve():
        staging=path.with_suffix('.part')
        shutil.copyfile(source,staging)
        staging.replace(path)
    return {**download,'path':str(path.resolve())}

def merge_parts(parts,voice,ffmpeg,folder):
    """Join the picture tracks against the original voice clock."""
    folder=Path(folder)
    output=folder/'Video_hoan_chinh.mp4'
    staging=folder/'Video_hoan_chinh.tmp.mp4'
    offset=float(parts[0]['source_start'])
    end=offset
    filters=[]
    inputs=[]
    for i,part in enumerate(parts):
        start,duration=float(part['source_start']),float(part['duration'])
        if not math.isfinite(start) or not math.isfinite(duration) or abs(start-end)>.01 or duration<=0:
            raise ValueError('Các phần voice không nối liền. Chưa thể ghép MP4.')
        path=verify_download(part['download_verified']['path'],ffmpeg,duration)['path']
        inputs.extend(['-i',path])
        frames=round((start+duration-offset)*30)-round((end-offset)*30)
        if frames<1:raise ValueError('Một phần quá ngắn để ghép.')
        filters.append(f'[{i}:v]fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,tpad=stop_mode=clone:stop_duration=0.6,trim=end_frame={frames},setpts=PTS-STARTPTS[v{i}]')
        end=start+duration
    duration=end-offset
    filters.append(''.join(f'[v{i}]' for i in range(len(parts)))+f'concat=n={len(parts)}:v=1:a=0[v]')
    filters.append(f'[{len(parts)}:a]atrim=start={offset:.6f}:duration={duration:.6f},asetpts=PTS-STARTPTS[a]')
    try:
        subprocess.run([str(ffmpeg),'-v','error','-y',*inputs,'-i',str(voice),'-filter_complex_threads','1',
                        '-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast',
                        '-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(staging)],
                       capture_output=True,check=True,timeout=max(300,duration*5),creationflags=0x08000000 if os.name=='nt' else 0)
        verify_download(str(staging.resolve()),ffmpeg,duration)
        staging.replace(output)
    except (OSError,subprocess.SubprocessError) as exc:
        raise ValueError('FFmpeg chưa ghép xong MP4. Các phần đã tải được giữ lại.') from exc
    finally:
        staging.unlink(missing_ok=True)
    return str(output.resolve())
