import sys,json,time,os,signal
class TO(Exception):pass
def _al(*a): raise TO()
from fractions import Fraction as Fr
from multiprocessing import Pool
import rr_exp as X
from rr_exp import *
import topo
import store_label as SL
def with_ub(P,out):
    r,_=X.srcgr(P,out,1)
    if r:
        c,s=r[-1];return P._replace(T=s+P.S/c.r+c.d)
    return P
def one(job):
    tp,N,seed,M,m,budget=job
    t=topo.TOPO[tp];cs=t["c"](seed);D=t["d"](N,seed);S=t["S"]
    P=I(cs,0,0,Fr(0),S,Fr(M),{},Fr(t["T"]));rows=[];t0=time.time();ov=bad=cap=0;stop=None
    signal.signal(signal.SIGALRM,_al);signal.alarm(int(budget))
    try:
     for b,(u,w,g) in enumerate(D):
        P=P._replace(src=u,dst=w,g=g)
        out={}
        for c in P.cs: out.setdefault(c.u,[]).append(c)
        t1=time.time();tr=None;ol=False;rawT=P.T
        if m in("ours","ours_noub"):
            Q=with_ub(P,out) if m=="ours" else P
            g_,_,_=search(Q)
            sch=backtrack(Q,g_) if g_ else None
            if sch and overlap(Q,sch):
                ol=True;tk=T.search_track(Q,"sep",200000)
                if tk=="CAP": cap+=1;sch=None
                elif tk is None: sch=None
                else: sch=T.back_track(Q,tk)
                if sch is None and Q.T!=P.T:
                    tk=T.search_track(P,"sep",200000)
                    if tk not in (None,"CAP"): sch=T.back_track(P,tk)
        elif m=="sf":
            Q=with_ub(P,out);g_=SL.search(Q);sch=SL.backtrack(Q,g_) if g_ else None
        elif m=="store":
            Q=with_ub(P,out);sch=X.search_store(Q,out)
        elif m=="sr1": sch,tr=X.srcgr(P,out,1)
        else: sch,tr=X.srcgr(P,out,10)
        dt=time.time()-t1;ov+=ol;arr=None
        if sch and (not replay(P,sch) or overlap(P,sch)): bad+=1;sch=None
        if sch:
            c,s=sch[-1];arr=s+S/c.r+c.d;P=commit(P,sch)
        rows.append(dict(arr=float(arr) if arr is not None else None,g=float(g),h=len(sch) if sch else 0,sec=round(dt,4),tr=tr,ol=ol,
                         cut=sum(1 for (a,sa),(b,sb) in zip(sch,sch[1:]) if sb<sa+a.d+S/a.r) if sch else 0))
        if time.time()-t0>budget: stop=b+1;break
    except TO: stop=len(rows)
    finally: signal.alarm(0)
    return dict(topo=tp,N=N,seed=seed,M=str(M),m=m,rows=rows,ov=ov,bad=bad,cap=cap,stop=stop,wall=round(time.time()-t0,1))
if __name__=="__main__":
    out=sys.argv[1];budget=float(sys.argv[2]);which=sys.argv[3] if len(sys.argv)>3 else "all"
    J=[]
    grids=dict(relay=([10,20,40],[5,10],range(1,21)),walker16=([50,150],[15,30],range(1,4)),rr_atrack=([100,300],[3,30],range(1,4)),rr_walker=([100,300],[3,30],range(1,4)))
    for tp,(Ns,Ms,ss) in grids.items():
        if which!="all" and tp not in which.split(","): continue
        for N in Ns:
            for M in Ms:
                for s in ss:
                    for m in(("sf",) if not (tp=="walker16" and N==150) else ("sf","sr1","sr10")): J.append((tp,N,s,M,m,budget))
    done=set()
    if os.path.exists(out):
        for l in open(out):
            d=json.loads(l);done.add((d["topo"],d["N"],d["seed"],int(d["M"]),d["m"]))
    J=[j for j in J if j[:5] not in done and (j[0],j[1],j[2],j[3],j[4]) not in done]
    with Pool(2) as p:
        for i,r in enumerate(p.imap_unordered(one,J)):
            open(out,"a").write(json.dumps(r)+"\n")
            print(i+1,len(J),r["topo"],r["N"],r["seed"],r["M"],r["m"],r["wall"],sum(x["arr"] is not None for x in r["rows"]),len(r["rows"]),r["ov"],r["bad"],flush=True)
