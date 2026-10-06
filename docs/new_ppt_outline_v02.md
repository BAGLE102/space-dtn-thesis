# New meeting PPT outline v02

> 已有後續範圍修正：finite buffer 為核心需求，M0 改作 baseline；正式製作須優先依 [ppt_storyline_revision_v03.md](ppt_storyline_revision_v03.md) 調整，不能直接使用本版 Algorithm 1 當主方法。

本文件是待確認的 storyline / slide content draft，**不是已生成的 PPTX**。依使用者本次指示，不含 Takeaway / Key Message / Core Insight 方框。正文建議 23 頁，附錄 3 頁；不沿用舊 27 頁數。若最後保留 finite buffer 為核心，須先重做演算法，再調整第 6–22 頁。

暫定報告定位：**Non-fragmented Bundle Routing in Space DTN: Model, Feasibility, and Research Gap**。目前研究成果是嚴謹的 baseline formulation 與研究缺口審查，尚不宣稱新演算法優於 CGR。

視覺基礎見 template_inspection_v01.md：保留 16:9、原 master、Times New Roman / 標楷體、右下校名 logo、底部頁碼。每頁 3 個短 bullet；複雜內容放 notes。

## 1. Research Scope

Slide Content:
- Space DTN 與已知 Contact Plan
- Non-fragmented bundle 的可行選路
- 本次確認 Model 與 Algorithm

Suggested Figure：精簡 source-contact-destination 示意，或直接使用模板標題版。

Speaker Notes：本次先確認問題與演算法正確性。範例是人工構造的 correctness case，尚無 performance claim；報告中的 proposed design 不代表已證明新穎性。

Source：[D] 本研究方向；本次使用者需求。

## 2. Space DTN and Contact Plan

Slide Content:
- 連線只在指定時間可用
- 節點儲存 bundle 等待轉送
- Contact 描述時間、速率與端點

Suggested Figure：兩跳 contact timeline，標 sender / receiver、start / end。

Speaker Notes：Paper A pp.6–10 提供 DTN 與 contact plan 背景。本文強調整包收到才轉送，不把 first-byte arrival 誤當下一跳可用時間。

Source：[A] pp.6–10；[D] 本文 store-and-forward 假設。

## 3. Graph Representation

Slide Content:
- Physical node：衛星或地面站
- Contact edge：一次有向通訊機會
- Contact-as-vertex graph 是另一種表示

Suggested Figure：同一 contact plan 的兩個簡單圖，左右明確標 graph type。

Speaker Notes：A 的 CGR 圖以 contact 為 vertex，但我們 M0 的 state 是 physical node 與 arrival。不同表示可以描述相同機會，不應混用 vertex 數、edges 數或 dominance 定義。

Source：[A] pp.10–12；[D] problem_formulation_v02.md。

## 4. Bundle Size and Feasibility

Slide Content:
- 傳輸時間由 S/r 決定
- Window 必須容納完整傳輸
- Residual volume 必須至少為 S

Suggested Figure：S=4 MB 與 R=3 MB 的 bottleneck contact，附 transmission interval。

Speaker Notes：這頁說明為何需要檢查大小，不宣稱既有標準完全沒有這些機制。容量不足與傳輸剩餘時間不足是不同拒絕原因。

Source：[D] small_topology_v02.md。

## 5. Existing Capacity Handling

Slide Content:
- SABR 已定義 route volume 檢查
- 禁止 fragmentation 時須容納整包
- 研究差異需要更精確界定

Suggested Figure：一個簡短「既有機制 / 本次待證差異」對照表。

Speaker Notes：SABR §3.2.6.9(g) 是直接影響 contribution 的證據。不可把只看時間的 naive routing 當成所有 CGR；這次不先聲稱首次容量感知。

Source：外部 S，https://ccsds.org/Pubs/734x3b1.pdf ，§3.2.6.9(g)。

## 6. Problem Definition and Assumptions

Slide Content:
- 單 bundle、單路徑、固定資源快照
- 一個 contact 內連續完整傳送
- M0 假設 buffer 足夠、無外部占時

Suggested Figure：Contact / Bundle 的精簡 notation table。

Speaker Notes：這是為先建立正確基礎模型所提出的 scope，不等於默認刪除碩論原本的 finite buffer 需求。若 buffer 必須保留，本版只能當 baseline。

Source：[D] problem_formulation_v02.md。

## 7. Research Objective

Slide Content:
- 求最早整包抵達目的地的 route
- 每 hop 通過時間與容量檢查
- 無可行 route 時明確回報

Suggested Figure：arg min A(P) 與 feasible set 定義，另標 o=d 空路徑。

Speaker Notes：固定 generation time 下 earliest arrival 和最小 delivery duration 相同，但不是最少 hops。Earliest arrival then cost 的 variant 放附錄，不混入此版本。

Source：[D] problem_formulation_v02.md。

## 8. Related Work A

