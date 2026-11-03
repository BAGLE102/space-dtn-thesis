from fractions import Fraction as Fr
from cut_through_audit import C,I,add,occ
from interval_label_validation import replay,start_parts,minus
import store_label as SL
from cut_through_audit import trap
def show(P,name):
    l=SL.search(P);print(name)
    if not l: print(' no path');return
    sch=SL.backtrack(P,l);print(' sched',[(c.id,float(s)) for c,s in sch],'arr',float(sch[-1][1]+P.S/sch[-1][0].r+sch[-1][0].d),'replay',replay(P,sch))
    x=l
    while x: print('  label',x.c.id,[(float(a),float(b)) for a,b in x.I],float(x.key));x=x.pred
F=Fr
# 範例一
c=[C('A>B','A','B',F(0),F(10),F(2),F(0),()),C('B>C','B','C',F(2),F(12),F(2),F(0),())]
O={'B':[(F(5),F(0)),(F(6),F(3))]}
show(I(c,'A','C',F(0),F(10),F(12),O,F(100)),'ex1')
P=I(c,'A','C',F(0),F(10),F(12),O,F(100))
l=[x for x in [SL.search(P)]][0];print(' ex1 parts',start_parts(P,c[1],F(5)))
from interval_label_validation import buffer_filter
print(' ex1 filter',[(float(a),float(b)) for a,b in buffer_filter(P,start_parts(P,c[1],F(5)),[(F(0),F(5))],c[0],c[1],True,EX=F(5))])
# 範例二
c2=[c[0],C('B>C','B','C',F(2),F(20),F(2),F(0),((F(12),F(13)),))]
P=I(c2,'A','C',F(0),F(10),F(40),{},F(100));print(' ex2 parts',start_parts(P,c2[1],F(5)));show(P,'ex2')
# 範例三
cs=[C('c1','A','B',F(0),F(10),F(2),F(0),()),C('c2','A','C',F(1),F(8),F(2),F(1),()),
C('c3','B','E',F(2),F(20),F(2),F(0),((F(9),F(10)),)),C('c4','E','D',F(16),F(21),F(2),F(0),()),
C('c5','B','V',F(5),F(10),F(2),F(0),()),C('c6','V','B',F(15),F(20),F(2),F(0),()),
C('c7','B','D',F(20),F(23),F(5),F(0),()),C('c8','C','D',F(9),F(11),F(5),F(0),()),
C('c9','A','F',F(0),F(6),F(2),F(0),()),C('c10','F','D',F(20),F(30),F(1),F(0),())]
O={'B':trap(F(11),F(10),F(1),F(10)),'E':trap(F(11),F(10),F(1),F(10)),'C':trap(F(5),F(10),F(1),F(10))}
print({k:[(float(a),float(b)) for a,b in v] for k,v in O.items()})
P=I(cs,'A','D',F(0),F(10),F(10),O,F(100));show(P,'ex3')
import heapq
# trace
out={}
for c_ in P.cs: out.setdefault(c_.u,[]).append(c_)
Q=[];tick=0;reached={}
def ins(c,parts,pred):
    global tick
    r=reached.get(c.id,[]);new=minus(parts,r);reached[c.id]=SL.merge(r+new)
    res=[]
    for I_ in new:
        k=I_[0]+P.S/c.r+c.d;tick+=1;heapq.heappush(Q,(k,tick,SL.L(c,[I_],pred,k)));res.append((c.id,float(I_[0]),float(I_[1]),float(k)))
    return res
for c_ in out['A']: print(' init',ins(c_,SL.source_parts(P,c_),None))
while Q:
    _,_,l=heapq.heappop(Q);print('pop',l.c.id,l.c.v,[(float(a),float(b)) for a,b in l.I],float(l.key))
    if l.c.v=='D':break
    d1=P.S/l.c.r
    for c2 in out.get(l.c.v,[]):
        p=start_parts(P,c2,l.I[0][0]+l.c.d+d1)
        q=buffer_filter(P,p,l.I,l.c,c2,True,EX=d1) if p else []
        print('  ',c2.id,'cand',[(float(a),float(b)) for a,b in p],'buf',[(float(a),float(b)) for a,b in q],'new',ins(c2,q,l) if q else [])
