# Label Setting 演算法：符號表與公式整理

日期：2026-10-05。對應目前研究進度簡報與 v04 的離散時間驗證版本。

本文件只統一符號與整理既有定義，**不修改演算法**。範例採目前簡報的五節點、八個 contacts，第一包於第 8 秒到達，第二包於第 12 秒到達；不混用早期 v04 小範例的 7 秒與 10 秒。

## 1. 使用前提

- 每次搜尋一個不可分割的 bundle，多個 bundles 依固定順序處理。
- 同一跳須在單一 contact 內連續送完整包；完整接收後才能轉送。
- 逐 byte 接收、逐 byte 釋放已送出的資料，不保留發送副本。
- 每個節點的 buffer 上限固定；既有占用由先前接受的路徑形成。
- 每次搜尋期間，剩餘可分配資料量與既有占用函數保持不變。
- 固定傳輸速率、非負傳播延遲；排除節點連到自己的 contact，但不禁止路徑重訪節點。
- 目前只搜尋有限時間格點；只檢查總可分配資料量，尚未檢查已排定的鏈路傳輸時段。

## 2. 符號表

### 2.1 網路與輸入資料

| 符號 | 名稱與定義 | 單位／範圍 |
|---|---|---|
| \(V\) | 節點集合 | 集合 |
| \(C\) | 通訊機會（contact）集合；同一對節點可有多個 contacts | 集合 |
| \(c\) | 一個有獨立 ID 的 contact | \(c\in C\) |
| \(u_c,v_c\) | contact \(c\) 的發送端與接收端 | 節點 |
| \(\alpha_c,\omega_c\) | contact 的發送窗口開始、結束時間；對應程式 `start`、`end` | 秒 |
| \(r_c\) | contact 的固定傳輸速率 | MB/s |
| \(\delta_c\) | contact 的傳播延遲（propagation delay） | 秒 |
| \(R_c\) | 本次搜尋開始時，contact 尚可分配的資料量；不是速率，也不是剩餘秒數 | MB |
| \(M_v\) | 節點 \(v\) 的 buffer 容量上限 | MB |
| \(O_v(t)\) | 時刻 \(t\)，先前已接受之 bundles 在節點 \(v\) 的既有 buffer 占用量 | MB |
| \(t\) | 用來檢查占用曲線的時間；不只限於格點 | 秒 |
| \(\Delta\) | 搜尋發送起始時間所採的格點間隔 | 秒，\(\Delta>0\) |
| \(T\) | 本次規劃允許的最晚完整到達時間 | 秒，有限 |
| \(\mathcal G_\Delta\) | 允許的時間格點集合 | 見式 F02 |

### 2.2 Bundle、路徑與標籤

| 符號 | 名稱與定義 | 單位／範圍 |
|---|---|---|
| \(o,d\) | 本次 bundle 的來源與目的地；不用 \(s\) 表示來源，以免與發送時間混淆 | 節點 |
| \(g\) | bundle 生成時間 | 秒 |
| \(S\) | 本次 bundle 的完整大小；各跳相同，不切割 | MB，\(S>0\) |
| \(P=(c_1,\ldots,c_m)\) | 候選路徑的 contact 序列；\(m\) 是跳數 | 序列 |
| \(\boldsymbol s=(s_1,\ldots,s_m)\) | 候選路徑各跳的發送起始時間 | 秒 |
| \(L=(v,a,U)\) | 搜尋標籤（label） | 狀態 |
| \(v\) | 標籤目前所在節點 | 節點 |
| \(a\) | 本包在目前節點的完整到達時間 | 秒 |
| \(U[c]\) | 此標籤對應的候選路徑，目前已使用 contact \(c\) 的累積資料量 | MB |
| \(\boldsymbol 0\) | 每一個 contact 的已用量皆為 0 的向量 | MB |
| \(e_c\) | contact \(c\) 分量為 1，其餘分量為 0 的單位向量 | 無單位 |
| \(Q\) | 依完整到達時間排序的優先佇列 | 標籤集合 |
| \(\mathcal F_\Delta\) | 滿足目前所有限制的格點路徑與發送時間安排 | 可行解集合 |

重建路徑另需 `pred`（前一個標籤）、`incoming_contact`（本跳 contact）、`transmission_start`（本跳發送起始時間）。它們不是額外最佳化目標。

### 2.3 單跳時間與占用曲線

