import sys; sys.path.insert(0,'.')
from fractions import Fraction as Fr
from dtn.model import Contact, Problem, Curve, ramp
from dtn.ours import plan
from dtn.validate import validate, commit
cs=[Contact('c1','A','B',Fr(0),Fr(100),Fr(1,4),Fr(1),()),
    Contact('c2','B','C',Fr(20),Fr(100),Fr(1,4),Fr(1),())]
P=Problem(cs,'A','C',Fr(0),Fr(1),Fr(1),{},Fr(1000))
for i,g in enumerate([0,20]):
    P=P._replace(g=Fr(g))
    O=P.O.get('B',Curve())
    sch=plan(P)
    print('bundle',i+1,'g',g,'sch',[(c.id,str(s)) for c,s in sch],'valid',validate(P,sch))
    (c1,s1),(c2,s2)=sch; h=s1+c1.d; A=h+P.S/c1.r; f=s2+P.S/c2.r
    print('  B: h',h,'A',A,'s2',s2,'f',f,'arrive C',f+c2.d)
    if i==1:
        own=lambda t: ramp(t,h,A,P.S)-ramp(t,s2,f,P.S)
        pts=sorted(set([h,A,s2,f]+O.between(h,f)+[Fr(22),Fr(23)]))
        for t in pts: print('  t',t,'O',O.top(t),'own',own(t),'sum',O.top(t)+own(t))
        print('  whole-bundle: peak',O.peak(h,f),'+S =',O.peak(h,f)+P.S)
    P=commit(P,sch)
    for n,cv in sorted(P.O.items()):
        print('  O_%s'%n,'ts',[str(x) for x in cv.ts],'ls',[str(x) for x in cv.ls],'rs',[str(x) for x in cv.rs])
