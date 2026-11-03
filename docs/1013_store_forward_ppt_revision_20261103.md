# 1013 → 1103：新版演算法簡報修改清單

日期：2026-11-03。

## 檔案

- 原稿：使用者提供的 `F:/1013.pptx`；保留原檔，未提交至 GitHub。
- 新稿：`output/presentations/1103_新版演算法完整流程.pptx`，32 頁。
- 折線修訂稿：`output/presentations/1103_新版演算法完整流程_原版折線.pptx`，依使用者偏好沿用原 1013 的拓樸折線，保留上述 32 頁文字與數值。
- 逐頁講稿：`docs/1103_store_forward_slide_notes_20261103.md`；同樣內容已寫入 PPT 講者備註。
- 案例資料：`output/ppt_store_forward_20261103/walkthrough.json`。
- 案例重建：`src/experiments/ppt_store_forward_walkthrough_20261103.py`。
- 簡報排版原始碼：`src/presentations/build_1013_store_forward_20261103.mjs`。

## 採用版本與適用範圍

採用 GitHub `d8ade1c` 的 store-and-forward 區間 Label 候選：`docs/store_forward_label_20261103.md` 與 `src/experiments/store_forward/store_label.py`。不修改演算法，也不改凍結的 v04。

- 每跳完整接收後才起送：`s2 ≥ A1`。
- Label 為 `(c, I, pred)`，`I` 是可達起送時間區間。
- Q 依 `lo(I)+S/r(c)+δ(c)` 排序，同值採建立順序。
- 以原始 contact 為索引的 `Reached[c]` 移除已涵蓋時間；不套用舊版「同節點較早抵達」支配。
- 無獨立 aggregate quota；每跳必須有連續且未預約的完整傳送時段。
- deadline 在展示中為選填；本例未設業務期限。原型的 `T=12` 是有限 Contact Plan 的完整抵達涵蓋上界，不額外排除本例排程。

## 最重要的數值變更

原稿把 c7 的獨立配額設為 2 MB，使第二包無法使用它。新版沒有此配額，保留原窗 `[4,5]` 與速率 4 MB/s 時，c7 可連續傳 4 MB。

| Bundle | 本次搜尋結果 | 發送時段 | 完整抵達 D |
|---|---|---|---:|
| 第一包 X→D，g=0 | c1→c2 | c1 `[2,3)`、c2 `[6,7)` | 8 秒 |
| 第二包 A→D，g=1 | c6→c7 | c6 `[1,2)`、c7 `[4,5)` | 5 秒 |

第二包由原稿 12 秒改為 5 秒，是**移除 c7 獨立配額造成可行集合變更**，不能視為單靠區間搜尋就讓同模型改善 7 秒。

c4→c5 保留作為未選路徑的補充回溯示例：固定末跳 `s=10`，在 c4 的 `[7,8]` 內取最晚前驅 8，9 秒到 B，12 秒到 D。主搜尋已在 c7 的目的地 Label 結束，未真的展開 c4。

## 逐頁內容

| 頁次 | 修改內容 |
|---|---|
| 1–2 | 新版總流程、中央規劃環境、F 與 O 的角色 |
| 3 | 區間 Label、前驅、key 與 lo(I)；Label ID 和 contact ID 分開 |
| 4–6 | 保留五節點八 contacts，列全參數與時間／buffer 符號，明示 c7 配額變更 |
| 7 | SourceRange 的 Head／Tail；沒有 deadline 的處理；連續 `[7,8]` |
| 8–11 | 第一包來源初始化、兩個下一跳、Q、回溯、F 及 B 曲線 |
| 12–14 | 第二包依 c3／c4／c6 初始化；Q 排成 key 2／3／8 |
| 15–16 | c3→c2 因預約拒絕；c3→c5 因 B 峰值 8>4 拒絕 |
| 17–18 | c6→c7 建立 key=5 的目的地 Label；c6→c8 因 Head>Tail 拒絕 |
| 19–22 | 先取出目的地、回溯實際時間、提交選定路徑及兩包結果 |
| 23 | 第二包所有 Q 變化與拒絕原因總表 |
| 24 | 未選 c4→c5 的區間回溯示例，與主搜尋明確分開 |
| 25 | 預約 `[3,5)` 如何切出 `[1,2]∪[5,9]` 起送集合（獨立示例） |
| 26 | Reached 去重，取消原稿的 s=7／8 分別建 Label 再支配示範 |
| 27–31 | 英文虛擬碼：逐包規劃、初始化、搜尋、起送集合、BufferFilter、回溯與提交 |
| 32 | 驗證範圍、原型尚缺內容及後續工作 |

