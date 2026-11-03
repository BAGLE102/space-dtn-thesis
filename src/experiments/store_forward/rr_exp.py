import random,heapq,time,json,sys,os
from fractions import Fraction as Fr
import interval_label_validation as v
from interval_label_validation import start_parts,buffer_filter,minus,merge,star,replay,overlap,search,backtrack,commit
from cut_through_audit import I
import track_check as T
from rr_common import load

def demand(N,seed,R=300):
    rng=random.Random(seed);D=[]
    for i in range(N):
        D.append((rng.randint(7,31),rng.randint(1,6),Fr(rng.randint(0,R))))
    D.sort(key=lambda x:x[2]);return D

# ---- SR-CGR：來源算路、收完才轉、逐包預約、選路不看節點 buffer ----
def fit(c,t,d):
    s=max(c.a,t)
    for x,y in sorted(c.F):
        if s+d<=x: break
        if s<y: s=y
    return s if s+d<=c.b else None
def cgr_dijkstra(P,out,start_node,t0,banned_c,banned_n,S):
    pq=[];best={};tick=0
    for c in out.get(start_node,[]):
        if c.id in banned_c or c.v in banned_n: continue
        d=S/c.r;s=fit(c,t0,d)
        if s is None or s+d+c.d>P.T: continue
        tick+=1;heapq.heappush(pq,(s+d+c.d,tick,c,s,None))
    while pq:
        A,_,c,s,prev=heapq.heappop(pq)
        if c.id in best: continue
        node=(c,s,prev);best[c.id]=node
        if c.v==P.dst:
            r=[];n=node
            while n: r.insert(0,(n[0],n[1]));n=n[2]
            return A,r
        seen={start_node}|banned_n;n=node
        while n: seen.add(n[0].v);n=n[2]
        for c2 in out.get(c.v,[]):
            if c2.b<A or c2.v in seen or c2.id in banned_c or c2.id in best: continue
            d=S/c2.r;s2=fit(c2,A,d)
            if s2 is None or s2+d+c2.d>P.T: continue
            tick+=1;heapq.heappush(pq,(s2+d+c2.d,tick,c2,s2,node))
    return None
def resched(P,cont,start=None):
    t=P.g;r=[]
    for c in cont:
        d=P.S/c.r;s=fit(c,t,d)
        if s is None: return None
        r.append((c,s));t=s+d+c.d
    return r
def yen(P,out,k):
    first=cgr_dijkstra(P,out,P.src,P.g,set(),set(),P.S)
    if not first: return
    A=[first];yield first[1];B=[];seen={tuple(c.id for c,_ in first[1])};tick=0
    while len(A)<k:
        last=A[-1][1]
        for i in range(len(last)):
            root=[c for c,_ in last[:i]]
            rootids=tuple(c.id for c in root)
            ban={r[i][0].id for _,r in A if tuple(c.id for c,_ in r[:i])==rootids and len(r)>i}
            pre=resched(P,root)
            if root and pre is None: continue
            n=root[-1].v if root else P.src
            t=(pre[-1][1]+P.S/root[-1].r+root[-1].d) if root else P.g
            bn={P.src}|{c.v for c in root[:-1]} if root else set()
            sp=cgr_dijkstra(P,out,n,t,ban,bn,P.S)
            if not sp: continue
            full=(pre or [])+sp[1]; ids=tuple(c.id for c,_ in full)
            if ids in seen: continue
            seen.add(ids);tick+=1;heapq.heappush(B,(sp[0],tick,full))
        if not B: return
        a,_,f=heapq.heappop(B);A.append((a,f));yield f
def srcgr(P,out,k):
    tried=0
    for r in yen(P,out,k):
        tried+=1
        if replay(P,r): return r,tried
    return None,tried
# ---- 本方法收完才轉（消融組）----
class SL:
    __slots__=("c","I","pred","key")
    def __init__(s,c,I_,pred,key): s.c,s.I,s.pred,s.key=c,I_,pred,key
