# 演算法虛擬碼／Algorithm Pseudocode（2026-11-23）

對應程式：`src/experiments/dtn_validation/dtn/`，註解版在 `src/algorithm/`。

本版已包含 2026-11-23 的修改：路徑不重複經過同一節點。

中文版在前，英文版在後，兩版內容一一對應。

---

# 中文版

## 符號

| 符號 | 意思 |
|---|---|
| c = (u, v, a, b, r, d, F) | 連線：從 u 到 v，a～b 開放，速率 r，傳播延遲 d，已預約時段 F |
| S、g、T、M | 包大小、產生時間、期限、Buffer 上限 |
| O[n] | 節點 n 的占用曲線（ts、ls、rs） |
| ct | 1 = 邊收邊轉，0 = 收完才轉 |
| τ(c) = S / c.r | 在連線 c 上傳一包的時間 |
| lag(c1, c2) | 收完才轉：τ(c1)；邊收邊轉：max(0, τ(c1) − τ(c2)) |
| ramp(t, x, y) | x 到 y 由 0 直線升到 S，t 時刻的值 |
| Label L = (c, lo, hi, pred) | 走連線 c，可在 [lo, hi] 任一時間出發，前一跳 pred |

## 演算法 1：依序規劃所有包

```
輸入：連線集合、需求清單（依產生時間排序）
對每一包 (src, dst, g)：
    sch ← 規劃(src, dst, g)                      // 演算法 2～6
    若 sch 存在 且 驗證(sch) 通過：
        寫入(sch)                                 // 演算法 7
        記為送達
    否則：
        記為未送達
```

## 演算法 2：搜尋

```
若 S > M：回傳 找不到
Q ← 空的優先佇列（依到達時間排序）
reached[c] ← 空集合（每條連線已放過的出發區間）

對每條從 src 出去的連線 c：
    P ← 候選區間(c, head = g)                    // 演算法 3
    P ← 來源篩選(c, P)                           // 演算法 4a
    若 c.v = dst：P ← 目的地篩選(c, P)            // 演算法 4c
    放入(c, P, pred = 無)

當 Q 不是空的：
    L1 ← 取出 Q 中到達時間最早的 Label
    若 L1.c.v = dst：回傳 回推(L1)               // 演算法 6
    已經過 ← {src} ∪ {L1 路徑上每一跳的終點}
    對每條從 L1.c.v 出去的連線 c2：
        若 c2.v ∈ 已經過：跳過                   // 不重複經過同一節點
        head ← L1.lo + L1.c.d + lag(L1.c, c2)
        P ← 候選區間(c2, head)
        若 P 是空的：跳過
        P ← 中繼篩選(L1, c2, P)                  // 演算法 4b
        若 c2.v = dst：P ← 目的地篩選(c2, P)
        放入(c2, P, pred = L1)
回傳 找不到

放入(c, P, pred)：
    新的 ← 合併(P − reached[c])                  // 只留這條連線還沒放過的部分
    若 新的 是空的：結束
    reached[c] ← 合併(reached[c] ∪ 新的)
    對 新的 裡的每段 [lo, hi]：
        把 Label(c, lo, hi, pred) 放進 Q，排序值 = lo + τ(c) + c.d
```

## 演算法 3：候選區間（連線限制）

```
候選區間(c, head)：
    lo ← max(c.a, head)
    hi ← min(c.b − τ(c), T − τ(c) − c.d)
    若 lo > hi：回傳 空
    P ← {[lo, hi]}
    對 c.F 裡每筆預約 (x, y)：
        P ← P 扣掉開區間 (x − τ(c), y)          // 出發時間落在這裡就會和預約重疊
    回傳 P
```

## 演算法 4：Buffer 篩選（先快速檢查，不行再細緻檢查）

