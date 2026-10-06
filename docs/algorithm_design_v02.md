# Capacity-Aware Label Setting Algorithm for Space DTN v02

狀態：[D] [Proposed Design] 基礎模型 M0 的精確求解草稿。更準確的副標題為 **Capacity-Filtered FIFO Earliest-Arrival Routing**。Dijkstra 是 label-setting 家族的一員；此名稱不代表本演算法具新穎性。

## Input / Output

- Input：合法的 V、有限 C、固定 R 快照、單一 b=(o,d,g,S)。M0 的所有假設見 problem_formulation_v02.md。
- Output：最早可行 contact sequence P*、每 hop 的 (s,f,a)、目的地 arrival；或 NO_FEASIBLE_ROUTE / INVALID_INPUT。
- 只承諾單 query routing；不直接更動網路資源，也不承諾多 bundle 最佳排程。

## 搜尋流程

1. 建 outgoing[v]，初始化 best[v]=null、settled[v]=false。
2. best[o] 設 source label，放入以 arrival 排序的 indexed priority queue U。
3. ExtractMin 取出目前最小有效 label。每 node 在 U 至多一項；decrease-key 更新待處理 label。
4. 將該 node settled。若為目的地，沿 predecessor 回溯並反轉，回傳 path 和 schedule。
5. 對 sender=目前 node 的每 contact 執行 Extend；window 或 R 不足就拒絕。
6. 若候選 arrival 不嚴格小於該 node 現有 arrival，則被支配或等價，不加入。
7. 若嚴格改善且 receiver 尚未 settled，替換 best 並 decrease-key。未被接受的候選不得扣 R。
8. U 空則無可行路徑。

若使用 lazy heap，須在 pop 時跳過已失效 / settled records，不能在第一次生成 destination 時回傳。

## 正確性摘要 [C]

**可行性 invariant：** 每一個接受的 label 對應一條從 o 出發且符合全部 M0 檢查的 route。source 成立；每一步 Extend 保留端點與時序、檢查整包容量和 window，因此歸納成立。

**Dominance invariant：** 同 node 最早到達可免費等待來模擬晚到 label 的 suffix。因此丟棄晚到及等價 labels 不影響最優值。

**Settling：** F_c(a) 單調且 F_c(a)>a（S/r>0），若有尚未發現且更早到達 settled node 的路徑，該路徑上第一個尚未 settled 節點的前驅應更早被展開，造成矛盾。因此 ExtractMin 的 destination label 最優。

**Completeness / termination：** 每 node 最多 settled 一次，有限 contacts 可列舉完，沒有因不安全 pruning 漏解。U 空表示在當前有限 horizon、固定快照與 M0 假設下不可達。

## Complexity

n=|V|、m=|C|。outgoing 建立 O(n+m)；indexed binary heap 的 queue operations O(log n)，每 contact 最多掃描一次，總 O((n+m)log n)，包含輸入的 memory O(n+m)。若採 lazy heap，可有 O(m) queue records，保守寫 O((n+m)log(n+m)) 與 O(n+m) memory，不能把實作與 bound 混用。

此 bound 用的是 physical-node multigraph；若先建立 contact-as-vertex graph，vertex 數為 m，contact transition edges 的數量可能到 O(m²)，不能沿用 physical graph 的 m。

## M0-Lex variant

- 每 node 改存 active non-dominated label set N[v]。
- state 增加 z，extension 增加 κ_c。
- 同 node 用 (a,z) componentwise dominance，不能以字典序只保留單一 prefix。
- U 以 (a,z,ID) 排序；每次展開一個 label，node 不做永久 settled。
- 刪除 label 僅使其失效，重建仍可能用到的 predecessor objects 必須保留。
- destination 在有效 label 被 ExtractMin 時回傳。

令 M 為整次生成 labels 的總數（含之後失效者）、H 為任一 node active labels 最大數、X 為 contact extension 嘗試總數。樸素 dominance 掃描需 O(X+M H+M log M)，記憶體 O(n+m+M)。M 可隨輸入呈指數成長，不能使用 M0 的 polynomial bound 宣稱此版本也一樣快。

## 不可擴張的保證

finite buffer、任意 dynamic R 更新、候選之間聯合占用、多 bundle fairness、外部 busy intervals，都不在 Algorithm 1 的保證範圍。對 real reservations 而言，R 只有 aggregate volume，不代表可排入整包。

## 驗證狀態

已用獨立 contact sequence 列舉及有理數算術檢查 small_topology_v02.md 的全部四條時間可行路線、三條 M0 feasible routes、兩個失敗 extension。這是構造案例的算術驗證，尚未實作整個 routing 系統或做統計效能實驗。
