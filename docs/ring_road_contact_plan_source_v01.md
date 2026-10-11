# Ring Road 公開 Contact Plan 來源核對

查閱日期：2026-10-11。僅搜尋、下載與資料盤點；未修改演算法或執行效能實驗。

## 結論

找到與黃文龍論文第 26 頁節點數、Contact 數量及時間範圍高度吻合的公開 Walker Ring Road Contact Plan。不能僅憑數量一致認定與學長實際輸入逐筆相同。

## 公開來源

- 研究團隊情境網站：https://sites.google.com/unc.edu.ar/dtsn-scenarios 。提供 RRN 軌道參數、地面站位置及 STK 情境等連結；網站亦有不同的月球及 Walker 情境，不能混用。
- DtnSim 程式庫：https://bitbucket.org/lcd-unc-ar/dtnsim/src/master/
- 檔案目錄：https://bitbucket.org/lcd-unc-ar/dtnsim/src/master/dtnsim/simulations/hindawi_rrn/contactPlan/
- Walker 原檔直連：https://api.bitbucket.org/2.0/repositories/lcd-unc-ar/dtnsim/src/master/dtnsim/simulations/hindawi_rrn/contactPlan/RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt
- NASA 收錄的 2023 年 (H)DtnSim 論文，其 reference [4] 指向上述 DtnSim 程式庫：https://ntrs.nasa.gov/api/citations/20220019062/downloads/HDTNSimSPACOMMApril2023_Italy.pdf

查閱時 master 最新 commit：`56d2c9835f6706563566768de646f9442a8602ab`。下載使用 master URL；原檔 SHA-256：`fe363dabdd182e292f5e3b74a28558245b2caf9d3aa7730db60d52afdb9763d2`。

NASA 文獻提供程式庫的追溯線索，不代表該情境為 NASA 實際部署網路或 NASA 官方標準拓樸。

## 原檔盤點與論文對照

| 項目 | 公開 Walker 原檔 | 學長論文第 26 頁 |
|---|---|---|
| 節點 | EID 1–48，共 48 個 | 47 個 |
| Hot spots | 1–6，6 個（依配套 ini） | 6 個 |
| Cold spots | 7–31，25 個（依配套 ini） | 25 個 |
| 衛星 | 32–47，16 個（依配套 ini） | 16 顆 |
| 額外 Server | 48，與 6 個 Hot spots 雙向常時連線 | 未列此額外節點 |
| Contact | 3,184 條 | 3,172 條 |
| 排除 EID 48 後 | 47 個節點、3,172 條 Contact | 數量一致 |
| 時間 | 最早開始 0，最晚結束 86,400 秒 | 一天 |
| 非 Server Contact 速率 | 12,500 Bytes/s | 100 KB/s |
| Buffer | 不在 Contact Plan 內定義 | 各節點 30,000 KB，自行設定 |

EID 48 的 12 條 Contact 為 `48→1..6` 及 `1..6→48`，皆為 `[0,86400]`，速率欄位為 125,000,000。

單位依原始碼 `dtnsim/src/node/dtn/Contact.h`：`dataRate_` 為 Bytes per seconds。因此原檔 12,500 Bytes/s 為 100,000 bits/s，不能誤讀成論文的 100 KB/s。論文是否刻意調整、或有單位誤植，尚未確認。

原檔有 2,174 條 `a range`，數值全部為 0；不能用它宣稱具有真實衛星傳播延遲。所有 Contact 皆滿足結束時間大於開始時間。

同目錄 ATrack 檔為另一個情境，共 1,512 條 Contact，並非此 Walker 檔。

## 格式與下載位置

```text
a contact +start +end sender receiver rate_bytes_per_second
a range   +start +end sender receiver range_value
```

本機唯讀下載暫存在 `tmp/topology_sources/`（Git 忽略），包含 Walker、ATrack 原檔與核對用原始碼。原始資料未重新發布到本專案 GitHub；使用／再散布授權尚未完整核對。

## 導入前待確認

1. 原始 Contact 的起訖與學長資料逐筆是否一致，不能只比數量。
2. 傳輸速率採原檔或論文版本，以及 KB 的單位慣例，須明確選擇並記錄。
3. 是否排除額外 Server；原檔保留，轉換版本另存。
4. 傳播延遲來源與 Buffer 設定須另外定義，不能由此檔自行推測。
5. 本次不採用學長刪除短時間槽的預處理，也未將此檔直接送入目前的時間枚舉演算法。
