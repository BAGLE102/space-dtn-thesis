# Space DTN 桌面實驗 GUI

日期：2026-10-11。

## 啟動

在專案根目錄執行：

```powershell
python -m src.experiments.gui
```

也提供 `launch_experiment_gui.pyw`；Windows 已設定 Python 的 `.pyw` 檔案關聯時可直接雙擊。使用 Python 標準函式庫 Tkinter，不需要瀏覽器、SimPy 或額外繪圖套件。

## 操作

1. 預設載入已保存的9組小型實驗，選擇案例與 bundle。
2. 「搜尋步驟」用上一步／下一步／播放／進度條，查看Contact嘗試、可行性與Dominance結果、Q的前後變化。
3. 「已接受排程」依時間播放選定路徑，顯示發送中的Contact、接收狀態及各節點Buffer占用。此模式的Q不適用。
4. 「開啟實驗結果」選擇含manifest.json的套件資料夾，或含results.json及report/replay_check.json的單次執行資料夾。
5. 「選擇JSON案例」讀取既有格式；JSON中的nodes、contacts／contacts_file、bundles等仍可自由設定。GUI目前不提供拖曳拓樸或直接編輯Contact表。
6. 「執行案例」在獨立子程序執行既有路由與獨立排程重播，完成後載入新結果。核對小型案例時可勾選完整搜尋；大型案例可能耗時，可用「停止執行」。

## 輸出與中止

- 每次新執行保存在 `output/experiments/gui_runs/<時間識別碼>/`，不覆蓋舊結果。
- 保留input、每跳排程、Labels、Q trace、資源預約及獨立數值檢查；GUI不需要PNG圖即可顯示。
- 診斷紀錄在 `output/experiments/gui_logs/`，預設不納入Git。
- 使用者中止時保留部分輸出與gui_cancelled.json；載入器拒絕將該結果視為完成實驗。
- 同模型錯誤沿用既有停止及證據保存機制；GUI不自動修正路由。

## 版本界線

沿用凍結v04路由核心，保留發送時間枚舉與內部usage cache；顯示c、A、s、pred不代表已完成移除U的實作。不是SimPy或實體Bundle Protocol模擬；不在搜尋中檢查傳輸時段互斥與共用radio。已知同Contact重疊案例會顯示警示，不挪動傳輸時段。

搜尋模式的Contact容量是該包搜尋前的狀態；已接受排程模式則顯示全部接受路徑提交後的剩餘容量。Buffer的時間控制步幅0.25秒只影響觀看位置，不改變路由格點；事件時刻顯示交付前峰值。

## 已執行檢查

- GUI實際操作：9案例、18查詢、179步，Q列數與事件一致，無Tk callback例外。
- 播放控制、背景執行案例與結果載入、中止自己啟動的子程序並保留標記。
- Buffer抵達瞬間峰值與交付後釋放。
- Windows DPI顯示縮放及搜尋／排程截圖目視確認。
- 40項既有unittest通過，沒有更改路由核心。

證據：`output/visualizations/desktop_gui_v01_20261011/`。

可重跑 GUI 檢查：`python tests/check_desktop_gui.py`。它會短暫開啟視窗並執行一個小案例；檢查用執行結果移到已忽略的 `.codex-ppt-build/gui_smoke_runs/`，不混入正式實驗資料。
