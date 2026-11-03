import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from canva_studio.downloads import verify_download

class DownloadTests(unittest.TestCase):
    def test_completed_file_must_have_video_audio_and_expected_duration(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'video.mp4';p.write_bytes(b'media')
            def result(streams,duration=5):return SimpleNamespace(stdout=json.dumps(dict(streams=streams,format=dict(duration=duration))).encode())
            with patch('subprocess.run',return_value=result([dict(codec_type='video'),dict(codec_type='audio')])) as run:
                self.assertEqual(verify_download(str(p),'ffmpeg.exe',5)['duration'],5)
                self.assertEqual(run.call_args.kwargs['timeout'],15)
            for value in [result([dict(codec_type='video')]),result([dict(codec_type='audio')]),result([dict(codec_type='video'),dict(codec_type='audio')],2)]:
                with patch('subprocess.run',return_value=value),self.assertRaises(ValueError):verify_download(str(p),'ffmpeg.exe',5)
            with self.assertRaises(ValueError):verify_download(str(p.with_name('missing.mp4')),'ffmpeg.exe',5)
