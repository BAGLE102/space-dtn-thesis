"""Store-and-forward 區間 Label（正式版候選）。Cut-through 版保留在 interval_label_validation.py。"""
import heapq
from fractions import Fraction as Fr
from collections import namedtuple
from interval_label_validation import start_parts,buffer_filter,minus,merge,star
from cut_through_audit import occ
L=namedtuple("L","c I pred key")
def source_limit(P,c):
    """SourceBufferFilter：來源從 g 持有 S，邊送邊釋放。s 可行集合向下封閉，回傳最大可行 s。"""
    O=P.O.get(P.src,[]);r=c.r;xs=lambda t:occ(O,t)+P.S-P.M
    ts=sorted({P.g}|{t for t,_ in O if t>P.g})
    # 起點 g 持有整包，一定要放得下
    if xs(P.g)>0: return None
    lim=None
    C=[t-xs(t)/r for t in ts if xs(t)>0]
    for a,b in zip(ts,ts[1:]):
        xa,xb=xs(a),xs(b)
        if xa<=0<xb: C.append(a+(b-a)*(-xa)/(xb-xa))
    if C: lim=min(C)
    return lim
def source_parts(P,c):
    p=start_parts(P,c,P.g);lim=source_limit(P,c)
    if not P.O.get(P.src):
        return p if P.S<=P.M else []
    if P.S>P.M: return []
    if lim is None:
        if occ(P.O[P.src],P.g)+P.S>P.M: return []
        return p
    return [(a,min(b,lim)) for a,b in p if a<=lim]
def search(P):
    out={}
    for c in P.cs: out.setdefault(c.u,[]).append(c)
    Q=[];tick=0;reached={}
    def ins(c,parts,pred):
        nonlocal tick
        r=reached.get(c.id,[]);new=minus(parts,r);reached[c.id]=merge(r+new)
        for I_ in new:
            k=I_[0]+P.S/c.r+c.d;tick+=1;heapq.heappush(Q,(k,tick,L(c,[I_],pred,k)))
    for c in out.get(P.src,[]): ins(c,source_parts(P,c),None)
    while Q:
        _,_,l=heapq.heappop(Q)
        if l.c.v==P.dst: return l
        c1=l.c;d1=P.S/c1.r
        for c2 in out.get(c1.v,[]):
            parts=start_parts(P,c2,l.I[0][0]+c1.d+d1)
            if parts: ins(c2,buffer_filter(P,parts,l.I,c1,c2,True,EX=d1),l)
    return None
def backtrack(P,l):
    s=l.I[0][0];sch=[(l.c,s)];x=l
    while x.pred is not None:
        q=x.pred;w=star(q.I,s-q.c.d-P.S/q.c.r,True);sch.insert(0,(q.c,w));x=q;s=w
    return sch
