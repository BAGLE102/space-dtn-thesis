# 研究合理性、現實性與證據審查 v01

日期：2026-10-06。審查基準：Git `63c0c0c`，現行 `sequential_label_setting_v04.md` 與 `current_algorithm_snapshot_v01.md`。本次只做 audit，不修改演算法、程式、PPT、既有論證或驗證結果。

## 1. Overall Assessment

**目前是有條件式正確性論證的小型研究原型，尚未形成可支持實際 Space DTN 排程或優於既有方法的論文成果。** 最大問題不是 Label Setting 的名稱，而是欲宣稱的實際問題與真正求解的可行集合尚未一致。

| 面向 | 評估 | 能支持到哪裡 |
|---|---|---|
| Problem Definition | PARTIAL | 格點、quota、固定既有占用的單包問題可辨識；任務場景、線上／離線、拒收語意仍不完整 |
| Algorithm | PROTOTYPE | 有搜尋、延伸、dominance 與回溯；沒有 transmission calendar |
| Correctness | CONDITIONAL | 有前綴可行性與後綴替代論證，保存的 15 次查詢一致；不是普遍實作正確性證明 |
| Realism | LOW | 預約可重疊；立即釋放發送資料、控制可達性與可靠傳輸未落實 |
| Baseline | MISSING | 目前只有獨立完整搜尋及 dominance ON/OFF；未找到正式 SABR／contact-splitting baseline |
| Experiment | VALIDATION ONLY | 14 個人工案例，沒有性能研究資料集或網路執行模擬 |
| Literature Support | PARTIAL | 已有重要來源及反向核對；尚無固定版本的完整差異矩陣 |
| Thesis Readiness | 尚可報告問題與原型，未達完成論文 | 需先定義有證據支持的貢獻與保證範圍 |
| IEEE Readiness | 不足 | 未建立新穎性、同模型競爭方法比較、代表性或效能證據 |

本報告的 CRITICAL 表示會推翻所指向的 claim；不表示每一項都已找到 frozen v04 的同模型錯誤。HIGH 表示核心證據缺口；MEDIUM 表示重要但可局部處理；LOW 表示呈現或工程問題。影響標示 C=correctness、E=external validity、F=比較公平性、N=新穎性。

## 2. 掃描範圍與證據界線

- 盤點 102 個追蹤檔案，包括 36 份 docs、src/validation、4 份測試程式、保存的 JSON/CSV/log、圖解與 4 份 PPTX。逐檔雜湊、測例參數、PPT 文字及備註保存於 [evidence_inventory.json](../output/research_audit_v01/evidence_inventory.json)。盤點不等於所有檔案均經形式驗證。
- 詳讀現行模型、公式、虛擬碼、extension/dominance/completeness 論證、核心 solver、model、獨立完整搜尋及比較流程；舊 M0/v03、文獻筆記、大綱與呈現文件作跨版本核對。
- PPT 審查為文字、公式、頁面敘述與備註的內容审查；未重新渲染全部圖片，未宣稱完成像素或版面 QA。圖解數據核對生成程式及 trace。
- 根目錄沒有 `experiments/`、`data/`、`outputs/`；實際結果放在 `output/`。未找到獨立正式論文章節全文、正式 benchmark config、軌道推算器或流量產生器。不能把沒有找到的內容當成已做錯。
- 學長論文使用專案既有 extraction 與 `paper_method_mapping_v01.md` 交叉核對重點；本次未重讀兩本原始 PDF 的每一頁。原始 PDF、私人附件不納入 Git。
- 外部重新核對 SABR、RFC 9171、NASA HDTN requirements，以及 Alhajj–Corlay v1/v3。來源限定原文，不以教學頁或論文是否有期刊名稱代替技術判斷。
- 沒有重跑大型實驗或原本整套測試。新增只有 **2 次單包搜尋** 的模型邊界反例，見第 4 節。原本「18 項通過、15 查詢一致」均指保存紀錄。
- 比較保存的程式雜湊，只有 `render_figures.py` 不同；核心求解與獨立完整搜尋等檔案相符。繪圖雜湊不同不構成 solver 錯誤，但舊 manifest 不能替目前全部輸出背書。

證據定位：下表以檔名＋章節／函式／PPT 頁碼定位。所有「候選修正」都是建議，未套用。

## 3. 不合理／不現實清單

