import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for n in("DFKai-SB","BiauKai","AR PL UKai TW","Noto Serif CJK TC"):
    if any(f.name==n for f in fm.fontManager.ttflist):plt.rcParams['font.family']=n;break
plt.rcParams.update({'axes.spines.top':False,'axes.spines.right':False,'font.size':13,'axes.edgecolor':'#8A8A8A','axes.unicode_minus':False})
OR,NV,RD,GN,K='#D97828','#5A50D0','#C0392B','#187A3E','#444444'
def base(ymax,ticks):
    f,a=plt.subplots(figsize=(5.9,2.9));a.grid(axis='y',color='#E4E4E4',lw=.8);a.set_axisbelow(True)
    a.set_xlim(0,12);a.set_ylim(0,ymax);a.set_yticks(ticks);a.set_xticks(range(0,13,2));a.set_xlabel('時間（秒）');a.set_ylabel('占用（MB）')
    a.axhline(4,color=K,ls=(0,(5,3)),lw=1.4,label='上限 4 MB');return f,a
def save(f,n):
    f.subplots_adjust(left=.1,right=.985,top=.86,bottom=.2);f.savefig(n,dpi=220);plt.close(f)
for n,lab,x,y,c in(('occ_p16.png','第一包在 B',[0,2,3,6,7,12],[0,0,4,4,0,0],OR),('occ_p26.png','第二包在 C',[0,2,3,4,5,12],[0,0,4,4,0,0],GN)):
    f,a=base(5,[0,2,4]);a.plot(x,y,color=c,lw=2.2,label=lab);a.legend(loc='upper center',bbox_to_anchor=(.5,1.2),ncol=2,frameon=False,fontsize=12);save(f,n)
f,a=base(9,[0,2,4,6,8])
X=[0,1,2,3,6,7,10,11,12];T=[0,0,4,8,8,4,4,0,0]
a.fill_between([2,3,6,7],[4,8,8,4],[4,4,4,4],color=RD,alpha=.13,lw=0)
a.plot([0,2,3,6,7,12],[0,0,4,4,0,0],color=OR,lw=1.8,label='第一包')
a.plot([0,1,2,10,11,12],[0,0,4,4,0,0],color=NV,lw=1.8,ls='--',label='第二包候選')
a.plot(X,T,color=RD,lw=2.4,label='合計')
a.text(4.5,6.2,'超過上限',ha='center',color='#222222',fontsize=12)
a.legend(loc='upper center',bbox_to_anchor=(.5,1.2),ncol=4,frameon=False,fontsize=12,columnspacing=1);save(f,'occ_p21.png')
