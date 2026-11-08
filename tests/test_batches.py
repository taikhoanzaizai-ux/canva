import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from canva_studio.core import split_batches,make_plan,describe
from canva_studio.bridge import Engine,MIN_EXTENSION_VERSION
from canva_studio.batches import prepare_parts

class BatchTests(unittest.TestCase):
    def plan(self,count=123):
        return dict(source_start=12.345,scenes=[dict(id=i+1,start=round(i*1.234,3),source_start=round(12.345+i*1.234,3),duration=1.234,text='người cao tuổi đi bộ',**describe('người cao tuổi đi bộ')) for i in range(count)])
    def test_fifty_fifty_remainder_exact_offsets(self):
        plan=self.plan();original=copy.deepcopy(plan);parts=split_batches(plan)
        self.assertEqual([len(p['scenes']) for p in parts],[50,50,23]);self.assertEqual(plan,original)
        for a,b in zip(parts,parts[1:]):self.assertAlmostEqual(a['source_start']+a['duration'],b['source_start'],places=3)
        self.assertAlmostEqual(parts[-1]['source_start']+parts[-1]['duration'],12.345+123*1.234,places=3)
        self.assertTrue(all(p['scenes'][0]['start']==0 and p['scenes'][0]['id']==1 for p in parts))
    def test_source_shorter_than_plan_is_rejected(self):
        with tempfile.TemporaryDirectory() as d,patch('canva_studio.batches.probe_duration',return_value=1):
            with self.assertRaises(ValueError):prepare_parts(self.plan(),'source.wav','ffmpeg',d)
    def test_truncated_output_rejected(self):
        with tempfile.TemporaryDirectory() as d,patch('canva_studio.batches.probe_duration',side_effect=[100,1]),patch('canva_studio.batches.subprocess.run'):
            with self.assertRaises(ValueError):prepare_parts(self.plan(3),'source.wav','ffmpeg',d)
    def test_silence_keeps_contextual_queries(self):
        plan=make_plan([dict(start=2,end=4,text='người cao tuổi đi bộ')],end=12)
        for scene in plan['scenes']:
            self.assertNotIn('Khoảng nghỉ',scene['queries']);self.assertFalse(scene['real_people_only']);self.assertTrue(scene['allow_all_media'])
    def test_anatomical_topics_allow_non_people_media(self):
        for text in ['tuần hoàn máu','trái tim','kinh thận','gân gót chân','bắp chân','Khoảng nghỉ']:
            scene=describe(text)
            self.assertFalse(scene['real_people_only']);self.assertTrue(scene['allow_all_media']);self.assertNotIn('animation',scene['negative'])
            self.assertFalse(any('mô phỏng' in q or 'anatomy' in q or 'blood clot' in q for q in scene['queries']))
    def test_handoff_requires_audit_and_retains_history_used(self):
        with tempfile.TemporaryDirectory() as d:
            engine=Engine(d);parts=split_batches(self.plan(51))
            for p in parts:p['voice']='part.wav'
            engine.configure(dict(**parts[0],parts=parts),'https://www.canva.com/design/one/token/edit','part.wav')
            engine.state.update(done=list(range(1,51)),voice_done=True,used=['never-repeat']);engine.start()
            client=dict(client='A',url=engine.state['target'],extension_version=MIN_EXTENSION_VERSION)
            self.assertEqual(engine.next_task(client)['task']['kind'],'audit')
            with self.assertRaises(ValueError):engine.result(dict(id='audit',client='A',verified_duration=1))
            with self.assertRaises(ValueError):engine.result(dict(id='audit',client='A',verified_duration=parts[0]['duration'],verified_count=49))
            engine.result(dict(id='audit',client='A',verified_duration=parts[0]['duration'],verified_count=50))
            self.assertEqual(engine.next_task(client)['task']['kind'],'export')
            with patch('canva_studio.bridge.verify_download',return_value={'path':'download.mp4'}),patch('canva_studio.bridge.save_part',return_value={'path':'part-1.mp4'}):
                engine.result(dict(id='export',client='A',download_complete=True,download_id=10))
            self.assertEqual(engine.next_task(client)['task']['kind'],'next_design')
            engine.result(dict(id='next_design',client='A',new_target='https://www.canva.com/design/two/token/edit'))
            self.assertEqual(engine.state['part_index'],1);self.assertEqual(engine.state['used'],['never-repeat'])
            self.assertEqual(len(engine.state['history']),1);self.assertEqual(engine.state['done'],[])
            self.assertFalse(engine.state['voice_done']);self.assertIsNone(engine.next_task(client)['task'])
            client.update(url=engine.state['target'])
            self.assertEqual(engine.next_task(client)['task']['kind'],'voice')
            resumed=Engine(d);self.assertEqual(resumed.state['part_index'],1);self.assertEqual(len(resumed.state['history']),1)

    def test_legacy_export_returns_to_missing_history_before_merge(self):
        with tempfile.TemporaryDirectory() as d:
            engine=Engine(d);parts=split_batches(self.plan(51))
            last='https://www.canva.com/design/two/token/edit'
            first='https://www.canva.com/design/one/token/edit'
            engine.configure(dict(**parts[1],parts=parts),last,'part.wav')
            engine.state.update(part_index=1,done=[1],voice_done=True,audit_done=True,history=[{**parts[0],'target':first}])
            engine.start()
            client=dict(client='A',url=last,extension_version=MIN_EXTENSION_VERSION)
            download=dict(id='export',client='A',download_complete=True,download_id=10)
            with patch('canva_studio.bridge.verify_download',return_value={'path':'download.mp4'}),patch('canva_studio.bridge.save_part',side_effect=[{'path':'part-2.mp4'},{'path':'part-1.mp4'}]),patch('canva_studio.bridge.threading.Thread') as worker:
                self.assertEqual(engine.next_task(client)['task']['kind'],'export')
                self.assertEqual(engine.result(download)['export_target'],first)
                self.assertEqual(engine.state['target'],last)
                self.assertIsNone(engine.next_task(client)['task'])
                self.assertEqual(engine.next_task({**client,'url':first})['task']['kind'],'export')
                engine.result({**download,'download_id':11})
                self.assertEqual(engine.state['history'][0]['download_verified']['path'],'part-1.mp4')
                self.assertEqual(engine.state['download_verified']['path'],'part-2.mp4')
                self.assertEqual(engine.state['mode'],'merging')
                worker.return_value.start.assert_called_once()