```
4a 來源篩選(c, P)：                              // 這包在來源：g 起占 S，出發後邊送邊降
    對 P 的每段 [lo, hi]：
        若 O[src].peak(g, hi + τ(c)) + S ≤ M：保留整段      // 快速檢查
        否則：用 細緻檢查 找出 [lo, hi] 中可行的出發時間 s
              檢查點：g、s，以及停留期間 O[src] 的變化點 x
              水位(x) = O(x) + S − ramp(x, s, s + τ(c))
              切點：x、x − τ(c)（x 為視窗內 O[src] 的變化點）
              切點本身用 來源規則(c, s) 判斷

4b 中繼篩選(L1, c2, P)：                         // 變數是下一跳出發時間 s2
    c1 ← L1.c，n ← c1.v
    s1*(s2) ← min(L1.hi, s2 − c1.d − lag(c1, c2))   // 前一跳只試最晚出發
              若 s2 − c1.d − lag < L1.lo：這個 s2 不可行
    對 P 的每段 [lo, hi]：
        若 O[n].peak(L1.lo + c1.d, hi + τ(c2)) + S ≤ M：保留整段     // 快速檢查
        否則：用 細緻檢查 找出可行的 s2
              h = s1* + c1.d（開始收），A = h + τ(c1)（收完），f = s2 + τ(c2)（送完）
              這包的量 own(t) = ramp(t, h, A) − ramp(t, s2, f)
              檢查點：A、s2，以及停留期間 O[n] 的變化點 x
              水位(x) = O(x) + own(x)
              切點：clamp = L1.hi + c1.d + lag，L1.hi + c1.d + τ(c1)，
                    以及每個變化點 x 的 x、x − τ(c2)、x + lag、x + lag − τ(c1)
              切點本身用 中繼規則(c1, s1*, c2, s2) 判斷
    回傳 合併(結果)

4c 目的地篩選(c, P)：                            // 只收不送，收完 A 那一刻交付
    若 O[dst] 是空的：若 S ≤ M 回傳 P，否則回傳 空
    對 P 的每段 [lo, hi]：
        若 O[dst].peak(lo + c.d, hi + c.d + τ(c)) + S ≤ M：保留整段  // 快速檢查
        否則：用 細緻檢查 找出可行的 s
              h = s + c.d，A = h + τ(c)
              檢查點：A 的左極限（水位 = O.left(A) + S），以及收的期間 O[dst] 的變化點 x
              水位(x) = O(x) + ramp(x, h, A)
              切點：x − c.d、x − c.d − τ(c)
              切點本身用 目的地規則(c, s) 判斷
```

## 演算法 5：細緻檢查

```
細緻檢查(lo, hi, 切點, 規則, 水位)：
    pts ← 排序後的 {lo, hi} ∪ {落在 (lo, hi) 內的切點}
    結果 ← {[p, p] : p ∈ pts 且 規則(p) 成立}     // 切點用原規則直接判斷
    對每一段 (p, q)：                            // 相鄰兩個切點之間
        e ← p + (q − p)/3，g ← p + 2(q − p)/3，m ← (p + q)/2
        L ← p，H ← q
        對每個檢查點 i：                          // 段內每個水位都是 s 的一次式
            k ← (水位_i(g) − 水位_i(e)) / (g − e)
            若 k = 0：若 水位_i(e) > M，整段不可行
            若 k > 0：H ← min(H, e + (M − 水位_i(e)) / k)       // 上界
            若 k < 0：L ← max(L, e + (M − 水位_i(e)) / k)       // 下界
        若 整段沒有被排除 且 L ≤ H：結果 加入 [L, H]
    回傳 合併(結果)
（m 用來決定這一段中，哪些舊變化點落在停留期間）
```

## 演算法 6：回推

```
回推(L)：
    s ← L.lo                                     // 最後一跳取最早，決定到達時間
    排程 ← [(L.c, s)]
    當 L.pred 存在：
        q ← L.pred
        k ← min(q.hi, s − q.c.d − lag(q.c, L.c))   // 趕得上下一跳的最晚出發
        把 (q.c, k) 加到排程最前面
        L ← q，s ← k
    回傳 排程
```

## 演算法 7：寫入

