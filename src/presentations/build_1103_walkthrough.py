import copy,json
from fractions import Fraction as F
from pptx import Presentation
from pptx.util import Inches as In,Pt
from pptx.dml.color import RGBColor as RGB
from pptx.enum.text import PP_ALIGN,MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.chart.data import XyChartData
from pptx.enum.chart import XL_CHART_TYPE,XL_LEGEND_POSITION
from pptx.oxml.ns import qn
from lxml import etree
FONT='DFKai-SB'
NAVY,INK,MUT,LINE,BLUE,GRN,RED,ORG,PALE,PALEG,PALER=[RGB.from_string(x) for x in '1F3A7A 222222 666666 C9CDD4 2A78D6 1B8A5A C8372D D9772B EAF1FB E6F4EC FBEAE8'.split()]
p=Presentation('template.pptx')
LAY={l.name:l for l in p.slide_layouts}
tmpl=p.slides[0]; NUM=copy.deepcopy([s for s in tmpl.placeholders if s.placeholder_format.type==13][0]._element)
def fontify(r,size,color=INK,bold=False):
    r.font.size=Pt(size);r.font.name=FONT;r.font.color.rgb=color;r.font.bold=bold
    rp=r._r.get_or_add_rPr()
    for t in('a:ea','a:cs'):
        e=rp.find(qn(t))
        if e is None:e=etree.SubElement(rp,qn(t))
        e.set('typeface',FONT)
def tb(sl,x,y,w,h,text,size=18,color=INK,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP,bold=False,name=None):
    s=sl.shapes.add_textbox(In(x),In(y),In(w),In(h));tf=s.text_frame;tf.word_wrap=True;tf.vertical_anchor=anchor
    tf.margin_left=tf.margin_right=In(.03);tf.margin_top=tf.margin_bottom=In(.02)
    ls=text if isinstance(text,list) else [text]
    for i,l in enumerate(ls):
        q=tf.paragraphs[0] if i==0 else tf.add_paragraph();q.alignment=align
        col=color
        if isinstance(l,tuple): l,col=l
        r=q.add_run();r.text=l;fontify(r,size,col,bold)
    if name:s.name=name
    return s
def box(sl,x,y,w,h,text='',fill=None,line=NAVY,size=16,color=INK,lw=1.25,shape=MSO_SHAPE.RECTANGLE,align=PP_ALIGN.CENTER):
    s=sl.shapes.add_shape(shape,In(x),In(y),In(w),In(h));s.shadow.inherit=False
    if fill is None:s.fill.background()
    else:s.fill.solid();s.fill.fore_color.rgb=fill
    if line is None:s.line.fill.background()
    else:s.line.color.rgb=line;s.line.width=Pt(lw)
    tf=s.text_frame;tf.word_wrap=True;tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    tf.margin_left=tf.margin_right=In(.05);tf.margin_top=tf.margin_bottom=In(.02)
    ls=text if isinstance(text,list) else [text]
    for i,l in enumerate(ls):
        q=tf.paragraphs[0] if i==0 else tf.add_paragraph();q.alignment=align
        r=q.add_run();r.text=l;fontify(r,size,color)
    return s
def arrow_el(s,w=1.5,dash=False):
    ln=s.line._get_or_add_ln()
    for t in ln.findall(qn('a:tailEnd')):ln.remove(t)
    if dash:
        d=etree.SubElement(ln,qn('a:prstDash'));d.set('val','dash')
    t=etree.SubElement(ln,qn('a:tailEnd'));t.set('type','triangle');t.set('w','med');t.set('len','med')
def arrow(sl,x1,y1,x2,y2,color=NAVY,w=1.5):
    c=sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,In(x1),In(y1),In(x2),In(y2));c.line.color.rgb=color;c.line.width=Pt(w);arrow_el(c);return c
def new(title,notes,lay='只有標題'):
    sl=p.slides.add_slide(LAY[lay])
    t=sl.shapes.title;t.left,t.top,t.width,t.height=In(.5),In(.28),In(12.3),In(.72)
    t.text_frame.text='';r=t.text_frame.paragraphs[0].add_run();r.text=title;fontify(r,30,NAVY)
    t.text_frame.vertical_anchor=MSO_ANCHOR.MIDDLE
    n=copy.deepcopy(NUM);sl.shapes._spTree.append(n)
    sl.notes_slide.notes_text_frame.text=notes
    return sl
GEO=json.load(open('geo.json'))
SC=.0125;OX,OY=.72,1.45
def X(a):return (a-130)*SC+OX+.05
def Y(b):return (b-210)*SC+OY+.1
WIN={'c1':'[2,3]','c2':'[6,7]','c3':'[1,2]','c4':'[7,9]','c5':'[10,11]','c6':'[1,2]','c7':'[4,5]','c8':'[2,3]'}
def poly(sl,pts,color,w,dash=False):
    fb=sl.shapes.build_freeform(In(pts[0][0]),In(pts[0][1]),scale=1.0)
    fb.add_line_segments([(In(a),In(b)) for a,b in pts[1:]],close=False)
    s=fb.convert_to_shape();s.fill.background();s.line.color.rgb=color;s.line.width=Pt(w);s.shadow.inherit=False;arrow_el(s,w,dash);return s
def topo(sl,used=(),rej=(),cand=(),nodes=()):
    for k,l in GEO['links'].items():
        col,w,dash=(LINE,1,False)
        if k in used:col,w=(GRN,2.5)
        elif k in rej:col,w,dash=(RED,2.25,True)
        elif k in cand:col,w=(BLUE,2.25)
        poly(sl,[(X(a),Y(b)) for a,b in l['points']],col,w,dash)
    for k,l in GEO['links'].items():
        col=GRN if k in used else RED if k in rej else BLUE if k in cand else MUT
        cx,cy=l['label_center_top'];cx,cy=X(cx),Y(cy)
        for tx,yy,sz,hh in((k,cy-.06,13,.25),(WIN[k],cy+.16,10.5,.2)):
            lb=tb(sl,cx-.3,yy,.6,hh,tx,sz,col,PP_ALIGN.CENTER);lb.fill.solid();lb.fill.fore_color.rgb=RGB(255,255,255)
    for k,(a,b) in GEO['original_node_centers'].items():
        hi=k in nodes
        box(sl,X(a)-.26,Y(b)-.26,.52,.52,k,fill=PALE if hi else RGB(255,255,255),line=NAVY,size=18,color=NAVY,lw=2 if hi else 1.25,shape=MSO_SHAPE.OVAL)