| ID | Severity | Category | Problem | Why Unreasonable / Unrealistic | Evidence | Impact | Fix |
|---|---|---|---|---|---|---|---|
| R01 | CRITICAL | 排程 claim | quota 通過仍可能同時超用鏈路 | 不限制已接受傳輸區間重疊，中央依序決策不會自動消除它 | v04 §6；`check_extension`；新反例第 4 節 | C/E：實際可執行排程保證不成立 | 限定為 quota 原型，或另提 calendar 模型供確認 |
| R02 | CRITICAL | 最優性 claim | 格點最優不能當連續時間最優 | 整數輸入仍會出現非整數最佳起送時間 | `search_completeness_review_v01.md` CE-GRID-01 | C：一般 earliest-arrival claim 被反例推翻 | 明限 Δ；若解連續問題，另證明候選時間完整性 |
| R03 | HIGH | 新穎性 | 研究貢獻尚未成立 | S/r、容量感知、buffer 預測與 Label Setting 均不能單獨當首創 | 文獻 mapping；S1/S2；centralized §8、11 | N：可能只是既有框架的特例實作 | 固定比較版本，找可證明且可量測的差異 |
| R04 | HIGH | Buffer 現實性 | 發出 byte 即刪除，無重傳副本 | 可靠傳輸是否還要保留資料尚未確認；所量 buffer 層級也不明 | v04 §1、6；RFC retention 規則 S3 | E/C：實際占用可能大於模型，原 state 論證也可能失效 | 確定 BPA/CLA/儲存的計量範圍與釋放事件 |
| R05 | HIGH | 中央架構 | 理想知識與控制及時送達未驗證 | 中央知道預約不代表節點已收到並能遵守；零 slack 特別危險 | centralized §3、9、13；PPT 圖解 v02 p2 | E/F：計畫與實際執行脫節；資訊優勢混入比較 | 定義批次預載或線上控制時序與可達性條件 |
| R06 | HIGH | 比較基準 | 沒有正式競爭方法實作 | ON/OFF 只是消融，完整搜尋只是正確性參考 | src/validation 全部程式；README | F/N：無法主張優於 CGR/SABR | 對齊模型後實作已指定版本的強 baseline |
| R07 | HIGH | 實驗外推 | toy topology 與單一大小主導所有驗證 | 沒有任務／軌道／流量代表性 | `validation_cases.py`；第 9、10 節 | E：不能支持 realistic、scalable、robust | 保留作驗證，另規劃具來源的研究拓樸 |
| R08 | HIGH | 多包語意 | 固定順序與 tie 對後包影響未研究 | 每包最佳可能消耗後包唯一資源；相同 arrival 的路線亦可改變後包結果 | `search` heap serial；`compare_one` canonical commit | C/F：不支持全體最佳或公平性 | 定義順序、同值選擇與系統指標；分開單查詢／序列實驗 |
| R09 | HIGH | 工作負載 | 拒收 bundle 直接消失的語意 | 若它真的已生成，源端未送出的資料仍可能占 buffer；目前未提交 | search SOURCE_FAIL；外層 continue | E：路由拒收率不能直接叫 delivery ratio | 定義 admission rejection、drop、retry 或外部來源儲存 |
| R10 | HIGH | 文獻同模型性 | 「2024 論文」版本與 buffer 定義不一致 | v3 已有 FEAP-CB；其正式 buffer 範圍和本研究不完全相同 | S2 §III-C；專案多用 v1／無版號 URL | F/N：結果差異可能來自問題不同 | 分開原版重現與明確標示的 adapted baseline |
| R11 | HIGH | 複雜度 | 目前 U 與全部起送時刻可能大量保留 labels | 不同路線的 U 常互不支配，過期 contact 用量也參與比較 | dominates；v04 §7；詳解 PPT p22 | E：效率 claim 無證據 | 分析 label 上界與主導成本；不要先刪 U |
| R12 | HIGH | 初始資源來源 | R 與 O 未形成一致、可追溯的預約輸入 | c7 物理量 4 MB、初始 quota 2 MB、初始 O 空；未交代保留量來源 | walkthrough；case 03/04/13 | E/F：若聲稱僅由前包造成，資料來源不完整 | 明確外生 quota 或附已接受排程推導資料 |
| R13 | MEDIUM | 接口驗證 | solver 不完整驗證真正傳入的資源 | validate_input 查 case contact quota；search 使用獨立 quota/background 參數 | model.validate_input；search | C：非法輸入可能崩潰或未被拒絕 | 明列合法輸入契約，之後才補驗證 |
| R14 | MEDIUM | Buffer 事件 | 同時生成／交付採峰值上界 | 可能拒绝實際能先釋放再接收的安排 | curve_value；snapshot 事件約定 | E/F：可行域變窄，需同事件語意比较 | 固定事件先後；測試端點及不同順序 |
| R15 | MEDIUM | 驗證涵蓋 | 共通模型錯誤不會被 independent oracle 發現 | 兩套皆省略 calendar、相同無副本假設與事件約定 | exhaustive_oracle；compare_oracle | C/E：一致性不是物理正確性 | 手算、不同模型邊界與執行層檢查補足 |
| R16 | MEDIUM | 實作測量 | trace 成本會污染 runtime/memory | 每次嘗試排序 heap、保存整份 Q、掃全部 labels；失效 label 仍保留 | search.queue、existing、labels[nid] | F：測到的可能主要是記錄成本 | 後續先定義同等紀錄負擔與核心／端到端計時 |
| R17 | MEDIUM | 驗證程序 | PASS gate 不綁定待比較程式／案例版本 | compare_dominance 只讀 status；旧 PASS 可被沿用 | comparison_gate.json；compare_dominance.run | C：未來程式更動後可能錯用通關結果 | 之後以 hash/版本綁定，保留本次審查紀錄 |
| R18 | MEDIUM | 提交程序 | 獨立驗證不是 commit 自動強制的前置條件 | compare_one 有檢查；build_walkthrough 直接 commit；model.commit 不驗證 | pseudocode §2 對照兩個 caller | C：完整流程契約只由部分呼叫端履行 | 指定正式入口與責任，避免宣稱 API 自帶防護 |
| R19 | MEDIUM | 系統約束 | 沒有共用 radio／半雙工／切換成本 | contact plan 未標明是否已先消除硬體互斥 | v04 §6；contacts schema | E：即使加每-contact calendar 仍未必可部署 | 指定獨立通道或由上游 plan 保證，否則另列資源互斥 |
| R20 | MEDIUM | 物理參數 | 固定速率／δ、零損失與零 overhead | 沒有誤差界或任務量測支持，緊貼 contact 邊界容易失效 | x=S/r；f≤end；第 8 節 | E：結果對小偏差可能敏感 | 定義有效速率／有效資料量及 margin；後續敏感度研究 |
| R21 | MEDIUM | 問題期限 | T 是人工截斷，沒有每包 expiry/deadline | 超出 T 無解不代表 DTN 網路永遠無路 | search arrival≤horizon | C/E：拒收原因可能混淆 | 區分計算 horizon 與應用 deadline |
| R22 | MEDIUM | 重現 | 保存結果與當前全專案版本未完全綁定 | renderer hash 不同；build_report 的 tests=18 為固定欄位 | reproducibility.json；build_report | C：metadata 不是本輪重測證據 | 結果註明來源版本、執行時間、測試日誌 |
| R23 | MEDIUM | 文件版本 | 多份歷史模型仍可獨立被誤讀 | v02 pseudocode 比 v01 舊；U 曾指佇列，現指用量 | snapshot 差異表；歷史 docs | C/溝通：可能引用錯誤保證 | 後續統一入口與歷史標籤，不刪研究紀錄 |
| R24 | LOW | 符號 | U=∅ 容易誤解成集合 | 程式是 contact→數量的 dict，數學是非負向量 | 圖解 v02 p6、9；usage | 溝通：無法理解為何要比較各 contact | 後續用零向量或空映射並註記 |
| R25 | MEDIUM | 標籤語意 | 「刪掉 U」容易只改儲存卻誤稱狀態變小 | pred 可重算 U，但未來可行性仍依路徑歷史 | 第 6 節；前次對話建議 | C：錯誤 state 合併風險 | 區分儲存欄位與數學狀態，先證明再簡化 |
| R26 | MEDIUM | 全面性 | 沒有連續時間誤差上界 | 一個 0.5 秒 gap 不是通用誤差，錯過 contact 可能造成大延遲或無解 | CE-GRID-01；格點定義 | E：不能宣稱 Δ 小就足夠準 | 提供界或承認未知，不能以單例估計上限 |

## 4. 已保存的反例：哪個判別式不足

### 4.1 新增 AUDIT-CALENDAR-02：不用外生流量，也能重複占用鏈路

