exec(open('buf_v1.py').read().split('# 1\n',1)[0].replace("p=Presentation('v125.pptx')","p=Presentation('three_questions_v1.2.pptx')").replace("T=p.slides[31]","T=p.slides[1]"))
src=Presentation('v126.pptx')
topo=[s for s in src.slides if s.shapes[0].text_frame.text.startswith('來源 A 建立三個 Label')][0]
TOPO=list(topo.shapes)[4:46]
def put_topo(s,hl=(),dim=()):
    n0=len(s.shapes)
    for x in TOPO:s.shapes._spTree.append(copy.deepcopy(x._element))
    for sh in list(s.shapes)[n0:]:
        if sh.has_text_frame:
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    r.font.color.rgb=RGB.from_string('747474' if r.text.startswith('[') else '222222')
    for sh in s.shapes:
        nm=sh.name
        if nm.startswith('topology-'):
            cid=nm.split('-')[1]
            col,w=('222222',2.75) if cid in hl else (('D0D0D0',1) if hl else ('595959',1.5))
            if True:
                sh.line.color.rgb=RGB.from_string(col);sh.line.width=Pt(w)
                if nm.endswith('arrow'):sh.fill.solid();sh.fill.fore_color.rgb=RGB.from_string(col)
L=p.slides._sldIdLst
def at(s,i):e=L[-1];L.remove(e);L.insert(i,e)
idx=[k for k,s in enumerate(p.slides) if s.shapes[0].text_frame.text.startswith('問題二：SR-CGR 是什麼')][0]
pos=idx+1
def add(title,bottom,notes):
    global pos
    s=new(title,bottom,notes);at(s,pos);pos+=1;return s
NOTE_TOPO='每跳傳 1 秒（d = 1）；傳播延遲 δ：c2、c5、c6 為 1 秒，其餘為 0；包在第 1 秒於 A 產生'
# A
s=add('Yen 示範（0）：A 到 D 有哪些路徑','Yen 要做的事：依抵達時間由早到晚，一條一條把這些路徑找出來。',
'用前面第二包的拓樸當例子，包在第 1 秒於 A 產生，要送到 D。每條 contact 傳一包要 1 秒，c2、c5、c6 的傳播延遲是 1 秒，其他是 0。SR-CGR 的 cost 是整包抵達 D 的時間，每跳都盡早送。A 到 D 一共有四條可行路徑：c6 接 c7 第 5 秒到；c3 接 c2 第 8 秒到；c4 接 c5 和 c3 接 c5 都是第 12 秒到。另外兩條組合不可行：c6 接 c8，包第 3 秒才在 C 收完，c8 第 3 秒就關了；c4 接 c2，包第 8 秒才在 B 收完，c2 第 7 秒就關了。Yen 演算法要做的，就是不用列舉所有組合，依抵達時間由早到晚把這些路徑一條一條找出來。')
put_topo(s)
table(s,6.0,1.25,[1.35,2.0,1.75,1.2],[['路徑','第一跳：送 → 收完','第二跳起送','抵達 D'],
 ['c6 → c7','1 → 3（在 C）','c7：4','第 5 秒'],
 ['c3 → c2','1 → 2（在 B）','c2：6','第 8 秒'],
 ['c4 → c5','7 → 8（在 B）','c5：10','第 12 秒'],
 ['c3 → c5','1 → 2（在 B）','c5：10','第 12 秒'],
 ['c6 → c8','1 → 3（在 C）','c8 只開到 3','不可行'],
 ['c4 → c2','7 → 8（在 B）','c2 只開到 7','不可行']],sz=15,rh=.45)
