import unittest
from canva_studio.manual_timing import compensate

class ManualTimingTests(unittest.TestCase):
    def rows(self):return [dict(id=1,start=0,duration=3),dict(id=2,start=3,duration=4),dict(id=3,start=7,duration=5)]
    def test_user_example_3_4_5_becomes_2_5_5(self):
        changes=compensate(self.rows(),{1},[dict(start=0,end=2)])
        self.assertEqual([s['duration'] for s in changes],[2,5,5])
        self.assertEqual([s['start'] for s in changes],[0,2,7])
    def test_longer_cut_spreads_compensation_across_several_future_scenes(self):
        changes=compensate(self.rows(),{1},[dict(start=0,end=8)])
        self.assertEqual(changes[0]['duration'],8)
        self.assertAlmostEqual(changes[1]['duration'],.1)
        self.assertAlmostEqual(changes[-1]['start']+changes[-1]['duration'],12)
    def test_old_completed_following_scenes_are_kept_then_pending_scene_compensates(self):
        changes=compensate(self.rows(),{1,2},[dict(start=0,end=2),dict(start=2,end=6)])
        self.assertEqual([s['duration'] for s in changes],[2,4,6])
        self.assertEqual(changes[-1]['start'],6)
    def test_original_anchors_survive_later_manual_repairs(self):
        rows=self.rows()
        for row,update in zip(rows,compensate(rows,{1},[dict(start=0,end=2)])):row.update(update)
        changes=compensate(rows,{1},[dict(start=0,end=4)])
        self.assertEqual([s['duration'] for s in changes],[4,3,5])
    def test_gaps_and_impossible_overruns_do_not_corrupt_plan(self):
        for frames in [[dict(start=1,end=2)],[dict(start=0,end=13)]]:
            with self.assertRaises(ValueError):compensate(self.rows(),{1},frames)
