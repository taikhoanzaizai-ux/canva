import tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit,parse_qs
from canva_studio.bridge import Engine,MIN_EXTENSION_VERSION
from canva_studio.browser import CREATE_VIDEO,open_chrome,chrome_path

class BootstrapTests(unittest.TestCase):
    def plan(self):return dict(scenes=[dict(id=1,start=0,duration=4,text='người cao tuổi',queries=['người cao tuổi'])])
    def test_pairing_persists_only_in_local_data(self):
        with tempfile.TemporaryDirectory() as d:
            a=Engine(d);b=Engine(d);self.assertEqual(a.token,b.token)
            self.assertNotIn(a.token,json.dumps(a.state));self.assertTrue((Path(d)/'pairing.json').is_file())
    def test_only_new_marker_and_blank_editor_can_autostart(self):
        with tempfile.TemporaryDirectory() as d:
            e=Engine(d);address=e.bootstrap(self.plan(),'voice.wav')
            marker=urlsplit(address).fragment
            client=dict(client='A',url='https://www.canva.com/design/new/token/edit',extension_version=MIN_EXTENSION_VERSION,blank_video=True)
            self.assertIsNone(e.next_task(client)['task']);self.assertEqual(e.state['target'],'')
            client['url']+='#'+marker;client['blank_video']=False
            self.assertIsNone(e.next_task(client)['task'])
            client['blank_video']=True;client['extension_version']='0.3.0'
            self.assertIsNone(e.next_task(client)['task'])
            client['extension_version']=MIN_EXTENSION_VERSION
            self.assertEqual(e.next_task(client)['task']['kind'],'voice')
            self.assertEqual(e.state['target'],'https://www.canva.com/design/new/token/edit')
            self.assertEqual(e.state['mode'],'running');self.assertEqual(e.state['bootstrap_nonce'],'')
    def test_second_click_cannot_create_another_design(self):
        with tempfile.TemporaryDirectory() as d:
            e=Engine(d);e.bootstrap(self.plan(),'v')
            with self.assertRaises(ValueError):e.bootstrap(self.plan(),'v')
    def test_missing_extension_times_out_without_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            e=Engine(d);e.bootstrap(self.plan(),'v');e.watchdog(e.state['bootstrap_deadline']+1)
            self.assertEqual(e.state['mode'],'attention');self.assertEqual(e.state['done'],[]);self.assertEqual(e.state['target'],'')
    def test_resume_old_design_without_replacing_progress(self):
        with tempfile.TemporaryDirectory() as d:
            e=Engine(d);target='https://www.canva.com/design/one/token/edit';e.configure(self.plan(),target,'v')
            e.state.update(voice_done=True,done=[],used=['keep']);e.resume_in_chrome()
            self.assertEqual(e.state['mode'],'opening_resume')
            wrong=dict(client='A',url='https://www.canva.com/design/other/token/edit',extension_version=MIN_EXTENSION_VERSION)
            self.assertIsNone(e.next_task(wrong)['task'])
            self.assertEqual(e.next_task({**wrong,'url':target})['task']['id'],'1');self.assertEqual(e.state['used'],['keep'])
    def test_chrome_launch_has_no_shell_and_preserves_profile(self):
        with patch('canva_studio.browser.chrome_path',return_value='chrome.exe'),patch('canva_studio.companion.registered_extensions',return_value=[dict(browser='Chrome',profile='Profile 2')]),patch('canva_studio.browser.subprocess.Popen') as run:
            open_chrome('https://www.canva.com/design/one/token/edit')
            self.assertEqual(run.call_args.args[0],['chrome.exe','--profile-directory=Profile 2','--new-window','https://www.canva.com/design/one/token/edit'])
            with self.assertRaises(ValueError):open_chrome('https://example.com/')
    def test_chrome_ambiguous_profiles_do_not_guess(self):
        with patch('canva_studio.companion.registered_extensions',return_value=[dict(browser='Chrome',profile='Default'),dict(browser='Chrome',profile='Profile 2')]),patch('canva_studio.browser.subprocess.Popen') as run:
            with self.assertRaises(ValueError):open_chrome('https://www.canva.com/design/one/token/edit')
            run.assert_not_called()