實際用現行 solver 做兩次小型查詢，未改任何函式。完整輸入與 trace 見 [counterexample_sequential_overlap.json](../output/research_audit_v01/counterexample_sequential_overlap.json)。

| 輸入／輸出 | 數值 |
|---|---|
| Contact | A→D，[0,4)，r=1 MB/s，δ=0，初始 R=4 MB |
| Buffer | A、D 各 4 MB |
| Bundles | b1、b2 都在 0 生成，各 2 MB，按 b1、b2 處理 |
| Grid | Δ=1 秒，T=4 秒 |
| b1 結果 | 發送 [0,2)，arrival=2，提交後 R=2 |
| b2 結果 | 仍發送 [0,2)，arrival=2，提交後 R=0 |
| Buffer | 兩包來源合計 4−2t；目的地接收合計 2t（0≤t≤2），峰值各 4，皆過關 |
| 真實鏈路 | [0,2) 需要 2 MB/s，但 contact 只有 1 MB/s |

原因是 F09 的 window 檢查與 F11 的 `U[c]+S≤R[c]` 未包含其他已接受 bundles 的區間互斥。實際可改排 b2 在 [2,4)，但那是**另一份排程**，arrival=4；不能把 solver 的 arrival=2 當作可執行解。

這是「由 aggregate 解推出實際鏈路可行」的確定反例，不是 frozen aggregate 問題的 same-model mismatch。未改舊 comparison gate，因它本來只表示有限測例一致；本輪沒有進行後續效能比較。

候選修正：A. 將 claim 明限聚合模型，撤回可部署排程保證；B. 另建 transmission calendar 約束，再驗證 extension、提交與搜尋。兩者都未採用。

### 4.2 已有 CE-CALENDAR-01

空檔各 1 秒，總共 3 秒；r=1、S=2。總量可容納，任何單一空檔都不能連續送完。它除了展示重疊，也展示空檔碎裂。候選修正同上。

### 4.3 已有 CE-GRID-01

整數格點最早 arrival=4；連續時間可取 s=1.5，arrival=3.5，並有模型下界推導。錯誤外推在「只列舉 s∈ΔZ」卻聲稱解原連續問題。將 Δ 改小的測試只驗證另一個格點，不是一般連續 oracle。

### 4.4 已有 CE-EARLY

早到 B 的 label 不能保存整包跨越既有占用高峰；晚到者卻能繼續。它推翻「只看早到即刪除」，現行 F18 已加等待與用量條件，故不是現行 dominance 已錯的證據。

## 5. 研究問題與文獻重疊

問題存在：受時窗、資料量與儲存限制的路由確實可能無法沿最早時間路徑完成。**存在問題不等於本研究已找到未解缺口。**

| 項目 | 審查判斷 | 不能推導的結論 |
|---|---|---|
| SABR/CGR | SABR 在 route evaluation 已有 serialization、last-byte arrival 及不可分割容量檢查（S1） | 不能寫「既有 CGR 都忽略傳輸時間／容量」 |
| RVL | 是 SABR 的 Route Volume Limit，由 route 各 contact 的有效量限制形成，與 priority 等設定相關（S1） | 不是一個獨立路由演算法，也不是 transmission calendar |
| Alhajj–Corlay | v1 已有 splitting／forecast buffer；v3 將問題命名為 FEAP-CB，並給出其模型的最優性論證（S2） | FEAP-CB 是問題名稱，不宜列作沒有版本的 solver 名稱 |
| 本方法對 v3 | v3 §III-C 的中繼儲存區間是完整到達至下一跳開始，且 source/destination 假設沒有儲存問題；本法另查兩端及收發斜坡（S2） | 不可直接說本法已解同一問題，亦不能以可行率差稱搜尋較佳 |
| Label Setting | 是可採用的框架；本題限制需自行導出狀態及 dominance（S5） | 方法名稱、換成 physical-node graph 或引用學長不足以構成新穎性 |
| Dijkstra | 也是 label-setting 類方法。M0 可用單節點單標籤；v04 的時間相依 buffer 使該簡化失效 | 不能說任何 Dijkstra 都不能解；擴充狀態的最短路搜尋仍可能可用 |

可繼續研究的差異是「在明確相同或清楚區分的模型下，新的狀態表示／延伸生成／支配方式是否有可證明、可量測的收益」。**現有資料尚未證明這項收益。** 若最後只是解更簡化的問題、又更慢，僅換方法無法支撐貢獻。

文獻版本：arXiv 記錄 v1=2024-10-21、v3=2026-03-07。本次頁面沒有提供可確認的期刊發表欄位；不能據此斷言未投稿、未發表或沒有可信度。新穎性判斷應看公開內容，實作重現則固定版號。（S2 metadata）

## 6. 演算法審查

### 6.1 Label 與 U

`R`、`O` 是每次 query 固定資料，沒有逐 label 複製。`U` 是該候選路徑的累積用量，**目前沒有把全域已接受占用誤塞入 U**。

在允許同一 contact 重用且 quota 獨立受限時，U 有功能；但它是否是最精簡表示、是否值得其成本，尚未證明。不同路線各用不同 contact，向量便可能不可比較，即使那些 contacts 已過期也會保留 labels。目的地沒有後綴，仍用同一向量 dominance 尤其保守；這不會使最早取出目的地的答案變錯，卻不能拿來宣稱高效率。

必須修正前次口頭建議：由 pred 重建 U 只是換儲存方式，**不等於數學狀態只剩 (v,a)**。禁止重複 contact 也不自動讓歷史無關：哪些 contact 已經使用，會改變允許的後續動作。沒有證明前，不能移除必要歷史或沿用原 dominance。允許循環本身不是錯；case 12 已示範在不能原地等待時離開再回來的作用，但其實務頻率及成本仍未知。

### 6.2 Extension

| 檢查 | 實作與論證結論 | 邊界 |
|---|---|---|
| Node continuity | outgoing 篩選與 check_extension 一致 | 仍應驗證所有 contact 端點存在 |
| Store-and-forward | s≥完整 arrival，符合現行定義 | 未包含接收完後的驗證／處理時間 |
| Duration | S/r，固定正速率下成立 | S 與 r 要對應同一資料層級 |
| Contact end | f≤end；非 a′≤end | 只有 sender-window 語意下成立 |
| Propagation | 接收 [s+δ,f+δ]，未看到漏加或重加 | 常數 δ≥0；非任意時變 range |
| Quota | U[c]+S≤R[c]，候選不修改全域 | 無法排除已接受鏈路時段衝突 |
| Buffer | 檢查 sender 等待／下降與 receiver 上升 | no-copy、固定既有 O、完整接收後轉送 |
| 接點 | 同一曲線取 max 避免相鄰片段重複計數 | 不等於任意不合法重疊曲線都能正確表示 |
| 提交 | 選定後累加完整 visits | commit 本身不驗證，也無 calendar 更新資料結構 |

