import sys,json
sys.path.insert(0,'.')
from fractions import Fraction as Fr
from dtn import topology,srcgr,validate as V
from dtn.model import Problem
cfg=json.load(open('config.json'))['performance']
PAR=("nodes","contacts","horizon","min_len","max_len","rates","delays")
CELLS=[("random_20n",100),("random_20n",300),("random_40n",100),("random_40n",300)]
def latest(c,ub,S):
    d=S/c.r;s=min(ub,c.b-d)
    for x,y in sorted(c.F,reverse=True):
        if s>=y:break
        if s+d>x:s=x-d
    return s if s>=c.a else None
def alap(P,r):
    out=[r[-1]];s=r[-1][1]
    for c,_ in reversed(r[:-1]):
        q=latest(c,s-c.d-P.S/c.r,P.S)
        if q is None:return None
        out.insert(0,(c,q));s=q
    return out if s>=P.g else None
for k in(1,10):
  for mode in('asap','alap'):
    res=[]
    for t,n in CELLS:
        ok=0
        for seed in range(1,11):
            tc=cfg['topologies'][t];cs=topology.random_contacts(seed,**{x:tc[x] for x in PAR});b=topology.random_bundles(seed,n,tc['nodes'],tc['release'])
            P=Problem(cs,None,None,Fr(0),Fr(1),Fr(3),{},Fr(tc['horizon']))
            for u,v,g in b:
                P=P._replace(src=u,dst=v,g=g);sch=None
                for r in srcgr.k_routes(P,srcgr.out_index(P.cs),k):
                    if V.validate(P,r):sch=r;break
                    if mode=='alap':
                        z=alap(P,r)
                        if z and V.validate(P,z):sch=z;break
                if sch:ok+=1;P=V.commit(P,sch)
        res.append(round(100*ok/(10*n),1))
    print('k',k,mode,res,flush=True)
