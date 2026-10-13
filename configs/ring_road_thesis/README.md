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

目前`src/ppt_validation/search.py`只接受DAG，尚不能直接跑這份完整拓樸。要先討論並定案可否重訪節點／contact，以及同一路徑前綴的Buffer占用如何計入，才能擴充支援。這是模型處理問題，不能只拿掉DAG檢查。

本次沒有修改演算法、支配規則、PPT或網站。五包來源／目的地／大小／生成時間尚未設定，不先宣稱五包可達。
