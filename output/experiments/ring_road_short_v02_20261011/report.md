# Ring Road 初步實驗

既有 frozen v04（含 usage cache、時間枚舉）。不是移除 U 後的新實作。
Profile=short；decimal MB；零傳播延遲假設；固定目的地；依需求清單順序規劃。
day使用固定seed 20261011；short/full_stress為預先列出的共用Contact壓力案例，不是隨機代表性流量。
每案例使用獨立程序及相同時間上限。TIMEOUT 不能當成無路徑或拒絕。
完整案例通過獨立排程、資源更新與 Buffer 回放；未對此大型拓樸執行完整搜尋證明最早到達。

| 案例 | 狀態 | 完成查詢/需求 | 接受包數 | 平均送達延遲(s) | Label數 |
|---|---|---:|---:|---:|---:|
| sat_900_n1 | COMPLETE | 1/1 | 1 | 31.0 | 367 |
| sat_900_n5 | COMPLETE | 5/5 | 5 | 31.0 | 1835 |
| sat_900_n10 | COMPLETE | 10/10 | 10 | 53.8 | 4279 |
| sat_900_size600_n5 | COMPLETE | 5/5 | 5 | 85.4 | 1905 |
| sat_900_size1200_n5 | COMPLETE | 5/5 | 2 | 153.0 | 1054 |
| sat_900_buffer300_n5 | COMPLETE | 5/5 | 1 | 31.0 | 367 |
| sat_900_buffer600_n5 | COMPLETE | 5/5 | 2 | 31.0 | 734 |
| sat_900_thesisrate_n5 | COMPLETE | 5/5 | 5 | 10.0 | 2045 |
| cold_1800_n1 | COMPLETE | 1/1 | 1 | 1213.0 | 1369 |
| cold_1800_n5 | COMPLETE | 5/5 | 5 | 1213.0 | 6845 |
| cold_transit_buffer300_n5 | COMPLETE | 5/5 | 1 | 1213.0 | 1373 |
| cold_transit_buffer600_n5 | COMPLETE | 5/5 | 2 | 1213.0 | 2741 |

## 解讀限制

- 原檔速率 0.0125 MB/s，論文速率組採 decimal 0.1 MB/s；不是單位等價。
- 900秒案例只是截取前段且以900秒作交付上限；不能替代一天結果。
- 學長處理多 Flow 聯合最佳化與各自 deadline；本實驗為固定目的地、不可分割 Bundle、逐包預約，因此不是重現學長效能。
- 採相同隨機需求前綴比較需求數，大小實驗沿用相同來源/目的地/生成時間；僅一個seed，不能做一般統計推論。
- 不比較其他演算法，不能據此宣稱優勢；剪枝比例只是搜尋工作量描述。
- 原始需求所需資料量、速率、Buffer與時間範圍詳見manifest；路徑與傳送時間見各案例schedule.csv。
- 平均/最小/最大/母體標準差只對已接受包計算；沒有已知最優值時，最優誤差及誤差百分比為未取得，不填零。
- bundle_time_breakdown的arrival_lower_bound_s忽略路徑前綴及Buffer，只看可承載整包的最後一跳；已驗證路徑等於此下界時，僅該查詢可證最早抵達。正差值不是對真實最優值的誤差。
- Contact時段重疊是aggregate模型的已知物理限制，必須同時報告；不是已驗證可實際執行的網路排程。
- 全量輸入及原始trace保留於tmp/ring_road_runs；正式輸出只保存摘要，未重新發布第三方Contact Plan。
