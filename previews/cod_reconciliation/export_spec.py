"""Export the prototype contract offline; no hosted URL or consumer secret."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent
identifier={'type':'string','minLength':1,'maxLength':100,'pattern':r'\S'}
money={'type':'string','pattern':r'^\d{1,12}(?:\.\d{1,6})?$'}
base={'carrier':identifier,'tracking_id':identifier,'currency':{'type':'string','pattern':'^[A-Z]{3}$'}}
order={'type':'object','additionalProperties':False,'required':[*base,'expected_net'],'properties':{**base,'expected_net':money}}
settlement={'type':'object','additionalProperties':False,'required':[*base,'settlement_id','net_received'],
            'properties':{**base,'settlement_id':identifier,'net_received':{'type':'string','pattern':r'^-?\d{1,12}(?:\.\d{1,6})?$'}}}
body={'type':'object','additionalProperties':False,'required':['orders','settlements'],'properties':{
    'orders':{'type':'array','minItems':1,'maxItems':500,'items':order},
    'settlements':{'type':'array','maxItems':1000,'items':settlement},
    'tolerance':{'type':'string','default':'0','pattern':r'^(?:0(?:\.\d{1,6})?|1(?:\.0{1,6})?)$'}}}
spec={'openapi':'3.0.3','info':{'title':'COD Net Reconciliation Preview','version':'0.1.0',
    'description':'Not deployed. Caller-supplied net amount comparison; no bank or carrier verification. Max 1 MB. Provider proxy guard required for deployment; consumer authentication configured by marketplace later.'},
    'paths':{'/v1/cod/reconcile':{'post':{'operationId':'reconcileCODNetAmounts','summary':'Compare supplied COD net amounts',
        'requestBody':{'required':True,'content':{'application/json':{'schema':body,'example':json.loads((root/'sample.json').read_text())}}},
        'responses':{'200':{'description':'Comparison results; mismatches require review'},'401':{'description':'Unauthorized'},
                     '413':{'description':'Payload exceeds 1 MB'},'422':{'description':'Invalid input'},'503':{'description':'Proxy secret not configured'}}}}}}
(root/'openapi.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('Exported offline prototype contract; no hosted URL')
