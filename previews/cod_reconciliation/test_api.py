import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app


class APITests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'COD_PROXY_SECRET':'t'*40}); self.env.start()
        self.client=TestClient(app)
        self.headers={'X-TNT-Proxy-Secret':'t'*40}
        self.body={'orders':[{'carrier':'demo','tracking_id':'A','currency':'VND','expected_net':'100'}],'settlements':[]}

    def tearDown(self):
        self.client.close(); self.env.stop()

    def test_health_and_missing_wrong_proxy(self):
        self.assertEqual(self.client.get('/health').status_code,200)
        self.assertEqual(self.client.post('/v1/cod/reconcile',json=self.body).status_code,401)
        self.assertEqual(self.client.post('/v1/cod/reconcile',json=self.body,headers={'X-TNT-Proxy-Secret':'wrong'}).status_code,401)

    def test_unconfigured_fail_closed(self):
        with patch.dict(os.environ,{'COD_PROXY_SECRET':''}):
            self.assertEqual(self.client.post('/v1/cod/reconcile',json=self.body,headers=self.headers).status_code,503)

    def test_authorized_response(self):
        r=self.client.post('/v1/cod/reconcile',json=self.body,headers=self.headers)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['results'][0]['status'],'missing_settlement')

    def test_body_bound_and_invalid_json(self):
        self.assertEqual(self.client.post('/v1/cod/reconcile',content=b'x'*1_000_001,headers=self.headers).status_code,413)
        self.assertEqual(self.client.post('/v1/cod/reconcile',content=b'{',headers=self.headers).status_code,422)
        self.assertEqual(self.client.post('/v1/cod/reconcile',json={'orders':[]},headers=self.headers).status_code,422)

    def test_no_public_docs_or_extra_business_routes(self):
        self.assertEqual(self.client.get('/openapi.json').status_code,401)
        self.assertEqual(self.client.get('/openapi.json',headers=self.headers).status_code,404)


if __name__=='__main__': unittest.main()
