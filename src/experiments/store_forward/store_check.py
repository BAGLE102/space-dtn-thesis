import random,sys,math
from fractions import Fraction as Fr
from cut_through_audit import occ,ramp,rand,add,trap
from interval_label_validation import replay
import track_check as T, store_label as SL
G=Fr(1,16)
def ok_src(P,c,s):
    O=P.O.get(P.src,[]);f=s+P.S/c.r
    for t in {P.g,s,f}|{x for x,_ in O if P.g<x<f}:
        if occ(O,t)+P.S-ramp(t,s,f,P.S)>P.M: return False
    return True
def ok_hop(P,c1,s1,c2,s2):
    h=s1+c1.d;A=h+P.S/c1.r;f=s2+P.S/c2.r;O=P.O.get(c1.v,[])
    if s2<A: return False
    for t in {h,A,s2,f}|{x for x,_ in O if h<x<f}:
        if occ(O,t)+ramp(t,h,A,P.S)-ramp(t,s2,f,P.S)>P.M: return False
    return True
def times(P,c):
    d=P.S/c.r;t=[];x=c.a
    x=Fr(math.ceil(c.a/G))*G
    while x+d<=c.b and x+d+c.d<=P.T:
        if not any(x<y and a<x+d for a,y in c.F): t.append(x)
        x+=G
    return t
def oracle(P):
    out={};best=None;seen=set();st=[]
    for c in P.cs: out.setdefault(c.u,[]).append(c)
    for c in out.get(P.src,[]):
        for s in times(P,c):
            if s>=P.g and ok_src(P,c,s): st.append((c,s));seen.add((c.id,s))
    while st:
        c,s=st.pop();A=s+P.S/c.r+c.d
        if c.v==P.dst:
            best=A if best is None else min(best,A);continue
        for c2 in out.get(c.v,[]):
            for s2 in times(P,c2):
                if (c2.id,s2) not in seen and ok_hop(P,c,s,c2,s2):
                    seen.add((c2.id,s2));st.append((c2,s2))
    return best
def main(n,seed):
    R=dict(cases=0,both_none=0,same=0,earlier=0,later=0,missed=0,extra=0,badreplay=0,feasible=0)
    for i in range(n):
        rng=random.Random(seed+i);g=i%3
        P=rand(rng,True) if g==0 else T.loopy(rng,True) if g==1 else T.directed(rng,True)
        if rng.random()<.6:
            P=P._replace(O={**P.O,"S":add([trap(Fr(rng.randint(0,16),2),Fr(rng.choice([1,2,3])),Fr(rng.randint(0,6),2))])})
        l=SL.search(P);a=None
        if l:
            sch=SL.backtrack(P,l);c,s=sch[-1];a=s+P.S/c.r+c.d
            if not replay(P,sch): R["badreplay"]+=1;print("bad",seed+i,g)
        o=oracle(P);R["cases"]+=1
        if o is None and a is None: R["both_none"]+=1
        elif o is None: R["extra"]+=1;print('extra',seed+i,g,float(a))
        elif a is None: R["missed"]+=1;print('missed',seed+i,g,float(o))
        else:
            R["feasible"]+=1
            k="same" if a==o else "earlier" if a<o else "later"
            R[k]+=1
            if k=="later": print('later',seed+i,g,float(a),float(o))
    print(R)
if __name__=="__main__": main(int(sys.argv[1]),int(sys.argv[2]))
