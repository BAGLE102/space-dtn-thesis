exec(open('v112.py').read().split("res=p.slides[29]")[0])
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
p=Presentation('v125.pptx')
old=list(p.slides._sldIdLst)
T=p.slides[31]
RED,GRAY,LIGHT=RGB.from_string('B03A2E'),RGB.from_string('9A9A9A'),RGB.from_string('F0EFF6')
def new(title,bottom,notes):
    s=p.slides.add_slide(T.slide_layout)
    for ph in list(s.placeholders):ph._element.getparent().remove(ph._element)
    for x in list(T.shapes)[:3]:s.shapes._spTree.append(copy.deepcopy(x._element))
    setText(s.shapes[0],title);setText(s.shapes[1],bottom);s.notes_slide.notes_text_frame.text=notes;return s
def box(s,x,y,w,h,t,fill='F0EFF6',line='B5B2CF',sz=16,c=None,bold=False):
    b=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,In(x),In(y),In(w),In(h));b.adjustments[0]=.12
    b.fill.solid();b.fill.fore_color.rgb=RGB.from_string(fill);b.line.color.rgb=RGB.from_string(line);b.line.width=Pt(.75);b.shadow.inherit=False
    f=b.text_frame;f.word_wrap=True;f.vertical_anchor=MSO_ANCHOR.MIDDLE
    for i,line_t in enumerate(t.split('\n')):
        para=f.paragraphs[0] if i==0 else f.add_paragraph();para.alignment=PP_ALIGN.CENTER
        r=para.add_run();r.text=line_t;font(r,sz,c or NAVY);r.font.bold=bold
    return b
def arrow(s,x1,y1,x2,y2,col='747474'):
    c=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,In(x1),In(y1),In(x2),In(y2));c.line.color.rgb=RGB.from_string(col);c.line.width=Pt(1.5)
    ln=c.line._get_or_add_ln();te=etree.SubElement(ln,qn('a:tailEnd'));te.set('type','triangle');return c
def rect(s,x,y,w,h,col):
    b=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,In(x),In(y),In(w),In(h));b.fill.solid();b.fill.fore_color.rgb=RGB.from_string(col);b.line.fill.background();b.shadow.inherit=False;return b
def hline(s,x1,y,x2,col='747474',w=1,dash=False):
    c=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,In(x1),In(y),In(x2),In(y));c.line.color.rgb=RGB.from_string(col);c.line.width=Pt(w)
    if dash:c.line.dash_style=7
    return c
def poly(s,pts,col,w=2.5,dash=False):
    ff=s.shapes.build_freeform(In(pts[0][0]),In(pts[0][1]),scale=1.0)
    ff.add_line_segments([(In(x),In(y)) for x,y in pts[1:]],close=False);sh=ff.convert_to_shape()
    sh.fill.background();sh.line.color.rgb=RGB.from_string(col);sh.line.width=Pt(w);sh.shadow.inherit=False
    if dash:sh.line.dash_style=7
    return sh
def bullets(s,x,y,w,items,sz=18,gap=.5,c=INK):
    for k,t in enumerate(items):tb(s,x,y+k*gap,w,gap-.06,t,sz,c)
def axis(s,x0,x1,y,ticks,unit='秒'):
    hline(s,x0,y,x1)
    for t,x in ticks:
        s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,In(x),In(y),In(x),In(y+.06)).line.color.rgb=RGB.from_string('747474')
        tb(s,x-.2,y+.08,.4,.25,str(t),12,MUT)
    tb(s,x1+.05,y+.08,.4,.25,unit,12,MUT)

