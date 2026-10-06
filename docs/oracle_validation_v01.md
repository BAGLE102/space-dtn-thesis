# Independent oracle validation v01

## Oracle independence

`exhaustive_oracle.py` 僅 import fractions、itertools、collections、copy。AST 測試確認沒有 import proposed search / extension / dominance / occupancy / commit。共用輸入資料格式，但不共用可行性 helper。

Oracle 先列出所有拓樸 walks（允許重訪）至可證明的正時間 hop bound；再對每條 route 列舉各 contact start slots 的 Cartesian product。每個完整 schedule 才重算 timing、per-contact 用量及全路徑 inventory，沒有 dominance、prefix buffer pruning 或 incumbent branch-and-bound。

Proposed 使用局部收發曲線；oracle 使用完整 schedule 的 per-visit inventory 公式，然後在全部事件端點求總占用。兩者都使用 Fraction 與相同事件峰值模型，以免把語意不同混成演算法差異。

## 同模型正確性比較

| Case | Proposed Feasible? | Oracle Feasible? | Proposed Arrival | Oracle Arrival | Match |
| --- | --- | --- | --- | --- | --- |
| 01_unique/bundle | True | True | 3 | 3 | True |
| 02_multiple/bundle | True | True | 3 | 3 | True |
| 03_no_route/bundle | False | False | — | — | True |
| 04_late_label/bundle | True | True | 10 | 10 | True |
| 05_prunable/bundle | True | True | 5 | 5 | True |
| 06_sequential_walkthrough/bundle1 | True | True | 8 | 8 | True |
| 06_sequential_walkthrough/bundle2 | True | True | 12 | 12 | True |
| 07_finish_at_end_nonzero_delay/bundle | True | True | 3 | 3 | True |
| 08_receive_overflow/bundle | False | False | — | — | True |
| 09_sender_drain_overflow/bundle | False | False | — | — | True |
| 10_source_equals_destination/bundle | True | True | 0 | 0 | True |
| 11_source_full/bundle | False | False | — | — | True |
| 12_cycle_needed/bundle | True | True | 6 | 6 | True |
| 13_quota_reuse/bundle | False | False | — | — | True |
| 14_destination_event_peak/bundle | False | False | — | — | True |

案例 01–06 對應使用者要求的六類；07–14 增加 boundary、δ、接收／發送超量、source=destination、source滿、必要循環、重複 quota、交付瞬間峰值。

## 每個案例的完整輸入與證據

人工重算用的逐案例 contact / bundle / buffer 表，見 [validation_case_catalog_v01.md](validation_case_catalog_v01.md)。

所有 contacts、bundles、buffers、O 曲線、每次 snapshot、proposed trace、oracle feasible schedules、拒絕原因及 witness，均保存在 `output/validation/oracle_results.json`。手工定義來源是 `validation_cases.py`。

| Case / bundle | Topological walks | Complete schedules | Feasible schedules | Expected arrival |
| --- | --- | --- | --- | --- |
| 01_unique/bundle | 1 | 1 | 1 | 3 |
| 02_multiple/bundle | 2 | 2 | 2 | 3 |
| 03_no_route/bundle | 1 | 1 | 0 | None |
| 04_late_label/bundle | 1 | 7 | 2 | 10 |
| 05_prunable/bundle | 1 | 3 | 3 | 5 |
| 06_sequential_walkthrough/bundle1 | 2 | 2 | 2 | 8 |
| 06_sequential_walkthrough/bundle2 | 6 | 8 | 2 | 12 |
| 07_finish_at_end_nonzero_delay/bundle | 1 | 1 | 1 | 3 |
| 08_receive_overflow/bundle | 1 | 1 | 0 | None |
| 09_sender_drain_overflow/bundle | 1 | 1 | 0 | None |
| 10_source_equals_destination/bundle | 1 | 1 | 1 | 0 |
| 11_source_full/bundle | 1 | 1 | 0 | None |
| 12_cycle_needed/bundle | 6 | 6 | 1 | 6 |
| 13_quota_reuse/bundle | 6 | 55986 | 0 | None |
| 14_destination_event_peak/bundle | 1 | 1 | 0 | None |

