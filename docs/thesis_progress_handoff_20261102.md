# 論文進度 Handoff

交接日期：2026-11-02。用途：交給下一位 AI、研究協作者或自己續作；可獨立閱讀。

工作目錄：`C:/Users/聖克里斯多福/Desktop/碩士`。
Repository：https://github.com/BAGLE102/space-dtn-thesis 。
交接前最近研究紀錄 commit：`53e8ca9`。本 handoff 另以新 commit 保存，不把此值當成持續最新的 HEAD。

## 0. 先讀這段

研究目標是在 Space DTN 中，為不可切分 bundle 找到符合 contact 與 node buffer 限制的最早可行抵達路徑。

**使用者最新明確選擇 contact splitting，仍逐包處理。完整新版搜尋尚未實作驗證；目前完成候選流程、簡報、背景文字與一個單 contact 區間元件的隔離測試。**

發現與 Alhajj、Corlay 的 arXiv:2410.15546v3 高度重疊。不能把 contact splitting、buffer 預測、逐包更新或等待跨溢位剪枝當成已確認的新貢獻。按需計算／局部更新只是候選改良，使用者沒有同意把它取代 contact splitting 主方法；整批重排／優先權也沒有採用。

目前另有約 5,000 字的課程論文需求，使用者要求碩士論文式結構與語氣。尚未提供課程 AI 規範、正式格式與截止日；不要把它誤記成已完成的正式碩士論文。

## 1. 協作方式與權限

- 先讀根目錄 `AGENTS.md`。使用繁體中文、臺灣用語，保留必要 English terms；用短段落與具體例子解釋。
- 使用者曾要求 ADHD 友善表達；先講結論，不一次引進未解釋的符號與額外模型假設。
- 使用者不信任未經核對的網站／程式結果。先確認版本，不宣稱它們自動等於 PPT 方法。
- 不因研究假設常見就當成合理；檢查 correctness、external validity 與比較公平性。
- 不虛構文獻、數值、證明、完成度或貢獻。發現同模型錯誤，保存案例、停止效能比較，先提出候選修正。
- 有意義工作完成後，更新 `PROGRESS.md`／`CHANGELOG.md`、檢查相關變更、commit 並 push；已有授權，不需每次重問。
- 不提交原始論文、私人附件、暫存或憑證；不 force push。不要順手提交無關的使用者檔案。

## 2. 版本與權威來源：不要混用

| 來源 | 地位 | 接手注意 |
|---|---|---|
| `docs/sequential_label_setting_v04.md`、`docs/current_algorithm_snapshot_v01.md` | AGENTS 指定的既有／凍結演算法基準 | 含時間格點與 U 的歷史設計；不得默默覆寫 |
| 本次對話的 contact splitting 選擇 | 使用者最新方法指示 | 優先保留；實作與凍結文件有差異，必須明列 |
| `docs/contact_splitting_flowchart_20261102.md` | 最新 contact splitting 候選流程 | 有三張圖；尚非完整可執行演算法 |
| `docs/1021_concrete_start_intervals_ppt_20261021.md` | 最新具體時間 Label 候選與 PPT 修改紀錄 | 提供目前 Label、事件、quota 與 dominance 依據 |
| `output/presentations/1021_起送時段修訂版.pptx` | 32 頁候選簡報 | F 槽副本：`F:/1021_起送時段修訂版.pptx`；11月2日流程尚未回填 PPT |
| 舊 `1021.pptx`、長 Contact 簡報 | 歷史方案／其他案例 | 曾有 `(c,I,pred,K)` 抵達區間 Label，不是目前具體時間 Label |
| 網站與既有 routing 程式 | 舊版本產物 | 不能作新版 contact splitting 已實作的證據 |

改稿前先判斷「本次對話候選」「正式凍結基準」「歷史示範」三者差異，不要自行合成一個聲稱已確立的版本。

## 3. 研究背景、問題與目前範圍

太空網路可能沒有持續的端到端路徑。節點保留 bundle，等 contact 可用再轉送。

Contact 的總容量足夠，不代表有足夠長的連續傳送時槽。接收完成時 buffer 放得下，也不代表接收過程或等下一跳的整段期間可行。較早抵達不一定可安全等待，因此不能僅以早到刪除較晚 Label。

目前目標：在先前已接受預約固定的條件下，為本包求最早可行完整抵達時間，輸出路徑及各跳起送時間。不是最少 hop，也不是所有 bundles 聯合最優。

目前候選假設：

- Bundle 不可切分、不可暫停、無副本；同一跳完整使用一個可用傳輸片段。
- 完整收到後才能轉送；r>0、傳播延遲 δ≥0；有限規劃範圍／deadline。
- 接收逐 byte 增加 buffer，送出逐 byte 釋放；其實務支援條件仍需交代。
- 已知 Contact Plan、先前已接受的占用曲線與預約；本次搜尋中不改變快照。
- 尚未加入共享 radio／天線互斥、未知流量或隨機接觸中斷。
- 候選仍保留獨立 aggregate quota 與傳送 calendar；quota 的物理／管理來源尚待釐清，不能為製造差異而硬加。