Slide Content:
- 多 flow 的集中 routing / scheduling
- 時槽 LP 納入容量、buffer 與 deadline
- 流量可分配，與整包模型不同

Suggested Figure：A 的 x_l^f 與本次單 bundle contact sequence 對照。

Speaker Notes：A 的目標是送達資料量/比例加權時間。它已研究 capacity 和 buffer，但連續 flow variables 沒有直接保證每 bundle 不分割、逐跳整包完成後轉傳。

Source：[A] pp.19–25；[C] model comparison。

## 9. Related Work B

Slide Content:
- SVC multicast 的滿意度最佳化
- 子問題 A：延遲受限最小成本路徑
- Label Setting 用於 cost / delay 取捨

Suggested Figure：全局 LR 與其 path subproblem 的簡單包含關係。

Speaker Notes：B 的容量是 Mbps、delay 是可加 link delay，與 DTN contact 的 MB volume 不同。B 引用既有 Label Setting 工具；本文未完整列出內部 label schema，後續 REF / dominance 是模型推導。

Source：[B] PDF pp.25–30（正文 pp.15–20）；[C] 推導。

## 10. Method Mapping

Slide Content:
- 保留 DTN 的時序與傳輸語意
- 使用 state、extension、dominance 框架
- M0 不需搬入 LR 或 multicast tree

Suggested Figure：A / B / Proposed 三欄精簡 mapping。

Speaker Notes：adaptation 的重點是證明哪些資訊會影響未來可行性，並非把兩份 pseudo-code 接起來。每條 R≥S 是局部條件，不自動造成一般多資源 SPPRC。

Source：[A/B/C/D] paper_method_mapping_v01.md。

## 11. Transmission and Arrival

Slide Content:
- s=max(a,start)
- finish=s+S/r≤end
- arrival=finish+δ

Suggested Figure：同一 contact 的 wait / transmit / propagate timeline。

Speaker Notes：contact end 在本模型是 sender serialization 的截止，不要求最後一個 bit 已到 receiver。若 residual 表示真實預約，s 需由 calendar 的 NextFree 求得。

Source：[D] problem_formulation_v02.md、extension_rule_v02.md。

## 12. Label Definition

Slide Content:
- 核心 state：(node,arrival)
- Predecessor 與 contact 用於重建
- 固定 S、R 保存在 query context

Suggested Figure：簡潔 label table，將 metadata 與 state 分列。

Speaker Notes：不用把整條 path 與所有時刻陣列複製到每個 label。M0 不含 cost objective，因此沒有理由加入 accumulated cost 欄位。

Source：[D] label_design_v02.md。

## 13. Label Extension

Slide Content:
- 檢查 sender 與目前 node 銜接
- 計算等待、傳輸與 window
- 容量通過後建立 arrival label

Suggested Figure：8-step extension 的精簡流程圖。

Speaker Notes：連接方向是上一跳 receiver 等於下一跳 sender。候選 extension 不代表已發送或已預約，不會直接扣全域 residual capacity。

Source：[D] extension_rule_v02.md。

## 14. Dominance and Its Assumptions

Slide Content:
- M0：同 node 早到可支配晚到
- 免費等待讓早到模擬晚到後續
- Cost 或有限 buffer 須另作分析

Suggested Figure：同 node 的早/晚 arrival 與共同後續 contact。

Speaker Notes：必須講清楚 future-feasibility inclusion 的理由，而非只寫 earlier dominates later。M0-Lex 不可直接用 prefix lex order；buffer bridge 與 delayed departure 的反例放附錄。

Source：[C/D] dominance_rule_v02.md。

## 15. Algorithm Pseudocode

Slide Content:
- ExtractMin 取最早有效 label
- Extend 並保留每 node 最早 arrival
- Destination 被取出後重建路徑

Suggested Figure：Algorithm 1 的短版 pseudocode；完整版本放附錄/文件。

Speaker Notes：不要在 destination label 第一次生成就停。這是 capacity-filtered time-dependent Dijkstra 的 label-setting 表達；不聲稱是新的演算法家族。

Source：[D] algorithm_pseudocode_v02.md。

## 16. Small Contact Plan

Slide Content:
- 五節點、八個 contacts
- Bundle size=4 MB，generation=0 s
- 包含容量失敗與時間失敗的分支

Suggested Figure：Figure 1 與精簡 contact table。

Speaker Notes：所有數值是為驗證流程而設計。共同 δ=1 秒；R 是 M0 quota。完整輸入與所有路徑枚舉列在 small_topology 文件。

Source：[D] small_topology_v02.md。

## 17. Initialization and First Expansion

Slide Content:
- 初始化 A0
- 產生 B3、C5、D6
- Queue 按 arrival 排序

Suggested Figure：Figure 2 / Figure 3，同 topology 依步驟顯示。

Speaker Notes：c1 在 [0,2) 發送，3 秒到 B；c3 在 [0,4) 發送，5 秒到 C；c5 等到 1 秒，5 秒發送完，6 秒到 D。label 顯示的是整包 arrival。

