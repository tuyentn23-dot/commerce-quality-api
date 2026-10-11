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
spec['components'].setdefault('securitySchemes', {})['RapidAPIProxy'] = {'type': 'apiKey', 'in': 'header', 'name': 'X-RapidAPI-Proxy-Secret', 'description': 'Provider-side proxy credential. Configure at RapidAPI; consumers use their own RapidAPI key.'}
spec['security'] = [{'RapidAPIProxy': []}]
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