沒有證據說本版「只在完整抵達時檢查 buffer」；程式確實檢查背景折點與區間端點。對合法、非負、分段線性曲線及所選峰值事件語意，可支持全區間檢查。若要接受任意 background，需另定曲線合法性；目前介面沒有完整守門。

### 6.3 Dominance

現行充分條件是同 query／node、a1≤a2、整段可持有 S、U1≤U2。它的論證是：L1 等到 a2，再照抄 L2 的 contact 與發送時間。quota 由 U1+W≤U2+W≤R 保證，未來占用由無副本保證相同。

**本次未找到此明列模型下的 dominance 反例。** 但成立前提包括合法前綴、固定資源、無額外 visited/hop/energy 限制、δ≥0、前綴不留未來副本。不能改 buffer 釋放規則後直接沿用。相同 arrival 並不必然等價：U 不可比較時仍可能要分開；a、U 全相同則保留一個代表，程式先查舊 label 是否支配新 label，可避免互刪。

### 6.4 完整性與終止

所有輸入時間及 S/r 對齊 Δ 時，start=max(a,contact.start) 亦對齊，依 Δ 前進涵蓋該模型所有允許起送時刻。正的每跳時間與有限 T 限制路徑深度；延伸嚴格增時，按 arrival 取首個有效目的地的論證合理。這不是多項式複雜度證明。

現行 alignment 檢查還會檢查不可達／容量不足 contact 的 S/r，可能拒絕原本可求的非對齊資料。這在輸入契約內不是漏解，但大幅限制可輸入的異質資料；不能偷偷 round 成整秒。

連續時間目前未完成。只納入 contact 邊界或既有占用折點仍不充分，buffer 線性交點也可能產生新門檻。event-based 是候選研究方向，不是已可直接套用的修正。

## 7. Oracle 獨立性與範圍

| 項目 | 審查结果 |
|---|---|
| 呼叫 proposed solver | 否；`exhaustive_oracle.py` 只匯入標準函式庫 |
| 共用 dominance／pruning | 否 |
| 共用 route generation | 否；先列拓樸 walks，再對各 contact 的 starts 做 Cartesian product |
| 共用 buffer helper／commit | 否；使用 per-visit inventory 及另一個 commit |
| 共用輸入與模型 | 是；這是同模型比較必要條件，也會共享模型盲點 |
| Exhaustive 範圍 | 有限 contacts、合法格點、正每跳時間導出的深度界限；到目的地即終止 |
| 提早終止目的地 | 最小 arrival 問題下合理，已達目的地後的額外循環不改善 arrival |
| Continuous oracle | 沒有；Δ=1/2 也只是一個較細格點 |
| 多包比較 | 用 proposed 所選排程共同提交，再分別重建 R/O；避免 tie 導致下一題不同 |
| 多包最優性 | 沒有；上述做法不枚舉所有前包最优 tie，也不驗證全批最佳 |

結論：**具實作層獨立性，未发现應因共用 solver 而列 HIGH 的問題。** 但它不獨立驗證物理模型，也不是外部團隊盲測；匯入清單測試只能檢查耦合，不能證明邏輯獨立或完整正確。

Oracle 會檢查全部节点、背景事件時間；proposed 只檢查相關延伸區段。若輸入 O 本身已在無關處超量，兩者可能不一致。因此「O 來自合法先前預約」必須是明列契約，不能將非法背景的差異直接稱 frozen solver 反例。

## 8. Assumption 審查表

分類：合理研究假設＝明確限定問題；可接受簡化＝需有使用範圍；危險簡化＝直接影響可行域或結論；不現實且影響結論＝已有反例或缺必要機制。不是以是否常見判定合理。

| Assumption | Current Definition | Why It May Be Unrealistic | Severity | Evidence Needed | Recommendation |
|---|---|---|---|---|---|
| 集中管理 | 中央保存 R/O、發局部指令 | 架構可選；不證明控制可達或狀態新鮮 | HIGH，E/F | 任務控制時序、預載窗口 | 作有條件研究假設；禁止由 NASA 名稱直接背書 |
| 全網即時同步 | 現行中央模型不要求每個節點都存全域表 | 不能誤批為已實作廣播；真正缺口是指令／回報 | MEDIUM，E | 指令交付與狀態修正機制 | 精確描述中央台帳，不宣稱實測狀態等於預約 |
| 完全已知 R/O | 接受後 deterministic 更新 | 失敗、延後、外生流量會使台帳失真 | HIGH，E | 無偏離前提或遙測／重規劃 | 離線理想研究可留，部署 claim 需補 |
| Arrival 已知 | 輸入所有 g，逐包查詢 | 尚未選批次或線上，不能假裝有未來需求資訊 | HIGH，E/F | 需求生成及可得時間 | 明定資訊集合 |
| 順序固定 | 列表順序，例子依 g | 不保證公平、接納最大化 | HIGH，F | 順序政策與 tie | 可作研究條件；不稱全體最優 |
| Contact window | sender 開放區間，傳完≤end | 外部 contact 資料可能採不同時鐘／定義 | MEDIUM，E | plan 產生器語意 | 明定 sender、receiver 及 clock 基準 |
| 固定 rate | contact 內常數 | ACM、有效 throughput 或損失未反映 | MEDIUM，E | 實測或鏈路預算 | 可接受的理想化；緊邊界需 margin |
| 固定 δ | 每 contact 非負常數 | 移動距離造成變化；0 秒只是 toy | MEDIUM，E | range 與誤差界 | 不把 0/1/2 秒當任務參數 |
| Aggregate quota | 單一總量，不看 busy intervals | 已有直接重疊反例 | CRITICAL，C/E | 同鏈路排程檢查 | 對實際排程 claim 不可接受 |
| Contact 中間起送 | 任一合法格點且完整送完 | 無啟動、對準、guard time 模型 | MEDIUM，E | 可用資料時窗是否已扣開銷 | 若已預處理可留，否則需調整模型 |
| 不分割 | 每包大小固定 | BP 可限制 fragmentation，但不表示所有任務都禁用 | MEDIUM，E | 應用／協定設定 | 合理限定；須明列理由 |
| 不可暫停且一跳單 contact | S/r 連續送完 | 不分割與不可暫停是兩件事 | HIGH，E/F | CLA/服務政策 | 各自宣告，所有方法對齊 |
| 完整接收後轉送 | s_next≥a | 禁 cut-through，可作整包路由條件 | MEDIUM，E | 目標 BPA/CLA 行為 | 保留但不概括所有系統 |
| 逐 byte 釋放 | 已發資料立即離開所有計量 buffer | 尚無實作證據；需重傳時可能仍存副本 | HIGH，C/E | 儲存釋放及可靠傳送流程 | 危險簡化；不能先說比整包預留更真實 |
| Destination 立即釋放 | 最後 byte 到達後交付清空 | 應用未必立即取走；資料儲存可能轉移另一層 | MEDIUM，E | 計量範圍與服務時間 | 可限定路由層 buffer，需界面說明 |
| No loss/retransmission/failure | 確定性傳輸，无額外資料／時段 | 消除實際網路擾動；無可靠性證據 | HIGH，E | 目標鏈路或誤差敏感度 | 理想可行性研究可留，不宣稱實際 delivery 保證 |
| No clock offset | 全域理想時間 | 首尾恰好相接可能衝突 | MEDIUM，E | 同步精度、guard margin | 明列理想化及後續測試 |
| No scheduling contention | 無共用 radio state | 物理鏈路可能互斥 | HIGH，E | radio 數／half-duplex／預處理證明 | 必須說明 plan 是否已排除 |
| Zero processing delay | 收完即可出發 | 程式處理與控制下發需要時間 | MEDIUM，E | 資料處理／控制延遲 | 離線可忽略求解時間，線上不行 |
| Zero queueing delay | **不是完全零**：有等 contact／buffer 的等待 | 缺的是實際鏈路佇列與 contention，而非所有等待 | HIGH，E | 執行服務紀律 | 勿將模型描述成無任何排隊／等待 |
| No protocol overhead | S/r，未分 payload/EVC/CLA volume | 恰好容量可能因 header 等失效 | MEDIUM，E/F | S、r 計量層級及 overhead | 有效速率或 wire size，與 SABR 一致 |
| 同時事件峰值 | 生成後／交付前合計上界 | 是保守約定，可能不是硬體排序 | MEDIUM，E/F | 事件順序 | 合理但需限定；比較必須相同 |
| Grid/horizon | Δ=1、T=12 主測例 | 任務並非天然整秒、12 秒期限 | HIGH，E | 離散服務規格或誤差界 | 定義格點問題，不推原連續問題 |

