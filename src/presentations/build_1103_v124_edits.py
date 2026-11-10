exec(open('v112.py').read().split("res=p.slides[29]")[0])
from pptx.util import Emu
p=Presentation('v123.pptx')
def pg(t):
    r=[s for s in p.slides if s.shapes[0].text_frame.text.startswith(t)];assert len(r)==1,t;return r[0]
def sh(s,t):
    r=[x for x in s.shapes if x.has_text_frame and x.text_frame.text.startswith(t)];assert len(r)==1,(t,len(r));return r[0]
def notes(s,t):s.notes_slide.notes_text_frame.text=t
def cellset(c,t):
    rs=c.text_frame.paragraphs[0].runs;rs[0].text=t
    for r in rs[1:]:r.text=''
    for para in c.text_frame.paragraphs[1:]:
        for r in para.runs:r.text=''
# 8
s=pg('如何算可行起送區間');setText(s.shapes[1],'預約把可行時間切成 [1,2] 和 [5,9] 兩段，每段各建一個 Label。')
# 9
s=pg('Label、Q 與 Reached');g=[x for x in s.shapes if x.has_table][0];T=g.table
tr=T._tbl.tr_lst[4];h=T.rows[4].height;T._tbl.remove(tr);g.height=g.height-h
n=s.notes_slide.notes_text_frame.text;notes(s,n.replace('不同 contacts 到同節點不能僅憑早到刪除。',''))
# 15,24
for t in ('第一包：選取目的地並回溯','第二包：沿 pred 選定'):
    s=pg(t);setText(sh(s,'lo(I)：'),'lo(I)：區間最早時間；δ、d：該跳的傳播延遲、傳完一包的時間；O：既有占用；S：包大小；M：Buffer 上限')
# 17
s=pg('第二包：來源 A 先建立 c3');setText(s.shapes[0],'來源 A 建立三個 Label（先看 c3）')
# 29
s=pg('實驗環境');T=[x for x in s.shapes if x.has_table][0].table
cellset(T.cell(2,1),'每條 contact 均勻隨機抽：節點對（單向）、長度 30～300 秒、開始時間 0～3,600 秒')
cellset(T.cell(3,1),'每條 contact 均勻隨機抽速率 1、2、5 MB/s 與傳播延遲 0、0.1、0.25、0.5 秒')
notes(s,s.notes_slide.notes_text_frame.text.replace('每條 contact 隨機抽節點對、開始時間、長度、速率和延遲，都是單向。','每條 contact 都是均勻隨機抽：先抽傳送端，再抽不同的接收端，然後抽開始時間、長度、速率和延遲，都是單向。'))
# 30
s=pg('做了哪些實驗');setText(sh(s,'簡化版 SR-CGR'),'簡化版 SR-CGR（依 [1]）：來源算 k 條路徑，選路不看 Buffer，取第一條可行；全不可行就拒絕。')
notes(s,s.notes_slide.notes_text_frame.text+'要注意，文獻 [1] 的版本找不到可行路徑時會等一個時間步再重試，所以它的實驗裡所有包最後都送達，比較的是延遲和重選路次數；我們的簡化版直接拒絕，才能用送達率比較。')
# 32
s=pg('多包結果：Buffer 吃緊');setText(s.shapes[1],'30 MB 差異幾乎消失；contact 使用率低於 1%，瓶頸是 Buffer，這個環境對本方法有利。')
setText(sh(s,'3 MB：本方法'),'3 MB：40 個 seed 都贏；但對照組改成盡晚送，k=1 就高 2～8 個百分點。')
notes(s,'左邊 Buffer 3 MB，右邊 30 MB。3 MB 時本方法送達率比 k=10 高約 4 到 13 個百分點，40 個 seed 都贏兩個對照組。但差距不全是選路看不看 Buffer：對照組每跳都盡早送，包會在中繼節點等比較久。我讓 k=1 在失敗時改成盡晚送，送達率就提高 2 到 8 個百分點，下一頁會細講。30 MB 時四組都是 99.3% 到 100%，差異主要出現在 Buffer 吃緊時。平均 contact 使用率低於 1%，瓶頸幾乎都是 Buffer，所以這個環境對本方法有利。這是自訂隨機拓樸和簡化版 SR-CGR，不能外推到真實網路。')
# 33
s=pg('多包結果：延遲與計算時間');notes(s,s.notes_slide.notes_text_frame.text.replace('右圖是 3 MB 的每包平均計算時間，本方法在所有組別是 0.05 到 0.58 秒，k=1 約 0.006 到 0.017 秒。','右圖是 3 MB 的每包平均計算時間：本方法 0.14 到 0.58 秒，k=10 是 0.068 到 0.30 秒，k=1 是 0.005 到 0.016 秒。最慢的一包約 5.5 秒。'))
# 34
s=pg('多包結果：contact 較吃緊');setText(s.shapes[1],'contact 較緊時本方法幾乎沒有優勢；15 MB 時三種方法送達率只有約 17～72%。')
notes(s,s.notes_slide.notes_text_frame.text+'要先說明送達率本身很低：15 MB 時三種方法只有約 17% 到 72%，N=300 最低。因為 contact 只有 5 到 30 秒、速率 1 或 2 MB/s，一條 contact 只能傳幾包，Buffer 又只放 3 包，所以大部分包是真的沒有可行路徑，不是哪個方法選錯。')
# 35
s=pg('限制與尚未解決');setText(sh(s,'對照組：'),'對照組：簡化版 SR-CGR 不在中繼重選路、不重試；文獻 [1] 會重試，全部送達後比延遲')
notes(s,s.notes_slide.notes_text_frame.text.replace('SR-CGR 是自行實作的簡化版，沒有逐跳重算。','SR-CGR 是自行實作的簡化版，沒有中繼節點重選路，找不到路就直接拒絕；文獻 [1] 會等一個時間步再重試，所以它的實驗全部送達，比的是延遲。'))
# 36
s=pg('請老師決定');g=[x for x in s.shapes if x.has_table][0];T=g.table
for row in (['來源 Buffer 從產生時間就算嗎？','產生後立即占用','3 MB 失敗有 35% 在來源'],['碰撞率怎麼定義？負載多少合理？','被拒絕包數／總包數；600 秒內產生','k=1 在 3 MB 時為 9～53%']):
    tr=copy.deepcopy(T._tbl.tr_lst[-1]);T._tbl.append(tr)
    for j,t in enumerate(row):cellset(T.cell(len(T.rows)-1,j),t)
