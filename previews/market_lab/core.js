'use strict';
function runTool(kind, rows) {
  if(!Array.isArray(rows)||rows.length<1||rows.length>(kind==='timezone'?30:500))throw Error('Cần mảng 1–500 dòng; múi giờ tối đa 30 dòng.');
  const str=(x,max=2000)=>{if(typeof x!=='string'||x.length>max)throw Error('Trường văn bản không hợp lệ.');return x;};
  const int=x=>{if(!Number.isSafeInteger(x)||Math.abs(x)>100000000)throw Error('Số lượng phải là số nguyên trong ±100 triệu.');return x;};
  return rows.map((r,index)=>{try{
    if(kind==='gtin'){
      const code=str(r,14);if(!/^(?:\d{8}|\d{12}|\d{13}|\d{14})$/.test(code))throw Error('GTIN phải là chuỗi 8/12/13/14 chữ số.');
      let sum=0;for(let i=code.length-2,n=0;i>=0;i--,n++)sum+=Number(code[i])*(n%2?1:3);
      const expected=String((10-sum%10)%10);
      return {index,code,checksum_matches:code.at(-1)===expected,expected_check_digit:expected,allocation_verified:false};
    }
    if(kind==='utm'){
      const raw=str(r);const u=new URL(raw);if(!['https:','http:'].includes(u.protocol)||u.username||u.password)throw Error('Chỉ nhận URL HTTP(S) không chứa tài khoản.');
      const issues=[];for(const key of ['utm_source','utm_medium','utm_campaign']){const values=u.searchParams.getAll(key);if(!values.length||values.some(v=>!v.trim()))issues.push('missing_or_empty:'+key);if(values.length>1)issues.push('duplicate:'+key);}
      for(const [k,v] of u.searchParams){if(k.toLowerCase().startsWith('utm_')&&k!==k.toLowerCase())issues.push('parameter_case:'+k);if(k.startsWith('utm_')&&(v!==v.trim()||v!==v.toLowerCase()))issues.push('review_value_case_or_spaces:'+k);}
      if(u.hash.includes('utm_'))issues.push('utm_in_fragment');
      return {index,url:raw,issues,tracking_delivery_verified:false};
    }
    if(kind==='csv-risk'){
      if(!Array.isArray(r)||r.length>100)throw Error('Mỗi dòng là mảng tối đa 100 ô văn bản.');
      const risks=[];r.forEach((v,column)=>{str(v,10000);if(/^[\t\r\n]/.test(v)||/^[\s\uFEFF]*[=+@\-＝＋＠－]/u.test(v))risks.push({column,reason:'potential_formula_prefix'});});
      return {index,flagged_cells:risks,scan_scope:'parsed_cells_only',spreadsheet_safety_guaranteed:false};
    }
    if(kind==='reorder'){
      if(!r||typeof r!=='object'||Array.isArray(r))throw Error('Dòng phải là đối tượng.');
      const sku=str(r.sku,100);if(!sku.trim())throw Error('Thiếu SKU.');
      const on=int(r.on_hand),incoming=int(r.incoming),out=int(r.committed),min=int(r.minimum),max=int(r.maximum),pack=int(r.pack);
      if(incoming<0||out<0||min<0||max<min||pack<1)throw Error('Quy tắc min/max/pack không hợp lệ.');
      const forecast=on+incoming-out,quantity=forecast<min?Math.ceil((max-forecast)/pack)*pack:0;
      return {index,sku,forecast,proposed_quantity:quantity,above_max_after_pack:quantity>0&&forecast+quantity>max,automatic_order_created:false,scope:'supplied_counts_no_demand_forecast'};
    }
    if(kind==='timezone'){
      const local=str(r.local,16),zone=str(r.zone,100);
      if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(local))throw Error('Giờ dạng YYYY-MM-DDTHH:mm.');
      const [y,m,d,h,mi]=local.match(/\d+/g).map(Number);if(y<2000||y>2035)throw Error('Chỉ hỗ trợ 2000–2035.');
      const wall=Date.UTC(y,m-1,d,h,mi);if(new Date(wall).toISOString().slice(0,16)!==local)throw Error('Ngày hoặc giờ không tồn tại.');
      const f=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
      const parts=t=>Object.fromEntries(f.formatToParts(new Date(t)).filter(x=>x.type!=='literal').map(x=>[x.type,x.value]));
      const offsets=new Set();for(let step=-48;step<=48;step+=6){const t=wall+step*3600000,p=parts(t);offsets.add(Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute)-t);}
      const matches=[];for(const off of offsets){const t=wall-off,p=parts(t);if(`${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`===local)matches.push(new Date(t).toISOString());}
      matches.sort();return {index,local,zone,status:matches.length===0?'nonexistent':matches.length>1?'ambiguous':'unique',utc_candidates:matches,time_zone_rules:'browser Intl; sample offsets; not historical certification'};
    }
    throw Error('Sản phẩm không tồn tại.');
  }catch(e){return {index,error:e.message};}});
}
if(typeof module!=='undefined')module.exports={runTool};
