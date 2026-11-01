"""Read only the registration metadata for this product's unpacked companion."""
import json,os
from pathlib import Path

def bundled_extension(install):
    folder=Path(install)/'TienIch_Canva'
    try:version=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))['version']
    except (OSError,ValueError,KeyError):version='chưa có'
    return folder,version

def registered_extensions(local_appdata=None):
    local=Path(local_appdata or os.environ.get('LOCALAPPDATA',Path.home()))
    results=[];seen=set()
    for browser,relative in [('Chrome','Google/Chrome/User Data'),('Cốc Cốc','CocCoc/Browser/User Data'),('Edge','Microsoft/Edge/User Data')]:
        root=local/relative
        for profile in [root/'Default',*root.glob('Profile *')]:
            for name in ['Secure Preferences','Preferences']:
                try:settings=json.loads((profile/name).read_text(encoding='utf8')).get('extensions',{}).get('settings',{})
                except (OSError,ValueError):continue
                for ident,entry in settings.items():
                    manifest=entry.get('manifest',{});path=entry.get('path','');title=str(manifest.get('name',''))
                    if 'SKST' not in title.upper() and 'skst_canva' not in str(path).lower():continue
                    key=(browser,profile.name,ident)
                    if key in seen:continue
                    seen.add(key);results.append(dict(browser=browser,profile=profile.name,id=ident,path=path,version=manifest.get('version'),enabled=entry.get('state',1)==1))
    return results

def companion_status(install,local_appdata=None):
    folder,version=bundled_extension(install)
    registrations=registered_extensions(local_appdata)
    mismatches=[r for r in registrations if r['path'] and Path(r['path']).resolve()!=folder.resolve()]
    return dict(folder=str(folder),version=version,registrations=registrations,mismatches=mismatches)


def update_manifest(install, extension_id, local_appdata=None):
    """Expose only the already verified local bundle; never download executable JS."""
    from .core import VERSION
    folder,version=bundled_extension(install)
    if version!=VERSION:raise ValueError('Gói tiện ích chưa khớp ứng dụng. Bấm Kiểm tra cập nhật trong ứng dụng trước.')
    registrations=[r for r in registered_extensions(local_appdata) if r['id']==extension_id]
    if any(not r['path'] or Path(r['path']).resolve()!=folder.resolve() for r in registrations):
        raise ValueError('Trình duyệt đang dùng thư mục tiện ích khác. Dùng TienIch_Canva cạnh ứng dụng làm thư mục cố định một lần.')
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
    if 'SKST' not in manifest.get('name','') or manifest.get('manifest_version')!=3:raise ValueError('Gói tiện ích không hợp lệ.')
    for name in ['adapter.js','content.js','background.js','popup.html','popup.js','manifest.json']:
        path=folder/name
        if path.is_symlink() or not path.is_file() or path.resolve().parent!=folder.resolve():raise ValueError('Thiếu tệp tiện ích hợp lệ.')
    return manifest
