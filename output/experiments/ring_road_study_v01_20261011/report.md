# Ring Road 實驗結果整理

完整一天、3,172 條 Contact：11 組完成、1 組逾時。
這裡的「完成」指該設定全部 Bundle 的搜尋、獨立排程與資源檢查均完成；不代表完成整篇論文的實驗或已證明方法優勢。
採原 frozen v04 的判別式及時間枚舉，精簡版只調整索引及紀錄。內部仍保留 usage cache。

| 案例 | 狀態 | 完成查詢/需求 | 模型接受包數 | 平均延遲(s) | Contact重疊對數 |
|---|---|---:|---:|---:|---:|
| sat_day_n1 | COMPLETE | 1/1 | 1 | 31.0 | 0 |
| sat_day_n5 | COMPLETE | 5/5 | 5 | 31.0 | 10 |
| sat_day_n10 | COMPLETE | 10/10 | 10 | 53.8 | 27 |
| sat_day_size600_n5 | COMPLETE | 5/5 | 5 | 85.4 | 5 |
| sat_day_size1200_n5 | TIMEOUT | 2/5 | — | — | — |
| sat_day_buffer300_n5 | COMPLETE | 5/5 | 1 | 31.0 | 0 |
| sat_day_buffer600_n5 | COMPLETE | 5/5 | 2 | 31.0 | 1 |
| sat_day_thesisrate_n5 | COMPLETE | 5/5 | 5 | 10.0 | 10 |
| cold_day_n1 | COMPLETE | 1/1 | 1 | 1213.0 | 0 |
| cold_day_n5 | COMPLETE | 5/5 | 5 | 1213.0 | 20 |
| cold_transit_buffer300_n5 | COMPLETE | 5/5 | 5 | 2365.0 | 12 |
| cold_transit_buffer600_n5 | COMPLETE | 5/5 | 5 | 2077.0 | 8 |

## 未完成部分

- 5包、每包1200 KB：300秒上限內只完成前2筆查詢，抵達時間為503、603秒；第3筆未完成，不能推論其餘無路徑。已完成部分見該組partial_summary.csv／partial_schedule.csv。
- 隨機單包22→3：原速率及論文速率兩組，用精簡版重試後皆在120秒逾時，沒有得到第一筆查詢的結果。
- 尚未完成學長50–175條Flow的規模、多seed／重複計時或與CGR／opt的公平比較；本次不是完整論文效能評估。

## 如何使用這些結果

- 衛星36→6案例顯示容量不足後改走中繼衛星，以及需求量、Bundle大小、速率對路徑和延遲的影響。
- 冷點22→5案例顯示只降低中繼37 Buffer時，後續Bundle可改走36並較晚抵達；短窗口可能拒絕，全日窗口可能找到替代路徑。逐包結果見各組routes.json。
- Buffer很小且所有節點一起降低時，可能在來源生成就拒絕；不能全部說成中繼Buffer效果。另有僅降低37的組別作診斷。
- 同Contact重疊仍存在，接受比例不等於實際網路送達率。不能拿這些接受結果直接宣稱比CGR好。
- 完成組共接受45包，其中38包達到獨立最後一跳下界，可就該查詢確認最早抵達；其餘沒有本次的最優證明。
- 下界只忽略前綴與Buffer；對其差距不等於對真正最優解的誤差。未執行全日完整搜尋oracle。
- 逾時不當成無路徑；未完成組不計整組接受比例或延遲平均值。先前嘗試與所有逾時紀錄保留於all_attempts.csv。
- wall time來自本機單次／有併行負載的初步執行，只作規模診斷，不能作正式加速比或統計顯著性結論。
- 固定來源的壓力案例不是一般隨機流量；隨機需求試跑與重試另存，不能以這些成功案例取代隨機流量結論。

## 檔案

- full_day_summary.csv：每組設定、完成狀態、延遲統計、Label總數、Buffer峰值與重疊。
- full_day/<case>/summary.csv、schedule.csv、routes.json：每包路徑、抵達及各跳時間。
- full_day/<case>/measurements.json：每包搜尋時間、剪枝、時間嘗試及失敗分類。
- full_day/<case>/bundle_time_breakdown.csv：傳輸／等待時間與最早抵達下界。
- full_day/<case>/buffer_samples.csv、buffer_peaks.json、link_conflicts.json：Buffer曲線及物理限制診斷。
- short_window_summary.csv：短窗口對照；完整短窗口資料保留在原run。
- random_demand_summary.csv／random_demand_manifest.json：隨機需求重試（若提供），與壓力案例分開。
- protocol_manifest.json：明列全部壓力案例需求、節點Buffer例外及來源hash。

研究方法、假設、與學長的差異及重現命令見docs/ring_road_experiment_protocol_v01.md。
