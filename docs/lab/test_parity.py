"""Compare the browser engine with the repository's Python evaluator."""
import sys,json,copy,random,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
sys.path.insert(0,str(ROOT))
from evaluator import evaluate,_unique_object
c=json.loads((ROOT/'examples/cases.json').read_text(encoding='utf-8'))
p=json.loads((ROOT/'examples/predictions.json').read_text(encoding='utf-8'))
bad=json.loads((ROOT/'examples/rejected-predictions.json').read_text(encoding='utf-8'))
sc=[]
def add(name,cases=c,pred=p,t=1,raw=False):
 sc.append({'name':name,'c':cases if raw else json.dumps(cases,ensure_ascii=True),'p':pred if raw else json.dumps(pred,ensure_ascii=True),'t':t})
add('accepted');add('critical',pred=bad);add('critical at zero',pred=bad,t=0)
for label in ['missing','wrong','actions type','duplicate actions','evidence missing','evidence duplicate','extra evidence','nonobject','bool decision','forbidden sorted']:
 q=copy.deepcopy(p);k='permissions-01';v=q[k]
 if label=='missing':del q[k]
 elif label=='wrong':v['decision']='allow'
 elif label=='actions type':v['actions']='log_denial'
 elif label=='duplicate actions':v['actions']=['log_denial']*2
 elif label=='evidence missing':v['evidence']=[]
 elif label=='evidence duplicate':v['evidence']=['policy-01']*2
 elif label=='extra evidence':v['evidence']+=['extra']
 elif label=='nonobject':q[k]=False
 elif label=='bool decision':v['decision']=True
 elif label=='forbidden sorted':v['actions']=['z','é','a','😀','\ue000']
 add(label,pred=q,t=0)
for t in [0,0.5,2/3,0.67,1]:
 q=copy.deepcopy(p);q['research-01']['decision']='approve';add('threshold '+str(t),pred=q,t=t)
for label in ['duplicate id','empty','not array','not object','blank id','blank decision','invalid allowed','duplicate allowed','required duplicate','critical string','critical number','critical null','required null','missing field']:
 q=copy.deepcopy(c)
 if label=='duplicate id':q.append(q[0])
 elif label=='empty':q=[]
 elif label=='not array':q={}
 elif label=='not object':q[0]=[]
 elif label=='blank id':q[0]['id']='\u0085\u001c'
 elif label=='blank decision':q[0]['expected_decision']=' '
 elif label=='invalid allowed':q[0]['allowed_actions']=[1]
 elif label=='duplicate allowed':q[0]['allowed_actions']=['x','x']
 elif label=='required duplicate':q[0]['required_evidence']=['x','x']
 elif label=='critical string':q[0]['critical']='false'
 elif label=='critical number':q[0]['critical']=1
 elif label=='critical null':q[0]['critical']=None
 elif label=='required null':q[0]['required_evidence']=None
 elif label=='missing field':del q[0]['allowed_actions']
 add(label,cases=q)
add('unexpected',pred=dict(p,unknown={}));add('invalid prediction root',pred=[]);add('blank prediction ID',pred={' ': {}})
for k in ['__proto__','constructor','toString','1','café','😀','\ufeff','\u200b']:
 add('special key '+k,cases=[{'id':k,'expected_decision':'ok','allowed_actions':[]}],pred={k:{'decision':'ok','actions':[],'evidence':[]}})
for text in ['{"x":1,"x":2}','{"x":1,"\\u0078":2}','{"meta":{"x":1,"x":2}}','{"__proto__":1,"__proto__":2}','{','{"x":01}','[1,]','{"x":true,}','{"x":"\\q"}']:
 add('raw '+text,cases=json.dumps(c),pred=text,raw=True)
for t in [-0.1,1.1]:add('invalid threshold',t=t)
rng=random.Random(20261124)
for i in range(200):
 q=copy.deepcopy(p);cc=copy.deepcopy(c)
 for v in q.values():
  if rng.random()<.4:v['decision']=rng.choice(['deny','abstain','request_review',None,True,5])
  if rng.random()<.4:v['actions']=rng.choice([[],['log_denial'],['x','x'],['z','a'],False,[None]])
  if rng.random()<.4:v['evidence']=rng.choice([[],['source-01'],['policy-01','policy-01'],['policy-01'],None,[2]])
 if rng.random()<.2:q['other']={}
 if rng.random()<.2:q.pop('research-01',None)
 if rng.random()<.2:rng.shuffle(cc)
 add(f'seeded {i}',cc,q,rng.choice([0,0.4,2/3,0.67,1]))
js=subprocess.run(['node','-e',"const fs=require('fs'),E=require('./engine.js');const a=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(a.map(s=>E.run(s.c,s.p,s.t))))"],cwd=P,input=json.dumps(sc),encoding='utf-8',capture_output=True,check=True);out=json.loads(js.stdout)
assert len(out)==len(sc), (len(out),len(sc))
for x,y in zip(sc,out):
 try:
  if not 0<=x['t']<=1:raise ValueError('minimum pass rate must be between 0 and 1')
  r=evaluate(json.loads(x['c'],object_pairs_hook=_unique_object),json.loads(x['p'],object_pairs_hook=_unique_object));r['minimum_pass_rate']=x['t'];r['accepted']=r['gate_passed'] and r['pass_rate']>=x['t'];assert y=={'exit':0 if r['accepted'] else 1,'report':r},(x['name'],y,r)
 except ValueError as e:
  assert y['exit']==2,(x['name'],y,e)
  if not isinstance(e,json.JSONDecodeError):assert y['error']==str(e),(x['name'],y,e)
print(f'{len(sc)}/{len(sc)} parity scenarios passed against the repository evaluator')
# Each restriction must fail for its own reason, not a separate invalid fixture.
controls=[('standard JSON NaN',json.dumps(c),'{{"x":NaN}}'.replace('{{','{').replace('}}','}'),'Invalid standard JSON'),('standard JSON Infinity',json.dumps(c),'{{"x":Infinity}}'.replace('{{','{').replace('}}','}'),'Invalid standard JSON'),('depth',json.dumps(c),'['*66+'0'+']'*66,'64 nesting levels'),('length',json.dumps(c),' '*100001,'100,000 characters'),('case count',json.dumps([dict(c[0],id=str(i)) for i in range(201)]),json.dumps(p),'200 cases')]
for name,ca,pr,diagnostic in controls:
 r=subprocess.run(['node','-e',"const e=require('./engine.js');const a=JSON.parse(require('fs').readFileSync(0,'utf8'));console.log(JSON.stringify(e.run(a[0],a[1],1)))"],cwd=P,input=json.dumps([ca,pr]),encoding='utf-8',capture_output=True,check=True)
 result=json.loads(r.stdout);assert result['exit']==2 and diagnostic in result['error'],(name,result)
print('5/5 deliberate browser-only restrictions passed with specific diagnostics')
