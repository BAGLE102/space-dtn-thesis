# Algorithm-style pseudocode v02

[D] [Proposed Design] 以下為演算法式 pseudo-code，不是 Python。Algorithm 1 僅適用 M0，與 problem / label / extension / dominance 文件一致。

```text
Algorithm 1  Capacity-Aware Label Setting Routing (M0)
Input:  Nodes V, contacts C with fixed quotas R, bundle b=(o,d,g,S)
Output: Earliest feasible route P*, hop schedule, and arrival A*
        or NO_FEASIBLE_ROUTE / INVALID_INPUT

 1  if input violates the M0 input domain then return INVALID_INPUT
 2  Build Out[v] = {c in C : sender(c)=v} for all v in V
 3  for each v in V do
 4      Best[v] <- null; Settled[v] <- false
 5  L0 <- Label(v=o, a=g, pred=null, c_in=null, s_in=null)
 6  Best[o] <- L0
 7  U <- empty indexed min-priority queue keyed by (arrival, node_ID)
 8  U.InsertOrDecrease(o, L0)
 9  while U is not empty do
10      L <- U.ExtractMin()
11      v <- L.v
12      Settled[v] <- true
13      if v=d then return Reconstruct(L)
14      for each c in Out[v] in ascending contact_ID do
15          Lnew <- ExtendM0(L,c,b)
16          if Lnew=REJECT then continue
17          w <- Lnew.v
18          if Settled[w] then continue
19          if Best[w] is not null and Best[w].a <= Lnew.a then
20              continue   // existing label dominates or is equivalent
21          Best[w] <- Lnew
22          U.InsertOrDecrease(w,Lnew)
23  return NO_FEASIBLE_ROUTE

Procedure ExtendM0(L,c,b)
 1  if L.v != sender(c) then return REJECT(NODE_MISMATCH)
 2  s <- max(L.a, start(c))
 3  x <- S / rate(c)
 4  f <- s + x
 5  if f > end(c) then return REJECT(WINDOW_INSUFFICIENT)
 6  if R[c] < S then return REJECT(CAPACITY_INSUFFICIENT)
 7  a_new <- f + propagationDelay(c)
 8  return Label(v=receiver(c), a=a_new, pred=L, c_in=c, s_in=s)

Procedure Reconstruct(L)
 1  A* <- L.a; Hops <- empty list
 2  while L.pred is not null do
 3      prepend (L.c_in, L.s_in,
                 L.s_in + S/rate(L.c_in), L.a) to Hops
 4      L <- L.pred
 5  return (contact_IDs(Hops), Hops, A*)
```

REJECT(reason) 是含 reason 的拒絕型別，line 16 判斷所有此類結果。indexed queue 同 node 只留一個 pending entry，故不會有 stale entries。每個 accepted predecessor 在建立 successor 前已 settled，不會被後續替換；Reconstruct 對 o=d 自動得到空路徑。

## 可選 Algorithm 2：M0-Lex

前提：κ_c≥0 為固定 cost、等待免費，其他 M0 假設相同。不是目前預設 objective。

```text
Algorithm 2  Earliest Arrival, Then Minimum Cost (M0-Lex)
Input:  M0 inputs and contact costs kappa[c]
Output: Feasible route minimizing (arrival, total_cost) lexicographically

 1  Validate inputs; N[v] <- empty for each v
 2  Create source label L0 with a=g, z=0, and null predecessor
 3  N[o] <- {L0}; U <- {L0}, ordered by (a,z,stable_ID)
 4  while U is not empty do
 5      L <- U.ExtractMin()
 6      if L is inactive then continue
 7      if L.v=d then return Reconstruct(L), L.z
 8      for each c with sender(c)=L.v do
 9          Lnew <- ExtendM0(L,c,b)
10          if Lnew=REJECT then continue
11          Lnew.z <- L.z + kappa[c]
12          w <- Lnew.v
13          if exists K in N[w] with K.a<=Lnew.a and K.z<=Lnew.z then
14              discard Lnew; continue
15          for each K in N[w] with Lnew.a<=K.a and Lnew.z<=K.z do
16              mark K inactive; remove K from N[w]
17          add Lnew to N[w]; insert Lnew into U
18      mark L processed, retaining it in N[L.v] while non-dominated
19  return NO_FEASIBLE_ROUTE
```

line 13 先處理等價，因此 line 15 的被刪 label 至少一維嚴格較差。inactive predecessor 的儲存物件仍可用來重建，不能連帶破壞已生成 successor。Algorithm 2 不使用 Settled[node]。

## 明確排除

本 pseudo-code 沒有 finite-buffer feasibility 或 departure-time enumeration；若選擇保留舊 PPT 的 buffer 問題，Algorithm 1/2 必須重新設計，不能標為已完成該版本。
