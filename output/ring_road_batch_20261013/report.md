# Ring Road擴充批次測試

共14組、規劃330包；206包已完成獨立核對，124包尚未完成。9組完整完成，5組在整個驗證流程的20秒上限被中止。
待測Label Setting未修改，保留全部Label；每組由自己的空預約狀態開始，使用學長報告速率100KB/s、零傳播延遲假設。

| 案例 | 要求包數 | 已核對 | 可行 | 無路徑 | 未處理 | 狀態 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| load_10 | 10 | 10 | 9 | 1 | 0 | COMPLETE |
| load_20 | 20 | 20 | 9 | 11 | 0 | INCOMPLETE_TIMEOUT |
| load_50 | 50 | 21 | 9 | 12 | 29 | INCOMPLETE_TIMEOUT |
| load_100 | 100 | 21 | 9 | 12 | 79 | INCOMPLETE_TIMEOUT |
| size_200KB | 20 | 20 | 4 | 16 | 0 | COMPLETE |
| size_500KB | 20 | 20 | 1 | 19 | 0 | COMPLETE |
| size_1000KB | 20 | 20 | 0 | 20 | 0 | COMPLETE |
| corridor_20_5 | 10 | 10 | 9 | 1 | 0 | COMPLETE |
| corridor_29_1 | 10 | 10 | 9 | 1 | 0 | COMPLETE |
| corridor_25_3 | 10 | 10 | 9 | 1 | 0 | COMPLETE |
| corridor_19_3 | 10 | 10 | 9 | 1 | 0 | COMPLETE |
| mixed_sources_20 | 20 | 13 | 7 | 6 | 7 | INCOMPLETE_TIMEOUT |
| buffer_200KB | 20 | 20 | 2 | 18 | 0 | COMPLETE |
| window_20s | 10 | 1 | 1 | 0 | 9 | INCOMPLETE_TIMEOUT |

## 如何解讀

- COMPLETE：全組查詢、核對與輸出都完成。INCOMPLETE_TIMEOUT：工作流程超時，不代表未處理的包都無路徑。
- load_20的20包個別查詢都已核對，但後續彙整尚未完成便超時，仍保留整組INCOMPLETE標記。
- 100KB、10秒兩跳走廊最多在本例送達9包；第10包仍有contact容量，但無法在截止前完成兩跳，不能說成容量不足。
- 200KB每跳需2秒，500KB需5秒，1MB需10秒；10秒時窗內送達數降低是傳輸時間與期限的作用，不是效能優勢。
- 四組其他來源使用不同時間片段的20→5、29→1、25→3、19→3；都是依Contact Plan選出的已知可銜接走廊，不是隨機代表性流量。
- mixed_sources_20交替使用9→2及7→2，來源7在這段時間沒有到目的地2的銜接路徑；它是不可達需求的診斷測試。
- buffer_200KB刻意把每節點Buffer從學長30MB降為0.2MB，測試同時生成需求的來源等待占用；不是學長原參數，也不是中繼Buffer壓力的完整研究。
- 各組按固定順序規劃；未輪到規劃的bundle不預先加入Buffer，低Buffer結果適用此預約語意。
- 所有其他案例維持30MB Buffer。每組保留47節點及時窗內全部活動contacts／方向／循環，窗口以外資料不參與；容量按裁切窗口重算。
- 超時包含待測搜尋、獨立完整列舉、檢查與輸出，沒有拆分階段計時，不能把它當作路由演算法的執行時間比較。
- 已核對206包的可行性及最早抵達時間皆與獨立完整列舉一致；沒有同模型反例。未完成124包不宣稱任何答案。
- 20項相關測試通過。未進行整天實驗、演算法效能比較、分散控制或實體收發器互斥模擬。

## 檔案

- batch_summary.csv：所有組別與完成／未完成計數。
- delay_statistics.csv：成功包延遲平均、最小、最大、母體標準差及對完整列舉的抵達誤差；未完成組只統計已核對部分。
- 完整組子資料夾：summary.csv、schedule.csv、verification.json及報告。
- 未完成組子資料夾：partial_status.json、worker_status.json、partial_verified_queries.json。worker_status可能保留中止前的RUNNING快照，以外層INCOMPLETE為最終狀態。
- configs/ring_road_batch_20261013/：事先列明的14組設定與20秒上限。
- tmp/ring_road_batch_20261013/：本機完整輸入、每包Label／候選／預約與執行log。

## 下一步

先選擇需要補完的50／100包或較長時窗，增加驗證時間預算。若要研究Buffer效益，應另設能實際形成中繼等待壓力的情境，不能把本批結果當作已完成。

## 重現命令

以下三個目錄必須尚不存在：

```powershell
python -m src.ppt_validation.ring_road_batch --source tmp/topology_sources/RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt --configs configs/ring_road_batch_rerun --local tmp/ring_road_batch_rerun --output output/ring_road_batch_rerun --seconds 20
```

原始來源及SHA見既有來源核對文件。20秒完成的查詢數會隨機器負載變動，不保證重現相同的未完成數；固定輸入下，已完成查詢的可行性與抵達答案才是核對目標。
