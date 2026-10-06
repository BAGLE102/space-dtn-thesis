# 固定有限 buffer 與逐 byte 占用 v03

範圍：單 bundle query、無背景 buffer 占用、各 node 固定 M_v、每跳單 contact 內不可中斷傳送、完整收完後才能轉送。以下 [C/D] 為依使用者選擇建立的模型與推導，不是 Paper A/B 原文。

## 時間定義

對 contact c_i，s_i 為 sender 發送開始、x_i=S/r_i、f_i=s_i+x_i。constant propagation δ_i 下，receiver 接收開始為 h_i=s_i+δ_i，完整抵達為 a_i=f_i+δ_i。

下一跳 s_(i+1)≥a_i，禁止 cut-through。假設 byte 發送後立即釋放 sender buffer，不保留 custody / retransmission copy；destination 整包交付後釋放。S、M 使用 bytes 或同一倍率單位，r 使用該資料量單位每秒；不能把 bits/s 直接和 MB 混算。

定義 clipped cumulative volume：

\[
H(t;q,r)=\min(S,\max(0,r(t-q))).
\]

對不重訪實體節點的 route，中繼 v_i 的 occupancy：

\[
b_{v_i}(t)=H(t;h_i,r_i)-H(t;s_{i+1},r_{i+1}).
\]

即接收時線性增加，等待時維持 S，發送時線性減少。完整接收前不能發送，故此差值不會為負。

Source：g 之前為 0；t≥g 時 b_o(t)=S-H(t;s_1,r_1)。Destination：接收完成前為 H(t;h_K,r_K)，a_K 交付後為 0；交付前 occupancy 的 supremum 為 S。o=d 時在 generation / local handoff 的整包輸入仍需能容納 S，除非另行定義 bypass storage。

## Buffer 可行性的等價條件

\[
b_v(t)\le M_v\quad\forall t
\quad\Longleftrightarrow\quad
M_v\ge S\quad\text{對 route 上每個 node}.
\]

**必要性：** source 初始持有 S；每個中繼在接收完成且尚未發出下一跳資料時達到 S；destination 完整接收的峰值亦為 S。若 M_v<S，無法完成 store-and-forward 的整包接收。

**充分性：** 該 bundle 在同一 node 的接收、等待、發送 occupancy 始終介於 0 與 S。沒有背景占用且 route 不重訪 node，所以 M_v≥S 就確保整段時間可容納。

每 hop 仍需計算 S/r、window、quota、δ；buffer 這項等價簡化並不使 transmission time 消失。

## 逐 byte 算術範例

S=4 MB、g=0。A→B：window [0,3)、r=2 MB/s、δ=1 s、R=4 MB；B→E：window [5,10)、r=1 MB/s、δ=2 s、R=4 MB。各 node 的 M=4 MB。

| Node | 時間區間 s | Buffer occupancy MB |
|---|---|---|
| A | [0,2] | 4−2t |
| B | [1,3] | 2(t−1) |
| B | [3,5] | 4 |
| B | [5,9] | 4−(t−5) |
| E | [7,11) | t−7 |
| E | 11 起 | 完整交付後為 0；交付前峰值 4 |

整包在 B 的 arrival=3，等待至 5 發送，sender 在 9 傳完、E 在 11 整包收完。

M_B=4 時可行，若改成 3，B 在 t>2.5 且接收未完時便超過容量；延後整個接收時間不會降低必須容納 S 的峰值。

不能把上述例子寫成「逐 byte 所以 M_B=3 也可以接收 4 MB bundle」。那需要 cut-through、外部儲存或 fragmentation 等其他假設，與目前範圍不同。

## 對研究貢獻的意義

finite buffer 應保留在 formulation、輸入與結果驗證中；逐 byte 曲線能驗證佔用語意。但在這個初期版本中，它不造成 time-varying resource trade-off，不能單靠它主張 general multi-resource SPPRC 或 multiple non-dominated labels 的必要性。

contact 的 aggregate R 可以視為外生 quota / allocation，不代表已知背景 bundles 的 buffer footprint。本階段不從 R 建構虛構的 buffer occupation。