# 1
s=new('Buffer 檢查的修改：從整段停用到逐步使用','上次：有占用的時段整段不給用；這次：只要容量沒滿就能用。',
'上次跟老師報告的版本，Buffer 的處理是只要節點在某段時間有其他包占用，這段時間就整段不讓新包停留。這樣一定不會超過上限，所以是對的，但很保守。這次我把它改成按容量逐步使用：只要每個時刻的總占用不超過上限 M，就可以用。接下來依序說明上次的做法、問題在哪、改成什麼、演算法怎麼做，以及怎麼確認改完還是對的。')
bullets(s,.95,1.45,11.4,['上次的做法：節點有占用的時段，新包不能停留（正確但保守）',
 '問題：M = 3 MB 可以同時放 3 包，舊規則卻只讓它放 1 包',
 '現在的做法：每個時刻 O_n(t) + 這包的占用 ≤ M 就可以用',
 '演算法：搜尋時逐跳篩選可行起送時間；接受後才把占用寫入',
 '正確性：獨立檢查、窮舉比對、拿掉篩選測試'],20,.66)
# 2
s=new('上次的做法：有占用就整段停用','一定不會超過上限，所以是對的；但可行的時間也會被擋掉。',
'上次的規則是：新包要在節點 n 停留的這段期間，只要 O_n(t) 大於 0，也就是已經有別的包在，就整段不能用。它為什麼是對的？因為同一個節點同時最多只會有一包，占用最多就是 S，而我們一開始就要求 S 不超過 M，所以不會爆。問題是 M 可能比 S 大很多。實驗裡 M 是 3 MB、包是 1 MB，可以同時放 3 包，舊規則卻只讓它放 1 包，剩下的容量都浪費了，其他包只能改道、等待或被拒絕。')
box(s,.95,1.35,11.4,.62,'規則：新包在節點 n 停留的期間，只要 O_n(t) > 0（已有別的包），整段不可用',sz=18,c=INK)
tb(s,.95,2.15,11.4,.42,'可行條件：停留期間的每個 t，O_n(t) = 0',20,NAVY)
tb(s,.95,2.75,11.4,.42,'為什麼正確：同一節點同時最多一包 → 占用 ≤ S ≤ M',18,INK)
tb(s,.95,3.25,11.4,.42,'代價：M = 3 MB、S = 1 MB 時，可以放 3 包卻只放 1 包',18,INK)
# timeline
tb(s,.95,4.15,1.6,.3,'B 已有包',14,MUT)
X=lambda t:2.75+(t-6)*.45
hline(s,X(6),4.3,X(24),'D0D0D0',.75);rect(s,X(10),4.2,X(20)-X(10),.2,'9A9A9A')
tb(s,.95,4.65,1.6,.3,'新包想停留',14,MUT);hline(s,X(6),4.75,X(24),'D0D0D0',.75);rect(s,X(12),4.65,X(18)-X(12),.2,'3932A8')
axis(s,X(6),X(24),5.15,[(t,X(t)) for t in (6,10,12,18,20,24)])
tb(s,.95,5.55,11.4,.4,'舊規則：新包停留的 [12, 18] 和 B 已有的包重疊 → 拒絕（但 1 + 1 = 2 MB，其實放得下）',17,RED)
# 3
s=new('三種檢查方式：由嚴到寬','舊 ⊆ 整包預留 ⊆ 逐步使用：三者都不會超過 M，越往下可行的時間越多。',
'修改時我把條件分成三層看。第一層是舊規則，停留期間占用要等於 0。第二層是整包預留，假設新包整段停留期間都占滿 S，只要原本占用的最高點加上 S 不超過 M 就可以。第三層是現在的做法，逐 byte 計算，新包接收時占用慢慢增加、送出時慢慢減少，只要每個時刻的總和不超過 M。這三層是包含關係：舊規則成立時，最高點是 0，加上 S 一定不超過 M，所以整包預留也成立；整包預留成立時，每個時刻的占用都不超過最高點加 S，所以逐步使用也成立。因此放寬之後不會變錯，只會多接受原本被擋掉的時間。整包預留在演算法裡當作快速通過的捷徑。')
table(s,.95,1.3,[2.6,4.6,4.2],[['做法','停留期間的條件','例：B 已有 1 包、M = 3 MB'],
 ['舊：有占用就停用','每個 t：O_n(t) = 0','不可（有重疊）'],
 ['整包預留','max O_n(t) + S ≤ M','可（1 + 1 = 2 ≤ 3）'],
 ['逐步使用（現在）','每個 t：O_n(t) + own(t) ≤ M','可']],sz=18,rh=.62)
