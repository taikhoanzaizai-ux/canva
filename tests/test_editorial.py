import copy,unittest
from canva_studio.core import make_plan,describe,split_batches
from canva_studio.editorial import headings,timed_headings,add_title_cards,refine_queries

class EditorialTests(unittest.TestCase):
    def test_cards_render_percent_and_expressions_as_literal_text(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from canva_studio.editorial import render_titles
        with tempfile.TemporaryDirectory() as folder:
            font=Path(folder)/'font.ttf';font.touch()
            for still in (False,True):
                scene=dict(kind='title',title_text='80% dây thần kinh — %{n} 100% đúng',duration=4.81,still_image=still,error_card=still)
                with patch('subprocess.run') as run:
                    render_titles({'scenes':[scene]},'ffmpeg',folder,font)
                args=run.call_args.args[0]
                self.assertIn(':expansion=none:',args[args.index('-vf')+1])
                self.assertEqual(run.call_args.kwargs['timeout'],120)
                self.assertIn('80%',next(Path(folder).glob('title-*.txt')).read_text(encoding='utf8'))

    def test_card_failure_reports_stderr_instead_of_command(self):
        import tempfile,subprocess
        from pathlib import Path
        from unittest.mock import patch
        from canva_studio.editorial import render_titles
        with tempfile.TemporaryDirectory() as folder:
            font=Path(folder)/'font.ttf';font.touch()
            with patch('subprocess.run',side_effect=subprocess.CalledProcessError(22,['private-command'],stderr=b'Stray % near text')):
                with self.assertRaisesRegex(ValueError,'Stray % near text'):
                    render_titles({'scenes':[dict(kind='title',title_text='80%',duration=2)]},'ffmpeg',folder,font)

    def test_near_duplicate_boundaries_never_create_one_millisecond_scene(self):
        plan=dict(duration=9.682,source_start=0,scenes=[dict(id=1,start=0,duration=4.778,text='đường ruột'),dict(id=2,start=4.779,duration=4.903,text='hệ tiêu hóa')])
        result=add_title_cards(plan,[], '')
        self.assertEqual(len(result['scenes']),2)
        self.assertTrue(all(s['duration']>=.1 for s in result['scenes']))
        self.assertAlmostEqual(sum(s['duration'] for s in result['scenes']),9.682,places=3)

    def test_pending_tiny_repair_keeps_ids_completed_scenes_and_total_voice(self):
        from canva_studio.core import repair_tiny_scenes
        rows=[dict(id=25,start=71.627,duration=4.778),dict(id=26,start=76.405,duration=.001),dict(id=27,start=76.406,duration=4.903,source_start=76.406)]
        before=copy.deepcopy(rows[0]);end=rows[-1]['start']+rows[-1]['duration']
        self.assertEqual(repair_tiny_scenes(rows,[25]),1)
        self.assertEqual(rows[0],before);self.assertEqual(rows[1]['id'],26);self.assertEqual(rows[1]['duration'],.25)
        self.assertAlmostEqual(rows[1]['start']+rows[1]['duration'],rows[2]['start'])
        self.assertAlmostEqual(rows[-1]['start']+rows[-1]['duration'],end)
        self.assertEqual(repair_tiny_scenes(rows,[25]),0)

    def test_medical_queries_target_the_object_without_requiring_people(self):
        for text,term in [('Bụ căng tức dù chẳng ăn bao nhiêu','stomach'),('hồng cầu trong mạch máu','blood'),('niêm mạc đường ruột','intestine'),('đo đường huyết','glucose')]:
            rows=[dict(id=1,text=text,**describe(text))];refine_queries(rows)
            self.assertIn(term,rows[0]['subjects']);self.assertTrue(rows[0]['allow_all_media'])
            self.assertEqual(rows[0]['negative'],[]);self.assertFalse(rows[0]['real_people_only'])
    def test_explicit_headings_not_quantities(self):
        result=headings('1. Nhón gót chân\nĂn 2 quả mỗi ngày.\na) Hít thở chậm\n2. Xoa bóp bắp chân')
        self.assertEqual([h['label'] for h in result],['1','a','2'])
    def test_titles_preserve_audio_duration_and_source_offset(self):
        tokens='mở đầu một nhón gót chân rồi tập nhẹ nhàng hai xoa bóp bắp chân cuối bài'.split()
        words=[dict(word=t,start=i,end=i+1) for i,t in enumerate(tokens)]
        segments=[dict(start=0,end=len(words),words=words,text=' '.join(tokens))]
        plan=make_plan(segments,end=len(words));before=plan['duration']
        result=add_title_cards(plan,segments,'1. Nhón gót chân\n2. Xoa bóp bắp chân')
        cards=[s for s in result['scenes'] if s.get('kind')=='title']
        self.assertEqual(len(cards),2);self.assertTrue(all(s['duration']<=3.15 for s in cards))
        self.assertAlmostEqual(sum(s['duration'] for s in result['scenes']),before,places=3)
        for a,b in zip(result['scenes'],result['scenes'][1:]):self.assertAlmostEqual(a['start']+a['duration'],b['start'],places=3)
        self.assertEqual(cards[0]['title_text'],'1. Nhón gót chân')
    def test_spoken_numbered_headings_without_script(self):
        segments=[dict(start=0,end=4,text='Một. Nhón gót chân'),dict(start=4,end=9,text='thực hiện chậm rãi'),dict(start=9,end=13,text='Hai. Xoa bóp bắp chân')]
        self.assertEqual(len(timed_headings(segments,'')),2)
    def test_food_is_specific_not_generic_home(self):
        scene=dict(id=1,text='Gọt vỏ đu đủ xanh rồi cắt miếng nấu canh',**describe('Gọt vỏ đu đủ xanh rồi cắt miếng nấu canh'))
        refine_queries([scene]);self.assertIn('papaya',scene['subjects']);self.assertIn('đu đủ',scene['queries'][0]);self.assertFalse(scene.get('requires_review'))
    def test_symptom_beats_food_context(self):
        scene=dict(id=1,text='đầy hơi và chướng bụng',section_title='Đu đủ xanh',**describe('đầy hơi và chướng bụng'))
        refine_queries([scene]);self.assertIn('stomach',scene['subjects']);self.assertNotIn('papaya',scene['subjects'])
    def test_custom_queries_and_completed_scenes_are_preserved(self):
        old=dict(id=1,text='đu đủ xanh',queries=['tùy chỉnh'],positive=[],review=False)
        rows=[copy.deepcopy(old),dict(id=2,text='đầy hơi',**describe('đầy hơi'))];before=copy.deepcopy(rows[0])
        refine_queries(rows,preserve_before=1);self.assertEqual(rows[0],before);self.assertIn('stomach',rows[1]['subjects'])
    def test_nonzero_source_start_keeps_title_timing(self):
        segments=[dict(start=0,end=4,text='Một. Nhón gót chân')]
        plan=make_plan(segments,end=4);plan['source_start']=100
        add_title_cards(plan,segments,'1. Nhón gót chân',timing_offset=100)
        card=next(s for s in plan['scenes'] if s.get('kind')=='title')
        self.assertGreaterEqual(card['source_start'],100);self.assertLess(card['start'],4)

    def test_named_numbered_benefit_headings(self):
        self.assertEqual([h['label'] for h in headings('LỢI ÍCH SỐ 1. Củng cố sức khỏe\nLỢI ÍCH SỐ 2. Hỗ trợ tiêu hóa')],['1','2'])
    def test_butterfly_topic_carries_into_benefit_sentence(self):
        rows=[dict(id=1,text='bài tập ngồi xếp chân cánh bướng',**describe('bài tập ngồi xếp chân cánh bướng')),dict(id=2,text='đồng tác này được mệnh danh là liều thuốc bổ tự nhiên',**describe('đồng tác này được mệnh danh là liều thuốc bổ tự nhiên'))]
        refine_queries(rows)
        self.assertIn('butterfly',rows[1]['subjects']);self.assertFalse(rows[1].get('requires_review'))

    def test_greeting_and_comma_fragments_do_not_block_first_scene(self):
        texts=['Quý vị thân mến,','mỗi ngày trôi qua,','cơ thể chúng ta phải tiếp xúc với nhiều tác nhân.','Từ không khí ô nhiễm,','khói bụi,','cho đến căng thẳng thần kinh.']
        rows=[dict(id=i+1,text=t,**describe(t)) for i,t in enumerate(texts)]
        refine_queries(rows)
        self.assertTrue(all(not r.get('requires_review') for r in rows))
        self.assertIn('doctor',rows[0]['subjects']);self.assertIn('mask',rows[3]['subjects'])
    def test_manual_keyword_flag_survives_future_reclassification(self):
        row=dict(id=1,text='Quý vị thân mến',queries=['doctor presenter speaking camera'],positive=['doctor'],manual_queries=True,review=True)
        before=copy.deepcopy(row);refine_queries([row]);self.assertEqual(row,before)
    def test_old_block_flag_clears_when_topic_becomes_concrete(self):
        row=dict(id=1,text='nhón gót chân',requires_review=True,**describe('nhón gót chân'))
        refine_queries([row]);self.assertFalse(row.get('requires_review'))

    def test_pending_text_repair_keeps_done_voice_and_timestamps(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from canva_studio.editorial import repair_scene_texts
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);voice=root/'part.wav';voice.write_bytes(b'')
            (root/'transcript.json').write_text('{}')
            rows=[dict(id=1,start=0,source_start=0,duration=1,text='old done',queries=['x']),dict(id=2,start=1,source_start=1,duration=1,text='nước tranh',**describe('nước tranh'))]
            state=dict(scenes=rows,done=[1],phase={},original_voice=str(root/'source.mp3'),voice=str(voice),voice_done=True)
            segments=[dict(words=[dict(word='nước',start=1,end=1.5),dict(word='chanh',start=1.5,end=2)])]
            with patch('canva_studio.editorial.neighboring_script',return_value=root/'script.docx'),patch('canva_studio.core.read_script',return_value='script'),patch('canva_studio.core.load_transcript',return_value=[]),patch('canva_studio.core.align_script',return_value=(segments,True)):
                self.assertEqual(repair_scene_texts(state),1)
            self.assertEqual(rows[0]['text'],'old done');self.assertEqual(rows[1]['text'],'nước chanh')
            self.assertEqual(rows[1]['start'],1);self.assertEqual(rows[1]['duration'],1);self.assertTrue(state['voice_done'])
    def test_script_auto_selection_is_unambiguous(self):
        import tempfile
        from pathlib import Path
        from canva_studio.editorial import neighboring_script
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);voice=root/'source.mp3';self.assertIsNone(neighboring_script(voice))
            (root/'one.docx').touch();self.assertEqual(neighboring_script(voice),root/'one.docx')
            (root/'two.docx').touch();self.assertIsNone(neighboring_script(voice))
