# Label Setting 過程視覺化

日期：2026-10-11。

## 觀看內容

- 實驗案例選單：對應已保存的9組案例。
- 搜尋步驟：取出Label、每個Contact與格點開始時間的延伸、容量／時間／Buffer拒絕原因、Dominance與Q的前後變化。
- 預設選取PPT案例的第二包。可上一／下一步、自動播放或拖動進度。
- 已接受排程：0至規劃上限，以0.25秒控制播放位置，顯示正在發送的Contact、接收狀態與每個節點Buffer占用。

搜尋的步數不是模擬時間。各Label的建立時間是演算法處理順序，不能當成Bundle實際移動時間。時間播放依完整排程與分段線性占用計算；控制步幅0.25秒僅是畫面取樣，不是重設搜尋格點。

## 資料來源與限制

來源為 `output/experiments/small_suite_v01_20261011/` 的 input.json、results.json、schedule.csv與獨立重播檢查。沒有重跑路由、修改演算法或自行編造Label紀錄。

- 內部usage cache仍屬舊v04版本，沒有把四欄位顯示冒充為移除U的新實作。
- 每一步Q依該事件queue_after繪製，遭支配狀態依截至當步的事件重建，不直接套用最終狀態。
- 起始Label的Contact、起送與pred顯示空值，不編造虛擬Contact欄位。
- Buffer於事件時刻採原模型的交付前峰值；下一個時刻顯示釋放後的占用。
- 第09組會顯示同Contact時段重疊警示，不自動排隊／挪動發送時間。
- 不是SimPy、實體Bundle Protocol或共用無線電模擬。

## 重新生成

```powershell
python -m src.experiments.process_view --suite output/experiments/small_suite_v01_20261011 --output <新的視覺化片段路徑>.html
```

輸出路徑必須不存在，避免覆寫。互動片段使用visualize顯示環境；不需要網路請求或外部資料載入。模板為 `src/experiments/process_view.html`，JSON嵌入器為 `src/experiments/process_view.py`。

## 確認結果

透過Playwright及本機Edge無頭模式實際操作：9案例、18查詢、179顯示步驟；檢查Q列數、無空白說明與NaN／undefined、播放／上下步、Buffer事件峰值與交付後釋放。320px寬度沒有整頁水平溢出，另保留搜尋、排程與窄畫面截圖。

證據在 `output/visualizations/dtn_process_replay_20261011/`。互動檢查入口：`tests/check_process_view.cjs`，依序接受Playwright模組路徑、預覽包裝頁路徑、截圖輸出資料夾與選配瀏覽器執行檔路徑。
