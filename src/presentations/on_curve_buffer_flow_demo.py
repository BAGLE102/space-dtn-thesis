import sys; sys.path.insert(0,'.')
from fractions import Fraction as Fr
from dtn.model import Contact, Problem, Curve, ramp
from dtn import ours
from dtn.ours import plan, candidate_range, source_filter, buffer_filter, destination_filter, Label
from dtn.validate import validate, commit, relay_ok
F=lambda xs:[Fr(x) for x in xs]
OB=Curve(F([100,104,112,116]),F([0,4,4,0]),F([0,4,4,0]))
c1=Contact('c1','A','B',Fr(100),Fr(130),Fr(1),Fr(0),())
c2=Contact('c2','B','C',Fr(104),Fr(140),Fr(1),Fr(0),())
P=Problem([c1,c2],'A','C',Fr(100),Fr(4),Fr(6),{'B':OB},Fr(1000))
r1=candidate_range(P,c1,P.g); print('range c1',r1)
s1=source_filter(P,c1,r1); print('source_filter',s1)
L1=Label(c1,s1[0][0],s1[0][1],None)
head=L1.lo+c1.d+P.S/c1.r; print('head',head)
r2=candidate_range(P,c2,head); print('range c2',r2)
print('fast window',L1.lo+c1.d, r2[0][1]+P.S/c2.r,'peak',OB.peak(L1.lo+c1.d, r2[0][1]+P.S/c2.r))
calls=[]
orig=ours.solve_region
def spy(P_,lo,hi,bps,feas,vals):
    r=orig(P_,lo,hi,bps,feas,vals); calls.append((lo,hi,sorted(set(b for b in bps if lo<b<hi)),r)); return r
ours.solve_region=spy
b2=buffer_filter(P,r2,L1,c2); print('buffer_filter',b2)
for lo,hi,bps,r in calls: print(' solve_region',lo,hi,'cuts',[str(x) for x in bps],'->',[(str(a),str(b)) for a,b in r])
ours.solve_region=orig
for s2 in (104,110,113,114,120):
    s2=Fr(s2); k=min(L1.hi, s2-c1.d-P.S/c1.r); h=k; A=h+4; f=s2+4
    own=lambda t: ramp(t,h,A,P.S)-ramp(t,s2,f,P.S)
    pts=sorted(set([h,A,s2,f]+OB.between(h,f)))
    worst=max(OB.top(t)+own(t) for t in pts)
    print(' s2',s2,'s1*',k,'stay',h,f,'ok',relay_ok(P,c1,k,c2,s2),'max sum',worst,[(str(t),str(OB.top(t)),str(own(t))) for t in pts])
sch=plan(P); print('plan',[(c.id,str(s)) for c,s in sch],'arrive',sch[-1][1]+4,'valid',validate(P,sch))
Q=commit(P,sch); cv=Q.O['B']; print('O_B after',[str(x) for x in cv.ts],[str(x) for x in cv.ls],[str(x) for x in cv.rs])