```
寫入(sch)：
    對每一跳 (c, s)：c.F 加入 (s, s + τ(c))
    來源：g < s0 時 ts [g, s0, f0]，ls [0, S, 0]，rs [S, S, 0]
          否則      ts [s0, f0]，ls [0, 0]，rs [S, 0]
    每個中繼（h、A、s2、f 同上）：
        邊收邊轉且 s2 < A：在 {h, A, s2, f} 上取 ramp(t, h, A) − ramp(t, s2, f)，ls = rs
        A < s2：         ts [h, A, s2, f]，值 [0, S, S, 0]
        A = s2：         ts [h, A, f]，值 [0, S, 0]
    目的地：ts [h, A]，ls [0, S]，rs [0, 0]
    每條曲線用 O[n] ← O[n] + 曲線 加進節點（變化點聯集、左右極限分別相加、刪掉共線點）
```

## 附：規則（驗證用，也是切點的判斷）

```
停留檢查(O, 起, 終, own, own_終點)：
    起點：own(起) > 0 時，O.right(起) + own(起) ≤ M
    終點：own_終點 > 0 時，O.left(終) + own_終點 ≤ M
    中間：對這包的變化點與 O 在 (起, 終) 內的變化點 t，own(t) > 0 時 O.top(t) + own(t) ≤ M

來源規則(c, s)：停留檢查(O[src], g, s + τ(c), S − ramp(t, s, s + τ(c)), 0)
中繼規則(c1, s1, c2, s2)：
    h = s1 + c1.d，A = h + τ(c1)，f = s2 + τ(c2)
    收完才轉：需要 s2 ≥ A
    邊收邊轉：需要 s2 ≥ h 且 f ≥ A
    停留檢查(O[c1.v], h, f, ramp(t, h, A) − ramp(t, s2, f), 0)
目的地規則(c, s)：h = s + c.d，A = h + τ(c)，停留檢查(O[dst], h, A, ramp(t, h, A), S)
連線規則(c, s)：s ≥ c.a，s + τ(c) ≤ c.b，s + τ(c) + c.d ≤ T，且不和 c.F 任一 (x, y) 重疊（s < y 且 x < s + τ(c)）
驗證(sch)：從 src 出發、到 dst 結束、s0 ≥ g、相鄰兩跳接得起來、不重複經過節點，
           每跳連線規則、來源規則、目的地規則、每個中繼規則都成立
```

## 已知限制

1. reached 以連線為單位去重；加上「不重複經過節點」後，可能漏掉少數可行路徑。
2. 停留檢查在 own = 0 的時刻不檢查，只在背景占用本身超過 M 時有影響。
3. 逐包規劃，不保證所有包一起看的最佳。

---

# English version

## Notation

| Symbol | Meaning |
|---|---|
| c = (u, v, a, b, r, d, F) | Contact from u to v, open [a, b], rate r, propagation delay d, reserved intervals F |
| S, g, T, M | Bundle size, creation time, deadline, buffer capacity |
| O[n] | Occupancy curve of node n (ts, ls, rs) |
| ct | 1 = cut-through, 0 = store-and-forward |
| τ(c) = S / c.r | Transmission time on contact c |
| lag(c1, c2) | Store-and-forward: τ(c1); cut-through: max(0, τ(c1) − τ(c2)) |
| ramp(t, x, y) | Linear rise from 0 at x to S at y, evaluated at t |
| Label L = (c, lo, hi, pred) | Use contact c, depart at any time in [lo, hi], previous hop pred |

## Algorithm 1: Sequential planning

```
Input: contacts, demands sorted by creation time
for each bundle (src, dst, g):
    sch ← Plan(src, dst, g)                       // Algorithms 2–6
    if sch exists and Validate(sch):
        Commit(sch)                               // Algorithm 7
        mark delivered
    else:
        mark not delivered
```

## Algorithm 2: Search

