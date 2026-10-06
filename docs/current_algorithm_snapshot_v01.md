# Current Algorithm Snapshot — frozen v04

2026-10-05。本次原始定義以 `sequential_label_setting_v04.md` 為準；凍結副本與 SHA-256 清單在 `output/validation/`。新程式是對既有 pseudocode 的驗證實作，不替換原始演算法文件。

## Input
- 有限 contacts：ID、u、v、start、end、rate>0、δ≥0、0≤R≤rate×duration。
- 每 node 固定 M≥0；已接受 bundles 所形成的 O_v(t)。搜尋中保持固定。
- 依序處理的 b=(source,dest,g,S>0)；source buffer 亦受限。
- Δ>0、有限 T；release、contact 邊界、S/r、δ 對齊同一時間格點。無 self-loop。

## Label
L=(v,a,U)，U 為本候選 route 各 contact 累積用量；metadata=(pred,c,s)。允許重訪 node/contact，不加 visited-set 限制。

## Extension Rule
對 outgoing contact、每個 s∈ΔZ∩[max(a,start),end−S/r]：f=s+S/r、h=s+δ、a′=f+δ；需 a′≤T。通过後建立 (receiver,a′,U+S e_c)。

## Temporal Constraint
Node continuity；s≥a；s≥start；f≤end。Window 是 sender 發送窗口，不要求 a′≤end。

## Capacity / Quota Constraint
U[c]+S≤R_c；不檢查其他 bundles 的鏈路忙碌時間。沒有提供或隱含 radio contention。

## Buffer Constraint
Sender a–s 占 S，s–f 線性降至 0；receiver h–a′ 線性升至 S。兩端均要求 O(t)+本包占用≤M。label 建立只驗證前綴；下一跳才檢查此節點的後續等待。

## Dominance Rule
同 node/query/snapshot：a1≤a2、O_v(t)+S≤M_v 對整段 [a1,a2]、U1≤U2 componentwise。完全相同保留一個，不能互刪。未使用 FIFO 作全域早到優於晚到的替代論證。

## Objective
最小化整包 destination arrival。沒有 secondary cost，不保證多 bundles 聯合最優。

## Termination Condition
ExtractMin 取出有效 destination label，或 Q 耗盡。每 label 展開一次，不能 settled 整個 node。

## 文件差異／衝突清單
| 文件 | 舊內容 | 本次處置 |
|---|---|---|
| formulation/label/extension/dominance/pseudocode v02 | 無限 buffer M0，earliest-start、單 node label；另有 cost variant | 僅歷史 baseline，不混入 v04 |
| algorithm_design_v03 / buffer_model_v03 | 固定 M 無其他占用，M≥S 即可，循環可由等待替代 | 不適用逐包預約版本 |
| research_scope_v03 | 開頭已註記 v04，但正文仍有「無背景占用」 | 列為歷史敘述衝突，未自行重寫 |
| small_topology_v02 | 單 bundle、不同拓樸 | 本次另建五節點八 contacts 的 walkthrough |
| v04 §6 與 §8 | 說明先時間後 quota，pseudocode 先 quota | 皆為必要檢查；執行 trace 遵照 pseudocode 的短路順序，SKIP 不記作 PASS |

未發現既有 routing code 或 tests；本次在新路徑建立驗證程式與測試。

## 操作化約定與未定義風險
- Contact ID / start time 遞增；heap tie 依建立序，僅為可重現 trace，不新增 objective。
- Fraction 精確有理數。O 為分段線性，固定 s 時檢查所有折點，不以逐秒 buffer sampling 取代全時間檢查。
- 依 v04「交付前檢查峰值再釋放」採事件峰值約定：相同時刻各曲線保留交付前／生成後的點值上界，然後釋放。此約定可能較特定硬體事件排序保守；原文件未完整指定同時生成與交付的先後，相關保證均以此約定為條件，不宣稱物理層唯一語意。
- 測試接收者與 sender 時均只加本候選的一份占用，不把 alternatives 累加。
- 發現同模型 oracle mismatch 時保存資料並關閉後續比較；不自行修補演算法。
