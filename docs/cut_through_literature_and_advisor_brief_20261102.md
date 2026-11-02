# Cut-through 文獻初查與 11 月 4 日老師討論稿

日期：2026-11-02。性質：初步文獻查證與研究決策稿，非完整 systematic review，非演算法定稿。

## 1. 本次確認的安排

- 下次老師討論：2026-11-04。
- 口試暫定：2027 年 8 月；確切日期未定。
- 使用者希望兩種轉送方法共存。先並列保留，不把任一種結果當成另一種的驗證。
- 本稿不修改演算法、不新增實驗，不覆蓋既有 handoff 或凍結定義。

## 2. 兩個版本先分清楚

以下名稱只是本稿的識別名稱。

| 版本 | 中繼節點何時可以起送？ | 現有候選與限制 |
|---|---|---|
| G：一般部分接收起送 | 可在第一個 byte 抵達後、整包收完前，選擇符合資料因果及資源限制的時間起送；也可收完才送 | v2 handoff 的區間 Label；TRACK 尚未實作，RELAX 曾產生 2 個自我重疊結果 |
| D：立即轉或收完才轉 | 第一個 byte 抵達時立即起送，或等整包收完才起送；不允許收到一半才開始 | `direct_or_store_audit.py` 原型；既有 2,000 個格點小例無不一致，仍不是正確性證明 |

「兩者共存」目前只確認並列保留。是否要做成單一演算法中的可選策略，或兩個獨立求解器，尚未決定。

上述時間忽略 header 處理與計算延遲，是候選理想模型；實際節點能否做到，另行查證。

### 最小區別例子（手算，未執行程式）

- A→B：contact [0,5]，B→C：[2,12]。
- Bundle 大小 5，兩跳速率均為 1，傳播延遲均為 0，buffer 足夠，沒有其他占用。
- A→B 的窗口剛好只夠傳整包，因此 A 必須在 0 起送；B 在 0 開始接收、5 收完整包。
- G 允許 B 在 2 起送，C 在 7 收完整包。
- D 因 B→C 在 0 未開啟，只能等 5 收完後起送，C 在 10 收完。

這個例子區分兩種允許的排程，不能證明任何候選演算法正確，也不能代表實驗收益。

注意：若把 A→B 改成 [0,10]，D 也可能把 A 的起送時間延到 2，讓 B 在第一個 byte 到達時立刻轉送，於 7 到 C。因此不能用那個寬窗口例子直接宣稱 G 的最優解必然比 D 快；必須同時考慮前一跳能否改時。

## 3. 已查核的一手來源

### 3.1 Alhajj／Corlay：不能只說「她預處理，我當下判斷」

**Tania Alhajj and Vincent Corlay, _Improved Contact Graph Routing in Delay Tolerant Networks with Capacity and Buffer Constraints_, arXiv:2410.15546v3。**