```
if S > M: return NONE
Q ← empty priority queue (ordered by arrival time)
reached[c] ← ∅ for every contact c

for each contact c leaving src:
    P ← CandidateRange(c, head = g)               // Algorithm 3
    P ← SourceFilter(c, P)                        // Algorithm 4a
    if c.v = dst: P ← DestinationFilter(c, P)     // Algorithm 4c
    Insert(c, P, pred = NONE)

while Q is not empty:
    L1 ← pop the label with the earliest arrival
    if L1.c.v = dst: return Backtrack(L1)         // Algorithm 6
    visited ← {src} ∪ {end node of every hop on L1's path}
    for each contact c2 leaving L1.c.v:
        if c2.v ∈ visited: continue               // no node is visited twice
        head ← L1.lo + L1.c.d + lag(L1.c, c2)
        P ← CandidateRange(c2, head)
        if P = ∅: continue
        P ← RelayFilter(L1, c2, P)                // Algorithm 4b
        if c2.v = dst: P ← DestinationFilter(c2, P)
        Insert(c2, P, pred = L1)
return NONE

Insert(c, P, pred):
    new ← Merge(P − reached[c])                   // keep only departure times not yet inserted for c
    if new = ∅: return
    reached[c] ← Merge(reached[c] ∪ new)
    for each interval [lo, hi] in new:
        push Label(c, lo, hi, pred) into Q with key lo + τ(c) + c.d
```

## Algorithm 3: Candidate range (contact constraints)

```
CandidateRange(c, head):
    lo ← max(c.a, head)
    hi ← min(c.b − τ(c), T − τ(c) − c.d)
    if lo > hi: return ∅
    P ← {[lo, hi]}
    for each reservation (x, y) in c.F:
        P ← P minus the open interval (x − τ(c), y)   // departures here would overlap it
    return P
```

## Algorithm 4: Buffer filters (fast check first, detailed check if it fails)

```
4a SourceFilter(c, P):                            // bundle holds S from g, drains while sending
    for each [lo, hi] in P:
        if O[src].peak(g, hi + τ(c)) + S ≤ M: keep [lo, hi]   // fast check
        else: SolveRegion over departure time s
              check points: g, s, and breakpoints x of O[src] during the stay
              level(x) = O(x) + S − ramp(x, s, s + τ(c))
              cut points: x and x − τ(c) for each breakpoint x of O[src] in the window
              cut points themselves are tested with SourceRule(c, s)

4b RelayFilter(L1, c2, P):                        // variable: next-hop departure s2
    c1 ← L1.c, n ← c1.v
    s1*(s2) ← min(L1.hi, s2 − c1.d − lag(c1, c2))     // try only the latest previous departure
              infeasible if s2 − c1.d − lag < L1.lo
    for each [lo, hi] in P:
        if O[n].peak(L1.lo + c1.d, hi + τ(c2)) + S ≤ M: keep [lo, hi]   // fast check
        else: SolveRegion over s2
              h = s1* + c1.d (start receiving), A = h + τ(c1) (received), f = s2 + τ(c2) (sent)
              own(t) = ramp(t, h, A) − ramp(t, s2, f)
              check points: A, s2, and breakpoints x of O[n] during the stay
              level(x) = O(x) + own(x)
              cut points: clamp = L1.hi + c1.d + lag, L1.hi + c1.d + τ(c1),
                          and x, x − τ(c2), x + lag, x + lag − τ(c1) for each breakpoint x
              cut points themselves are tested with RelayRule(c1, s1*, c2, s2)
    return Merge(result)

4c DestinationFilter(c, P):                       // receive only, delivered at A
    if O[dst] is empty: return P if S ≤ M else ∅
    for each [lo, hi] in P:
        if O[dst].peak(lo + c.d, hi + c.d + τ(c)) + S ≤ M: keep [lo, hi]   // fast check
        else: SolveRegion over s
              h = s + c.d, A = h + τ(c)
              check points: left limit at A (level = O.left(A) + S), and breakpoints x of O[dst] while receiving
              level(x) = O(x) + ramp(x, h, A)
              cut points: x − c.d and x − c.d − τ(c)
              cut points themselves are tested with DestinationRule(c, s)
```

