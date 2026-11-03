# 1103 新版演算法：逐頁講者備註（v1.2）

來源：1013.pptx；方法：GitHub 67db7a2 的 dtn_validation 區間 Label。

## P01 新版流程：區間 Label 延伸

本次沿用 1013 的拓樸與逐步講解。方法是 store-and-forward：收完整包才轉送。以連續區間取代逐秒枚舉，不再對每個 s 建立 Label。每個連通可行區間是一個 Label；此處的移除已達集合不等同舊版同節點較早抵達支配。
一句重點：保留整段可行起送時間；實際起送時刻在回溯時選定。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P02 研究環境：中央規劃、節點執行

中央端知道 contact plan 與已接受 bundles 的傳送時段和背景占用；這是固定已知預約的理想規劃模型，非分散式即時共識。Bundle 規劃順序固定，不保證多包整體最佳。節點依中央產生的排程執行 store-and-forward。
一句重點：上一包接受並預約後，下一包才使用更新後的資源搜尋。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P03 Label 的完整定義

L_i 的 i 是本次單包搜尋中的唯一編號，不是 contact 編號或 Label 狀態欄位。數學狀態為 c、I、pred 三項；key=lo(I)+d(c)+δ(c) 是優先佇列的推導值。程式 Label(c,lo,hi,pred) 以 lo、hi 表示區間 I。v(c) 統一表示 contact 接收端。I 是沿該前驅鏈可達的連通起送區間，不代表可以任意搭配前驅的所有時間。選定 s 後 A(L,s)=s+d(c)+δ(c)。目前範例為閉區間，下界可取到；一般開區間仍待完整處理。SOURCE 是來源標記，程式用 None。子 Label 的 pred 引用保留前驅，移出 Q 不等於刪除前驅物件。
一句重點：Label 記錄可達時間與前驅；編號與 key 另列。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P04 固定拓樸與兩包需求

沿用 1013 五節點八個 contacts。第一包 release g=0，第二包 g=1。規劃先後不是實際送達先後。新版移除獨立配額後，第二包可走 c6、c7，故結果改為第 5 秒到達。
一句重點：先規劃 X→D，再規劃 A→D；兩包皆為 4 MB。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P05 Contact plan 與容量模型

資料逐項取自 1013：時間窗與傳播延遲不變。原稿額外設定 R[c7]=2 MB，但新版無此獨立配額。此處列出的是 rate×duration 的初始物理傳輸量；不代表多個分離時段可以拼成不分割 bundle。每跳仍須有連續長度 d 的空檔。
一句重點：c7 的時長 1 秒、速率 4 MB/s，故傳輸量為 4 MB。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P06 傳送、抵達與 Buffer 占用

a(c)、b(c) 是 contact 開始與結束；s 是起送；f 是發送完成；h 是第一個 byte 抵達；A 是最後一個 byte 抵達。傳播延遲 δ 與傳輸時間 d 不同。中繼占用為已收減已送，接收時上升、持有時固定、發送時下降。來源從 g 擁有整包；目的地在 A 完整接收後交付並釋放。新版已檢查來源、中繼與目的地，Commit 也納入三者。
一句重點：上一跳整包抵達後，下一跳才可起送：s2 ≥ A1。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P07 SourceRange：直接得到起送區間

來源已在 g=1 備妥。c4 從 7 開到 9，d=1，沒有預約，故起送集合 [7,8]。例如 7.5 也在其中。此例沒有 deadline；若輸入 D*，Tail 再與 D*−d−δ 取較小值。實驗程式使用 T=12 是此有限 contact plan 的涵蓋上界，沒有額外排除本例任何完整抵達。
一句重點：c4 的 [7,8] 包含所有實數起送時間，不逐秒枚舉。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P08 第一包：來源 X 建立 c1 Label

初始化不再把虛擬 L0 放進 Q，而是對來源的 outgoing contacts 建立可行起送區間。X 從 0 等到 2，持有 4 MB；2 到 3 逐 byte 發送下降。來源檢查通過。此時尚未預約任何全域資源。
一句重點：c1 只能在第 2 秒起送，最早完整抵達 B 的時間為 3。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P09 第一包：從 B 延伸 c2、c5

