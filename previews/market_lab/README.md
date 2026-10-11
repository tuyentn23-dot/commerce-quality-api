# Five independent browser evaluation products

These are working free browser tools, not five new hosted API listings. No user input is uploaded, persisted or used for analytics. Generated HTML is served on existing free Commerce hosting. No new secret, paid service or platform subscription required. JSON report downloads are local. Builders and tests use Node built-ins only.

Run `node products/market_lab/build.cjs` then `node products/market_lab/test.cjs`. Core input is a JSON array, up to 500 rows; timezone up to 30. Browser input limit 1 MB. Individual errors preserve row index. Algorithms do not execute formulas, navigate submitted URLs or place orders.

| Product / segment | Verified problem source | Free substitute | Hypothesized benefit |
|---|---|---|---|
| GTIN / catalog imports | GS1 check digit calculator | GS1 free calculator | Batch review, retained leading zeros and JSON report |
| UTM / marketing agencies | Google Analytics campaign URL documentation | Google Campaign URL Builder | Audit existing batches rather than construct single URLs |
| CSV cell risk / reporting teams | OWASP CSV Injection | Export libraries, internal review | Identify row/column for human review, conservative flags |
| Timezone / international scheduling | Microsoft ambiguous-time documentation | Calendar/timezone libraries | Keep both UTC candidates, report nonexistent times |
| Min/max / small warehouses | Odoo reordering rules | Native ERP replenishment | Sandbox supplier pack rounding without ERP setup |

Source URLs are retained in catalog.json. Access date 2026-10-11. GS1 and Odoo facts available in search-index excerpts; direct retrieval failed (403/timeout). Google/OWASP/Microsoft full official pages retrieved. These sources establish workflow/rules, not paid demand. Interviews zero; search volume, external evaluations, retention, CAC and willingness to pay unknown.

## 4P, SWOT and experiment

Product: each has a separate job, bounded input, usable sample, human-readable scope and machine-readable result. Price: free evaluation; paid API pricing intentionally not set before repeat-use/cost qualification. Place: public website catalog, individual canonical URLs and sitemap, source kit in existing GitHub repo. Promotion: problem-specific source-backed pages, no bulk spam or additional outreach.

Strengths: local processing, no setup, bounded batches, transparent examples. Weaknesses: JSON requires normalization, no live integration, browser timezone data varies, no automatic conversion/repair. Opportunities: workflows between existing systems; entirely hypothetical until external users demonstrate need. Threats: strong free native substitutes, easy copying, low willingness to pay for narrow utility.

User explicitly requested at least five additional products on 11 October. This portfolio experiment overrides the prior preference to focus only on invoice onboarding; it does not replace financial/evidence gates. All five niches are exploratory, with no ranking by imaginary market size. Do not create paid listings just to increase count.

Seven-day observation ending 18 October: target three non-owner successful evaluations and one repeat evaluator per niche. Seek actual repeated work, current substitute and a specific benefit. These are targets, not forecast or observed counts. No input tracking is implemented: use voluntary feedback in existing provider Discussions and provider evidence for already-sold APIs; do not fabricate per-tool conversion. No additional outreach was authorized in this run. If reach is unknown, fix discoverability before inferring lack of demand. Prioritize a paid API only after meaningful unmet repeated use, representative anonymized fixtures, auth/proxy design, cost bounds and marketplace publication gates.

## Limits by product

GTIN checks syntax/checksum, not allocation, ownership or approval. String-only preserves zeros. UTM warns about case/whitespace without claiming all uppercase values are wrong. It never contacts destination or verifies analytics receipt. CSV scan takes parsed string cells, not raw CSV; separators/quoting and export/reopen behavior remain outside scope. Negative numbers can be flagged and require review. No universal safety guarantee or automatic sanitization.

Timezone accepts 2000–2035 minute precision and IANA zones supported by browser Intl. Candidate offsets sampled ±48 hours in six-hour steps; suitable for modern DST fixtures, not certified historical coverage. It refuses invalid dates and keeps ambiguous candidates. No appointment is booked. Inventory assumes same units, safe integer counts within ±100 million; forecast = on_hand + incoming − committed. Below minimum: round (maximum − forecast) up to pack multiple. May exceed maximum due to pack rounding. No demand forecast, lead-time economics, spending or supplier purchase occurs.
