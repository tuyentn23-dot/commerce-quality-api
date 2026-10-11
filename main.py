"""Three stateless commerce data APIs, packaged as one deployable service."""
import hashlib
import hmac
import json
import os
import re
import sqlite3
import threading
from decimal import Decimal
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title='Commerce Data Quality API', version='0.1.0', description='Invoice arithmetic checks, contact syntax normalization, and exact duplicate candidates. No live identity verification. No customer payloads are stored.')
DB_PATH = Path(os.getenv('METRICS_DB', str(Path(__file__).with_name('usage.sqlite3'))))
DB_LOCK = threading.Lock()
STARTED_AT = datetime.now(timezone.utc).isoformat()
Money = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=6, allow_inf_nan=False)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Line(StrictModel):
    quantity: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=6, allow_inf_nan=False)]
    unit_price: Money
    line_total: Money


class InvoiceCheck(StrictModel):
    subtotal: Money
    tax: Money = Decimal('0')
    shipping: Money = Decimal('0')
    discount: Money = Decimal('0')
    total: Money
    tolerance: Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)] = Decimal('0.01')
    lines: list[Line] = Field(default_factory=list, max_length=200)


class Contact(StrictModel):
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)


class ContactBatch(StrictModel):
    contacts: list[Contact] = Field(min_length=1, max_length=200)


class DedupeBatch(StrictModel):
    records: list[dict[str, Any]] = Field(min_length=1, max_length=500)
    key_fields: list[str] = Field(min_length=1, max_length=8)
    casefold: bool = False