## 9. Topology 與參數

目前主例屬於 **Toy topology + Validation topology**。它是人工合成，但尚不是具參數生成機制、分布與規模設計的 Synthetic research topology。沒有 Literature-based 或 Orbit-derived topology 的本方法實驗。

1–5 個節點、0–8 個 contacts 並不是正確性案例的缺點；刻意安排時序以觸發反例也是必要作法。問題是拿它支持一般效能、實際衛星場景或可擴充性。學長的 47-node 實驗不是本研究的資料，也不能移借其結果。

| Parameter | Current Value | Source | Realistic? | Risk | Suggested Range / Action |
|---|---:|---|---|---|---|
| data rate | 主例4；case09為2 MB/s | Synthetic：validation_cases | Unsupported（任務代表性） | MEDIUM | 先選任務，再由資料決定；不要任意給「衛星常用範圍」 |
| contact duration | 14案例1–7秒；主例1–2秒 | Synthetic | Unsupported | HIGH | 保留邊界例，另用任務 plan |
| propagation delay | 0、1、2秒；主例0/1 | Synthetic | Unsupported | MEDIUM | 由 range/c 或來源設定；0 不當物理實測 |
| bundle size | 14案例全部4 MB | Synthetic；NASA HDTN有100 B–4 MB需求範圍（S4） | 值有相關產品範圍，**此 workload 仍 Unsupported** | HIGH | 不能因4 MB落範圍內就聲稱流量具代表性；需分布與應用 |
| buffer size | 14案例全4 MB；CE-grid 中繼5 MB | Synthetic | Unsupported | HIGH | 探索 M/S 而非只用恰好一包 |
| physical capacity | 由rate×duration，14案例4–28 MB | Derived from Synthetic | Unsupported（實際鏈路） | MEDIUM | 另區分物理量與 admission quota |
| initial quota | 2、3、4、8 MB | Synthetic | Unsupported（預約來源） | HIGH | 從一致的先前排程推導，或標外生 allocation |
| traffic load | 未定義分布／強度 | Unsupported | 無法判斷 | HIGH | 定義 offered load；拒收不移出分母 |
| bundle arrival rate | 無統計到達率；g多0，部分1 | Synthetic | Unsupported | HIGH | 2個已知g不構成arrival process；批次／線上分開 |
| simulation horizon | 全14案例T=12秒；CE-grid T=4 | Synthetic | Unsupported | HIGH | 目前是搜尋期限而非完整網路模擬時長 |
| number of bundles | 每案例1；主例2，合計15 queries | Synthetic | Validation only | HIGH | 需多包序列、同值路徑與順序研究 |
| number of nodes | 1–5 | Synthetic | Validation only | HIGH | 後續由選定場景及規模系列決定 |
| number of contacts | 0–8 | Synthetic | Validation only | HIGH | 控制密度、時間重疊與平行 contacts，不只節點數 |
| grid interval | 14案例1秒；CE另0.5秒 | Synthetic | Unsupported作連續近似 | HIGH | 後續敏感度可用多Δ，但不能宣稱由此證明連續最優 |

「Unsupported」是指所宣稱的真實代表性無來源，不是說人工測試值不能使用。無來源的參數不補造合理範圍。

## 10. Baseline fairness

| 比較對象／方式 | Status | 現況與理由 |
|---|---|---|
| Proposed vs independent grid exhaustive | FAIR | 同一問題、資源與目標，用於 correctness；不作大型速度競爭者 |
| Dominance ON/OFF，同一 query | FAIR | 可測剪枝影響；不等於證明優於既有路由 |
| Time-only / no-buffer | FAIR 作 ablation；UNFAIR 代表完整 CGR | 目前未找到其 benchmark 實作，不能假裝已比較 |
| Capacity-filtered time-dependent Dijkstra | FAIR 用於 M0；QUESTIONABLE 直接當 v04 exact baseline | M0條件不同，不能靠故意不查動態buffer創造優勢 |
| SABR-style | QUESTIONABLE（尚未實作／驗證） | 須明確 route count、EVC、priority、backlog、重路由與停止規則 |
| RVL | QUESTIONABLE 作獨立 baseline | 它是標準中的量，不是完整方法；不能簡化成 min R 後叫完整SABR |
| Alhajj–Corlay contact splitting/edge pruning | QUESTIONABLE（重要但未對齊） | calendar、buffer生命週期、source/destination限制與grid均須列差異 |
| Proposed有全域預約、baseline只有本地資訊 | UNFAIR 支持「求解方法本身較佳」 | 可比較系統設計但要明示資訊差，不能归因Label Setting |
| 不同模型可行率／arrival直接比較 | UNFAIR | 改變可行域即可改變答案，不能當算法品質 |
| 同一 workload 的各方法逐包自行提交 | FAIR 作系統策略比較 | 後續狀態會不同，不能稱每次 query 同輸入；需固定順序與tie政策 |

