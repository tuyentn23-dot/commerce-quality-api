# Batch Duplicate Candidates

Check a JSON batch for exact duplicate keys before a reviewed CRM, order or ETL import. Choose one to eight scalar fields, and receive zero-based groups of record indices and indices skipped for incomplete keys. This API never deletes or merges records.

POST /v1/records/duplicate-candidates — up to 500 records and 1 MB per request.

```json
{"records":[{"order_id":" A-001 "},{"order_id":"A-001"},{"order_id":""},{"order_id":"B-002"}],"key_fields":["order_id"],"casefold":false}
```

Expected response:
```json
{"candidate_groups":[[0,1]],"candidate_record_count":2,"skipped_indices":[2],"scope":"exact_selected_keys","records_deleted":0}
```

Multiple key fields use AND matching: every selected value must match. Strings are trimmed. casefold=true enables Unicode case-insensitive string comparisons for all selected fields. Types are preserved: true, 1, 1.0 and "1" are distinct. Missing, null, empty/whitespace and object/array keys skip the record. Nested paths are unsupported: field names refer to top-level keys.

This checks only records in the submitted batch, not existing CRM data. It does not recognize fuzzy names, semantic similarities or identity. Normalize phone/email values before comparing them. Shared household numbers or role mailboxes can refer to different people; candidates require review. No deletion, merging or write-back occurs. The backend does not retain record payloads; RapidAPI may handle request data under its own policies.

Subscribe to BASIC and run the synthetic example using your own RapidAPI key. Provider proxy secrets are managed by the provider.

Published launch plans: BASIC $0 / 100 batch requests per month; PRO $4.99 / 5,000 batch requests per month, hard limits. Each request can contain up to 500 records; a record is not a request. Confirm the live pricing page before subscribing. RapidAPI displays its standard bandwidth fee separately.

Hosted on Render Free with possible cold starts and no uptime SLA. This is an initial convenience experiment for HTTP automation and import review, not an alternative to a CRM's existing record database.

[Request/response examples and workflow guide](https://commerce-quality-api.onrender.com/batch-duplicate-candidates)