def timeline(sl,rows,t0,t1,x=6.75,y=1.4,w=6.05,rowh=.46,labw=1.25,step=1):
    ax=x+labw;scale=(w-labw)/(t1-t0)
    for i,(lab,bars) in enumerate(rows):
        yy=y+i*rowh
        tb(sl,x,yy,labw-.05,rowh,lab,14,INK,PP_ALIGN.RIGHT,MSO_ANCHOR.MIDDLE)
        box(sl,ax,yy+rowh/2-.005,w-labw,.01,fill=LINE,line=None)
        for a,b,c in bars:
            ww=max((b-a)*scale,.05)
            box(sl,ax+(a-t0)*scale,yy+.09,ww,rowh-.18,fill=c,line=None)
    yb=y+len(rows)*rowh
    box(sl,ax,yb,w-labw,.012,fill=MUT,line=None)
    t=t0
    while t<=t1:
        tb(sl,ax+(t-t0)*scale-.25,yb+.02,.5,.26,str(t),12,MUT,PP_ALIGN.CENTER);t+=step
    tb(sl,x,yb+.02,labw-.05,.26,'時間（秒）',12,MUT,PP_ALIGN.RIGHT)
    return yb+.3
def qrow(sl,items,y=4.95,taken=None):
    tb(sl,.5,y,.95,.5,'Q',18,NAVY,PP_ALIGN.CENTER,MSO_ANCHOR.MIDDLE)
    x=1.25
    if not items:tb(sl,x,y,3,.5,'（空）',16,MUT,anchor=MSO_ANCHOR.MIDDLE)
    for it,ch in items:
        w=3.55
        box(sl,x,y+.02,w,.46,it,fill=PALE if ch else None,line=BLUE if ch else LINE,size=14,color=INK,lw=1.5 if ch else 1);x+=w+.12
    if taken:tb(sl,.5,y+.5,12,.3,taken,14,MUT)
def concl(sl,t,y=5.85,color=NAVY):
    tb(sl,.5,y,9.2,.62,t,17,color,anchor=MSO_ANCHOR.MIDDLE)
def _common(series):
    from collections import Counter
    mult=Counter()
    for _,pts,*_r in series:
        for k,v in Counter(a for a,_b in pts).items(): mult[k]=max(mult[k],v)
    xs=sorted(mult.elements())
    out=[]
    for nm,pts,col,wd,dash in series:
        seen=Counter();res=[]
        for a in xs:
            same=[b for u,b in pts if u==a]
            if same:
                i=min(seen[a],len(same)-1);res.append((a,same[i]));seen[a]+=1
            else:
                lo=max((q for q in pts if q[0]<a),key=lambda q:q[0]);hi=min((q for q in pts if q[0]>a),key=lambda q:q[0])
                lo=[q for q in pts if q[0]==lo[0]][-1];hi=[q for q in pts if q[0]==hi[0]][0]
                res.append((a,lo[1]+(hi[1]-lo[1])*(a-lo[0])/(hi[0]-lo[0])))
        out.append((nm,res,col,wd,dash))
    return out
def chart(sl,series,x,y,w,h,ymax=None,xmax=None):
    series=_common(series)
    cd=XyChartData()
    for nm,pts,col,wd,dash in series:
        s=cd.add_series(nm)
        for a,b in pts:s.add_data_point(a,b)
    gf=sl.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS,In(x),In(y),In(w),In(h),cd);ch=gf.chart
    ch.has_title=False;ch.has_legend=True;ch.legend.position=XL_LEGEND_POSITION.TOP;ch.legend.include_in_layout=False
    ch.legend.font.size=Pt(13);ch.legend.font.name=FONT
    for s,(nm,pts,col,wd,dash) in zip(ch.plots[0].series,series):
        s.format.line.color.rgb=col;s.format.line.width=Pt(wd);s.smooth=False
        if dash:
            from pptx.enum.dml import MSO_LINE;s.format.line.dash_style=MSO_LINE.DASH
    for ax,ttl in((ch.category_axis,'時間（秒）'),(ch.value_axis,'占用（MB）')):
        ax.has_major_gridlines=ax is ch.value_axis
        if ax.has_major_gridlines:ax.major_gridlines.format.line.color.rgb=RGB(0xE4,0xE3,0xDF)
        ax.tick_labels.font.size=Pt(12);ax.tick_labels.font.name=FONT;ax.has_title=True
        ax.axis_title.text_frame.text=ttl;r=ax.axis_title.text_frame.paragraphs[0].runs[0];r.font.size=Pt(12);r.font.name=FONT;r.font.bold=False
        ax.format.line.color.rgb=MUT
    ch.category_axis.minimum_scale=0
    if xmax:ch.category_axis.maximum_scale=xmax
    ch.value_axis.minimum_scale=0
    if ymax:ch.value_axis.maximum_scale=ymax
    return ch
def table(sl,rows,widths,x,y,rowh=.46,size=15,hl=None):
    gf=sl.shapes.add_table(len(rows),len(widths),In(x),In(y),In(sum(widths)),In(rowh*len(rows)));t=gf.table
    tp=t._tbl.tblPr
    for a in('bandRow','firstRow'):tp.set(a,'0')
    sid=tp.find(qn('a:tableStyleId'))
    if sid is not None:sid.text='{5940675A-B579-460E-94D1-54222C63F5DA}'
    for j,w in enumerate(widths):t.columns[j].width=In(w)
    for i,row in enumerate(rows):
        t.rows[i].height=In(rowh)
        for j,v in enumerate(row):
            c=t.cell(i,j);c.vertical_anchor=MSO_ANCHOR.MIDDLE;c.margin_left=c.margin_right=In(.07);c.margin_top=c.margin_bottom=In(.02)
            tf=c.text_frame;q=tf.paragraphs[0];r=q.add_run();r.text=v;fontify(r,size,NAVY if i==0 else INK)
            if i==0:c.fill.solid();c.fill.fore_color.rgb=PALE
            elif hl and hl.get((i,j)):c.fill.solid();c.fill.fore_color.rgb=hl[(i,j)]
            else:c.fill.background()
    return gf
def code(sl,lines,x=.6,y=1.15,w=12.1,h=5.3,size=17):
    s=tb(sl,x,y,w,h,lines,size,INK);return s