目前沒有證據指出有人「故意」削弱 baseline；可確認的是尚未建好可供判斷的正式 baseline。

## 11. Experiment 與 Metrics

有失敗案例、adversarial 邊界、循環與格點／calendar 反例，不能批評為「全是成功例」。不足的是涵蓋面：幾乎同大小、同buffer，多包互動只有主例；未見多種 workload、隨機小網路、規模系列、參數敏感度、種子、信賴區間或重複計時。

Deterministic 正確性手算不需要亂加 seeds 或 CI；只有開始主張統計性能與網路代表性時才需要。現在不能拿15次人工查詢算一個漂亮平均「成功率」外推。

| Metric | 優先度 | 現有證據／正確解讀 |
|---|---|---|
| feasible/infeasible agreement | 必須 | 有保存15次；需分 false feasible、false infeasible |
| earliest-arrival error | 必須 | 有格點答案比對；同模型、同輸入才有意義 |
| 完整 schedule feasibility | 必須（若claim可執行） | 目前只aggregate，新增反例已失敗於鏈路互斥 |
| 接納率／可行query比例 | 必須（多包claim） | 分母含全部請求；與實際delivery分開 |
| delivery success ratio | 必須（若claim網路傳送） | 目前無執行模擬，沒有這項結果 |
| travel delay A−g | 必須（earliest arrival研究） | 比較共同可行查詢，並另外報拒收；失敗不能填0 |
| runtime、peak memory | 必須（效率claim） | 尚無；含預處理與更新，另報核心搜尋 |
| labels created/enqueued/expanded/pruned | 必須（Label Setting效率） | 已記部分；還缺峰值live數與dominance比較次數 |
| rejection reason | 必須 | 有trace，但短路順序的第一原因不等於唯一原因 |
| scalability | 必須（擴充性claim） | 缺少節點、contact、Δ、T、預約事件數的系列 |
| contact utilization | 建議 | 要先有無衝突時間表；總quota使用率不等於時間可排性 |
| buffer occupancy／峰值 | 建議；buffer保證需有驗證 | 已有toy曲線；後續含安全裕度及哪一層儲存 |
| rerouting／control overhead | 視claim；目前可不做 | 本版無失敗重規劃，不能將rerouting=0解讀為優點 |
| energy、額外cost | 目前可以不要 | 沒有研究需求，不應為了使用SPPRC而硬加 |

未來計時需保存 n、mean/min/max/std、median/P95、重複次數與環境；統計CI以適當獨立單位（例如workload/seed）估計，不能把同一台帳內高度相依bundles假裝全獨立。Timeout、INVALID_INPUT、NO_ROUTE_ON_GRID、真正證明不可行必須分開。

## 12. Claim 審查與過度解讀

| Claim | Evidence | Supported? | Problem | Safer Wording |
|---|---|---|---|---|
| 目前為有限grid＋quota原型 | README首段、PPT圖解p3 | YES | 無 | 保留 |
| 15查詢一致、18tests通過 | 保存JSON/CSV/log | YES，歷史紀錄 | 本次未重跑，不擴張成一般證明 | 保存測例中一致 |
| dominance可保留最佳值 | suffix-copy論證及ON/OFF | CONDITIONAL | 依固定資源、無副本等前提 | 在所列模型下具充分條件論證 |
| 可產生節點照表執行的排程 | centralized §2、5、9；圖解p2 | NO作現況保證 | R01反例；架構願景與原型能力混用 | 架構目標；本版安排尚未保證鏈路無衝突 |
| 同時處理傳輸時間／容量／buffer是貢獻 | centralized §8、11的研究定位 | 尚未成立新穎性 | 已有相關工作；方法換名不等於突破 | 目前研究內容，貢獻待同模型比較 |
| c4起始時間只有7或8 | 圖解v02 p10 | YES僅Δ=1 | 單獨看頁面容易誤以為物理上只有兩種 | 在Δ=1格點下有7、8兩種 |
| labels 7→3 / 7→5 | 詳解p43、dominance CSV | YES指定enqueued | 不能推CPU/記憶體同比下降 | 指定案例入列數下降，效能未測 |
| Continuous-time最優 | 現行文件明列未完成 | NO；不是發現现行偷偷宣稱 | 已有反例界線 | 不列成成果 |
| Scalable / robust / superior | 現行README/PPT未找到已完成宣稱 | Unsupported若未來使用 | 不能把潛在風險捏造成現有造假 | 仍待實驗 |
| NASA支持集中式全域準確buffer排程 | 官方只支持部分路由／contact機制 | NO | 把不禁止／可預計算誤當整個系統已可行 | 中央設計為本研究假設，官方依據只支持明列部分 |
| 逐byte更符合真實BP | v04是使用者指定模型，无實作證據 | Unsupported | 可能低估持久儲存／CLA資料 | 理想化資料占用模型，待對應協定層 |

目前主要文件已有多處自我限制，沒有發現把toy性能當大規模優勢的正式結果表。真正要撤回的是任何超出上述條件的口頭說法，不是刪掉有價值的失敗案例。

## 13. 文獻依據分類

| 內容 | 分類 | 審查 |
|---|---|---|
| SABR有整包傳輸時間／RVL檢查 | Direct | S1指定章節支持 |
| BP不規定路由演算法與資訊庫建立 | Direct | S3 §1；不等於中央零成本 |
| NASA可由既算contact plan取得路由資訊 | Direct | S4 §3.5；不證明全域buffer即時正確 |
| 學長B用Label Setting處理其子問題 | Direct（依既有PDF extraction） | 細部label/dominance非作者明列，不能補成Direct |
| 本法 L=(v,a,U)、F18及no-copy前綴論證 | Derived／本研究設計 | 不需要假裝每個新式子都有文獻原樣；但需要完整推導 |
| 逐byte曲線 | Derived from chosen assumptions | 它的代數可成立，實務適用性仍Unsupported |
| 4MB／4MB/s／4MB buffer／12秒 | Synthetic | 人工驗證數據，不是衛星任務實測 |
| 此參數能代表Space DTN | Unsupported | 單一產品支持4MB也不能證明整組比例具代表性 |
| 本方法優於SABR／contact splitting | Unsupported | 沒有公平benchmark |
| 使用Label Setting便有新穎性 | Unsupported | 框架已存在 |
| 文獻尚未發期刊所以無可信度 | Unsupported inference | 發表狀態與內容是否成立需分開 |

