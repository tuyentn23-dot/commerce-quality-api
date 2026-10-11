# Try Invoice Validator

## Validator-only n8n starter

Already have an OCR/extraction provider? Start with [n8n_validator_trial.json](n8n_validator_trial.json); it needs only the Validator BASIC subscription, not the Extractor subscription. Download the JSON and import it using n8n's **Import from File**. Create/select your own Header Auth credential with header `X-RapidAPI-Key` in **Validate arithmetic**. Never paste a key into the workflow JSON or send it to us.

One manual execution sends **three synthetic requests** and consumes three requests from your monthly quota. The final node reports one `passed` and two `mismatch` results. Mismatches request manual review; arithmetic passes continue other checks. Neither result authorizes payment or automatic accounting posting. HTTP authentication/quota/server failures stop execution rather than becoming an arithmetic result. Free hosting can cause timeouts; inspect completed nodes before repeating a run because it may consume additional requests.

Code-node inputs and result classification were executed locally against the API contract fixtures, including malformed responses. The validator-only starter was imported and executed in actual n8n 2.42.6 using a local synthetic-only endpoint on 12 October 2026. All three validation results and review flags matched the expected fixtures. For this test, only the HTTP destination/auth headers were replaced; no RapidAPI key or requests were used. Authenticated n8n execution through RapidAPI remains unverified. The separate extractor workflow has not been executed in n8n. See [n8n's HTTP Request documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/) and [workflow import documentation](https://docs.n8n.io/workflows/export-import/).

After evaluation, replace the synthetic input node with your reviewed invoice JSON and preserve required fields. Do not replace missing amounts with zero. Start with this isolated check before adding your own OCR or accounting integration.

1. Subscribe to BASIC on [Invoice Arithmetic Validator](https://rapidapi.com/tuyentn23/api/invoice-arithmetic-validator).
2. Choose **Validate invoice arithmetic** and run the supplied example. A correct example returns `valid: true`. Change total from 110 to 120 to get a field-level mismatch.
3. To try the validator alone, set your own `RAPIDAPI_KEY` in your terminal or secret manager, then run the standard-library example:

```powershell
python examples/validate_invoice.py --case correct
python examples/validate_invoice.py --case wrong-total
python examples/validate_invoice.py --case wrong-line
```

Each command sends one synthetic invoice and consumes one request from your plan. Expected results are `valid: true` with total `0.30`, a total mismatch with expected `110`, and a line mismatch with expected `16`, respectively. Use `--preview` to inspect input without a key or request. No provider secret is needed. Free hosting can have cold starts; the example allows up to 90 seconds and does not automatically send repeated requests.

For the extractor pipeline, also subscribe to [Invoice to JSON Extractor](https://rapidapi.com/tuyentn23/api/invoice-to-json-extractor1).

```powershell
python examples/extract_then_validate.py examples/sample_invoice.txt --shipping 0 --discount 0
```

Shipping and discount must be reviewed because the extractor's schema does not supply them. Missing subtotal, tax or total stops the workflow for manual review; incomplete line items are not silently replaced with zero. Arithmetic consistency is not invoice authenticity or tax compliance. Extraction can be wrong even when all extracted values add up.

## n8n / Make mapping

Use two HTTP POST steps with your key in the platform's credential manager. First request uses the extractor's generated RapidAPI example; second uses the validator's generated example.

| Validator field | Extractor field / review |
|---|---|
| subtotal | invoice.subtotal |
| tax | invoice.tax_amount |
| total | invoice.total |
| shipping | reviewed amount |
| discount | reviewed amount |
| lines[].quantity | invoice.line_items[].quantity |
| lines[].unit_price | invoice.line_items[].unit_price |
| lines[].line_total | invoice.line_items[].amount |

Insert a review branch when required fields are null. Do not automatically post invoices to accounting simply because `valid` is true.

n8n supports JSON bodies and header authentication in its [HTTP Request node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/). The example has been prepared against the documented schema; an imported n8n/Make workflow has not yet been executed.

## Importable n8n template

Import `n8n_extract_validate.json` from the n8n workflow menu. Create a **Header Auth** credential named for your own account, with header `X-RapidAPI-Key` and your key as its value. Select that credential in both HTTP Request nodes. Subscribe to BASIC on both API listings before executing.

The template is inactive and contains synthetic sample input. Review shipping and discount in **Reviewed Input** before using real invoices. **Review and map** stops when extraction is incomplete. The workflow does not write to accounting software.

JSON structure and mapping have been checked locally; execution in a real n8n installation is still unverified. UI support for workflow JSON import is described in [n8n's import guide](https://docs.n8n.io/build/manage-workflows/export-and-import.md).
