# Invoice Arithmetic Validator

Check invoice totals before posting them to accounting software. Detect mismatched totals, subtotals and line-item amounts using decimal arithmetic, with a configurable rounding tolerance.

Send structured invoice values as decimal strings. The API returns a `valid` flag plus field-level expected and actual amounts. It works with OCR/extraction tools and automation platforms through a single JSON endpoint.

## What it checks

- Total = subtotal + tax + shipping - discount.
- Subtotal equals the sum of supplied line totals, when lines are present.
- Each line total equals quantity × unit price.
- A caller-selected tolerance (default 0.01 in the invoice's amount unit).

Amounts are interpreted in the unit you supply; no currency conversion or tax calculation is performed. Supports up to 200 lines per invoice and payloads up to 1 MB. Numbers should be supplied as decimal strings to preserve precision.

This is an arithmetic consistency check. It does not authenticate invoices, validate tax compliance, verify vendors or detect fraud. A valid result can still contain consistently incorrect input data. Missing values from an extractor should be reviewed rather than silently replaced with zero.

## Three examples

Correct decimal arithmetic:
```json
{"subtotal":"0.10","tax":"0.20","total":"0.30","tolerance":"0"}
```
Expected: `valid: true`, `expected_total: "0.30"`.

Wrong total:
```json
{"subtotal":"100","tax":"10","total":"120"}
```
Expected: `valid: false`, issue for `total`, expected `110`.

Wrong line amount:
```json
{"subtotal":"20","total":"20","lines":[{"quantity":"2","unit_price":"8","line_total":"20"}]}
```
Expected: `valid: false`, issue for `lines[0].line_total`, expected `16`.

## First request

Subscribe to BASIC, copy the RapidAPI request example from the endpoint page, and replace the request body with one of the examples above. Consumer authentication uses your RapidAPI key. The backend proxy secret is managed by the provider and is never needed by consumers.

## Suggested initial plans

- BASIC: $0, 100 requests/month, hard limit, no overage.
- PRO: $4.99/month, 5,000 requests/month, hard limit, no overage.

One request checks one invoice, including up to 200 lines. Pricing is an initial experiment, not a demand forecast. The listing is not public until the proxy path has passed smoke tests.
