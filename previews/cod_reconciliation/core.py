"""Caller-supplied COD net-amount comparison. No carrier access or persistence."""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import re

MAX_BYTES = 1_000_000


def text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 100:
        raise ValueError(field + ' must be a nonblank string up to 100 characters')
    return value.strip()


def amount(value, field, signed=False):
    pattern = r'-?\d{1,12}(?:\.\d{1,6})?' if signed else r'\d{1,12}(?:\.\d{1,6})?'
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError(field + ' must be a decimal string, max 12 integer and 6 fractional digits')
    try:
        return Decimal(value)
    except InvalidOperation:
        raise ValueError('Invalid ' + field) from None


def key(row):
    currency = text(row.get('currency'), 'currency')
    if not re.fullmatch('[A-Z]{3}', currency):
        raise ValueError('currency must be three uppercase letters; no currency conversion')
    return (text(row.get('carrier'), 'carrier'), text(row.get('tracking_id'), 'tracking_id'), currency)


def reconcile(body):
    if not isinstance(body, dict) or set(body) - {'orders', 'settlements', 'tolerance'}:
        raise ValueError('Allowed top-level fields: orders, settlements, tolerance')
    orders, settlements = body.get('orders'), body.get('settlements')
    if not isinstance(orders, list) or not 1 <= len(orders) <= 500:
        raise ValueError('orders must contain 1 to 500 rows')
    if not isinstance(settlements, list) or len(settlements) > 1000:
        raise ValueError('settlements must contain 0 to 1000 rows')
    tolerance = amount(body.get('tolerance', '0'), 'tolerance')
    if tolerance > 1:
        raise ValueError('tolerance must be between 0 and 1 in supplied currency units')
    order_groups, settlement_groups = defaultdict(list), defaultdict(list)
    ids = defaultdict(list)
    for index, row in enumerate(orders):
        if not isinstance(row, dict) or set(row) != {'carrier', 'tracking_id', 'currency', 'expected_net'}:
            raise ValueError('Order rows require exactly carrier, tracking_id, currency, expected_net')
        order_groups[key(row)].append((index, amount(row['expected_net'], 'expected_net')))
    for index, row in enumerate(settlements):
        if not isinstance(row, dict) or set(row) != {'carrier', 'tracking_id', 'currency', 'settlement_id', 'net_received'}:
            raise ValueError('Settlement rows require exactly carrier, tracking_id, currency, settlement_id, net_received')
        row_key = key(row)
        settlement_groups[row_key].append((index, amount(row['net_received'], 'net_received', signed=True)))
        # IDs are scoped to carrier, but duplicate IDs across tracking/currency are ambiguous.
        ids[(row_key[0], text(row['settlement_id'], 'settlement_id'))].append(row_key)
    duplicate_keys = {k for keys in ids.values() if len(keys) > 1 for k in keys}
    results = []
    for row_key in sorted(set(order_groups) | set(settlement_groups)):
        expected_rows = order_groups[row_key]
        received_rows = settlement_groups[row_key]
        result = {'carrier': row_key[0], 'tracking_id': row_key[1], 'currency': row_key[2],
                  'order_indices': [r[0] for r in expected_rows], 'settlement_indices': [r[0] for r in received_rows]}
        if len(expected_rows) > 1 or row_key in duplicate_keys:
            result.update(status='ambiguous', expected_net=None, net_received=None, difference=None,
                          reason='duplicate_order_key_or_settlement_id')
        else:
            received = sum((r[1] for r in received_rows), Decimal(0))
            expected = expected_rows[0][1] if expected_rows else None
            difference = received - expected if expected is not None else None
            status = ('orphan_settlement' if expected is None else 'missing_settlement' if not received_rows else
                      'matched' if abs(difference) <= tolerance else 'shortfall_observed' if difference < 0 else 'excess_observed')
            result.update(status=status, expected_net=str(expected) if expected is not None else None,
                          net_received=str(received), difference=str(difference) if difference is not None else None)
        results.append(result)
    counts = dict(Counter(r['status'] for r in results))
    return {'scope': 'supplied_net_amounts_only', 'results': results, 'status_counts': counts,
            'manual_review_required': any(r['status'] != 'matched' for r in results),
            'bank_receipt_verified': False, 'carrier_payment_verified': False,
            'automatic_payment_authorized': False}
