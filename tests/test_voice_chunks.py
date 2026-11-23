import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from canva_studio.bridge import Engine,MIN_EXTENSION_VERSION,VOICE_CHUNK_BYTES


class VoiceChunkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.audio=Path(self.tmp.name)/'large.wav'
        with self.audio.open('wb') as file:
            file.seek(90*1024*1024)
            file.write(b'end')
        self.engine=Engine(self.tmp.name)
        self.engine.configure(dict(scenes=[dict(id=1,start=0,duration=4,text='test',queries=['test'])]),
            'https://www.canva.com/design/abc/def/edit',self.audio)
        self.client=dict(client='A',url=self.engine.state['target'],extension_version=MIN_EXTENSION_VERSION)
        self.engine.start();self.engine.next_task(self.client)
        self.body=dict(id='voice',client='A')

    def metadata(self):
        return self.engine.voice_data({**self.body,'metadata':True})

    def chunk(self,meta,offset):
        return self.engine.voice_data({**self.body,'transfer_id':meta['transfer_id'],'offset':offset})

    def test_large_voice_has_no_file_size_cap_and_small_responses(self):
        meta=self.metadata()
        self.assertGreater(meta['size'],80*1024*1024)
        self.assertNotIn('data',meta)
        self.assertEqual(meta['chunk_size'],VOICE_CHUNK_BYTES)
        for offset in (0,meta['size']-3,VOICE_CHUNK_BYTES):
            result=self.chunk(meta,offset)
            raw=base64.b64decode(result['data'],validate=True)
            self.assertLess(len(json.dumps(result).encode()),1024*1024)
            self.assertEqual(result['offset'],offset)
            self.assertEqual(len(raw),min(VOICE_CHUNK_BYTES,meta['size']-offset))
            self.assertEqual(hashlib.sha256(raw).hexdigest(),result['sha256'])
        self.assertEqual(base64.b64decode(self.chunk(meta,meta['size']-3)['data']),b'end')

    def test_bad_offset_foreign_client_and_pause_are_rejected(self):
        meta=self.metadata()
        for offset in (-1,True,1.5,meta['size']):
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.chunk(meta,offset)
        with self.assertRaises(ValueError):
            self.engine.voice_data(dict(id='voice',client='B',transfer_id=meta['transfer_id'],offset=0))
        self.engine.pause()
        with self.assertRaises(ValueError):self.chunk(meta,0)

    def test_file_change_and_replacement_invalidate_transfer(self):
        meta=self.metadata()
        with self.audio.open('ab') as file:file.write(b'changed')
        with self.assertRaises(ValueError):self.chunk(meta,0)
        meta=self.metadata()
        other=Path(self.tmp.name)/'other.wav';other.write_bytes(b'other')
        self.engine.state['voice']=str(other)
        with self.assertRaises(ValueError):self.chunk(meta,0)

    def test_new_transfer_invalidates_old_and_restart_can_retry(self):
        first=self.metadata();second=self.metadata()
        with self.assertRaises(ValueError):self.chunk(first,0)
        self.assertTrue(self.chunk(second,0)['data'])
        self.engine.pause();self.engine.start();self.engine.next_task(self.client)
        fresh=self.metadata()
        self.assertEqual(fresh['name'],second['name'])
        self.assertEqual(self.chunk(fresh,0)['offset'],0)
