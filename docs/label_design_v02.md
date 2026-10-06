# Label design v02

[D] [Proposed Design] 基於 problem_formulation_v02.md 的 M0，核心 state 為 **(v,a)**。

Label 以 L=(v,a,pred,c_in,s_in) 表示，後三欄是重建 metadata，不參與 dominance。source label 的 c_in、s_in、pred 為 null。

| Label Field | Meaning | Necessary? | Reason |
|---|---|---|---|
| v | 整包已抵達的實體 node | 是 | 決定 outgoing contacts；不同 incoming contact 的同 node labels 可比較 |
| a | last-byte arrival time | 是 | 決定等待、window feasibility 與 objective |
| pred | 前驅 label reference | 輸出路徑需要 | 指向穩定的 label，不是會變更內容的候選 record |
| c_in | 抵達 v 使用的 contact ID | 輸出路徑需要 | 同端點可有平行 contacts，僅存 predecessor node 不足 |
| s_in | incoming contact 的 transmission start | 可省略但建議留 | 可由 pred.a 及 c_in 重算；保留方便驗證排程 |
| whole path P | 完整 contact sequence | 否 | 由 pred chain 重建，避免每個 label 複製路徑 |
| all start times | 全路徑排程陣列 | 否 | 由各 label 的 s_in 重建 |
| S | bundle size | 否 | 本次 query 固定，在 query context 保存 |
| R vector | 所有 contact residual capacity | 否 | 固定 global snapshot，不是每個候選真的預約後的剩餘量 |
| bottleneck R | 路徑最小 residual capacity | 否 | 已逐邊檢查≥S，對 M0 的未來可行性沒有額外資訊 |
| accumulated cost z | Σκ_c | M0 否；M0-Lex 是 | 只有目標/限制確實使用 cost 才需要 |
| settled / active | queue bookkeeping | 實作需要 | 不屬於物理 resource，可在 node record 或 queue 保存 |
| visited set | 已訪問 nodes/contacts | M0 否 | 正時間與免費等待下移除 cycle 不會變差；不額外要求 elementary path |
| buffer interval / resource history | 可等待區間或候選造成的占用 | M0 否；M1 待定 | 一旦影響 future feasibility，(v,a) 可能不足 |

## 為何不用 last contact 作為唯一 state

[C] A 的 CGR background 使用 contact-as-vertex，不代表任何 DTN 演算法都必須用 contact 作 state。M0 下一步只需目前 receiver v、arrival a、固定 C/R。因此同 node 的早到 label 能取代經由不同 contacts 抵達的晚到 label。只比較 same-contact 不一定錯，但會少做可安全執行的 pruning。

若實作需要某個 incoming radio state、path restrictions 或歷史 reservation，必須把它納入等價 state 的定義；改成「同 contact」並不自動解決所有歷史依賴。

## Paper B 與來源邊界

[B] B 的 PDF p.27 明列 delay-constrained minimum-cost path，引用 Label Setting 工具。
[C] 可由其子問題重建 time/cost 的 label；B 本文沒有完整 label schema，故不能把本表說成 B 原文。
[D] M0-Lex 使用 L=(v,a,z,pred,c_in,s_in)。同 node 要保留 time/cost trade-off 的 non-dominated labels，不能只存一個字典序最小 prefix。詳見 dominance_rule_v02.md。
