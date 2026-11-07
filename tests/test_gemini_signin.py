import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from canva_studio import gemini_signin
from canva_studio.keyword_api import GEMINI_SIGNIN, request_keywords


class FakeCLI:
    def __init__(self, permission, result):
        events = [{'event':'init','init':{'permission_mode':permission}}, result]
        self.stdout = io.BytesIO(b''.join(json.dumps(event).encode()+b'\n' for event in events))
        self.writes = []
        self.stdin = self
        self.exited = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stdout.close()

    def write(self, data):
        self.writes.append(data)

    def close(self):
        pass

    def wait(self, timeout):
        self.exited = True

    def poll(self):
        return 0 if self.exited else None

    def kill(self):
        self.exited = True


class GeminiSigninTests(unittest.TestCase):
    def test_uses_signed_in_cli_and_structured_result(self):
        result = {'event':'result','result':{'status':'SUCCESS','structured_output':{'scenes':[]}}}
        process = FakeCLI('strict', result)
        with tempfile.TemporaryDirectory() as d, patch.object(
            gemini_signin.subprocess,'Popen',return_value=process
        ) as popen, patch.dict(gemini_signin.os.environ, {'GEMINI_API_KEY':'fixture', 'GOOGLE_GEMINI_BASE_URL':'https://example.test'}):
            self.assertEqual(request_keywords(GEMINI_SIGNIN,'',(Path('agy.exe'),Path(d)),[{'id':1,'text':'Lời đọc'}]),[])
            args = popen.call_args.args[0]
            self.assertIn('--json-schema',args)
            self.assertNotIn('Lời đọc',' '.join(args))
            self.assertNotIn('GEMINI_API_KEY',popen.call_args.kwargs['env'])
            self.assertNotIn('GOOGLE_GEMINI_BASE_URL',popen.call_args.kwargs['env'])
            self.assertIn('Lời đọc',json.loads(process.writes[0])['message']['content'])

    def test_refuses_non_strict_cli_before_sending_text(self):
        process = FakeCLI('always-proceed', {'event':'result'})
        with tempfile.TemporaryDirectory() as d, patch.object(gemini_signin.subprocess,'Popen',return_value=process):
            with self.assertRaisesRegex(ValueError,'Strict'):
                gemini_signin.request_keywords(Path('agy.exe'),Path(d),'','private script',{})
        self.assertEqual(process.writes,[])
        self.assertTrue(process.exited)

    def test_reports_quota_without_printing_provider_error(self):
        result = {'event':'result','result':{'status':'ERROR','error':'429 quota; private diagnostic'}}
        with tempfile.TemporaryDirectory() as d, patch.object(
            gemini_signin.subprocess,'Popen',return_value=FakeCLI('strict',result)
        ):
            with self.assertRaisesRegex(ValueError,'chạm hạn mức') as error:
                gemini_signin.request_keywords(Path('agy.exe'),Path(d),'','fixture',{})
        self.assertNotIn('private diagnostic',str(error.exception))