## Dominance OFF / ON（相同 query snapshot）

Labels 欄位定義為 enqueued（含來源）；另列 created（包含立即被 pruning 的候選）、expanded，避免只選有利數字。比較最優值，不強制最優路徑唯一；是否同一路徑另外記錄。

| Case | Arrival OFF | Arrival ON | Labels OFF | Labels ON | Created OFF/ON | Expanded OFF/ON | Same optimal value? | Same route? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_unique/bundle | 3 | 3 | 3 | 3 | 3/3 | 2/2 | True | True |
| 02_multiple/bundle | 3 | 3 | 4 | 4 | 4/4 | 2/2 | True | True |
| 03_no_route/bundle | None | None | 2 | 2 | 2/2 | 2/2 | True | True |
| 04_late_label/bundle | 10 | 10 | 6 | 4 | 6/5 | 4/3 | True | True |
| 05_prunable/bundle | 5 | 5 | 7 | 3 | 7/5 | 4/2 | True | True |
| 06_sequential_walkthrough/bundle1 | 8 | 8 | 4 | 4 | 4/4 | 2/2 | True | True |
| 06_sequential_walkthrough/bundle2 | 12 | 12 | 7 | 5 | 7/6 | 5/4 | True | True |
| 07_finish_at_end_nonzero_delay/bundle | 3 | 3 | 2 | 2 | 2/2 | 1/1 | True | True |
| 08_receive_overflow/bundle | None | None | 1 | 1 | 1/1 | 1/1 | True | True |
| 09_sender_drain_overflow/bundle | None | None | 1 | 1 | 1/1 | 1/1 | True | True |
| 10_source_equals_destination/bundle | 0 | 0 | 1 | 1 | 1/1 | 0/0 | True | True |
| 11_source_full/bundle | None | None | 0 | 0 | 0/0 | 0/0 | True | True |
| 12_cycle_needed/bundle | 6 | 6 | 4 | 4 | 4/4 | 3/3 | True | True |
| 13_quota_reuse/bundle | None | None | 3 | 3 | 3/3 | 3/3 | True | True |
| 14_destination_event_peak/bundle | None | None | 1 | 1 | 1/1 | 1/1 | True | True |

這是 correctness/pruning 觀察，不是 runtime、memory 或大規模 performance benchmark。Sequential queries 使用同一已接受 canonical schedule 建構下一快照，oracle 以獨立 commit 重建並核對；不讓 tie 選不同路徑造成第二包輸入不同。

## Sequential reservation 的因果對照

相同第二包與 contact plan，未提交第一包時選 c3→c2、arrival=8；提交後選 c4→c5、arrival=12。測試亦核對 B@2.5 的占用=2、B@4=4、B@8=0，與未選 c5 在第一包後 quota 仍為 4。

## 模型邊界 witness

`counterexample_grid_continuous.json` 保存同一網路的 Δ=1 與 Δ=1/2 結果，分別 4、7/2。每種格點上 proposed=oracle；連續時間 witness 與最優下界推導見 search_completeness_review_v01.md。這不是將演算法改成 event-based。

## 停止條件

目前 gate=PASS_FINITE_CASES；未發現同模型 oracle mismatch。程式若發現 mismatch 會保存 counterexample JSON、將 gate 設 STOP 並拒絕後續 dominance comparison；不會自動修演算法。

## 限制

14 個人工案例／15 次查詢與 18 項測試，不是任意規模或所有輸入的機械證明。輸入驗證也不是 production-grade；負 buffer、無效既有 O、radio/custody 的實務驗證尚不完整。

## 重現指令

於專案根目錄，以可用 Python 執行：

```text
python -m src.validation.compare_oracle
python -m src.validation.compare_dominance
python -m unittest discover -s tests -v
python -m src.validation.build_report
python -m src.validation.render_figures
```

首次產生 walkthrough 使用 `python -m src.validation.build_walkthrough`；重新執行時核對既有 freeze manifest，不覆寫凍結來源。Python 實際路徑與執行記錄見 output/validation/reproducibility.json。