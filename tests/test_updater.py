import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from canva_studio import updater as u

class ReleaseTests(unittest.TestCase):
    def release(self):
        return dict(tag_name='v0.2.1',draft=False,prerelease=False,assets=[dict(name=u.ASSET_NAME,state='uploaded',browser_download_url=f'https://github.com/{u.REPOSITORY}/releases/download/v0.2.1/{u.ASSET_NAME}',digest='sha256:'+'a'*64,size=123)])
    def test_only_new_complete_stable_release(self):
        r=self.release();self.assertEqual(u.select_release(r,'0.2.0')['version'],'0.2.1')
        self.assertIsNone(u.select_release(r,'0.2.1'));self.assertIsNone(u.select_release(r,'0.3.0'))
        r['draft']=True;self.assertIsNone(u.select_release(r,'0.2.0'))
        r['draft']=False;r['prerelease']=True;self.assertIsNone(u.select_release(r,'0.2.0'))
    def test_checksum_and_repository_required(self):
        for field,value in [('digest',None),('browser_download_url','https://evil.test/update.zip'),('size',0)]:
            r=self.release();r['assets'][0][field]=value
            with self.assertRaises((ValueError,TypeError)):u.select_release(r,'0.2.0')
    def test_archive_paths(self):
        for path in ['../SKST Canva Studio.exe','/SKST Canva Studio.exe','C:/SKST Canva Studio.exe','TienIch_Canva/../../project.json','settings.json','TienIch_Canva/CON.js','./SKST Canva Studio.exe','TienIch_Canva/adapter.js:evil','TienIch_Canva//adapter.js']:
            self.assertFalse(u.allowed_file(path),path)
        self.assertTrue(u.allowed_file(u.EXE_NAME));self.assertTrue(u.allowed_file('TienIch_Canva/adapter.js'))

class InstallTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def archive(self,extra=None):
        zpath=self.root/'update.zip'
        with zipfile.ZipFile(zpath,'w') as z:
            z.writestr(u.EXE_NAME,b'new exe');z.writestr('version.json','{"version":"0.2.1"}')
            for name,data in (extra or {}).items():z.writestr(name,data)
        return zpath,hashlib.sha256(zpath.read_bytes()).hexdigest()
    def test_verified_extract_and_preserve_user_files(self):
        archive,digest=self.archive({'TienIch_Canva/adapter.js':'new script'})
        staged=u.extract_verified(archive,self.root/'staged',digest)
        target=self.root/'installed';target.mkdir();(target/u.EXE_NAME).write_text('old exe')
        (target/'project.json').write_text('private progress');(target/'voice.mp3').write_text('private voice')
        changes=u.install_files(staged,target,self.root/'backup')
        self.assertEqual((target/u.EXE_NAME).read_text(),'new exe')
        self.assertEqual((target/'project.json').read_text(),'private progress');self.assertEqual((target/'voice.mp3').read_text(),'private voice')
        u.rollback(changes);self.assertEqual((target/u.EXE_NAME).read_text(),'old exe');self.assertFalse((target/'TienIch_Canva/adapter.js').exists())
    def test_bad_digest_never_extracts(self):
        archive,_=self.archive()
        with self.assertRaises(ValueError):u.extract_verified(archive,self.root/'staged','0'*64)
        self.assertFalse((self.root/'staged').exists())
    def test_traversal_never_extracts(self):
        archive,digest=self.archive({'../outside.txt':'bad'})
        with self.assertRaises(ValueError):u.extract_verified(archive,self.root/'staged',digest)
        self.assertFalse((self.root/'outside.txt').exists())
    def test_failed_install_rolls_back_previous_replacement(self):
        archive,digest=self.archive();stage=u.extract_verified(archive,self.root/'staged',digest)
        target=self.root/'installed';target.mkdir();(target/u.EXE_NAME).write_text('old exe')
        real=u.os.replace;calls=[]
        def replace(a,b):
            calls.append(str(b))
            if len(calls)==2:raise OSError('simulated disk failure')
            return real(a,b)
        with patch.object(u.os,'replace',side_effect=replace):
            with self.assertRaises(OSError):u.install_files(stage,target,self.root/'backup')
        self.assertEqual((target/u.EXE_NAME).read_text(),'old exe');self.assertFalse((target/'version.json').exists())

if __name__=='__main__':unittest.main()
