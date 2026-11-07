import tempfile
import unittest

from canva_studio.bridge import Engine


class ProjectArchiveTests(unittest.TestCase):
    def test_restore_linked_part_skips_newer_unlinked_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            engine = Engine(folder)
            target = 'https://www.canva.com/design/example/token/edit'
            engine.state.update(
                target=target, voice='part.wav', voice_done=True, part_index=3,
                scenes=[{'id': n} for n in range(1, 51)], done=list(range(1, 49)),
                phase={'id': '49', 'stage': 'inserted'}, manual_edit_scene=49,
                manual_review={'scene_id': 49, 'token': 'old-review'},
            )
            engine.archive_project()
            engine.state.update(target='', voice_done=False, scenes=[{'id': 1}], done=[])
            engine.archive_project()
            saved = engine.latest_linked_archive()
            engine.restore_linked_archive(saved)
            state = engine.state
            self.assertEqual((state['mode'], state['target'], state['part_index']), ('paused', target, 3))
            self.assertEqual((len(state['done']), state['manual_edit_scene']), (48, 49))
            self.assertEqual(state['phase']['stage'], 'inserted')
            self.assertNotIn('manual_review', state)
