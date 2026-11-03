import hashlib,io,json,tempfile,unittest,urllib.request,zipfile
from pathlib import Path
from unittest.mock import patch
from canva_studio import recognizer as r
from canva_studio.updater import allowed_file

class RecognizerTests(unittest.TestCase):
    def test_download_rejects_checksum_and_preserves_good_file(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'model.bin';target.write_bytes(b'old')
            class Response(io.BytesIO):headers={}
            class Opener:
                def open(self,*args,**kwargs):return Response(b'wrong')
            with patch('urllib.request.build_opener',return_value=Opener()):
                with self.assertRaises(ValueError):r.download(r.MODEL_URL,target,'0'*64,100)
            self.assertEqual(target.read_bytes(),b'old');self.assertFalse(target.with_suffix('.bin.part').exists())

    def test_cached_model_works_offline(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m';p.write_bytes(b'verified')
            with patch('urllib.request.build_opener',side_effect=AssertionError('No network')):
                self.assertEqual(r.download(r.MODEL_URL,p,hashlib.sha256(b'verified').hexdigest(),100),p)

    def test_verified_zip_rejects_traversal_and_missing_parts(self):
        for bad in ['../escape.dll','C:/bad.dll','Release\\bad.dll']:
            with tempfile.TemporaryDirectory() as d:
                archive=Path(d)/'a.zip'
                with zipfile.ZipFile(archive,'w') as z:z.writestr(bad,b'x')
                with patch.object(r,'RUNTIME_SHA',r.digest(archive)):
                    with self.assertRaises(ValueError):r.extract_runtime(archive,Path(d)/'out')
                self.assertFalse((Path(d)/'out').exists())

    def test_only_runtime_allowlisted_files_are_extracted(self):
        with tempfile.TemporaryDirectory() as d:
            archive=Path(d)/'a.zip'
            with zipfile.ZipFile(archive,'w') as z:
                for n in r.FILES:z.writestr('Release/'+n,b'data')
                z.writestr('Release/server.exe',b'not needed')
            with patch.object(r,'RUNTIME_SHA',r.digest(archive)):r.extract_runtime(archive,Path(d)/'out')
            self.assertEqual({p.name for p in (Path(d)/'out').iterdir()},r.FILES)

    def test_redirects_cannot_fetch_arbitrary_executables(self):
        req=urllib.request.Request(r.MODEL_URL)
        for bad in ['http://huggingface.co/a','https://evil.test/a','https://huggingface.co.evil.test/a']:
            with self.assertRaises(ValueError):r.Redirect().redirect_request(req,None,302,'',{},bad)

    def test_native_command_has_no_python_and_local_output(self):
        args=r.command('whisper-cli.exe','m.bin','voice.wav','out')
        self.assertEqual(Path(args[0]).name,'whisper-cli.exe');self.assertIn('-ng',args);self.assertEqual(args[args.index('-l')+1],'vi')

    def test_accented_install_root_never_reaches_native_file_arguments(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'Ứng dụng tiếng Việt có dấu';job=root/'Data/Projects/abc';job.mkdir(parents=True)
            args=r.command(root/'Data/Tools/whisper-cli.exe',root/'Data/Models/ggml-base.bin',job/'recognition.wav',job/'native')
            self.assertEqual(args[4],'recognition.wav');self.assertEqual(args[-1],'native')
            self.assertTrue(args[2].isascii());self.assertFalse(Path(args[2]).is_absolute())
            self.assertEqual((job/args[2]).resolve(),(root/'Data/Models/ggml-base.bin').resolve())

    def test_utf8_split_tokens_reassemble_before_parsing_words(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'native.json';out=Path(d)/'transcript.json'
            # Native JSON can split a Vietnamese UTF-8 codepoint across token strings.
            raw=b'{"transcription":[{"text":" ch\xc3\xa2n","offsets":{"from":0,"to":1000},"tokens":[{"text":" ch\xc3","offsets":{"from":0,"to":500}},{"text":"\xa2n","offsets":{"from":500,"to":1000}}]}]}'
            p.write_bytes(raw);rows=r.convert_output(p,out)
            self.assertEqual(rows[0]['text'],'chân');self.assertEqual(rows[0]['words'][0]['word'],'chân')
            self.assertEqual(json.loads(out.read_text(encoding='utf8'))['segments'][0]['end'],1)

    def test_updater_runtime_extension_is_narrow(self):
        self.assertTrue(allowed_file('_internal/msvcp140.dll'));self.assertTrue(allowed_file('_internal/vcomp140.dll'))
        self.assertFalse(allowed_file('_internal/evil.dll'));self.assertFalse(allowed_file('_internal/../msvcp140.dll'))
