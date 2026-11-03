"""Sample-aligned local voice parts, cut only at planned scene boundaries."""
import hashlib,json,os,subprocess
from pathlib import Path
from .core import split_batches,atomic_json

NO_WINDOW=0x08000000 if os.name=='nt' else 0

def probe_duration(ffmpeg,voice):
    probe=Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')
    if not probe.is_file():raise ValueError('Cần FFprobe đi kèm FFmpeg để kiểm tra voice.')
    return float(subprocess.check_output([str(probe),'-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(voice)],timeout=20,creationflags=NO_WINDOW))

def prepare_parts(plan,source,ffmpeg,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    duration=probe_duration(ffmpeg,source)
    parts=split_batches(plan)
    for part in parts:
        start=part['source_start'];end=start+part['duration']
        if start<0 or end>duration+.03:raise ValueError('Danh sách cảnh vượt thời lượng voice gốc. Chọn lại đúng voice gốc.')
        path=folder/f"voice-part-{part['number']:03d}.wav"
        subprocess.run([str(ffmpeg),'-v','error','-y','-i',str(source),'-af',f'atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS','-vn','-ar','48000','-ac','1','-c:a','pcm_s16le',str(path)],check=True,capture_output=True,creationflags=NO_WINDOW)
        actual=probe_duration(ffmpeg,path)
        if abs(actual-part['duration'])>.03:raise ValueError('Đoạn voice sau khi cắt không đủ thời lượng. Chưa bắt đầu dựng.')
        part['voice']=str(path);part['voice_duration']=actual
    atomic_json(folder/'parts.json',dict(source=str(source),source_duration=duration,parts=parts))
    return parts


def cached_transcript(projects,clip):
    """Reuse recognition only when the decoded WAV bytes are identical."""
    from .core import load_transcript
    projects=Path(projects).resolve();clip=Path(clip).resolve()
    def digest(path):
        with path.open('rb') as f:return hashlib.file_digest(f,'sha256').digest()
    expected=None
    for output in sorted(projects.glob('*/transcript.json'),key=lambda p:p.stat().st_mtime,reverse=True):
        candidate=output.with_name('recognition.wav')
        try:
            if candidate.resolve()==clip or not candidate.resolve().is_relative_to(projects) or not output.resolve().is_relative_to(projects):continue
            if candidate.stat().st_size!=clip.stat().st_size:continue
            if expected is None:expected=digest(clip)
            if digest(candidate)!=expected:continue
            load_transcript(output)
            return output
        except (OSError,ValueError,KeyError,TypeError):continue
    return None
