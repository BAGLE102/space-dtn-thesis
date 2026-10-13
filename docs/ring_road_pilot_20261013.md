# Ring Road第一輪五包傳送測試

## 結果

5包皆可行，走9（cold spot）→41（衛星）→2（hot spot）。每包100KB，在100KB/s下每跳發送需1秒。前包預約後，後包依序晚1秒起送。

| Bundle | 9→41發送時段 | 41→2發送時段 | 完整抵達秒 | 生成後延遲秒 |
| --- | --- | --- | ---: | ---: |
| 1 | [1342,1343) | [1343,1344) | 1344 | 2 |
| 2 | [1343,1344) | [1344,1345) | 1345 | 3 |
| 3 | [1344,1345) | [1345,1346) | 1346 | 4 |
| 4 | [1345,1346) | [1346,1347) | 1347 | 5 |
| 5 | [1346,1347) | [1347,1348) | 1348 | 6 |

每包完整排程檢查通過，且最早抵達時間與獨立完整列舉相同。獨立列舉每包檢查511個時間可銜接的完整排程（含繞圈），在當次既有預約下可行排程數分別為511、255、127、63、31。

成功包延遲平均4秒、最小2、最大6、母體標準差約1.414秒；相對本案例完整列舉答案的抵達誤差皆0秒／0%。不是相對物理網路或學長論文結果的誤差。

## 來源與設定

- 使用已核對SHA的公開Walker Ring Road檔，原情境47節點、3,172 contacts。
- 保留47節點，截取1342～1352秒；與此窗相交的10個有向contacts全數保留，沒有刪除反向連線或循環。
- contact起訖裁切至此窗，初始可用容量按裁切後時窗重新計算；不是使用原一整天剩餘容量。
- 本例每條裁切contact長10秒，初始容量1MB。實際使用的rrn_0057／rrn_0059各傳5包，剩餘0.5MB。
- 速率及Buffer採學長報告值100KB/s、30,000KB；明列十進位KB，換成0.1MB/s、30MB。
- 每包0.1MB，同時在1342秒生成；依bundle1到bundle5固定順序規劃。所有來源及目的地相同。
- 來源／目的地是依公開Contact Plan刻意選定的可銜接走廊。需求為本次人工設定，不是學長的原始flow，也不是隨機代表性流量。
- Δ=1秒，抵達期限1352秒；傳播延遲δ=0仍為假設；初始沒有背景占用或發送預約。
- 保留全部Label，不做支配刪除，沿pred核對重用contact容量。待測路由與上一輪相同。

## 這輪實際驗證了什麼

1. 公開研究情境的contact資料可轉換並載入。
2. 同contact較早時段被預約後，後包會繼續嘗試較晚時段。
3. 依完整接收後轉送安排兩跳時間，並在接受後提交資源。
4. 五包結果與獨立完整列舉一致，無容量或Buffer超限。

Buffer峰值：節點9為0.5MB、節點41及2各0.1MB，遠低於30MB。這輪沒有讓Buffer成為瓶頸，不能用來證明Buffer約束的效能優勢。

節點41同時在不同contacts接收後包及發送前包；本研究模型未包含共用天線／半雙工硬體互斥，所以這是模型內可行排程，不是實體無線設備可直接執行的保證。

## 核對方法與程式調整

原完整列舉以拓樸walk乘所有時間組合，會產生大量時間上根本接不起來的組合。本輪另加`temporal_reference.py`，先列出時間可銜接的完整walk，再核對整條路徑的Buffer／容量／預約。不以資源條件做前綴剪枝，不排除重訪，也不使用待測Label搜尋。

`run.py`新增可選的reference_solver參數，預設仍是原完整列舉。路由規則與待測`search.py`未修改。

新舊兩種完整列舉在可行繞圈及容量不足案例的最早抵達／可行排程數相同，18項相關測試通過。執行外層設60秒上限，未觸發；測試數量上限未觸發。沒有進行效能比較。

## 檔案

- `configs/ring_road_thesis/pilot_5bundles.json`：本輪需求與時窗。
- `src/ppt_validation/ring_road_pilot.py`：資料裁切、載入、測試及結果輸出。
- `src/ppt_validation/temporal_reference.py`：獨立時間順序完整列舉。
- `output/ring_road_pilot_20261013/summary.csv`：五包結果。
- `output/ring_road_pilot_20261013/schedule.csv`：各跳時間。
- `output/ring_road_pilot_20261013/verification.json`：完整排程檢查及列舉結果。
- `output/ring_road_pilot_20261013/figures/`：Buffer與發送預約圖，含PNG／SVG。
- `tmp/ring_road_pilot_20261013/`：本機裁切輸入及完整Label／候選／逐包預約紀錄。

圖的0秒代表原Contact Plan的1342秒；Buffer圖放大活動範圍，30MB上限在圖外並明確標註。公開結果不包含原始一整天Contact Plan。

## 重現

以下兩個輸出目錄必須不存在：

```powershell
python -m src.ppt_validation.ring_road_pilot --source tmp/topology_sources/RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt --config configs/ring_road_thesis/pilot_5bundles.json --local tmp/ring_road_pilot_rerun --output output/ring_road_pilot_rerun
```

完整原始情境與本案例不同，不能把5/5成功外推成47節點一天網路的成功率。下一階段再增加需求變化及時間範圍；本輪尚未測整天資料或Buffer壓力。
