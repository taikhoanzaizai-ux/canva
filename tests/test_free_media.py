import json,tempfile,unittest,urllib.error,time
from pathlib import Path
from unittest.mock import patch
from canva_studio.free_media import Page,valid_page,allowed_url,extract_asset,prepare_external
from canva_studio.fallback import begin_fallback
from canva_studio.bridge import Engine

class FreeMediaTests(unittest.TestCase):
    def test_broad_topic_accepts_device_without_exact_action(self):
        from canva_studio.free_media import relevant
        scene=dict(topic_only=True,allow_all_media=True,subjects=['glucose'],actions=['testing'])
        self.assertTrue(relevant(dict(title='Glucose meter on table'),scene))
        self.assertFalse(relevant(dict(title='Rainbow animation'),scene))

    def test_failed_fallback_is_retried_and_pending_job_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as d:
            e=Engine(d);s=dict(id=1,start=0,duration=3,text='test')
            with patch('canva_studio.fallback.threading.Thread') as thread:
                begin_fallback(e,s);self.assertEqual(thread.call_count,1)
                begin_fallback(e,s);self.assertEqual(thread.call_count,1)
                next(iter(e.asset_jobs.values())).update(pending=False,error='old error')
                self.assertEqual(begin_fallback(e,s)['error'],'old error');self.assertEqual(thread.call_count,1)
                begin_fallback(e,s,retry=True);self.assertEqual(thread.call_count,2)

    def test_external_action_is_required_even_when_all_media_styles_allowed(self):
        from canva_studio.free_media import relevant
        scene=dict(allow_all_media=True,subjects=['heel'],actions=['raise'])
        self.assertFalse(relevant(dict(title='Heel anatomy'),scene))
        self.assertTrue(relevant(dict(title='3D heel raise exercise'),scene))
        self.assertFalse(relevant(dict(title='Organic vegan food'),dict(allow_all_media=True,subjects=['gan','liver'])))

    def test_error_card_uses_error_text_and_never_searches_stock(self):
        with tempfile.TemporaryDirectory() as d:
            engine=Engine(d);scene=dict(id=8,start=12.14,duration=2.76,text='Lời đọc gốc',error_card=dict(start=12.14,message='Không thấy ô tìm kiếm video'))
            captions=[]
            def render(plan,ffmpeg,folder):
                captions.append(plan['scenes'][0]['title_text'])
                self.assertTrue(plan['scenes'][0]['still_image'])
                path=Path(folder)/'test.png';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'png');plan['scenes'][0]['title_path']=str(path)
            with patch('canva_studio.fallback.prepare_external') as search,patch('canva_studio.fallback.render_titles',side_effect=render):
                job=begin_fallback(engine,scene)
                for _ in range(100):
                    if not job.get('pending'):break
                    time.sleep(.01)
                self.assertTrue(job.get('done'));search.assert_not_called()
                self.assertIn('LỖI CẢNH 8',captions[0]);self.assertIn('Không thấy ô tìm kiếm video',captions[0]);self.assertIn('Lời đọc gốc',captions[0])
                self.assertEqual(scene['fallback_source']['kind'],'error_card')
                self.assertEqual(Path(scene['fallback_path']).suffix,'.png')

    def test_legacy_error_mp4_is_not_reused_for_new_png_path(self):
        with tempfile.TemporaryDirectory() as d:
            engine=Engine(d);old=Path(d)/'old.mp4';old.write_bytes(b'old')
            scene=dict(id=29,start=115.34,duration=4.2,text='Lời đọc',fallback_path=str(old),error_card=dict(message='Video tải lên bị lỗi',start=115.34))
            def render(plan,ffmpeg,folder):
                path=Path(folder)/'new.png';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'png');plan['scenes'][0]['title_path']=str(path)
            with patch('canva_studio.fallback.render_titles',side_effect=render):
                job=begin_fallback(engine,scene)
                for _ in range(100):
                    if not job.get('pending'):break
                    time.sleep(.01)
                self.assertTrue(job.get('done'));self.assertTrue(old.exists())
                self.assertEqual(Path(scene['fallback_path']).suffix,'.png')

    def test_native_pages_only_and_no_sponsored_domains(self):
        self.assertTrue(valid_page('https://www.pexels.com/video/doctor-consulting-patient-123/','pexels','video'))
        self.assertTrue(valid_page('https://pixabay.com/videos/doctor-patient-123/','pixabay','video'))
        for url in ['https://www.istockphoto.com/video/doctor-123/','https://pexels.com.evil.test/video/doctor-123/','https://www.pexels.com/search/videos/doctor/']:
            self.assertFalse(valid_page(url,'pexels','video'))
        self.assertFalse(allowed_url('http://videos.pexels.com/file.mp4'))
        self.assertFalse(allowed_url('https://shutterstock.com/file.mp4'))
    def test_only_official_cdn_from_structured_public_metadata(self):
        obj={'@type':'VideoObject','name':'Doctor consulting patient','contentUrl':'https://videos.pexels.com/video-files/123/test.mp4','author':{'name':'Example Author'}}
        markup='<script type="application/ld+json">'+json.dumps(obj)+'</script>'
        result=extract_asset(markup,'https://www.pexels.com/video/doctor-123/','pexels','video')
        self.assertEqual(result['author'],'Example Author');self.assertEqual(result['license'],'https://www.pexels.com/license/')
        obj['contentUrl']='https://ads.example/file.mp4'
        self.assertIsNone(extract_asset('<script type="application/ld+json">'+json.dumps(obj)+'</script>','https://www.pexels.com/video/doctor-123/','pexels','video'))
    def test_explicit_sponsored_links_are_excluded(self):
        parser=Page();parser.feed('<a rel="sponsored" href="https://www.pexels.com/video/doctor-123/">Ad</a><a href="/video/doctor-456/">Real</a>')
        self.assertEqual(parser.links,['/video/doctor-456/'])
    def test_access_barrier_is_not_retried_or_bypassed(self):
        with tempfile.TemporaryDirectory() as d,patch('canva_studio.free_media.fetch',side_effect=urllib.error.HTTPError('url',403,'Forbidden',{},None)) as fetch:
            path,source,diagnostics=prepare_external(dict(duration=3,subjects=['doctor'],queries=['doctor']),[],d,'ffmpeg')
            self.assertIsNone(path);self.assertIsNone(source);self.assertEqual(fetch.call_count,2)
            self.assertTrue(all(r['status']==403 for r in diagnostics))
    def test_background_fallback_keeps_heartbeat_available(self):
        with tempfile.TemporaryDirectory() as d:
            engine=Engine(d);scene=dict(id=1,start=0,duration=3,text='Bảo vệ cơ thể')
            def render(plan,ffmpeg,folder):
                path=Path(folder)/'test.mp4';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'video');plan['scenes'][0]['title_path']=str(path)
            with patch('canva_studio.fallback.prepare_external',return_value=(None,None,[{'status':403}])),patch('canva_studio.fallback.render_titles',side_effect=render):
                job=begin_fallback(engine,scene)
                for _ in range(100):
                    if not job.get('pending'):break
                    time.sleep(.01)
                self.assertTrue(job.get('done'));self.assertTrue(Path(scene['fallback_path']).is_file());self.assertEqual(scene['fallback_source']['provider'],'SKST')