## 4. 目前方法與符號

| 符號 | 意義 |
|---|---|
| S | 本次 bundle 大小 |
| c | 原始 contact；含傳送端、接收端、發送時窗、速率 r 與傳播延遲 δ |
| R[c] | 本次搜尋前的獨立剩餘容量配額；各切片共用原始 contact 配額 |
| F[c] | 該原始 contact 上已接受的發送預約，採半開時槽 `[s,f)` |
| O_v(t) | 前包已接受排程在節點 v、時間 t 的 buffer 占用 |
| M_v | 節點 v 的 buffer 上限 |
| L=(c,A,s,pred) | 最後原始 contact、整包完整抵達時間、該跳起送時間、前驅 Label |
| Q | 待處理 Label 的優先佇列；依 A、建立順序取出，不依 Label 編號 |
| J | 本包在某個 contact／片段上允許的起送時間集合；不是物理時窗本身 |

每次延伸，前驅抵達為 A，選定起送時間 s：

`d=S/r`、`f=s+d`、`h=s+δ`、`Anew=s+d+δ`。

條件包括：s≥A；s 不早於可用時窗；f 不晚於發送結束；Anew 符合期限；發送預約不重疊；quota 足夠。

一般區段的 buffer 條件：

- 等待 t∈[A,s]：`O_u(t)+S≤M_u`。
- 送出 t∈[s,f]：`O_u(t)+S-r(t-s)≤M_u`。
- 接收 t∈[h,Anew]：`O_v(t)+r(t-h)≤M_v`。

來源生成、目的地交付與跳變端點不能直接套一般連續曲線公式。候選 P 採同時事件先交付釋放、再接納新來源資料；來源用事件後背景、目的地需保留交付前接收峰值。這部分未整合到完整新版搜尋。

時間目標：`Anew=s+S/r+δ`。若寫成一跳時間成本，是 `(s-A)+S/r+δ`；非固定 contact 權重。容量、buffer 是限制，不是目前的加權懲罰項。

## 5. Contact splitting 與搜尋流程

1. 取下一包，固定已接受的 F、O、R。
2. 移除已接受發送時槽，保留實體可用 contact 片段。
3. 依本包 S、r、δ 與兩端 buffer 條件，計算本包專用可用片段／允許起送範圍。
4. 建立來源 Label，加入 Q。
5. 取出有效且 A 最小的 Label，探索 outgoing 片段；依原始 ID 檢查前綴 quota。
6. 用前驅抵達時間與可安全等待範圍裁切候選起送時間。
7. 每個連通部分取最早可取得起送時間，建立具體 Label；此規則仍需一般完整性證明。
8. 做保守 dominance；不能取代則保留，不讓候選占用全域資源。
9. 取出目的地後回溯、獨立驗證完整排程，再決定結果的證明狀態。
10. 驗證成功才一次提交 F、R、O，處理下一包。

兩種切割不要混淆：已接受傳輸造成的占用適用後包；buffer 切割依本包大小等條件，只適用本次搜尋，不永久刪去其他 bundles 可能用到的時段。

最重要的表示問題：物理時窗 `[a,b]` 的起送上限是 `b-d`。若 buffer 限制後得到 J，不能把 J 的右端再當成發送結束時間而扣一次 d。接收端滿載時段也不能原封不動從傳送端 contact 刪除。這些映射的等價性尚待驗證。

不是每建立 Label 都重新切割／預約。以固定資源快照與有限事件建立本包結果；已接受路徑提交後才更新後續資源。合併只限等價相鄰片段。不能因候選 Label 抵達未來，就刪掉其他規劃仍需要的較早資料。

## 6. 目前 dominance

同一包、同一快照，一般中繼節點 L1 支配 L2 的候選充分條件：

1. 同一目前節點。
2. `A1≤A2`。
3. 能完整持有本包由 A1 等到 A2，即兩者位於同一可完整持有時段。
4. 每個原始 contact 的前綴使用量／次數，L1 都不多於 L2。

第四項源自仍保留的獨立 quota；可由 pred 回算，不重新加入已廢棄的 U 欄位。Label 編號與 contact 編號沒有對應關係。

新候選通過可行性檢查後、進 Q 前比較。被既有 Label 支配則丟棄；它支配其他 Label 則使對方失效，但保留 pred 鏈所需物件。完全等價時穩定保留一個，避免互刪。來源／目的地特殊狀態需另按候選定義處理。

