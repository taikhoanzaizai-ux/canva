"""Test the packaged EXE with empty portable Data and no external Python on PATH."""
import hashlib,json,os,subprocess,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    folder=ROOT/'work'/'Máy mới có dấu và khoảng trắng';folder.mkdir(parents=True,exist_ok=True)
    audio=folder/'giọng đọc mẫu.wav'
    with urllib.request.urlopen('https://raw.githubusercontent.com/ggml-org/whisper.cpp/v1.8.4/samples/jfk.wav',timeout=45) as response:raw=response.read(2*1024*1024)
    assert hashlib.sha256(raw).hexdigest()=='59dfb9a4acb36fe2a2affc14bacbee2920ff435cb13cc314a08c13f66ba7860e'
    audio.write_bytes(raw)
    data=folder/'Data';env=os.environ.copy();env['SKST_DATA_DIR']=str(data);env['PATH']=str(Path(os.environ['WINDIR'])/'System32');env.pop('PYTHONPATH',None)
    app=ROOT/'build/package/SKST_Canva_Studio/SKST Canva Studio.exe'
    subprocess.run([str(app),'--recognizer-self-test',str(audio)],env=env,cwd=folder,check=True,timeout=240,creationflags=0x08000000)
    report=json.loads((data/'recognizer-check-report.json').read_text(encoding='utf8'))
    assert report['ready'] and report['segments']>0 and not report['python_required']
    assert Path(report['model']).is_relative_to(data) and Path(report['runtime']).is_relative_to(data)
    print('Packaged portable recognizer: verified downloads and transcription without external Python passed.')

if __name__=='__main__':main()
