import io
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from canva_studio.bridge import Engine
from canva_studio.keyword_api import DEFAULT_MODELS, GEMINI, OPENAI, keyword_updates, request_keywords


def peanut_result(ident):
    return dict(id=ident, evidence='lạc luộc', subject_vi='lạc', subject_en='peanut',
                query_vi='lạc luộc', query_en='boiled peanuts')


class KeywordApiTests(unittest.TestCase):
    def test_two_provider_wire_formats(self):
        result = json.dumps({'scenes': [peanut_result(1)]})
        for provider, envelope, host, auth in [
            (OPENAI, {'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': result}]}]}, 'api.openai.com', 'Authorization'),
            (GEMINI, {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
                {'text': result}]}}]}, 'generativelanguage.googleapis.com', 'X-goog-api-key'),
        ]:
            with self.subTest(provider=provider), patch('canva_studio.keyword_api.build_opener') as opener:
                opener.return_value.open.return_value = MagicMock(
                    __enter__=lambda _: io.BytesIO(json.dumps(envelope).encode()), __exit__=lambda *_: None)
                self.assertEqual(request_keywords(provider, DEFAULT_MODELS[provider], 'fixture-key', []), [peanut_result(1)])
                request = opener.return_value.open.call_args.args[0]
                self.assertEqual(request.host, host)
                self.assertIn(auth, dict(request.header_items()))
                self.assertNotIn('fixture-key', request.full_url + request.data.decode())

    def test_evidence_validation_preserves_manual_and_completed_rows(self):
        scenes = [
            {'id': 1, 'text': 'Ăn lạc luộc.', 'start': 0, 'duration': 3},
            {'id': 2, 'text': 'Người già đi bộ.'},
            {'id': 3, 'text': 'Ăn lạc luộc.', 'manual_queries': True},
            {'id': 4, 'text': 'Ăn lạc luộc.'},
        ]
        with patch('canva_studio.keyword_api.request_keywords', return_value=[
            peanut_result(1), dict(peanut_result(2), evidence='cà rốt'), peanut_result(3), peanut_result(4),
        ]) as request:
            updates, note = keyword_updates(scenes, (OPENAI, 'model', 'fixture-key'), skip_ids={4})
        self.assertEqual([row['id'] for row in request.call_args.args[-1]], [1, 2])
        self.assertEqual(updates[1]['queries'][:2], ['lạc luộc', 'boiled peanuts'])
        self.assertEqual(set(updates[2]), {'keyword_review'})
        self.assertEqual(set(updates), {1, 2})
        self.assertNotIn('queries', scenes[0])
        self.assertIn('1/2', note)

    def test_api_error_keeps_existing_keywords_and_hides_response_body(self):
        with patch('canva_studio.keyword_api.build_opener') as opener:
            opener.return_value.open.side_effect = HTTPError(
                'https://api.openai.com', 429, 'private response', {}, None)
            updates, note = keyword_updates([{'id': 1, 'text': 'Ăn lạc luộc.'}], (OPENAI, 'model', 'fixture-key'))
        self.assertIn('429', note)
        self.assertNotIn('private response', note)
        self.assertEqual(set(updates[1]), {'keyword_review'})

    def test_model_keywords_survive_configure_and_reopen(self):
        scene = {'id': 1, 'text': 'Ăn lạc luộc.', 'start': 0, 'duration': 3}
        with tempfile.TemporaryDirectory() as folder, patch(
            'canva_studio.keyword_api.request_keywords', return_value=[peanut_result(1)]
        ):
            updates, _ = keyword_updates([scene], (OPENAI, 'model', 'fixture-key'))
            scene.update(updates[1])
            Engine(folder).configure({'scenes': [scene]}, '', 'fixture.wav', allow_empty=True)
            restored = Engine(folder).state['scenes'][0]
            self.assertEqual(restored['queries'][0], 'lạc luộc')
            self.assertEqual((restored['start'], restored['duration']), (0, 3))
            self.assertEqual(restored['keyword_provider'], OPENAI)
