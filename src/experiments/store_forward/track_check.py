"""TRACK 查核原型：pseudo = 文件虛擬碼；sep = Stream/Store 分開篩選。oracle：格點 + 真正不重疊。"""
import heapq, json, random, sys, time
from fractions import Fraction as Fr
import cut_through_audit as ct
from cut_through_audit import C, I, trap, add
import interval_label_validation as v
from interval_label_validation import start_parts, buffer_filter, minus, merge, star, replay, overlap, search, backtrack, stress, Stat

class TL:
    __slots__=("c","I","pred","key","ch","store")
    def __init__(s,c,I_,pred,key,ch,store): s.c,s.I,s.pred,s.key,s.ch,s.store=c,I_,pred,key,ch,store

def search_track(P, variant, cap=20000):
    out={}
    for c in P.cs: out.setdefault(c.u,[]).append(c)
    Q=[];tick=0;reached={};pops=0
    def ins(c,parts,pred,ch,store):
        nonlocal tick
        k0=(c.id,ch); r=reached.get(k0,[])
        new=minus(parts,r); reached[k0]=merge(r+new)
        for I_ in new:
            k=I_[0]+P.S/c.r+c.d; tick+=1
            heapq.heappush(Q,(k,tick,TL(c,[I_],pred,k,ch,store)))
    for c in out.get(P.src,[]): ins(c,start_parts(P,c,P.g),None,frozenset({P.src}),False)
    while Q:
        k,_,l=heapq.heappop(Q); pops+=1
        if pops>cap: return "CAP"
        if l.c.v==P.dst: return l
        c1=l.c;d1=P.S/c1.r;n=c1.v
        lo,r=l.I[0]
        for c2 in out.get(n,[]):
            d2=P.S/c2.r
            parts=start_parts(P,c2,lo+c1.d+max(Fr(0),d1-d2))
            chS=l.ch|{n}
            C_=buffer_filter(P,parts,l.I,c1,c2,True)
            if variant=="pseudo":
                b=r+c1.d+d1
                store=[(max(x,b),y) for x,y in C_ if y>=b]
                stream=[(x,min(y,b)) for x,y in C_ if x<b]
            else:
                store=buffer_filter(P,parts,l.I,c1,c2,True,EX=d1)
                stream=minus(C_,store)
            if c2.v not in chS: ins(c2,stream,l,chS,False)
            ins(c2,store,l,frozenset({n}),True)
    return None

def back_track(P,goal):
    l=goal;s=l.I[0][0];sch=[(l.c,s)]
    while l.pred is not None:
        q=l.pred;d=P.S/q.c.r;dn=P.S/l.c.r
        ex=d if l.store else max(Fr(0),d-dn)
        k=star(q.I,s-q.c.d-ex,True)
        sch.insert(0,(q.c,k));l=q;s=k
    return sch

def oracle(P):
    out={}
    for c in P.cs: out.setdefault(c.u,[]).append(c)
    pq=[(P.g,0,P.src,None,())];t=0;seen=set()
    while pq:
        A,_,n,h,hist=heapq.heappop(pq)
        key=(n,h,A,hist)
        if key in seen: continue
        seen.add(key)
        if n==P.dst: return A
        for c in out.get(n,[]):
            d=P.S/c.r
            for s in ct.starts(P,c,h,A,True):
                h2=s+c.d;f=s+d
                H=dict(hist);H[n]=max(H.get(n,f),f)
                if c.v in H and h2<H[c.v]: continue
                nh=tuple(sorted((a,b) for a,b in H.items() if b>h2))
                t+=1;heapq.heappush(pq,(h2+d,t,c.v,h2,nh))
    return None

def loopy(rng,het):
    """偏向來回 contact，製造自我重疊。"""
    cs=[];Ns=["S","U","V","W"];i=0
    def add_c(u,v):
        nonlocal i
        a=Fr(rng.randint(0,12),2);ln=Fr(rng.randint(3,16),2)
        cs.append(C(f"c{i}",u,v,a,a+ln,Fr(rng.choice([2,4,8]) if het else 4),Fr(rng.choice([0,0,1,2,4]),4),()));i+=1
    add_c("S","U");add_c("U","V");add_c("V","U");add_c("V","W");add_c("W","U")
    for _ in range(rng.randint(1,4)):
        u=rng.choice(Ns);x=rng.choice([n for n in Ns[1:] if n!=u]);add_c(u,x)
    add_c(rng.choice(["U","V","W"]),"T")
    S_=Fr(rng.choice([2,4]));M=S_+Fr(rng.choice([0,0,1]))
    O={}
    for n in Ns[1:]:
        if rng.random()<.8: O[n]=add([trap(Fr(rng.randint(0,16),2),Fr(rng.choice([2,3,4])),Fr(rng.randint(0,6),2)) for _ in range(rng.randint(1,2))])
    return I(cs,"S","T",Fr(0),S_,M,O,Fr(18))

