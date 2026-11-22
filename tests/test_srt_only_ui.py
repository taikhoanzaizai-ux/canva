"""Exercise the app entry points without requiring a Windows display or audio tools."""
import ast
import queue
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from canva_studio.core import load_transcript,make_keyword_plan,split_batches


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
        methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('analyze','choose_transcript','run','tick')]
        self.dialog=SimpleNamespace(showinfo=Mock(),showerror=Mock())
        self.thread=Mock()
        self.probe=Mock(return_value=369)
        self.env=dict(Path=Path,load_transcript=load_transcript,make_keyword_plan=make_keyword_plan,
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
            tasks=queue.Queue(),analyze_worker=Mock(),project_name=Value(),save_project_name=Mock(),
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

    def test_valid_voice_enters_existing_audio_worker(self):
        audio=Path(self.tmp.name)/'voice.wav';audio.touch()
        tool=Path(self.tmp.name)/'ffmpeg.exe';tool.touch()
        self.app.voice.set(str(audio));self.app.ffmpeg.set(str(tool))
        self.app.analyze()
        self.probe.assert_called_once()
        self.thread.assert_called_once()
        inputs=self.thread.call_args.kwargs['args'][0]
        self.assertEqual(inputs['voice'],str(audio))
        self.assertEqual(inputs['transcript'],str(self.path))
        self.assertTrue(self.app.tasks.empty())

    def test_start_preview_with_voice_prepares_audio_before_canva(self):
        audio=Path(self.tmp.name)/'voice.wav';audio.touch()
        self.app.voice.set(str(audio))
        self.app.plan={'transcript_only':True}
        self.app.analyze=Mock(side_effect=lambda:setattr(self.app,'worker_busy',True))
        self.env['run'](self.app)
        self.app.analyze.assert_called_once()
        self.assertTrue(self.app.analyze_then_run)
        self.dialog.showerror.assert_not_called()
