# 允許循環的Label Setting虛擬碼（無支配驗證版）

本版依使用者確認修改：允許節點及contact重訪，沿pred計算同contact已用容量，保留四欄Label與全部候選。不是已定案的dominance版本。

## 符號

| 符號 | 定義 |
| --- | --- |
| C | Contact Plan；每個c含sender、receiver、start、end、rate、delay |
| b=(source,destination,g,S) | 本包的來源、目的地、生成時間、大小 |
| R[c] | 搜尋開始前contact c的剩餘容量，搜尋中不變 |
| O[v](t) | 先前已接受bundles在節點v的預約占用量 |
| M[v] | 節點v的Buffer上限 |
| F[c] | 先前已接受bundles在contact c的發送預約區間集合 |
| Δ | 候選起送時間的格點間隔，Δ>0 |
| T | 搜尋上限，同時作本輪抵達期限 |
| L=(c(L),A(L),s(L),pred(L)) | 最後contact、完整抵達時間、該contact起送時間、前驅Label |
| c₀ | 起點虛擬contact，其receiver為source；程式以None表示 |
| Q | 以(A(L),建立順序)排序的最小優先佇列 |
| f、h、a | 最後byte送出、第一byte抵達、最後byte抵達時間 |
| P | 沿pred回溯得到的有序(contact,起送時間)序列，可重複contact |

適用前提：不可分割、整包接收後轉送、每跳固定正速率、非負傳播延遲、單一副本、逐byte釋放、有限T、固定規劃順序。同contact的發送預約不可重疊。本段以source≠destination的傳送需求表示；程式另處理本地交付峰值。

## Algorithm 1: Sequential Routing and Reservation

```text
Input: C, ordered bundles B, R, O, M, F, Δ, T
Output: route and transmission times for each bundle

for each bundle b in B do:
    P ← LabelSetting(C, b, R, O, M, F, Δ, T)
    if P = NO_ROUTE_ON_GRID:
        report failure for b
        continue

    ValidateCompleteSchedule(P, b, R, O, M, F, Δ, T)
    if validation fails:
        preserve failure case and stop               // 不自動修演算法

    for each hop (c, s) in P do:
        R[c] ← R[c] − b.size                         // 每使用一次扣一次
        F[c] ← F[c] ∪ {(s, s + b.size/rate(c))}
    O ← O + BufferProfiles(P, b)                     // 接收、等待、發送
    report P and its hop times
```

ValidateCompleteSchedule必須逐跳累計容量與檢查完整時間／Buffer／發送預約，失敗時不能先提交部分資源。BufferProfiles以每次節點停留的實際時段建立曲線，不把以前已釋放的資料一直加到現在。

## Algorithm 2: Label Setting with Contact Reuse

```text
Input: C, b=(source,destination,g,S), R, O, M, F, Δ, T
Output: an earliest-arrival route on the grid, or NO_ROUTE_ON_GRID

L₀ ← (c₀, g, —, ∅)
Q ← {L₀}

while Q is not empty do:
    L ← ExtractMin(Q, (arrival time, creation order))
    u ← Node(L)                                     // c(L) 的接收端
    if u = destination:
        return TraceBack(L)

    for each contact c with sender(c) = u do:
        used ← ContactUsage(L, c, S)
        if used + S > R[c]:
            continue

        first ← Δ × ceil(max(A(L), start(c))/Δ)
        last ← end(c) − S/rate(c)
        for s ← first to last, step Δ do:             // 某個 s 失敗仍試後面
            f ← s + S/rate(c)
            h ← s + delay(c)
            a ← f + delay(c)
            if a > T:
                continue

            v ← receiver(c)
            if ReceiverBufferFails(v, h, a, S, rate(c), O, M):
                continue
            if [s,f) overlaps any interval in F[c]:
                continue
            if SenderBufferFails(u, A(L), s, f, S, rate(c), O, M):
                continue

            N ← (c, a, s, predecessor=L)
            Insert(Q, N)                             // 本版不做支配刪除

return NO_ROUTE_ON_GRID
```

Contact依ID排序，候選起送時間遞增，新Label依建立序號決定同時間的取出順序。允許重訪節點及同一contact，不設visited節點排除規則。

## Algorithm 3: Contact Usage Along the Predecessor Chain

```text
Input: current label L, contact c, bundle size S
Output: capacity used on c by this candidate route

used ← 0
K ← L
while pred(K) ≠ ∅ do:
    if c(K) = c:
        used ← used + S
    K ← pred(K)
return used
```

used是本次判斷的臨時變數，不是新增Label欄位。搜尋期間R保留原值，所以重用contact時需要沿pred累計；選定完整路徑後才真正扣R。

## Buffer判別式

接收端v，在整段接收時間：

```text
O[v](t) + rate(c) × (t − h) ≤ M[v]     for every t in [h,a]
```

傳送端u，等待與逐byte發送：

```text
O[u](t) + S ≤ M[u]                    for every t in [A(L),s]
O[u](t) + S − rate(c) × (t − s) ≤ M[u] for every t in [s,f]
```

實作在所有相關分段線性折點檢查全段峰值，包含交付前峰值，不只檢查整數秒。接收完成後的等待在下一次延伸檢查。

在單一副本、完整接收後轉送、逐byte釋放的前提下，重返同一節點時，前次停留的資料已送完並釋放；不需把本包歷史Buffer量重複加到新接收期間。這不適用保留副本、custody保留或不同釋放規則。

## 有限性與核對範圍

每跳完整抵達時間嚴格增加：A(new)≥A(L)+S/rate(c)+delay(c)>A(L)。有限contacts與有限T下，hop數由最小正的每跳耗時界定，不會無限繞圈，但候選數仍可能很大。

完整列舉核對程式使用上述hop上界，保留重訪，對各walk的起送時間笛卡兒積核對完整排程，不以待測搜尋的Buffer或容量規則做增量剪枝。實作設Label／walk數量上限，超過會回報INCOMPLETE，不能當作NO_ROUTE。

## 已完成檢查

- 新增可行繞圈案例A→B→A→B→D，同contact ab用兩次，抵達5秒，容量扣兩次且發送區間分別[0,1)、[3,4)。
- 將ab剩餘容量由2降為1時，搜尋與完整列舉都無解。
- 不可達目的地的循環案例會在有限期限內結束。
- 原PPT兩包仍抵達8、12秒；八節點五包仍為12、12、13、20秒與第5包無解。
- 16項相關測試通過。完整列舉一致是小案例證據，不是一般支配正確性證明。

程式在src/ppt_validation/；新輸出在output/ppt_cycles_20261013/。未改frozen v04、PPT或網站，未執行整天Ring Road效能實驗。
