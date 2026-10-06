# 單 bundle、固定有限 buffer 的演算法 v03

> 本文件是無其他 bundle 占用的 baseline。2026-10-05 已依使用者澄清新增 [依序預約 Label Setting v04](sequential_label_setting_v04.md)；其時間相依占用下，不可直接沿用本版單 label dominance。

適用範圍見 research_scope_v03.md；逐 byte buffer model 見 buffer_model_v03.md。所有核心設計 [D]，論證 [C]。本版沒有 cost、time-varying buffer 或 Known transmission calendar。

## State 與 extension

核心 L=(v,a)，重建欄位 pred、incoming_contact、transmission_start。

Global query context 保存 S、M_v、R_c 與 contact plan，不在 labels 重複保存容量陣列或完整路徑。

Extend(L,c)：

1. sender(c)=L.v。
2. M_sender≥S 且 M_receiver≥S。
3. s=max(L.a,start(c))，x=S/r_c。
4. f=s+x≤end(c)。
5. R_c≥S。
6. a'=f+δ_c，建立 receiver label，保存前驅與 s。

在本版使用最早 s 不會犧牲 buffer 可行性，因為符合 M_v≥S 的 node 可以不限時間等待。buffer 曲線在回傳 route 後由各 hop 的 (s,f,δ,r) 精確重建。

## Dominance 與正確性範圍

同 node、同 query 下 a_1≤a_2，早到者可等待至 a_2，再採相同 suffix；等待最多占 S≤M_v。故只需保留最早 arrival，不需成本欄位或 time/cost Pareto set。

對任一有 cycle 的 feasible route，將回到同一 node 之前的 cycle 改為留在該 node 等待，仍不超過 M_v，且不消耗被刪 contacts 的 quota。故存在無 physical-node cycle 的最優 route，沒有必要透過重複 contacts 取得更佳 arrival。此結論使用固定 buffer、無背景占用，不能套到前版的 blackout 反例。

sender/receiver buffer filtering 與 R filtering 後，每個 contact 的 arrival function 為 FIFO，且 S/r>0。因此同 node 單標籤的 time-dependent Dijkstra 正確；Dijkstra 與 Label Setting 不是互斥選擇。

## Pseudocode

```text
Algorithm 3  Earliest Arrival with Quota and Fixed Finite Buffer
Input: V, contacts C, quotas R, node buffer limits M, bundle (o,d,g,S)
Output: Earliest feasible route, schedule and occupancy functions

Validate rates, windows, quotas, buffer sizes and S
if M[o] < S or M[d] < S:
    return NO_FEASIBLE_ROUTE

Best[v] <- infinity for all nodes
Best[o] <- g
U <- indexed min-priority queue containing source label (o,g)
Settled <- empty set

while U is not empty:
    L <- ExtractMin(U)
    add L.node to Settled
    if L.node = d:
        Reconstruct route and schedule from predecessors
        Derive byte-level occupancy functions from the schedule
        return route, schedule, arrival and occupancy functions

    for each contact c with sender(c)=L.node:
        if receiver(c) in Settled:
            continue
        if M[receiver(c)] < S or R[c] < S:
            continue
        s <- max(L.arrival, start(c))
        f <- s + S/rate(c)
        if f > end(c):
            continue
        a_new <- f + propagationDelay(c)
        if a_new < Best[receiver(c)]:
            Best[receiver(c)] <- a_new
            Store stable predecessor label, contact c and start s
            InsertOrDecrease(U, receiver label)

return NO_FEASIBLE_ROUTE
```

合法 query 的 source/destination buffer 不足屬 NO_FEASIBLE_ROUTE；負容量、非正 rate 等屬 INVALID_INPUT。o=d 且 buffer 足夠時返回空路徑及 a=g。

使用 indexed heap，n=physical nodes、m=contacts，搜尋 O((n+m)log n)、包含輸入 memory O(n+m)。輸出 K-hop route 的 compact piecewise occupancy functions 為 O(K)。若為繪圖做時間取樣，其額外成本另列，不混進 routing bound。

## 實驗定位

這是正確的初期基礎版本，不能宣稱新的 multi-resource algorithm。

- 無 τ 的版本：只作 ablation，觀察錯誤 window acceptance 與 route ordering。
- 無 buffer filter 的版本：只作 ablation，觀察 M_v<S 的接收失敗。
- 同模型的 size-aware time-dependent Dijkstra：應得到同 optimum。
- SABR：需指定 route search、候選數與 size-aware evaluation 設定，不稱其完全忽略 transmission time。

目前未實作完整 routing 軟體或統計效能 benchmark。已獨立核對 byte-level occupancy 範例與 BDT/PAT 排序反例的算術。
