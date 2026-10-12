# GitHub Pages 逐步圖解

網站：https://bagle102.github.io/space-dtn-thesis/

## 操作
- 選擇案例與 Bundle，使用上一步／下一步、播放或進度條。
- 點選 Label 看前驅路徑；點節點篩選該節點的 Label。
- 看當步 Q、容量、Buffer 峰值、虛擬碼亮起位置與執行紀錄。
- PPT 案例保留兩包順序；第二包使用第一包已預約的資源。
- 人工後段可行案例：s=0、1 失敗，但 s=2 可行，並非淘汰整條 Contact。

## 資料與模型界線
靜態網站重播已保存 trace，不是瀏覽器中的路由求解器。每個 EXTEND 分成檢查與決策兩個展示階段，不新增搜尋事件。GOAL 後展示 runner 已完成的驗證與資源更新；放棄餘下候選不代表它們被支配。接收曲線只畫到完整抵達，不以抵達後降為零暗示資源已釋放；後續等待留待下一跳檢查。網頁計算僅供繪圖，核心仍用 Python Fraction。網站無實體網路模擬、鏈路時段互斥或聯合最佳化宣稱。

Label 顯示 c/A/s/pred；內部 usage cache 由前驅鏈推導，不是新增公開 Label 欄位。舊核心文件的狀態向量表示法不直接作為畫面 Label 表格。

## 替換案例
先依 `modular_routing_v01.md` 執行可替換拓樸與演算法，完成結果與 report。再執行：

```powershell
python -m src.experiments.export_website --run output/experiments/ppt_modular_20261012 --title "PPT 拓樸：兩包依序路由" --output web/data/ppt.json
```

使用網頁「匯入重播 JSON」可在本機查看新案例，不上傳檔案至伺服器。匯入檔的驗證標記來自資料，瀏覽器不重新獨立驗證。要永久新增預設案例，將 JSON 加到 web/data 並更新 app.mjs 的案例清單。

## 本機與部署
```powershell
python -m http.server 8765 --directory web --bind 127.0.0.1
node web/model.test.mjs
python -m unittest discover -s tests
```
瀏覽 http://127.0.0.1:8765 。main 的 web/ 或 Pages workflow 更新會由 GitHub Actions 部署；僅 web/ 內容進入 Pages artifact，不部署論文或其他研究輸出。

互動版面參考 Adrian Haarbach 的 SPPRC 示範，使用本專案原創前端與現行 v04 紀錄，沒有套用參考網站的 time/cost 模型。