def search_store(P,out):
    Q=[];tick=0;reached={}
    def ins(c,parts,pred):
        nonlocal tick
        r=reached.get(c.id,[]);new=minus(parts,r);reached[c.id]=merge(r+new)
        for I_ in new:
            k=I_[0]+P.S/c.r+c.d;tick+=1;heapq.heappush(Q,(k,tick,SL(c,[I_],pred,k)))
    for c in out.get(P.src,[]): ins(c,start_parts(P,c,P.g),None)
    while Q:
        k,_,l=heapq.heappop(Q)
        if l.c.v==P.dst:
            s=l.I[0][0];sch=[(l.c,s)];x=l
            while x.pred is not None:
                q=x.pred;w=star(q.I,s-q.c.d-P.S/q.c.r,True);sch.insert(0,(q.c,w));x=q;s=w
            return sch
        c1=l.c;d1=P.S/c1.r
        for c2 in out.get(c1.v,[]):
            parts=start_parts(P,c2,l.I[0][0]+c1.d+d1)
            if parts: ins(c2,buffer_filter(P,parts,l.I,c1,c2,True,EX=d1),l)
    return None

def ours(P):
    g,_,_=search(P)
    if g is None: return None,False
    sch=backtrack(P,g)
    if overlap(P,sch):
        t=T.search_track(P,"sep")
        if t is None or t=="CAP": return None,True
        return T.back_track(P,t),True
    return sch,False
METHODS=("ours","store","sr1","sr10")
def run_case(cs,N,seed,S,M,Tt,methods=METHODS,budget=None):
    res={}
    D=demand(N,seed)
    for m in methods:
        Fs={c.id:() for c in cs};O={};cur=list(cs)
        P0=I(cur,0,0,Fr(0),S,M,O,Tt);rows=[];t0=time.time();ov=0;bad=0;buf_peak=0;stopped=None
        P=P0
        for b,(u,w,g) in enumerate(D):
            P=P._replace(src=u,dst=w,g=g)
            out={}
            for c in P.cs: out.setdefault(c.u,[]).append(c)
            t1=time.time();tried=None
            if m=="ours": sch,ol=ours(P);ov+=ol
            elif m=="store": sch=search_store(P,out)
            elif m=="sr1": sch,tried=srcgr(P,out,1)
            else: sch,tried=srcgr(P,out,10)
            dt=time.time()-t1
            arr=None
            if sch:
                if not replay(P,sch) or overlap(P,sch): bad+=1;sch=None
            if sch:
                c,s=sch[-1];arr=s+P.S/c.r+c.d
                P=commit(P,sch)
            rows.append(dict(b=b,src=u,dst=w,g=float(g),arr=float(arr) if arr is not None else None,hops=len(sch) if sch else None,sec=round(dt,4),tried=tried))
            if budget and time.time()-t0>budget: stopped=b;break
        res[m]=dict(rows=rows,overlap=ov,invalid=bad,stopped=stopped,wall=round(time.time()-t0,2))
    return res
def summ(r):
    rows=r["rows"];ok=[x for x in rows if x["arr"] is not None]
    return dict(n=len(rows),delivered=len(ok),ratio=round(len(ok)/max(1,len(rows)),4),mean_delay=round(sum(x["arr"]-x["g"] for x in ok)/max(1,len(ok)),2),hops=round(sum(x["hops"] for x in ok)/max(1,len(ok)),2),sec=round(sum(x["sec"] for x in rows)/max(1,len(rows)),4),ov=r["overlap"],bad=r["invalid"],stop=r["stopped"],wall=r["wall"])
if __name__=="__main__":
    cs=load()
    N=int(sys.argv[1]);M=Fr(sys.argv[2]);S=Fr(sys.argv[3]);methods=sys.argv[4].split(',');budget=float(sys.argv[5])
    r=run_case(cs,N,1,S,M,Fr(86400),methods,budget)
    for m,x in r.items(): print(m,summ(x),flush=True)
