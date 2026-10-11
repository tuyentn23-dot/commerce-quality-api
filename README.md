# Invoice Arithmetic Validator / Commerce Data Quality API

Live API: [Invoice Arithmetic Validator on RapidAPI](https://rapidapi.com/tuyentn23/api/invoice-arithmetic-validator)

Check invoice arithmetic after OCR or extraction and before a reviewed accounting import. One JSON request checks total, subtotal and up to 200 line-item amounts with decimal precision. The response reports the fields that do not add up.

## Try it

Subscribe to BASIC and run `validateInvoiceArithmetic` in the RapidAPI playground. The ready-to-run example returns `valid: true` and `expected_total: "110"`. Change total to `"120"` to see a mismatch.

- BASIC: $0/month, 100 requests/month.
- PRO: $4.99/month, 5,000 requests/month, Recommended.
- Request quotas use hard limits. RapidAPI displays its standard bandwidth platform fee separately.

```json
{"subtotal":"100","tax":"10","shipping":"0","discount":"0","total":"110","lines":[{"quantity":"2","unit_price":"50","line_total":"100"}]}
```

Checks: total = subtotal + tax + shipping - discount; subtotal equals supplied line totals when lines are present; each line total equals quantity × unit price. Default tolerance is 0.01 in the unit you provide. Use decimal strings for amounts and set tolerance deliberately for your currency/workflow. This service does not authenticate invoices, establish tax compliance, verify vendors, convert currency or detect fraud. A valid result may contain consistently incorrect input. Review missing extraction fields rather than replacing them with zero.

## Integrations

[Python pipeline, mapping guide and inactive n8n template](examples/README.md) connect the existing [Invoice Extractor](https://rapidapi.com/tuyentn23/api/invoice-to-json-extractor1) to this validator. Keys are configured in the environment or credential manager and are absent from the examples. The n8n template has not yet been executed in a live n8n installation.

## Other backend functions

The same backend serves [VN Contact Cleaner](https://rapidapi.com/tuyentn23/api/vn-contact-cleaner), `/v1/contacts/normalize` (up to 200 contacts), and [Batch Duplicate Candidates](https://rapidapi.com/tuyentn23/api/batch-duplicate-candidates), `/v1/records/duplicate-candidates` (up to 500 records). Both listings are public. Contact checks are syntax-only, not ownership or deliverability verification. Duplicate detection returns candidates on selected scalar keys and never deletes records. Payload limit is 1 MB.

Read the [Contact Cleaner guide](listing/CONTACTS.md) and [Duplicate Candidates guide](listing/DUPLICATES.md). Each listing offers BASIC 100 batch requests/month and PRO $4.99 for 5,000 batch requests/month with hard limits. The specifications include synthetic examples for invalid contacts, missing fields and skipped duplicate keys.

## Hosting and monitoring

Provider health: https://commerce-quality-api.onrender.com/health

Backend is hosted on Render Free in Singapore. Cold starts can take 50 seconds or more after inactivity; there is no uptime SLA for this experiment. Metrics are stored in local SQLite and are ephemeral on this hosting plan. RapidAPI is the source for long-term usage, subscriptions and financial transactions. Backend observed users are not necessarily paid subscribers, and provider smoke tests are not customers.

`/health` is public. `/metrics` needs `Authorization: Bearer <ADMIN_TOKEN>`. The deployed gateway adds `X-TNT-Proxy-Secret` automatically; consumers only use their own RapidAPI key. Configure `TNT_GATEWAY_TOKEN` and `RAPIDAPI_PROXY_HEADER=X-TNT-Proxy-Secret` on the host. The guard also supports the standard RapidAPI proxy header for other deployments. Missing or redacted credentials fail closed. Secrets must stay outside source.

To run locally, install `requirements.txt`, set secrets in your process environment and run:

```text
uvicorn main:app --host 127.0.0.1 --port 8010
```

`METRICS_HASH_SECRET` should remain stable if tracking observed users. Only HMAC user digests and aggregate counts are stored, not request payloads or raw RapidAPI user IDs. Set `METRICS_DB` to a mounted persistent volume for durable counters; multiple instances need shared storage rather than local SQLite.

## Validation

- 12 local regression tests cover arithmetic, contact shapes, duplicate keys, authentication, placeholder rejection, custom gateway headers, payload bounds and metrics.
- Deployed backend: 8 smoke checks passed.
- RapidAPI playground: proxy request verified 200 OK with expected arithmetic response.
- Public visibility verified after page reload on 11 October 2026.

These checks demonstrate behavior and configuration, not customer demand or revenue.
