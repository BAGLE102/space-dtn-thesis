# 現行研究問題、參數與演算法正式定義 v01

日期：2026-10-06  
狀態：現行 v04 的統一定義；未修改演算法  
適用範圍：中央依序規劃、有限時間格點、aggregate contact quota、有限 buffer

## 1. 問題名稱

中文工作名稱：

> **具有 Aggregate Contact Quota 與有限緩衝區之不可分割 Bundle 依序最早到達路由問題**

英文工作名稱：

> **Sequential Earliest-Arrival Routing for Unsplittable Bundles with Aggregate Contact Quotas and Finite Buffers**

「有限時間格點」是目前求解版本的重要限制，論文中首次介紹問題時應直接寫明。這個名稱描述目前實際求解的問題，不代表已建立文獻新穎性。

## 2. 一句話問題定義

在已知 contact plan、固定 bundle 處理順序，以及先前已接受 bundles 所形成的 contact 剩餘 quota 與節點 buffer 預約下，對目前的一個不可分割 bundle，尋找一條路徑及各跳的格點發送時間，使整包符合 contact 時窗、傳輸時間、aggregate quota 與全時段 buffer 容量限制，並最小化最後一個 byte 抵達目的地的時間。

## 3. 系統模型與研究假設

### 3.1 網路架構

- 網路是具有可預測 contacts 的 Space DTN。
- 系統採中央規劃模式；中央端保存 contact plan 及已接受 bundles 的資源預約。
- 中央端依給定順序逐一處理 bundles。
- 每次只求解目前 bundle 的路徑；已接受路徑才會更新資源。
- 節點依中央端提供的路徑與發送時間執行 store-and-forward。

中央架構是本研究假設。現行演算法沒有建模控制訊息傳送、狀態回報、指令延遲或執行偏差。

### 3.2 Bundle 假設

- Bundle 不可分割（unsplittable / non-fragmented）。
- 每一跳必須在單一 contact 內連續送完整包，不允許暫停後恢復。
- 中繼節點必須完整接收 bundle，才能開始下一跳傳送。
- 發送期間資料逐 byte 離開發送端 buffer；接收期間逐 byte 進入接收端 buffer。
- 發送端不保留 custody 或 retransmission copy。
- Bundle 在目的地完整接收並檢查峰值後立即交付，因此不再占用本研究所計算的 buffer。

最後兩項是理想化的 buffer 生命週期假設，不應寫成所有 BP 實作的一般事實。

### 3.3 Contact 假設

- 每個 contact 是具有固定傳輸方向、發送窗口、固定資料速率及固定傳播延遲的通訊機會。
- Contact window 定義為發送端可傳送資料的時間範圍。
- 最後一個 byte 必須在 contact end 前離開發送端；它可在 contact end 後抵達接收端。
- 現行模型沒有 packet loss、retransmission、unexpected contact failure、processing delay、protocol overhead、clock offset 或 guard time。
- 現行模型沒有不同 contacts 共用同一 radio 的互斥限制。

### 3.4 現行 quota 的精確語意

\(R_c\) 是本次 query 開始時，contact \(c\) 尚可分配的**總資料量**。它不是剩餘時間，也不表示資料可在哪些時段傳送。

因此目前問題只保證：

\[
\text{候選路徑在 contact }c\text{ 上的累積資料量}\le R_c.
\]

目前不保證：

\[
\text{不同已接受 bundles 的實際傳輸區間彼此不重疊。}
\]

所以現行輸出應稱為「aggregate-quota 模型下的路徑與發送時間安排」，不能稱為已保證可執行的完整鏈路排程。

## 4. 問題輸入

### 4.1 網路與 contact plan

令實體節點集合為：

\[
V=\{v_1,v_2,\ldots,v_n\}.
\]

令 contact 集合為 \(C\)。每個 contact \(c\in C\) 定義為：

\[
c=(u_c,v_c,\alpha_c,\omega_c,r_c,\delta_c),
\]