tb(s,.95,4.95,11.4,.34,NOTE_TOPO,14,MUT)
tb(s,.95,5.35,11.4,.34,'抵達時間 = 最後一跳起送 + 傳送時間 d + 傳播延遲 δ；例：c2 為 6 + 1 + 1 = 8',15,INK)
# B
s=add('Yen 的做法：從上一條路的每個分岔點另找出路','第 1 條用 Dijkstra；之後每一條都是「照抄前段 + 禁走舊路 + Dijkstra 補完」，再取最早的候選。',
'Yen 演算法的想法是：第 1 條路用 Dijkstra 找抵達最早的路。要找第 2 條時，第 2 條一定在某個節點和第 1 條分開，所以把第 1 條路上的每個節點都當成分岔點試一次。對每個分岔點，分岔點之前的路段照抄，稱為根路徑；分岔點出去的那一條 contact 如果已被某條同根路徑的舊路用過，就禁止使用，避免重找同一條；然後從分岔點用 Dijkstra 找最早抵達 D 的後半段。前半段加後半段就是一條候選路徑，放進候選池。所有候選中取抵達最早的，就是下一條路。重複到找滿 k 條，或候選池空了為止。還有一個限制：後半段不能經過根路徑上的節點，保證是簡單路徑。')
steps=[('1','第 1 條：用 Dijkstra 找抵達最早的路徑 P₁'),
 ('2','分岔點：把上一條路徑 Pᵢ 上的每個節點，輪流當成分岔點'),
 ('3','根路徑：分岔點之前的路段照抄，起送時間也照原本的'),
 ('4','禁用：已找到的路徑若有相同根路徑，它們從分岔點出去的那條 contact 不能再走'),
 ('5','補完：從分岔點用 Dijkstra 找最早抵達 D 的後半段，不經過根路徑上的節點'),
 ('6','選下一條：根路徑 + 後半段放進候選池；取抵達最早的當 Pᵢ₊₁'),
 ('7','停止：找滿 k 條，或候選池空了')]
for k,(n_,t) in enumerate(steps):
    box(s,.95,1.25+k*.62,.5,.48,n_,sz=16,bold=True)
    tb(s,1.6,1.25+k*.62,10.7,.48,t,18,INK)
# C
s=add('Yen 示範（1）：第 1、2 條','P₁ = c6 → c7（第 5 秒）；P₂ = c3 → c2（第 8 秒）。',
'第 1 條直接用 Dijkstra：從 A 出發，c6 接 c7 第 5 秒到 D，是最早的，所以 P1 是 c6 接 c7。找第 2 條時，把 P1 上的節點 A 和 C 輪流當分岔點。分岔點 A：根路徑是空的，禁止走 P1 從 A 出去的 c6，Dijkstra 從 A 第 1 秒出發，找到 c3 接 c2，第 8 秒到，這是一個候選。分岔點 C：根路徑照抄 c6，包第 3 秒在 C 收完；禁止走 P1 從 C 出去的 c7，剩下 c8，但 c8 第 3 秒就關了，沒有候選。候選池只有 c3 接 c2，所以 P2 是 c3 接 c2。')
put_topo(s,hl=('c6','c7'))
table(s,6.0,1.25,[1.05,1.75,1.0,2.5],[['分岔點','根路徑','禁用','Dijkstra 補完'],
 ['—','—','—','P₁ = c6 → c7（5）'],
 ['A','（空）','c6','c3 → c2（8）✓'],
 ['C','c6（3 秒）','c7','c8 已關閉，無']],sz=15,rh=.48)
