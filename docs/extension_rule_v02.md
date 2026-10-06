# Label extension v02

適用：[D] M0。全域輸入 b=(o,d,g,S)、固定 C/R 已通過資料驗證。Extend(L,c) 回傳一個新 label 或具理由的拒絕。

| Step | 操作 / 判斷 | 失敗的意義 |
|---|---|---|
| 1 | 驗證 L.v=u_c | bundle 不在 contact sender，無法銜接 |
| 2 | 讀 L.a，bundle 必須已完整接收 | M0 把 a 定義成 last-byte arrival，不能用 first-byte time |
| 3 | s=max(L.a,t_start) | 允許等待；若 M1 有 busy calendar，此式須改 NextFree |
| 4 | x=S/r_c | r≤0 是 INVALID_INPUT，不是一般拒絕 |
| 5 | f=s+x；要求 f≤t_end | contact 剩餘時間不足以完整傳送，即使 R 足夠仍不可行 |
| 6 | 要求 R_c≥S | admission quota 不足，不允許只傳部分 bundle |
| 7 | a'=f+δ_c | 非負固定 propagation delay；在 sender-window 語意下不要求 a'≤t_end |
| 8 | L'=(v_c,a',L,c,s) | 留存 predecessor 與 contact；搜尋階段不扣 global R |

M0-Lex 在 step 8 加 z'=L.z+κ_c；κ_c 為固定非負 cost，不是 R。

## Resource extension function 與 FIFO

[C] 令不可行轉移為 +∞：

\[
F_c(a)=\begin{cases}
\max(a,t_c^{start})+S/r_c+\delta_c,& R_c\ge S\ \land\ \max(a,t_c^{start})+S/r_c\le t_c^{end};\\
+\infty,&\text{otherwise}.
\end{cases}
\]

對 a_1≤a_2，若 F_c(a_2) 有限，則 F_c(a_1) 亦有限且不大於它。理由是 max 對 a 單調，而較早開始的 finish 不晚於較晚開始的 finish。這正是 M0 可使用單 label / node 的基礎。

## Capacity accounting

- 搜尋同時保留的 routes 是互斥候選，不應逐 label 扣 R，否則 expansion 順序會改變問題。
- 如成功路徑提交，需要在同一版本資源快照中重新驗證，並對所用 contact 扣 S；有時間預約時也要提交相應 intervals。
- 多 bundle 依序搜尋與提交是 sequential admission，不保證全局 optimum 或公平性。
- M0 的最優解可取無 physical-node cycle 的路徑：回到同節點時更晚，原 label 可等候取得同樣 suffix；因此不用候選內重複扣同一 contact 的 label resource。此論證不能外推到等待受限的 M1。

## Buffer 的必要修正

[E] 舊 PPT 的 buffer 檢查不在本 M0 procedure 中。若保留 finite buffer，必須增加完整 buffer occupancy 模型、可延後發送的 extension，以及相容的 dominance proof；不能宣稱只檢查一次 arrival 或 [a,s) 就完成所有資源限制。
