"""Compare two normalized CSV files locally, without carrier access."""
import argparse
import csv
import io
import json
import sys
from pathlib import Path
from core import MAX_BYTES, reconcile

ORDER_COLUMNS = ['carrier', 'tracking_id', 'currency', 'expected_net']
SETTLEMENT_COLUMNS = ['carrier', 'tracking_id', 'currency', 'settlement_id', 'net_received']


def read_csv(path, columns, max_rows):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('CSV exceeds size limit')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames) or set(reader.fieldnames) != set(columns):
        raise ValueError('CSV header must contain exactly the documented distinct columns')
    rows = []
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('CSV row has missing or extra cells')
        rows.append(row)
        if len(rows) > max_rows:
            raise ValueError('CSV exceeds row limit')
    return rows, len(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('orders', type=Path)
    parser.add_argument('settlements', type=Path)
    parser.add_argument('--tolerance', default='0')
    args = parser.parse_args()
    try:
        orders, order_bytes = read_csv(args.orders, ORDER_COLUMNS, 500)
        settlements, settlement_bytes = read_csv(args.settlements, SETTLEMENT_COLUMNS, 1000)
        if order_bytes + settlement_bytes > MAX_BYTES:
            raise ValueError('Combined CSV input exceeds 1 MB')
        result = reconcile({'orders':orders,'settlements':settlements,'tolerance':args.tolerance})
    except (ValueError, OSError, csv.Error):
        print('Input rejected. Check UTF-8 comma-separated CSV headers, row sizes and decimal strings.', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
