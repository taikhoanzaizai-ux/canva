import json,tempfile,unittest,threading,urllib.request,urllib.error
from pathlib import Path
from canva_studio.core import make_plan,describe,load_transcript,align_script,valid_canva
from canva_studio.bridge import Engine,serve,MIN_EXTENSION_VERSION

class PlannerTests(unittest.TestCase):
    def test_project_titles_use_base_name_then_numbered_parts(self):
        from canva_studio.core import project_title
        self.assertEqual([project_title('Bài 1',i) for i in range(3)],['Bài 1','Bài 1.2','Bài 1.3'])
        self.assertEqual(project_title('Bài 1',9),'Bài 1.10')
        self.assertEqual(project_title('',2),'')
        self.assertEqual(project_title('  Bài   1  ',0),'Bài 1')
        with self.assertRaises(ValueError):project_title('x'*181)
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
        self.assertTrue(describe('từ từ kiễng cao hai gót chân')['allow_all_media'])
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
    def test_missing_stock_does_not_schedule_a_text_card(self):
        self.e.state['voice_done']=True
        self.e.next_task(self.client)
        self.e.result(dict(id='1',client='A',missing_stock='Canva không có kết quả'))
        self.assertEqual(self.e.state['done'],[])
        self.assertNotIn('error_card',self.e.state['scenes'][0])
        self.e.start()
        self.e.next_task(self.client)
        self.e.result(dict(id='1',client='A',asset='lower-stock',fallback_warning='Video thay thế'))
        self.assertEqual(self.e.state['used'],['lower-stock'])
        self.assertNotIn('missing_stock',self.e.state['scenes'][0])
        self.assertEqual(self.e.state['scenes'][0]['fallback_warning'],'Video thay thế')

    def test_manual_final_cut_uses_voice_anchor_and_tolerance(self):
        self.prepare_manual(done=[1])
        self.e.state['scenes'][-1]['voice_end']=8
        self.e.request_manual_review(2)
        task=self.e.next_task(self.client)['task']
        self.assertTrue(task['fit_final'])
        self.assertEqual(task['voice_duration'],8)
        body=self.manual_result(2,2)
        body.update(review_token=task['review_token'],verified_start=4,verified_end=8.09)
        body['frames'][-1]['end']=8.09
        self.e.result(body)
        self.assertEqual(self.e.next_task(self.client)['task']['duration'],8)

    def test_failed_rename_continues_drafting_and_gets_one_final_retry(self):
        self.e.pause();self.e.set_project_name('Bài 1');self.e.start()
        self.assertEqual(self.e.next_task(self.client)['task']['kind'],'rename')
        self.e.result(dict(id='rename',client='A',design_name='Bài 1',rename_warning='Canva chưa nhận tên'))
        self.assertEqual(self.e.state['mode'],'running');self.assertEqual(self.e.state['named_title'],'')
        self.assertEqual(self.e.next_task(self.client)['task']['kind'],'voice')
        self.e.running=None;self.e.state.update(voice_done=True,done=[1],audit_done=True)
        self.assertEqual(self.e.next_task(self.client)['task']['kind'],'rename')
        self.e.result(dict(id='rename',client='A',design_name='Bài 1',rename_warning='Vẫn chưa nhận tên'))
        self.assertEqual(self.e.next_task(self.client)['task']['kind'],'export')
    def test_successful_rename_retry_clears_warning_without_losing_scene_checkpoint(self):
        self.e.pause();self.e.set_project_name('Bài 1');self.e.state['phase']=dict(id='1',stage='inserted');self.e.start()
        self.e.next_task(self.client);self.e.result(dict(id='rename',client='A',design_name='Bài 1',rename_warning='delay'))
        self.e.pause();self.e.state['rename_failed_title']='';self.e.start();self.e.next_task(self.client)
        self.e.result(dict(id='rename',client='A',design_name='Bài 1'))
        self.assertNotIn('rename_warning',self.e.state);self.assertEqual(self.e.state['phase']['stage'],'inserted')
    def manual_result(self,ident=1,count=1):
        return dict(id=f'manual:{ident}',client='A',review_token=self.e.state['manual_review']['token'],manual_verified=True,verified_count=count,verified_start=0,verified_end=4,frames=[dict(start=0,end=4)]+([dict(start=4,end=8)] if count==2 else []),verified_voice_start=0,verified_voice_end=8,voice_name='SKST_voice_test.wav',asset='manual-image')
    def prepare_manual(self,done=None,phase=None):
        self.e.pause();self.e.state.update(voice_done=True,voice_name='SKST_voice_test.wav',done=done or [],phase=phase or {})
        self.e.state['scenes'].append(dict(id=2,start=4,duration=4,text='next',queries=['next']))
        self.e.state['scenes'][0]['error_card']=dict(message='test error')
    def test_manual_repair_finishes_current_scene_and_continues_without_replacing_it(self):
        self.prepare_manual(phase=dict(id='1',stage='inserted'))
        voice=self.e.state['voice'];self.e.request_manual_review(1)
        task=self.e.next_task(self.client)['task'];self.assertEqual(task['kind'],'manual_review')
        self.e.result(self.manual_result())
        self.assertEqual(self.e.state['done'],[1]);self.assertEqual(self.e.state['phase'],{})
        self.assertTrue(self.e.state['scenes'][0]['manual_verified']);self.assertEqual(self.e.state['voice'],voice)
        self.assertEqual(self.e.next_task(self.client)['task']['id'],'2')
    def test_manual_repair_of_completed_scene_preserves_other_scene_checkpoint(self):
        self.prepare_manual(done=[1],phase=dict(id='2',stage='inserted'))
        self.e.request_manual_review(1);task=self.e.next_task(self.client)['task']
        self.assertEqual(task['allowed_counts'],[1,2])
        self.e.result(self.manual_result(count=2))
        self.assertEqual(self.e.state['phase']['id'],'2')
        self.assertEqual(self.e.next_task(self.client)['task']['phase']['stage'],'inserted')
    def test_bad_manual_scene_never_marks_done_or_schedules_error_replacement(self):
        self.prepare_manual();self.e.request_manual_review(1);self.e.next_task(self.client)
        for field,value in [('verified_start',1),('verified_end',7),('verified_count',3),('verified_voice_start',1),('verified_voice_end',7),('voice_name','wrong.wav'),('verified_end',float('nan'))]:
            body=self.manual_result();body[field]=value
            with self.assertRaises(ValueError):self.e.result(body)
        self.e.result(dict(id='manual:1',client='A',review_token=self.e.state['manual_review']['token'],error='Cảnh chưa đúng mốc'))
        self.assertEqual(self.e.state['mode'],'attention');self.assertEqual(self.e.state['done'],[])
        self.assertEqual(self.e.state['manual_review']['scene_id'],1)
        self.assertIn('chưa đúng',self.e.state['manual_review_error'])
    def test_manual_review_survives_restart_and_cannot_skip_gap(self):
        self.prepare_manual()
        with self.assertRaises(ValueError):self.e.request_manual_review(2)
        self.e.request_manual_review(1);restored=Engine(self.tmp.name);restored.start()
        self.assertEqual(restored.next_task(self.client)['task']['kind'],'manual_review')
    def test_repeated_manual_confirmation_rejects_stale_result(self):
        self.prepare_manual();self.e.request_manual_review(1);self.e.next_task(self.client);old=self.manual_result()
        self.e.pause();self.e.request_manual_review(1);self.e.next_task(self.client)
        with self.assertRaises(ValueError):self.e.result(old)
        self.assertEqual(self.e.state['done'],[]);self.assertEqual(self.e.state['mode'],'running')
        self.e.result(self.manual_result());self.assertEqual(self.e.state['done'],[1])
    def test_standard_continue_checks_manual_edit_instead_of_replacing_it(self):
        self.prepare_manual(phase=dict(id='1',stage='inserted'))
        self.e.begin_manual_edit(1);self.assertEqual(self.e.state['mode'],'paused')
        self.e.start();task=self.e.next_task(self.client)['task']
        self.assertEqual(task['kind'],'manual_review');self.assertEqual(self.e.state['phase']['stage'],'inserted')
        self.e.result(self.manual_result());self.assertNotIn('manual_edit_scene',self.e.state)
        self.assertEqual(self.e.next_task(self.client)['task']['id'],'2')
    def test_restarted_review_does_not_reset_another_insert_intent(self):
        self.prepare_manual(done=[1],phase=dict(id='2',stage='insert_intent'))
        self.e.request_manual_review(1);restored=Engine(self.tmp.name);restored.start()
        self.assertEqual(restored.next_task(self.client)['task']['kind'],'manual_review')
        self.assertEqual(restored.state['phase'],dict(id='2',stage='insert_intent'))
    def test_manual_shorter_cut_is_kept_and_next_scene_absorbs_difference(self):
        self.prepare_manual();self.e.request_manual_review(1);self.e.next_task(self.client)
        body=self.manual_result();body.update(verified_end=2,frames=[dict(start=0,end=2)])
        self.e.result(body)
        self.assertEqual(self.e.state['scenes'][0]['duration'],2)
        next_scene=self.e.next_task(self.client)['task']['scene']
        self.assertEqual((next_scene['start'],next_scene['duration']),(2,6))

    def test_name_is_saved_and_rename_preserves_scene_checkpoint(self):
        self.e.pause();self.e.set_project_name('Bài 1')
        self.e.state.update(voice_done=True,phase=dict(id='1',stage='inserted'));self.e.save()
        restored=Engine(self.tmp.name);restored.start()
        task=restored.next_task(self.client)['task']
        self.assertEqual(task['kind'],'rename');self.assertEqual(task['design_name'],'Bài 1')
        restored.result(dict(id='rename',client='A',design_name='Bài 1'))
        self.assertEqual(restored.state['done'],[])
        task=restored.next_task(self.client)['task'];self.assertEqual(task['id'],'1');self.assertEqual(task['phase']['stage'],'inserted')
        restored.pause();again=Engine(self.tmp.name);again.start()
        self.assertEqual(again.next_task(self.client)['task']['id'],'1')

    def test_each_new_part_is_named_from_original_base(self):
        self.e.pause();self.e.set_project_name('Bài 1');self.e.start()
        task=self.e.next_task(self.client)['task'];self.e.result(dict(id='rename',client='A',design_name=task['design_name']))
        self.e.state['parts']=[dict(source_start=0,duration=4)]+[dict(source_start=i*4,duration=4,voice=f'part{i+1}.wav',scenes=[dict(id=1,start=0,duration=4,text='test',queries=['test'])]) for i in (1,2)]
        client=dict(self.client)
        for index in (1,2):
            self.e.state.update(voice_done=True,done=[1],audit_done=True,export_done=True,download_verified={'path':f'part{index}.mp4'})
            self.assertEqual(self.e.next_task(client)['task']['id'],'next_design')
            client['url']=f'https://www.canva.com/design/part{index+1}/token/edit'
            self.e.result(dict(id='next_design',client='A',new_target=client['url']))
            task=self.e.next_task(client)['task']
            self.assertEqual(task['design_name'],f'Bài 1.{index+1}')
            self.e.result(dict(id='rename',client='A',design_name=task['design_name']))
            self.assertEqual(self.e.next_task(client)['task']['kind'],'voice')
            self.e.running=None
        self.assertEqual(self.e.state['project_name'],'Bài 1')

    def test_error_image_endpoint_needs_no_ffmpeg_and_keeps_exact_time(self):
        self.e.state['voice_done']=True;self.e.next_task(self.client)
        self.e.result(dict(id='1',client='A',error='80%: không tìm được tư liệu'))
        self.e.next_task(self.client)
        server=serve(self.e,18767)
        try:
            req=urllib.request.Request('http://127.0.0.1:18767/fallback',data=json.dumps(dict(id='1',client='A')).encode(),headers={'Content-Type':'application/json','X-SKST-Token':self.e.token},method='POST')
            result=json.load(urllib.request.urlopen(req))
            self.assertIn('80%',result['error_text']);self.assertIn('0.00–4.00',result['error_text'])
            self.assertNotIn('pending',result);self.assertTrue(result['name'].endswith('.png'))
        finally:server.shutdown();server.server_close()

    def test_error_scene_moves_on_without_searching_it_again(self):
        self.e.state['scenes'].append(dict(id=2,start=4,duration=5,text='next',queries=['next']))
        self.e.state['voice_done']=True;self.e.next_task(self.client)
        self.e.check(dict(id='1',client='A',stage='muted'))
        self.e.result(dict(id='1',client='A',error='Sai thời lượng'))
        task=self.e.next_task(self.client)['task'];self.assertIn('error_card',task['scene'])
        self.e.result(dict(id='1',client='A',asset='error:1',title='LỖI CẢNH 1'))
        task=self.e.next_task(self.client)['task'];self.assertEqual(task['id'],'2');self.assertEqual(task['scene']['start'],4)
        self.assertEqual(self.e.state['done'],[1]);self.assertEqual(self.e.state['mode'],'running')

    def test_export_requires_finished_download(self):
        self.e.state.update(voice_done=True,done=[1],audit_done=True)
        self.e.next_task(self.client)
        with self.assertRaises(ValueError):self.e.result(dict(id='export',client='A'))
        self.assertFalse(self.e.state['export_done'])
        self.e.result(dict(id='export',client='A',download_complete=True,download_id=9))
        self.assertEqual(self.e.state['mode'],'complete')

    def test_reuse_history_is_soft_and_scoped_to_one_project(self):
        self.e.state.update(voice_done=True,used=['blood'],usage={'blood':2},last_asset='blood')
        task=self.e.next_task(self.client)['task']
        self.assertEqual(task['usage']['blood'],2)
        self.e.result(dict(id='1',client='A',asset='blood',title='Blood cells'))
        self.assertEqual(self.e.state['usage']['blood'],3)
        self.e.pause();self.e.configure(dict(scenes=[dict(id=1,start=0,duration=4,text='blood',queries=['blood'])]),self.client['url'],'new.wav')
        self.assertEqual(self.e.state['usage'],{});self.assertEqual(self.e.state['used'],[])

    def test_scene_error_schedules_visible_card_without_skipping_voice_time(self):
        self.e.state['voice_done']=True;self.e.next_task(self.client)
        response=self.e.result(dict(id='1',client='A',error='Hết thời gian chờ: ô tìm kiếm video (16 giây).'))
        self.assertTrue(response['continuing']);self.assertEqual(self.e.state['mode'],'running')
        self.assertEqual(self.e.state['done'],[])
        task=self.e.next_task(self.client)['task']
        self.assertIn('error_card',task['scene']);self.assertEqual(task['scene']['duration'],4)
        self.assertTrue((Path(self.tmp.name)/'Errors.json').is_file())
        self.e.result(dict(id='1',client='A',title='LỖI CẢNH 1'))
        self.assertEqual(self.e.state['done'],[1])

    def test_verified_card_uses_actual_end_and_starts_next_scene(self):
        self.e.state['scenes'].append(dict(id=2,start=4,duration=4,text='next',queries=['next']))
        self.e.state['voice_done']=True
        self.e.next_task(self.client)
        self.e.check(dict(id='1',client='A',stage='trimmed',media_kind='image',card_kind='error'))
        with self.assertRaises(ValueError):
            self.e.result(dict(id='1',client='A',card_frames=[dict(start=.3,end=4.2)]))
        self.assertEqual(self.e.state['done'],[])
        self.e.result(dict(id='1',client='A',card_frames=[dict(start=0,end=4.2)]))
        self.assertEqual(self.e.state['done'],[1])
        following=self.e.next_task(self.client)['task']['scene']
        self.assertEqual((following['id'],following['start'],following['duration']),(2,4.2,3.8))

    def test_uncertain_insertion_is_never_silently_skipped(self):
        self.e.state['voice_done']=True;self.e.next_task(self.client)
        self.e.check(dict(id='1',client='A',stage='insert_intent'))
        self.e.result(dict(id='1',client='A',error='Chưa chèn được cảnh'))
        self.assertEqual(self.e.state['mode'],'running');self.assertEqual(self.e.state['done'],[])
        self.assertIn('error_card',self.e.state['scenes'][0])
        self.assertEqual(self.e.state['scenes'][0]['error_recovery']['stage'],'insert_intent')

    def test_title_upload_failure_can_be_replaced_before_timeline_insertion(self):
        self.e.state['voice_done']=True;self.e.state['scenes'][0]['kind']='title'
        self.e.next_task(self.client);self.e.check(dict(id='1',client='A',stage='title_uploading',asset='uploaded-title.mp4'))
        result=self.e.result(dict(id='1',client='A',error='Không thấy thẻ Tải lên để chèn cảnh'))
        self.assertTrue(result['continuing']);self.assertEqual(self.e.state['phase'],{})
        self.assertEqual(self.e.state['done'],[]);self.assertTrue(self.e.state['voice_done'])
        self.assertIn('error_card',self.e.next_task(self.client)['task']['scene'])

    def test_verified_rollback_turns_inserted_scene_into_error_card(self):
        self.e.state['voice_done']=True;self.e.next_task(self.client)
        self.e.check(dict(id='1',client='A',stage='inserted'))
        self.e.check(dict(id='1',client='A',stage='rollback_intent',reason='Canva không áp dụng thời lượng'))
        self.e.check(dict(id='1',client='A',stage='rollback_done'))
        result=self.e.result(dict(id='1',client='A',error='Canva không áp dụng thời lượng'))
        self.assertTrue(result['continuing']);self.assertEqual(self.e.state['mode'],'running')
        self.assertEqual(self.e.state['done'],[]);self.assertTrue(self.e.state['voice_done'])
        self.assertIn('error_card',self.e.next_task(self.client)['task']['scene'])

    def test_error_card_failure_is_bounded_and_pause_is_respected(self):
        self.e.state['voice_done']=True;self.e.next_task(self.client)
        self.e.result(dict(id='1',client='A',error='Không thấy ô tìm kiếm'))
        self.e.next_task(self.client);self.e.result(dict(id='1',client='A',error='Không thấy Tải lên'))
        self.assertEqual(self.e.state['mode'],'running')
        for _ in range(2):
            self.e.next_task(self.client);self.e.result(dict(id='1',client='A',error='Canva không phản hồi'))
        self.assertEqual(self.e.state['mode'],'attention');self.assertEqual(len(self.e.state['errors']),4)
        self.e.state['phase']=dict(id='1',stage='inserted')
        self.e.start();self.assertEqual(self.e.state['scenes'][0]['error_card_attempts'],0)
        self.assertEqual(self.e.state['phase']['stage'],'inserted')

    def setUp(self):
        from unittest.mock import patch
        self.download_patch=patch('canva_studio.bridge.verify_download',return_value=dict(path='verified.mp4',duration=4));self.download_patch.start()
        self.addCleanup(self.download_patch.stop)
        self.tmp=tempfile.TemporaryDirectory();self.e=Engine(self.tmp.name)
        self.e.configure(dict(scenes=[dict(id=1,start=0,duration=4,text='test',queries=['test'])]),'https://www.canva.com/design/abc/def/edit','voice.mp3')
        self.client=dict(client='A',url=self.e.state['target'],extension_version=MIN_EXTENSION_VERSION);self.e.start()
    def tearDown(self):self.tmp.cleanup()
    def test_durable_insert_intent_blocks_duplicate(self):
        self.e.state['voice_done']=True;t=self.e.next_task(self.client)['task'];self.e.check(dict(id=t['id'],client='A',stage='insert_intent'))
        resumed=Engine(self.tmp.name)
        resumed.start();task=resumed.next_task(self.client)['task']
        self.assertIn('error_card',task['scene']);self.assertEqual(task['phase'],{})
        self.assertEqual(resumed.state['done'],[])
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
    def test_connection_watchdog_allows_throttled_active_task(self):
        self.e.next_task(self.client)
        last=self.e.last_activity
        self.e.watchdog(now=last+61)
        self.assertEqual(self.e.state['mode'],'running')
        self.e.watchdog(now=last+91)
        self.assertEqual(self.e.state['mode'],'attention')
    def test_wrong_design_is_explained(self):
        self.e.next_task({**self.client,'url':'https://www.canva.com/design/other/design/edit'})
        self.assertEqual(self.e.connection_status()['code'],'wrong_design')
    def test_full_lifecycle(self):
        for id_ in ['voice','1','audit','export']:
            task=self.e.next_task(self.client)['task'];self.assertEqual(task['id'],id_)
            self.e.result(dict(id=id_,client='A',asset='unique' if id_=='1' else None,verified_duration=4,verified_count=1,download_complete=True,download_id=7))
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
        self.assertIn('senior leg massage',describe('tắc nghẽn mạch máu')['queries'])
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


class GeneralKeywordTests(unittest.TestCase):
    def test_substrings_in_unrelated_words_never_match_organs(self):
        from canva_studio.core import describe
        for text in ['thời gian dành cho bản thân','hợp tác chăm sóc sức khỏe','tinh thần thoải mái']:
            result=describe(text)
            self.assertNotIn('blood clot vein',result['queries'])
            self.assertNotIn('mô phỏng nội tạng',result['queries'])
            self.assertNotIn('human kidney',result['queries'])
    def test_generic_migration_repairs_other_false_matches(self):
        from canva_studio.core import legacy_description,repair_pending_keywords,describe
        text='thời gian dành cho bản thân'
        old=legacy_description(text)
        state=dict(scenes=[dict(id=1,text=text,**old)],done=[],phase={})
        self.assertEqual(repair_pending_keywords(state),1)
        self.assertEqual(state['scenes'][0]['queries'],describe(text)['queries'])
        self.assertEqual(repair_pending_keywords(state),0)
    def test_specific_exercise_wins_over_generic(self):
        from canva_studio.core import describe
        self.assertIn('calf raises',describe('động tác nhón gót chân')['queries'])