## Algorithm 5: Detailed check

```
SolveRegion(lo, hi, cutPoints, Rule, Level):
    pts ← sorted({lo, hi} ∪ {cut points strictly inside (lo, hi)})
    result ← {[p, p] : p ∈ pts and Rule(p)}       // cut points use the exact rule
    for each segment (p, q) between consecutive points:
        e ← p + (q − p)/3, g ← p + 2(q − p)/3, m ← (p + q)/2
        L ← p, H ← q
        for each check point i:                   // every level is linear in s inside a segment
            k ← (Level_i(g) − Level_i(e)) / (g − e)
            if k = 0: segment infeasible if Level_i(e) > M
            if k > 0: H ← min(H, e + (M − Level_i(e)) / k)   // upper bound
            if k < 0: L ← max(L, e + (M − Level_i(e)) / k)   // lower bound
        if the segment is not excluded and L ≤ H: add [L, H] to result
    return Merge(result)
(m decides which old breakpoints fall inside the stay for this segment)
```

## Algorithm 6: Backtrack

```
Backtrack(L):
    s ← L.lo                                      // last hop: earliest, sets the arrival time
    schedule ← [(L.c, s)]
    while L.pred exists:
        q ← L.pred
        k ← min(q.hi, s − q.c.d − lag(q.c, L.c))  // latest departure that still meets the next hop
        prepend (q.c, k) to schedule
        L ← q, s ← k
    return schedule
```

## Algorithm 7: Commit

```
Commit(sch):
    for each hop (c, s): add (s, s + τ(c)) to c.F
    Source: if g < s0: ts [g, s0, f0], ls [0, S, 0], rs [S, S, 0]
            else:      ts [s0, f0], ls [0, 0], rs [S, 0]
    Each relay (h, A, s2, f as above):
        cut-through and s2 < A: values ramp(t, h, A) − ramp(t, s2, f) at {h, A, s2, f}, ls = rs
        A < s2:                 ts [h, A, s2, f], values [0, S, S, 0]
        A = s2:                 ts [h, A, f], values [0, S, 0]
    Destination: ts [h, A], ls [0, S], rs [0, 0]
    Add each curve with O[n] ← O[n] + curve (union of breakpoints, add left and right limits separately, drop collinear points)
```

## Appendix: rules (used by Validate and at cut points)

```
StayCheck(O, start, end, own, ownEnd):
    start: if own(start) > 0 then O.right(start) + own(start) ≤ M
    end:   if ownEnd > 0 then O.left(end) + ownEnd ≤ M
    inside: for this bundle's breakpoints and O's breakpoints t in (start, end),
            if own(t) > 0 then O.top(t) + own(t) ≤ M

SourceRule(c, s): StayCheck(O[src], g, s + τ(c), S − ramp(t, s, s + τ(c)), 0)
RelayRule(c1, s1, c2, s2):
    h = s1 + c1.d, A = h + τ(c1), f = s2 + τ(c2)
    store-and-forward: require s2 ≥ A
    cut-through:       require s2 ≥ h and f ≥ A
    StayCheck(O[c1.v], h, f, ramp(t, h, A) − ramp(t, s2, f), 0)
DestinationRule(c, s): h = s + c.d, A = h + τ(c); StayCheck(O[dst], h, A, ramp(t, h, A), S)
HopRule(c, s): s ≥ c.a, s + τ(c) ≤ c.b, s + τ(c) + c.d ≤ T, and no overlap with any (x, y) in c.F (s < y and x < s + τ(c))
Validate(sch): starts at src, ends at dst, s0 ≥ g, consecutive hops connect, no node visited twice,
               and HopRule, SourceRule, DestinationRule, and every RelayRule hold
```

## Known limitations

1. reached deduplicates per contact. With the no-revisit rule, a few feasible paths may be missed.
2. StayCheck skips instants where own = 0; this matters only when background occupancy already exceeds M.
3. Bundles are planned one at a time, so the result is not guaranteed to be optimal for all bundles together.