## 檢查與限制

- 原型搜尋與逐步紀錄一致，兩包結果為 8、5 秒。
- 另用 1/4 秒窮舉核對這個小型、無環拓樸，不以格點核對取代一般連續時間證明。
- 獨立重放不共用候選的 `occ`、`ramp` 或 `buffer_filter`，檢查完整來源、中繼、目的地的聚合占用，包括來源接納與目的地釋放的兩側值。
- 兩包來源不同，目的地接收時段不重疊，所以本例通過完整節點核對，不代表原型已完成 endpoint Commit。
- 現行原型仍缺 `DestinationFilter`、目的地 replay，以及來源／目的地 Commit；已在 P30–32 與講者備註標明。
- 保留「候選方法」；未新增 RetimePath、TRACK、incompleteLB 或保護 ε，未跑研究級實驗。
- 32 頁均有講者備註；6 個 native tables、3 個 native scatter charts；拓樸與時間軸使用可編輯物件。
- 保留原尺寸、標楷體與紫／綠／橘配色。檔案結構、字型、幾何與圖表檢查通過；已逐頁渲染檢查並重匯入最終檔。
- 本機未偵測到 PowerPoint COM，因此未宣稱已在原生 PowerPoint 中開啟或測試編輯。

## 重現本例

```powershell
python src/experiments/ppt_store_forward_walkthrough_20261103.py
```

這只核對本簡報兩包，不執行完整實驗矩陣。排版程式使用既有 Presentations skill 的 Artifact Tool；先依 `load_workspace_dependencies` 設定 `RUNTIME_NODE_MODULES`、`PRESENTATIONS_SKILL_DIR`，再以 bundled Node 執行，參數為原始 PPT 路徑。它輸出私人 build 目錄的 draft，仍須依該 skill 完成 finalization；不直接覆寫已交付的新稿。

## 使用者下一步

先看 P5 的 c7 模型變更、P12–23 的第二包流程，再看 P27–31 的英文虛擬碼。在 PowerPoint 確認字型、連線、圖表與講者備註。

## 原版折線修訂（同日）

- 從原 1013 的第 6 頁擷取 8 條三點折線的轉折位置與標籤位置，保存於 `src/presentations/1013_topology_link_geometry.json`。
- 在新版既有節點位置上套用原轉折樣式，恢復平行 contacts 的分離路徑，保留原版開放箭頭與新版路徑配色。
- 修改全部 15 個含拓樸的頁面（P4、8、9、11–19、21、22、24）；其餘 17 頁預覽保持一致。
- 比對兩份 PPT：32 頁文字與講者備註、所有表格內容、3 個原生圖表 XML 皆相同；未修改演算法或案例資料，未重跑實驗。
- 修訂稿仍為可編輯的 native shapes；保留前一份簡報及原始 1013。

## 完整 Label 展示修正

- 另存 `1103_新版演算法完整流程_完整Label.pptx`，保留原版折線與全部案例數值。
- 每一步 Q 改列完整 `(c,I,pred)`，`key` 另列在三元組外；例如 `L2=(c2,[6,6],L1), key=8`。來源前驅為 SOURCE（Python 為 None）。
- P3 補齊 Label 編號、contact、起送區間、前驅引用及推導 key；P9 明示 L1 取出後仍由 L2、L3 的 pred 引用。
- P23 明標摘要欄位為 Label ID:key；P26 區分 Q、pred 鏈與 Reached，P28/P31 補齊取出與回溯符號。
- 本次為呈現與虛擬碼記法修正，未修改研究演算法、數值或實驗。
- 驗證：32 頁重新匯入與渲染完成；套件、字型及版面檢查通過（0 幾何問題），前驅示例核對通過；3 張圖表 XML 與 contact／結果數值維持不變。未在原生 PowerPoint 驗證。

