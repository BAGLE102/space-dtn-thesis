# 1103 新版演算法：逐頁講者備註

來源：1013.pptx；方法：GitHub d8ade1c 的 store-and-forward 區間 Label。

## P01 新版流程：區間 Label 延伸

本次沿用 1013 的拓樸與逐步講解。方法是 store-and-forward：收完整包才轉送。以連續區間取代逐秒枚舉，不再對每個 s 建立 Label。每個連通可行區間是一個 Label；此處的移除已達集合不等同舊版同節點較早抵達支配。
一句重點：保留整段可行起送時間；實際起送時刻在回溯時選定。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P02 研究環境：中央規劃、節點執行

中央端知道 contact plan 與已接受 bundles 的傳送時段和背景占用；這是固定已知預約的理想規劃模型，非分散式即時共識。Bundle 規劃順序固定，不保證多包整體最佳。節點依中央產生的排程執行 store-and-forward。
一句重點：上一包接受並預約後，下一包才使用更新後的資源搜尋。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P03 Label 與優先佇列 Q

L_i 的 i 只是本次搜尋的標籤編號，不是 contact 編號。c 是原始 contact 的識別；I 是在該 contact 上可達的起送時間。pred 指向產生此區間的前驅，來源使用 SOURCE 標記，不新增虛構 contact。key 為區間下界加傳輸時間與傳播延遲；同值按建立順序取出。
一句重點：I 記錄起送時間區間；Q 比較的是最早完整抵達時間。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P04 固定拓樸與兩包需求

沿用 1013 五節點八個 contacts。第一包 release g=0，第二包 g=1。規劃先後不是實際送達先後。新版移除獨立配額後，第二包可走 c6、c7，故結果改為第 5 秒到達。
一句重點：先規劃 X→D，再規劃 A→D；兩包皆為 4 MB。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P05 Contact plan 與容量模型

資料逐項取自 1013：時間窗與傳播延遲不變。原稿額外設定 R[c7]=2 MB，但新版無此獨立配額。此處列出的是 rate×duration 的初始物理傳輸量；不代表多個分離時段可以拼成不分割 bundle。每跳仍須有連續長度 d 的空檔。
一句重點：c7 的時長 1 秒、速率 4 MB/s，故傳輸量為 4 MB。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P06 傳送、抵達與 Buffer 占用

a(c)、b(c) 是 contact 開始與結束；s 是起送；f 是發送完成；h 是第一個 byte 抵達；A 是最後一個 byte 抵達。傳播延遲 δ 與傳輸時間 d 不同。中繼占用為已收減已送，接收時上升、持有時固定、發送時下降。來源從 g 擁有整包；目的地交付時釋放。端點實作缺口列於最後一頁。
一句重點：上一跳整包抵達後，下一跳才可起送：s2 ≥ A1。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P07 SourceRange：直接得到起送區間

來源已在 g=1 備妥。c4 從 7 開到 9，d=1，沒有預約，故起送集合 [7,8]。例如 7.5 也在其中。此例沒有 deadline；若輸入 D*，Tail 再與 D*−d−δ 取較小值。實驗程式使用 T=12 是此有限 contact plan 的涵蓋上界，沒有額外排除本例任何完整抵達。
一句重點：c4 的 [7,8] 包含所有實數起送時間，不逐秒枚舉。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P08 第一包：來源 X 建立 c1 Label

初始化不再把虛擬 L0 放進 Q，而是對來源的 outgoing contacts 建立可行起送區間。X 從 0 等到 2，持有 4 MB；2 到 3 逐 byte 發送下降。來源檢查通過。此時尚未預約任何全域資源。
一句重點：c1 只能在第 2 秒起送，最早完整抵達 B 的時間為 3。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P09 第一包：從 B 延伸 c2、c5

取出 c1 的 Label 後只考慮從 B 出發的 contacts。c2 起送集合 [6,6]，完整到 D 為 8；c5 為 [10,10]，完整到 D 為 12。B 接收、等待、發送期間的占用最高 4 MB。這些是替代候選，搜尋期間不各自提交占用。
一句重點：兩個下一跳都通過時段與 B 的 Buffer 檢查。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P10 第一包：選取目的地並回溯

本例先取出 c2 的目的地 Label，c5 的另一目的地 Label 尚在 Q 中。回溯先定末跳 s=6，再在 c1 的 [2,2] 內找不超過 6−0−1=5 的最大值，得到 2。未取出的候選不是因 dominance 刪除。本頁只說明候選控制流程，本方法的一般最優性仍待證明。
一句重點：取出 key=8 的目的地 Label，回推出 c1 在 2、c2 在 6 起送。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P11 第一包：提交 F 與 B 的占用曲線

本頁忠實呈現目前 Commit：contact 傳送預約加上中繼節點曲線。B 在 2 到 3 接收，3 到 6 持有，6 到 7 發送下降。來源與目的地提交仍未完成；本例另有獨立完整節點重放，不能把該核對器當成原型已補完。
一句重點：接受後才預約 c1[2,3)、c2[6,7)，並寫入 B 的占用。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P12 第二包：來源 A 先建立 c3 Label

