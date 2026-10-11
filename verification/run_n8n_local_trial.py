"""Run published nodes in actual n8n against a loopback synthetic-only validator.
No RapidAPI credential, customer payload, public listener or paid request.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import threading
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
QUALITY=ROOT if (ROOT/'main.py').exists() else ROOT/'products/commerce_quality'
sys.path[:0]=[str(ROOT/'.testdeps'),str(QUALITY)]
import main as quality

def run():
    x64='--x64' in sys.argv
    executable=ROOT/('.runtime/n8n-x64/node_modules/n8n/bin/n8n' if x64 else '.runtime/n8n/node_modules/n8n/bin/n8n')
    node_binary=str(ROOT/'.runtime/node-x64/node.exe') if x64 else 'node'
    if not executable.exists() or not executable.parent.parent.joinpath('package.json').exists():
        raise RuntimeError('n8n installation incomplete; do not claim actual workflow execution')
    workflow=json.loads((QUALITY/'examples/n8n_validator_trial.json').read_text(encoding='utf-8'))
    workflow['id']='TNTInvoiceSyntheticTrial'
    # Inputs are copied from the existing published Code node, not real invoices.
    fixture_inputs=json.loads((QUALITY/'examples/trial_cases.json').read_text(encoding='utf-8'))
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=10000 or self.path!='/synthetic-invoice': raise ValueError('Only bounded synthetic route is allowed')
                body=json.loads(self.rfile.read(size))
                # Require exact published synthetic payloads: no arbitrary input processing.
                allowed=[x['request'] for x in fixture_inputs['cases']]
                if body not in allowed: raise ValueError('Only existing synthetic cases accepted')
                response=quality.validate_invoice(quality.InvoiceCheck(**body))
                data=json.dumps(response).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
            except Exception:
                self.send_response(400);self.end_headers();self.wfile.write(b'{"error":"synthetic route rejected input"}')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    node=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.httpRequest')
    node['parameters']['url']=f'http://127.0.0.1:{server.server_port}/synthetic-invoice'
    node['parameters'].pop('authentication',None);node['parameters'].pop('genericAuthType',None)
    node['parameters'].pop('headerParameters',None);node['parameters']['sendHeaders']=False
    work=ROOT/'.runtime/n8n-trial';work.mkdir(parents=True,exist_ok=True)
    filename=work/'local-workflow.json';filename.write_text(json.dumps(workflow),encoding='utf-8')
    env=dict(os.environ,N8N_USER_FOLDER=str(work),N8N_DIAGNOSTICS_ENABLED='false',N8N_VERSION_NOTIFICATIONS_ENABLED='false',N8N_PERSONALIZATION_ENABLED='false')
    try:
        imported=subprocess.run([node_binary,str(executable),'import:workflow','--input',str(filename)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        if imported.returncode!=0:
            raise RuntimeError('n8n workflow import failed: '+(imported.stdout+imported.stderr)[-2000:])
        proc=subprocess.run([node_binary,str(executable),'execute','--id','TNTInvoiceSyntheticTrial','--rawOutput'],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        output=proc.stdout+proc.stderr
        items=[]
        for match in re.finditer(r'(?m)^\{',proc.stdout):
            try:
                document,_=json.JSONDecoder().raw_decode(proc.stdout[match.start():])
                runs=document['data']['resultData']['runData']['Interpret review result']
                items=[item['json'] for execution in runs for item in execution['data']['main'][0]]
                break
            except (ValueError,KeyError,TypeError):
                continue
        passed=proc.returncode==0 and len(items)==3 and all(item.get('validation')==case['expected_response'] and item.get('automatic_payment_authorized') is False and item.get('automatic_accounting_post_authorized') is False for item,case in zip(items,fixture_inputs['cases']))
        target=QUALITY/'e2e/n8n_local_trial.json'
        target.parent.mkdir(parents=True,exist_ok=True)
        report={'checked_at':datetime.now(timezone.utc).isoformat(),'exit_code':proc.returncode,'all_three_results_verified':passed,'results':items,'scope':'real n8n CLI; original published Code/HTTP nodes; loopback actual validator function, not RapidAPI gateway','rapidapi_live_verified':False,'output':output[-16000:] if not passed else 'Execution results verified; verbose migration logs omitted'}
        target.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({'exit_code':proc.returncode,'all_three_results_verified':passed,'report':str(target),'scope':report['scope']}))
        return 0 if passed else 1
    finally:
        server.shutdown();server.server_close()
if __name__=='__main__':raise SystemExit(run())
