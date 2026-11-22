"""Exercise the app entry points without requiring a Windows display or audio tools."""
import ast
import copy
import os
import queue
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from canva_studio.core import load_transcript,make_keyword_plan,split_batches,make_plan


class Value:
    def __init__(self,value=''):self.value=value
    def get(self,*args):return self.value
    def set(self,value):self.value=value


class SrtOnlyUiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'input.srt'
        self.path.write_text('\n\n'.join(
            f'{i+1}\n00:{i*3//60:02d}:{i*3%60:02d},000 --> 00:{(i+1)*3//60:02d}:{(i+1)*3%60:02d},000\nĐi bộ.\nTừ khóa: đi bộ; thể dục'
            for i in range(123)),encoding='utf-8-sig')
        tree=ast.parse((Path(__file__).parents[1]/'canva_studio/main.py').read_text(encoding='utf8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='App')
        methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('analyze','analyze_worker','choose_transcript','choose_voice','prepare_srt_voice','prepare_srt_voice_worker','run','tick')]
        self.dialog=SimpleNamespace(showinfo=Mock(),showerror=Mock())
        self.thread=Mock()
        self.probe=Mock(return_value=369)
        self.env=dict(Path=Path,copy=copy,load_transcript=load_transcript,make_keyword_plan=make_keyword_plan,
            split_batches=split_batches,messagebox=self.dialog,
            filedialog=SimpleNamespace(askopenfilename=Mock(return_value=str(self.path))),
            neighboring_script=Mock(return_value=None),probe_duration=self.probe,
            threading=SimpleNamespace(Thread=self.thread),project_title=lambda name:name)
        for method in methods:
            exec(compile(ast.Module(body=[method],type_ignores=[]),'main.py','exec'),self.env)
        self.app=SimpleNamespace(worker_busy=False,engine=SimpleNamespace(state={'mode':'ready'},set_project_name=Mock()),
            transcript=Value(str(self.path)),voice=Value(),start=Value('0'),end=Value(),opening=Value('35'),
            ffmpeg=Value('missing-ffmpeg'),python=Value(),model=Value(),script=Value(),
            plan_button=Mock(),notice=Value(),save_settings=Mock(),keyword_config=Mock(side_effect=AssertionError('Unexpected AI')),
            tasks=queue.Queue(),analyze_worker=Mock(),prepare_srt_voice_worker=Mock(),project_name=Value(),save_project_name=Mock(),
            plan=None,analyze_then_run=False)
        self.app.analyze=lambda:self.env['analyze'](self.app)

    def test_choose_srt_populates_plan_without_voice_ai_or_ffmpeg(self):
        self.env['choose_transcript'](self.app)
        kind,(plan,clip)=self.app.tasks.get_nowait()
        self.assertEqual(kind,'plan')
        self.assertTrue(plan['transcript_only'])
        self.assertEqual(clip,'')
        self.assertEqual([len(p['scenes']) for p in plan['parts']],[50,50,23])
        self.assertEqual(plan['parts'][-1]['source_start']+plan['parts'][-1]['duration'],369)
        self.assertEqual(plan['scenes'][0]['queries'],['đi bộ','thể dục'])
        self.probe.assert_not_called()
        self.thread.assert_not_called()
        self.dialog.showerror.assert_not_called()

    def test_srt_preview_uses_selected_range(self):
        self.app.start.set('3');self.app.end.set('9')
        self.app.analyze()
        plan=self.app.tasks.get_nowait()[1][0]
        self.assertEqual(plan['source_start'],3)
        self.assertEqual(plan['duration'],6)

    def test_imported_table_survives_refresh_of_an_old_part(self):
        self.app.analyze()
        self.app.engine.state.update(part_index=2,parts=[{}, {}, {}],scenes=[],done=[],message='old')
        self.app.display_part=2
        for name in ('archive_project','save','watchdog'):
            setattr(self.app.engine,name,Mock())
        self.app.engine.can_defer_final_scene=lambda:False
        self.app.engine.connection_status=lambda:{'message':'ready'}
        self.app.root=Mock()
        self.app.tick=Mock()
        self.app.refresh_scene_status=Mock()
        self.app.populate=Mock()
        self.app.progress={}
        for name in ('target','manual_scene','keyword_notice','keyword_plan_hint','name_hint','status','connection'):
            setattr(self.app,name,Value())
        for name in ('keyword_update_button','next_part_button','name_entry'):
            setattr(self.app,name,Mock())
        self.env['tick'](self.app)
        self.assertTrue(self.app.plan['transcript_only'])
        self.assertEqual(len(self.app.plan['scenes']),50)
        self.assertEqual(len(self.app.plan['parts']),3)
        self.assertEqual(self.app.display_part,0)
        self.assertEqual(self.app.engine.state['part_index'],0)
        self.app.populate.assert_called_once()
        self.assertIn('Tổng 123 cảnh',self.app.notice.get())
        self.assertNotIn('voice đã kiểm tra',self.app.notice.get().lower())

    def test_plain_srt_uses_local_keywords_without_ai_login(self):
        self.path.write_text('1\n00:00:00,000 --> 00:00:03,000\nĐi bộ.\n',encoding='utf8')
        self.app.analyze()
        plan=self.app.tasks.get_nowait()[1][0]
        self.assertTrue(plan['scenes'][0]['queries'])
        self.app.keyword_config.assert_not_called()

    def test_invalid_srt_reports_error_and_leaves_existing_plan(self):
        self.path.write_text('invalid',encoding='utf8')
        self.app.plan={'sentinel':True}
        self.app.analyze()
        self.dialog.showerror.assert_called_once()
        self.assertEqual(self.app.plan,{'sentinel':True})
        self.assertTrue(self.app.tasks.empty())

    def test_srt_import_is_independent_of_selected_voice(self):
        audio=Path(self.tmp.name)/'voice.wav';audio.touch()
        tool=Path(self.tmp.name)/'ffmpeg.exe';tool.touch()
        self.app.voice.set(str(audio));self.app.ffmpeg.set(str(tool))
        self.app.analyze()
        self.probe.assert_not_called()
        self.app.keyword_config.assert_not_called()
        self.env['neighboring_script'].assert_not_called()
        self.thread.assert_not_called()
        plan=self.app.tasks.get_nowait()[1][0]
        self.assertTrue(plan['transcript_only'])
        self.assertEqual(sum(len(p['scenes']) for p in plan['parts']),123)

    def test_plain_srt_with_voice_does_not_require_ai(self):
        self.path.write_text('1\n00:00:00,000 --> 00:00:03,000\nĐi bộ.\n',encoding='utf8')
        audio=Path(self.tmp.name)/'voice.wav';audio.touch()
        tool=Path(self.tmp.name)/'ffmpeg.exe';tool.touch()
        self.app.voice.set(str(audio));self.app.ffmpeg.set(str(tool))
        self.app.analyze()
        self.app.keyword_config.assert_not_called()
        self.probe.assert_not_called()
        self.thread.assert_not_called()
        self.assertEqual(self.app.tasks.get_nowait()[1][0]['duration'],3)

    def test_voice_without_srt_keeps_voice_analysis(self):
        audio=Path(self.tmp.name)/'voice.wav';audio.touch()
        tool=Path(self.tmp.name)/'ffmpeg.exe';tool.touch()
        self.app.voice.set(str(audio));self.app.ffmpeg.set(str(tool));self.app.transcript.set('')
        self.app.keyword_config=Mock(return_value=None)
        self.app.analyze()
        self.app.keyword_config.assert_called_once()
        self.probe.assert_called_once()
        self.assertEqual(self.thread.call_args.kwargs['args'][0]['transcript'],'')

    def test_worker_uses_srt_for_both_plain_and_keyword_cues(self):
        for suffix in ('','\nTừ khóa: quả cam; nước ép cam'):
            with self.subTest(keywords=bool(suffix)):
                self.path.write_text('1\n00:00:00,000 --> 00:00:03,000\nQuả cam.'+suffix+'\n',encoding='utf8')
                def prepare(plan,*args):
                    parts=split_batches(plan)
                    for part in parts:part['voice']='prepared.wav'
                    return parts
                forbidden=Mock(side_effect=AssertionError('SRT must supply content'))
                self.env.update(DATA=Path(self.tmp.name),uuid=uuid,os=os,NO_WINDOW=0,
                    ensure_recognizer=forbidden,cached_transcript=forbidden,align_script=forbidden,
                    subprocess=SimpleNamespace(run=forbidden,Popen=forbidden),make_plan=make_plan,
                    add_title_cards=forbidden,keyword_updates=forbidden,render_titles=Mock(),
                    prepare_parts=Mock(side_effect=prepare))
                c=dict(transcript=str(self.path),voice='voice.wav',ffmpeg='ffmpeg.exe',
                       python='',model='',a=0,b=3,o=35,script='Nội dung voice khác về tim.')
                self.env['analyze_worker'](self.app,c)
                kind,(plan,audio)=self.app.tasks.get_nowait()
                self.assertEqual(kind,'plan')
                self.assertEqual(plan['planning_source'],'srt')
                self.assertEqual(plan['scenes'][0]['text'],'Quả cam.')
                self.assertEqual(audio,'prepared.wav')
                if suffix:self.assertEqual(plan['scenes'][0]['queries'],['quả cam','nước ép cam'])
                forbidden.assert_not_called()

    def test_start_preview_with_voice_prepares_audio_before_canva(self):
        audio=Path(self.tmp.name)/'voice.wav';audio.touch()
        self.app.voice.set(str(audio))
        self.app.plan={'transcript_only':True}
        self.app.prepare_srt_voice=Mock(side_effect=lambda:setattr(self.app,'worker_busy',True))
        self.env['run'](self.app)
        self.app.prepare_srt_voice.assert_called_once()
        self.assertTrue(self.app.analyze_then_run)
        self.dialog.showerror.assert_not_called()

    def test_start_rebuilds_stale_plan_after_srt_selection_changes(self):
        audio=Path(self.tmp.name)/'voice.wav';audio.touch()
        self.app.voice.set(str(audio))
        self.app.plan={'transcript_path':'older.srt'}
        self.app.analyze=Mock(side_effect=lambda:setattr(self.app,'worker_busy',True))
        self.env['run'](self.app)
        self.app.analyze.assert_called_once()
        self.assertTrue(self.app.analyze_then_run)
        self.dialog.showerror.assert_not_called()

    def test_choosing_srt_with_voice_also_loads_it_immediately(self):
        self.app.voice.set('voice.wav')
        self.app.analyze=Mock()
        self.env['choose_transcript'](self.app)
        self.app.analyze.assert_called_once()

    def test_attach_voice_keeps_srt_preview_and_manual_keywords(self):
        self.app.analyze();self.app.worker_busy=False
        self.app.plan=self.app.tasks.get_nowait()[1][0]
        self.app.plan['scenes'][0]['queries']=['từ khóa đã sửa']
        before=self.app.plan
        audio=Path(self.tmp.name)/'voice.wav';audio.touch()
        self.env['filedialog'].askopenfilename.return_value=str(audio)
        self.env['choose_voice'](self.app)
        self.assertIs(self.app.plan,before)
        self.assertEqual(self.app.plan['scenes'][0]['queries'],['từ khóa đã sửa'])

    def test_prepare_audio_uses_all_imported_parts_without_reparsing(self):
        self.app.analyze();self.app.worker_busy=False
        self.app.plan=self.app.tasks.get_nowait()[1][0]
        self.app.plan['scenes'][0]['queries']=['từ khóa đã sửa']
        audio=Path(self.tmp.name)/'voice.wav';audio.touch()
        tool=Path(self.tmp.name)/'ffmpeg.exe';tool.touch()
        self.app.voice.set(str(audio));self.app.ffmpeg.set(str(tool))
        self.env['prepare_srt_voice'](self.app)
        snapshot,voice,ffmpeg=self.thread.call_args.kwargs['args']
        self.assertEqual(len(snapshot['scenes']),123)
        self.assertEqual(snapshot['scenes'][50]['id'],51)
        self.assertEqual(snapshot['scenes'][50]['start'],150)
        self.assertEqual(snapshot['scenes'][0]['queries'],['từ khóa đã sửa'])
        def prepare(plan,*args):
            parts=split_batches(plan)
            for part in parts:part['voice']='prepared.wav'
            return parts
        self.env.update(DATA=Path(self.tmp.name),uuid=uuid,prepare_parts=Mock(side_effect=prepare))
        self.env['load_transcript']=Mock(side_effect=AssertionError('Keep imported scenes'))
        self.env['prepare_srt_voice_worker'](self.app,snapshot,voice,ffmpeg)
        kind,(prepared,clip)=self.app.tasks.get_nowait()
        self.assertEqual(kind,'plan')
        self.assertFalse(prepared['transcript_only'])
        self.assertEqual([len(p['scenes']) for p in prepared['parts']],[50,50,23])
        self.assertEqual(prepared['scenes'][0]['queries'],['từ khóa đã sửa'])
        self.assertEqual(clip,'prepared.wav')
