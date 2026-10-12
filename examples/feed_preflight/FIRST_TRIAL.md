# Try two synthetic products in five minutes

1. Open https://rapidapi.com/tuyentn23/api/product-feed-preflight and choose BASIC. Use your own consumer key; never use the backend proxy or admin token.
2. Open the POST feed-preflight endpoint. Paste the JSON from `python try_feed.py --preview`, replacing the entire example body. Send one request.
3. DEMO-A should have no issues in checked scope. DEMO-B should return `gtin_check_digit` with error severity. Both outcomes are HTTP 200 because the review completed; invalid input contracts are 422.
4. For Python automation set RAPIDAPI_KEY in your own environment and run `python try_feed.py --host YOUR_LISTING_HOST`. Copy the exact X-RapidAPI-Host from this listing playground. Never put keys in source, chat or screenshots.

You can try this without a real catalog. Numeric GTIN input is refused; keep quoted strings and leading zeroes. Up to 500 rows, 1 MB, BASIC 100 batch calls/month; PRO $4.99/5,000 batch calls hard limit. Check RapidAPI pricing for platform bandwidth fees separately. Free backend can sleep; initial requests may need a retry.

This is selected identifier/duplicate review, not product ownership verification or Google approval. No automatic upload, correction, deletion or payment. A no-issues result does not prove the complete feed is valid. Duplicate candidates require review of supplied variant scope.

If the trial fails, retain HTTP status and non-sensitive issue codes, not keys or private product data. Report the blocker through the listing's provider contact. External trial success/repeat use and purchases will be measured separately; owner tests are excluded.
