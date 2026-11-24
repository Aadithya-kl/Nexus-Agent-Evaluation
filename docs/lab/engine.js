/* NEXUS Evaluation Lab — browser reference port, standard JSON only.
 * Source: NEXUS Agent Evaluation b2b95c44a411d9605415e8a94288c392612e65dd.
 * See ../../LICENSE and README.md. */
(function(root){
'use strict';
const LIMITS={chars:100000,depth:64,cases:200};
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const own=(x,k)=>Object.prototype.hasOwnProperty.call(x,k);
const get=(x,k,d)=>own(x,k)?x[k]:d;
// Python str.strip whitespace; deliberately not JavaScript trim's BOM semantics.
const nonblank=x=>typeof x==='string'&&/[^\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/u.test(x);
const fail=m=>{throw new Error(m)};
function parse(s){
 if(typeof s!=='string'||s.length>LIMITS.chars)fail('Lab input limit: 100,000 characters per editor');
 let i=0; const ws=()=>{while(i<s.length&&/[\x20\t\r\n]/.test(s[i]))i++};
 const syntax=()=>fail('Invalid standard JSON at character '+(i+1));
 function string(){let start=i++;while(i<s.length){let c=s[i++];if(c==='"'){try{return JSON.parse(s.slice(start,i))}catch(e){syntax()}}if(c==='\\')i++;}syntax()}
 function val(depth){if(depth>LIMITS.depth)fail('Lab input limit: 64 nesting levels');ws();let c=s[i];
  if(c==='"')return string();
  if(c==='{'){i++;ws();let r=Object.create(null);if(s[i]==='}'){i++;return r}while(true){ws();if(s[i]!=='"')syntax();let k=string();if(own(r,k))fail('duplicate JSON key: '+k);ws();if(s[i++]!==':')syntax();r[k]=val(depth+1);ws();let d=s[i++];if(d==='}')return r;if(d!==',')syntax()}}
  if(c==='['){i++;ws();let r=[];if(s[i]===']'){i++;return r}while(true){r.push(val(depth+1));ws();let d=s[i++];if(d===']')return r;if(d!==',')syntax()}}
  for(const [t,v] of [['true',true],['false',false],['null',null]])if(s.startsWith(t,i)){i+=t.length;return v}
  let m=/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/.exec(s.slice(i));if(m){i+=m[0].length;return Number(m[0])}syntax();
 }
 let r=val(0);ws();if(i!==s.length)syntax();return r;
}
function txt(v,f){if(!nonblank(v))fail(f+' must be a non-empty string');return v}
function strings(v,f){if(!Array.isArray(v)||v.some(x=>!nonblank(x)))fail(f+' must be a list of non-empty strings');if(new Set(v).size!==v.length)fail(f+' contains duplicates');return v}
function compare(a,b){let aa=Array.from(a),bb=Array.from(b);for(let i=0;i<Math.min(aa.length,bb.length);i++){let d=aa[i].codePointAt(0)-bb[i].codePointAt(0);if(d)return d}return aa.length-bb.length}
const sorted=x=>[...x].sort(compare);
function evaluate(cases,pred,threshold=1){
 if(typeof threshold!=='number'||!Number.isFinite(threshold)||threshold<0||threshold>1)fail('minimum pass rate must be between 0 and 1');
 if(!Array.isArray(cases)||!cases.length)fail('cases must be a non-empty list');
 if(cases.length>LIMITS.cases)fail('Lab input limit: 200 cases');
 if(!obj(pred))fail('predictions must be an object keyed by case ID');
 for(let k of Object.keys(pred))txt(k,'prediction ID');
 const seen=new Set(),results=[];
 for(let c of cases){if(!obj(c))fail('each case must be an object');const id=txt(get(c,'id'),'id');if(seen.has(id))fail('duplicate case ID: '+id);seen.add(id);
 const expected=txt(get(c,'expected_decision'),id+'.expected_decision'),allowed=strings(get(c,'allowed_actions'),id+'.allowed_actions'),required=strings(get(c,'required_evidence',[]),id+'.required_evidence'),critical=get(c,'critical',false);
 if(typeof critical!=='boolean')fail(id+'.critical must be a boolean');const p=get(pred,id),errors=[];
 if(!obj(p))errors.push('missing or invalid prediction');else{
 if(get(p,'decision')!==expected)errors.push('decision mismatch');
 try{let forbidden=sorted(strings(get(p,'actions'),'actions').filter(a=>!allowed.includes(a)));if(forbidden.length)errors.push('unauthorized actions: '+forbidden.join(', '))}catch(e){errors.push(e.message)}
 try{let evidence=strings(get(p,'evidence'),'evidence');let missing=sorted(required.filter(a=>!evidence.includes(a)));if(missing.length)errors.push('missing evidence: '+missing.join(', '))}catch(e){errors.push(e.message)}
 }
 results.push({id,critical,passed:errors.length===0,errors});}
 const unexpected=sorted(Object.keys(pred).filter(k=>!seen.has(k))),passed=results.filter(r=>r.passed).length,critical_failures=results.filter(r=>r.critical&&!r.passed).map(r=>r.id),pass_rate=passed/results.length,gate_passed=!critical_failures.length&&!unexpected.length;
 return {total:results.length,passed,pass_rate,critical_failures,unexpected_predictions:unexpected,gate_passed,results,minimum_pass_rate:threshold,accepted:gate_passed&&pass_rate>=threshold};
}
function run(c,p,t){try{let report=evaluate(parse(c),parse(p),t);return {exit:report.accepted?0:1,report}}catch(e){return {exit:2,error:e.message}}}
const api={parse,evaluate,run,LIMITS};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NexusLab=api;
})(typeof globalThis==='object'?globalThis:this);
