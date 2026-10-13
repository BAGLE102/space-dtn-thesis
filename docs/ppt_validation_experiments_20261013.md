# PPT版本：第一輪小案例驗證

使用者已同意：先做PPT兩包及8節點／5包案例，暫不刪除任何Label。
本工具與舊frozen v04分開，沒有更新網站，也沒有改寫既有研究定義。

版本註記：本文保留第一輪DAG驗證的歷史紀錄。之後使用者確認的循環支援，請見`ppt_label_setting_cycles_pseudocode_v01.md`；不要把舊DAG限制當作現行程式限制。

## 本輪結果

| 案例 | Bundle | 選定路徑 | 完整抵達（秒） | 完整列舉核對 |
| --- | --- | --- | ---: | --- |
| PPT兩包 | 1 | X → B → D | 8 | 相同 |
| PPT兩包 | 2 | A → B → D | 12 | 相同 |
| 八節點 | 1 | S1 → A → D → T | 12 | 相同 |
| 八節點 | 2 | S2 → C → E → T | 12 | 相同 |
| 八節點 | 3 | S1 → B → E → T | 13 | 相同 |
| 八節點 | 4 | S2 → A → D → T | 20 | 相同 |
| 八節點 | 5 | 無可行路徑 | 不適用 | 同樣無解 |

以上是固定輸入、固定規劃順序與Δ=1秒下的結果。不是隨機實驗統計，不宣稱一般最優性證明或效能提升。

成功包延遲（抵達−生成）：PPT案例平均9.5秒，最小8、最大11、母體標準差1.5；八節點案例平均13.5秒，最小12、最大18、母體標準差約2.598。失敗包不納入延遲平均，無路徑不寫成0秒。

## 第5包的可重現失敗原因

前4包已成功預約後，bundle5由A出發。A的三個可用contacts各有3個時間候選，共9個候選皆在接收端Buffer檢查被拒絕。

| Contact | 候選起送秒 | 接收節點 | 候選接收峰值 | 上限 |
| --- | --- | --- | ---: | ---: |
| c05 | 5、6、7 | B | 各8 MB | 4 MB |
| c06 | 4、5、6 | D | 各8 MB | 4 MB |
| c13 | 11、12、13 | D | 各8 MB | 4 MB |

這裡是搜尋依檢查順序最先記錄的拒絕原因，不表示其他限制一定通過。例：c13在11秒還會與第4包發送重疊。A在3秒既有占用8MB，也無法再持有第5包的4MB；這是完整排程的另一個限制。

完整列舉檢查了第5包的18條拓樸路徑、570個時間組合，0個可行排程。這是正常的無解結果，不是搜尋程式與核對結果不一致；未改參數強迫五包成功。

## 版本與範圍

- 四欄Label為`(c,A,s,pred)`，以獨立Label編號索引，不設U、route_usage或dominance。
- DAG範圍內，一條路徑不會重用contact，容量直接判斷`S≤R[c]`。遇到循環拓樸會明確拒絕，不偷偷過濾。
- Q以完整抵達時間最小優先，同時間以Label建立序號排序。初始L0的c=None代表PPT虛擬c0，不是實際contact。
- 接收可行起送時間仍逐格枚舉；失敗只淘汰該時間，不淘汰整個contact。
- 接收端檢查逐byte上升；傳送端檢查等待與逐byte釋放。Buffer峰值檢查相關分段線性折點，而非只取整數時間。
- contact使用發送時窗，同contact一次只傳送一包。預約`[s,f)`不含傳播延遲，允許端點相接。
- 候選搜尋不修改全域資源。完整路徑驗證後，才提交容量、Buffer及發送預約。
- 固定規劃順序、固定已接受排程，不重排前包。未輪到規劃的需求不預先加入Buffer占用。
- 目的地完整收到後立即交付，但仍計入交付前峰值；生成／交付同時事件採峰值約定。
- horizon同時作搜尋上限與抵達期限。不同contact共用硬體互斥、真正傳輸失敗及分散控制不在本輪。
- 人工拓樸驗證，沒有使用SimPy、真實衛星軌道或實體封包模擬。

## 程式與資料分開

| 檔案 | 用途 |
| --- | --- |
| src/ppt_validation/search.py | 無支配Label Setting、接收時間篩選、時段與Buffer檢查 |
| src/ppt_validation/reference.py | DFS完整路徑＋各跳時間笛卡兒積，核對完整排程 |
| src/ppt_validation/run.py | 固定順序規劃、核對、提交預約及CSV／JSON／報告 |
| src/ppt_validation/figures.py | 依已接受排程輸出Buffer及contact預約圖 |
| configs/ppt_modular/experiment_ppt_validation.json | PPT案例的新驗證入口 |
| configs/topology_8nodes_5bundles/experiment_ppt_validation.json | 五包案例的新驗證入口 |
| tests/test_ppt_validation.py | 晚起送、等待失敗、接收中途峰值等回歸檢查 |

拓樸、contacts及bundles仍用既有拆分檔案。替換資料時改config，不必修改搜尋程式。新入口不接受標記legacy演算法的設定，避免版本混用。

完整排程的時間／容量／Buffer核對沿用`src/validation/exhaustive_oracle.py`的獨立計算；另寫發送時段重疊檢查。沒有共用待測端的增量延伸或發送時段判別函式。它仍然是同一模型的交叉核對，不是獨立的物理模型。

## 重現命令

在專案根目錄執行，下列輸出路徑必須尚不存在：

```powershell
python -m src.ppt_validation.run --config configs/ppt_modular/experiment_ppt_validation.json --output output/ppt_validation_rerun/ppt_2bundles
python -m src.ppt_validation.run --config configs/topology_8nodes_5bundles/experiment_ppt_validation.json --output output/ppt_validation_rerun/8nodes_5bundles
python -m src.ppt_validation.figures --output output/ppt_validation_rerun/ppt_2bundles
python -m src.ppt_validation.figures --output output/ppt_validation_rerun/8nodes_5bundles
python -m unittest tests.test_ppt_validation -v
```

搜尋與核對使用標準函式庫及既有輸入層，繪圖需要Matplotlib。數值運算使用Fraction，輸出JSON中的有理數以字串保存。

## 輸出

`output/ppt_validation_20261013/`下分`ppt_2bundles/`及`8nodes_5bundles/`。

優先看`summary.csv`、`schedule.csv`及`report.md`。`query_*.json`保存全部Label及Q的取出／加入事件，`candidates.csv`保存起送時間與拒絕原因，`reservations_after_*.json`保存逐包預約。

`figures/buffer_occupancy.png`與`.svg`：橘／藍／綠／紫依序為已接受的bundle，黑虛線為總占用，灰線為上限。目的地收完後的垂直下降表示立即交付。第5包失敗，所以不出現在已接受曲線中。

`figures/contact_reservations.png`與`.svg`：灰色為contact開放時窗，彩色為已接受發送預約。

## 尚未完成

一般支配條件尚未定案；本輪不驗證dominance，也不宣稱正式演算法的效能。下一步先核對這7次查詢的排程，再討論支配條件及更大規模實驗。
