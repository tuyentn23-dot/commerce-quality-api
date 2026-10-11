"""Generate an inactive validator-only trial; no stored credentials."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
cases = json.loads((HERE / 'trial_cases.json').read_text(encoding='utf-8'))['cases']
inputs = [{'case_name': c['name'], 'invoice_check': c['request']} for c in cases]
input_code = 'return ' + json.dumps(inputs) + '.map(value => ({json:value}));'
review_code = '''if (typeof $json.valid !== 'boolean' || $json.scope !== 'arithmetic_only' || !Array.isArray($json.issues)) {
  throw new Error('Unexpected validator response: stop for manual review');
}
if (($json.valid && $json.issues.length !== 0) || (!$json.valid && $json.issues.length === 0)) {
  throw new Error('Inconsistent validator response: stop for manual review');
}
return [{json: {
  arithmetic_status: $json.valid ? 'passed' : 'mismatch',
  next_step: $json.valid ? 'continue_other_checks' : 'manual_review_required',
  automatic_payment_authorized: false,
  automatic_accounting_post_authorized: false,
  validation: $json
}}];'''
nodes = [
    {'id':'start','name':'Run three synthetic checks','type':'n8n-nodes-base.manualTrigger','typeVersion':1,'position':[0,0],'parameters':{}},
    {'id':'cases','name':'Synthetic invoice cases','type':'n8n-nodes-base.code','typeVersion':2,'position':[240,0],'parameters':{'jsCode':input_code}},
    {'id':'validate','name':'Validate arithmetic','type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[480,0],'parameters':{
        'method':'POST','url':'https://invoice-arithmetic-validator.p.rapidapi.com/v1/invoices/validate',
        'authentication':'genericCredentialType','genericAuthType':'httpHeaderAuth',
        'sendHeaders':True,'headerParameters':{'parameters':[{'name':'X-RapidAPI-Host','value':'invoice-arithmetic-validator.p.rapidapi.com'}]},
        'sendBody':True,'specifyBody':'json','jsonBody':'={{ JSON.stringify($json.invoice_check) }}','options':{'timeout':90000}}},
    {'id':'review','name':'Interpret review result','type':'n8n-nodes-base.code','typeVersion':2,'position':[720,0],
     'parameters':{'mode':'runOnceForEachItem','jsCode':review_code.replace('return [{json:', 'return {json:').replace('}}];','}};')}},
]
connections = {a['name']:{'main':[[{'node':b['name'],'type':'main','index':0}]]} for a,b in zip(nodes,nodes[1:])}
workflow = {'name':'Invoice arithmetic review — three synthetic checks (RapidAPI)', 'nodes':nodes,'connections':connections,
            'active':False,'settings':{'executionOrder':'v1'},'pinData':{}}
(HERE/'n8n_validator_trial.json').write_text(json.dumps(workflow,indent=2),encoding='utf-8')
print('Generated validator-only trial, inactive, no credentials; one run uses three API requests')
