# Paper method mapping v01

狀態：第一階段研究審查草稿，2026-10-04。沒有建立或修改 PPTX。

## 來源與標記

- [A] Paper A：黃文龍，*延遲容忍衛星網路之路由規劃與封包發送排程 / Routing and scheduling for delay tolerant communication in satellite networks*，國立中正大學碩士論文，2026 年 7 月。全文 46 PDF 頁；下文 A 頁碼均為 PDF 頁碼，也等於正文印刷頁碼。
- [B] Paper B：吳峻至（封面英文 JYUN-JHIH WU），*基於拉格朗日鬆弛之可伸縮性視訊編碼視訊會議的路由演算法 / A Lagrangian Relaxation based routing algorithm for SVC Video Conferencing*，國立中正大學碩士論文，2026 年 7 月。全文 63 PDF 頁；正文印刷頁碼 = PDF 頁碼 − 10。
- [C] Derived / adapted：從模型或既有框架推導，不能稱為作者直接提出。
- [D] [Proposed Design]：本次提出供確認的設計，不等同已證明具文獻新穎性。
- [E] [Need Verification]：資料不足、實作未提供或研究範圍尚未決定。
- 外部 S：CCSDS，*Schedule-Aware Bundle Routing*，734.3-B-1，July 2019，https://ccsds.org/Pubs/734x3b1.pdf 。核對 §3.2.6.2–.10、§3.2.8.1。
- 外部 H：Adrian Haarbach，*Shortest Paths with Resource Constraints*，2015 教學工具，https://www.adrian-haarbach.de/idp-graph-algorithms/implementation/spp-rc-label-setting/index_en.html 。這是 B 的 reference [11]，也是舊 PPT 第 24 頁的來源，不是另一篇已提供的研究論文。
- 外部 G：Boost Graph Library，*Resource-Constrained Shortest Paths*，https://www.boost.org/doc/libs/1_61_0/libs/graph/doc/r_c_shortest_paths.html 。用於核對 REF / dominance 的框架語意。

外部來源於 2026-10-04 查閱。PDF 文字抽取部分中文字有字形映射錯誤；核心模型公式、B 的 SPPRC 段落另以頁面影像核對。論文數據均為作者報告，未重新執行其實驗。

## Paper A

**一句話摘要：[A]** 在已知 contact plan 下，集中規劃多筆 flow 的路由與資料量排程，考慮 contact capacity、buffer、各別 release time 與 deadline。

**問題與動機：[A]** 多 flow 共用 contact / buffer，獨立選路可能造成資源衝突；既有特定模型要求相同 deadline，因此 A 希望支援不同時間需求並全域規劃。見 pp.12–14、19。

**方法：[A]** 先按 contact 起訖事件切時槽，實驗中棄用 ≤5 秒的時槽；使用時間索引的 multi-commodity flow LP。變數為 contact 上傳輸量 x_l^f、時槽末 buffer 占用 b_(t,s)^f、hot spots 已收資料量 y_(t,f)。x 與 b 是非負連續量，不是 bundle 選路的 0/1 變數。見 pp.15–25。

**目標：[A]** g(Y) 的四個版本以每槽新增送達資料量或資料比例加權時間；實驗採式 (A)，使用平均時槽長度換算。不能直接稱為「每個不可分割 bundle 的 last-byte earliest arrival」，也不是單純最大化 throughput。見 pp.23–24、27。

**模型與限制：[A]** 式 (1) 為多 flow 共用 contact 容量；(2) 為流量守恆；(3) 為初始 buffer；(4) 為總 buffer 上限；(5) 為 deadline 前送達 hot spots；(7) 定義累積送達量。目的地是 hot spots 集合，不是本次固定單一目的節點。

**實驗：[A]** 47 節點（16 衛星、25 cold spots、6 hot spots），一天 contact plan，原始 3172 contacts，100 KB/s、buffer 30000 KB；切割後 2221 時槽與 17180 contacts。CPLEX 求解；比較 opt 與固定 CGR-deltime / CGR-hops 路線後再由同一 LP 排程的版本。見 pp.26–28。

