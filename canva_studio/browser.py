"""Launch the installed Chrome with a public Canva UI URL; no browser-profile edits."""
import os,re,shutil,subprocess
from pathlib import Path

CREATE_VIDEO='https://www.canva.com/design?create&type=TADUvCyAV_U&category=tADs1de8MlY&ui=e30'

def chrome_path(env=None):
    env=os.environ if env is None else env
    for root in ['PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA']:
        if env.get(root):
            p=Path(env[root])/'Google/Chrome/Application/chrome.exe'
            if p.is_file():return str(p)
    found=shutil.which('chrome')
    if found:return found
    raise ValueError('Chưa tìm thấy Google Chrome. Cài Chrome và tiện ích SKST một lần trước khi dùng tự dựng.')

def open_chrome(url):
    from .core import valid_canva
    if not valid_canva(url) and not re.fullmatch(re.escape(CREATE_VIDEO)+r'#skst_start=[A-Za-z0-9_-]{24}',url):raise ValueError('Chỉ mở đường dẫn Canva hợp lệ.')
    from .companion import registered_extensions
    profiles=sorted({r['profile'] for r in registered_extensions() if r['browser']=='Chrome' and r.get('enabled',True)})
    if len(profiles)>1:raise ValueError('Có nhiều hồ sơ Chrome cài SKST. Chỉ giữ tiện ích bật trong hồ sơ dùng để dựng rồi thử lại.')
    args=[chrome_path()]
    if profiles:
        if not re.fullmatch(r'Default|Profile [0-9]+',profiles[0]):raise ValueError('Hồ sơ Chrome không hợp lệ.')
        args+=['--profile-directory='+profiles[0]]
    return subprocess.Popen(args+['--new-window',url],creationflags=0x08000000 if os.name=='nt' else 0)
