# Extension correctness review v01

本文件檢查 frozen v04 的判別式，不新增條件或修改算法。適用 aggregate quota、固定既有 O、grid start、constant rate/delay、no copies、無 radio contention。必要與充分均相對於此模型。

## Node continuity
每次只從 label.v 的 outgoing contact 延伸，保證資料確實在 sender。下一次 sender 必須等於本次 receiver。這是必要條件；單獨不能保證任何時間或資源可行性。

## Temporal feasibility 與 transmission completion
令 x=S/r>0，s≥max(a,start)，f=s+x≤end，a′=f+δ≤T。因 a 是整包到達，s≥a 保證 store-and-forward；因 rate constant 且不中斷，傳輸量 r(f−s)=S。連續區間 [s,f) 落在 sender window，足以保證本模型的 contact window feasibility。

δ 只影響 receiver 接收時段 [s+δ,f+δ]；完整到達可以晚於 contact end。若實際 contact 定義為接收窗口，這組式子不適用。不存在把 t_end 同時當 sender 與 receiver 截止的混用。

## Capacity / Quota
正確凍結規則是 **U[c]+S≤R_c**，不是每次都只檢 R_c≥S。後者僅在此 prefix 尚未用過 c 時等價。這保證整條候選 route 累積用量不超過快照 quota；搜尋中不同候選不互扣。

不能保證鏈路時間衝突、連續空檔或 radio 排程。此缺口已存在於模型，不以單元測試通過代替 calendar 證明。

## Buffer：局部 extension 為何能組合成完整可行路徑
假設 parent label 對應的過去接收與離開節點皆已檢查。目前 u 完整持有 S；延伸檢查 O_u+S 在 a–s，並檢查 O_u+S−r(t−s) 在 s–f；故等待和逐 byte 釋放均可行。Receiver 檢查 O_v+r(t−s−δ) 在 s+δ–a′，故接收亦可行。

尚未決定 v 的等待期限，因此只建立已完成接收的 label；不可宣稱它已能抵達目的地。下一次 extension 接續檢查其等待／發送，對 route 長度歸納即涵蓋整條路徑。

此歸納使用：之前 sender 最晚在到達目前 node 前已釋放；沒有 custody copies，δ≥0、無 replication、self-loop 排除。重訪舊 node 時，候選本身以前的資料已離開，不會與其未來 visit 重疊。若改這些條件，要重新檢查 state 是否足夠。

固定 s 後，總占用為分段線性；最大值出現在折點或跳躍兩側。實作查每條曲線端點，採事件峰值約定；**不是只在 transmission start/end 或整秒取樣**。

| Constraint | Necessary | Sufficient? | Current Limitation |
|---|---|---|---|
| Node continuity | 是 | 僅對連接關係 | 不代表可排程 |
| s≥a、s≥start | 是 | 對開始時序 | 無 processing delay |
| s+S/r≤end | 是 | 對 sender window 與完整傳輸 | constant rate，未檢 busy intervals |
| U[c]+S≤R_c | 是 | 對 aggregate quota | 不保證 transmission scheduling |
| sender 全段曲線≤M | 是 | 對等待／逐 byte 釋放 | 無發送副本保留 |
| receiver 全段曲線≤M | 是 | 對本次接收 | 不保證下一跳存在 |
| source O(g)+S≤M | 是 | 對生成時放入 buffer | simultaneous events 依 snapshot 約定 |
| s∈ΔZ、a′≤T | 是（限定模型） | 限制搜尋域 | 不是連續時間／無限 horizon 證明 |

結論：在列明條件下可論證 extension 的局部正確性與路徑可行性 invariant；尚需 oracle 核對實作是否忠實，不能由文字論證排除程式錯誤。