這是候選充分條件，不是已驗證的完整新版 dominance 實作。單向圖不保證無循環；目前未採用禁止重訪的假設。若改成 simple path，必須重新檢查歷史狀態與支配。

## 7. 與既有論文的重疊

主要文獻：Tania Alhajj、Vincent Corlay，*Improved Contact Graph Routing in Delay Tolerant Networks with Capacity and Buffer Constraints*，arXiv:2410.15546v3。
來源：https://arxiv.org/html/2410.15546v3 。本機原檔：`F:/2410.15546v3.pdf`，不可提交。

已核對的核心重疊：容量／buffer 限制的最早抵達問題、逐包規劃、前包預約、contact splitting、forecast buffer tables、禁止等待跨溢位的銜接。

候選差異仍待核對：逐 byte 下精確起送集合、按需／增量成本、容量歷史與允許 walk。不同 buffer 或循環模型造成可行集合改變，不可全部歸成搜尋演算法更好。

原文 §VIII／IX 提到 traffic-level、優先權重排、大規模成本、資訊誤差與分散式等延伸。優先權／搶占已有構想，不能只加優先權便宣稱新穎。使用者尚未選擇換成整批重排題目。

原文 §V benchmark 與提出的方法不同，不能混用其 buffer 計量細節。也不能說作者完全沒談送出時釋放 buffer。

## 8. 已完成驗證：範圍務必說清楚

最近已保存數值實驗日期為 2026-10-21；本次交接未重跑。

**A. PPT 固定排程案例**：原五節點／八 contacts；S=4MB、r=4MB/s、buffer 上限4MB。δ(c2,c5,c6)=1秒，其餘0。

- 第一包 c1 起送2、c2起送6，完整到D8。
- 第二包 c4起送7、c5起送10，完整到D12。
- 第二包 c3早到B2後等待會超 buffer；c6到C3後已錯過c8，c7配額不足。
- 固定排程核對不是完整搜尋／dominance 正確性證明。

**B. 單 contact 區間元件 pilot**：

- Fraction 精確有理數；以事件分段解線性不等式，不是逐秒產生 J。
- 9 個解析案例、9,307 次固定起送檢查、22,320 次快取答案對照無差異；5個單元測試已通過，含漏版本的負控制。
- 四策略：全量重建、按需單輪快取、增量全量、按需增量。共用同一 solver，並非四個獨立正確性 oracle。
- 96 contacts、24 nodes、5快照、每策略7次計時；196筆時間。計時使用一個 workload seed；正確性對照使用三個 seeds。

| 情境 | 增量全量中位數 | 按需增量中位數 | 可支持的解讀 |
|---|---:|---:|---|
| 約10% contacts查詢、局部更新 | 228.056 ms | 28.443 ms | 人工稀疏查詢可省計算 |
| 全部contacts查詢、局部更新 | 211.385 ms | 239.450 ms | 沒有穩定優勢；不可只報正面案例 |

時間均為五個快照合計，不是每包路由。Memory 是 Python 額外追蹤配置峰值，不是整個程序 RSS。

**沒有完成**：完整搜尋、前驅等待整合、跳變事件、提交、真實搜尋 trace、論文忠實重現、原文效能比較、大規模／一萬包新版實驗。合成資源快照不等於由完整前包 traffic trace 生成。

## 9. 寫作進度與課程論文

- 2026-10-25 已整理背景／動機／目的／進度的英文與繁體中文稿。
- 英文依 ASD-STE100 Issue 9 的簡化寫作原則；68句、24段，每句最多17個計數詞、每段最多3句。
- 未逐詞核對完整受控字典；不能稱 STE 完整合規／認證，中文亦不是 STE 認證文件。
- 使用者要求約5,000字課程論文，按碩士論文式結構與正式語氣，先逐段協作，不直接生成整篇。
- 工作題名是助理暫擬的「考量 Contact 容量與 Buffer 限制之 Space DTN 路徑規劃研究」，尚非正式定題。

對話提出的暫定字數表如下；含摘要，暫不含參考文獻／附錄，須依課程要求調整：

| 部分 | 字數 |
|---|---:|
| 摘要 | 250 |
| 第一章 緒論 | 850 |
| 第二章 文獻探討 | 1100 |
| 第三章 研究方法 | 1400 |
| 第四章 初步驗證與討論 | 1000 |
| 第五章 結論與未來工作 | 400 |
| 合計 | 5000 |

未提供：課程名稱、評分規準、校系格式、引用格式、截止日與 AI 規範。先前已詢問 AI 是否允許初稿，尚未收到答案，不可記成已允許代寫或已符合規範。

使用者指定的 Skills 已閱讀相關部分，沒有安裝：

