import tempfile
import unittest
from pathlib import Path
from canva_studio.core import load_transcript, make_keyword_plan, split_batches


class KeywordSrtTests(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.srt'
            path.write_text(text,encoding='utf-8-sig')
            return load_transcript(path)

    def test_import_text_keywords_and_cue_boundaries(self):
        segments=self.read('1\n00:00:00,000 --> 00:00:03,000\nLời đọc: Nước ép cam.\nTừ khóa: quả cam; nước ép cam\n\n2\n00:00:03,000 --> 00:00:07,000\nTim đang đập.\nKeywords: heart | tim\n')
        self.assertEqual(segments[0]['text'],'Nước ép cam.')
        self.assertEqual(segments[0]['queries'],['quả cam','nước ép cam'])
        plan=make_keyword_plan(segments,0,9)
        self.assertEqual(plan['duration'],9)
        self.assertEqual(plan['scenes'][0]['queries'],['quả cam','nước ép cam'])
        self.assertTrue(any(s['source_start']==3 and s['queries']==['heart','tim'] for s in plan['scenes']))
        self.assertTrue(all('Từ khóa' not in s['text'] for s in plan['scenes']))
        at=0
        for scene in plan['scenes']:
            self.assertAlmostEqual(scene['start'],at,places=3)
            self.assertLessEqual(scene['duration'],5.001)
            at=round(at+scene['duration'],3)
        self.assertEqual(at,9)

    def test_plain_srt_remains_plain(self):
        self.assertEqual(self.read('1\n00:00:00,000 --> 00:00:02,000\nXin chào.\n')[0]['text'],'Xin chào.')

    def test_long_cue_crop_keywords_and_batches(self):
        segments=self.read('1\n00:00:00,000 --> 00:00:12,000\nMột hai ba bốn năm sáu bảy tám chín mười.\nTừ khóa Canva: đi bộ\n- thể dục\n')
        plan=make_keyword_plan(segments,2,10)
        self.assertGreater(len(plan['scenes']),1)
        self.assertTrue(all(s['queries']==['đi bộ','thể dục'] for s in plan['scenes']))
        self.assertEqual(plan['scenes'][0]['source_start'],2)
        parts=split_batches(plan,1)
        self.assertAlmostEqual(sum(p['duration'] for p in parts),8,places=3)