第二包 g=1。在 A 的 outgoing contacts 依輸入順序 c3、c4、c6 初始化。c3 只能於 1 起送，2 到 B。來源 A 的 Buffer 通過；B 在 1 到 2 的接收也可行，但接續 c5 時會因等待遇到背景占用而失敗。
一句重點：收到整包只代表這個前綴可達；能否等待要延伸時再檢查。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P13 第二包：c4 用一個 Label 保留 [7,8]

c4 的可行起送集合為閉區間 [7,8]。建立一個 L2，key=7+1=8；s=7.5 仍保存在同一個 Label 中。此頁沒有刪除較晚起送時間，也沒有用較早抵達做同節點 dominance。
一句重點：不建立 s=7、8 的兩個 Label；整段時間一起保留。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P14 第二包：c6 加入 Q，依 key 排序

c6 在 1 到 2 發送，傳播延遲為 1，C 在 2 到 3 接收，故 key=3。初始化建立順序為 c3、c4、c6，但 Q 排序為 c3(key2)、c6(key3)、c4(key8)。每次僅延伸被取出 Label 所在節點的 outgoing contacts，不在全圖按 contact 開始時間逐條走。
一句重點：取出順序由最早完整抵達時間決定，不依 contact 編號。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P15 取出 c3：c2 的唯一空檔已被預約

取出 L1 代表目前前綴於 B 的可行抵達，並不是已選整條路。c2 的 d=1，原本只能 s=6；第一包預約 [6,7)，衝突起送區間為 (6−1,7)=(5,7)，剛好把 6 排除。因此是時段用完，不是另一個獨立配額判斷。
一句重點：c2 的候選起送時間 {6} 被已有傳送預約排除。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P16 取出 c3：等待 c5 會使 B 超限

c5 可於 10 起送，但 c3 只能在 1 起送，因此第二包於 2 完整到 B 後須持有到 10。既有第一包在 B 的占用從 2 到 3 上升，合計第 3 秒達 8。圖從 0 秒開始；第二包於 1 到 2 接收，不與第一包於 2 到 3 的接收誤畫成同時上升。只拒絕 c3→c5 這個延伸，不取消其他候選。
一句重點：第 3 秒：前包 4 MB＋本包 4 MB＝8 MB，拒絕此延伸。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P17 取出 c6：c7 可傳整包

c7 初始 rate×duration=4 MB，沒有舊版的獨立 2 MB 配額。本包在 C 的接收為 2 到 3，持有為 3 到 4，發送為 4 到 5，峰值 4。BufferFilter 保留起送集合 [4,4]，新增 L4，key=5。此頁先 c7 再 c8，依輸入 outgoing contacts 順序；不影響 Q 以 key 取最小的規則。
一句重點：C 在 3 收完，4 起送 c7，5 完整抵達 D。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P18 同一個 c6 Label：c8 已經來不及

c8 在 2 到 3 開放，d=1，所以最晚 2 必須起送。C 在 3 才收完整包；store-and-forward 不允許於 2 邊收邊轉，故 c8 不能使用。c7 剛建立的 L4 仍在 Q，不因 c8 失敗而移除。
一句重點：Head=3、Tail=2，候選起送區間為空。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P19 第二包：先取出 key=5 的目的地

Q 中是 c7 的 L4(key5)與 c4 的 L2(key8)。先取出 L4 後，搜尋按候選規則結束。不能把剩下候選稱為 dominated：只是本次不再探索。此固定案例的最早抵達另由獨立小例窮舉核對；一般方法的首次目的地最優性尚待證明。
一句重點：L2 尚未展開；它不是被較早 Label 支配刪除。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P20 第二包：沿 pred 選定實際起送時間

先選末跳 c7 的起送時間 4。前驅 c6 的可用上界為 4−δ(c6)−d(c6)=4−1−1=2；c6 的 I=[1,1]，最大可用值就是 1。整包於 C 的抵達為 1+1+1=3，不晚於下一跳 4。沿 pred 不是倒著傳，而是由最後一跳決定前面實際採用的時間。
一句重點：結果為 c6 在 1 起送、c7 在 4 起送，D 於 5 收完整包。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P21 第二包：驗證後提交 c6、c7 與 C 曲線

目前 Commit 把 c6[1,2)、c7[4,5) 加入 F，並加入 C 的占用。c3 前綴與未選的 c4 都不提交。這裡仍沿用現行原型的中繼提交範圍，不把來源或目的地尚缺的功能畫成已完成。
一句重點：只提交選定排程；c3、c4 的候選不占用全域資源。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P22 兩包完成：送達時間與資源預約

第一包先規劃，不等於第一包先抵達。它經 B 於 8 到 D；第二包經 C 於 5 到 D。中繼背景位在不同節點，各節點峰值最高 4。獨立核對器另外檢查來源與目的地，這個特殊案例沒有共用來源、沒有重疊的 D 接收，因此目前 Commit 缺口不改變結果；不可以外推到多包一般情況。
一句重點：規劃第二包時已知第一包的未來預約，但仍可在較早時間抵達。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P23 第二包：Q 與拒絕原因總表

