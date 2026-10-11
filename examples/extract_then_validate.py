"""RapidAPI extractor -> validator example. Secrets come only from environment."""
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
import argparse

EXTRACTOR = 'invoice-to-json-extractor1.p.rapidapi.com'
VALIDATOR = 'invoice-arithmetic-validator.p.rapidapi.com'


def call(host, path, body):
    key = os.environ.get('RAPIDAPI_KEY')
    if not key:
        raise ValueError('Set RAPIDAPI_KEY in your environment; never put it in source.')
    req = urllib.request.Request('https://' + host + path, data=json.dumps(body).encode(), headers={
        'X-RapidAPI-Key': key, 'X-RapidAPI-Host': host, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        # Do not print request headers or credential values.
        raise RuntimeError(f'API returned HTTP {error.code}') from None


def map_invoice(invoice, shipping, discount):
    required = ('subtotal', 'tax_amount', 'total')
    missing = [field for field in required if invoice.get(field) is None]
    if missing:
        raise ValueError('Manual review required: missing ' + ', '.join(missing))
    body = {'subtotal': str(invoice['subtotal']), 'tax': str(invoice['tax_amount']),
            'total': str(invoice['total']), 'shipping': shipping, 'discount': discount,
            'tolerance': '0.01', 'lines': []}
    for i, line in enumerate(invoice.get('line_items', [])):
        if any(line.get(field) is None for field in ('quantity', 'unit_price', 'amount')):
            raise ValueError(f'Manual review required: incomplete line {i}')
        body['lines'].append({'quantity': str(line['quantity']), 'unit_price': str(line['unit_price']), 'line_total': str(line['amount'])})
    return body


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('text_file', type=Path)
    parser.add_argument('--shipping', required=True, help='Reviewed decimal amount, including 0 when confirmed absent')
    parser.add_argument('--discount', required=True, help='Reviewed decimal amount, including 0 when confirmed absent')
    args = parser.parse_args()
    extracted = call(EXTRACTOR, '/v1/invoice/extract', {'content': args.text_file.read_text(encoding='utf-8-sig')})
    if not extracted.get('success') or not isinstance(extracted.get('invoice'), dict):
        raise ValueError('Extraction failed; review source invoice')
    body = map_invoice(extracted['invoice'], args.shipping, args.discount)
    result = call(VALIDATOR, '/v1/invoices/validate', body)
    print(json.dumps({'invoice_number': extracted['invoice'].get('invoice_number'), 'line_checks': len(body['lines']), 'validation': result}, indent=2))
