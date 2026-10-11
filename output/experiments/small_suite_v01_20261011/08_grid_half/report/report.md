# 時間格點由1秒改為0.5秒

依固定順序規劃兩包，再依選定發送時間做分段線性的排程重播。
Buffer使用原模型的事件峰值約定；同時事件在CSV的排序不代表新的處理優先序。

| Bundle | Node路徑 | Contacts | 完整抵達（秒） | 生成至交付（秒） |
|---|---|---|---|---|
| bundle1 | X → B → D | c1 → c2 | 8 | 8 |
| bundle2 | A → B → D | c4 → c5 | 12 | 11 |

## 每跳傳送

| Bundle | Contact | Sender→Receiver | 發送起訖 | 接收起訖 |
|---|---|---|---|---|
| bundle1 | c1 | X→B | 2–3 | 2–3 |
| bundle1 | c2 | B→D | 6–7 | 7–8 |
| bundle2 | c4 | A→B | 7–8 | 7–8 |
| bundle2 | c5 | B→D | 10–11 | 11–12 |

## 檢查結果

- 同模型完整排程與資源更新：通過。
- 所有節點的buffer峰值與上限，見buffer_peaks.csv。
- 選定傳輸的同contact時間重疊：0筆。
- 這是此案例的事後檢查，沒有將transmission calendar加入路由搜尋。
- 未模擬實際Bundle Protocol、共用radio、遺失、重傳或控制指令延遲。
- 已在原執行入口啟用完整搜尋的案例，可在results.json查看oracle_checked。