**結果：[A]** 實驗 1 中作者報告 deltime / hops 在 demand 2100 / 2400 KB 起出現無解，opt 至 3000 KB 仍有解。實驗 10 使用 50 組 flow patterns，opt 在所測情境皆有解。這些結論只適用論文的模型、需求及 baseline，不能外推為完整 SABR 無容量感知。見 pp.29–30、41–42。

**限制與 reviewer 判斷：[C/E]**

1. 連續資料量可分流，未加每 bundle 單一路徑與整包接收後才轉送條件。故未直接解決本次 non-fragmented bundle 問題。
2. 正式式 (1)–(9) 未看到逐 hop 的 S/r + propagation delay 遞推；同槽流入與流出可同時平衡，不能據此宣稱連續時間的整包 store-and-forward 已被保證。需要原始模型 / 程式才能進一步核對實際排程語意。
3. 棄用短時槽會改變可行集合。p.27 以棄用時間比例 1.4% 解釋 throughput 犧牲，不足以保證所有需求的最大吞吐損失上界。
4. A p.10 文字 From=0 與 p.9 contact 表第一列 From=10 不一致；p.11 的敘述不能取代依 arrival、bundle size 判定的 extension。
5. A 已研究容量與 buffer；將「新增 capacity constraint」當作相對 A 的貢獻不成立。

**Related Work 用法：[C]** 用於說明全域多 flow LP 與單 bundle 線上可行路徑的範圍差異，以及容量、buffer 與時間離散化的重要性。

## Paper B

**一句話摘要：[B]** 對 SVC 多來源、多層 multicast routing 建立 ILP，再用 Lagrangian relaxation、子問題分解與可行解修復，提升 receiver satisfaction。

**問題與動機：[B]** 相同資料使用 unicast 重複傳送浪費頻寬；SVC layer 具有相依性，各 layer tree 同時受到頻寬與 end-to-end delay 限制，大規模 ILP 成本高。見 PDF pp.11–23。

**方法與貢獻：[B]** 原問題最大化加權接收層數，base layer 必須送達；鬆弛 path/tree 耦合與共用容量限制。子問題 A 對固定 (sender, receiver, layer) 解 delay-constrained minimum-cost path，成本由 λ 決定，再用 maximum prefix-sum 選層。子問題 B 選擇鏈路；primal heuristic 處理多父節點衝突、超載及回補。見 PDF pp.25–42。

**Label Setting 的真正地位：[B/C/E]**

- [B] PDF p.27（印刷 p.17）明確寫使用 Label Setting [11] 求 SPPRC；PDF p.38 的 reroute 先排除容量不足或違反 parent 限制的鏈路。
- [B] 此子問題的 time resource 是 Σd_l，上限 D_max；cost 是 Σλ_(s,r,k,l)。B 的 C_l、Δb_k 單位是 Mbps，不能直接搬成 DTN 的 MB contact volume。
- [C] 從子問題可重建 L=(v,d,z,pred,edge)，d'=d+d_l、z'=z+λ_l，d'≤D_max；同節點 d、z 都不大且至少一項嚴格較小時可支配。這些是依模型推導的規則。
- [E] B 沒有逐項列出自己的 label struct、queue tie-breaking、完整 dominance / equality handling pseudo-code；沒有原始碼，不能宣稱上述細節就是 B 的實作。
- 外部 H 的教學例子是帶 node time windows 的二維 time/cost SPPTW；B 的固定 D_max 問題不等於直接使用相同 time windows。H 的展示式使用兩維皆嚴格較小，還有 time(l)<time(l) 的排字問題，不應逐字照抄。

**實驗與結果：[B]** Pioro40、France，5–60 人，四個 SVC layers，與 BSMA 配合容量修復比較。Pioro40 高容量設定 60 人時 LR 22329 分、BSMA 19526 分；小規模 ILP 比較在 25 人為 ILP 4200、LR 4195。圖表中的 gap 是相對 LR upper bound，不是已知真實 optimum 的 error。見 PDF pp.43–59。

