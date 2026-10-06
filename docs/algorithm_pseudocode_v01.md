# Label Setting 演算法虛擬碼

日期：2026-10-05。搭配 [符號表與公式整理](algorithm_symbols_and_equations_v01.md)。

本文件整理現行 v04 的有限時間格點版本，不修改演算法。已核對 `src/validation/proposed_v04.py`、`model.py` 與 v04 第 8 節；省略追蹤紀錄、統計計數等實作細節。

## 1. 輸入、輸出與前提

**輸入**：contact 集合 C、剩餘可分配資料量 R、節點容量 M、既有占用 O、固定順序的 bundles，以及時間格點間隔 Δ、規劃截止時間 T。

每個 bundle 記為 b = (o, d, g, S)：來源、目的地、生成時間、大小。每個 contact c 包含 (u_c, v_c, α_c, ω_c, r_c, δ_c)。

**輸出**：各 bundle 的可行路徑 P、各跳發送起始時間，以及最早完整到達時間；或回報格點上無可行解。

前提：S > 0、r_c > 0、δ_c ≥ 0；非分割、不中斷、完整接收後轉送、無發送副本、不含 self-loop。資料對齊 Δ；輸入不符合時應回報輸入錯誤，不能偷偷四捨五入。本版本未檢查已排定的鏈路傳輸時段，亦不考慮共用無線電競爭。

## 2. 演算法一：依序處理 bundles

```text
SEQUENTIAL_ROUTING(C, R, M, O, Bundles, Δ, T)

01  檢查輸入與時間格點設定是否合法
02  Results ← 空清單
03
04  for 每個 bundle b，依給定順序 do
05      // 本次搜尋只讀取 R、O；候選路徑不改動它們
06      result ← LABEL_SETTING(C, R, M, O, b, Δ, T)
07
08      if result = NO_ROUTE_ON_GRID then
09          Results 加入 (b, NO_ROUTE_ON_GRID)
10          continue                         // R、O 不變，處理下一包
11
12      (P, starts, arrival) ← result
13      以獨立的完整路徑檢查程序，核對 P 與 starts
14      if 完整路徑檢查失敗 then
15          保存輸入、候選解與失敗原因
16          return VALIDATION_FAILURE        // 停止，不更新資源
17
18      U* ← 計算 P 在各 contact 的累積使用量
19      B* ← 重建本包在各節點的完整占用曲線
20      for 每個 contact c ∈ C do
21          R[c] ← R[c] − U*[c]
22      for 每個節點 v do
23          O_v(t) ← O_v(t) + B*_v(t)
24
25      記錄 P 的發送區間，供後續傳輸時段表版本使用
26      Results 加入 (b, P, starts, arrival)
27
28  return Results
```

第 13～16 行是接受完整路徑前的驗證關卡；不等於每次正式查詢都要執行完整列舉。驗證若發現錯誤，依目前研究要求保留失敗案例，停止後續效能比較，不自行修改演算法。

第 25 行目前只是記錄，不表示搜尋已利用傳輸時段表排除重疊。若從零開始且沒有已接受路徑，初始 O_v(t)=0；若已有合法預約，則保留其占用。

## 3. 演算法二：單包 Label Setting

### 資料結構

- 核心標籤：L = (v, a, U)。U 未記錄的 contact 分量視為 0。
- 重建欄位：pred、incoming_contact、transmission_start。
- active：是否尚未被支配。已展開不等於失效。
- Registry：保存所有已登錄標籤，包含前驅紀錄。
- Q：優先佇列，以 (a, 建立序號) 排序。