Source：[D] small_topology_v02.md steps 0–3。

## 18. Infeasible Contact Rejection

Slide Content:
- c2：R=3 MB<4 MB
- c8：finish=5 s>end=4 s
- 保留 C5 與 D6

Suggested Figure：Figure 4，兩條被拒 contact 標明不同原因。

Speaker Notes：若只看時間，A→B→E 會在 6 秒到達，但 quota 不足。c8 則是 capacity 足夠但 window 不足，讓兩項判斷各有示例。

Source：[D] small_topology_v02.md steps 4–5。

## 19. Label Generation and Dominance

Slide Content:
- C5 經 c4 產生 E9
- D6 支配候選 D8
- E9 支配候選 E11

Suggested Figure：Figure 5 / Figure 6，失效 labels 用虛線，edge 不刪除。

Speaker Notes：D8 在時間與容量上本來可行，只是未來不會比 D6 更好。prune 的對象是候選 label，不是宣布整條 contact 永久不可用。

Source：[D] small_topology_v02.md steps 6–8。

## 20. Destination and Route Reconstruction

Slide Content:
- 取出有效目的地 label E9
- 最終 route：A→C→E
- 完整 bundle 在 9 s 抵達

Suggested Figure：Figure 7 / Figure 8，附兩跳 transmission intervals。

Speaker Notes：c3 用 [0,4)，C 等待 [5,6)，c4 用 [6,8)，8 秒最後 bit 離開 C、9 秒抵達 E。獨立枚舉的可行 route arrivals 是 9、11、11，與手算相同；這不是效能改善實驗。

Source：[D] small_topology_v02.md。

## 21. Correctness and Complexity

Slide Content:
- Extension 保留每跳可行性
- FIFO 支持單 label / node
- Indexed heap：O((n+m)log n)

Suggested Figure：feasibility invariant、dominance、ExtractMin 正確性的三列短表。

Speaker Notes：n 是 physical nodes，m 是 contacts；不是 contact graph 的 transition 數。若增加 cost 保留多 labels，複雜度依生成 label 數成長，不能繼續用這個 bound。

Source：[C/D] algorithm_design_v02.md。

## 22. Validation and Experiment Plan

Slide Content:
- 小型 oracle 核對可行性與最優值
- 比較相同模型的 Dijkstra / SABR baseline
- 報告 runtime、解品質與 label 數

Suggested Figure：baseline 與 metrics 對照表，不放虛構曲線。

Speaker Notes：M0 與同模型 Dijkstra 應同最優；只看時間的 routing 屬於 ablation。SABR 需固定版本、資訊與 fragmentation 設定。未有原始 data 前不建立 Preliminary Results 頁。

Source：[D] reviewer_assessment_v02.md。

## 23. Research Limitations and Next Steps

Slide Content:
- M0 的新穎性仍不足
- 確認 buffer 與 reservation 語意
- 決定 baseline 或擴充模型的主線

Suggested Figure：M0 baseline / finite buffer / 多 bundle 三項 scope 對照。

Speaker Notes：問題有價值不等於目前方法已有充分 contribution。優先確認核心研究邊界，再決定需要的 state、extension、dominance 與實驗；不要先完成漂亮簡報再掩蓋模型缺口。

Source：[C/D/E] reviewer_assessment_v02.md。

## Appendix A. Lexicographic Objective

Slide Content:
- 最終按 (arrival,cost) 選解
- 中間節點保留 Pareto labels
- 等待可能讓不同 arrival 合流

Suggested Figure：dominance_rule_v02.md 的 C1 / C2 反例。

Speaker Notes：(4,9) 與 (6,1) 經 10 秒開始的共同 contact，都在 11 秒到達；早到昂貴的 prefix 不能刪除晚到便宜者。cost 必須先有研究用途，不能為了用 multi-label 人工添加。

Source：[C/D] 本次推導。

## Appendix B. Finite Buffer Counterexample

Slide Content:
- 早到可能遇到 buffer 不可用區間
- 延後前一跳發送可恢復可行性
- 必須重設 extension 與 dominance

Suggested Figure：problem_formulation_v02.md 的 A→B→E 時線與 B buffer calendar。

Speaker Notes：A→B 若最早發送會在 1 秒抵達，B 在 [1,4) 沒空間；3 秒才發送、4 秒到達則可以等到 5 秒。這說明不只是加 buffer if 或改 same-contact pruning。

Source：[D] 本次構造反例。

## Appendix C. Full Notation and References

Slide Content:
- Contact / bundle / label 的一致符號
- A、B 與外部標準分開列示
- Proposed / derived / uncertain 明確標記

Suggested Figure：必要 notation table；文獻太長可在正式階段拆為兩頁。

Speaker Notes：Paper A 頁碼使用 PDF 實際頁，Paper B 同時給 PDF 與正文頁。完整公式與 pseudo-code 由同一組 Markdown 文件產生，避免再次出現多版本衝突。

Source：paper_method_mapping_v01.md。