其中：

| 符號 | 定義 | 單位／條件 |
|---|---|---|
| \(u_c\) | contact \(c\) 的發送節點 | \(u_c\in V\) |
| \(v_c\) | contact \(c\) 的接收節點 | \(v_c\in V\)，且 \(u_c\ne v_c\) |
| \(\alpha_c\) | 發送窗口開始時間 | 秒 |
| \(\omega_c\) | 發送窗口結束時間 | 秒，\(\alpha_c<\omega_c\) |
| \(r_c\) | 固定傳輸速率 | MB/s，\(r_c>0\) |
| \(\delta_c\) | 固定 propagation delay | 秒，\(\delta_c\ge0\) |

物理 contact 的理論資料量為：

\[
Q_c=r_c(\omega_c-\alpha_c).
\]

\(Q_c\) 是由速率與窗口推得的理論總量；它與扣除預約後的 \(R_c\) 不同。

### 4.2 Contact 資源狀態

| 符號 | 定義 | 單位／條件 |
|---|---|---|
| \(R_c\) | 本次 query 的 contact 剩餘 aggregate quota | MB，\(0\le R_c\le Q_c\) |

所有 \(R_c\) 在單次 bundle 搜尋期間保持固定。候選 labels 彼此是不同方案，不會互相扣除 \(R_c\)。

### 4.3 節點 buffer

| 符號 | 定義 | 單位／條件 |
|---|---|---|
| \(M_v\) | 節點 \(v\) 的 buffer 容量上限 | MB，\(M_v\ge0\) |
| \(O_v(t)\) | 先前已接受 bundles 在時刻 \(t\) 對節點 \(v\) 的既有預約占用 | MB，\(O_v(t)\ge0\) |

\(O_v(t)\) 是單次 query 的固定背景函數。現行實作以分段線性曲線表示，並假設輸入的背景占用本身來自合法的既有預約。

### 4.4 Bundle

目前 bundle \(b\) 定義為：

\[
b=(o,d,g,S),
\]

其中：

| 符號 | 定義 | 單位／條件 |
|---|---|---|
| \(o\) | bundle source | \(o\in V\) |
| \(d\) | bundle destination | \(d\in V\) |
| \(g\) | bundle generation / release time | 秒 |
| \(S\) | bundle 完整資料量 | MB，\(S>0\) |

多個 bundles 以有序序列表示：

\[
\mathcal B=(b_1,b_2,\ldots,b_m).
\]

此順序是輸入，不是演算法決定的結果。現行問題不最佳化 bundle 處理順序。

### 4.5 時間格點與規劃期限

| 符號 | 定義 | 單位／條件 |
|---|---|---|
| \(\Delta\) | 可選發送時間的格點間隔 | 秒，\(\Delta>0\) |
| \(T\) | 本次 query 的最晚完整到達時間 | 秒，有限 |
| \(\mathcal G_\Delta\) | 可使用的發送時間集合 | \(\{k\Delta:k\in\mathbb Z,0\le k\Delta\le T\}\) |

目前要求 \(g\)、contact boundaries、\(S/r_c\) 與 \(\delta_c\) 對齊同一格點。這是格點問題的輸入限制，不是連續時間最佳性的證明。

## 5. 決策輸出

對目前 bundle，演算法選擇：

1. Contact 序列：

\[
P=(c_1,c_2,\ldots,c_K).
\]

2. 各跳發送開始時間：

\[
\boldsymbol s=(s_1,s_2,\ldots,s_K),\qquad s_i\in\mathcal G_\Delta.
\]

3. 最後一個 byte 抵達目的地的時間：

\[
A_d(P,\boldsymbol s).
\]

如果沒有滿足所有限制的 \((P,\boldsymbol s)\)，輸出：

\[
\texttt{NO\_ROUTE\_ON\_GRID}.
\]