```text
LABEL_SETTING(C, R, M, O, b=(o,d,g,S), Δ, T)

01  if O_o(g) + S > M_o then
02      return NO_ROUTE_ON_GRID
03
04  L0 ← (v=o, a=g, U=零向量)
05  L0.pred ← NONE
06  L0.active ← TRUE
07  Registry ← {L0}
08  Q ← 僅含 L0 的最小優先佇列
09
10  while Q 非空 do
11      L ← Q 取出 a 最小的標籤；同時刻依建立序號
12      if L.active = FALSE then
13          continue
14
15      if L.v = d then
16          (P, starts) ← RECONSTRUCT(L, Registry)
17          return (P, starts, L.a)
18
19      for 每個滿足 u_c = L.v 的 contact c，依固定 ID 順序 do
20          if L.U[c] + S > R[c] then
21              continue
22
23          first ← max(L.a, α_c)
24          last  ← ω_c − S/r_c
25          if first > last then
26              continue
27
28          for s = first, first+Δ, first+2Δ, …，且 s ≤ last do
29              N ← EXTEND(L, c, s, S, R, M, O, Δ, T)
30              if N = INFEASIBLE then
31                  continue
32
33              Existing ← Registry 中 active=TRUE 且節點為 N.v 的標籤
34
35              if 存在 K ∈ Existing，使 DOMINATES(K,N,S,M,O)=TRUE then
36                  捨棄 N，不加入 Q
37                  continue
38
39              for 每個 K ∈ Existing do
40                  if DOMINATES(N,K,S,M,O)=TRUE then
41                      K.active ← FALSE
42                      // 保留 K 的紀錄，既有子標籤仍可能用它回溯
43
44              N.active ← TRUE
45              指派 N 的固定建立序號
46              Registry 登錄 N
47              Q 加入 N
48
49  return NO_ROUTE_ON_GRID
```

### 這段程式中最重要的五點

1. 第 19 行列舉可延伸的 contacts；第 28 行列舉發送起始時刻。不是只試最早可發送時間。
2. first 在目前輸入對齊前提下已是格點。EXTEND 另檢查到達是否超過 T。也可用公式表 F10 表達可嘗試時刻集合；此處保留目前程式的檢查順序。
3. Existing 不只包含仍在 Q 的標籤，也包含已展開但尚未失效的標籤。
4. 先檢查舊標籤是否支配 N，再用 N 標記舊標籤失效。相同 a、U 時保留既有代表，避免兩者互刪。
5. 不設「整個節點已處理完成」的旗標。同一節點可以有多個到達時間與已用量不同的標籤。

被支配的標籤可以留在 Q，等取出時跳過；這只是佇列管理方式。標記前驅失效不會連帶刪掉所有後代，回溯時仍可讀取其歷史紀錄。

## 4. 演算法三：標籤延伸

```text
EXTEND(L=(u,a,U), c, s, S, R, M, O, Δ, T)

01  if u_c ≠ u then
02      return INFEASIBLE
03  if s 不屬於允許的時間格點 then
04      return INFEASIBLE
05
06  x  ← S/r_c
07  f  ← s + x
08  h  ← s + δ_c
09  a' ← f + δ_c
10
11  if s < max(a, α_c) or f > ω_c or a' > T then
12      return INFEASIBLE
13  if U[c] + S > R[c] then
14      return INFEASIBLE
15
16  定義發送端本包占用 send(t)：
17      send(t) = S                    ，a ≤ t ≤ s
18      send(t) = S − r_c(t−s)         ，s ≤ t ≤ f
19
20  if BUFFER_OK(O_u, send, [a,f], M_u) = FALSE then
21      return INFEASIBLE
22
23  定義接收端本包占用 recv(t)：
24      recv(t) = r_c(t−h)             ，h ≤ t ≤ a'
25
26  if BUFFER_OK(O_vc, recv, [h,a'], M_vc) = FALSE then
27      return INFEASIBLE
28
29  U' ← 複製 U
30  U'[c] ← U[c] + S
31  N ← (v=v_c, a=a', U=U')
32  N.pred ← L 的識別碼
33  N.incoming_contact ← c
34  N.transmission_start ← s
35  return N
```

第 3 行明列上層格點列舉所保證的前提，不是新增搜尋限制。接收完成只建立「本包已完整到達此節點」的標籤；在中繼節點接下來能等多久，由下一次延伸檢查。若為目的地，也必須先檢查交付前的完整接收峰值。

