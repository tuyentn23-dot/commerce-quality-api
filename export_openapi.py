"""Export offline OpenAPI 3.0.3 specs; no real secrets or fake server URL."""
import copy
import json
from pathlib import Path
from main import app

HERE = Path(__file__).resolve().parent

def walk(value):
    if isinstance(value, list):
        return [walk(item) for item in value]
    if not isinstance(value, dict):
        return value
    value = {key: walk(item) for key, item in value.items()}
    variants = value.get('anyOf', [])
    nonnull = [item for item in variants if item.get('type') != 'null']
    if variants and len(nonnull) != len(variants):
        value.pop('anyOf')
        if len(nonnull) == 1:
            value.update(nonnull[0])
        else:
            value['anyOf'] = nonnull
        value['nullable'] = True
    for key in ('exclusiveMinimum', 'exclusiveMaximum'):
        bound = value.get(key)
        if isinstance(bound, (int, float)) and not isinstance(bound, bool):
            value['minimum' if key == 'exclusiveMinimum' else 'maximum'] = bound
            value[key] = True
    for key in ('examples', 'const', 'prefixItems', '$comment', 'jsonSchemaDialect'):
        value.pop(key, None)
    return value

spec = walk(app.openapi())
spec['openapi'] = '3.0.3'
# RapidAPI handles consumer authentication and injects the provider proxy secret.
# Declaring the proxy secret here incorrectly exposes a consumer header prompt.
for schema_name in ('InvoiceCheck', 'Line'):
    for field in spec['components']['schemas'][schema_name]['properties'].values():
        types = {variant.get('type') for variant in field.get('anyOf', [])}
        if types == {'number', 'string'}:
            field.pop('anyOf')
            field['type'] = 'string'
            field['pattern'] = r'^\d+(?:\.\d{1,6})?$'
            field['example'] = '1.00'
            if 'default' in field:
                field['default'] = str(field['default'])
invoice = spec['paths']['/v1/invoices/validate']['post']
invoice['operationId'] = 'validateInvoiceArithmetic'
invoice['summary'] = 'Validate invoice arithmetic'
invoice['requestBody']['content']['application/json']['example'] = {
    'subtotal': '100', 'tax': '10', 'shipping': '0', 'discount': '0', 'total': '110',
    'tolerance': '0.01', 'lines': [{'quantity': '2', 'unit_price': '50', 'line_total': '100'}],
}
invoice['responses']['200']['content']['application/json'] = {
    'schema': {'type': 'object', 'required': ['valid', 'expected_total', 'issues', 'scope'],
               'properties': {'valid': {'type': 'boolean'}, 'expected_total': {'type': 'string'},
                              'issues': {'type': 'array', 'items': {'type': 'object'}},
                              'scope': {'type': 'string'}}},
    'example': {'valid': True, 'expected_total': '110', 'issues': [], 'scope': 'arithmetic_only'},
}
spec['servers'] = [{'url': 'https://commerce-quality-api.onrender.com'}]
contact = spec['paths']['/v1/contacts/normalize']['post']
contact['operationId'] = 'normalizeVNContacts'
contact['summary'] = 'Normalize Vietnamese mobile shapes and email syntax'
contact['requestBody']['content']['application/json']['example'] = {'contacts': [
    {'email': 'User@EXAMPLE.COM ', 'phone': '+84 912 345 678'},
    {'email': 'bad-email', 'phone': 'abc'}, {}]}
contact['responses']['200']['content']['application/json']['example'] = {
    'count': 3, 'results': [
        {'email': 'User@example.com', 'email_syntax_valid': True, 'phone_e164': '+84912345678', 'vn_mobile_shape_valid': True, 'scope': 'syntax_only', 'deliverability_verified': False, 'ownership_verified': False},
        {'email': None, 'email_syntax_valid': False, 'phone_e164': None, 'vn_mobile_shape_valid': False, 'scope': 'syntax_only', 'deliverability_verified': False, 'ownership_verified': False},
        {'email': None, 'email_syntax_valid': None, 'phone_e164': None, 'vn_mobile_shape_valid': None, 'scope': 'syntax_only', 'deliverability_verified': False, 'ownership_verified': False}]}
duplicate = spec['paths']['/v1/records/duplicate-candidates']['post']
duplicate['operationId'] = 'findBatchDuplicateCandidates'
duplicate['summary'] = 'Find exact duplicate candidates on selected keys'
duplicate['requestBody']['content']['application/json']['example'] = {'records': [
    {'order_id': ' A-001 '}, {'order_id': 'A-001'}, {'order_id': ''}, {'order_id': 'B-002'}], 'key_fields': ['order_id'], 'casefold': False}
duplicate['responses']['200']['content']['application/json']['example'] = {
    'candidate_groups': [[0, 1]], 'candidate_record_count': 2, 'skipped_indices': [2], 'scope': 'exact_selected_keys', 'records_deleted': 0}
for suffix, path, title in [
    ('import', None, 'Commerce Data Quality API'),
    ('invoice', '/v1/invoices/validate', 'Invoice Arithmetic Validator'),
    ('contacts', '/v1/contacts/normalize', 'VN Contact Cleaner'),
    ('duplicates', '/v1/records/duplicate-candidates', 'Batch Duplicate Detector'),
]:
    output = copy.deepcopy(spec)
    output['info']['title'] = title
    if path:
        output['paths'] = {path: output['paths'][path]}
    (HERE / f'openapi.{suffix}.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
print('Exported 4 OpenAPI 3.0.3 specs')
