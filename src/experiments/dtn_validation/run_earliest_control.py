import sys,heapq,collections,time
sys.path.insert(0,'.')
from dtn import ours,topology as tp,validate as V
from dtn.model import arrival,out_index
L=ours.Label
def earliest(P):
    out=out_index(P.cs);Q=[];tick=0;seen={}
    def ins(c,parts,pred):
        nonlocal tick
        d=seen.get(c.id,[]);new=ours.merge(ours.minus(parts,d))
        if not new:return
        seen[c.id]=ours.merge(d+new)
        for a,b in new:
            tick+=1;heapq.heappush(Q,(a+P.S/c.r+c.d,tick,L(c,a,a,pred)))
    if P.S>P.M:return None
    for c in out.get(P.src,[]):
        p=ours.source_filter(P,c,ours.candidate_range(P,c,P.g))
        if c.v==P.dst:p=ours.destination_filter(P,c,p)
        ins(c,p,None)
    while Q:
        _,_,l=heapq.heappop(Q)
        if l.c.v==P.dst:return l
        h=l.lo+l.c.d+P.S/l.c.r
        for c2 in out.get(l.c.v,[]):
            p=ours.candidate_range(P,c2,h)
            if p:
                p=ours.buffer_filter(P,p,l,c2)
                if c2.v==P.dst:p=ours.destination_filter(P,c2,p)
                ins(c2,p,l)
c=collections.Counter()
for sd in range(1,3001):
    P,bs=tp.small_case(sd)
    for u,v,g in bs:
        P=P._replace(src=u,dst=v,g=g);a=ours.search(P);e=earliest(P);c['q']+=1
        if a is None:
            c['aNone']+=1
            if e is not None:c['eOnly']+=1
        else:
            c['feas']+=1
            sa=ours.backtrack(P,a);ta=arrival(P,sa)
            if e is None:c['missed']+=1
            else:
                se=ours.backtrack(P,e);c['badE']+=not V.validate(P,se)
                te=arrival(P,se);c['same' if te==ta else ('later' if te>ta else 'earlier')]+=1
            P=V.commit(P,sa)
print(dict(c))