## 5. 演算法四：支配判斷

```text
DOMINATES(L1, L2, S, M, O)

01  // 只比較同一次 bundle 搜尋中的標籤
02  if L1.v ≠ L2.v then
03      return FALSE
04  if L1.a > L2.a then
05      return FALSE
06
07  for 每個 contact c do
08      if L1.U[c] > L2.U[c] then
09          return FALSE
10
11  v ← L1.v
12  wait(t) ← S，定義於 [L1.a, L2.a]
13  if BUFFER_OK(O_v, wait, [L1.a,L2.a], M_v) = FALSE then
14      return FALSE
15
16  return TRUE
```

TRUE 表示 L1 可以取代 L2：更早或同時到達、能持有整包等到 L2 的時間、各 contact 已用量不更多。這是目前模型的充分條件，不是只看誰比較早，也不是最強的支配規則。

## 6. 輔助程序：全區間 buffer 檢查

```text
BUFFER_OK(O_v, added, I=[left,right], M_v)

01  E ← I 的端點，以及 O_v、added 在 I 內的所有折點與事件時刻
02  對不連續事件，納入事件點值與 I 內必要的左右極限
03  // 點值沿用現行「生成後／交付前峰值，再釋放」的約定
04
05  for 每個評估位置 ξ ∈ E do
06      if O_v(ξ) + added(ξ) > M_v then
07          return FALSE
08
09  return TRUE
```

因總占用在相鄰折點間為線性，只需檢查這些位置。現行程式用精確有理數與保留事件峰值的分段曲線表示，不是每隔 Δ 秒取樣 buffer。曲線相鄰兩段在交界描述同一份占用，不可重複相加。

## 7. 輔助程序：路徑回溯

```text
RECONSTRUCT(L, Registry)

01  Hops ← 空清單
02  while L.pred ≠ NONE do
03      Hops 加入 (L.incoming_contact, L.transmission_start)
04      L ← Registry[L.pred]
05  將 Hops 順序反轉
06  return Hops 的 contact 序列與發送起始時間序列
```

來源等於目的地時，來源容量檢查通過後，第一個取出的標籤就是目的地；回傳零跳路徑與到達時間 g。

## 8. 可直接放進 PPT 的精簡版

```text
輸入：bundle (o,d,g,S)、C、R、O、M、Δ、T
輸出：最早完整到達路徑與發送時間，或格點上無解

1  若來源無法容納整包，回報格點上無解
2  建立 L0=(o,g,0)，加入優先佇列 Q
3  while Q 非空：
4      取出到達時間最早的有效標籤 L
5      若 L 位於目的地，回溯並回傳路徑
6      對 L 的每個 outgoing contact c：
7          若 U[c]+S > R[c]，跳過 c
8          對窗口內每個格點發送時刻 s：
9              檢查時間、容量及兩端整段 buffer 占用
10             若可行，建立新標籤 N
11             若既有有效標籤支配 N，捨棄 N
12             否則標記被 N 支配的標籤失效，將 N 加入 Q
13 回報格點上無解

外層：完整路徑驗證通過後，更新 R、O，再搜尋下一包。
```

## 9. 講解時應明確說明

- **列舉的位置**：嘗試每個 contact，再嘗試每個格點發送起始時間。
- **資源更新的位置**：外層接受完整路徑之後；搜尋候選期間不更新。
- **停止的位置**：從優先佇列取出有效的目的地標籤，不是第一次產生目的地標籤。
- **buffer 的檢查範圍**：發送端的等待與逐 byte 釋放，以及接收端的逐 byte 接收。
- **結果的範圍**：目前單包、固定先前預約、有限時間格點模型；不保證多包聯合最佳，也不代表連續時間或鏈路傳輸時段衝突已被解決。

虛擬碼是現行規則的整理，不是新增的一般性正確性證明。若 walkthrough、獨立列舉驗證或反例顯示同模型錯誤，依既定要求保留案例，停止後續效能比較，再提出候選修正供確認。