rh=int(g.height/len(T.rows))
for r in T.rows:r.height=rh
notes(s,'這頁是本次討論要帶走的決定。前三項影響模型與所有實驗數字；第四項影響比較的可信度；第五項影響研究目標與 ILP 基準要不要做。第六項：目前來源從產生時間就占用 Buffer，3 MB 時 k=1 的失敗有 35% 發生在來源；如果來源不算，k=1 送達率會提高 4 到 15 個百分點。第七項：碰撞率目前定義為被拒絕的包占全部包的比例；全部包在前 600 秒產生，負載偏高，需要老師決定合理範圍。')
# 37
s=pg('參考文獻');setText(s.shapes[1],'SR-CGR 見 [1] §II-E、§V：找不到路會等一個時間步重試，實驗全部送達，比的是延遲。')
notes(s,'SR-CGR 的定義和 benchmark 來自文獻 [1]：來源用 Yen 算 k 條最短路徑，k=10，計算時看不到 Buffer。[1] 的版本在中繼節點會檢查 Buffer，失敗時重新選路或退回來源；找不到可行路徑時等一個時間步再重試，所以它的實驗送達率都是 1，比較的是延遲和重選路次數。容量也用線性體積扣除。我們的簡化版沒有中繼重選路，也不重試，而是依序回放候選路徑，取第一條可行的，都不行就拒絕。所以結果不能當成和 [1] 的 SR-CGR 直接比較。文獻 [3] 說明 CGR 常用 Yen 演算法。')
# ---- structural
L=p.slides._sldIdLst
def idx(s):return list(p.slides).index(s)
def blank_from(src,at):
    s=p.slides.add_slide(src.slide_layout)
    for ph in list(s.placeholders):ph._element.getparent().remove(ph._element)
    e=L[-1];L.remove(e);L.insert(at,e);return s