ALL=True
def directed(rng,het):
    """暫存緊的 U，必須靠 U-V-U 來回才趕得上晚開的 U->T，故意誘發自我重疊。"""
    r=lambda:Fr(rng.choice([2,4,8]) if het else 4)
    dl=lambda:Fr(rng.choice([0,0,1,2,4,8]),4)
    S_=Fr(rng.choice([2,4]));M=S_+Fr(rng.choice([0,0,1]))
    cs=[];i=0
    def a_(u,v,a,ln):
        nonlocal i
        cs.append(C(f"c{i}",u,v,Fr(a),Fr(a)+Fr(ln),r(),dl(),()));i+=1
    t0=rng.randint(0,4)
    a_("S","U",t0,Fr(rng.randint(4,12),2));a_("U","V",t0+Fr(rng.randint(0,4),2),Fr(rng.randint(4,14),2))
    a_("V","U",t0+Fr(rng.randint(0,8),2),Fr(rng.randint(4,14),2))
    a_("U","T",t0+Fr(rng.randint(2,14),2),Fr(rng.randint(3,12),2))
    if rng.random()<.5: a_("V","W",t0+Fr(rng.randint(0,8),2),Fr(rng.randint(4,10),2));a_("W","U",t0+Fr(rng.randint(2,12),2),Fr(rng.randint(4,10),2))
    O={"U":add([trap(Fr(t0)+Fr(rng.randint(2,12),2),M,Fr(rng.randint(0,4),2),Fr(8)) for _ in range(rng.randint(1,2))])}
    if rng.random()<.3:O["V"]=add([trap(Fr(rng.randint(0,14),2),S_,Fr(rng.randint(0,4),2),Fr(8))])
    return I(cs,"S","T",Fr(0),S_,M,O,Fr(24))

def main(n,seed,gen,grid):
    ct.GRID=grid;rng=random.Random(seed)
    R=dict(n=n,relax_feasible=0,relax_overlap=0,oracle_better_than_relax_nooverlap=0)
    for k in ("pseudo","sep"): R[k]=dict(arrival_same=0,later=0,missed=0,earlier=0,invalid=0,still_overlap=0,cap=0,cand_only=0)
    ex=[]
    for i in range(n):
        P=gen(rng,i%2==1)
        g,_,_=search(P)
        if g is None: continue
        R["relax_feasible"]+=1
        sch=backtrack(P,g)
        ov=overlap(P,sch)
        R["relax_overlap"]+=ov
        if not ov and not ALL: continue
        o=oracle(P)
        rec=dict(i=i,relax=str(g.key),oracle=str(o))
        for k in ("pseudo","sep"):
            r=R[k];t=search_track(P,k)
            if t=="CAP": r["cap"]+=1;continue
            a=t.key if t else None
            if t:
                s2=back_track(P,t)
                if not replay(P,s2): r["invalid"]+=1
                if overlap(P,s2): r["still_overlap"]+=1
            if a is None and o is None: r["arrival_same"]+=1
            elif a is None: r["missed"]+=1
            elif o is None: r["cand_only"]+=1
            elif a==o: r["arrival_same"]+=1
            elif a>o: r["later"]+=1
            else: r["earlier"]+=1
            rec[k]=str(a)
        if rec.get("pseudo")!=rec["oracle"] or rec.get("sep")!=rec["oracle"]: ex.append(rec)
    R["examples"]=ex[:12]
    return R
if __name__=="__main__":
    t=time.time()
    for name,gen,n,seed,al in (("stress",stress,int(sys.argv[1]),1,True),("loopy",loopy,int(sys.argv[1]),2,True),("directed_all",directed,int(sys.argv[1]),3,True),("directed_ovl",directed,int(sys.argv[2]),4,False)):
        ALL=al
        r=main(n,seed,gen,Fr(1,8));print(name,json.dumps(r,ensure_ascii=False),round(time.time()-t),flush=True)
