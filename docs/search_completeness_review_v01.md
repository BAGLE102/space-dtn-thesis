# Search completeness review v01

## 目前到底枚舉什麼
每個 label、每個 outgoing contact，枚舉 s∈ΔZ 且 max(a,start)≤s≤end−S/r，並限制 a′≤T。對齊格點的輸入下，這個集合是有限的。沒有只挑 earliest start，也沒有預先排除重訪節點。

每 hop 用時≥x_min>0，所以 route 深度≤floor((T−g)/x_min)。有限 contacts × 有限 start choices 給有限搜尋樹。未 pruning 時每個格點可行排程均逐跳出現在樹上；現有 dominance 保留 suffix 可取代性。依 a 排序取首個目的地可得到格點最優值。這是給定模型的論證，不把有限測例當成一般定理證明。

## 整數輸入也可能有非整數最優發送時間：CE-GRID-01
新 bundle S=4、g=0。A→B=[0,3]、r=4、δ=0、quota=4；B→D=[2,4]、r=4、δ=0、quota=4。M_A=M_D=4、M_B=5，T=4。

B 有先前排程的 4 MB，在 [0,1] 保持 4，於 [1,3] 以 2 MB/s 釋放：O_B(t)=6−2t（1≤t≤3），之後為 0。這可由先前已排定的 B→另一節點 contact 所形成，不是不可實現的 buffer 曲線。該既有 contact 可在固定背景快照外記錄，本 query 的兩條可選 contacts 不受其 quota 影響。

當前包完整抵達 B 的時間 a_B=s+1，必須 O_B(a_B)+4≤5。當 a_B∈[1,3]，得 a_B≥5/2，所以 s≥3/2。s=3/2 時接收段總占用上升至 5，合法；立即由 B 發送 5/2–7/2 亦合法。連續時間最早到達 D=7/2。

Δ=1 時，s=1 會在 B 完整到達 t=2 時占用 2+4=6>5；最早格點 start=2，B arrival=3，D arrival=4。因此 gap=1/2 秒。所有 contact 邊界、S/r 與背景折點均為整數，**光是原始時間對齊，並不保證連續時間最優解落在同一格點**。

這是「格點最優等於連續時間最優」的反例，不是 v04 已限定格點的最優性命題遭推翻。另存可重現 witness；不因此修改 v04 的時間搜尋。

## 是否需要枚舉所有實數
不必把不可數個實數逐一嘗試；可以研究可行 departure intervals／有限事件表示。但要證明代表點不會漏掉對後續有用的 arrival，不能只找到当前 contact 的最早可行 start 就結束。

| Candidate event | 用途 | 單獨是否足夠 |
|---|---|---|
| g、contact start、previous arrival | 最早時序界 | 否 |
| contact end−S/r | 最晚完成界 | 否 |
| reservation / buffer 折點 | 背景曲線區段變化 | 否 |
| 折點減 δ、減 δ+S/r、減 S/r | 收發區間相對事件的對齊 | 仍不夠 |
| O_v(t)=M_v−S 的交點 | 整包容納門檻 | 必須考慮；本例 t=5/2 |
| O_v(t)+接收／釋放線性函數=M_v 的根 | 部分接收／釋放門檻 | 必須考慮，依 rate/start 變化 |
| downstream 限制向上游投影的時間界 | 不漏掉後續所需的到達狀態 | 全域完整性尚待證明 |

## Formal idea（候選方案，未實作／未替換）
對固定 contact sequence 與有限 hop bound，將所有可變傳輸起訖點與既有 buffer 折點的時間順序分成有限個 regimes。在每個 regime 中，曲線與時序可寫成線性不等式，對完整 schedule 求可行 polyhedral regions 與最早 arrival。邊界由線性等式交點生成，不只來自原始 contact timestamps。

此想法說明可能建立有限的精確表示，但不是已完成的 label algorithm：還需處理跳躍事件端點、可行域是否閉合／最小值是否可達、regime 數量、把約束投影成局部 labels 時的資訊損失，以及所有 path/regime 的覆蓋證明。不能直接宣稱只枚舉每條邊的有限端點便足夠。

SIPP 提供「以區間表達動態可行時間」的研究線索，但機器人碰撞模型的保證不能直接移植到逐 byte buffer routing。[作者機構介紹](https://publications.ri.cmu.edu/sipp-safe-interval-path-planning-for-dynamic-environments)

**Search completeness is not yet established.** 這句指一般 continuous-time 版本；有限格點版本有上述條件式論證，並另做 oracle 核對。
