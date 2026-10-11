"""Separate API prototype, not deployed. No local payload storage."""
import hmac
import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core import MAX_BYTES, reconcile

app = FastAPI(title='COD Net Reconciliation Preview', version='0.1.0', docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware('http')
async def guard(request: Request, call_next):
    if request.url.path == '/health':
        return await call_next(request)
    secret = os.getenv('COD_PROXY_SECRET', '')
    if len(secret) < 32 or secret in {'<redacted>', '<masked>'}:
        return JSONResponse({'error': 'not_configured'}, status_code=503)
    received = request.headers.get('X-TNT-Proxy-Secret', '')
    if not hmac.compare_digest(received.encode(), secret.encode()):
        return JSONResponse({'error': 'unauthorized'}, status_code=401)
    size = 0
    chunks = []
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_BYTES:
            return JSONResponse({'error': 'payload_too_large'}, status_code=413)
        chunks.append(chunk)
    request._body = b''.join(chunks)
    return await call_next(request)


@app.get('/health')
def health():
    return {'ok': True, 'version': '0.1.0', 'stage': 'prototype'}


@app.post('/v1/cod/reconcile')
async def compare(request: Request):
    try:
        body = json.loads(await request.body())
        return reconcile(body)
    except (ValueError, UnicodeDecodeError):
        return JSONResponse({'error': 'invalid_input', 'detail': 'Check documented fields, decimal strings and row limits'}, status_code=422)
