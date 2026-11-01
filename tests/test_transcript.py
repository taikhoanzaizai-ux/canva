import json,tempfile,unittest
from pathlib import Path
from canva_studio.core import load_transcript,make_plan,split_batches
from canva_studio.batches import cached_transcript

class TranscriptTests(unittest.TestCase):
    def load(self,segments):
        self.path.write_text(json.dumps({'segments':segments}),encoding='utf8');return load_transcript(self.path)
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'t.json'
    def tearDown(self):self.tmp.cleanup()
    def test_empty_whisper_marker_is_ignored_without_moving_clock(self):
        source=[dict(start=0,end=2,text='người cao tuổi đi bộ'),dict(start=3,end=3,text='',words=[]),dict(start=2.5,end=5,text='hít thở nhẹ nhàng')]
        rows=self.load(source)
        self.assertEqual(len(rows),2);self.assertEqual(rows[1]['start'],2.5)
        plan=make_plan(rows,end=5);self.assertAlmostEqual(sum(s['duration'] for s in plan['scenes']),5)
    def test_zero_duration_speech_is_not_silently_dropped(self):
        for row in [dict(start=1,end=1,text='lời đọc'),dict(start=1,end=1,text='',words=[dict(word='lời',start=1,end=1)])]:
            with self.assertRaisesRegex(ValueError,'đoạn lời đọc 1'):self.load([row])
    def test_invalid_ranges_and_true_overlap_still_fail(self):
        for row in [dict(start=-1,end=-1,text=''),dict(start=3,end=2,text=''),dict(start=float('nan'),end=2,text='')]:
            with self.assertRaises(ValueError):self.load([row])
        with self.assertRaisesRegex(ValueError,'đoạn lời đọc 2'):self.load([dict(start=0,end=4,text='a'),dict(start=3,end=5,text='b')])
    def test_only_empty_markers_is_not_a_transcript(self):
        with self.assertRaisesRegex(ValueError,'Không có lời đọc'):self.load([dict(start=1,end=1,text='',words=None)])
    def test_cache_requires_exact_audio_and_readable_transcript(self):
        root=Path(self.tmp.name);old=root/'old';new=root/'new';old.mkdir();new.mkdir()
        (old/'recognition.wav').write_bytes(b'abcd');clip=new/'recognition.wav';clip.write_bytes(b'abcd')
        out=old/'transcript.json';out.write_text(json.dumps({'segments':[dict(start=0,end=1,text='a'),dict(start=1,end=1,text='')]}))
        self.assertEqual(cached_transcript(root,clip),out)
        clip.write_bytes(b'abce');self.assertIsNone(cached_transcript(root,clip))
        clip.write_bytes(b'abcd');out.write_text('{invalid');self.assertIsNone(cached_transcript(root,clip))
