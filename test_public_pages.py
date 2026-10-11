import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from xml.etree import ElementTree
from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location('quality_public', Path(__file__).with_name('main.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicPageTests(unittest.TestCase):
    def test_public_pages_do_not_require_or_record_credentials(self):
        with patch.dict(os.environ, {'TNT_GATEWAY_TOKEN':'', 'RAPIDAPI_PROXY_SECRET':''}), patch.object(module, 'record_usage') as record:
            with TestClient(module.app) as client:
                for path in module.PUBLIC_PAGES:
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('text/html', response.headers['content-type'])
                    self.assertIn('rel="canonical"', response.text)
                    self.assertIn('rapidapi.com/tuyentn23/api/', response.text)
                record.assert_not_called()

    def test_sitemap_exactly_lists_public_documents(self):
        with TestClient(module.app) as client:
            response = client.get('/sitemap.xml')
            self.assertEqual(response.status_code, 200)
            self.assertIn('application/xml', response.headers['content-type'])
            root = ElementTree.fromstring(response.text)
            urls = {node.text for node in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
            self.assertEqual(urls, {'https://commerce-quality-api.onrender.com'+p for p in module.PUBLIC_PAGES})
            self.assertIn('Disallow: /metrics', client.get('/robots.txt').text)

    def test_public_routes_do_not_open_business_or_admin_paths(self):
        with patch.dict(os.environ, {'TNT_GATEWAY_TOKEN':'synthetic-proxy','ADMIN_TOKEN':'synthetic-admin'}):
            with TestClient(module.app) as client:
                for path in ('/metrics','/docs','/openapi.json','/vn-contact-cleaner/private'):
                    self.assertEqual(client.get(path).status_code,401)
                for path in ('/v1/invoices/validate','/v1/contacts/normalize','/v1/records/duplicate-candidates'):
                    self.assertEqual(client.post(path,json={}).status_code,401)


if __name__=='__main__':
    unittest.main()