本表來自 walkthrough.json 的真實候選控制流程。Label 編號僅在第二包搜尋中有效。初始化先產生 c3、c4、c6，Q 以 key 排序。取出 c3 後試 c2、c5；取出 c6 後試 c7、c8；最後取出 c7 目的地。
一句重點：只有 c3→c5 因 Buffer 拒絕；c2 因預約、c8 因時間拒絕。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P24 補充：c4 區間何時變成實際時間

這一頁解釋尚未展開的 c4 區間如何用，不把它冒充主搜尋實際發生的步驟。假設固定選 c4→c5，末跳 c5 的 s=10，前一跳上界 10−0−1=9；在 I=[7,8] 取最大值 8，故 B 於 9 收完，再等到 10 發送，D 於 12 收完。s=7 也是可行排程，但候選回溯採最晚前驅；這不表示它對後續 bundles 一定最好。
一句重點：固定 c4→c5 時，回溯會選 c4 的 s=8；這不是本例選中路徑。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P25 補充：預約如何切出可行起送區間

獨立示例，非主案例的新預約。contact 開放 [1,10]，傳輸時間 1；原起送集合 [1,9]。若既有預約 [3,5)，相衝突的起送時間是 (3−1,5)=(2,5)，兩端 2、5 皆可緊貼使用，因此剩 [1,2] 與 [5,9]。之後還要做 Buffer 檢查，不能從剩餘總量夠就判整包可傳。
一句重點：切的是起送時間集合；仍要完整保留每段連通區間。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P26 Reached：只移除同 contact 已涵蓋的時間

Reached[c] 是以原始 contact 為索引的已達起送集合。完整重複區間不重建；未涵蓋部分仍保留，連通區間分開建立 Label。本頁用完全覆蓋示例，避免把尚未處理完整的開閉端點假裝已解決。跨歷史狀態壓縮、一般完備性與開區間需另證。
一句重點：不同 contact 到達同一節點，不能只因較晚就刪除。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P27 虛擬碼 1：逐包規劃與初始化

英文虛擬碼呈現最新候選流程。兩包依固定規劃順序，並非依最終抵達時間排序。SourceBufferFilter 在原型已實作。DestinationFilter 與來源／目的地 Commit 尚未實作，本簡報在相應頁面有明示。
一句重點：搜尋不預約資源；接受選定排程後才 Commit。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P28 虛擬碼 2：取出與延伸 Label

此頁區間搜尋原型沒有 RELAX、TRACK、Ch，也沒有逐秒迴圈。key 為 lo(I)+d+δ，pop 同 key 時以建立順序分辨。Reached 是在插入時移除已涵蓋時間，不是全域 node visited。沒有以資料證明一般最優性；此頁是目前控制流程。
一句重點：收完整包才轉送；每次只展開目前接收節點的 outgoing contacts。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P29 虛擬碼 3：StartRange 與 SourceRange

延伸的 Head 為 max(a(c2),lo(I1)+δ1+d1)，這是 store-and-forward。Tail b−d 確保整包發送在 contact 結束前完成。可選 D* 需要再扣傳播延遲，確保整包抵達不逾期。程式目前的 P.T 是有限上界；此案例為 max(b+δ)=12，不構成額外 deadline。每個 F 預約排除的是開區間 (x−d,y)，允許剛好相接。
一句重點：未提供 deadline 時，Tail 只使用 contact 結束時間限制。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P30 虛擬碼 4：BufferFilter

固定下一跳起送 s2 時，前驅允許上界 U=s2−δ1−d1。候選只取 I1 中不超過 U 的最晚起送 s1*，以減少目前節點提前接收占用；此壓縮的充分性仍須正式證明。依背景曲線與分段邊界求可行 s2 區間，不枚舉所有實數。來源已實作的曲線檢查與尚未實作的目的地檢查分開說明。
一句重點：同時檢查接收、等待與發送；只接收可行還不夠。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P31 虛擬碼 5：回溯、驗證與提交

回溯從目的地 Label 的區間下界起送，逐步求前驅最大可用起送時間。ValidateSchedule 應檢查完整排程與全程 Buffer；原型現有 replay 未檢查目的地。Commit 實際只寫 F 及中繼 O；來源與目的地需補完。這頁不新增未經同意的 RetimePath、incompleteLB 或保護 ε。
一句重點：前驅最晚取值是目前選擇規則，不保證對後續 bundles 最好。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。

## P32 目前驗證範圍與下一步

此簡報本例兩包由現行 store_label.py 求得，逐步鏡像流程與原型結果一致，另用四分之一秒小例窮舉及不共用 ramp/occ/filter 的完整來源、中繼、目的地重放核對。這不是新的研究級實驗或一般證明。GitHub 文件記錄的 3000 例是既有結果，本次未重跑。沒有執行 Alhajj/Corlay baseline；舊網頁與本版方法尚不一致。
一句重點：本例已重算核對；一般正確性與完整多包實驗尚未完成。
方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。
案例資料：output/ppt_store_forward_20261103/walkthrough.json。
本簡報呈現候選方法，尚無一般正確性證明。
