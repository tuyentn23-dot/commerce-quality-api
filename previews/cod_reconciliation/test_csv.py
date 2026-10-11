import json
import tempfile
import unittest
from pathlib import Path
from csv_cli import read_csv, ORDER_COLUMNS, SETTLEMENT_COLUMNS
from core import reconcile

HERE=Path(__file__).resolve().parent


class CSVTests(unittest.TestCase):
    def parse(self, text, limit=500):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            p=Path(folder)/'input.csv';p.write_text(text,encoding='utf-8')
            return read_csv(p,ORDER_COLUMNS,limit)[0]

    def test_csv_and_json_samples_have_identical_result(self):
        orders,_=read_csv(HERE/'sample_orders.csv',ORDER_COLUMNS,500)
        settlements,_=read_csv(HERE/'sample_settlements.csv',SETTLEMENT_COLUMNS,1000)
        expected=reconcile(json.loads((HERE/'sample.json').read_text()))
        self.assertEqual(reconcile({'orders':orders,'settlements':settlements}),expected)

    def test_bom_and_quoted_tracking_id(self):
        rows=self.parse('\ufeffcarrier,tracking_id,currency,expected_net\ndemo,"A,B",VND,100\n')
        self.assertEqual(rows[0]['tracking_id'],'A,B')

    def test_duplicate_and_unknown_headers_rejected(self):
        for header in ['carrier,tracking_id,currency,currency','carrier,tracking_id,currency,fees']:
            with self.assertRaises(ValueError):self.parse(header+'\ndemo,A,VND,100\n')

    def test_missing_extra_cells_rejected(self):
        for cells in ['demo,A,VND','demo,A,VND,100,extra']:
            with self.assertRaises(ValueError):self.parse('carrier,tracking_id,currency,expected_net\n'+cells+'\n')

    def test_row_and_file_bound(self):
        with self.assertRaises(ValueError):self.parse('carrier,tracking_id,currency,expected_net\ndemo,A,VND,1\ndemo,B,VND,1\n',limit=1)
        with self.assertRaises(ValueError):self.parse('x'*1_000_001)

    def test_locale_money_is_not_silently_coerced(self):
        rows=self.parse('carrier,tracking_id,currency,expected_net\ndemo,A,VND,"1,000"\n')
        with self.assertRaises(ValueError):reconcile({'orders':rows,'settlements':[]})


if __name__=='__main__':unittest.main()
