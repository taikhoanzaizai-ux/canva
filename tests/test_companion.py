import json,tempfile,unittest
from pathlib import Path
from canva_studio.companion import companion_status

class CompanionTests(unittest.TestCase):
    def test_detect_old_registered_folder_without_modifying_browser(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);install=root/'portable';ext=install/'TienIch_Canva';ext.mkdir(parents=True)
            (ext/'manifest.json').write_text('{"version":"0.2.4"}')
            profile=root/'profiledata/Google/Chrome/User Data/Default';profile.mkdir(parents=True)
            config=profile/'Secure Preferences'
            old=str(root/'old/SKST_Canva_Studio/TienIch_Canva')
            config.write_text(json.dumps({'extensions':{'settings':{'own':{'path':old},'unrelated':{'path':'another extension','manifest':{'name':'Unrelated'}}}}}))
            original=config.read_bytes();info=companion_status(install,root/'profiledata')
            self.assertEqual(info['version'],'0.2.4');self.assertEqual(len(info['mismatches']),1)
            self.assertEqual(info['mismatches'][0]['path'],old);self.assertEqual(config.read_bytes(),original)
    def test_correct_folder_needs_no_registration_change(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ext=root/'SKST_Canva_Studio/TienIch_Canva';ext.mkdir(parents=True)
            (ext/'manifest.json').write_text('{"version":"0.2.4"}')
            profile=root/'local/Google/Chrome/User Data/Default';profile.mkdir(parents=True)
            (profile/'Preferences').write_text(json.dumps({'extensions':{'settings':{'own':{'path':str(ext)}}}}))
            self.assertFalse(companion_status(ext.parent,root/'local')['mismatches'])

if __name__=='__main__':unittest.main()