**限制與論文關聯：[C/E]** 靜態 rate capacity、可加 delay、multicast tree 與 layer utility 均不符合本次 DTN 原始語意。可移植 REF、非支配 labels、局部可行性檢查的框架；不能移植 multiplier cost、multicast sharing、layer dropping 來假裝解 non-fragmented bundle。初始 sequential Dijkstra 建樹失敗也不等於全網數學上無解。B 已展示 capacity-aware Dijkstra（PDF pp.28–30），這對本次新穎性判斷尤其重要。

**Related Work 用法：[C]** 說明何時 cost 和 constrained resource 的取捨需要 multiple labels，並作為框架使用案例；不要稱 B 發明 Label Setting。

## Concept mapping

下表的 proposed method 是待確認的 M0 基礎模型：單 bundle、固定資源快照、buffer 不限制、不含外部 transmission 時段衝突。

| Concept | Paper A | Paper B | My Proposed Method |
|---|---|---|---|
| Graph Model | [A] CGR 背景使用 contact-as-vertex；正式 LP 使用時間索引 flow network | [B] 靜態有向 network、multicast trees | [D] 節點為實體 node、邊為帶 window 的 contact，temporal directed multigraph |
| Node / Vertex | [A] CGR vertex 是 contact；LP s 是衛星或地面站 | [B] 參與者及交換機 | [D] v 是整包目前所在實體 node |
| Edge | [A] CGR 為 contact 銜接；LP l 為切割後 contact | [B] 有容量及 delay 的 link | [D] c=(u,v,t_start,t_end,r,δ,Q,R) |
| State | [A] 多 flow 傳輸量及時槽 buffer 占用 | [C] 路徑子問題可用 (v,d,z) | [D] 核心 (v,a)，加重建 metadata |
| Time Resource | [A] 時槽、release、deadline | [B] 累積 delay≤D_max | [C/D] a'=max(a,t_start)+S/r+δ |
| Capacity Resource | [A] Σ_f x_l^f≤c_l，資料量 | [B] Σ_s,k Δb_k x_s,k^l≤C_l，資料速率 | [D] 每 contact R_c≥S，非累積 path budget |
| Objective | [A] 送達量/比例加權時間 g(Y) | [B] 全局滿意度最大；子問題 A 成本最小 | [D] 單 bundle 最早整包到達；cost 版另列 |
| Feasibility | [A] flow conservation、capacity、buffer、deadlines | [B] delay、capacity、tree、layer dependency | [D] node continuity、完整傳送 window、R_c≥S |
| Extension Rule | [A] LP 約束，非 label extension | [C] d'=d+d_l；z'=z+λ_l | [D] 指定 contact 時間轉移，詳細見 extension_rule_v02.md |
| Dominance | [E] A 未提出本次用的 label dominance | [C] 由子問題與 framework 重建 time/cost componentwise | [C/D] M0 同 node 早到支配；lex 版需 time/cost Pareto |
| Pruning | [A] 小時槽棄用是預處理，不是 label dominance | [B] heuristic 刪除不可用 link；[C] label pruning | [D] 不可行 extension、被支配 label、stale record |
| Termination | [A] LP solver 終止 | [B] 外層預定迭代；[E] 內層未詳述 | [D] 最小有效 destination label 被取出，或 queue 空 |

## Combination 與新穎性結論

[C] 合理結合的是「DTN 接觸時序與整包傳輸語意」及「依未來可行性定義 state / REF / dominance 的框架」。這不要求使用 B 的 LR，也不要求保留多個 labels。

外部 S 的 §3.2.6.9(g) 已要求 non-fragmentable bundle 排除 RVL<EVC 的路線。因此 **CGR/SABR 完全不考慮容量** 這個動機不成立。該標準也有 last-byte arrival 與 reservation volume 機制；本次簡化模型不能冒稱完整 SABR。

[C] M0 的 FIFO 證明使 node-based time-dependent Dijkstra 足以精確求解。可行的數學整理、範例與程式驗證屬於必要基礎工作，尚不構成新的研究演算法。[E] 是否能在精確 reservation calendar、finite buffer 或多 bundle 資源耦合下提出新方法，需另行確認問題與文獻差異。
