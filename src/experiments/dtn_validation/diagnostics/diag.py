import sys,json,collections,statistics as st
sys.path.insert(0,'.')
from fractions import Fraction as Fr
from dtn import topology,srcgr,validate as V,ours
from dtn.model import Problem,arrival
cfg=json.load(open('config.json'))['performance']
PAR=("nodes","contacts","horizon","min_len","max_len","rates","delays")
CELLS=[("random_20n",100),("random_20n",300),("random_40n",100),("random_40n",300)]
def prob(t,seed,M,n,release=None):
    tc=cfg['topologies'][t];cs=topology.random_contacts(seed,**{k:tc[k] for k in PAR})
    b=topology.random_bundles(seed,n,tc['nodes'],release or tc['release'])
    return Problem(cs,None,None,Fr(0),Fr(1),Fr(M),{},Fr(tc['horizon'])),b
def why(P,sch):
    if not V.source_ok(P,*sch[0]):return 'source'
    for i,((a,s),(b,q)) in enumerate(zip(sch,sch[1:])):
        if not V.relay_ok(P,a,s,b,q):return 'relay'
    if not V.destination_ok(P,*sch[-1]):return 'dest'
    if not all(V.hop_ok(P,c,s) for c,s in sch):return 'hop'
    return 'other'
def occ_events(sch,g,S=Fr(1)):
    """回傳 (node, t0,v0,t1,v1) 分段線性占用，不用 Curve。"""
    seg=[]
    c0,s0=sch[0];d0=S/c0.r
    seg+= [(c0.u,g,S,s0,S),(c0.u,s0,S,s0+d0,Fr(0))]
    for (a,s),(b,q) in zip(sch,sch[1:]):
        h=s+a.d;A=h+S/a.r;f=q+S/b.r
        seg+=[(a.v,h,Fr(0),A,S),(a.v,A,S,q,S),(a.v,q,S,f,Fr(0))]
    c,s=sch[-1];h=s+c.d;A=h+S/c.r
    seg+=[(c.v,h,Fr(0),A,S)]
    return seg
def check(all_seg,M):
    by=collections.defaultdict(list)
    for x in all_seg:
        if x[3]>x[1]:by[x[0]].append(x)
    peak=Fr(0);pn={}
    for n,ss in by.items():
        ts=sorted({t for x in ss for t in(x[1],x[3])});p=Fr(0)
        for a,b in zip(ts,ts[1:]):
            for t in((a+b)/2,):
                v=sum(x[2]+(x[4]-x[2])*(t-x[1])/(x[3]-x[1]) for x in ss if x[1]<=t<x[3])
                p=max(p,v)
        pn[n]=p;peak=max(peak,p)
    return peak,pn
def run(t,n,seed,M,k,nosrc=False,release=None):
    P,b=prob(t,seed,M,n,release);c=collections.Counter();segs=[];hold=[];wsrc=[];wrel=[];hops=[]
    for u,v,g in b:
        P=P._replace(src=u,dst=v,g=g)
        if k=='ours':
            sch=ours.plan(P);r=None
        else:
            out=srcgr.out_index(P.cs);sch=None;first=None
            for rt in srcgr.k_routes(P,out,k):
                first=first or rt
                if nosrc:
                    ok=(V.destination_ok(P,*rt[-1]) and all(V.relay_ok(P,a,s,x,q) for (a,s),(x,q) in zip(rt,rt[1:])))
                else: ok=V.validate(P,rt)
                if ok:sch=rt;break
            if not first:c['noroute']+=1
            elif not sch:c['rej']+=1;c['rej_'+why(P,first)]+=1
        if sch:
            c['ok']+=1;segs+=occ_events(sch,g)
            old=P.O.get(u)
            wsrc.append(float(sch[0][1]-g));hops.append(len(sch))
            for (a,s),(x,q) in zip(sch,sch[1:]):wrel.append(float(q-(s+a.d+P.S/a.r)))
            P2=V.commit(P,sch)
            if nosrc:
                O=dict(P2.O)
                if old is None:O.pop(u,None)
                else:O[u]=old
                P2=P2._replace(O=O)
            P=P2
    return c,segs,wsrc,wrel,hops
def m(x):return round(st.mean(x),1) if x else None
out={}
print('--- k=1 rejection breakdown, M=3 and independent peak check')
for t,n in CELLS:
    A=collections.Counter();pk=0;ws=[];wr=[];ho=[];pko=0
    for s in range(1,11):
        c,seg,w1,w2,h=run(t,n,s,3,1);A.update(c);ws+=w1;wr+=w2;ho+=h
        pk=max(pk,check(seg,3)[0])
        if t=='random_20n' and n==100 and s<=3:
            c2,seg2,*_=run(t,n,s,3,'ours');pko=max(pko,check(seg2,3)[0])
    print(t,n,dict(A),'peak',float(pk),'ours peak',float(pko),'wait source',m(ws),'wait relay',m(wr),'hops',m(ho))
print('--- unconstrained k=1 (M=1e6): holding and peak bundles per node')
for t,n in CELLS:
    ws=[];wr=[];ho=[];peaks=[];over=[]
    for s in range(1,11):
        c,seg,w1,w2,h=run(t,n,s,10**6,1);ws+=w1;wr+=w2;ho+=h
        _,pn=check(seg,0);v=[float(x) for x in pn.values()]
        peaks.append(st.mean(v));over.append(sum(x>3 for x in v)/cfg['topologies'][t]['nodes'])
    print(t,n,'wait source',m(ws),'median',st.median(ws),'wait relay',m(wr),'median',st.median(wr) if wr else None,'hops',m(ho),'mean node peak',round(st.mean(peaks),2),'share nodes peak>3',round(st.mean(over),2))
print('--- M sweep k=1 delivery %')
for M in(3,4,5,6,8,10,15,30):
    print(M,[round(100*sum(run(t,n,s,M,1)[0]['ok'] for s in range(1,11))/(10*n),1) for t,n in CELLS])
print('--- source not counted, M=3, k=1');print([round(100*sum(run(t,n,s,3,1,nosrc=True)[0]['ok'] for s in range(1,11))/(10*n),1) for t,n in CELLS])
print('--- release 0-3000 instead of 600, M=3, k=1');print([round(100*sum(run(t,n,s,3,1,release=3000)[0]['ok'] for s in range(1,11))/(10*n),1) for t,n in CELLS])