tb(s,.95,4.05,11.4,.4,'own(t)：新包在這個節點的占用，接收時 0 → S、等待時 S、送出時 S → 0',16,MUT)
tb(s,.95,4.55,11.4,.4,'為什麼放寬後仍然正確：上一列成立 ⇒ 下一列一定成立；而最後一列本身就是「不超過 M」',18,GRN)
tb(s,.95,5.05,11.4,.4,'O_n(t)：已接受的包在節點 n 的占用；S：包大小；M：Buffer 上限',14,MUT)
# 4
s=new('逐步使用：每個節點的占用怎麼算','每個角色只差在「這包的占用」和「停留期間」，檢查條件都一樣。',
'這包在節點上的占用依角色不同。來源從產生時間 g 就持有整包，送出時逐 byte 減少。中繼從開始接收 h 起逐 byte 增加，整包收完後維持 S 等下一跳，再逐 byte 送出。目的地逐 byte 接收，整包收完的瞬間交付，占用歸零。R 表示從 0 線性增加到 S 的函數，也就是逐 byte 接收或送出。三種角色的檢查條件都是同一條：停留期間每個時刻 O_n(t) 加上 own(t) 不超過 M。')
table(s,.95,1.3,[1.7,5.5,4.2],[['角色','這包的占用 own(t)','停留期間'],
 ['來源','S − R(t; s, s + d)','[g, s + d]'],
 ['中繼','R(t; h, A) − R(t; s₂, s₂ + d₂)','[h, s₂ + d₂]'],
 ['目的地','R(t; h, A)，收完瞬間歸零','[h, A]']],sz=18,rh=.62)
tb(s,.95,3.95,11.4,.42,'檢查條件（三種角色相同）：停留期間每個 t，O_n(t) + own(t) ≤ M',20,NAVY)
tb(s,.95,4.55,11.4,.36,'R(t; t₀, t₁)：從 t₀ 到 t₁ 由 0 線性增加到 S（逐 byte 接收或送出）',15,MUT)
tb(s,.95,4.95,11.4,.36,'s：起送時間；d：傳完一包的時間；h = s + δ：開始接收；A = h + d：整包收完；g：產生時間',15,MUT)
# 5 example
s=new('例子：逐步使用比整包預留多接受','整包預留：2 + 4 = 6 > 4 → 拒絕；逐步使用：每個時刻都 ≤ 4 → 可行。',
'這個例子 S=4 MB，B 的上限也是 4 MB。B 原本有一包正在送出，占用從第 0 秒的 2 MB 線性降到第 2 秒的 0。新包從第 0 秒開始以 1 MB/s 接收，第 4 秒收完。舊規則看到第 0 到 2 秒有占用，直接拒絕。整包預留假設新包一開始就占滿 4 MB，2 加 4 等於 6，超過 4，也拒絕。逐步使用看每個時刻：前 2 秒新包只收了 0 到 2 MB，總和一直是 2 MB；之後背景已經清空，總和就是新包本身，第 4 秒剛好 4 MB，沒有超過。所以只有逐步使用接受。如果改成等背景清空才開始收，第 2 秒才開始，就來不及在第 4 秒前收完。')
x0,yb,sx,sy=1.3,5.25,1.25,.62
for v in (0,2,4,6):
    hline(s,x0,yb-v*sy,x0+4*sx,'E3E3E3',.5);tb(s,x0-.5,yb-v*sy-.13,.4,.26,str(v),12,MUT)
