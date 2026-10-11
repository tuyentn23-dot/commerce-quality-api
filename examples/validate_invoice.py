"""Try one synthetic invoice through RapidAPI; uses only Python's standard library."""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

HOST = 'invoice-arithmetic-validator.p.rapidapi.com'
CASES = {
    'correct': {'subtotal': '0.10', 'tax': '0.20', 'total': '0.30', 'tolerance': '0'},
    'wrong-total': {'subtotal': '100', 'tax': '10', 'total': '120'},
    'wrong-line': {'subtotal': '20', 'total': '20', 'lines': [
        {'quantity': '2', 'unit_price': '8', 'line_total': '20'}]},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, default='correct')
    parser.add_argument('--preview', action='store_true', help='Show synthetic input without a request or key')
    args = parser.parse_args()
    body = json.dumps(CASES[args.case]).encode()
    if args.preview:
        print(body.decode())
        return 0
    key = os.getenv('RAPIDAPI_KEY', '').strip()
    if not key:
        print('Set RAPIDAPI_KEY to your own key and subscribe to BASIC first.', file=sys.stderr)
        return 2
    request = urllib.request.Request('https://' + HOST + '/v1/invoices/validate', data=body,
        headers={'Content-Type': 'application/json', 'X-RapidAPI-Key': key, 'X-RapidAPI-Host': HOST}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        advice = {401: 'Check your RapidAPI key.', 403: 'Check your BASIC subscription and key.',
                  429: 'Your request quota or rate limit was reached; wait or review your plan.',
                  422: 'Input was rejected.'}.get(error.code, 'Try later and check the API status.')
        print(f'HTTP {error.code}. {advice}', file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError):
        print('Request failed or response was not JSON. Free hosting may need time to wake; retry once later.', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    # A detected arithmetic mismatch is a successful response, not a transport failure.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
