# 02_capacity_insufficient：小案例驗證

本輪依新版PPT做有限格點搜尋，保留所有Label，不做支配刪除。
允許節點與contact重訪，以小案例核對，不代表真實衛星模擬、一般證明或效能比較。

| Bundle | 路徑 | Contact序列 | 完整抵達秒 | 完整列舉抵達秒 | 結果 |
| --- | --- | --- | ---: | ---: | --- |
| b1 | A |  | None | None | NO_ROUTE_ON_GRID |

## 判斷與限制

- contact容量使用 本路徑已用量＋S≤R[c]，已用量沿pred計算。
- 逐格試起送時間，整包在contact結束前送完，完整抵達不超過horizon。
- 接收端以已接受前包占用＋逐byte接收量檢查整段接收期間。
- 傳送端檢查完整抵達後的等待與逐byte發送釋放。
- 同一contact的已接受發送區間不得重疊，端點可首尾相接。
- 目的地在完整接收後立即交付，交付前峰值仍檢查。
- 依bundles檔案固定順序，成功後才提交容量、Buffer及發送時段。
- 尚未輪到規劃的bundle不預先加入Buffer占用；失敗包不增加預約。
- 不檢查不同contacts共用天線或收發器的互斥，不能外推為硬體排程可執行。
- Label數量與列舉數僅供診斷，本輪沒有比較執行速度。
- horizon目前同時作搜尋／抵達期限，沒有另加每包deadline。
- 四欄Label獨立編號，未加入U或route_usage，也沒有支配規則。

## 可檢查的檔案

- summary.csv：每包路徑、抵達時間及完整列舉核對。
- schedule.csv：各跳起送、送完、開始接收與完整抵達。
- candidates.csv：每個嘗試時間的接收／傳送峰值與通過或失敗原因。
- labels.csv、query_*.json：Label前驅、Q的POP／加入事件與完整搜尋紀錄。
- reservations_after_*.json：接受各包後的三種資源預約。
- buffer_breakpoints.csv：各次提交後所有分段線性折點的占用。
- statistics.json：成功包延遲的平均、最大、最小及母體標準差。

## 延伸拒絕原因（含同一contact在不同Label的重複嘗試）

- b1：{'CAPACITY': 1}
