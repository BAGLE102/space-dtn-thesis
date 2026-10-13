# 採用學長Ring Road情境

使用者已選擇沿用黃文龍學長所用情境。具體採「相符的公開Walker Ring Road contact plan＋學長論文第26頁報告參數」。尚未取得學長實際輸入檔，不能稱為逐筆完整重現。

## 已準備

- 47節點：6個hot spots、25個cold spots、16顆衛星；3,172 contacts；一天86,400秒。
- 傳輸速率採論文100KB/s，Buffer採30,000KB。初步明列十進位KB／MB，轉成0.1MB/s與30MB。
- 公開原檔速率12,500Bytes/s，轉換時明確改成論文參數100,000Bytes/s，沒有把兩者混成一樣。
- 移除額外Server48的12條contacts。保留其餘方向、時窗、短contacts及循環。
- δ=0是初步實驗假設，不能宣稱已重現實際衛星傳播延遲。
- 未套用學長的時間槽切割及刪除≤5秒時槽，也未把他的flow當成不可分割bundle需求。

參數選擇在`selection.json`，來源核對在`docs/ring_road_contact_plan_source_v01.md`。

## 本機可用輸入

- `tmp/ring_road_ppt_thesis/topology.json`：節點與Buffer。
- `tmp/ring_road_ppt_thesis/contacts.csv`：完整Contact Plan與初始容量。
- `tmp/ring_road_ppt_thesis/source_and_parameters.json`：原檔SHA、來源、單位、調整及未確認事項。
- `tmp/ring_road_ppt_thesis/input_validation.json`：格式及循環拓樸檢查。

原始及轉換contact逐筆資料維持本機存放，沿用既有來源管理方式，不隨本次Git同步重新發布。Git保存可重建的轉換程式、參數與說明。

## 重建

取得來源檔後，在專案根目錄執行（輸出資料夾必須不存在）：

```powershell
python -m src.ppt_validation.prepare_ring_road --source tmp/topology_sources/RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt --output tmp/ring_road_ppt_thesis
```

固定來源URL及SHA保存在轉換程式；不同版本會停止，不默默套用。本次核對輸入47節點／3,172 contacts通過，2項轉換測試通過，未執行路由。

## 接下來的工作

已依使用者確認支援重訪節點／contact：沿pred累計同contact已用容量，保持四欄Label及無支配搜尋。繞圈、容量不足及有限終止的小案例通過，原兩包及五包回歸結果不變。詳細虛擬碼在`docs/ppt_label_setting_cycles_pseudocode_v01.md`。

整天Ring Road尚未執行；五包與擴充批次的需求設定及已核對結果見下文。完整列舉僅供小案例，不能直接承諾一天資料能在資源上限內完成。尚未確認原始逐筆資料與學長完全相同，單位及延遲假設仍保留。

## 五包功能測試已完成

`pilot_5bundles.json`指定1342～1352秒、5包100KB、cold spot 9→hot spot 2。使用相交的10個有向contacts，保留47節點與循環。抵達1344～1348秒，全部與獨立完整列舉一致。這不是整天流量實驗；詳見`docs/ring_road_pilot_20261013.md`。

## 擴充批次測試

完成14組嘗試，規劃330包；206包已獨立核對，124包未完成。9組完整完成，5組遇到20秒整體驗證上限。涵蓋10／20／50／100包、不同bundle大小、其他4條已知走廊、混合來源、Buffer診斷及較長時窗。

`output/ring_road_batch_20261013/report.md`列出全部狀態與限制，未完成不算無路徑。除了明列的Buffer診斷組，其餘維持學長30MB Buffer；路由搜尋未修改。
