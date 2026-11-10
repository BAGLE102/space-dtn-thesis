"""同狀態比較：照本方法的提交順序重放；每包在相同狀態下跑 ours、sr1、sr10、不限 Buffer 下限。"""
import json,sys,time
sys.path.insert(0,'/home/claude/space-dtn-thesis/src/experiments/dtn_validation')
from fractions import Fraction as Fr
from dtn import topology, ours, srcgr, validate as V
from dtn.model import Problem, arrival
cfgall=json.load(open('/home/claude/space-dtn-thesis/src/experiments/dtn_validation/config.json'))['performance']
R={}
for l in open('/tmp/claude-0/-home-claude/819686f6-3cdd-509d-8e62-177447d84cb3/scratchpad/final/res2/performance.jsonl'):
    r=json.loads(l)
    if r['method']=='ours':R[(r['topology'],r['N'],r['M'],r['seed'])]=r
jobs=[(t,N,3,s) for s in (1,2,3) for t in ('random_20n','random_40n') for N in (100,300)]+[(t,N,30,s) for s in (1,2) for t in ('random_20n','random_40n') for N in (100,300)]
out=open(sys.argv[1],'a')
for (t,N,M,seed) in jobs:
    tc=cfgall['topologies'][t];params={k:tc[k] for k in ("nodes","contacts","horizon","min_len","max_len","rates","delays")}
    cs=topology.random_contacts(seed,**params);r=R[(t,N,M,seed)]
    P=Problem(cs,None,None,Fr(0),Fr(1),Fr(M),{},Fr(tc['horizon']));t0=time.time()
    for x in r['rows']:
        Pb=P._replace(src=x['src'],dst=x['dst'],g=Fr(x['g']))
        res={'topology':t,'N':N,'M':M,'seed':seed,'i':x['i'],'g':x['g'],'ours':x['arr']}
        for k in (1,10):
            sch,_=srcgr.plan(Pb,k);res['sr%d'%k]=float(arrival(Pb,sch)) if sch else None
        lb=ours.plan(Pb._replace(M=Fr(10**9)));res['lb']=float(arrival(Pb,lb)) if lb else None
        out.write(json.dumps(res)+'\n');out.flush()
        if x['arr'] is not None:
            byid={c.id:c for c in Pb.cs}
            P=V.commit(Pb,[(byid[a],Fr(str(b))) for a,b in (s.split('@') for s in x['starts'].split(';'))])
    print(t,N,M,seed,'done %.0fs'%(time.time()-t0),flush=True)
