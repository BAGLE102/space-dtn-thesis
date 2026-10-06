# Dominance correctness review v01

## 命題：continuation preservation
在同 query/snapshot/node，若 a1≤a2、U1≤U2 且 O_v(t)+S≤M_v 對所有 t∈[a1,a2]，則 L2 每個可行 continuation 都可由 L1 以不更晚的目的地 arrival 完成。

## 證明
取任意 L2 的可行後綴，其第一跳 start s≥a2。L1 先在 v 等至 a2：此段由 dominance 的等待條件保證。從 a2 起，完整複製 L2 的每個 contact 及 start time。

時間／window 完全相同；第一跳 sender 的 a2–s 占用均為 S，後續接收與釋放曲線相同。其他前綴不保留 future copies，所以不會新增隱藏 buffer 占用。對每個 contact c，若後綴用量為 W[c]，則 U1[c]+W[c]≤U2[c]+W[c]≤R_c。因此 quota 全部可行；最終 arrival 與 L2 相同。

這是 suffix-copy 論證，不需要假定有 time-varying buffer 的網路具有「無條件早到較好」的 FIFO。等待判別式提供這一對 labels 的可取代性。

## Required Conditions for Safe Dominance
| Required condition | Current model satisfies? | 如不成立的風險 |
|---|---|---|
| 同 node、bundle、resource snapshot | 是，固定每次 query | 不同 S 或預約不能比較 |
| 在 a1–a2 可持有整包 | 顯式檢查 | 早到等待越過 buffer 高峰 |
| U componentwise 不更多 | 顯式檢查 | 重複花掉同 contact quota |
| Prefix 無尚未釋放的 future copies | 由 no-copy / 完整接收假設成立 | 需要記錄歷史 footprint |
| 允許等待且不另耗 energy/cost | 是 | 可能不能複製 suffix |
| 無 simple-path、hop budget 等額外歷史限制 | 是，不強制無循環 | suffix 可能重訪 L1 prefix node |
| 候選分支不修改全域 O/R | 是 | label 可比較性失效 |
| 原始 labels 已有可行前綴 | 由 extension invariant | 可由無效 label 錯刪可行解 |
| 等價 labels 保留一個穩定代表 | 實作先查 dominator 再刪 others | 互刪導致無解 |

## Remaining Risk
- 這是保守充分條件，不是必要條件；比較已過期 contacts 的 U 可能阻止原本可做的 pruning。不能為效率而未經確認移除 U。
- 同時生成／交付的精確事件排序未由原始文檔完整定義；目前依已記錄的峰值約定做條件式證明。
- 不能由 dominance 定理推得 continuous-time successor enumeration 已完整。
- 目的地立即交付時，等待到晚到時刻不是必須；原規則仍是充分但可能過度保守，本次不強化。

網頁一般 dominance 的核心也是「每個可行後續存在不更差的替代」，其 time/cost 示範不是本題可直接照抄的 buffer 規則。[Haarbach SPPRC](https://www.adrian-haarbach.de/idp-graph-algorithms/implementation/spp-rc-label-setting/index_en.html)

結論：在上述假設下可給出 continuation-preservation 證明；原規則本身目前沒有在此推導中出現反例。這不等於所有實作都正確，待 independent oracle 及 ON/OFF 核對。
