# Product Feed Preflight API

Review a batch of product identifiers before catalog import. Detect invalid GTIN shapes/check digits, missing GTINs declared assigned, duplicate product IDs and exact GTIN/variant candidates within supplied country/language scope.

POST `/v1/products/feed-preflight`, JSON `{"products":[{"id":"DEMO-A","gtin":"4006381333931","country":"DE","language":"de","condition":"new"}]}`.

Results preserve row indices and return issue codes, warning/error severity and review status. `no_issues_in_checked_scope` is not Google approval. Numeric GTIN inputs are rejected to preserve leading zeros. 1–500 products, 1 MB payload, 200 characters per text field. Country is uppercase two-letter shape and language follows documented tag shape; no country/language registry lookup. GTIN-8 prefix review is explicitly unsupported. Restricted/coupon prefix findings are review warnings, not authoritative eligibility decisions. Exact supplied variants can produce false-positive duplicate candidates when fields are omitted. `gtin_assigned` is caller declaration, never verified ownership.

No external lookup, uploads, automatic corrections, deletions or storage of payloads. No GS1 allocation/ownership verification, Google affiliation, full feed validation or guarantee of acceptance. Price/availability/images/links and category-specific policy are outside scope.

Pricing hypothesis: BASIC free 100 batch requests/month, PRO $4.99/month 5,000 batches hard limit. Each request counts one batch regardless of row count. At full PRO usage gross is $0.000998/batch, $3.7425/month after a 25% marketplace fee assumption, before processing/support/tax/hosting. This is not realized profit. Worst case 2.5 million rows/month per full-quota subscriber; deterministic linear processing, no paid upstream dependencies. Free Render can sleep; no uptime SLA. Price is a test, willingness-to-pay unverified.

Alternatives: Merchant Center diagnostics, GS1 check-digit calculator and local libraries. Differentiation hypothesis: structured, row-indexed pre-import batch review callable from automation. Evidence of task: Google GTIN documentation; this is desk research, not a customer survey.

Sources read 12/10/2026: https://support.google.com/merchants/answer/6324461?hl=en and https://support.google.com/merchants/answer/6324507?hl=en . Direct GS1 pages returned 403; no claim of freshly inspected complete GS1 specification.
