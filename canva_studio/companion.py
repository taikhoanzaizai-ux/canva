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
                    seen.add(key);results.append(dict(browser=browser,profile=profile.name,id=ident,path=path,version=manifest.get('version')))
    return results

def companion_status(install,local_appdata=None):
    folder,version=bundled_extension(install)
    registrations=registered_extensions(local_appdata)
    mismatches=[r for r in registrations if r['path'] and Path(r['path']).resolve()!=folder.resolve()]
    return dict(folder=str(folder),version=version,registrations=registrations,mismatches=mismatches)