# new diagnosis slide after 32
r32=pg('多包結果：Buffer 吃緊');d=blank_from(r32,idx(r32)+1)
for x in list(r32.shapes)[:3]:d.shapes._spTree.append(copy.deepcopy(x._element))
setText(d.shapes[0],'3 MB 碰撞率為什麼高');setText(d.shapes[1],'沒有找到計算錯誤；碰撞率高主要來自負載設定：全部包集中在前 600 秒產生。')
table(d,.92,1.25,[4.3,1.575,1.575,1.575,1.575],[
 ['只改一項（k=1 送達率 %）','20 節點\nN=100','20 節點\nN=300','40 節點\nN=100','40 節點\nN=300'],
 ['原設定（Buffer 3 MB）','70.2','47.3','91.4','70.8'],
 ['產生時間 0～600 → 0～3,000 秒','96.3','80.0','100','98.3'],
 ['來源 Buffer 不計','79.7','61.8','95.3','80.8'],
 ['失敗時改成盡晚送','77.7','53.3','93.7','77.3'],
 ['Buffer 3 → 5 MB','84.4','59.4','98.2','84.2'],
 ['Buffer 3 → 10 MB','98.0','79.3','99.8','97.2'],
 ['參考：本方法（3 MB）','89.0','62.7','98.4','89.1']],sz=16,rh=.44)
tb(d,.92,5.1,11.5,.38,'碰撞率 = 被拒絕包數／總包數；k=1 原設定為 9～53%。失敗位置：來源 35%、中繼 54%、目的地 11%',16,INK)
tb(d,.92,5.5,11.5,.38,'Buffer 只放 3 包；來源產生後立即占用；對照組每跳盡早送，包在中繼等待較久',16,MUT)
notes(d,'老師質疑 3 MB 的碰撞率太高，我做了診斷。先檢查計算：用獨立程式重算每個節點的占用峰值，都沒有超過 3 MB，也沒有找到錯誤。碰撞率高是設定造成的。第一，所有包都在前 600 秒產生，而 contact 分布在 3,600 秒內，流量很集中；只要把產生時間拉長到 3,000 秒，k=1 送達率就從 47% 到 91% 升到 80% 到 100%。第二，Buffer 只放 3 包，Buffer 每加 1 MB 送達率就明顯上升，到 10 MB 時大多接近 100%。第三，來源從產生時間就占用 Buffer，失敗有 35% 發生在來源；不計來源時提高 4 到 15 個百分點。第四，對照組每跳盡早送，包到中繼後要等比較久；失敗時改成盡晚送，提高 2 到 8 個百分點。每一列只改一項，其他維持原設定。')
# split SearchBundle
a=pg('演算法 2：SearchBundle');b=blank_from(a,idx(a)+1)
for x in a.shapes:b.shapes._spTree.append(copy.deepcopy(x._element))
notes(b,a.notes_slide.notes_text_frame.text)
def big(box,x,w,sz=22):
    box.left=In(x);box.width=In(w)
    for para in box.text_frame.paragraphs:
        for r in para.runs:r.font.size=Pt(sz)
la=[x for x in a.shapes if x.has_text_frame and x.text_frame.text.startswith('Q ← empty')][0]
ra=[x for x in a.shapes if x.has_text_frame and x.text_frame.text.startswith('while Q')][0]
ra._element.getparent().remove(ra._element);big(la,1.2,10.5)
setText(a.shapes[0],'演算法 2：SearchBundle（初始化）');setText(a.shapes[1],'來源的每條 contact 都先建立 Label 放進 Q，不先選一條走。')
lb=[x for x in b.shapes if x.has_text_frame and x.text_frame.text.startswith('Q ← empty')][0]
rb=[x for x in b.shapes if x.has_text_frame and x.text_frame.text.startswith('while Q')][0]
lb._element.getparent().remove(lb._element);big(rb,1.2,10.5)
setText(b.shapes[0],'演算法 2：SearchBundle（主迴圈）')
notes(a,'初始化：Q 和 Reached 先清空。來源的每條 outgoing contact 都用產生時間 g 算候選區間，做來源 Buffer 篩選；如果這條 contact 直接到目的地，再做目的地篩選。最後全部 Insert 進 Q，key=lo(I)+d(c)+δ(c)。')
notes(b,'主迴圈：每次取 key 最小的 Label。如果它已到目的地就回傳，第一個取出且到目的地的 Label 就是最早抵達。否則對下一跳的每條 contact，以上一跳最早收完的時間算候選，做中繼 Buffer 篩選；到目的地的再做目的地篩選，然後 Insert。不排除已訪節點，所以允許繞路。')
# delete old backup c8 slide (last)
last=p.slides[-1];assert last.shapes[0].text_frame.text.startswith('同一個 c6 Label：c8');rid=L[-1].get(qn('r:id'));p.part.drop_rel(rid);L.remove(L[-1])
# renumber
for i,s in enumerate(p.slides,1):
    for x in s.shapes:
        if x.has_text_frame and x.left==5762625 and x.top==6562725:setText(x,str(i))
p.save('v124.pptx');print(len(p.slides))
