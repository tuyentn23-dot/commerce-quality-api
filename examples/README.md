# Try Invoice Validator

1. Subscribe to BASIC on [Invoice Arithmetic Validator](https://rapidapi.com/tuyentn23/api/invoice-arithmetic-validator).
2. Choose **Validate invoice arithmetic** and run the supplied example. A correct example returns `valid: true`. Change total from 110 to 120 to get a field-level mismatch.
3. For the extractor pipeline, also subscribe to [Invoice to JSON Extractor](https://rapidapi.com/tuyentn23/api/invoice-to-json-extractor1). Set your own `RAPIDAPI_KEY` in the environment.

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
