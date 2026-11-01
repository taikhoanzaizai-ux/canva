import json,tempfile,unittest,threading,urllib.request,urllib.error
from pathlib import Path
from canva_studio.core import make_plan,describe,load_transcript,align_script,valid_canva
from canva_studio.bridge import Engine,serve,MIN_EXTENSION_VERSION

class PlannerTests(unittest.TestCase):
    def test_continuous_and_max_duration(self):
        words=[dict(word=t,start=i*.43,end=(i+1)*.43) for i,t in enumerate(('Sáng thức dậy, chân nặng trĩu, thắt lưng ê ẩm, đầu óc lờ đờ. '*20).split())]
        result=make_plan([dict(start=0,end=words[-1]['end'],words=words)],end=100)
        at=0
        for s in result['scenes']:
            self.assertAlmostEqual(at,s['start'],places=2);self.assertLessEqual(s['duration'],5.001);self.assertGreater(s['duration'],0);at+=s['duration']
        self.assertAlmostEqual(at,100,places=2)
        self.assertIn('thức dậy',result['scenes'][0]['queries'][0])
    def test_timestamp_silence_and_srt(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'t.srt';p.write_text('1\n00:00:04,000 --> 00:00:07,000\nThở ra nhẹ nhàng.\n',encoding='utf8')
            plan=make_plan(load_transcript(p),end=13)
            self.assertTrue(plan['approximate']);self.assertAlmostEqual(sum(s['duration'] for s in plan['scenes']),13,places=3)
            self.assertLessEqual(max(s['duration'] for s in plan['scenes']),5)
    def test_invalid_transcript(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'t.json';p.write_text('[{"start":2,"end":1}]')
            with self.assertRaises(ValueError):load_transcript(p)
    def test_topics_and_negative(self):
        self.assertIn('ballet',describe('từ từ kiễng cao hai gót chân')['negative'])
        self.assertIn('đau lưng',describe('thắt lưng ê ẩm')['queries'][0])
    def test_script_alignment_weak_rejected(self):
        seg=[dict(start=0,end=10,words=[dict(word='xin',start=i,end=i+1) for i in range(10)])]
        _,ok=align_script(seg,'một kịch bản hoàn toàn khác nội dung')
        self.assertFalse(ok)
    def test_script_alignment_keeps_times(self):
        tokens='Sáng thức dậy chân nặng trĩu thắt lưng ê ẩm đầu óc lờ đờ'.split()
        seg=[dict(start=0,end=len(tokens),words=[dict(word=t,start=i,end=i+1) for i,t in enumerate(tokens)])]
        out,ok=align_script(seg,'Sáng thức dậy, chân nặng trĩu, thắt lưng ê ẩm, đầu óc lờ đờ.')
        self.assertTrue(ok);self.assertEqual(out[0]['words'][0]['start'],0);self.assertEqual(out[0]['words'][-1]['end'],len(tokens))
    def test_url_allowlist(self):
        self.assertTrue(valid_canva('https://www.canva.com/design/abc/def/edit'))
        self.assertFalse(valid_canva('https://www.canva.com.evil/design/abc/def/edit'))

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.e=Engine(self.tmp.name)
        self.e.configure(dict(scenes=[dict(id=1,start=0,duration=4,text='test',queries=['test'])]),'https://www.canva.com/design/abc/def/edit','voice.mp3')
        self.client=dict(client='A',url=self.e.state['target'],extension_version=MIN_EXTENSION_VERSION);self.e.start()
    def tearDown(self):self.tmp.cleanup()
    def test_durable_insert_intent_blocks_duplicate(self):
        self.e.state['voice_done']=True;t=self.e.next_task(self.client)['task'];self.e.check(dict(id=t['id'],client='A',stage='insert_intent'))
        resumed=Engine(self.tmp.name)
        with self.assertRaises(ValueError):resumed.start()
        resumed.recover('inserted');resumed.start();self.assertEqual(resumed.next_task(self.client)['task']['phase']['stage'],'inserted')
    def test_only_target_and_single_client(self):
        self.assertIsNone(self.e.next_task(dict(client='X',url='https://wrong.test'))['task'])
        self.assertEqual(self.e.next_task(self.client)['task']['kind'],'voice')
        self.assertIsNone(self.e.next_task({**self.client,'client':'B'})['task'])
    def test_old_extension_cannot_start_mutation(self):
        old={k:v for k,v in self.client.items() if k!='extension_version'}
        response=self.e.next_task(old)
        self.assertEqual(response['mode'],'extension_outdated');self.assertIsNone(response['task']);self.assertIsNone(self.e.running)
        self.assertIn(MIN_EXTENSION_VERSION,self.e.state['message'])
    def test_heartbeat_before_project_target_is_configured(self):
        target=self.e.state['target'];self.e.state['target']=''
        self.e.next_task(self.client)
        self.assertTrue(self.e.connection_status(target)['ready'])
    def test_old_controller_cannot_lock_out_new_controller(self):
        self.e.next_task({**self.client,'client':'old','extension_version':'0.2.2'})
        self.assertEqual(self.e.next_task(self.client)['task']['kind'],'voice')
    def test_connection_watchdog_preserves_progress(self):
        self.e.state['done']=[1];self.e.watchdog(now=self.e.last_activity+26)
        self.assertEqual(self.e.state['mode'],'attention');self.assertEqual(self.e.state['done'],[1])
    def test_wrong_design_is_explained(self):
        self.e.next_task({**self.client,'url':'https://www.canva.com/design/other/design/edit'})
        self.assertEqual(self.e.connection_status()['code'],'wrong_design')
    def test_full_lifecycle(self):
        for id_ in ['voice','1','export']:
            task=self.e.next_task(self.client)['task'];self.assertEqual(task['id'],id_)
            self.e.result(dict(id=id_,client='A',asset='unique' if id_=='1' else None))
        self.assertEqual(self.e.state['mode'],'complete');self.assertEqual(self.e.state['used'],['unique'])
    def test_resume_after_two_completed_scenes_keeps_voice(self):
        self.e.state.update(scenes=[dict(id=1,start=0,duration=2.76),dict(id=2,start=2.76,duration=3.98),dict(id=3,start=6.74,duration=4.84)],done=[1,2],voice_done=True,mode='attention',phase={})
        self.e.start();task=self.e.next_task(self.client)['task']
        self.assertEqual(task['id'],'3');self.assertEqual(task['scene']['start'],6.74)
        self.assertEqual(self.e.state['done'],[1,2]);self.assertTrue(self.e.state['voice_done'])
    def test_paused_checkpoint_denies_click(self):
        self.e.next_task(self.client);self.e.pause()
        self.assertFalse(self.e.check(dict(id='voice',client='A'))['continue_'])
    def test_auth_and_loopback(self):
        server=serve(self.e,18766)
        try:
            req=urllib.request.Request('http://127.0.0.1:18766/ping',data=b'{}',headers={'Content-Type':'application/json'},method='POST')
            with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(req)
            req.add_header('X-SKST-Token',self.e.token)
            self.assertTrue(json.load(urllib.request.urlopen(req))['ok'])
        finally:server.shutdown();server.server_close()
    def test_voice_upload_uses_unique_content_identity(self):
        import hashlib
        audio=Path(self.tmp.name)/'voice-cut.mp3';audio.write_bytes(b'first voice')
        self.e.state['voice']=str(audio);self.e.next_task(self.client)
        server=serve(self.e,18767)
        try:
            def fetch_voice():
                req=urllib.request.Request('http://127.0.0.1:18767/voice',data=json.dumps(dict(id='voice',client='A')).encode(),headers={'Content-Type':'application/json','X-SKST-Token':self.e.token},method='POST')
                return json.load(urllib.request.urlopen(req))
            a=fetch_voice();self.assertEqual(a['name'],'SKST_voice_'+hashlib.sha256(b'first voice').hexdigest()[:16]+'.mp3')
            audio.write_bytes(b'different voice');b=fetch_voice()
            self.assertNotEqual(a['name'],b['name']);self.assertEqual(b['mime'],'audio/mpeg')
        finally:server.shutdown();server.server_close()

if __name__=='__main__':unittest.main()


class KeywordRepairTests(unittest.TestCase):
    def test_exercise_is_not_clot(self):
        from canva_studio.core import describe
        for text in ['Ở cuối video là bộ 6 động tác đơn giản, tập ngay tại nhà,','không cần dụng cụ. Đặc biệt có một động tác chỉ mất 20 giây mỗi lần,']:
            self.assertIn('senior home exercise',describe(text)['queries'])
        self.assertIn('blood clot vein',describe('tắc nghẽn mạch máu')['queries'])
        self.assertNotIn('blood clot vein',describe('hợp tác chăm sóc sức khỏe')['queries'])
    def test_repair_preserves_done_custom_and_inflight(self):
        from canva_studio.core import repair_pending_keywords
        old=['tắc nghẽn mạch máu','huyết khối tĩnh mạch','blood clot vein']
        scenes=[dict(id=i,text='động tác tập tại nhà',queries=list(old)) for i in range(1,5)]
        scenes[3]['queries']=['từ khóa tự chọn']
        state=dict(scenes=scenes,done=[1],phase={'id':'3','stage':'inserted'})
        self.assertEqual(repair_pending_keywords(state),1)
        self.assertEqual(scenes[0]['queries'],old)
        self.assertEqual(scenes[2]['queries'],old)
        self.assertEqual(scenes[3]['queries'],['từ khóa tự chọn'])
        self.assertIn('senior home exercise',scenes[1]['queries'])