這只表示指定 \(\Delta\)、\(T\) 與 aggregate-quota 模型中無解，不表示原連續時間或實際排程問題無解。

## 6. 單跳時間定義

對第 \(i\) 跳 contact \(c_i\)，令：

\[
x_i=\frac{S}{r_{c_i}}
\]

為傳送完整 bundle 所需時間。定義：

\[
f_i=s_i+x_i,
\]

\[
h_i=s_i+\delta_{c_i},
\]

\[
a_i=f_i+\delta_{c_i}
=s_i+\frac{S}{r_{c_i}}+\delta_{c_i}.
\]

| 符號 | 意義 |
|---|---|
| \(s_i\) | 第 \(i\) 跳開始發送時間 |
| \(f_i\) | 最後一個 byte 離開發送端的時間 |
| \(h_i\) | 第一個 byte 抵達接收端的時間 |
| \(a_i\) | 最後一個 byte 抵達接收端的時間 |

## 7. 可行路徑限制

### 7.1 路徑銜接

\[
u_{c_1}=o,
\]

\[
v_{c_i}=u_{c_{i+1}},\qquad i=1,\ldots,K-1,
\]

\[
v_{c_K}=d.
\]

### 7.2 Store-and-forward

第一跳不得早於 bundle generation：

\[
s_1\ge g.
\]

後續跳必須等上一跳完整接收：

\[
s_{i+1}\ge a_i,qquad i=1,\ldots,K-1.
\]

### 7.3 Contact window

每一跳必須在 contact 發送窗口內送完：

\[
s_i\ge\alpha_{c_i},
\]

\[
f_i=s_i+\frac{S}{r_{c_i}}\le\omega_{c_i}.
\]

因 \(\omega_c\) 是 sender window，所以不要求 \(a_i\le\omega_{c_i}\)。

### 7.4 規劃期限

\[
a_K\le T.
\]

### 7.5 Aggregate quota

同一條候選路徑可能重複使用 contact。對每個 \(c\in C\)：

\[
S\sum_{i=1}^{K}\mathbf 1\{c_i=c\}\le R_c.
\]

這是累積資料量限制，不是傳輸區間互斥限制。

### 7.6 Buffer 限制

令 \(B_v^{P,\boldsymbol s}(t)\) 表示目前 bundle 在選定路徑與排程下，於節點 \(v\) 的占用量。所有節點及所有相關時間必須滿足：

\[
O_v(t)+B_v^{P,\boldsymbol s}(t)\le M_v,
\qquad \forall v\in V,\ \forall t\in[0,T].
\]

對一次由節點 \(u\) 經 contact \(c=(u,v,\ldots)\) 的延伸，若 bundle 於 \(a\) 完整位於 \(u\)，並於 \(s\) 開始發送，則發送端新增占用為：

\[
b_u^{\mathrm{send}}(t)=
\begin{cases}
S, & a\le t\le s,\\
S-r_c(t-s), & s\le t\le f.
\end{cases}
\]

接收端新增占用為：

\[
b_v^{\mathrm{recv}}(t)=r_c(t-h),
\qquad h\le t\le a'.
\]

其中：

\[
f=s+S/r_c,\qquad h=s+\delta_c,\qquad a'=f+\delta_c.
\]

延伸必須同時滿足：

\[
O_u(t)+b_u^{\mathrm{send}}(t)\le M_u,
\qquad \forall t\in[a,f],
\]