先從 Q 取出 L1，Q 暫時為空，再對 B 出發的 c2、c5 延伸。c2 起送集合 [6,6]，完整到 D 為 8；c5 為 [10,10]，完整到 D 為 12。B 占用最高 4 MB。L2.pred=L1、L3.pred=L1，所以 L1 雖然離開 Q，仍透過子 Label 的引用保留供回溯。這些是替代候選，搜尋期間不各自提交占用。
一句重點：取出 L1 並完成延伸；L2、L3 的 pred 仍指向 L1。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P10 第一包：選取目的地並回溯

本例先取出 c2 的目的地 Label，c5 的另一目的地 Label 尚在 Q 中。回溯先定末跳 s=6，再在 c1 的 [2,2] 內找不超過 6−0−1=5 的最大值，得到 2。未取出的候選不是因 dominance 刪除。本頁只說明候選控制流程，本方法的一般最優性仍待證明。
一句重點：取出 key=8 的目的地 Label，回推出 c1 在 2、c2 在 6 起送。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P11 第一包：提交預約與各節點占用

Validate 通過後，Commit 寫入 c1[2,3)、c2[6,7) 及所有節點占用。X 從 0 持有 4 MB 到 2，再於 2 到 3 發送下降；B 在 2 到 3 接收、3 到 6 持有、6 到 7 發送下降；D 在 7 到 8 接收，於 8 交付釋放。本圖只展示 B，未畫出的 X 與 D 同樣已提交。
一句重點：預約 c1、c2，並提交來源 X、中繼 B 與目的地 D 的占用。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P12 第二包：來源 A 先建立 c3 Label

第二包 g=1。在 A 的 outgoing contacts 依輸入順序 c3、c4、c6 初始化。c3 只能於 1 起送，2 到 B。來源 A 的 Buffer 通過；B 在 1 到 2 的接收也可行，但接續 c5 時會因等待遇到背景占用而失敗。
一句重點：收到整包只代表這個前綴可達；能否等待要延伸時再檢查。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P13 第二包：c4 用一個 Label 保留 [7,8]

c4 的可行起送集合為閉區間 [7,8]。建立一個 L2，key=7+1=8；s=7.5 仍保存在同一個 Label 中。此頁沒有刪除較晚起送時間，也沒有用較早抵達做同節點 dominance。
一句重點：不建立 s=7、8 的兩個 Label；整段時間一起保留。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P14 第二包：c6 加入 Q，依 key 排序

c6 在 1 到 2 發送，傳播延遲為 1，C 在 2 到 3 接收，故 key=3。初始化建立順序為 c3、c4、c6，但 Q 排序為 c3(key2)、c6(key3)、c4(key8)。每次僅延伸被取出 Label 所在節點的 outgoing contacts，不在全圖按 contact 開始時間逐條走。
一句重點：取出順序由最早完整抵達時間決定，不依 contact 編號。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P15 取出 c3：c2 的唯一空檔已被預約

取出 L1 代表目前前綴於 B 的可行抵達，並不是已選整條路。c2 的 d=1，原本只能 s=6；第一包預約 [6,7)，衝突起送區間為 (6−1,7)=(5,7)，剛好把 6 排除。因此是時段用完，不是另一個獨立配額判斷。
一句重點：c2 的候選起送時間 {6} 被已有傳送預約排除。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P16 取出 c3：等待 c5 會使 B 超限

c5 可於 10 起送，但 c3 只能在 1 起送，因此第二包於 2 完整到 B 後須持有到 10。t=2 時合計為 4；在 2<t<3 既有第一包逐漸接收，合計立刻超過 4，第 3 秒達 8。圖從 0 秒開始；第二包於 1 到 2 接收，不與第一包於 2 到 3 的接收誤畫成同時上升。只拒絕 c3→c5 這個延伸，不取消其他候選。
一句重點：第 2 秒後即超限，第 3 秒達 8 MB；拒絕 c3→c5。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P17 取出 c6：c7 可傳整包

c7 初始 rate×duration=4 MB，沒有舊版的獨立 2 MB 配額。本包在 C 的接收為 2 到 3，持有為 3 到 4，發送為 4 到 5，峰值 4。BufferFilter 保留起送集合 [4,4]，新增 L4，key=5。此頁先 c7 再 c8，依輸入 outgoing contacts 順序；不影響 Q 以 key 取最小的規則。
一句重點：C 在 3 收完，4 起送 c7，5 完整抵達 D。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P18 同一個 c6 Label：c8 已經來不及

