import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('commerce_quality', HERE / 'main.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class QualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=HERE)
        self.env = patch.dict(os.environ, {'RAPIDAPI_PROXY_SECRET': 'test-proxy', 'ADMIN_TOKEN': 'test-admin', 'METRICS_HASH_SECRET': 'test-hash'})
        self.env.start()
        self.db = patch.object(module, 'DB_PATH', Path(self.temp.name) / 'usage.sqlite3')
        self.db.start()
        self.client = TestClient(module.app)
        self.headers = {'X-RapidAPI-Proxy-Secret': 'test-proxy', 'X-RapidAPI-User': 'test-user'}

    def tearDown(self):
        self.client.close()
        self.db.stop()
        self.env.stop()
        self.temp.cleanup()

    def post(self, path, body):
        return self.client.post(path, json=body, headers=self.headers)

    def test_decimal_arithmetic(self):
        response = self.post('/v1/invoices/validate', {'subtotal': '0.1', 'tax': '0.2', 'total': '0.3', 'tolerance': '0'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['valid'])

    def test_total_and_line_mismatches(self):
        response = self.post('/v1/invoices/validate', {'subtotal': '20', 'total': '21', 'lines': [{'quantity': '2', 'unit_price': '8', 'line_total': '19'}]})
        self.assertEqual(len(response.json()['issues']), 3)

    def test_invalid_money_and_batch_limits(self):
        self.assertEqual(self.post('/v1/invoices/validate', {'subtotal': '-1', 'total': '1'}).status_code, 422)
        self.assertEqual(self.post('/v1/contacts/normalize', {'contacts': [{}] * 201}).status_code, 422)

    def test_phone_and_email_normalization(self):
        result = self.post('/v1/contacts/normalize', {'contacts': [{'email': 'User@EXAMPLE.COM ', 'phone': '+84 912 345 678'}]}).json()['results'][0]
        self.assertEqual(result['email'], 'User@example.com')
        self.assertEqual(result['phone_e164'], '+84912345678')
        self.assertFalse(result['ownership_verified'])

    def test_invalid_contact_and_missing_fields(self):
        results = self.post('/v1/contacts/normalize', {'contacts': [{'email': 'a..b@example.com', 'phone': 'abc0912345678'}, {}]}).json()['results']
        self.assertFalse(results[0]['email_syntax_valid'])
        self.assertFalse(results[0]['vn_mobile_shape_valid'])
        self.assertIsNone(results[1]['phone_e164'])

    def test_duplicates_skip_empty_and_preserve_types(self):
        response = self.post('/v1/records/duplicate-candidates', {'records': [{'id': ' A '}, {'id': 'A'}, {'id': ''}, {}, {'id': True}, {'id': 1}], 'key_fields': ['id']})
        self.assertEqual(response.json()['candidate_groups'], [[0, 1]])
        self.assertEqual(response.json()['skipped_indices'], [2, 3])

    def test_casefold_opt_in(self):
        body = {'records': [{'id': 'A'}, {'id': 'a'}], 'key_fields': ['id']}
        self.assertEqual(self.post('/v1/records/duplicate-candidates', body).json()['candidate_groups'], [])
        body['casefold'] = True
        self.assertEqual(self.post('/v1/records/duplicate-candidates', body).json()['candidate_groups'], [[0, 1]])

    def test_auth_and_admin_separation(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        self.assertEqual(self.client.get('/metrics', headers=self.headers).status_code, 401)
        self.assertEqual(self.client.post('/v1/invoices/validate', json={}).status_code, 401)
        with patch.dict(os.environ, {'RAPIDAPI_PROXY_SECRET': ''}):
            self.assertEqual(self.post('/v1/invoices/validate', {}).status_code, 503)

    def test_metrics_persist_and_do_not_count_monitoring(self):
        self.post('/v1/invoices/validate', {'subtotal': '1', 'total': '1'})
        headers = {'Authorization': 'Bearer test-admin'}
        first = self.client.get('/metrics', headers=headers).json()
        self.client.get('/health')
        second = self.client.get('/metrics', headers=headers).json()
        self.assertEqual(first['total_requests'], 1)
        self.assertEqual(second, first)
        self.assertEqual(first['unique_subscribers'], 1)
        self.assertNotIn(b'test-user', module.DB_PATH.read_bytes())

    def test_body_size_bound(self):
        response = self.client.post('/v1/invoices/validate', content=b'x' * 1_000_001, headers=self.headers)
        self.assertEqual(response.status_code, 413)

    def test_redacted_placeholder_never_authenticates(self):
        with patch.dict(os.environ, {'RAPIDAPI_PROXY_SECRET': '<redacted>', 'TNT_GATEWAY_TOKEN': '<redacted>'}):
            self.assertEqual(self.post('/v1/invoices/validate', {}).status_code, 503)

    def test_configured_gateway_header(self):
        with patch.dict(os.environ, {'TNT_GATEWAY_TOKEN': 'custom-gateway-token', 'RAPIDAPI_PROXY_HEADER': 'X-TNT-Proxy-Secret'}):
            response = self.client.post('/v1/invoices/validate', json={'subtotal': '1', 'total': '1'}, headers={'X-TNT-Proxy-Secret': 'custom-gateway-token'})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()['valid'])

if __name__ == '__main__':
    unittest.main()
