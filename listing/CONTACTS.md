# VN Contact Cleaner

Prepare a batch of contacts for a Vietnam CRM import. One JSON request normalizes Vietnamese mobile number shapes to +84 format and checks a conservative subset of email syntax. Results preserve input order, so results[i] refers to contacts[i].

POST /v1/contacts/normalize — up to 200 contacts and 1 MB per request.

```json
{"contacts":[{"email":"User@EXAMPLE.COM ","phone":"+84 912 345 678"},{"email":"bad-email","phone":"abc"},{}]}
```

The first result has email User@example.com and phone_e164 +84912345678. The second returns false validity flags and null normalized values; omitted fields return null validity flags, not true. Email local-part case is preserved; domain case is lowered and IDN domains are encoded. Whitespace is trimmed. Mobile prefixes 0, +84, 0084 and bare 84 are accepted when the final shape is valid. Landlines, extensions and obsolete 11-digit local mobile forms are unsupported.

This is syntax-only preflight. It does not check carrier allocation, active service, reachability, mailbox existence, deliverability, consent or ownership. It is not a full RFC email validator; quoted local parts and Unicode local parts are unsupported. Do not treat a valid shape as proof that a phone or email exists. No customer payloads are stored by this backend; RapidAPI may handle request data under its own policies.

Subscribe to BASIC and run the supplied playground example with your own RapidAPI key. A provider secret is never needed. You may test with synthetic contact data.

Proposed launch plans: BASIC $0 / 100 batch requests per month; PRO $4.99 / 5,000 batch requests per month, hard limits. A request is a batch, not a contact; up to 200 contacts in each request. Confirm the live pricing page before subscribing. RapidAPI displays its standard bandwidth fee separately.

Hosted on Render Free: cold starts are possible and there is no uptime SLA. This initial experiment offers convenience for HTTP workflows, not a guarantee of accuracy, customers or revenue.