def record_usage(path, status, user):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DB_LOCK, closing(sqlite3.connect(DB_PATH)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS counters (path TEXT PRIMARY KEY, requests INTEGER, errors INTEGER)')
        db.execute('CREATE TABLE IF NOT EXISTS users (digest TEXT PRIMARY KEY)')
        db.execute('INSERT INTO counters VALUES (?, 1, ?) ON CONFLICT(path) DO UPDATE SET requests=requests+1, errors=errors+excluded.errors', (path, int(status >= 400)))
        if user:
            # Pseudonymous aggregate only: never retain raw RapidAPI user IDs.
            secret = os.getenv('METRICS_HASH_SECRET', '')
            if secret:
                digest = hmac.new(secret.encode(), user.encode(), hashlib.sha256).hexdigest()
                db.execute('INSERT OR IGNORE INTO users VALUES (?)', (digest,))


def metrics_snapshot():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DB_LOCK, closing(sqlite3.connect(DB_PATH)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS counters (path TEXT PRIMARY KEY, requests INTEGER, errors INTEGER)')
        db.execute('CREATE TABLE IF NOT EXISTS users (digest TEXT PRIMARY KEY)')
        rows = db.execute('SELECT path, requests, errors FROM counters').fetchall()
        users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    return {'total_requests': sum(r[1] for r in rows), 'total_errors': sum(r[2] for r in rows),
            'counter_scope': 'backend_local_database', 'process_started_at': STARTED_AT,
            'storage_persistence': os.getenv('METRICS_STORAGE_MODE', 'ephemeral'),
            'unique_subscribers': users if os.getenv('METRICS_HASH_SECRET') else None,
            'subscriber_tracking': 'observed_users' if os.getenv('METRICS_HASH_SECRET') else 'not_configured',
            'endpoint_counts': {r[0]: r[1] for r in rows}}


@app.middleware('http')
async def guard(request: Request, call_next):
    path = request.url.path
    if path == '/health':
        return await call_next(request)
    secret = os.getenv('ADMIN_TOKEN' if path == '/metrics' else 'RAPIDAPI_PROXY_SECRET', '')
    supplied = request.headers.get('Authorization', '') if path == '/metrics' else request.headers.get(os.getenv('RAPIDAPI_PROXY_HEADER', 'X-RapidAPI-Proxy-Secret'), '')
    if not secret or secret in ('<redacted>', '[redacted]'):
        return JSONResponse({'detail': 'Service authentication not configured'}, status_code=503)
    expected = 'Bearer ' + secret if path == '/metrics' else secret
    if not hmac.compare_digest(supplied.encode(), expected.encode()):
        return JSONResponse({'detail': 'Unauthorized'}, status_code=401)
    # Bound streamed and chunked bodies, not just Content-Length.
    payload = bytearray()
    async for chunk in request.stream():
        payload.extend(chunk)
        if len(payload) > 1_000_000:
            return JSONResponse({'detail': 'Payload too large'}, status_code=413)
    request._body = bytes(payload)
    response = await call_next(request)
    if path.startswith('/v1/'):
        record_usage(path, response.status_code, request.headers.get('X-RapidAPI-User'))
    return response


@app.get('/health', include_in_schema=False)
def health():
    return {'ok': True, 'version': app.version, 'process_started_at': STARTED_AT}


@app.get('/metrics', include_in_schema=False)
def metrics():
    return metrics_snapshot()


@app.post('/v1/invoices/validate', tags=['Invoice Arithmetic Validator'])
def validate_invoice(body: InvoiceCheck):
    """Check arithmetic of supplied values; does not validate tax law or invoice authenticity."""
    issues = []
    expected = body.subtotal + body.tax + body.shipping - body.discount
    if abs(body.total - expected) > body.tolerance:
        issues.append({'field': 'total', 'expected': str(expected), 'actual': str(body.total), 'difference': str(body.total - expected)})
    if body.lines:
        line_sum = sum((line.line_total for line in body.lines), Decimal('0'))
        if abs(body.subtotal - line_sum) > body.tolerance:
            issues.append({'field': 'subtotal', 'expected': str(line_sum), 'actual': str(body.subtotal)})
        for i, line in enumerate(body.lines):
            amount = line.quantity * line.unit_price
            if abs(line.line_total - amount) > body.tolerance:
                issues.append({'field': f'lines[{i}].line_total', 'expected': str(amount), 'actual': str(line.line_total)})
    return {'valid': not issues, 'expected_total': str(expected), 'issues': issues, 'scope': 'arithmetic_only'}


def normalize_contact(contact):
    email = None
    email_ok = None
    phone = None
    phone_ok = None
    if contact.email is not None:
        value = contact.email.strip()
        local, separator, domain = value.rpartition('@')
        try:
            domain = domain.encode('idna').decode('ascii').lower()
        except UnicodeError:
            domain = ''
        # Conservative ASCII dot-atom subset; not a complete RFC email validator.
        local_ok = bool(re.fullmatch(r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*", local)) and len(local) <= 64
        labels = domain.split('.')
        domain_ok = len(labels) >= 2 and all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label) for label in labels)
        email_ok = bool(separator and local_ok and domain_ok and len(local + '@' + domain) <= 254)
        email = local + '@' + domain if email_ok else None
    if contact.phone is not None:
        value = re.sub(r'[\s().-]', '', contact.phone)
        if value.startswith('+84'):
            value = '0' + value[3:]
        elif value.startswith('0084'):
            value = '0' + value[4:]
        elif value.startswith('84') and len(value) == 11:
            value = '0' + value[2:]
        phone_ok = bool(re.fullmatch(r'0[35789][0-9]{8}', value))
        phone = '+84' + value[1:] if phone_ok else None
    return {'email': email, 'email_syntax_valid': email_ok, 'phone_e164': phone, 'vn_mobile_shape_valid': phone_ok,
            'scope': 'syntax_only', 'deliverability_verified': False, 'ownership_verified': False}


@app.post('/v1/contacts/normalize', tags=['VN Contact Cleaner'])
def contacts(body: ContactBatch):
    """Normalize email domains and Vietnamese mobile shapes, preserving email local-part case."""
    return {'count': len(body.contacts), 'results': [normalize_contact(c) for c in body.contacts]}


@app.post('/v1/records/duplicate-candidates', tags=['Batch Duplicate Detector'])
def duplicate_candidates(body: DedupeBatch):
    """Group exact matches on supplied scalar keys. No records are deleted; review candidates."""
    groups = {}
    skipped = []
    for index, record in enumerate(body.records):
        key = []
        for field in body.key_fields:
            value = record.get(field)
            if value is None or isinstance(value, (dict, list)) or (isinstance(value, str) and not value.strip()):
                skipped.append(index)
                break
            if isinstance(value, str):
                value = value.strip().casefold() if body.casefold else value.strip()
            # Preserve types so True and 1 never collide.
            key.append((type(value).__name__, json.dumps(value, ensure_ascii=False, sort_keys=True)))
        else:
            groups.setdefault(tuple(key), []).append(index)
    matches = [indices for indices in groups.values() if len(indices) > 1]
    return {'candidate_groups': matches, 'candidate_record_count': sum(map(len, matches)),
            'skipped_indices': skipped, 'scope': 'exact_selected_keys', 'records_deleted': 0}