# ========== 1
s0=tmpl
tt=[q for q in s0.placeholders if q.placeholder_format.type==3][0];st=[q for q in s0.placeholders if q.placeholder_format.type==4][0]
tt.text_frame.text='';r=tt.text_frame.paragraphs[0].add_run();r.text='Space DTN 區間 Label 路由';fontify(r,40,NAVY);tt.text_frame.paragraphs[0].alignment=PP_ALIGN.CENTER
st.text_frame.text='';r=st.text_frame.paragraphs[0].add_run();r.text='用一個例子，逐步看懂方法怎麼運作';fontify(r,24,INK);st.text_frame.paragraphs[0].alignment=PP_ALIGN.CENTER
s0.notes_slide.notes_text_frame.text='這份簡報用同一個小例子，逐步說明方法如何找路徑、如何處理 Buffer 與預約。這是候選方法，目前沒有正式最優性證明。本份不放實驗數據。'
# ========== 2 contact
s=new('問題一：連線只有特定時間才開放','衛星會移動，兩個節點只有特定時間連得上。軌道可預測，所以可以事先列出時刻表，也就是 Contact Plan。每筆 contact 就像一班車：從哪裡到哪裡、幾點開放、速率多少、訊號在路上要多久。')
tb(s,.7,1.3,11.8,.5,'每一筆 contact 就像一班車：只有開放時才能傳，錯過就要等下一次。',21)
timeline(s,[('X→B',[(2,3,BLUE)]),('A→B',[(1,2,BLUE),(7,9,BLUE)]),('B→D',[(6,7,BLUE),(10,11,BLUE)]),('C→D',[(2,3,BLUE),(4,5,BLUE)])],0,12,x=.8,y=2.05,w=11.6,rowh=.56,labw=1.2,step=1)
concl(s,'所以路由不只要選路徑，還要選「什麼時候傳」。',y=5.35)
# ========== 3 limits
s=new('問題二：一包資料要同時滿足四個限制','四個限制：一，bundle 不可切分，整包要在一段連續時間內傳完。二，不能和前面的包預約同一段傳送時間。三，節點要收完整包才能轉送，也就是 store-and-forward。四，節點的 Buffer 有上限，且是整段停留時間都要滿足，不是只看抵達瞬間。')
cards=[('整包傳完','Bundle 不可切分，要在 contact 開放時連續傳完'),('不撞預約','不可使用前面的包已預約的傳送時段'),('收完才轉','上一跳整包收完後，下一跳才能開始'),('不超過 Buffer','接收、等待、送出的全程，占用都不超過上限')]
for i,(a,b) in enumerate(cards):
    x=.75+(i%2)*6.05;y=1.45+(i//2)*2.3
    box(s,x,y,5.75,2.0,fill=PALE,line=None)
    tb(s,x+.25,y+.2,5.25,.55,a,24,NAVY)
    tb(s,x+.25,y+.85,5.25,1.0,b,19)
# ========== 4 early
s=new('為什麼最短路徑不夠：早到不一定好','A→B 可在第 0 到 5 秒間起送，傳 5 秒。下一跳第 15 秒才能走。B 上限 12 MB，第 6 到 8 秒有 3 MB 背景占用。第 0 秒就送，第 5 秒收完，第 6 秒總占用 13 MB，超過上限。第 5 秒才送，第 8 秒時總占用只有 9 MB，第 10 秒收完時背景已結束，所以可行。這就是一般最短路徑只記最早抵達不夠的原因。')
tb(s,.55,1.25,5.2,3.9,['一包 10 MB，A→B 傳 5 秒','可在第 0～5 秒間起送','下一跳第 15 秒才能走','','B 上限 12 MB','第 6～8 秒有 3 MB 背景占用'],20)
chart(s,[('第 0 秒送（早到）',[(0,0),(5,10),(6,10),(6,13),(8,13),(8,10),(15,10),(20,0)],RED,2.5,False),('第 5 秒送（晚到）',[(0,0),(5,0),(6,2),(6,5),(8,9),(8,6),(10,10),(15,10),(20,0)],GRN,2.5,False),('上限 12 MB',[(0,12),(20,12)],MUT,1.5,True)],5.9,1.15,6.95,4.55,ymax=16,xmax=20)
concl(s,'早到要等更久，第 6 秒就超過上限；晚一點送反而可行。')
# ========== 5 Label
s=new('核心想法：Label 存一段時間，不存單一時間','Label 有三項：這一跳用哪條 contact、可以在哪段時間起送、前一個 Label 是誰。key 不是狀態，是由它們推導出來的最早完整抵達時間，用來決定佇列取出順序。區間讓一筆資料代表連續的所有時間，不必逐秒列舉。')
tb(s,.7,1.2,11.9,.6,'L = (c, I, pred)',30,NAVY,PP_ALIGN.CENTER)
table(s,[['欄位','意思','例子'],['c','這一跳使用的 contact','c4（A→B）'],['I','可以起送的時間區間','[7, 8]：第 7～8 秒內任一時刻'],['pred','前一個 Label，回溯時用','SOURCE（第一跳）']],[1.6,5.4,4.9],.7,2.0,rowh=.62,size=19)
concl(s,'一個 Label 代表一整段可行時間；實際幾點送，到最後才決定。',y=5.0)
# ========== 6 flow
s=new('方法的四個步驟','搜尋：每次從佇列取出最早能完整抵達的 Label，第一個到目的地的就是答案。篩選：候選時間要扣掉預約，再檢查 Buffer。回溯：到目的地後才決定每一跳的實際時間。驗證與提交：獨立檢查排程後，寫入預約與占用，再換下一包。')
steps=[('1 取出','從 Q 取出 key 最小的 Label'),('2 延伸','算下一跳的候選時間，扣除預約、檢查 Buffer，建立新 Label'),('3 回溯','到目的地後，由最後一跳往回決定實際時間'),('4 提交','獨立驗證排程，寫入預約與占用')]
for i,(a,b) in enumerate(steps):
    x=.6+i*3.1
    box(s,x,1.7,2.75,2.75,fill=PALE,line=None)
    tb(s,x+.1,1.85,2.55,.55,a,23,NAVY,PP_ALIGN.CENTER)
    tb(s,x+.15,2.5,2.45,1.85,b,18)
    if i<3:arrow(s,x+2.77,3.07,x+3.08,3.07,NAVY,2)
arrow(s,3.45,4.7,1.95,4.7,MUT,1.5)
tb(s,1.2,4.75,3.3,.4,'還沒到目的地就重複 1、2',15,MUT)
concl(s,'一次規劃一包；前面提交的結果，會變成後面的限制。',y=5.45)
# ========== 7 symbols
s=new('看例子前只要記三個式子','d 是傳完一包要多久。A 是整包抵達下一個節點的時間，d 是傳輸時間，δ 是傳播延遲，兩者不同。key 用區間最早起送時間算出最早完整抵達，佇列依它排序。例子中 c2 第 6 秒起送，d=1，δ=1，第 8 秒整包到 D。')
table(s,[['符號','算法','意思','例子（c2 第 6 秒起送）'],['d','S / r','傳完整包要多久','4 MB ÷ 4 MB/s = 1 秒'],['A','s + d + δ','整包抵達下一節點的時間','6 + 1 + 1 = 8 秒'],['key','lo(I) + d + δ','這個 Label 最早完整抵達的時間','6 + 1 + 1 = 8']],[1.2,2.6,4.2,3.9],.7,1.5,rowh=.72,size=18)
tb(s,.7,4.6,11.9,.9,['S：包大小；r：速率；s：起送時間；δ：傳播延遲；lo(I)：區間 I 的最早時間','收完才轉：下一跳起送 s2 ≥ 上一跳的 A'],18,MUT)
# ========== 8 example
s=new('例子：五個節點、八條 contact、兩包資料','兩包都是 4 MB，每條 contact 速率 4 MB/s，所以 d=1 秒。Buffer 上限 4 MB。先規劃 X 到 D，再規劃 A 到 D。c2、c5、c6 的傳播延遲是 1 秒，其他是 0。範例裡沒有業務期限，時間只涵蓋到第 12 秒。')
topo(s)
table(s,[['','來源→目的地','g'],['第一包','X → D','0'],['第二包','A → D','1']],[1.6,3,1.2],6.85,1.3,rowh=.5,size=18)
tb(s,6.85,3.0,6,2.2,['S = 4 MB，r = 4 MB/s，所以 d = 1 秒','Buffer 上限 M = 4 MB','c2、c5、c6 的 δ = 1 秒，其他 δ = 0','[a, b] 是 contact 開放時間；g 是可開始的時間'],18)
# ========== first bundle
L1a='L1=(c1,[2,2],SOURCE)  key=3';L2a='L2=(c2,[6,6],L1)  key=8';L3a='L3=(c5,[10,10],L1)  key=12'
s=new('第一包 ①：從來源 X 建立 Label','X 只有 c1 一條出去。duration d 是傳完整包的時間：S÷r=4÷4=1 秒。delay δ 是訊號在路上的時間，c1 為 0。最早起送 Head 要 contact 已開放、bundle 也已產生，所以取 a=2 和 g=0 的較大值，得到 2。最晚起送 Tail 要在 contact 關閉前傳完，所以是 b−d=3−1=2。範例沒有業務期限，也沒有預約。所以 I=[2,2]，也就是只能第 2 秒起送。key=2+1+0=3。X 從 g=0 就持有整包，2 到 3 邊送邊釋放，來源 Buffer 檢查通過。此時還沒有預約任何資源。')
topo(s,cand=('c1',),nodes=('X',))
timeline(s,[('X 持有',[(0,2,LINE)]),('X 發送',[(2,3,BLUE)]),('B 接收',[(2,3,BLUE)])],0,5,y=1.05,rowh=.3)
table(s,[['項目','計算','結果'],['duration d（傳完要多久）','S / r = 4 / 4','1 秒'],['delay δ（訊號在路上）','c1 的傳播延遲','0 秒'],['最早 Head','max(a, g) = max(2, 0)','2'],['最晚 Tail','b − d = 3 − 1','2']],[2.75,2.3,1.0],6.75,2.45,rowh=.37,size=13.5)
tb(s,6.75,4.33,6.05,.5,'I = [Head, Tail] = [2,2]；key = 2 + 1 + 0 = 3',17,NAVY)
qrow(s,[(L1a,True)]);concl(s,'c1 只能第 2 秒起送；搜尋時只建立候選，還沒有預約任何資源。')
s=new('區間怎麼取：先定最早和最晚，再扣除不能用的','取區間有四步。第一步最早：contact 要開放，這一跳也要能開始；第一跳 e=g，後面每跳 e 是前一跳最早收完的時間。第二步最晚：要在 contact 關閉前傳完，也要趕上期限。第三步扣預約：起送落在 (x−d, y) 就會撞到 [x, y)。第四步檢查 Buffer。剩下的每段連續時間各建一個 Label。下表的數字都是這個例子。c8 的 Head=3 大於 Tail=2，所以沒有候選。')
table(s,[['步驟','算法','意思'],['1 最早','Head = max(a, e)','contact 已開放，這一跳也能開始'],['2 最晚','Tail = min(b − d, D* − d − δ)','關閉前傳完，並趕上期限'],['3 扣預約','移除 (x − d, y)','不撞到已預約的 [x, y)'],['4 查 Buffer','只留占用不超限的時間','剩下每段各建一個 Label']],[2.0,5.0,5.2],.55,1.08,rowh=.38,size=15)
table(s,[['contact','開放 [a, b]','最早可開始 e','Head','Tail','區間 I'],['c1（第一跳）','[2,3]','g = 0','2','2','[2,2]'],['c4（第一跳）','[7,9]','g = 1','7','8','[7,8]'],['c2（接 L1）','[6,7]','2 + 0 + 1 = 3','6','6','[6,6]'],['c7（接 c6）','[4,5]','1 + 1 + 1 = 3','4','4','[4,4]'],['c8（接 c6）','[2,3]','1 + 1 + 1 = 3','3','2','空（3 > 2）']],[2.6,1.9,2.9,1.1,1.1,2.6],.55,3.15,rowh=.38,size=15)
tb(s,.55,5.65,9.2,.5,'e：第一跳是 g；後面每跳是前一跳最早收完的時間 lo(I1) + δ1 + d1',16,NAVY)
s=new('第一包 ②：取出 L1，從 B 延伸','取出 L1，整包第 3 秒到 B。從 B 有 c2、c5 兩條。c2 只能第 6 秒起送，第 8 秒到 D；c5 只能第 10 秒起送，第 12 秒到 D。兩者都通過 Buffer 檢查。L1 離開 Q，但 L2、L3 的 pred 還指向它，回溯時用得到。')
topo(s,used=('c1',),cand=('c2','c5'),nodes=('B',))
timeline(s,[('c2 發送',[(6,7,BLUE)]),('D 接收',[(7,8,BLUE)]),('c5 發送',[(10,11,ORG)]),('D 接收',[(11,12,ORG)])],5,13,y=1.35)
tb(s,6.75,3.6,6,.6,'L2 key = 6+1+1 = 8；L3 key = 10+1+1 = 12',18)
qrow(s,[(L2a,True),(L3a,True)]);concl(s,'兩條都是候選；Q 依 key 排序，下一個取 L2。')
s=new('第一包 ③：第一個到目的地的 Label 就結束','L2 的 key 最小，取出後發現它到目的地，搜尋結束。L3 還留在 Q 裡，它不是被支配刪除，只是不必再探索。其他還沒展開的 Label，抵達都不會比目前這個早，因為每多走一跳 key 不會變小。')
topo(s,used=('c1',),cand=('c2',),nodes=('D',))
tb(s,6.85,1.6,5.9,2.6,['取出 L2，v(c2) = D','D 是目的地 → 搜尋結束','','L3 還在 Q，但不用再展開：',('它只是不必探索，不是被刪除',MUT)],20)
qrow(s,[(L3a,False)]);concl(s,'每多走一跳，key 不會變小，所以第一個取出的目的地 Label 最早。')
s=new('第一包 ④：回溯決定實際時間','回溯從最後一跳開始。c2 取區間最早 6。前一跳上限是 6−0−1=5，c1 的區間只有 2，所以取 2。沿著 pred 走回去，不是真的倒著傳。結果：c1 第 2 秒、c2 第 6 秒，第 8 秒到 D。')
topo(s,used=('c1','c2'),nodes=('X','B','D'))
table(s,[['Label','區間','上限','定案'],['L2：c2','[6,6]','最後一跳取最早','6'],['L1：c1','[2,2]','6 − 0 − 1 = 5','2']],[1.75,1.25,2.45,.8],6.65,1.45,rowh=.56,size=16)
tb(s,6.7,3.35,6.1,1,['c1 第 2 秒起送，第 3 秒到 B','c2 第 6 秒起送，第 8 秒整包到 D'],19)
concl(s,'最後一跳取最早；前面每一跳取「能接上的最晚時間」。')
s=new('第一包 ⑤：驗證後提交資源','驗證通過後才提交。預約 c1 [2,3)、c2 [6,7)。占用也要寫入：X 從 0 持有到 3；B 第 2 到 3 接收、3 到 6 等待、6 到 7 送出；D 第 7 到 8 接收，第 8 秒交付後離開。這些都會成為第二包的限制。圖只畫 B。')
topo(s,used=('c1','c2'))
chart(s,[('第一包在 B 的占用',[(0,0),(2,0),(3,4),(6,4),(7,0),(12,0)],BLUE,2.5,False),('上限 4 MB',[(0,4),(12,4)],MUT,1.5,True)],6.6,1.1,6.25,3.3,ymax=6,xmax=12)
tb(s,6.75,4.4,6,.45,'預約：F[c1] = {[2,3)}，F[c2] = {[6,7)}',18)
concl(s,'來源 X、中繼 B、目的地 D 的占用都寫入，換下一包。',y=5.1)
# ========== second bundle
La='L1=(c3,[1,1],SOURCE)  key=2';Lb='L2=(c4,[7,8],SOURCE)  key=8';Lc='L3=(c6,[1,1],SOURCE)  key=3';Ld='L4=(c7,[4,4],L3)  key=5'
s=new('第二包 ①：來源 A 先建立 c3 Label','第二包 A 到 D，g=1。Label 編號重新從 L1 開始。c3 開放 [1,2]，只能第 1 秒起送，第 2 秒到 B，key=2。來源檢查通過。收到整包只代表到得了，之後能不能等待，要延伸時才檢查。')
topo(s,cand=('c3',),nodes=('A',))
timeline(s,[('A 發送',[(1,2,BLUE)]),('B 接收',[(1,2,BLUE)])],0,5,y=1.45)
tb(s,6.75,3.05,6,.9,['c3：I = [1,1]，key = 1+1+0 = 2',('第二包重新編號，L1、L2…與第一包分開',MUT)],18)
qrow(s,[(La,True)]);concl(s,'到得了 B，不代表能在 B 等到下一跳。')
s=new('第二包 ②：c4 用一個 Label 保留整段時間','c4 開放 [7,9]，d=1，所以可以在第 7 到 8 秒任一時刻起送，區間是 [7,8]。不需要為第 7、7.5、8 秒各建 Label，一個 L2 就代表整段。key 用區間最早的 7，得到 8。')
topo(s,cand=('c4',),nodes=('A',))
timeline(s,[('c4 開放',[(7,9,LINE)]),('起送區間 I',[(7,8,BLUE)])],6,10,y=1.45)
tb(s,6.75,3.05,6,.9,['I = [7,8]：7.5 秒也包含在內','key = 7+1+0 = 8'],18)
qrow(s,[(La,False),(Lb,True)]);concl(s,'一個 Label 代表整段連續時間，不用逐秒列舉。')
s=new('第二包 ③：c6 加入，Q 依 key 排序','c6 第 1 秒起送、傳 1 秒、延遲 1 秒，第 3 秒到 C，key=3。建立順序是 c3、c4、c6，但 Q 依 key 排序，所以是 L1、L3、L2。取出順序由最早完整抵達決定，不看 contact 編號。')
topo(s,cand=('c6',),nodes=('A',))
timeline(s,[('A 發送',[(1,2,BLUE)]),('C 接收',[(2,3,BLUE)])],0,5,y=1.45)
tb(s,6.75,3.05,6,.5,'key = 1+1+1 = 3（δ = 1）',18)
qrow(s,[(La,False),(Lc,True),(Lb,False)]);concl(s,'取出順序看 key，不看 contact 編號。')
s=new('第二包 ④：取出 L1，c2 被預約擋住','取出 L1，第 2 秒到 B。c2 只能第 6 秒起送，但第一包預約了 [6,7)。傳送 1 秒時，起送落在開區間 (5,7) 都會撞到，所以 6 被扣掉，候選變空。這是時段被用掉，不是另外的配額判斷。')
topo(s,used=('c3',),rej=('c2',),nodes=('B',))
timeline(s,[('c2 開放',[(6,7,LINE)]),('已預約',[(6,7,ORG)]),('不可起送',[(5,7,PALER)])],4,8,y=1.45)
tb(s,6.75,3.5,6,.8,['預約 [6,7)，d = 1 → 扣除 (5,7)',('[6,6] − (5,7) = 空集合',RED)],19)
qrow(s,[(Lc,False),(Lb,False)]);concl(s,'拒絕原因：contact 的時段已被第一包預約。',color=RED)
s=new('第二包 ⑤：同一個 L1，c5 被 Buffer 擋住','c5 第 10 秒才能起送，所以第二包第 2 秒到 B 後要等到第 10 秒。第一包第 2 到 3 秒也在 B 接收，第 2 秒之後合計馬上超過 4 MB，第 3 秒達 8 MB。所以拒絕 c3→c5 這個延伸，但其他候選不受影響。')
topo(s,used=('c3',),rej=('c5',),nodes=('B',))
chart(s,[('第一包',[(0,0),(2,0),(3,4),(6,4),(7,0),(12,0)],BLUE,1.75,False),('第二包',[(0,0),(1,0),(2,4),(10,4),(11,0),(12,0)],ORG,1.75,False),('合計',[(0,0),(1,0),(2,4),(3,8),(6,8),(7,4),(10,4),(11,0),(12,0)],RED,3,False),('上限 4 MB',[(0,4),(12,4)],MUT,1.5,True)],6.6,1.1,6.25,3.7,ymax=10,xmax=12)
qrow(s,[(Lc,False),(Lb,False)]);concl(s,'拒絕原因：等待期間 B 超過上限；第 2 秒後即超限，第 3 秒達 8 MB。',color=RED)
s=new('第二包 ⑥：取出 L3，c7 可以傳','取出 L3，第 3 秒到 C。c7 開放 [4,5]，只能第 4 秒起送，通過收完才轉。C 第 2 到 3 接收、3 到 4 等待、4 到 5 送出，峰值 4 MB，沒超過上限。建立 L4，key=5，已到目的地但還要等它被取出。')
topo(s,used=('c6',),cand=('c7',),nodes=('C',))
timeline(s,[('C 接收',[(2,3,BLUE)]),('C 等待',[(3,4,LINE)]),('c7 發送',[(4,5,GRN)]),('D 接收',[(4,5,GRN)])],1,6,y=1.35)
tb(s,6.75,3.6,6,.5,'I = [4,4]，key = 4+1+0 = 5',18)
qrow(s,[(Ld,True),(Lb,False)]);concl(s,'C 最高 4 MB，沒有超過上限，建立新 Label。',color=GRN)
s=new('第二包 ⑦：同一個 L3，c8 已經來不及','c8 開放 [2,3]，d=1，最晚第 2 秒要起送。但整包第 3 秒才到 C，收完才能轉，所以 Head=3、Tail=2，沒有候選。如果允許邊收邊轉，這裡才可能用得上；現行模型不允許。')
topo(s,used=('c6',),rej=('c8',),nodes=('C',))
timeline(s,[('c8 開放',[(2,3,LINE)]),('C 接收',[(2,3,BLUE)]),('最早可送',[(3,4,RED)])],1,5,y=1.45)
tb(s,6.75,3.5,6,.8,['Head = 3（第 3 秒才收完）','Tail = 3 − 1 = 2  →  3 > 2，沒有候選'],18)
qrow(s,[(Ld,False),(Lb,False)]);concl(s,'拒絕原因：收完時已經來不及傳完。',color=RED)
s=new('第二包 ⑧：取出 L4，回溯並提交','L4 key=5 最小，取出後到目的地，搜尋結束；L2 還沒展開，也不是被刪除。回溯：c7 取 4；前一跳上限 4−1−1=2，c6 區間只有 1，取 1。驗證後提交 c6 [1,2)、c7 [4,5)，以及 A、C、D 的占用。未選的候選都不提交。')
topo(s,used=('c6','c7'),nodes=('A','C','D'))
table(s,[['Label','區間','上限','定案'],['L4：c7','[4,4]','最後一跳取最早','4'],['L3：c6','[1,1]','4 − 1 − 1 = 2','1']],[1.75,1.25,2.45,.8],6.65,1.45,rowh=.56,size=16)
tb(s,6.7,3.3,6.1,1.3,['c6 第 1 秒起送，第 3 秒到 C','c7 第 4 秒起送，第 5 秒整包到 D',('提交：F[c6] = {[1,2)}，F[c7] = {[4,5)}',MUT)],18)
qrow(s,[(Lb,False)]);concl(s,'先規劃的包不一定先到：第二包第 5 秒就到了。')
s=new('兩包結果與三種拒絕原因','第一包第 8 秒到達，第二包第 5 秒到達。第二包在 c2 因預約被拒、c5 因 Buffer 被拒、c8 因時間被拒。提醒：舊版第二包是 12 秒，現在 5 秒是因為取消了 c7 的獨立配額，不能當成區間搜尋的效果。')
table(s,[['Bundle','路徑','起送','到 D'],['第一包','X → B → D','2、6','第 8 秒'],['第二包','A → C → D','1、4','第 5 秒']],[2.2,4,2.2,3.5],.7,1.25,rowh=.5,size=18)
table(s,[['被拒絕的延伸','原因','屬於哪個限制'],['c3 → c2','唯一時段已被第一包預約','預約'],['c3 → c5','等待時 B 超過 4 MB','Buffer'],['c6 → c8','收完才轉時已來不及','時間']],[3,5.4,3.5],.7,3.05,rowh=.5,size=18)
concl(s,'路徑不是只看遠近；時間、預約和 Buffer 都會影響。',y=5.3)
# ========== interval value
s=new('區間 ①：預約可能把時間切成兩段','獨立的小例子。contact 開放 [1,10]，d=1，起送範圍是 [1,9]。已有預約 [3,5)，會撞到的是開區間 (2,5)。第 2 秒起送剛好在第 3 秒傳完，第 5 秒起送剛好接在預約後面，所以都可以。切成兩段要建兩個 Label，不能合併成 [1,9]，否則會誤以為第 3 秒也能送。')
timeline(s,[('contact 開放',[(1,10,LINE)]),('已預約',[(3,5,ORG)]),('可起送 I',[(1,2,GRN),(5,9,GRN)])],0,10,x=.8,y=1.4,w=11.6,rowh=.56,labw=1.6)
tb(s,.8,3.85,11.6,.5,'[1,9] − (2,5) = [1,2] ∪ [5,9]',24,NAVY,PP_ALIGN.CENTER)
tb(s,.8,4.45,11.6,.8,['每段連續區間各建一個 Label：(c, [1,2], pred) 和 (c, [5,9], pred)','兩段屬於同一條 contact，共用同一份預約 F[c] 和 Reached[c]'],18)
concl(s,'不能合併成 [1,9]，否則會誤以為第 3 秒也能送。',y=5.55)
s=new('區間 ②：同一段時間，可接不同下一跳','A→B 區間 [0,5]，傳 5 秒。B 上限 12 MB，第 6 到 8 秒背景 3 MB。接 B→D：只能第 5 秒起送，所以 A→B 只能第 0 秒。接 B→C：第 15 秒才能走，第 8 秒時已收量不可超過 9 MB，所以 A→B 要在第 3.5 到 5 秒。兩個範圍沒有交集，所以搜尋時不能先定時間。這些數字用程式的限制檢查核對過。')
timeline(s,[('接 B→D',[(0,.08,BLUE)]),('接 B→C',[(3.5,5,GRN)])],0,5,x=.8,y=1.45,w=11.6,rowh=.62,labw=1.6)
table(s,[['下一跳','限制','A→B 要何時起送'],['B→D','開放 [5,10]，傳 5 秒，只能第 5 秒起送','只能第 0 秒'],['B→C','第 15 秒才能走，要在 B 等比較久','第 3.5～5 秒']],[2,6.4,3.2],.8,3.2,rowh=.54,size=18)
concl(s,'兩個範圍沒有交集：先定一個時間，一定切斷其中一條路。',y=5.0)
s=new('區間 ③：回溯時為什麼取最晚','固定下一跳時間，前一跳越晚送，資料越晚進節點，占用越少。如果最晚的都不可行，更早的也不可行，所以 BufferFilter 每個 s2 只要測最晚的 s1*。回溯取最晚，就和檢查過的情況一致。抵達時間由最後一跳決定，不會因此變晚。但這只對這一包可行，對後面的包是否最好，目前還不知道。')
table(s,[['為什麼取最晚','說明'],['占用最少','前一跳越晚送，資料越晚進節點'],['和檢查一致','BufferFilter 測的就是最晚的 s1*'],['不影響抵達','抵達時間已由最後一跳決定']],[3.6,8.3],.7,1.35,rowh=.62,size=19)
tb(s,.75,4.05,11.8,.55,'上限 = s − δ(前一跳) − d(前一跳)，在前一跳的區間內取不超過上限的最大值',19)
concl(s,'取最晚對這一包可行，但對後面的包是否最好，目前尚未研究。',y=4.95,color=ORG)
# ========== detour
def mini(sl):
    N={'A':(.95,3.0),'B':(2.75,3.0),'V':(2.75,1.5),'D':(4.95,3.0),'F':(2.75,4.45)}
    E=[('A','B','c1',GRN,0),('B','V','c5',GRN,-.14),('V','B','c6',GRN,.14),('B','D','c7',GRN,0),('A','F','c9',LINE,0),('F','D','c10',LINE,0)]
    for u,v,k,c,o in E:
        (a,b),(e,f)=N[u],N[v]
        import math
        L=math.hypot(e-a,f-b);dx,dy=(e-a)/L,(f-b)/L
        arrow(sl,a+dx*.28+o,b+dy*.28,e-dx*.28+o,f-dy*.28,c,2.5 if c==GRN else 1.25)
    for t,x,y,c in(('c1',1.7,2.62,GRN),('c5',2.0,2.1,GRN),('c6',2.97,2.1,GRN),('c7',3.72,2.62,GRN),('c9',1.3,3.8,MUT),('c10',4.1,3.8,MUT)):
        tb(sl,x,y,.6,.3,t,14,c,PP_ALIGN.CENTER)
    for k,(a,b) in N.items():
        box(sl,a-.26,b-.26,.52,.52,k,fill=RGB(255,255,255),size=18,color=NAVY,shape=MSO_SHAPE.OVAL)
s=new('繞路：有時先離開，反而比較快','獨立的小例子。包 10 MB，M=10，B 在第 11 到 14 秒有其他資料占用，第 12、13 秒滿載。第 0 秒 A 送到 B，第 5 秒收完；第 5 秒送去 V，第 10 秒離開 B；第 15 秒從 V 回 B，第 20 秒收完；第 20 秒送往 D，第 22 秒到達。如果禁止回到走過的節點，只能走 F，第 30 秒才到。這個結果由程式跑過。')
mini(s)
timeline(s,[('c1',[(0,5,GRN)]),('c5',[(5,10,GRN)]),('B 滿載',[(11,14,RED)]),('c6',[(15,20,GRN)]),('c7',[(20,22,GRN)])],0,24,x=5.85,y=1.3,w=7.0,rowh=.45,labw=1.05,step=4)
tb(s,5.9,4.0,6.9,.9,['留在 B 等到第 20 秒：撞上滿載，不可行',('走 A→B→V→B→D：第 22 秒；不回訪只能走 F：第 30 秒',GRN)],17)
concl(s,'所以不禁止回到走過的節點，這就是 Buffer Detour。',y=5.5)
s=new('允許繞路，為什麼不會無限繞圈','三個理由：每跳都要等上一跳收完，時間一定前進；超過期限就沒有候選；同一 contact 的相同起送時間只處理一次。無意義的繞路不會被選中，但可能還是會被搜尋，增加計算量。終止性目前是論證，還沒寫成正式證明。')
cards=[('時間一定前進','s2 ≥ s1 + d1 + δ1，且 d = S/r > 0'),('時間有上限','超過期限 D*，就沒有候選時間'),('不重複處理','Reached[c]：相同 (c, s) 只建立一次')]
for i,(a,b) in enumerate(cards):
    x=.65+i*4.08
    box(s,x,1.55,3.85,2.45,fill=PALE,line=None)
    tb(s,x+.2,1.75,3.45,.6,a,23,NAVY)
    tb(s,x+.2,2.5,3.45,1.3,b,18)
tb(s,.7,4.3,11.9,.5,'同一包回到同一節點時，前一次一定已送完，不會和自己重疊。',19)
concl(s,'無意義的繞路不會被選中，但可能會被搜尋，增加計算量。',y=4.95)
s=new('目前可以主張與不能主張的事','可以說：這是一個把 contact、預約和 Buffer 一起考慮的候選方法，能在例子中找出可行排程。不能說：已證明最優、所有包整體最佳，或在真實網路一定較好。模型中的收完才轉、不設獨立配額和目的地收完即釋放，都還要和老師確認。本份不放實驗數據。')
box(s,.7,1.3,5.8,3.9,fill=PALEG,line=None);box(s,6.85,1.3,5.8,3.9,fill=PALER,line=None)
tb(s,.95,1.45,5.3,.55,'可以說',24,GRN);tb(s,7.1,1.45,5.3,.55,'還不能說',24,RED)
tb(s,.95,2.1,5.3,3,['同時考慮 contact、預約和 Buffer','Label 存區間，時間到回溯才決定','允許繞路，搜尋會結束（論證）'],19)
tb(s,7.1,2.1,5.3,3,['單包一定最優：還沒有正式證明','所有包整體最佳：逐包規劃不保證','真實網路較好：模型假設待確認'],19)
concl(s,'待確認的模型假設：收完才轉、不設獨立配額、目的地收完即釋放。',y=5.4)
# ========== backup
s=new('備用頁：完整演算法','以下是論文版的 4 個演算法，老師追問細節時再翻。')
tb(s,.8,2.4,11.7,1.5,['演算法 1：RoutePlan；演算法 2：SearchBundle','演算法 3：BufferFilter；演算法 4：Backtrack'],24,INK,PP_ALIGN.CENTER)
s=new('演算法 1：RoutePlan','驗證失敗代表演算法或程式有錯，要保存案例並停止。驗證檢查路徑、時段與期限、預約、收完才轉及全程 Buffer。')
code(s,["Input: contacts, bundles in a fixed order, node buffer limits","Output: for each bundle, a path with hop start times, or no path","","for each bundle B in the fixed planning order do","    L_goal ← SearchBundle(B)","    if L_goal = NO_PATH then","        record that B has no path; continue","    schedule ← Backtrack(L_goal)","    validate schedule independently; if any constraint fails, save the case and stop","    add each hop's period to F[c] and each node's occupancy to O_n","end for"],size=19)
s=new('演算法 2：SearchBundle','第一跳的最早時間是 g；後續跳是前一跳最早收完的時間。Range 算候選時間，Insert 去重並建立 Label。')
code(s,["Q ← priority queue ordered by key;  Reached ← ∅","for each c with u(c) = source(B) do","    C ← Range(c, g)","    C ← BufferFilter(C, source(B), source, c)","    if v(c) = destination(B) then","        C ← BufferFilter(C, v(c), destination, c)","    Insert(c, C, SOURCE)","","Range(c, e):","    [max(a(c),e), min(b(c)−d(c), D*−d(c)−δ(c))]","    minus (x−d(c), y) for each [x,y) in F[c]","Insert(c, C, pred):","    New ← C − Reached[c];  add New to Reached[c]","    push (c, I, pred) for each connected I in New"],x=.5,w=6.15,size=15.5)
code(s,["while Q ≠ ∅ do","    L1 = (c1, I1, pred1) ← extract min key","    if v(c1) = destination(B) then return L1","    for each c2 with u(c2) = v(c1) do","        C ← Range(c2, lo(I1) + δ(c1) + d(c1))","        C ← BufferFilter(C, v(c1), relay, c2, L1)","        if v(c2) = destination(B) then","            C ← BufferFilter(C, v(c2), destination, c2)","        Insert(c2, C, L1)","return NO_PATH"],x=6.75,w=6.2,size=15.5)
s=new('演算法 3：BufferFilter','三種節點共用同一個不等式，差別在這一包的占用 Own 和檢查時間。')
code(s,["if mode is source then","    Own(t,s) ← S − Sent(t,s);  t ∈ [g, s + d(c)]","else if mode is relay then","    s1*(s) ← max{ x ∈ I1 : x ≤ s − δ(c1) − d(c1) }","    Own(t,s) ← Recv(t, s1*(s)) − Sent(t,s);  t ∈ [s1*(s) + δ(c1), s + d(c)]","else","    Own(t,s) ← Recv(t,s);  t ∈ [s + δ(c), s + d(c) + δ(c)]","split C into segments at breakpoints of O_n(t) and Own","for each segment G do","    solve O_n(t) + Own(t,s) ≤ M_n and add each feasible s in G to R","return R"],size=18)
s=new('演算法 4：Backtrack','最後一跳取區間下界，往前每跳取不超過上限的最大值。')
code(s,["L ← L_goal;  s ← lo(I(L))","schedule ← [(c(L), s)]","while pred(L) ≠ SOURCE do","    P ← pred(L)","    s ← max{ x ∈ I(P) : x ≤ s − δ(c(P)) − d(c(P)) }","    prepend (c(P), s) to schedule;  L ← P","end while","return schedule"],size=21)

# ========== 符號小註解
D={'node':'X、A、B、C、D：節點','nodeA':'A、B、C：節點','nodeD':'A、B、C、D：節點','nodeV':'A、B、V、D、F：節點','ci':'c1、c2…：各條 contact','c':'c：contact','L':'L：Label','Li':'L1、L2…：Label 編號（每包重新編號）','I':'I：可起送區間','win':'[a, b]：contact 開放時間','pred':'pred：前一個 Label','src':'SOURCE：第一跳的 pred 標記','key':'key：最早完整抵達時間','Q':'Q：待處理 Label 的佇列','g':'g：可開始傳送的時間','S':'S：包大小','r':'r：速率','M':'M：Buffer 上限','d':'d：傳完一包的時間','delta':'δ：傳播延遲','s':'s：起送時間','A':'A：整包抵達時間','lo':'lo(I)：區間 I 的最早時間','s12':'s1、s2：前一跳、下一跳的起送時間','F':'F[c]：c 已預約的時段','half':'[x, y)：含 x、不含 y 的時段','open':'(x, y)：不含兩端的時段','HT':'Head、Tail：候選範圍的最早、最晚時間','R':'Reached[c]：c 已處理過的起送時間','Ds':'D*：抵達期限','uv':'u(c)、v(c)：c 的傳送端、接收端','Own':'Own：這一包在節點的占用','On':'O_n：節點 n 的既有占用','Mn':'M_n：節點 n 的 Buffer 上限','SR':'Sent、Recv：已送出、已收到的量','star':'s1*：最晚可行的前一跳起送時間','sch':'schedule：每一跳的 (c, s)','goal':'L_goal：到目的地的 Label','abm':'a(c)、b(c)：c 開始、結束時間','e':'e：這一跳最早可開始的時間','new':'New：扣除已處理後的新時間','C':'C：候選起送時間集合','P':'P：前一個 Label','G':'G：C 切出的小段','mode':'R：可行的起送時間','t':'t：檢查占用的時間','cj':'c1、c2：前一跳、下一跳 contact','I1':'L1=(c1,I1,pred1)：目前取出的 Label','term':'Bundle：要傳送的資料包；Buffer：節點的暫存空間'}
K0={2:'node',3:'term',4:'nodeA',5:'L c I pred src',6:'Q key',7:'ci s12',8:'node ci win g S r d M delta',
9:'ci L I key src Q win HT g S r',10:'ci Li pred key Q',11:'ci Li uv Q',12:'ci Li s d delta',13:'ci win F half',
14:'ci Li I key src Q g',15:'ci Li I key Q win',16:'ci Li I key Q delta',17:'ci Li Q half open d',18:'ci Li Q M',19:'ci Li I key Q win',20:'ci Li Q HT win d',21:'ci Li Q F half delta d',22:'ci node',
23:'c F R win open half pred',24:'nodeD win',25:'s star delta d lo',26:'ci nodeV',27:'s12 d S r delta Ds R c',28:'',
30:'goal sch F On',31:'Q key R uv g lo delta d I1 C e Ds abm F new',32:'Own On Mn S SR g star I1 delta d C G mode t',33:'goal lo sch pred src P s delta d'}
K={(k if k<10 else k+1):v for k,v in K0.items()}
K[10]='win HT e g d delta Ds lo I'
for i,sl in enumerate(p.slides,1):
    ks=K.get(i,'').split()
    if not ks:continue
    txt='；'.join(D[k] for k in ks)
    long=len(txt)>=165
    tb(sl,.5,5.72 if long else 6.45,9.25,1.25 if long else .54,'符號：'+txt,11 if long else (10.5 if len(txt)>=120 else 11.5),MUT,name='symbol-note')

p.save('walk.pptx');print(len(p.slides))