tb(s,x0-.75,yb-6*sy-.5,1.2,.3,'占用 MB',12,MUT)
axis(s,x0,x0+4*sx,yb,[(t,x0+t*sx) for t in range(5)])
P=lambda pts:[(x0+t*sx,yb-v*sy) for t,v in pts]
hline(s,x0,yb-4*sy,x0+4*sx,'B03A2E',1.5,True)
poly(s,P([(0,2),(2,0),(4,0)]),'9A9A9A',2)
poly(s,P([(0,0),(4,4)]),'3932A8',2)
poly(s,P([(0,2),(2,2),(4,4)]),'187A3E',3)
for k,(t,c) in enumerate([('M = 4 MB 上限','B03A2E'),('背景占用','9A9A9A'),('新包占用','3932A8'),('合計','187A3E')]):
    hline(s,6.55,1.5+k*.35,6.85,c,2.5);tb(s,6.95,1.37+k*.35,1.8,.26,t,13,INK)
table(s,8.75,1.3,[.75,.85,.85,.85],[['t','背景','新包','合計'],['0','2','0','2'],['1','1','1','2'],['2','0','2','2'],['3','0','3','3'],['4','0','4','4']],sz=15,rh=.42)
tb(s,6.55,4.0,5.6,.34,'S = 4 MB、M = 4 MB、速率 1 MB/s、δ = 0',14,MUT)
tb(s,6.55,4.4,5.6,.34,'舊規則：0～2 秒有占用 → 拒絕',15,INK)
tb(s,6.55,4.78,5.6,.34,'等背景清空再收：第 2 秒才開始，來不及',15,INK)
# 6 search
s=new('演算法怎麼做（一）：搜尋時逐跳篩選','每展開一跳都做一次，會爆的起送時間在搜尋中就被扣掉。',
'搜尋時，每次從 Q 取出一個 Label、往下一跳展開，都要對那個節點做一次 Buffer 篩選。第一步，Range 先依 contact 開放時段、期限和預約算出候選起送區間。第二步是快速通過：如果停留期間原本占用的最高點加上 S 都不超過 M，就整段保留，不用細算，Buffer 寬鬆時大多走這條路。第三步，快速檢查沒通過時，用 O_n 的轉折點把候選區間切成很多小段。每一小段裡，總占用都是起送時間的一次函數，可以直接解不等式，留下可行的部分。中繼節點的占用由上一跳和下一跳兩個時間決定，對每個下一跳起送時間，只測上一跳最晚的起送時間 s1 星號，因為越晚到、在中繼等越短、占用越少，最晚到都會爆的話，早到一定也會爆。最後，剩下的時間建成 Label 放進 Q。')
steps=['Range：依 contact 開放時段、期限、預約，算候選起送區間 I',
 '快速通過：停留期間 max O_n(t) + S ≤ M → 整段保留',
 '否則精確切割：用 O_n 的轉折點把 I 切成小段，每段解一次不等式',
 '中繼只測上一跳最晚起送：s₁* = min(hi(I₁), s₂ − δ₁ − d₁)',
 '剩下的時間建 Label 放進 Q；搜尋中不寫入占用']
for k,t in enumerate(steps):
    box(s,.95,1.3+k*.86,.6,.6,str(k+1),sz=18,bold=True)
    tb(s,1.75,1.3+k*.86,10.6,.6,t,19,INK)
# 7 commit
s=new('演算法怎麼做（二）：接受後才更新占用','搜尋中的 Label 只是候選；只有通過獨立檢查並提交後，下一包才看得到。',
'找到目的地 Label 後，先回溯決定每一跳的起送時間：最後一跳取最早，前面每跳取不超過上限的最晚時間，和搜尋時中繼檢查的 s1 星號一致。接著用獨立的 Validate 重新檢查整條排程，它不呼叫任何搜尋或篩選函式，在每個轉折點驗算占用不超過 M。通過後 Commit：每一跳的傳送時段寫入預約 F，每個經過的節點把這包的占用曲線疊加到 O_n(t)。下一包規劃時，看到的就是更新後的 F 和 O。搜尋過程中各個 Label 都不寫入，互不影響。')
labels=['回溯\n決定起送時間','Validate\n獨立重檢','Commit\n寫入 F 與 O_n(t)','下一包\n用更新後的 O_n(t)']
xs=[.95,4.0,7.05,10.1]
for k,(x,t) in enumerate(zip(xs,labels)):
    box(s,x,1.6,2.3,1.1,t,fill='E3F1E7' if k==2 else 'F0EFF6',line='187A3E' if k==2 else 'B5B2CF',sz=17,c=GRN if k==2 else NAVY)
    if k<3:arrow(s,x+2.35,2.15,xs[k+1]-.05,2.15)
