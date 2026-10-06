# Algorithm validation summary v01

## 結果
已完成 frozen v04 correctness audit：兩包逐步 trace、兩類 dominance 例子、extension/dominance 論證、completeness 盤點、獨立 exhaustive oracle、ON/OFF 比較與 calendar gap。沒有修改原始 v04 或加入 event-based/calendar 搜尋。

## Confirmed Correct（在明列假設下的論證）
- Extension 的 sender/receiver 分段占用檢查可維持可行前綴 invariant。
- 同 node/query 的等待橋接與 U componentwise comparison，支持 continuation-preserving dominance。
- Source、destination、propagation、quota 累計與提交均在手算與測試中核對。
- 這些結論依賴固定預約、無 copies、無額外路徑歷史限制及 snapshot 所列事件約定。

## Verified Only Under Finite Grid Model
- 14 個案例、15 次查詢：proposed 與 independent oracle 的可行性／最優 arrival 一致。
- Dominance ON/OFF 全部維持最優值；Case 05 入列 labels 從 7 減至 3；walkthrough 第二包從 7 減至 5。
- 18 個 unittest tests 通過；原始 test_results.txt 可重現。有限測例不是一般性正確證明。

## Not Yet Proven
- Continuous-time successor enumeration 與全域 completeness。
- 有限事件表示能否完整且有效率地壓縮所有必要 labels。
- 記憶體、runtime 或大網路的效能優勢；本次沒有執行這些比較。
- 同時 generation/delivery 的硬體事件語意尚未唯一決定；目前採保守峰值約定。

## Known Counterexamples
| ID | 被推翻的主張 | Witness | 是否為 frozen v04 同模型錯誤 |
|---|---|---|---|
| CE-EARLY | 早到即可刪晚到 | B@2 無法跨越既有占用，B@8 可繼續 | 否，v04 已有等待條件 |
| CE-GRID-01 | 整數資料即代表整數格點等於連續最優 | Δ=1 arrival=4；continuous witness=7/2 | 否，v04 保證明限 grid |
| CE-CALENDAR-01 | Quota 足夠即可排入連續傳輸 | 3 MB 剩餘分成三個 1 秒空檔，2 MB 包無法連續傳 | 否，calendar 不在當前模型 |

未發現 frozen v04 在本次同模型比較中的反例，**不代表不存在尚未測到的反例**。以上 witness 保留，沒有為讓結果好看而變更演算法。

## Missing Components
- Continuous-time exact extension / search 定義與證明。
- Contact transmission calendar，以及共用 radio（若要納入）的資料与約束。
- Production input validation、custody/retransmission copy 模型（若要納入）。
- 更廣輸入的測試與效能比較；必須在模型及正確性問題先確立後進行。

## 候選修正方案（未採用，需使用者確認）
1. 保留 finite-grid problem 作正式第一階段問題，清楚限定保證。
2. 研究依 buffer 線性交點與可行 departure intervals 生成候選時間；不可只列原始事件點。
3. 增加 Ω_c 與連續 free-window 檢查，另建同模型 oracle，再與 2024 方法公平比較。

## Ready for Advisor Discussion
可以展示：固定問題定義、逐步 label trace、前包如何改變後包路徑、pruning 的可取代性證明、測試結果以及尚未解決的兩個模型邊界。
不能宣稱：已完成連續時間最優路由、已等價解決 2024 完整排程問題、首次提出 Label Setting、或比既有方法快。

## 文件與證據索引
- [Current snapshot](current_algorithm_snapshot_v01.md)
- [完整 walkthrough](algorithm_walkthrough_v01.md)
- [兩種 dominance 例子](dominance_examples_v01.md)
- [Extension review](extension_correctness_review_v01.md)
- [Dominance review](dominance_correctness_review_v01.md)
- [Search completeness](search_completeness_review_v01.md)
- [Oracle 與 ON/OFF 表格](oracle_validation_v01.md)
- [全部測例輸入與可行排程](validation_case_catalog_v01.md)
- [Calendar gap](transmission_calendar_gap_v01.md)
- 原始數字／JSON／CSV：`output/validation/`
- 程式：`src/validation/`；測試：`tests/`
- 九張同拓樸 PNG：`figures/algorithm_walkthrough/`

## 檔案保全
原始演算法與歷史研究文件未改；SHA-256 清單與核對結果在 output/validation。新增驗證實作忠實保留 v04 定義；開發時曾修正報告輸出根目錄的程式路徑錯誤，非演算法或判別式修改。
