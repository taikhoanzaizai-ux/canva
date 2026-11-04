import unittest
from canva_studio.scene_status import scene_status

class SceneStatusTests(unittest.TestCase):
    def test_error_is_visible_even_after_placeholder_was_completed(self):
        scene=dict(id=1,error_card=dict(message='Không tìm thấy ảnh'))
        status,tag,detail=scene_status(scene,dict(done=[1]))
        self.assertEqual(tag,'error');self.assertIn('đã chèn ảnh',status);self.assertIn('Không tìm',detail)
        scene['manual_verified']=True
        self.assertEqual(scene_status(scene,dict(done=[1]))[1],'manual')
    def test_error_history_does_not_leak_between_parts(self):
        state=dict(part_index=1,errors=[dict(id='1',part=1,message='old error')])
        self.assertEqual(scene_status(dict(id=1),state)[0],'Chưa dựng')
        state['errors'].append(dict(id='1',part=2,message='current error'))
        self.assertEqual(scene_status(dict(id=1),state)[2],'current error')
    def test_failed_manual_review_remains_visible(self):
        state=dict(manual_review=dict(scene_id=1),manual_review_error='Mốc sai')
        self.assertEqual(scene_status(dict(id=1,manual_verified=True),state),('Cần sửa lại','error','Mốc sai'))
