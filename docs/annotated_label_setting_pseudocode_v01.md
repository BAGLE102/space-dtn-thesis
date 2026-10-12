# Label Setting pseudocode（簡短註解版）

2026-10-13。保留英文虛擬碼，只在關鍵步驟加上簡短註解。對應現行有限格點、aggregate quota v04；不修改演算法判別式。

```text
Input: C, R, O, M, b=(src, dst, g, S), Δ, T

if source buffer check fails at g: return NO_ROUTE_ON_GRID
Q ← {source label L0}; Labels ← {L0}; solution ← none  // Q 依 A 排序
while Q is not empty:
    L ← ExtractMin(Q, arrival time)
    if L is inactive: continue
    if node(L) = destination:
        solution ← TraceBack(L); break                // 找到目的地，先回溯
    for each outgoing contact c:
        if route_usage(L,c) + S > R[c]: continue      // 檢查剩餘總容量
        first ← max(A(L), start(c))
        last  ← end(c) − S/r(c)
        for s = first to last, step Δ:                // 枚舉所有可用格點
            f ← s + S/r(c)
            h ← s + δ(c)
            Anew ← f + δ(c)
            if Anew > T or sender/receiver buffer check fails: continue
            N ← (c, Anew, s, predecessor=L)
            compare N with active labels at the same node
            if an existing label dominates N: discard N
            else: invalidate dominated labels; insert N into Q

if solution is none: return NO_ROUTE_ON_GRID
if independent validation fails: stop and preserve the case
commit capacity and buffer reservations; return solution  // 選定後才預約
```

原網站在取出目的地時直接 `return TraceBack(L)`，使後面的驗證與預約無法執行。此處以 `break` 接續驗證與預約；這是展示流程修正。`route_usage(L,c)` 可由前驅鏈計算，不是新增 Label 欄位。
