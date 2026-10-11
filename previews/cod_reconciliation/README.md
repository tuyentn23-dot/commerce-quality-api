# COD Net Reconciliation — evaluation prototype

Compare reviewed expected net remittances with caller-supplied settlement rows. Run the local tool without a network connection, carrier account or API subscription. This is not yet a hosted API or RapidAPI listing, and paid demand is unverified.

## Try locally

Requires Python 3.10 or newer; the local CLI uses only its standard library:

```text
python cli.py sample.json
```

The synthetic example returns one matched shipment, one observed shortfall of VND 20,000, one missing settlement and one settlement without an order. Output is printed locally; the tool does not upload input or write a customer-data database.

## Compare normalized CSV files

```text
python csv_cli.py sample_orders.csv sample_settlements.csv
```

Use UTF-8 (BOM accepted), comma-separated CSV. Orders need exactly `carrier,tracking_id,currency,expected_net`; settlements need exactly `carrier,tracking_id,currency,settlement_id,net_received`. Header order may differ. Duplicate/unknown headers and missing/extra cells are rejected. Combined files must be at most 1 MB, with the same row limits as JSON. Amounts stay decimal strings; thousands separators and comma decimals are rejected rather than guessed.

This is an adapter for **our normalized CSV schema**, not a reader for arbitrary Haravan/GHN/carrier exports. Map and review expected net and settlement meanings first. JSON results are printed locally; sample files contain synthetic data only.

## Contract

Top-level `orders` (1–500 rows), `settlements` (0–1,000 rows), optional `tolerance` (decimal string 0–1; default `"0"`). File/request limit: 1 MB. Unknown fields are rejected.

- Order: `carrier`, `tracking_id`, `currency`, `expected_net`.
- Settlement: `carrier`, `tracking_id`, `currency`, `settlement_id`, `net_received`.
- All identifiers are nonblank strings up to 100 characters, trimmed, case-sensitive. Currency must be three uppercase letters; code membership is not verified. Use stable canonical carrier identifiers. Matching uses carrier + tracking ID + currency; currencies are never converted or combined.
- Money must be decimal strings, at most 12 integer and 6 fractional digits. No commas, exponent notation, NaN or number/boolean coercion. Expected net must be nonnegative; received amounts can be negative to represent an explicit adjustment/reversal.
- **Expected net is the amount you expect to receive after reviewing applicable fees/refunds.** This tool does not infer gross COD, deduct carrier fees or parse export columns. Convert carrier files to this explicit normalized contract yourself; incorrect mapping can produce misleading comparisons.
- Unique settlement IDs are scoped to a carrier. Multiple distinct settlement rows for a shipment are summed. Repeated order keys or repeated settlement IDs make affected shipment keys `ambiguous`, with no amount comparison. IDs reused across tracking IDs/currencies block all affected keys. Historical duplicates outside the submitted batch cannot be detected.

Statuses: `matched`, `shortfall_observed`, `excess_observed`, `missing_settlement`, `orphan_settlement`, `ambiguous`. Difference is received minus expected. Missing rows mean absent from this submission, not proof of nonpayment. Shortfall can be a partial or delayed settlement, an incorrect expected amount, a fee discrepancy or missing input; it is not a finding of overdue debt or carrier fault. Tolerance is in supplied currency units and is not rounded implicitly.

## API prototype

`main.py` contains a separate FastAPI app with `POST /v1/cod/reconcile`, public `/health`, a 1 MB streamed body bound and fail-closed `X-TNT-Proxy-Secret` guard. `COD_PROXY_SECRET` comes from environment only; no example production credential is provided. Local offline OpenAPI is in `openapi.json`. No hosted URL, subscriber metrics, SLA or marketplace plan exists yet. Do not change credentials or services of existing products to use this prototype.

No bank receipt or carrier payment is verified. No automatic payment, carrier connection, accounting posting, fraud judgment or customer record modification. The result is a review aid over supplied net amounts. Credit-note expected negative net and bank/CSV parsing are unsupported.

## 4P and evidence

Product hypothesis: developers combining multiple sources could use normalized net comparison independent of a carrier platform. Haravan already documents native COD reconciliation, and GHN documents settlement exports; these are strong alternatives and problem evidence, not customer willingness to pay for this tool.

- https://help.haravan.com/docs/shipping/manage-shipping/quan-ly-thu-ho-cod-tren-don-van-chuyen/
- https://ghn.vn/blogs/tin-tuc-ghn/huong-dan-su-dung-tinh-doi-soat-cod-linh-hoat-moi

Accessed 2026-10-11; GHN article is older and does not establish current export schema. Price: free evaluation artifact, no paid plan chosen. Place: inspectable source/download, hosted channel later only after qualification. Promotion: synthetic mismatch example with explicit limitations. Next evidence needed: representative anonymized schema and a real user's unmet cross-source workflow; no interviews have been collected. No throughput/accuracy or sales claim is made.
