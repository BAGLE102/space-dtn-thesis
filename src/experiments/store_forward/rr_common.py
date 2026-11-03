import os
import random,heapq,time,json,sys
from fractions import Fraction as Fr
import cut_through_audit as ct
from cut_through_audit import C,I
import interval_label_validation as v
SRC=os.environ.get("TOPOLOGY_DIR","tmp/topology_sources")+"/RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt"
def load(rate=Fr(1,10),horizon=86400):
    cs=[]
    for ln in open(SRC):
        p=ln.split()
        if len(p)>=7 and p[0]=='a' and p[1]=='contact':
            a,b,u,w=int(p[2]),int(p[3]),int(p[4]),int(p[5])
            if 48 in (u,w) or a>=horizon: continue
            cs.append(C(f"c{len(cs)}",u,w,Fr(a),Fr(min(b,horizon)),rate,Fr(0),()))
    return cs
if __name__=="__main__":
    cs=load();print(len(cs),len({c.u for c in cs}|{c.v for c in cs}))
    import collections
    print(sum(1 for c in cs if c.u>=32 and c.v<32),sum(1 for c in cs if c.u<32 and c.v>=32),sum(1 for c in cs if c.u>=32 and c.v>=32),sum(1 for c in cs if c.u<32 and c.v<32))
    print(min(c.b-c.a for c in cs),sum(c.b-c.a for c in cs)/len(cs))
