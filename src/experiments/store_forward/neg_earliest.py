import random,heapq
from fractions import Fraction as Fr
from cut_through_audit import rand,add,trap
import track_check as T,store_label as SL
from store_label import L,source_parts,start_parts,buffer_filter,minus,merge
from interval_label_validation import replay
def earliest(P):
    out={}
    for c in P.cs: out.setdefault(c.u,[]).append(c)
    Q=[];tick=0;seen={}
    def ins(c,parts,pred):
        nonlocal tick
        r=seen.get(c.id,[]);new=minus(parts,r);seen[c.id]=merge(r+new)
        for a,b in new:
            k=a+P.S/c.r+c.d;tick+=1;heapq.heappush(Q,(k,tick,L(c,[(a,a)],pred,k)))
    for c in out.get(P.src,[]): ins(c,source_parts(P,c),None)
    while Q:
        _,_,l=heapq.heappop(Q)
        if l.c.v==P.dst: return l
        d1=P.S/l.c.r
        for c2 in out.get(l.c.v,[]):
            p=start_parts(P,c2,l.I[0][0]+l.c.d+d1)
            if p: ins(c2,buffer_filter(P,p,l.I,l.c,c2,True,EX=d1),l)
    return None
R=dict(n=0,both=0,feas=0,same=0,later=0,missed=0,bad=0)
A=lambda P,l:(lambda s:s[-1][1]+P.S/s[-1][0].r+s[-1][0].d)(SL.backtrack(P,l))
for i in range(3000):
    rng=random.Random(50000+i);g=i%3
    P=rand(rng,True) if g==0 else T.loopy(rng,True) if g==1 else T.directed(rng,True)
    if rng.random()<.6: P=P._replace(O={**P.O,"S":add([trap(Fr(rng.randint(0,16),2),Fr(rng.choice([1,2,3])),Fr(rng.randint(0,6),2))])})
    a=SL.search(P);e=earliest(P);R['n']+=1
    if a is None and e is None: R['both']+=1;continue
    if e is not None and not replay(P,SL.backtrack(P,e)): R['bad']+=1
    if a is not None: R['feas']+=1
    if e is None: R['missed']+=1
    elif a is not None:
        R['same' if A(P,a)==A(P,e) else 'later']+=1
print(R)
