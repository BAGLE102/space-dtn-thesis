# Dominance rule v02

## 問題分類

[C] M0 有時間與多條 local capacity inequalities，但不是因此就成為一般 multi-resource constrained shortest path。固定 bundle size 下，R_c≥S 可局部篩邊；唯一必須追蹤的連續 state 是 arrival。它是 FIFO time-dependent earliest-arrival problem，Dijkstra 本身就是一種 label-setting 方法。

[D] M0-Lex 另外考慮 path cost，才會發生 arrival / cost 的不可比較性。有限 buffer、energy budget、多 bundle 競爭是不同擴充，不能混稱同一演算法。

## 一般原則

真正的 dominance 必須讓被刪 label 的任何可行 suffix，都能由保留 label 完成且 objective 不差。比較座標之前，先確認兩者的 state、允許的未來操作及資源背景可比。

## M0：Earliest Arrival

同一實體 node v、相同 bundle 與相同資源快照下：

\[
L_1\preceq L_2\iff v_1=v_2\ \land\ a_1\le a_2.
\]

a_1<a_2 為嚴格支配；a_1=a_2 為 objective / future-feasibility 等價，固定保留一個即可。不要因互相弱支配把兩者都刪掉。

**成立條件：** buffer 不限制、等待免費、資源不因候選 prefix 而改變、無 path-dependent costs/restrictions、contact transfer 為 FIFO。

**證明：[C]** L_1 可在 v 等到 a_2，然後採 L_2 的同一 suffix schedule；或逐 hop 套用 F_c 的單調性得到更早或同時到達。因此刪除 L_2 不影響最早可行目的地到達。若同一 suffix 回到 prefix node，可刪去 cycle，以原 node 等待取代，得到不晚且不用更多資源的 route。

## M0-Lex：Earliest Arrival first, then minimum cost

目的地比較 (a,z) 採 lexicographic order。**中間節點 pruning 不可直接以 prefix 字典序決定。** 使用安全的充分條件：

\[
v_1=v_2,\quad a_1\le a_2,\quad z_1\le z_2,
\]

且至少一項嚴格小。兩項相等則合併一個等價 label。κ_c≥0、固定且不依 departure 改變，等待免費。早到但昂貴、晚到但便宜的 labels 均保留。

Queue 以 (a,z,stable_ID) 排序。不得 settled 一整個 node；只標記已處理的 label。當有效 destination label 被取出才回傳。由 S/r>0，任意能改善該目的地 arrival 的未生成 route，其 predecessor arrival 必更早，理應先被展開；相同目的地 arrival 的較低 cost route 也同樣如此。這裡的終止證明依賴本文件的限制，不是 B 原算法的直接聲明。

## Examples

| Case | 同節點 labels | 判定 | 理由 |
|---|---|---|---|
| A | L1=(v,a=4,z=2)，L2=(v,a=6,z=5) | M0-Lex 中 L1 支配 L2 | time、cost 都不差，等待可模擬後續 |
| B | L1=(v,4,9)，L2=(v,6,1) | M0-Lex 中互不支配 | 早到與低成本取捨；M0 中沒有 z，才可刪 L2 |
| C1 | L1=(v,5,9)，L2=(v,5,1) | 必須保留 L2 | 相同 arrival 不能任意保留昂貴者 |
| C2 | L1=(v,4,9)，L2=(v,6,1)，下一跳在 10 開始、傳輸 1、δ=0、cost=0 | 最後皆在 11 抵達，但 L2 成本 1 | 若以中間 prefix lex order 刪 L2，會輸出錯誤 tie-break |

## Finite-buffer 反例與適用邊界

同 node B 的兩個 labels 在 2、5 抵達，bundle size=1；B 剩餘 buffer 在 [3,4) 為 0，其他時段≥1，下一 contact 在 6 開始。晚到 label 可等至 6；早到 label 無法跨越 [3,4) 保存整包，因此不能無條件刪晚到者。

這個反例只用來推翻「早到永遠支配」；若上游可以延後發送而在 5 抵達，演算法也必須能生成該 state。把晚到 label 刪掉，又只保留 earliest-start extension，仍然不完整。

在外部 buffer 日曆固定、候選前綴不影響未來資源、已定義好 buffer 釋放時刻的簡化模型下，額外要求 B_res_v(t)≥S 對所有 t∈[a_1,a_2) 成立，可作為早到模擬晚到的橋接條件。舊 PPT 第 8 頁其實有此形式；第 26、27 頁卻刪去了它。**此條件只支持特定 dominance 推論，不代表整個 finite-buffer algorithm 已完整。**

若不同 prefixes 造成不同未來預約，或等待會增加 cost / 消耗 energy，還要比較相應 calendar / resource，不能只對 arrival 判斷。僅要求同 incoming contact 也不夠。
