"""Generate an importable n8n example without keys or credential IDs."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
mapper = '''const invoice = $json.invoice;
if (!$json.success || !invoice) throw new Error('Extraction failed: manual review required');
for (const field of ['subtotal', 'tax_amount', 'total']) {
  if (invoice[field] === null || invoice[field] === undefined) throw new Error('Missing ' + field + ': manual review required');
}
const reviewed = $('Reviewed Input').first().json;
const lines = (invoice.line_items || []).map((line, i) => {
  for (const field of ['quantity', 'unit_price', 'amount']) {
    if (line[field] === null || line[field] === undefined) throw new Error('Incomplete line ' + i + ': manual review required');
  }
  return {quantity: String(line.quantity), unit_price: String(line.unit_price), line_total: String(line.amount)};
});
return [{json: {subtotal: String(invoice.subtotal), tax: String(invoice.tax_amount), total: String(invoice.total), shipping: reviewed.shipping, discount: reviewed.discount, tolerance: '0.01', lines}}];'''

nodes = [
    {'id': 'start', 'name': 'Run sample', 'type': 'n8n-nodes-base.manualTrigger', 'typeVersion': 1, 'position': [0, 0], 'parameters': {}},
    {'id': 'input', 'name': 'Reviewed Input', 'type': 'n8n-nodes-base.code', 'typeVersion': 2, 'position': [240, 0], 'parameters': {'jsCode': "return [{json:{content:'Invoice #: SAMPLE-001\\nVendor: Example Supplies\\nSubtotal: 100.00\\nVAT: 10.00\\nTotal: 110.00 USD',shipping:'0',discount:'0'}}];"}},
    {'id': 'extract', 'name': 'Extract invoice', 'type': 'n8n-nodes-base.httpRequest', 'typeVersion': 4.2, 'position': [480, 0], 'parameters': {
        'method': 'POST', 'url': 'https://invoice-to-json-extractor1.p.rapidapi.com/v1/invoice/extract',
        'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth',
        'sendHeaders': True, 'headerParameters': {'parameters': [{'name': 'X-RapidAPI-Host', 'value': 'invoice-to-json-extractor1.p.rapidapi.com'}]},
        'sendBody': True, 'specifyBody': 'json', 'jsonBody': '={{ JSON.stringify({content:$json.content}) }}', 'options': {'timeout': 90000}}},
    {'id': 'map', 'name': 'Review and map', 'type': 'n8n-nodes-base.code', 'typeVersion': 2, 'position': [720, 0], 'parameters': {'jsCode': mapper}},
    {'id': 'validate', 'name': 'Validate arithmetic', 'type': 'n8n-nodes-base.httpRequest', 'typeVersion': 4.2, 'position': [960, 0], 'parameters': {
        'method': 'POST', 'url': 'https://invoice-arithmetic-validator.p.rapidapi.com/v1/invoices/validate',
        'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth',
        'sendHeaders': True, 'headerParameters': {'parameters': [{'name': 'X-RapidAPI-Host', 'value': 'invoice-arithmetic-validator.p.rapidapi.com'}]},
        'sendBody': True, 'specifyBody': 'json', 'jsonBody': '={{ JSON.stringify($json) }}', 'options': {'timeout': 90000}}},
]
connections = {a['name']: {'main': [[{'node': b['name'], 'type': 'main', 'index': 0}]]} for a, b in zip(nodes, nodes[1:])}
workflow = {'name': 'Extract invoice then validate arithmetic (RapidAPI)', 'nodes': nodes, 'connections': connections,
            'active': False, 'settings': {'executionOrder': 'v1'}, 'pinData': {}}
(HERE / 'n8n_extract_validate.json').write_text(json.dumps(workflow, indent=2), encoding='utf-8')
print('Generated inactive n8n template with no credentials')