tb(s,6.0,3.6,6.3,.4,'候選池：{ c3 → c2（8） } → 取抵達最早的',16,INK)
tb(s,6.0,4.05,6.3,.4,'P₂ = c3 → c2，第 8 秒',18,INK)
tb(s,.95,4.95,11.4,.34,'圖中粗線：P₁。括號內：抵達 D 的時間；根路徑括號：到達分岔點的時間',14,MUT)
# D
s=add('Yen 示範（2）：第 3、4 條，然後停止','共找到 4 條；就算 k = 10，候選池空了也只會有 4 條。',
'找第 3 條，從 P2，也就是 c3 接 c2 分岔。分岔點 A：根路徑是空的，P1 和 P2 都是空根路徑，所以禁止 c6 和 c3，只剩 c4。c4 第 8 秒到 B，c2 已經關了，只能接 c5，第 12 秒到，是候選。分岔點 B：根路徑照抄 c3，第 2 秒到 B；禁止 P2 從 B 出去的 c2，改走 c5，也是第 12 秒到，是候選。兩個候選一樣早，程式取先放進候選池的 c4 接 c5 當 P3，c3 接 c5 留在池子裡。找第 4 條，從 P3 分岔：A 的三條 contact 都被禁了；B 的根路徑是 c4，禁止 c5，剩 c2 已關閉。沒有新候選，池子裡剩的 c3 接 c5 就是 P4。再從 P4 分岔也找不到新路，候選池空了，所以停止。這個例子就算 k 等於 10，也只會找到 4 條。')
put_topo(s,hl=('c3','c2'))
table(s,6.1,1.25,[.65,.85,1.3,1.6,2.15],[['找第','分岔點','根路徑','禁用','補完'],
 ['3','A','（空）','c6、c3','c4 → c5（12）✓'],
 ['3','B','c3（2 秒）','c2','c3 → c5（12）✓'],
 ['4','A','（空）','c6、c3、c4','無'],
 ['4','B','c4（8 秒）','c5','c2 已關閉，無'],
 ['5','A、B','—','全部','無 → 停止']],sz=14,rh=.45)
tb(s,6.1,4.3,6.5,.36,'P₃ = c4 → c5（12）：同時間時取先進候選池者',15,INK)
tb(s,6.1,4.65,6.5,.36,'P₄ = c3 → c5（12）：池中剩下的候選',15,INK)
tb(s,.95,5.1,11.4,.34,'圖中粗線：P₂（找第 3 條時從它分岔）；找第 4 條從 P₃、第 5 條從 P₄ 分岔',14,MUT)
# E
s=add('k = 1 和 k = 10 在這個例子的差別','k 越大，Buffer 失敗時越有機會換到可行的路；但每條路仍是選好之後才檢查 Buffer。',
'Yen 找出路徑之後，SR-CGR 依序回放每條路，檢查 Buffer 和 contact 是否可行，取第一條通過的。假設第一包已經讓 C 在第 3 到 4 秒滿載，那 P1 c6 接 c7 會因為包要在 C 等第 3 到 4 秒而失敗。k 等於 1 時只有 P1，這包就被拒絕。k 等於 10 時，接著試 P2 c3 接 c2，若 B 放得下，第 8 秒送到。這就是 k 等於 10 送達率比 k 等於 1 高的原因。但不管 k 多大，Yen 找路時都看不到 Buffer，是先選路、再檢查；本方法則是在搜尋時就把 Buffer 不可行的時間扣掉。')
table(s,.95,1.3,[2.0,4.7,4.7],[['','k = 1','k = 10'],
 ['Yen 找到','P₁','P₁、P₂、P₃、P₄（本例只有 4 條）'],
 ['依序檢查','P₁ = c6 → c7','P₁ → P₂ → P₃ → P₄，取第一條通過的'],
 ['若 C 在第 3～4 秒已滿','P₁ 失敗 → 拒絕','P₁ 失敗 → 改試 P₂ = c3 → c2，第 8 秒送達'],
 ['計算量','1 次 Dijkstra','每找一條路要對每個分岔點各跑一次 Dijkstra']],sz=16,rh=.62)
tb(s,.95,4.65,11.4,.4,'共同限制：Yen 找路時看不到 Buffer，是「先選路、再檢查」；本方法在搜尋時就扣掉 Buffer 不可行的時間',16,INK)
# recolor all text black and renumber
BL={'3932A8','187A3E','B03A2E'}
for s in p.slides:
    tfs=[]
    for sh in s.shapes:
        if sh.has_text_frame:tfs.append(sh.text_frame)
        if sh.has_table:tfs+=[c.text_frame for r in sh.table.rows for c in r.cells]
    for tf in tfs:
        for para in tf.paragraphs:
            for r in para.runs:
                if r.font.color and r.font.color.type is not None and str(r.font.color.rgb) in BL:r.font.color.rgb=RGB.from_string('222222')
for i,s in enumerate(p.slides,1):setText(s.shapes[2],str(i))
p.save('three_questions_v1.3.pptx');print(len(p.slides),idx)
