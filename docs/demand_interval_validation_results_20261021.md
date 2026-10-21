# 按需區間元件：驗證過程與結果

日期：2026-10-21。詳細設計見 `docs/demand_interval_validation_method_20261021.md`。

## 結論先行

**有限度支持「減少無關區間計算」這個方向，尚不足以確立論文突破。** 在人工控制只查詢 10% contacts 的情境，按需增量明顯減少工作；查詢全部 contacts 時沒有可靠優勢。這是工作量避免的元件證據，不是優於原論文、完整搜尋最優性或新穎性的證據。

## 實際執行順序

1. 讀取專案凍結 v04、snapshot 與最新 PPT 候選紀錄，確認舊枚舉程式不能作為新方法實作。
2. 另建立隔離元件，只處理單 contact 的可行起送集合 J；不改舊 routing、PPT、Q 或 dominance。
3. 以 Fraction 實作事件分段與線性不等式交集；不使用時間格點產生 J。
4. 九個解析案例先核對預期集合。
5. 執行 100 個隨機小例的 9,307 次固定 s 檢查，無差異。
6. 七種 workload、三個 correctness seeds 下，四策略共 22,320 次查詢答案對照，無差異。
7. 五個單元測試通過，包含 sender／receiver／contact／size／deadline 失效與故意漏版本的負控制。
8. 先暖機，再對七情境×四策略各計時七次，合計 196 筆原始時間；順序固定種子打亂。
9. 另行量測每個情境／策略的 Python 追蹤配置峰值，保存統計與逐步 query trace，產生圖表。

執行命令：

```powershell
python -m unittest tests.test_demand_interval_validation -v
python -m src.experiments.demand_interval_validation --contacts 96 --epochs 5 --repeats 7
python -m src.experiments.report_demand_interval_validation output/demand_interval_validation_20261021
```

## 數值結果

96 contacts、24 nodes、5 個資源快照。時間是五個快照的總時間中位數，不是每包路由時間。「增量全量」也有版本快取，因此不是故意只選最弱對照。

| 查詢情境 | 增量全量 ms | 按需增量 ms | 對照／按需時間比 | 重算次數：對照→按需 |
|---|---:|---:|---:|---|
| 10% contacts、局部更新 | 228.056 | 28.443 | 8.018× | 129→13 |
| 50% contacts、局部更新 | 225.643 | 115.966 | 1.946× | 137→69 |
| 100% contacts、局部更新 | 211.385 | 239.450 | 0.883× | 129→129 |
| 10% contacts、全部更新 | 857.634 | 99.360 | 8.632× | 480→50 |
| 100% contacts、全部更新 | 945.185 | 928.059 | 1.018× | 480→480 |
| 10% contacts、size 改變 | 916.603 | 108.614 | 8.439× | 480→50 |
| 10% contacts、較多折點 | 462.966 | 60.273 | 7.681× | 131→18 |

### 如何判讀

- 少量查詢的優勢有可解釋的機制：不重算沒查詢的 contacts。這個 query 比例是人工指定，因此「8 倍」不能直接移植成真實路由加速。
- 100% 查詢／局部更新時，按需中位數反而約慢 13.3%；兩者的時間範圍重疊（增量全量 198.353～249.354 ms、按需 189.719～246.146 ms），七次樣本不足以斷言穩定退化幅度，但足以否定目前的「普遍更快」說法。
- 全部查詢／全部更新時，同樣重算 480 次，觀察到約 1.8% 時間差，不當成可靠改善證據。
- 同大小局部更新下，全重建的 842.675 ms 降到增量全量的 228.056 ms，顯示 cache 本身是重要來源；不能把所有增益都歸給按需。
- 首情境 Python 額外配置峰值：增量全量 42,320 bytes，按需增量 10,640 bytes。它不包含共同輸入，且不是程序總記憶體；不能宣稱總記憶體減少同樣百分比。
- size 多變時，單 context cache 無法跨輪重用；按需仍避免無關計算。這不表示支持所有大小流量或高命中率。

## 可核對的流程例子

`output/demand_interval_validation_20261021/comparison/query_trace.csv` 記錄 sparse_local 的前兩個快照：每策略準備階段算了幾條 contact、每次 query 是 solve 或 cache_hit、資源版本與回傳 J。

例如第一個快照的 contact 23 回傳 J=[26/3,21]，contact 46 回傳單點 [6,6]，contact 88 無可行起送時間。四策略對同一查詢均須相同。區間含非整數與單點，沒有用逐秒列舉取代。

## 仍未完成的驗證

- 尚未接真正的 Q／Label 搜尋，所以不知道真實探索比例是否只有 10%、50% 或接近全部。
- 未重現原文 Algorithm 1／2；四個對照是自建、共用 solver 的資源管理策略，不能稱作擊敗原文。
- 背景連續，未處理 P 的 source／destination 跳變與開端點；沒有前驅等待、quota 歷史或路由提交。
- 合成快照未從完整已接受 bundle 排程生成，也沒有實際動態鏈路／突發流量模擬。
- 僅 96 contacts，不能稱大規模或十萬級可擴展性驗證；重複計時只用一個 workload seed，不能建立普遍效能結論。
- 固定 s 檢查不等於完整連續時間 oracle；同 solver 的快取一致性不等於完整路由正確性。

## 對研究決策的影響

值得進下一步，但下一步應先取得**同模型完整搜尋的 query trace**，再比較端到端時間，包含預處理、搜尋、失效與提交。若實際大多要查全部 contacts，按需方向就不應成為主要貢獻。

短期可寫的主張僅為：在本受控查詢 workload，按需計算對稀疏查詢有元件成本優勢；大量查詢沒有穩定優勢。

## 證據位置

- 程式：`src/experiments/demand_interval_validation.py`。
- 報表：`src/experiments/report_demand_interval_validation.py`。
- 測試：`tests/test_demand_interval_validation.py`。
- 原始輸入、CSV、correctness、metadata：`output/demand_interval_validation_20261021/`。
- 圖表與逐步查詢：同目錄 `comparison/`。
- 腳本與輸入 SHA256 記錄於 metadata.json，交付前核對一致。
