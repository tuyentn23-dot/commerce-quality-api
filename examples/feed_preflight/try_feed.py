"""Synthetic first-call trial, standard library only; never prints credentials."""
import argparse,json,os,sys,re,urllib.request,urllib.error
SAMPLE={'products':[{'id':'DEMO-A','gtin':'4006381333931','country':'DE','language':'de'},{'id':'DEMO-B','gtin':'4006381333932','country':'DE','language':'de'}]}
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preview',action='store_true');p.add_argument('--host',help='X-RapidAPI-Host shown in this listing playground');a=p.parse_args(argv)
    if a.preview:print(json.dumps(SAMPLE,indent=2));return 0
    if not a.host or not re.fullmatch(r'[a-z0-9-]+\.p\.rapidapi\.com',a.host):print('Supply this listing X-RapidAPI-Host via --host.',file=sys.stderr);return 2
    key=os.environ.get('RAPIDAPI_KEY','').strip()
    if not key:print('Set RAPIDAPI_KEY to your own key and subscribe to BASIC.',file=sys.stderr);return 2
    req=urllib.request.Request('https://'+a.host+'/v1/products/feed-preflight',data=json.dumps(SAMPLE).encode(),headers={'Content-Type':'application/json','X-RapidAPI-Key':key,'X-RapidAPI-Host':a.host},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=90) as r:result=json.load(r)
    except urllib.error.HTTPError as e:print('HTTP '+str(e.code)+'; check subscription/key, quota or input. No key printed.',file=sys.stderr);return 1
    except (urllib.error.URLError,TimeoutError,ValueError):print('Request failed or returned invalid JSON; retry after free backend wakes.',file=sys.stderr);return 1
    rows=result.get('results',[]) if isinstance(result,dict) else []
    ok=len(rows)==2 and rows[0].get('status')=='no_issues_in_checked_scope' and any(x.get('code')=='gtin_check_digit' for x in rows[1].get('issues',[])) and result.get('platform_approval_verified') is False
    print(json.dumps(result,indent=2));print('Synthetic trial verified.' if ok else 'Unexpected contract: review result before using.')
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