bullets(s,.95,3.2,11.4,['回溯：最後一跳取最早；前面每跳取 ≤ s_next − δ − d 的最晚時間',
 'Validate：不呼叫搜尋程式，在每個轉折點驗 O_n(t) + own(t) ≤ M（左右極限都檢查）',
 'Commit：來源 [g, s₁] 為 S 再降到 0；中繼升到 S、等待、降到 0；目的地升到 S 後歸零'],17,.55)
# 8 diff
s=new('改了哪些地方','節點狀態從「有沒有人在用」改成「現在用了多少」。',
'這頁整理上次規則和現在做法的差別。節點的狀態從有沒有占用，改成占用多少的曲線。篩選條件從停留期間占用要等於 0，改成每個時刻占用加上這包不超過 M。篩選結果從扣掉有占用的時段，改成解不等式得到確切的可行起送時間。提交時從標記這段時間被占用，改成把這包的占用曲線疊加上去。另外新增了快速通過和中繼只測最晚起送這兩個處理。')
table(s,.95,1.3,[2.2,4.4,4.8],[['項目','上次的規則','現在'],
 ['節點狀態','哪些時段有占用（有／沒有）','占用曲線 O_n(t)（分段線性，MB）'],
 ['可行條件','停留期間 O_n(t) = 0','每個 t：O_n(t) + own(t) ≤ M'],
 ['篩選結果','扣掉有占用的時段','解不等式，得到確切的可行起送時間'],
 ['提交','標記停留時段為占用','把這包的占用曲線疊加到 O_n(t)'],
 ['新增處理','—','快速通過；中繼只測最晚起送 s₁*']],sz=17,rh=.66)
# 9 correctness
s=new('怎麼確認改完還是對的','測試沒有發現違反 Buffer 上限的排程；正式證明尚未完成。',
'放寬條件最怕的是放太寬，排出會爆的排程。我用三種方式檢查。第一，獨立檢查：每一包被接受前都用 Validate 重檢，它不呼叫搜尋程式；多包實驗兩個環境共 480 次執行，沒有任何一次失敗。第二，和窮舉比對：4,701 個小案例，節點有隨機的背景占用，Buffer 上限只比包大 0 到 2，正好是需要逐步使用的情況；9,311 次查詢中沒有一次本方法比窮舉晚，也沒有不合法排程。第三，拿掉篩選測試：分別拿掉來源、中繼、目的地的篩選，會出現 79、27、32 個不合法排程，表示這個測試抓得到錯誤。限制是窮舉和本方法共用模型規則，而且還沒有正式證明。另外還沒有直接量化舊規則和新做法的送達率差距。')
table(s,.95,1.3,[3.2,5.9,2.3],[['檢查','做法','結果'],
 ['獨立檢查','每包接受前用 Validate 重檢；多包實驗共 480 次執行','失敗 0 次'],
 ['窮舉比對','4,701 個小案例（含背景占用，M 只比 S 大 0～2）、9,311 次查詢','較晚、不合法 0 次'],
 ['拿掉篩選','分別拿掉來源、中繼、目的地的 Buffer 篩選','不合法 79／27／32 次']],sz=17,rh=.72)
tb(s,.95,4.4,11.4,.38,'尚未完成：逐步使用的正式證明；舊規則與現在做法的送達率量化比較',17,RED)
tb(s,.95,4.85,11.4,.38,'限制：窮舉與本方法共用模型規則，抓不到規則本身的錯誤',15,MUT)
# remove old slides and renumber
L=p.slides._sldIdLst
for e in old:
    p.part.drop_rel(e.get(qn('r:id')));L.remove(e)
for i,s in enumerate(p.slides,1):
    setText(s.shapes[2],str(i))
p.save('buffer_update_v1.pptx');print(len(p.slides))
