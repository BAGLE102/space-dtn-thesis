# Problem formulation v02

## 範圍與來源

[D] [Proposed Design] 本文件定義待確認的 M0 基礎模型，以便取得一致、可證明的 algorithm。它**不保留舊 PPT 的有限 buffer 保證**；finite buffer 必須另建模型 M1，不可在簡報省略此差異。來源與 A/B 原始符號見 paper_method_mapping_v01.md。新符號避免和 A 的 S=節點集合、B 的 C_l=Mbps 混用。

## 輸入與假設

Contact plan 為有限 contact 集合 C，實體節點集合 V。同一對端點可有多個不同 contact，因此 G=(V,C) 是 temporal directed multigraph，不是 contact-as-vertex graph。

每個 contact 有唯一 ID：

\[
c=(u_c,v_c,t_c^{start},t_c^{end},r_c,\delta_c,Q_c,R_c),\qquad
Q_c=r_c(t_c^{end}-t_c^{start}).
\]

時間以秒、資料量以 MB（decimal）、rate 以 MB/s 計。Q_c 是整個 contact 的總傳輸量，R_c 是搜尋快照下可分配給本 bundle 的資料量上限。要求 start<end、r>0、δ≥0、0≤R≤Q。

Bundle：b=(o,d,g,S)，o,d∈V，g 為整包可用的 generation time，S>0 為全 hop 一致的傳輸量。若 S 只含 payload，後續必須加入 protocol overhead 才能與實際 EVC 比較。

M0 的必要假設：

1. 單 bundle、單一路徑、無 replication、無 fragmentation。
2. 每一跳在同一 contact 內連續傳完；這個 non-preemption 假設比單純 non-fragmentation 更強，需確認。
3. 整包收完才能下一跳發送；忽略 processing / custody delay，或日後明確加到模型。
4. rate、propagation delay 在各 contact 內固定；contact window 限制發送端 serialization，最後一個 bit 抵達可晚於 contact end。
5. buffer 足夠，等待免費且不耗額外受限資源；contacts 已能同時使用，不另外處理 radio / antenna 衝突。
6. R 是本次搜尋固定的 admission quota。window 中沒有另行占用的不可用 transmission intervals，故只要 quota 和 window 都通過，就可安排連續發送。**若 R 是其他 bundle 預約後剩餘 volume，此假設通常不足，必須附 reservation calendar。**
7. 搜尋中候選 labels 互斥，不會因展開候選路徑就更動 global R。真正提交 route 是搜尋後的獨立步驟，需再次檢查快照。

## 路徑、時間與可行性

Contact sequence P=(c_1,…,c_K)，K≥1，滿足：

\[
u_{c_1}=o,\quad v_{c_K}=d,\quad v_{c_i}=u_{c_{i+1}}\;(1\le i<K).
\]

注意這和舊 PPT 第 1、6 頁的 u_(c_i)=v_(c_(i+1)) 方向相反。

令 a_0=g。每一跳：

\[
s_i=\max(a_{i-1},t_{c_i}^{start}),\quad
x_i=S/r_{c_i},\quad f_i=s_i+x_i,\quad
a_i=f_i+\delta_{c_i}.
\]

s_i 是第一個 bit 的發送時刻，f_i 是最後一個 bit 發送完成時刻，a_i 是最後一個 bit 抵達的時刻。Temporal feasibility 要求等待與全跳遞推都有效，且：

\[
f_i\le t_{c_i}^{end},\qquad R_{c_i}\ge S.
\]

等號允許恰好在 window end 傳完，傳輸區間採 [s_i,f_i)。若 contact end 定義為 receiver 端完成接收期限，則必須改成 a_i≤end；不能兩種定義混用。

有限速率使 S/r 不可忽略；propagation delay 只加一次，不能乘 bundle size，也不能直接從 sender window 減去而又重複加在 arrival。

Feasible route 是同時滿足端點、node continuity、所有 temporal / window / quota 條件的 P。M0 中任一可行排程都可沿相同 contacts 左移到上述 earliest-start 排程而不變差，故只枚舉這種排程足夠。[C] 這個論證在有限 buffer 下可能失效。

## Objective 與無解

\[
P^*\in\arg\min_{P\in\mathcal F(b,C,R)} A(P),\quad A(P)=a_K.
\]

因 g 固定，最小化 A(P) 等價最小化 A(P)−g；不是最少 hop，也不是所有 flow 的總延遲。

o=d 時空路徑可行，A(∅)=g。若可行集合為空，回傳 NO_FEASIBLE_ROUTE。在有限 contact plan 外的未知未來不列入此結論。輸入資料不合法回傳 INVALID_INPUT，不能當成網路無解。

可選版本 M0-Lex：每 contact 指定非負固定 cost κ_c，Z(P)=Σκ_c，最小化 (A(P),Z(P)) 的 lexicographic order。cost 必須有用途與單位，例如 hop cost κ=1；不憑空新增 LR multiplier 或 energy constraint。

## 為何 capacity 不是累積 resource

[C] 固定 S 下每條 contact 的 R_c≥S 是 local admissibility。不能把不相同 contacts 的 R 相加，不能在每一跳執行 S←S−R，也不需把整個 residual vector 複製進 label。容量充足的邊可先過濾；剩下是時間依賴 earliest-arrival routing。

無資源占用、全 contacts R=Q 時，window feasibility 已隱含 Q≥S。R<Q 時 quota 檢查可能另外拒絕 route，但仍不是一個隨路徑累積的 resource constraint。

## 真實 reservation 與 finite buffer 的缺口

[D/E] M1 若考慮固定外部 transmission 預約 Ω_c，應定義：

\[
NextFree_c(a,S)=\min\{s\ge\max(a,t_c^{start}):
[s,s+S/r_c)\subseteq[t_c^{start},t_c^{end}),
[s,s+S/r_c)\cap\Omega_c=\varnothing\}.
\]

集合空時不能 extension。接著 a'=NextFree+S/r+δ。若只是固定 calendar 且 buffer 無限制，早到仍能模擬晚到，**精確 calendar 本身也不一定需要 multiple labels**。

例：contact [0,10)、r=1、外部占用 [2,4)、[6,8)，剩餘 volume=6。S=3 雖 R≥S，但最大連續空檔只有 2，non-preemptive 傳送無解。

有限 buffer 必須定義完整占用時間：接收中是否逐 byte 存入、何時釋放 sender 的 copy、發送中是否仍占 buffer、是否有 custody retention。舊 PPT 只檢查等待 [a,s) 不能自動涵蓋完整 store-and-forward 記憶體需求。

即使暫用「到齊後占 S，開始下一跳時立即釋放」的簡化 buffer 語意，earliest-only extension 也可能漏解：S=1、A→B=[0,10)、r=1、δ=0；B→E=[5,6)、r=1；B 在 [1,4) 無 buffer，其他時刻至少 1。A 在 0 時已有 bundle。立刻發送於 1 抵達 B 不可行，但等至 3 發送、4 抵達 B、5 發送至 E 就可行。需要搜尋 departure / safe intervals，不能只往原 pseudo-code 塞 buffer if。

結論：[E] 在 buffer / reservation 語意確認前，M0 只能稱基礎模型的精確方法，不能稱完整資源受限 Space DTN 解法。