\[
O_v(t)+b_v^{\mathrm{recv}}(t)\le M_v,
\qquad \forall t\in[h,a'].
\]

目前採「生成後／交付前先檢查峰值，再釋放」的事件約定。

## 8. 最佳化目標

令 \(\mathcal F_\Delta\) 為符合第 7 節全部限制的格點可行解集合。目標為：

\[
\min_{(P,\boldsymbol s)\in\mathcal F_\Delta}
A_d(P,\boldsymbol s).
\]

目前沒有 secondary cost、hop count、energy 或 fairness objective。

此目標只保證：在處理目前 bundle 前固定的 \(R\) 與 \(O\) 下，求目前 bundle 的格點最早完整到達解。它不保證整個 bundle 序列的聯合最佳解。

## 9. Label 定義

現行核心 label 為：

\[
L=(v,a,U).
\]

| 欄位 | 定義 | 為何需要 |
|---|---|---|
| \(v\) | bundle 目前完整所在的節點 | 決定可使用哪些 outgoing contacts |
| \(a\) | bundle 在 \(v\) 完整接收的時間 | 決定下一跳最早起送時間及 buffer 等待區間 |
| \(U[c]\) | 此候選前綴在 contact \(c\) 的累積使用量 | 防止候選路徑重複使用同一 contact 時重複花費 quota |

\(U\) 的數學型態是以 contacts 為索引的非負數值向量：

\[
U\in\mathbb R_{ge0}^{|C|}.
\]

實作可使用稀疏 mapping，只保存非零分量。例如：

\[
U=\{c_4:4,c_5:4\}
\]

表示目前前綴在 \(c_4\) 與 \(c_5\) 各使用 4 MB；未列出的 contact 用量皆為 0。它不是一般集合，也不是其他候選方案已占用的資源。

每個 label 另保存以下路徑重建資料：

| 欄位 | 定義 |
|---|---|
| `pred` | 產生目前 label 的前一個 label |
| `incoming_contact` | 本次延伸使用的 contact |
| `transmission_start` | 本次延伸的發送開始時間 |

這三項不參與目前 dominance 比較，但用來重建完整路徑與發送時間。

## 10. Label Extension 定義

從 label：

\[
L=(u,a,U)
\]

經 outgoing contact：

\[
c=(u,v,\alpha_c,\omega_c,r_c,\delta_c)
\]

延伸。可嘗試的起送時間集合為：

\[
\mathcal S_c(L)=\mathcal G_\Delta\cap
\left[
\max(a,\alpha_c),
\min\left(
\omega_c-\frac{S}{r_c},
T-\frac{S}{r_c}-\delta_c
\right)
\right].
\]

對每個 \(s\in\mathcal S_c(L)\)：

1. 計算

\[
f=s+S/r_c,\quad h=s+\delta_c,\quad a'=f+\delta_c.
\]

2. 檢查候選前綴 quota：

\[
U[c]+S\le R_c.
\]

3. 檢查發送端在 \([a,f]\) 的完整 buffer 曲線。

4. 檢查接收端在 \([h,a']\) 的完整 buffer 曲線。

5. 全部通過後建立：

\[
U'=U+S e_c,
\]

\[
L'=(v,a',U').
\]

其中 \(e_c\) 是 contact \(c\) 分量為 1、其他分量為 0 的單位向量。

## 11. Dominance 定義

只能比較同一次 query、相同 \(R/O\) 狀態、相同節點的兩個 labels：

\[
L_1=(v,a_1,U_1),\qquad
L_2=(v,a_2,U_2).
\]

若以下三項同時成立，則 \(L_1\) 支配 \(L_2\)：

\[
a_1\le a_2,
\]

\[
O_v(t)+S\le M_v,
\qquad \forall t\in[a_1,a_2],
\]

\[
U_1[c]\le U_2[c],
\qquad \forall c\in C.
\]

第一項表示 \(L_1\) 不晚到；第二項表示它可以安全等待至 \(a_2\)；第三項表示它在任何 contact 上都沒有使用更多 quota。因此 \(L_1\) 可先等到 \(a_2\)，再複製 \(L_2\) 的任一可行後續安排。

這是安全的充分條件，不是必要條件，也不是已證明最強的 pruning 規則。

當 \(a_1=a_2\) 且 \(U_1=U_2\) 時，兩者對現行未來可行性等價，只保留一個穩定代表。

## 12. 演算法定義

### 12.1 單一 bundle 搜尋

```text
FINITE_GRID_LABEL_SETTING(C, R, M, O, b, Delta, T)

Input:
    contact plan C
    fixed aggregate quotas R
    node capacities M
    fixed booked occupancy O
    bundle b=(o,d,g,S)
    time-grid interval Delta and horizon T

Output:
    feasible contact sequence, start times and earliest complete arrival
    or NO_ROUTE_ON_GRID

1   if O_o(g)+S > M_o:
2       return NO_ROUTE_ON_GRID

3   create L0=(o,g,zero-vector)
4   Q <- min-priority queue ordered by complete arrival a
5   insert L0 into Q and the label registry

6   while Q is not empty:
7       L <- remove the active label with minimum arrival
8       if L is inactive:
9           continue
10      if L.v = d:
11          reconstruct and return its path, starts and arrival

12      for each contact c with u_c = L.v:
13          if L.U[c]+S > R_c:
14              continue

15          for each s in S_c(L), in increasing order:
16              compute f, h and a_new
17              check sender occupancy throughout [L.a,f]
18              check receiver occupancy throughout [h,a_new]
19              if any check fails:
20                  continue

21              create N=(v_c,a_new,L.U+S e_c)
22              save pred, incoming contact and start time

23              if an active same-node label dominates N:
24                  discard N
25                  continue

26              mark every active same-node label dominated by N inactive
27              register N and insert N into Q

28  return NO_ROUTE_ON_GRID
```

### 12.2 多 bundle 依序處理

```text
SEQUENTIAL_RESERVATION(C, R, M, O, ordered bundles, Delta, T)

1   for each bundle b in the given order:
2       freeze the current R and O for this query
3       result <- FINITE_GRID_LABEL_SETTING(C,R,M,O,b,Delta,T)

4       if result = NO_ROUTE_ON_GRID:
5           record rejection under the current grid model
6           do not change R or O
7           continue

8       independently validate the returned complete path
9       if validation fails:
10          preserve the case and stop

11      reconstruct the chosen route's complete contact usage U_star
12      reconstruct its complete node-occupancy curves B_star
13      R_c <- R_c-U_star[c] for every contact c
14      O_v(t) <- O_v(t)+B_star_v(t) for every node v
15      record the accepted route and continue with the next bundle
```

這裡的資源更新仍是 aggregate quota 與 buffer occupancy。現行演算法沒有更新或檢查 transmission calendar。

## 13. Queue 與終止規則

優先佇列 \(Q\) 依 label 的完整到達時間 \(a\) 由小到大排列。同時到達的 labels 以固定建立順序處理，僅用於重現，不構成新的最佳化目標。

搜尋必須在「有效目的地 label 從 \(Q\) 取出」時終止，不能在第一次產生目的地 label 時終止。

搜尋也不能將整個實體節點永久 settled。相同節點可能需要保留多個 arrival／usage 狀態。

## 14. 正確性主張的精確範圍

目前可以主張：

> 在輸入符合既定格點、有限 horizon、固定 aggregate quota、合法既有 buffer 預約、無發送副本、逐 byte 收發、完整接收後轉送及現行事件約定時，演算法搜尋有限格點可行解，並以安全的 dominance 充分條件刪除可被取代的 labels。現有小型完整搜尋未發現同模型答案差異。

目前不能主張：

- 已求得一般連續時間問題的最早到達解。
- 已保證不同 bundles 在 contact 上的傳輸時段不重疊。
- 已處理共用 radio、半雙工、packet loss、retransmission 或 contact failure。
- 已求得全部 bundles 的聯合最佳解或公平處理順序。
- 已證明方法比 CGR、SABR 或 contact splitting 更快或更好。
- 使用 Label Setting 本身具有研究新穎性。

## 15. 現行模型與未來 Transmission Calendar 模型的界線

若未來要保證不可中斷傳輸的實際鏈路排程，需另外定義每個 contact 已接受的傳輸區間集合：

\[
\Omega_c=\{[p_1,q_1),[p_2,q_2),\ldots\}.
\]

候選傳送區間還必須滿足：

\[
[s,f)\cap[p,q)=\varnothing,
\qquad \forall[p,q)\in\Omega_c.
\]

這個條件目前尚未加入演算法。加入後必須重新檢查：

- 起送時間生成是否完整；
- label state 是否足夠；
- dominance 是否仍能複製後續安排；
- 完整搜尋參考是否採相同 calendar 模型；
- 多 contacts 共用 radio 時是否需要額外資源集合。

本節只標示下一版本的問題邊界，不是已確認或已實作的修改。

## 16. 參數、決策與狀態的分類總表

| 類別 | 符號／資料 | 說明 |
|---|---|---|
| 固定網路輸入 | \(V,C,u_c,v_c,\alpha_c,\omega_c,r_c,\delta_c\) | Contact plan |
| Query 前資源輸入 | \(R_c,M_v,O_v(t)\) | 剩餘 aggregate quota 與既有 buffer 預約 |
| Bundle 輸入 | \(o,d,g,S\) | 目前查詢的來源、目的地、生成時間與大小 |
| 搜尋範圍輸入 | \(\Delta,T\) | 格點間隔與規劃期限 |
| 決策輸出 | \(P,\boldsymbol s\) | Contact 序列與各跳發送時間 |
| 目標值 | \(A_d(P,\boldsymbol s)\) | 目的地完整到達時間 |
| Label state | \(v,a,U\) | 目前節點、完整到達時間、候選前綴用量 |
| 重建資料 | `pred`, `incoming_contact`, `transmission_start` | 重建完整路徑與排程 |
| 搜尋資料結構 | \(Q\)、label registry、active flag | 搜尋與 stale label 管理 |
| 接受後更新 | \(R^{new},O^{new}\) | 供下一個 bundle query 使用 |
| 尚未實作 | \(\Omega_c\) | Contact 已接受傳輸區間集合 |

## 17. 可直接放入論文的問題敘述

> 本研究考慮具有已知 contact plan 的中央規劃 Space DTN。每個 contact 具有發送端、接收端、發送時間窗口、固定傳輸速率及傳播延遲；每個節點具有固定緩衝區容量。多個不可分割 bundles 依給定順序逐一規劃，已接受 bundles 形成後續查詢所使用的 contact 剩餘 aggregate quota 及隨時間變化的節點緩衝區預約。對每一個 bundle，本研究於有限時間格點中選擇 contact 序列與各跳發送時間，使 bundle 在每一跳皆能於單一 contact 內連續傳送完成，並滿足完整接收後轉送、contact 時窗、累積 quota 及全時段緩衝區限制。最佳化目標為最小化該 bundle 最後一個 byte 抵達目的地的時間。完整路徑被接受後，中央規劃器更新 quota 與緩衝區預約，再處理下一個 bundle。本版本未使用 contact transmission calendar，因此其保證限定於 aggregate-quota 模型，不包含已接受傳輸區間的互斥排程保證。

## 18. 與其他現行文件的關係

- 本文件是現行問題、參數與演算法的統一入口。
- 詳細式子及逐 byte 曲線推導見 `algorithm_symbols_and_equations_v01.md`。
- 可執行層級虛擬碼見 `algorithm_pseudocode_v01.md`。
- 原始研究規則見 `sequential_label_setting_v04.md`。
- 實作對照見 `current_algorithm_snapshot_v01.md`。
- 條件式正確性與已知反例見 `algorithm_validation_summary_v01.md`。
- 現實性、新穎性及實驗風險見 `research_reality_audit_v01.md`。

若本文件與舊 M0、v02 或 v03 文件衝突，以本文件、`sequential_label_setting_v04.md` 及 `current_algorithm_snapshot_v01.md` 所描述的現行 aggregate-grid 模型為準。
