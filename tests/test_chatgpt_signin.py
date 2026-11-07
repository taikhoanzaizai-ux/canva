import base64
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen

from canva_studio import chatgpt_signin as oauth
from canva_studio.keyword_api import CHATGPT_PLAN, request_keywords


class ChatGPTSigninTests(unittest.TestCase):
    def test_loopback_authorization_uses_issued_client_pkce_and_granted_models(self):
        issued = 'oaiapp_fixture'
        params = {}

        def open_browser(url):
            params.update({k: v[0] for k, v in parse_qs(urlsplit(url).query).items()})
            def callback():
                query = urlencode({'code':'one-time', 'state':params['state'], 'client_id':issued})
                with urlopen(params['redirect_uri'] + '?' + query, timeout=3) as response:
                    response.read()
            threading.Thread(target=callback, daemon=True).start()
            return True

        def response(url, form=None, token=None):
            if form:
                self.assertEqual(form['client_id'], issued)
                self.assertEqual(form['redirect_uri'], params['redirect_uri'])
                self.assertEqual(form['resource'], oauth.RESOURCE)
                challenge = base64.urlsafe_b64encode(hashlib.sha256(form['code_verifier'].encode()).digest())
                self.assertEqual(challenge.decode().rstrip('='), params['code_challenge'])
                return {'id_token':'identity', 'access_token':'private-bearer', 'expires_in':3600,
                        'scope':oauth.SCOPES, 'token_type':'Bearer'}
            self.assertEqual(url, oauth.RESOURCE + '/models')
            self.assertEqual(token, 'private-bearer')
            return {'models':[{'visibility':'list', 'slug':'gpt-fixture', 'display_name':'Fixture'},
                              {'visibility':'hidden', 'slug':'hidden', 'display_name':'Hidden'}]}

        with tempfile.TemporaryDirectory() as directory, patch.object(
            oauth.webbrowser,'open_new_tab',side_effect=open_browser
        ), patch.object(oauth,'api_json',side_effect=response), patch.object(
            oauth,'validate_identity',return_value={'sub':'verified'}
        ) as identity:
            session = oauth.sign_in(Path(directory), threading.Event())
            identity.assert_called_once_with('identity', issued, params['nonce'])
            self.assertEqual(params['client_id'], 'dynamic_agent_client')
            self.assertEqual(session.models, (('gpt-fixture','Fixture'),))
            self.assertNotIn('private-bearer', repr(session))
            self.assertNotIn('private-bearer', (Path(directory)/'chatgpt-registration.json').read_text())

    @unittest.skipUnless(os.name == 'nt' and shutil.which('node'), 'Windows CNG and Node fixture signer required')
    def test_windows_checks_signature_and_oidc_nonce(self):
        now = int(time.time())
        claims = {'iss':oauth.ISSUER, 'aud':'oaiapp_fixture', 'sub':'fixture', 'nonce':'match',
                  'iat':now, 'exp':now+600}
        code = '''
const c = require('node:crypto');
const {publicKey,privateKey} = c.generateKeyPairSync('rsa',{modulusLength:2048});
const enc = o => Buffer.from(JSON.stringify(o)).toString('base64url');
const body = enc({alg:'RS256',kid:'fixture'})+'.'+enc(JSON.parse(process.argv[1]));
const signature = c.sign('sha256',Buffer.from(body),privateKey).toString('base64url');
console.log(JSON.stringify({token:body+'.'+signature,key:{...publicKey.export({format:'jwk'}),kid:'fixture'}}));
'''
        fixture = json.loads(subprocess.check_output(['node','-e',code,json.dumps(claims)], text=True))
        with patch.object(oauth,'api_json',return_value={'keys':[fixture['key']]}):
            self.assertEqual(oauth.validate_identity(fixture['token'],'oaiapp_fixture','match')['sub'],'fixture')
            with self.assertRaises(ValueError):
                oauth.validate_identity(fixture['token'],'oaiapp_fixture','different')
            head, body, signature = fixture['token'].split('.')
            wrong = ('A' if signature[0]!='A' else 'B') + signature[1:]
            with self.assertRaises(ValueError):
                oauth.validate_identity('.'.join((head,body,wrong)),'oaiapp_fixture','match')

    def test_chatgpt_plan_uses_completed_stream_and_omits_unsupported_output_cap(self):
        session = oauth.Session('private-bearer', time.time()+100, ())
        content = [{'type':'output_text','text':'{"scenes": []}'}]
        event = {'type':'response.completed','response':{'status':'completed',
                 'output':[{'type':'message','content':content}]}}
        def stream(event):
            return io.BytesIO(b'data: '+json.dumps(event).encode()+b'\n\n')
        with patch('canva_studio.keyword_api.build_opener') as opener:
            opener.return_value.open.return_value = stream(event)
            self.assertEqual(request_keywords(CHATGPT_PLAN,'gpt-fixture',session,[]),[])
            request = opener.return_value.open.call_args.args[0]
            body = json.loads(request.data)
            self.assertEqual(request.get_header('Authorization'), 'Bearer private-bearer')
            self.assertEqual((body['store'],body['stream']),(False,True))
            self.assertIsInstance(body['input'],list)
            self.assertNotIn('max_output_tokens',body)
            opener.return_value.open.return_value = stream({'type':'response.failed','response':{
                'error':{'code':'subscription_sharing_usage_limit_exceeded'}}})
            with self.assertRaisesRegex(ValueError,'chạm giới hạn'):
                request_keywords(CHATGPT_PLAN,'gpt-fixture',session,[])
