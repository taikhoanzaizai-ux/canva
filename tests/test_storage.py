import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from canva_studio.storage import data_dir,configure_runtime,migrate_legacy

class StorageTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_portable_default_ignores_appdata(self):
        install=self.root/'another-drive/app'
        self.assertEqual(data_dir(install,{'LOCALAPPDATA':'C:/old'}),install.resolve()/'Data')
    def test_all_temp_cache_paths_under_portable_root(self):
        target=self.root/'install/Data';old=tempfile.tempdir
        try:
            with patch.dict(os.environ,{},clear=False):
                configure_runtime(target)
                for key in ['TEMP','TMP','TMPDIR','XDG_CACHE_HOME','TORCH_HOME','HF_HOME','WHISPER_CACHE','PYTHONPYCACHEPREFIX']:
                    self.assertTrue(Path(os.environ[key]).is_relative_to(target))
                self.assertEqual(Path(tempfile.gettempdir()),target/'Temp')
        finally:tempfile.tempdir=old
    def test_migration_verified_media_and_paths_and_keeps_source(self):
        old=self.root/'old';target=self.root/'app/Data';old.mkdir()
        (old/'voice-cut.mp3').write_bytes(b'audio content')
        (old/'project.json').write_text(json.dumps({'voice':str(old/'voice-cut.mp3'),'done':[1,2]}))
        (old/'settings.json').write_text(json.dumps({'voice':str(old/'voice-cut.mp3')}))
        (old/'Updates').mkdir();(old/'Updates/obsolete.zip').write_bytes(b'old')
        self.assertEqual(migrate_legacy(target,old),3)
        self.assertEqual((target/'voice-cut.mp3').read_bytes(),b'audio content')
        self.assertEqual(json.loads((target/'project.json').read_text())['voice'],str(target/'voice-cut.mp3'))
        self.assertTrue((old/'voice-cut.mp3').exists());self.assertFalse((target/'Updates').exists())
        self.assertEqual(migrate_legacy(target,old),0)
    def test_migration_never_overwrites_portable_project(self):
        old=self.root/'old';target=self.root/'app/Data';old.mkdir();target.mkdir(parents=True)
        (old/'project.json').write_text('{"done":[]}');(target/'project.json').write_text('{"done":[9]}')
        self.assertEqual(migrate_legacy(target,old),0)
        self.assertEqual(json.loads((target/'project.json').read_text())['done'],[9])

if __name__=='__main__':unittest.main()
