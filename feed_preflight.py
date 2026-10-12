"""Bounded, deterministic pre-import review; no external lookups or uploads."""
import re
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr

class ProductRow(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: StrictStr = Field(min_length=1, max_length=200)
    gtin: StrictStr = Field(default='', max_length=200)
    gtin_assigned: StrictBool | None = None
    brand: StrictStr = Field(default='', max_length=200)
    mpn: StrictStr = Field(default='', max_length=200)
    country: StrictStr = Field(default='', max_length=2, pattern=r'^(?:[A-Z]{2})?$')
    language: StrictStr = Field(default='', max_length=35, pattern=r'^(?:[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*)?$')
    condition: StrictStr = Field(default='', max_length=200)
    multipack: StrictStr = Field(default='', max_length=200)
    color: StrictStr = Field(default='', max_length=200)
    size: StrictStr = Field(default='', max_length=200)

class FeedBatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    products: list[ProductRow] = Field(min_length=1, max_length=500)

def review_feed(body: FeedBatch):
    results=[]; keys={}; ids={}
    for index,r in enumerate(body.products):
        issues=[]
        def add(code, severity='warning'): issues.append({'code':code,'severity':severity})
        if not r.id.strip(): add('blank_id','error')
        if r.id in ids:
            add('duplicate_id','error')
            results[ids[r.id]]['issues'].append({'code':'duplicate_id','severity':'error'})
        else: ids[r.id]=index
        g=r.gtin.replace(' ','').replace('-','')
        shape=bool(re.fullmatch(r'(?:[0-9]{8}|[0-9]{12}|[0-9]{13}|[0-9]{14})',g))
        if g:
            if not shape: add('gtin_format','error')
            else:
                check=(10-sum(int(c)*(3 if i%2==0 else 1) for i,c in enumerate(g[-2::-1]))%10)%10
                if check!=int(g[-1]): add('gtin_check_digit','error')
                if len(g)==8: add('gtin8_prefix_not_reviewed')
                else:
                    prefix=g.zfill(14)[1:3]
                    if prefix in ('02','04') or prefix.startswith('2'): add('google_restricted_prefix_review')
                    if prefix in ('05','98','99'): add('google_coupon_prefix_review')
            if r.gtin_assigned is False: add('gtin_present_but_declared_unassigned')
        elif r.gtin_assigned is True: add('assigned_gtin_missing','error')
        elif r.gtin_assigned is None: add('gtin_assignment_unknown')
        if not g and (not r.brand.strip() or not r.mpn.strip()): add('review_missing_brand_or_mpn')
        if not r.country or not r.language: add('duplicate_scope_incomplete')
        row={'index':index,'id':r.id,'normalized_gtin':g or None,'issues':issues}
        if shape and r.country and r.language:
            key=(g.zfill(14),r.country,r.language.lower(),r.condition,r.multipack,r.color,r.size)
            if key in keys:
                prior=keys[key];add('duplicate_gtin_variant_candidate');row['duplicate_of_index']=prior
                if not any(x['code']=='duplicate_gtin_variant_candidate' for x in results[prior]['issues']):
                    results[prior]['issues'].append({'code':'duplicate_gtin_variant_candidate','severity':'warning'})
            else: keys[key]=index
        results.append(row)
    for r in results: r['status']='errors' if any(i['severity']=='error' for i in r['issues']) else 'review' if r['issues'] else 'no_issues_in_checked_scope'
    return {'ruleset':'feed-preflight-0.2','count':len(results),'results':results,'platform_approval_verified':False,'gtin_assignment_verified':False,'scope':'Selected GTIN and exact supplied variant rules; not full feed validation; GTIN-8 prefixes not reviewed'}
