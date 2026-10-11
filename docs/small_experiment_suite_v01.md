# 小型實驗套件 v01

日期：2026-10-11。

## 執行

```powershell
python -m src.experiments.batch --output output/experiments/my_small_suite --figures
```

輸出資料夾必須尚未存在。若只要數值，省略 `--figures`，只需 Python 標準函式庫；繪圖沿用本機既有 matplotlib。自訂案例可複製 `configs/experiments_v01/`，修改JSON與manifest，再指定 `--manifest`。

## 案例與判讀

共8組小型設定檢查與1組已知模型限制示例，每組2包。manifest列出依處理順序的預期完整抵達時間與重疊數，預期值與獨立完整搜尋是分開的檢查。完整搜尋核對有解／無解與最早抵達；路徑相同不是通過條件。

- 01：PPT原始案例。
- 02／03：只改B的Buffer為2／8MB。
- 04：c1剩餘容量改為2MB。
- 05：c2傳播延遲改為2秒。
- 06：c7剩餘容量改為4MB。
- 07：反轉規劃順序，保留生成時間，表示集中規劃的順序敏感度；不是按到達自動排序的線上策略。
- 08：時間格點改為0.5秒。
- 09：兩個2MB bundles共用單一contact，剩餘總容量4MB，但都被排在0–2秒。此例總容量模型內接受，實體鏈路時段不相容；僅記錄，不修正排程。

## 版本與驗證界線

本次不修改 `src/validation/proposed_v04.py`，內部仍有usage cache。Label輸出採c、A、s、pred四欄，但不能稱為已完成移除U的實作。保留時間枚舉，未使用SimPy，未加入transmission calendar、共用radio、協定或遺失／重傳。

這是既有版本的可重現案例驗證，不是論文最終演算法驗證，也不是效能比較。沒有透過這9組構造案例估計真實網路成功率或宣稱方法優於CGR。各案例延遲統計僅含接受包，無路徑不設為0；同一案例的2包不視為獨立隨機重複。

同模型排程、完整搜尋或資源更新不一致時，既有runner保存failure.json；預期結果不一致時保存expectation_failure.json。批次層寫status=STOP與partial_results.json，不處理後續案例，不修改演算法。

## 輸出

`output/experiments/small_suite_v01_20261011/`：

- report.md：9組結果與限制。
- case_summary.csv：接受包數、接受比例、延遲平均／最小／最大／母體標準差、Label數、Buffer峰值與衝突數。
- bundle_summary.csv：路徑、抵達、延遲、Label建立／延伸／刪除數及相對完整搜尋的抵達誤差。
- 每個案例：原始正規化輸入、Contact表、每跳排程、Label／Q事件紀錄與獨立檢查。
- 01_ppt_baseline/report/：兩包路徑圖與Buffer圖。
- test_results.txt：40項測試紀錄。

## 下一步

先確認移除U後的用量取得方式與Dominance定義，才另建新版實作並重跑相同套件。若要驗證實體傳輸行為，再設計獨立SimPy模型及明確的鏈路競爭規則。