- https://github.com/WenyuChiou/ai-research-skills 是技能目錄；實際文獻矩陣／研究設計入口位於 `WenyuChiou/research-hub`。當時讀取 revision `208b3a2d54e18ceba8292dc3933a720861a6afc2`。
- https://github.com/WenyuChiou/academic-writing-skills ，當時讀取 revision `404eb2aacbd8a4f3f0813053cf615acad8ed68aa`。
- 後續依任務載入需要的 skill／reference；不要因此啟動完整 pipeline、安裝全部套件或擅自委派。

## 10. 尚未解決的關鍵問題

| 優先 | 問題 | 需要的下一份證據 |
|---|---|---|
| 高 | 原始 contact、切片與允許起送範圍的等價映射 | 可手算邊界案例與獨立連續時間核對 |
| 高 | 本包buffer切割＋前驅等待是否保留必要晚到解 | 同模型早到失敗／晚到成功案例 |
| 高 | 最早候選選取與支配的一般正確性 | 證明草稿、獨立oracle與失敗案例 |
| 高 | 是否有可成立的差異／貢獻 | 原文同模型重現、相關工作查核及與老師確認 |
| 中 | 獨立quota是否有需求、是否由calendar可推得 | 明確物理／管理來源，不為製造差異增加限制 |
| 中 | P端點、開區間、無可取得最早點如何處理 | 事件側測例與 incompleteLB 狀態核對 |
| 中 | 按需方法是否降低整體成本 | 真實完整搜尋的查詢trace與端到端成本 |

Q 空、超時或忽略分支不能一律叫無解。第一個目的地 Label 出 Q，也不能在完整性條件未立時無條件標最優。驗證失敗須停下保存反例，不能照常扣資源。

## 11. 重要檔案索引

下列路徑皆相對於本 handoff 開頭的工作目錄。

| 用途 | 路徑 |
|---|---|
| 工作約定 | `AGENTS.md` |
| 進度／變更 | `PROGRESS.md`、`CHANGELOG.md` |
| 最新流程 | `docs/contact_splitting_flowchart_20261102.md` |
| 具體Label候選／PPT紀錄 | `docs/1021_concrete_start_intervals_ppt_20261021.md` |
| 相關論文重疊查核 | `docs/paper_2410_15546v3_contact_splitting_comparison_20261021.md` |
| 延伸方向 | `docs/paper_extension_choices_20261021.md` |
| 工作規劃 | `docs/research_validation_roadmap_20261021.md` |
| Pilot方法／結果 | `docs/demand_interval_validation_method_20261021.md`、`docs/demand_interval_validation_results_20261021.md` |
| Pilot程式／報表 | `src/experiments/demand_interval_validation.py`、`src/experiments/report_demand_interval_validation.py` |
| Pilot測試 | `tests/test_demand_interval_validation.py` |
| 原始輸入／計時／查詢trace | `output/demand_interval_validation_20261021/` |
| 中文背景稿 | `docs/research_background_objectives_zh_TW_20261025.md` |
| 英文背景稿 | `docs/research_background_objectives_ste_en_20261025.md` |
| STE寫作審查 | `docs/research_background_objectives_ste_review_20261025.md` |
| 候選簡報 | `output/presentations/1021_起送時段修訂版.pptx` |

原始 `F:/1013.pptx`、`F:/2410.15546v3.pdf` 只在使用者本機；接手環境未必可用。不要下載後上傳原論文。

## 12. 接手後怎麼繼續

1. 先讀本 handoff、AGENTS 與目前任務需要的索引檔，不重掃整個 repository。
2. 若繼續寫課程論文：先取得課程 AI 規範與格式；確認可用證據，再從第一章逐節協作。不要將候選流程寫成已驗證成果。
3. 若繼續方法研究：先以原PPT兩包案例查核切割映射、等待與支配，保留原始contact ID與配額語意；不直接跑一萬包。
4. 若繼續成本方向：先取得完整搜尋的真實query trace，再評估按需方案；不預設探索比例只有10%。
5. 如要改quota、buffer模型、禁止循環或改成整批目標，先說明為何需要與影響，取得使用者的實際選擇，不把助理提案當成定案。

可重現隔離元件（這不是完整contact splitting路由）：

```powershell
python -m unittest tests.test_demand_interval_validation -v
python -m src.experiments.demand_interval_validation --contacts 96 --epochs 5 --repeats 7 --output output/demand_interval_validation_rerun
python -m src.experiments.report_demand_interval_validation output/demand_interval_validation_rerun --output output/demand_interval_validation_rerun/comparison
```

套件 runtime 路徑可能依機器改變；使用目前環境的 Python。重跑寫新輸出目錄，保留10月21日原始結果。

交接時有一份無關未追蹤檔 `Space_DTN_Problem_Definition_Label_Setting_v01.pptx`，未納入本次工作。接手前請重新檢查 git status，不擅自提交它。

**本次交接只整理狀態，沒有新增實驗、修改研究模型、更新PPT或完成論文正文。**
