import unittest
from core import reconcile


def order(id='A', currency='VND', expected='100'):
    return {'carrier':'demo','tracking_id':id,'currency':currency,'expected_net':expected}


def settlement(id='A', sid='S1', amount='100', currency='VND'):
    return {'carrier':'demo','tracking_id':id,'currency':currency,'settlement_id':sid,'net_received':amount}


class ReconciliationTests(unittest.TestCase):
    def result(self, orders, rows, **kwargs):
        return reconcile({'orders':orders,'settlements':rows,**kwargs})

    def test_partial_payments_and_reversal(self):
        r=self.result([order()], [settlement(amount='60'),settlement(sid='S2',amount='50'),settlement(sid='S3',amount='-10')])
        self.assertEqual(r['results'][0]['status'],'matched')
        self.assertFalse(r['bank_receipt_verified'])
        self.assertFalse(r['automatic_payment_authorized'])

    def test_observed_shortfall_not_claim_of_overdue(self):
        r=self.result([order()], [settlement(amount='60')])
        self.assertEqual(r['results'][0]['status'],'shortfall_observed')
        self.assertEqual(r['results'][0]['difference'],'-40')

    def test_missing_and_orphan_not_matched(self):
        r=self.result([order(expected='0')], [settlement(id='B')])
        self.assertEqual(r['status_counts'],{'missing_settlement':1,'orphan_settlement':1})

    def test_duplicate_order_never_summed(self):
        r=self.result([order(),order()], [settlement(amount='200')])
        self.assertEqual(r['results'][0]['status'],'ambiguous')
        self.assertIsNone(r['results'][0]['net_received'])

    def test_duplicate_payment_id_blocks_both_tracking_keys(self):
        r=self.result([order(),order('B')], [settlement(),settlement(id='B')])
        self.assertEqual(r['status_counts'],{'ambiguous':2})

    def test_currency_not_combined(self):
        r=self.result([order()], [settlement(currency='USD')])
        self.assertEqual(r['status_counts'],{'orphan_settlement':1,'missing_settlement':1})

    def test_decimal_tolerance(self):
        r=self.result([order(expected='0.30')], [settlement(amount='0.1'),settlement(sid='S2',amount='0.2')])
        self.assertEqual(r['results'][0]['difference'],'0.00')
        r=self.result([order()], [settlement(amount='100.01')],tolerance='0.01')
        self.assertEqual(r['results'][0]['status'],'matched')

    def test_excess(self):
        self.assertEqual(self.result([order()], [settlement(amount='101')])['results'][0]['status'],'excess_observed')

    def test_invalid_amounts_limits_and_unknown_fields(self):
        for value in [100, True, 'NaN','1e2','1,000','-1','1000000000000','1.1234567']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.result([order(expected=value)],[])
        with self.assertRaises(ValueError): self.result([order()]*501,[])
        with self.assertRaises(ValueError): self.result([order()],[settlement()]*1001)
        with self.assertRaises(ValueError): self.result([order()],[],tolerance='2')
        with self.assertRaises(ValueError): self.result([dict(order(),fees='10')],[])


if __name__=='__main__': unittest.main()