## v1.1：Buffer 圖改為分段直線

- 之後此簡報修訂採 `v1.x` 命名；本次另存 `1103_新版演算法完整流程_v1.1.pptx`，不改名或覆蓋先前交付檔。
- P11、P16、P21 的原生散佈圖每個 series 明設 `smooth=false`，將原資料點以斜線／水平線連接，移除造成占用超出資料點的平滑插值。
- contact 折線、完整 pred、所有時間／占用數值、文字與講者備註保持不變；未修改演算法或執行實驗。
- 核對：排除重建識別碼後，32 頁 slide／notes XML 相同；chart 指向不變。3 張圖的 8 個 series 僅新增 smooth=0，其他 chart XML 不變。32 頁最終檔渲染與預覽一致；套件、字型、幾何檢查通過。原生 PowerPoint 未驗證。

## v1.2：同步目的地檢查、完整 Commit 與最新驗證

- 方法依據改為 `67db7a2` 的 `dtn_validation/dtn/ours.py`、`validate.py`；舊凍結定義及演算法程式未修改。逐步 Q 的數值仍沿用本例紀錄，另外以新版重算核對兩包。
- P11、P21 標題與備註說明提交 F 及來源／中繼／目的地占用；圖中仍分別展示 B、C，不將未繪出的端點誤稱未提交。
- P22、P27、P30、P31、P32 移除已過時的 endpoint 缺口。P27、P28 在來源初始化與延伸時，對目的地 contact 先做 DestinationFilter 再 InsertLabels；P31 補齊起訖、release、期限及全部節點的驗證／提交。
- P3 保持 `(c,I,pred)` 三項，把 i 與 key 明標為編號／推導值，統一接收端為 v(c)，移除舊 namedtuple 快取說明。
- P5 加上速率欄，將「初始量」改為「傳輸量上限 r×時長」；P16 改為第 2 秒後即超限、第 3 秒達 8 MB。
- P22 明說第二包舊稿 12→5 秒來自取消 c7 配額，不能宣稱區間演算法效能改善；P12 提醒第二包重新編號。
- P1、P32 標示 store-and-forward／無獨立配額主模型待老師確認，並列出目的地收完即交付釋放的假設；P32 加入 SR-CGR 與隨機拓樸實驗。
- 驗證紀錄實際統計為 3,000 案例、5,961 查詢：2,250 同抵達、3,705 雙方無解、6 次較格點早；沒有較晚、漏解、多解及 replay 失敗。
- 本次沒有重跑全部 3,000 案例。針對 6 個較早案例重算並將窮舉格點從 1/16 秒細化至 1/48 秒，6 次均與區間結果相同，且排程驗證通過；此為測試證據，非一般證明。
- 本例兩包用新版搜尋、完整驗證、完整 Commit 和 1/4 秒格點重新核對，抵達仍為 8 與 5 秒；保留完整 Label、原版折線及分段直線 Buffer 圖。
- 暫維持 P1、P2、P14 隱藏，未擅自改放映設定。v1.1 與 1013 原檔均保留。
- 核對腳本：`src/presentations/verify_1103_v1_2_sources.py`；結果：`output/ppt_store_forward_20261103/v1_2_source_checks.json`。
- PPT 驗證：32 頁重新匯入／渲染與作者預覽一致，套件／字型／幾何檢查通過；3 張 chart XML 與 v1.1 相同，pred 展示保留。所有備註版本、DestinationFilter 兩個呼叫點、隱藏頁及原檔雜湊核對通過。原生 PowerPoint 未驗證。
