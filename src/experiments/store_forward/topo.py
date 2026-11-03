import os
import math,random,functools
from fractions import Fraction as Fr
import numpy as np
from cut_through_audit import C
RR=os.environ.get("TOPOLOGY_DIR","tmp/topology_sources")+"/RingRoad_16sats_%s_6hotspots_simtime24hs_comrange1000km.txt"
def ringroad(kind,rate=Fr(1,10)):
    cs=[]
    for ln in open(RR%kind):
        p=ln.split()
        if len(p)>=7 and p[0]=='a' and p[1]=='contact':
            a,b,u,w=int(p[2]),int(p[3]),int(p[4]),int(p[5])
            if 48 in (u,w): continue
            cs.append(C(f"c{len(cs)}",u,w,Fr(a),Fr(b),rate,Fr(0),()))
    return cs
def rr_demand(N,seed,R=300):
    rng=random.Random(seed);D=[(rng.randint(7,31),rng.randint(1,6),Fr(rng.randint(0,R))) for _ in range(N)]
    D.sort(key=lambda x:x[2]);return D
RE=6371.0;MU=398600.4418;WE=7.2921159e-5
def walker(nsat,planes=4,inc=52.0,alt=780.0,hor=21600,step=10,R_isl=5000.0,elev=10.0,rgs=Fr(1,2),risl=Fr(2)):
    """Walker-delta，零相位。節點：0..nsat-1 衛星；GS: 100+。地面站自訂：巴黎、台北、聖保羅、奈洛比。"""
    r=RE+alt;n=math.sqrt(MU/r**3);i=math.radians(inc);per=nsat//planes
    ts=np.arange(0,hor+step,step,dtype=float)
    P=[]
    for p in range(planes):
        O=2*math.pi*p/planes
        for k in range(per):
            u=2*math.pi*k/per+n*ts
            x=r*np.cos(u);y=r*np.sin(u)
            P.append(np.stack([x*math.cos(O)-y*math.cos(i)*math.sin(O),x*math.sin(O)+y*math.cos(i)*math.cos(O),y*math.sin(i)],1))
    GS=[(48.85,2.35),(25.03,121.56),(-23.55,-46.63),(-1.29,36.82)]
    G=[]
    for la,lo in GS:
        la,lo=math.radians(la),math.radians(lo);th=lo+WE*ts
        G.append(np.stack([RE*math.cos(la)*np.cos(th),RE*math.cos(la)*np.sin(th),RE*math.sin(la)*np.ones_like(ts)],1))
    cs=[]
    def emit(u,w,vis,dist,rate):
        k=0;L=len(ts)
        while k<L:
            if vis[k]:
                j=k
                while j+1<L and vis[j+1]: j+=1
                if j>k:
                    dl=Fr(int(round(float(dist[k:j+1].mean())/299792.458*100)),100)
                    for a,b in ((u,w),(w,u)):
                        cs.append(C(f"c{len(cs)}",a,b,Fr(int(ts[k])),Fr(int(ts[j])),rate,dl,()))
                k=j+1
            else:k+=1
    N=len(P)
    for a in range(N):
        for b in range(a+1,N):
            d=np.linalg.norm(P[a]-P[b],axis=1)
            m=(P[a]+P[b])/2
            vis=(d<=R_isl)&(np.linalg.norm(m,axis=1)>RE+100)
            emit(a,b,vis,d,risl)
    for g,gp in enumerate(G):
        for a in range(N):
            v=P[a]-gp;d=np.linalg.norm(v,axis=1)
            sinel=(v*gp).sum(1)/(d*RE)
            emit(100+g,a,sinel>=math.sin(math.radians(elev)),d,rgs)
    return cs
def walker_demand(N,seed,R=600):
    rng=random.Random(seed);D=[]
    for _ in range(N):
        u,w=rng.sample([100,101,102,103],2);D.append((u,w,Fr(rng.randint(0,R))))
    D.sort(key=lambda x:x[2]);return D
def relay(seed,nodes=12,nc=70,hor=600):
    rng=random.Random(10000+seed);cs=[]
    for i in range(nc):
        u=rng.randrange(nodes);w=rng.choice([x for x in range(nodes) if x!=u and abs(x-u)<=4])
        a=rng.randint(0,hor-40);ln=rng.randint(30,160)
        cs.append(C(f"c{i}",u,w,Fr(a),Fr(min(a+ln,hor)),Fr(rng.choice([1,2,5])),Fr(rng.choice([0,0,1,2,5]),10),()))
    return cs
def relay_demand(N,seed,R=100,nodes=12):
    rng=random.Random(seed);D=[]
    for _ in range(N):
        u=rng.randrange(0,3);w=rng.randrange(nodes-3,nodes);D.append((u,w,Fr(rng.randint(0,R))))
    D.sort(key=lambda x:x[2]);return D
TOPO=dict(
 rr_walker=dict(c=lambda s:ringroad("Walker"),d=rr_demand,T=86400,S=Fr(1)),
 rr_atrack=dict(c=lambda s:ringroad("ATrack"),d=rr_demand,T=86400,S=Fr(1)),
 walker16=dict(c=lambda s:WK(16),d=walker_demand,T=21600,S=Fr(10)),
 relay=dict(c=lambda s:relay(s),d=relay_demand,T=600,S=Fr(4)))
@functools.lru_cache(None)
def WK(n): return walker(n)
if __name__=="__main__":
    for k,t in TOPO.items():
        cs=t["c"](1);print(k,len(cs),len({c.u for c in cs}|{c.v for c in cs}),float(sum(c.b-c.a for c in cs)/len(cs)),float(max(c.d for c in cs)))