[原文](https://arxiv.org/html/2410.15546v3)

- 定位：§II-A 的 Edge、§III-C、§IV-A／B、Introduction 的 Main contributions。
- 原文規定下一跳不得早於上一跳整包抵達；其方法同時包含搜尋前 splitting 與搜尋中的 edge pruning。
- 因此，「搜尋當下判定」本身不足以確立差異；G／D 的轉送時機則與其定義不同。
- 尚未執行其演算法，也未完成同模型實作對照。不能宣稱已超越它，亦不能由這次閱讀判定其證明錯誤。

### 3.2 SPICE：DTN 部分資料立即轉送已有先例

**European Commission CORDIS, _Space Internetworking Center (SPICE)_, project 264226, final reporting。**

[官方報告](https://cordis.europa.eu/project/id/264226/reporting/es)（本次可讀頁面的技術正文為英文。）

- 定位：搜尋 `DtnAgent`、`cut-through strategy`、`placeholders`。
- ns-2 模擬器將 bundle 的已收到 packetload 立即交給下游；另說明可改為整包接收後轉送。
- 但其部分接收 bundle 先保留整包大小，並有 custody／重傳的資料保留規則；不同於你的逐 byte 收入減送出占用模型。
- 能支持「DTN 曾研究部分資料轉送」，不能支持你的 buffer 公式、排程最優性或 BPv7 實作相容性。

### 3.3 RFC 9171：不能由 implementation matter 推出已支援 cut-through

**Burleigh, Fall and Birrane, _Bundle Protocol Version 7_, RFC 9171, 2022。**

[§5.3](https://www.rfc-editor.org/rfc/rfc9171.html#section-5.3)、[§5.6](https://www.rfc-editor.org/rfc/rfc9171.html#section-5.6)

- Dispatch 在 reception Step 4 完成後開始；reception 包含 CRC 與 extension block 處理。
- §5.4 的發送時機由實作決定，不等於明文授權「未收完整包就轉送」。
- 判讀：尚不能聲稱 G／D 是標準 BPA 已保證的能力；也不能僅憑此判定所有特殊實作都不可能。
- 後續須查明 header 可用時間、完整性／安全檢查、錯誤後撤回或重傳、傳完後何時釋放資料。

### 3.4 NASA HDTN：「cut-through」一詞可能指不同事情

**Nathan Drzadinski, Stephanie Booth, Blake LaFuente and Daniel Raible, _Space Networking Implementation for Lunar Operations_, Small Satellite Conference, 2023。**

[NASA 原文 PDF](https://ntrs.nasa.gov/api/citations/20230009059/downloads/SmallSat_Conference_Paper%20V2.pdf)

- 定位：第 1 頁 Introduction。
- 該文的 cut-through setup 繞過 Storage、Scheduler、Router、CGR Client 與 Contact Plan，以避開儲存瓶頸。
- 這段文字不足以證明「同一 bundle 還沒收完就送」，更不是 contact-plan 最早抵達排程演算法。
- 要證實逐 byte 轉送，仍需追到特定版本的接收／發送 callback 或作者實驗說明。本次未做該程式查核。

## 4. 目前能說與不能說的研究定位

**候選研究問題：** 在既有 reservations 固定、bundle 不做 BP fragmentation、每跳連續傳送、允許指定 cut-through 能力的模型下，如何找到符合 contact 時間、資料因果與逐時 buffer 限制的最早整包抵達排程？

這是待老師確認的定位，不是已確認的新貢獻。

| 說法 | 目前狀態 |
|---|---|
| Contact splitting 是新方法 | 不成立；已有直接相關文獻 |
| DTN 邊收邊轉本身是新概念 | 不成立；已有模擬先例 |
| 任意部分接收起送下，前後兩跳會共同決定占用與可行性 | 候選模型中的結構，可由公式說明；實務適用性待確認 |
| 所有 cut-through 演算法都必須使用區間 Label | 未證，不應宣稱；需要比較其他狀態表示與求解法 |
| 區間 Label 已完整解決不允許自我重疊的模型 | 未成立；TRACK 未實作且有失敗案例 |
| 已證明與既有文獻不重疊 | 尚未；本次僅初查四個來源，並非完整新穎性檢索 |

建議把「區間 Label」當候選解法，把「解哪個問題、比既有解法多處理什麼」當優先決策。

## 5. 既有測試證據如何解讀

來源：`docs/interval_label_validation_20261102.md` 及對應已保存 JSON；本次只查閱，沒有重跑。

- 1,864 次查詢、1,240 次有解；已報告格點 oracle 對照未見較晚或漏解。
- **RELAX 有 2 個自我重疊結果**，不符合「同節點造訪不可重疊」的目標模型；不能計入該模型的成功結果。
- 開區間旗標為 0，來源／目的地沒有背景占用，全部節點可邊收邊轉；不能外推這些未測條件。
- 格點對照與候選共用部分占用函式，也未真正檢驗到非格點優勢。

因此，先保存並處理失敗案例、建立更獨立的 validator，暫停研究級效能排名。即使最後排程驗證通過，也不能只靠此證明「最早抵達」。

## 6. Baseline 要分開回答兩件事

| 比較目的 | 做法 | 可以得出的結論 |
|---|---|---|
| 搜尋方法是否正確／有效率 | 同一 G 或 D 模型，比獨立小例 oracle；也可比較相同模型的其他求解器 | 可行性、答案差距、漏解、時間與記憶體 |
| Cut-through 能力有什麼效果 | 固定其他資源條件，G、D 與 store-and-forward 分開求解 | 允許排程改變帶來的收益；不能單歸因於搜尋技巧 |
| 與 Alhajj／Corlay 對照 | 先忠實實作原模型並核對，再限定共同模型，或清楚標記模型不同 | 原方法重現、共同假設下差異；尚未執行 |

共同控制：contact plan、bundle 大小與順序、deadline、背景 reservations、buffer 記帳／釋放、節點收送能力、來源／目的地、重訪規則、時間精度及 timeout。比較多包時，每個策略可產生自己的後續 reservations，另以固定 snapshot 單包比較隔離搜尋效果。

先收集可行性違規、oracle 差距與失敗原因，再談平均延遲、交付率、CPU、Label／區間數。超時應記 UNKNOWN，不能算已證無解。

## 7. 11 月 4 日請老師決定的五件事

1. **主線：** G 與 D 是否都保留？哪個當主模型，哪個當特例或對照？上述問題與候選解法是否足以繼續發展？
2. **系統依據：** 可否先研究有明確能力假設的 cut-through 排程，而不宣稱標準 BPv7 已直接支援？完整性及重傳保留要做到哪一層？
3. **節點能力：** 是否所有節點都可同時收送？若只有部分節點，能力是否作為輸入？
4. **容量模型：** 能否主模型只用速率、時間窗與已預約傳送時段，不另加獨立 aggregate quota？
5. **Buffer Detour：** 主問題要允許重訪但禁止自我重疊嗎？若要，先補 TRACK；若不要，限制與可能漏掉的路徑需明寫。

### 可直接口頭報告

「我現在把一般部分接收起送，以及立即轉或整包收完才轉，分成兩個候選版本。文獻已有 contact splitting 和 DTN cut-through，所以不把這兩個概念本身當新貢獻。我想確認是否以指定節點能力、固定既有預約與有限 buffer 下的最早抵達排程作為主問題。區間版本已有小例測試，但有兩個自我重疊案例未解決，所以目前不宣稱完整正確，也尚未和 Alhajj／Corlay 完成實驗對照。」

## 8. 時程建議（建議，並非已確認承諾）

- **11/2–11/3：** 整理本稿、兩版本時間圖與 2 個失敗案例；檢查既有簡報字型與版面。
- **11/4：** 帶五項決策問老師，記錄同意的模型與貢獻邊界。
- **主線確認後：** 先解反例與獨立驗證，再補證明／複雜度、baseline、研究級實驗。
- **2027/8 口試前：** 保留論文撰寫、老師修改、口試申請與行政時程；實際校方期限待確認，不能從口試月份自行推定。

## 9. 查核範圍與檔案狀態

- 查閱使用者的中英文 v2 handoff、兩份 audit 摘要、既有結果與上述官方／作者來源。
- 沒有執行新實驗、驗證標準相容性、實作 TRACK、跑原論文 baseline，亦未以 PowerPoint 檢查簡報。
- 既有 audit 文件含互相衝突的同日模型註記；本次以使用者最新的「兩個方法共存」為準，保留原檔差異供追溯。
- 本稿不代表完整 Related Work；接下來仍須以明確問題條件搜尋 cut-through／wormhole／streaming 的時間相依路由、有限 buffer 排程與相關最優演算法。