來源（本輪重新查閱）：

- **S1** [CCSDS 734.3-B-1, Schedule-Aware Bundle Routing](https://ccsds.org/Pubs/734x3b1.pdf)，§3.2.6.3–.9：serialization／last-byte timing／EVL、RVL及不可分割篩選。它不是本研究現成的完整buffer模型。
- **S2** [Alhajj–Corlay v1](https://arxiv.org/html/2410.15546v1)、[v3](https://arxiv.org/html/2410.15546v3)、[版本紀錄](https://arxiv.org/abs/2410.15546)。v3 §I、III-C、IV為本輪重點；本報告沒有獨立證明其所有定理，也不把作者最優性宣稱當本法保證。
- **S3** [RFC 9171](https://www.rfc-editor.org/rfc/rfc9171.html)，§1、3.1、5.4、5.11：路由範圍、retention與discard；不足以直接推出逐byte立即釋放。
- **S4** [NASA HDTN Software Requirements Specification](https://ntrs.nasa.gov/api/citations/20240011318/downloads/TM-20240011318.pdf)，§3.5、HDTN REQ-001。軟體支援範圍不是任務流量分布。
- **S5** Irnich & Desaulniers, *Shortest Path Problems with Resource Constraints*, 2005，[章節](https://www2.imm.dtu.dk/courses/02735/rcsppchapter.pdf)，[DOI](https://doi.org/10.1007/0-387-25486-2_2)。用於框架背景；本輪PDF網頁無文字抽取，未據此新增任何逐頁細部主張。

## 14. 文件／程式／PPT 差異

| ID | 對照 | 發現 | 判斷 |
|---|---|---|---|
| D01 | M0/v03 vs v04 | 舊文件無背景、earliest-start、單node label；現行有O、逐grid、多label | 已知版本差異；不得當現行互相等價 |
| D02 | algorithm_pseudocode_v02 vs v01 | v02反而是較舊模型 | 檔名容易誤用；README已警示 |
| D03 | v04原例 vs walkthrough/PPT | 原例5contacts、arrival7/10；現例8contacts、8/12 | 不是算法mismatch，現行符號文件已說明 |
| D04 | v04 §9／snapshot文字 vs src | 保留「沒有實作／未發現程式」的歷史時點敘述 | 必須按日期讀，不能代表目前 |
| D05 | 公式F02 vs validate_input/search | F02限定0≤時間；程式未檢查g與start非負，也未全面驗證M/端點/background/實傳quota | 輸入契約未完整落實，未執行非法輸入反例 |
| D06 | pseudocode外層 vs實際入口 | pseudocode驗證後commit；compare_one做了，build_walkthrough直接commit | 防護不是所有呼叫路徑強制具備 |
| D07 | 「記錄傳輸區間」vs code | hops與s可重建；沒有獨立Ω台帳或衝突檢查 | 不可將可重建資料稱已實作calendar |
| D08 | 中央架構/PPT p2 vs solver | 說節點依排程執行，solver可能產生重疊安排 | 現況能力與部署目標不一致，R01 |
| D09 | Q說明 vs heap trace | Q文字指待延伸labels；heap亦可含已dominated stale項及目的地 | 簡報可作有效Q示意；一般trace應區分raw/active queue |
| D10 | U向量 vs U=∅、舊U佇列 | 表示／命名不一致 | 低風險但已造成使用者困惑 |
| D11 | 初始R與「只有前包占用」 | c7已有減量但沒有來源排程 | 必須標外生quota或補來源，非計算錯字 |
| D12 | 凍結來源與輸出manifest | 核心hash一致，renderer不同；report tests=18是固定metadata | 不得宣稱全專案從未修改或本輪新測18項 |
| D13 | README現行20頁 vs逐頁PNG | 圖片目錄仍17頁舊圖解，README已標17張 | 不可當20頁逐頁截圖使用；不是數據反例 |
| D14 | 首跳窗口／buffer／dominance公式 vs code | 核心判別式一致，程式先quota短路再時間 | 無實質mismatch；未執行不是PASS |

## 15. Top 10 Most Serious Problems

### 1. 實際傳輸排程保證不成立（R01，CRITICAL）
- 重要：這直接觸及「整包能否送完」。不修：會回傳物理上做不到的arrival。
- 老師：「兩包都排同一時段，誰先送？」
- Reviewer：The feasibility claim omits transmission-resource conflicts.
- 候選修正：限定claim，或經確認後加入calendar；先用本次兩包反例驗證。

### 2. 貢獻尚未與既有工作分開（R03，HIGH）
- 重要：方法名稱不是研究貢獻。不修：論文可能只是較簡化的重作。
- 老師：「比SABR與contact splitting新增了哪一個能力？」
- Reviewer：Novelty over existing capacity- and buffer-aware routing is not demonstrated.
- 候選修正：固定版本與同模型比較矩陣，選一個可證明／量測的差異。

### 3. 逐byte釋放缺乏實作層依據（R04，HIGH）
- 重要：buffer是研究核心。不修：可行率優勢可能來自低估儲存。
- 老師：「資料送掉就刪，那重傳拿哪份？」
- Reviewer：The storage lifecycle is not tied to the target protocol implementation.
- 候選修正：指定buffer層級、可靠傳輸與釋放事件；重新評估state證明。

### 4. 連續時間保證不存在（R02/R26，CRITICAL於該claim）
- 重要：一般網路沒有天然整秒起送限制。不修：漏掉更早解，甚至誤判無解。
- 老師：「為什麼只能7或8，不能7.5？」
- Reviewer：Grid optimality does not establish optimality for the stated continuous-time problem.
- 候選修正：正式研究格點問題，或另證候選事件完整性；不靠更細格點掩飾。

### 5. 中央控制的因果時序未定（R05，HIGH）
- 重要：決策須在動作前送到。不修：把預知資訊及零延遲控制當免費能力。
- 老師：「bundle剛生成就要送，中央何時收到請求並下令？」
- Reviewer：Control-plane reachability and information availability are unspecified.
- 候選修正：先固定批次预載或線上模式，給明確資訊時間。

### 6. 沒有正式且公平的baseline（R06/R10，HIGH）
- 重要：無法區分模型放寬與演算法進步。不修：比較結論不成立。
- 老師：「你的CGR是哪一版？做了哪些檢查？」
- Reviewer：The comparison does not control for differing constraints and network knowledge.
- 候選修正：同輸入、同可行域、同目標；原版與改編版分別標示。

### 7. Toy結果無外部代表性（R07，HIGH）
- 重要：最大五節點不代表衛星網路。不修：不能支持擴充性／任務價值。
- 老師：「這些contact怎麼來的？為何buffer剛好一包？」
- Reviewer：The evaluation is limited to hand-crafted validation instances.
- 候選修正：保留toy驗證，另選一種明確任務與可重現資料來源。

### 8. 多包與拒收語意未封閉（R08/R09，HIGH）
- 重要：被拒收資料和同值路徑都影響後續資源。不修：系統負載与公平性解讀失真。
- 老師：「找不到路的bundle還在來源嗎？換順序會怎樣？」
- Reviewer：Admission, tie-breaking and workload accounting are insufficiently specified.
- 候選修正：定義drop/retry及分母；將單query與逐包策略分開測。

### 9. U與枚舉的計算成本未知（R11/R16，HIGH）
- 重要：目前方法可能只在極小例子可用。不修：不能保證中央能及時算完。
- 老師：「U長度多少？一天contact plan會產生多少labels？」
- Reviewer：No complexity or performance evidence supports the proposed state representation.
- 候選修正：先分析與記錄成本；U是否可縮減須另證明，不先刪。

### 10. 可用資源與驗證契約不完整（R12/R13/R18，HIGH）
- 重要：任意R/O不一定來自合法排程，獨立檢查也非入口強制。不修：數學合法輸入與實際API分歧。
- 老師：「c7少掉2MB是誰用的？每次commit都驗證了嗎？」
- Reviewer：The provenance and admissibility of reservation inputs are not established.
- 候選修正：定義初始allocation與accepted ledger，固定完整驗證入口。

## 16. 模擬口試問題與目前回答能力

| # | 問題 | 能否回答 | 尚缺內容 |
|---:|---|---|---|
| 1 | 為何一定要Label Setting？ | PARTIAL | 能說明一節點一label失效，不能證明此方法效率必要性 |
| 2 | CGR已有容量管理，你新增甚麼？ | NO | 可驗證的貢獻差異 |
| 3 | R是volume還是calendar？ | YES | 是aggregate quota，不能保證傳輸互斥 |
| 4 | 中央管理為何不用全網廣播？ | PARTIAL | 可發局部指令，但時效／可達未建模 |
| 5 | 中央何時知道bundle生成？ | NO | 批次／線上規格 |
| 6 | 為何逐byte釋放能在BP實作？ | NO | target storage/CLA證據 |
| 7 | 相同arrival可否合併？ | YES | 需看U／其他狀態；同a、U留代表 |
| 8 | 如何保證dominance不漏最佳解？ | PARTIAL | 有條件suffix-copy證明，仍需完整合法輸入／實作契約 |
| 9 | 為何只查折點就檢查全時段？ | YES | 合法分段線性、峰值事件約定下成立 |
| 10 | 為何arrival能晚於contact end？ | YES | end是sender窗口，arrival另加δ |
| 11 | 格點答案等於連續最佳嗎？ | YES（否） | 已有反例；沒有連續solver |
| 12 | Oracle是否呼叫同一段程式？ | YES | 核心求解與可行性helpers分開 |
| 13 | Oracle是否證明物理可執行？ | YES（否） | 同樣不查calendar |
| 14 | 五節點為何能代表衛星網路？ | NO | 只能稱驗證拓樸 |
| 15 | 4MB與4MB buffer的依據？ | PARTIAL | 4MB有產品支援範圍；組合與分布無任務依據 |
| 16 | 少labels是否更快？ | NO | 沒有runtime/memory研究 |
| 17 | b1同樣早到的不同路徑會影響b2嗎？ | PARTIAL | 會，但未做系統分析 |
| 18 | 被拒收bundle會去哪裡？ | NO | admission/drop/retry規則 |
| 19 | 能否禁止循環後拿掉U？ | PARTIAL | 不可直接推導，歷史限制需重證dominance |
| 20 | 與FEAP-CB解的是同一問題嗎？ | YES（目前否） | calendar、buffer及grid不一致 |
| 21 | radio只有一組時可同時用兩contact嗎？ | NO | 硬體互斥未定義 |
| 22 | 結果最優是每包還是全部bundle？ | YES | 固定前包預約下的單query格點目標 |

## 17. 修正順序、可保留與應撤回內容

1. **先決定claim與可行集合**：承認R01反例；決定第一階段是否只研究aggregate grid，或另立calendar問題。這是研究選擇，本次未修改。
2. **固定buffer與架構契約**：釋放／副本／拒收、source/destination、批次／線上、資訊可得性、初始R/O來源。
3. **固定文獻差異與正式baseline**：先證明比較是同一問題，或清楚拆開模型差異研究。
4. **補正確性與實作契約**：若經確認修改模型，再做最小反例、輸入界線、獨立驗證；出現same-model錯誤立即停止效能比較。
5. **最後才做性能與外部效度研究**：代表性拓樸、多工作負載、規模與敏感度；控制trace成本及資訊公平性。

**What Can Stay**：現行原型作限定模型參考；S/r與δ的區分；候選不先扣全域資源；全區間buffer檢查；條件式dominance；獨立grid完整搜尋；toy手算、失敗案例及歷史版本。

**What Must Be Reworked**：實際可行排程claim、研究貢獻、buffer實作語意、中央控制時序、拒收／順序／tie、baseline與性能研究設計、初始台帳來源及輸入契約。

**What Must Be Removed**：任何「首次考慮transmission delay／容量」、「兩包依序規劃就不會衝突」、「已解2024完整問題」、「少labels所以一定更快」、「toy代表真實網路」、「NASA所以整個假設成立」的說法。這是撤回不成立主張，**不刪除歷史文件或反例**。

完成項目：跨文件／程式／文獻／PPT內容audit，保存一個2-query實際重現反例。
生成文件：本報告、`output/research_audit_v01/evidence_inventory.json`、`counterexample_sequential_overlap.json`。
修改文件：僅README／PROGRESS／CHANGELOG加入審查入口與紀錄；未修改code、algorithm、paper或PPT。
輸出位置：`docs/`及`output/research_audit_v01/`。
建議下一步：先討論R01與R04的模型及claim，確認後才另開修正工作。