| 符號 | 名稱與定義 | 單位 |
|---|---|---|
| \(x_c\) | 本包經 contact \(c\) 的傳輸時間（transmission delay） | 秒 |
| \(s\) | 發送開始時間 | 秒 |
| \(f\) | 發送完成時間：最後一個 byte 離開發送端 | 秒 |
| \(h\) | 接收開始時間：第一個 byte 抵達接收端 | 秒 |
| \(a'\) | 接收完成時間：最後一個 byte 抵達接收端 | 秒 |
| \(w\) | 本包在目前節點完整收妥後的等待時間 | 秒 |
| \(b_u^{\mathrm{send}}(t)\) | 本次延伸在發送端造成的本包占用量 | MB |
| \(b_v^{\mathrm{recv}}(t)\) | 本次延伸在接收端造成的本包占用量 | MB |
| \(B_v^{P,\boldsymbol s}(t)\) | 選定完整路徑與發送時間後，本包在節點 \(v\) 的完整占用曲線 | MB |
| \(\mathcal E(I)\) | 區間 \(I\) 內須檢查的端點、折點與事件時刻，包含必要的左右極限 | 時間點集合 |

**三個量不要混用：** \(R_c\) 是 contact 的剩餘可分配資料量；\(U[c]\) 是本候選路徑的已用量；\(O_v(t)\) 是先前 bundles 的 buffer 占用量。其他候選路徑不會加進 \(U\) 或 \(O\)。

## 3. 輸入與目標

### F01：輸入基本條件

\[
r_c>0,\qquad \delta_c\ge0,\qquad
0\le R_c\le r_c(\omega_c-\alpha_c),\qquad M_v\ge0.
\tag{F01}
\]

\(r_c(\omega_c-\alpha_c)\) 是該發送窗口的理論資料量上限；不可直接把已扣除預約後的 \(R_c\) 當成這個乘積。

### F02：有限時間格點

\[
\mathcal G_\Delta=\{k\Delta:k\in\mathbb Z,\ 0\le k\Delta\le T\}.
\tag{F02}
\]

目前設定生成時間、contact 邊界、\(S/r_c\)、\(\delta_c\) 對齊同一格點。**限制在格點的是發送時間選擇；buffer 仍檢查整段時間，不是只在整秒取樣。**

### F03：最早完整到達目標

\[
\min_{(P,\boldsymbol s)\in\mathcal F_\Delta} A_d(P,\boldsymbol s),
\qquad A_d(P,\boldsymbol s)=a_m.
\tag{F03}
\]

\(a_m\) 為最後一跳的完整到達時間。來源等於目的地時，先通過來源容量檢查，再以 \(g\) 為到達時間。此目標只針對當前這一包，不是多包聯合最佳化，也沒有額外 cost。

## 4. 初始化與單跳時間

### F04：來源容量與起始標籤

\[
O_o(g)+S\le M_o,
\qquad L_0=(o,g,\boldsymbol0).
\tag{F04}
\]

來源容量不符即結束本次查詢，不扣除任何資源。

### F05：路徑銜接

\[
u_{c_1}=o,\qquad
v_{c_i}=u_{c_{i+1}}\ (1\le i<m),\qquad
v_{c_m}=d.
\tag{F05}
\]

在標籤延伸中，只選擇 \(u_c=L.v\) 的 outgoing contacts，自然維持這項條件。

### F06：整包傳輸時間

\[
x_c=\frac{S}{r_c}.
\tag{F06}
\]

這是將整包送上鏈路所需的時間；與傳播延遲 \(\delta_c\) 不同。

### F07：發送與接收時刻

\[
f=s+x_c,\qquad h=s+\delta_c,\qquad
a'=f+\delta_c=s+\frac{S}{r_c}+\delta_c.
\tag{F07}
\]

發送區間為 \([s,f)\)，接收區間為 \([h,a')\)。接收完成當下仍須檢查整包占用峰值。

### F08：等待時間與單跳經過時間

\[
w=s-a\ge0,\qquad
a'-a=w+\frac{S}{r_c}+\delta_c.
\tag{F08}
\]

這只是 F07 的時間分解，不代表額外加入等待 cost。等待可能使後續不可行，不能因為沒有費用就忽略。

### F09：時間可行性

\[
s\in\mathcal G_\Delta,\qquad
s\ge\max(a,\alpha_c),\qquad
s+\frac{S}{r_c}\le\omega_c,\qquad
s+\frac{S}{r_c}+\delta_c\le T.
\tag{F09}
\]

目前 contact 定義為**發送窗口**，所以檢查 \(f\le\omega_c\)，不是要求 \(a'\le\omega_c\)。完整到達可以晚於 contact 結束，但不能超過 \(T\)。

### F10：要列舉的發送起始時間集合

\[
\mathcal S_c(L)=\mathcal G_\Delta\cap
\left[\max(a,\alpha_c),
\min\left(\omega_c-\frac{S}{r_c},\ T-\frac{S}{r_c}-\delta_c\right)\right].
\tag{F10}
\]

集合為空，該 contact 無可嘗試的時刻；非空則逐一檢查其中每個 \(s\)。這就是演算法內「列舉」的主要位置。此集合只處理時間，尚未通過容量與 buffer 檢查。

## 5. Contact 容量

### F11：本次延伸的容量判別式

\[
U[c]+S\le R_c.
\tag{F11}
\]

等價於 \(S\le R_c-U[c]\)。只有目前路徑尚未用過這個 contact、即 \(U[c]=0\) 時，才能簡化成 \(S\le R_c\)。

### F12：候選已用量與新標籤

\[
U'=U+S e_c,\qquad L'=(v_c,a',U').
\tag{F12}
\]

也就是 \(U'[c]=U[c]+S\)，其他 contact 分量保持原值。這不是更新全域的 \(R_c\)。

## 6. 逐 byte 緩衝區限制

以下從標籤 \(L=(u,a,U)\) 經 \(c=(u,v,\ldots)\) 延伸，先固定一個候選 \(s\)。

### F13：發送端新增占用

\[
b_u^{\mathrm{send}}(t)=
\begin{cases}
S, & a\le t\le s,\\
S-r_c(t-s), & s\le t\le f.
\end{cases}
\tag{F13}
\]

在 \(t=s\) 兩式都等於 \(S\)，在 \(t=f\) 等於 0。第一段是等待，第二段是逐 byte 釋放。此局部曲線只定義本次待檢查的 \([a,f]\)，不能把它當成整條路徑的完整占用。

### F14：發送端全時段容量檢查

\[
O_u(t)+b_u^{\mathrm{send}}(t)\le M_u,
\qquad \forall t\in[a,f].
\tag{F14}
\]

### F15：接收端新增占用

\[
b_v^{\mathrm{recv}}(t)=r_c(t-h),
\qquad h\le t\le a'.
\tag{F15}
\]

因為 \(a'-h=S/r_c\)，所以 \(b_v^{\mathrm{recv}}(h)=0\)，\(b_v^{\mathrm{recv}}(a')=S\)。

### F16：接收端全時段容量檢查

\[
O_v(t)+b_v^{\mathrm{recv}}(t)\le M_v,
\qquad \forall t\in[h,a'].
\tag{F16}
\]

通過只表示能完成這次接收；若 \(v\ne d\)，接收後的等待與發送要在下一次延伸中檢查。若 \(v=d\)，先檢查交付前的接收峰值，再釋放本包。

### F17：分段線性占用的實際檢查方式

對 F14 或 F16 的總占用 \(H(t)=O(t)+b(t)\)，分段線性時可改查：

\[
\sup_{t\in I}H(t)
=\max_{\xi\in\mathcal E(I)}H(\xi)
\le M.
\tag{F17}
\]

\(\mathcal E(I)\) 包含區間端點、所有曲線折點，以及跳躍事件的點值與區間內的左右極限；\(\xi\) 在此也包含這些單側評估。不能只檢查 \(s,f\)，也不能只檢查整秒。

**事件約定：**目前驗證版本採生成後／交付前的峰值再釋放。同時生成與交付可能因此較某些硬體事件排序保守；相關結果以此約定為前提。

## 7. 支配關係（Dominance）

同一次 bundle 搜尋、同一份 \(R,O\)，比較同節點的 \(L_1=(v,a_1,U_1)\)、\(L_2=(v,a_2,U_2)\)。

### F18：三個條件須同時成立

\[
\boxed{\begin{aligned}
a_1&\le a_2,\\
O_v(t)+S&\le M_v &&\forall t\in[a_1,a_2],\\
U_1[c]&\le U_2[c] &&\forall c\in C.
\end{aligned}}
\tag{F18}
\]

成立時，\(L_1\) 可以等到 \(a_2\)，再沿用 \(L_2\) 的後續發送安排，因此可以刪除 \(L_2\) 而不失去它能提供的最佳結果。

這是目前模型下的**充分條件**，不是最強或必要的支配條件。只比較 \(a_1\le a_2\) 不足夠。當 \(a_1=a_2\) 且 \(U_1=U_2\) 時，只保留一個固定代表，不能兩者互相刪除。

## 8. 搜尋順序與終止

### F19：每次取出最早的有效標籤

\[
L_{\mathrm{next}}\in
\arg\min_{L\in Q_{\mathrm{active}}} a(L).
\tag{F19}
\]

\(Q_{\mathrm{active}}\) 是佇列中尚未失效的標籤。同時刻以固定建立順序處理，只為可重現，不新增次要最佳化目標。

### F20：延伸後完整到達時間嚴格增加

\[
a'-a=(s-a)+\frac{S}{r_c}+\delta_c>0.
\tag{F20}
\]

使用 \(S>0,r_c>0,s\ge a,\delta_c\ge0\)。有限 contacts、有限規劃時間及格點，再加上正的最小每跳時間，使候選路徑數有限；不代表多項式效率。

終止規則：取出目的地的有效標籤即回溯解；佇列耗盡則只回報「本時間格點上無可行解」。**不能把後者直接解讀為連續時間問題無解。**

## 9. 接受完整路徑後的資源更新

### F21：完整路徑在各 contact 的累積用量

\[
U^*[c]=S\sum_{i=1}^{m}\mathbf1\{c_i=c\}.
\tag{F21}
\]

\(\mathbf1\{\cdot\}\) 是指示函數：條件成立為 1，否則為 0；重複使用同一 contact 要重複計量。

### F22：接受後更新 contact 剩餘資料量

\[
R_c^{\mathrm{new}}=R_c^{\mathrm{old}}-U^*[c].
\tag{F22}
\]

### F23：接受後更新節點既有占用

\[
O_v^{\mathrm{new}}(t)=O_v^{\mathrm{old}}(t)
+B_v^{P^*,\boldsymbol s^*}(t).
\tag{F23}
\]

星號表示已接受的解。\(B\) 必須由完整路徑重建，不可把多個候選標籤或重複的區段端點任意相加。沒有找到解時，\(R,O\) 都不更新。

### F24：中繼節點單次停留的完整占用

對第 \(i\) 跳接收後，再由第 \(i+1\) 跳發送的中繼節點：

\[
B^{(i)}(t)=
\begin{cases}
0,&t<h_i,\\
r_{c_i}(t-h_i),&h_i\le t<a_i,\\
S,&a_i\le t<s_{i+1},\\
S-r_{c_{i+1}}(t-s_{i+1}),&s_{i+1}\le t\le f_{i+1},\\
0,&t>f_{i+1}.
\end{cases}
\tag{F24}
\]

這是 F13、F15 沿完整路徑拼接後的寫法，不是額外的演算法條件。重訪同節點時，將各次停留曲線合成為 \(B_v^{P,\boldsymbol s}(t)\)。相鄰區段交界是同一份資料，不重複累加。

來源：在 \(g\) 生成整包，\([g,s_1)\) 保持 \(S\)，之後以 F13 釋放。目的地：用 F15 接收，\(t=a_m\) 檢查 \(S\) 的峰值，\(t>a_m\) 不再保留。來源等於目的地的零跳情況，於 \(g\) 檢查生成／交付峰值。

## 10. 目前簡報範例的式子

以下 \(S=4\) MB、\(r=4\) MB/s，故每跳 \(x=S/r=1\) 秒，且 \(M_B=4\) MB。

### E01：第一包的到達時間

\[
a_B=2+4/4+0=3,\qquad
a_D=6+4/4+1=8.
\tag{E01}
\]

路徑為 \(X\xrightarrow{c1}B\xrightarrow{c2}D\)。

### E02：第一包在 B 的占用

\[
O_B(t)=
\begin{cases}
0,&t<2,\\
4(t-2),&2\le t<3,\\
4,&3\le t<6,\\
4(7-t),&6\le t\le7,\\
0,&t>7.
\end{cases}
\tag{E02}
\]

這是在第一包接受後、第二包開始搜尋時使用的既有占用。

### E03：第二包早到 B 後等待會超限

\[
O_B(2.5)+S=4(2.5-2)+4=6>4=M_B.
\tag{E03}
\]

因此第 2 秒到 B 的標籤不能一直等到後續 c5 的發送時刻。

### E04：第二包較晚抵達 B 的兩個標籤

\[
a_1=8\le9=a_2,\qquad
O_B(t)+4=4\le M_B\quad(8\le t\le9),\qquad U_1=U_2.
\tag{E04}
\]

兩者都使用 c4，因此第 8 秒標籤滿足三項支配條件，可取代第 9 秒標籤。

### E05：第二包選定路徑與到達時間

\[
a_B=7+4/4+0=8,\qquad
a_D=10+4/4+1=12.
\tag{E05}
\]

路徑為 \(A\xrightarrow{c4}B\xrightarrow{c5}D\)。第二包接受後：

\[
R_{c4}^{\mathrm{new}}=8-4=4,\qquad
R_{c5}^{\mathrm{new}}=4-4=0.
\tag{E06}
\]

第二包在 B 的占用為：

\[
B_B^{(2)}(t)=
\begin{cases}
0,&t<7,\\
4(t-7),&7\le t<8,\\
4,&8\le t<10,\\
4(11-t),&10\le t\le11,\\
0,&t>11.
\end{cases}
\quad
\sup_t\bigl(O_B(t)+B_B^{(2)}(t)\bigr)=4\le M_B.
\tag{E07}
\]

## 11. 尚未納入的式子：傳輸時段衝突

設 \(\mathcal I_c\) 是 contact \(c\) 已排定的傳輸區間集合；這是本節才使用的未來擴充符號。

\[
[s,f)\cap[p,q)=\varnothing,
\qquad \forall[p,q)\in\mathcal I_c.
\tag{N01：尚未實作}
\]

對半開區間，等價於每筆預約滿足 \(f\le p\) 或 \(q\le s\)。首尾相接不算重疊。

這項限制**目前沒有加入搜尋**，不能把它列成現行演算法已通過的檢查。若不同 contacts 共用同一個無線電，還需要另外定義共用資源的互斥限制。

目前總容量條件與排程可行性並不等價：剩餘空檔為 \([0,1),[2,3),[4,5)\)，\(r=1\) MB/s，則 \(R=3\) MB。即使 \(S=2\le R\)，仍沒有長度 \(S/r=2\) 秒的連續空檔。

## 12. 可放入 PPT 的核心公式總表

| 項目 | 核心公式 | 意義 |
|---|---|---|
| 標籤 | \(L=(v,a,U)\) | 節點、完整到達時間、各 contact 已用量 |
| 傳輸時間 | \(x_c=S/r_c\) | 整包不可分割且連續傳送 |
| 接收完成 | \(a'=s+S/r_c+\delta_c\) | 最後一個 byte 抵達時間 |
| 時間 | \(s\ge\max(a,\alpha_c),\ f\le\omega_c,\ a'\le T\) | 收完才轉送，並滿足窗口與截止時間 |
| 格點 | \(s\in\mathcal G_\Delta\) | 目前只搜尋離散起始時刻 |
| Contact 容量 | \(U[c]+S\le R_c\) | 候選路徑累積使用量不超限 |
| Buffer | \(O(t)+b(t)\le M\)，全區間成立 | 檢查接收、等待與發送 |
| 支配 | \(a_1\le a_2\)、可等待、\(U_1\le U_2\) | 三條件同時成立才可取代 |
| 資源更新 | \(R^{new}=R^{old}-U^*\)、\(O^{new}=O^{old}+B^*\) | 僅接受完整路徑後更新 |
| 目標 | \(\min A_d\) | 當前單包的最早完整到達 |

## 13. 來源與尚未證明的範圍

- 定義：[sequential_label_setting_v04.md](sequential_label_setting_v04.md) 第 5～8 節。
- 驗證約定：[current_algorithm_snapshot_v01.md](current_algorithm_snapshot_v01.md)。
- 延伸檢查：[extension_correctness_review_v01.md](extension_correctness_review_v01.md)。
- 範例數據：`output/validation/walkthrough_input.json` 與 `walkthrough_trace.json`。
- 本整理不新增一般性正確性證明；既有小案例一致性不代表所有輸入已被證明。
- 連續時間候選起始時刻的完整性，以及納入傳輸時段表後的搜尋方法，仍未完成。

