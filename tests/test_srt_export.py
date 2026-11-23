import math
import tempfile
import unittest
from pathlib import Path
from canva_studio.core import keyword_srt, load_transcript, make_keyword_plan, split_batches


class SrtExportTests(unittest.TestCase):
    def test_full_voice_round_trip_over_fifty_scenes(self):
        scenes=[dict(start=i*4,source_start=10+i*4,duration=4,text=f'Cảnh {i+1}.\nĐi bộ.',queries=['đi bộ','walking','đi bộ']) for i in range(123)]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'Canva.srt'
            path.write_text(keyword_srt(dict(scenes=scenes,source_start=10)),encoding='utf-8-sig')
            imported=load_transcript(path)
        self.assertEqual(len(imported),123)
        self.assertEqual(imported[0]['start'],10)
        self.assertEqual(imported[-1]['end'],502)
        self.assertEqual(imported[0]['queries'],['đi bộ','walking'])
        self.assertEqual(imported[0]['text'],'Cảnh 1. Đi bộ.')
        parts=split_batches(make_keyword_plan(imported,start=10))
        self.assertEqual([len(p['scenes']) for p in parts],[50,50,23])

    def test_millisecond_carry_and_nonzero_source_offset(self):
        text=keyword_srt(dict(source_start=3599.9996,scenes=[dict(start=0,duration=1.234,text='Não bộ.',queries=['não'])]))
        self.assertIn('01:00:00,000 --> 01:00:01,234',text)

    def test_reject_invalid_or_overlapping_cues(self):
        row=dict(start=0,duration=1,text='Đầu.',queries=['đầu'])
        for plan in [dict(scenes=[]),dict(scenes=[dict(row,duration=math.inf)]),dict(scenes=[dict(row,queries=[])]),dict(scenes=[row,row])]:
            with self.assertRaises(ValueError):keyword_srt(plan)