c8 在 2 到 3 開放，d=1，所以最晚 2 必須起送。C 在 3 才收完整包；store-and-forward 不允許於 2 邊收邊轉，故 c8 不能使用。c7 剛建立的 L4 仍在 Q，不因 c8 失敗而移除。
一句重點：Head=3、Tail=2，候選起送區間為空。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P19 第二包：先取出 key=5 的目的地

Q 中是 c7 的 L4(key5)與 c4 的 L2(key8)。先取出 L4 後，搜尋按候選規則結束。不能把剩下候選稱為 dominated：只是本次不再探索。此固定案例的最早抵達另由獨立小例窮舉核對；一般方法的首次目的地最優性尚待證明。
一句重點：L2 尚未展開；它不是被較早 Label 支配刪除。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P20 第二包：沿 pred 選定實際起送時間

先選末跳 c7 的起送時間 4。前驅 c6 的可用上界為 4−δ(c6)−d(c6)=4−1−1=2；c6 的 I=[1,1]，最大可用值就是 1。整包於 C 的抵達為 1+1+1=3，不晚於下一跳 4。沿 pred 不是倒著傳，而是由最後一跳決定前面實際採用的時間。
一句重點：結果為 c6 在 1 起送、c7 在 4 起送，D 於 5 收完整包。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P21 第二包：提交 c6、c7 與各節點占用

Validate 通過後，把 c6[1,2)、c7[4,5) 加入 F，並提交所有節點占用。A 在 g=1 出現整包，1 到 2 發送下降；C 在 2 到 3 接收、3 到 4 持有、4 到 5 發送下降；D 在 4 到 5 接收並於 5 交付釋放。本圖只展示 C，A 與 D 同樣已提交。c3 前綴與未選的 c4 都不提交。
一句重點：提交來源 A、中繼 C、目的地 D；未選候選不提交。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P22 兩包完成：送達時間與資源預約

第一包先規劃，不等於第一包先抵達。它經 B 於 8 到 D；第二包經 C 於 5 到 D。新版使用來源、中繼與目的地檢查及完整 Commit。c7 物理傳輸量為 4 MB，取消舊稿的 2 MB 獨立配額後才可傳送本包，因此第二包由舊稿 12 秒變 5 秒是模型限制不同，不能當成演算法效能提升。
一句重點：第二包 12→5 秒是取消 c7 配額造成，不能歸因於區間搜尋。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P23 第二包：Q 與拒絕原因總表

本表來自 walkthrough.json 的真實候選控制流程。Label 編號僅在第二包搜尋中有效。初始化先產生 c3、c4、c6，Q 以 key 排序。取出 c3 後試 c2、c5；取出 c6 後試 c7、c8；最後取出 c7 目的地。
一句重點：只有 c3→c5 因 Buffer 拒絕；c2 因預約、c8 因時間拒絕。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P24 補充：c4 區間何時變成實際時間

這一頁解釋尚未展開的 c4 區間如何用，不把它冒充主搜尋實際發生的步驟。假設固定選 c4→c5，末跳 c5 的 s=10，前一跳上界 10−0−1=9；在 I=[7,8] 取最大值 8，故 B 於 9 收完，再等到 10 發送，D 於 12 收完。s=7 也是可行排程，但候選回溯採最晚前驅；這不表示它對後續 bundles 一定最好。
一句重點：固定 c4→c5 時，回溯會選 c4 的 s=8；這不是本例選中路徑。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P25 補充：預約如何切出可行起送區間

獨立示例，非主案例的新預約。contact 開放 [1,10]，傳輸時間 1；原起送集合 [1,9]。若既有預約 [3,5)，相衝突的起送時間是 (3−1,5)=(2,5)，兩端 2、5 皆可緊貼使用，因此剩 [1,2] 與 [5,9]。之後還要做 Buffer 檢查，不能從剩餘總量夠就判整包可傳。
一句重點：切的是起送時間集合；仍要完整保留每段連通區間。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P26 Label、Q 與 Reached 的分工

Q 是待展開 Label 的優先佇列，不是所有 Label 的儲存庫。ExtractMin 後取出的 Label 不再排隊，但已建立的子 Label 透過 pred 持有前驅物件，直到回溯不再需要它；不必因此新增研究狀態欄位或假裝程式已有全域 Labels／Processed 集合。Reached[c] 是以原始 contact 為索引的已達起送集合，不是 Label 清單。完整重複區間不重建，未涵蓋部分仍保留；不同 contacts 到同節點不能僅憑早到刪除。一般完備性與開閉端點仍待證。
一句重點：離開 Q 是取出來展開；被子 Label 引用的前驅仍須保留。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P27 虛擬碼 1：逐包規劃與初始化

