# Ring Road 實驗方法與重現方式

日期：2026-10-11。這是現行程式的初步可行性、規模與資源限制實驗，不是與學長 opt／CGR 的效能比較。

## 演算法與執行版本

- 原版：`src/validation/proposed_v04.py`，未修改。仍含內部 usage cache 及時間枚舉；不是已移除 U 的新實作。
- 執行轉接版本：`src/experiments/compact_search.py`。不更動接收／發送時間、quota、Buffer、dominance、候選時間、排序或終止條件。
- 調整僅限依來源節點索引 Contact、依節點索引 active Labels、不保存從未入列且已被支配的候選紀錄，以及將每一步 Q 複本／完整 trace 改成計數器。
- 被支配但曾入列的 Label 仍保留，供 stale heap 及 pred 回溯；處理過但仍 active 的 Label 照常參與 dominance。
- 原版與轉接版本在 9 案例、開／關 dominance、共 36 次逐包查詢上比對路徑、抵達時間、五項 Label 統計、決策事件及 Q 長度，結果一致。計數器模式也與保留事件模式一致。這是測試證據，不是全輸入形式證明。
- 精簡執行輸出沒有完整 Q 軌跡，不能直接當作現有 GUI 的逐步 trace。原版與原 GUI 保留。

## 拓樸與單位

原始來源與檔案 SHA-256 見 `ring_road_contact_plan_source_v01.md`。

- 移除 Server EID 48 的 12 條 Contact，保留 47 節點、3,172 條有向 Contact，時間 0–86,400 秒。
- 不合併不同 Contact，不刪除短 Contact，不採學長的時間槽切割／刪除規則。
- 全日模式保留全部起訖；短模式只保留觀察範圍內 Contact，跨邊界者截斷並依截斷長度計算容量。因此短模式是另一個明列情境。
- Decimal MB = 1,000,000 Bytes；KB = 1,000 Bytes。原始速率為 0.0125 MB/s；論文速率敏感度組為 0.1 MB/s。
- 時間格點 Δ=1 秒；Bundle 大小 0.3、0.6、1.2 MB。各組傳輸時間均對齊格點；使用 Fraction。
- 傳播延遲 δ=0 是輸入假設。原檔 range 都為零，尚未有真實距離／延遲資料。
- 基準各節點 Buffer 30 MB。接收逐 byte 增加、發送逐 byte 釋放，完整接收後才轉送；來源 Buffer 也依既有程式計入。
- 逐包預約，固定單一目的地。沒有各 Flow 獨立 deadline；觀察終點 T 是共同交付上限。
- Aggregate quota 不檢查共享 Contact 的實際傳送時段；每次均另做重疊診斷，不修復重疊。

## 實驗矩陣

| Profile | 需求 | 用途 |
|---|---|---|
| day | seed=20261011，冷點 7–31、Hot spot 1–6 均勻取整數，release 0–300 秒；需求量組沿用相同前綴 | 隨機需求試跑與可伸縮性界線 |
| short | 衛星 36→6，release=400 秒，T=900；冷點 22→5，release=253 秒，T=1800 | 可查核的路徑與共用資源壓力案例 |
| full_stress | 與 short 相同明列需求，但 T=86400、全部 3,172 條 Contact | 全日輸入上的可查核壓力案例 |

壓力案例設定（12組）：衛星來源包數 1／5／10、5包大小 300／600／1200 KB、5包各節點 Buffer 0.3／0.6／30 MB、5包速率 0.1 MB/s；冷點來源 1／5包，以及只降低中繼節點37 Buffer到0.3／0.6 MB的5包案例。重複的基準組只執行一次。

中繼 Buffer 組是在初次結果發現來源 Buffer 會限制接受包數後追加的診斷；保留原組，不替換不利結果。這些案例是刻意設計的共用資源壓力案例，不代表一般網路流量分布，也不能證明優於其他方法。

## 收集資料與檢查

- 每包：是否接受、節點／Contact 路徑、各跳發送／接收時間、完整抵達時間、送達延遲、hop數、傳輸時間總和與等待時間總和。
- 搜尋：wall time、created／enqueued／expanded／pruned_new／pruned_old、開始時間嘗試數、來源 Buffer 拒絕、延伸 Buffer 拒絕、Contact quota／時間失敗與最大 heap 紀錄數。
- 資源：Buffer 峰值、峰值時間、分段線性回放樣本、共享 Contact 的重疊區間對數。重疊對數不是不同 Contact 的數量。
- 平均／最小／最大／母體標準差：接受包的延遲及每包搜尋時間。拒絕不填0秒；逾時不當成拒絕，也不計整案送達率。
- 每條接受路徑執行獨立完整排程檢查及獨立資源更新，再做多包 Buffer 回放。若出現同模型錯誤，保存證據並停止後續案例，不自行改演算法。
- 全日未使用完整搜尋 oracle；一般性的最早抵達正確性尚未由這次測試證明。
- 另計算「最後一跳抵達下界」：忽略前綴路徑和 Buffer，對剩餘容量足夠的目的地 incoming Contact 求最早完成時間。任何可行路徑都不得早於此值；已驗證路徑達到下界時，僅該次查詢可確定為最早抵達。正的下界差距不是對真正最優值的誤差。若無任何可用最後一跳，才可由此條件證明無路徑。

## 執行環境與時間限制

本機 Windows、Intel Core i7-7700 @3.60GHz、Python 3.12.10。這不是學長 Ubuntu／CPLEX 的執行環境。

初次原版每案例20秒；兩個全日隨機單包重試提高到120秒。精簡版亦保留每組程序時間上限；設定在各次 manifest 中。時間上限涵蓋程序啟動、搜尋、驗證、輸出，不只純搜尋。完整查詢的純搜尋時間另外記錄。

初步批次有重疊執行／其他本機負載，wall time僅作診斷；不能用不同批次的單次時間推導嚴格加速比。正式效能評估須固定環境、串行執行、重複量測並另訂實驗矩陣。

## 重現

先依來源文件下載原檔，置於 `tmp/topology_sources/`；程式會核對 SHA-256，不會重新發布原檔。

```powershell
python -m src.experiments.ring_road --compact --profile short --source tmp/topology_sources/RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt --output output/experiments/my_short_run --budget 20
python -m src.experiments.ring_road --compact --profile full_stress --source tmp/topology_sources/RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt --output output/experiments/my_full_run --budget 120
python -m src.experiments.ring_road --compact --profile day --source tmp/topology_sources/RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt --output output/experiments/my_random_run --budget 120
python -m unittest discover -s tests -p 'test_*.py'
```

輸出目錄必須為新目錄。`--case NAME` 可重複指定少數案例；移除 `--compact` 可用保留詳細 trace 的原版。

完整輸入與 trace／本機log在 `tmp/ring_road_runs/<run_name>/`，不納入 Git；公開摘要在指定 `output/experiments/<run_name>/`。候選 Contact ID 保留原檔中的 Contact 列序號，方便追溯。