英文虛擬碼依新版 ours.py 與 validate.py。兩包依固定規劃順序，不是最終抵達時間排序。來源候選先做 SourceBufferFilter；若 contact 直達目的地，還須做 DestinationFilter，再 InsertLabels。Validate 包含來源、中繼、目的地與時段／期限。Commit 寫入 F 與所有造訪節點的占用。
一句重點：到目的地的候選，先做 DestinationFilter 再建 Label。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P28 虛擬碼 2：取出與延伸 Label

此頁區間搜尋原型沒有 RELAX、TRACK、Ch，也沒有逐秒迴圈。key 為 lo(I)+d+δ，pop 同 key 時以建立順序分辨。Reached 是在插入時移除已涵蓋時間，不是全域 node visited。沒有以資料證明一般最優性；此頁是目前控制流程。
一句重點：收完整包才轉送；每次只展開目前接收節點的 outgoing contacts。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P29 虛擬碼 3：StartRange 與 SourceRange

延伸的 Head 為 max(a(c2),lo(I1)+δ1+d1)，這是 store-and-forward。Tail b−d 確保整包發送在 contact 結束前完成。可選 D* 需要再扣傳播延遲，確保整包抵達不逾期。程式目前的 P.T 是有限上界；此案例為 max(b+δ)=12，不構成額外 deadline。每個 F 預約排除的是開區間 (x−d,y)，允許剛好相接。
一句重點：未提供 deadline 時，Tail 只使用 contact 結束時間限制。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P30 虛擬碼 4：BufferFilter

固定下一跳起送 s2 時，前驅允許上界 U=s2−δ1−d1。候選只取 I1 中不超過 U 的最晚起送 s1*，以減少目前節點提前接收占用；此壓縮的充分性仍須正式證明。依背景曲線與分段邊界求可行 s2 區間，不枚舉所有實數。新版已實作 SourceBufferFilter 與 DestinationFilter。目的地接收從 h=s+δ 到 A=s+d+δ，使用 O_dst(t)+Received(t,s)≤M，包含交付前的峰值，A 時交付釋放。
一句重點：來源、中繼、目的地均檢查；目的地收完即交付釋放。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P31 虛擬碼 5：回溯、驗證與提交

回溯從目的地 Label 的區間下界起送，逐步求前驅最大可用起送時間。ValidateSchedule 對應 validate.py 的 validate：檢查非空排程、來源與目的地、release、路徑相接、時段與期限、不和 F 重疊、store-and-forward 先後條件及來源／中繼／目的地 Buffer。Commit 納入 F 與每次節點造訪的占用：來源從 g 持有整包並逐步送出；中繼接收、等待、送出；目的地接收後交付釋放。
一句重點：前驅最晚取值是目前選擇規則，不保證對後續 bundles 最好。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。

## P32 目前驗證範圍與下一步

依 GitHub 67db7a2 的 ours.py 與 validate.py，兩包重算為 8 秒、5 秒；1/4 秒格點窮舉與完整節點驗證均通過。保存的 validation.jsonl 含 3,000 案例、5,961 次查詢：2,250 次同抵達、3,705 次雙方無解、6 次區間方法較早；沒有較晚、漏解、多解或 replay 失敗。本次只重新統計既有紀錄、核對兩包並重算這 6 個差異案例，沒有重跑全部 3,000 案例。6 次的排程通過驗證，原窮舉用 1/16 秒格點；改為 1/48 秒後抵達時間均相同，支持格點差異解釋，不等於一般正確性證明。尚待完成一般證明、開閉端點與正式多包效能實驗；比較 SR-CGR 與原論文方法，擴大隨機拓樸。store-and-forward、無獨立配額主模型待老師確認；本版假設目的地整包收完即釋放。
一句重點：小例驗證不是一般證明；主模型仍待老師確認。
方法來源：src/experiments/dtn_validation/dtn/ours.py、validate.py；GitHub 67db7a2。
文件：docs/store_forward_label_20261103.md（部分歷史段落未同步，以此程式版本為準）。
案例資料：output/ppt_store_forward_20261103/walkthrough.json；新版重算核對：v1_2_source_checks.json。
本簡報呈現候選方法，尚無一般正確性證明；store-and-forward 與無獨立配額的主模型待老師確認。
