# 可設定拓樸的實驗入口 v01

日期：2026-10-06。

用途：使用同一份程式，替換節點、contacts與bundle請求，重複執行現行finite-grid／aggregate容量模型。這是**路由計算與驗證入口**；不是實際網路傳送模擬器。

## 1. 開始使用

從專案根目錄執行；Python標準函式庫即可，不需要另外安裝套件。

```powershell
python -m src.experiments --config configs/walkthrough.json
```

預設在 `output/experiments/` 下建立新的執行資料夾。指定輸出位置時，該資料夾不能已存在，避免覆蓋舊結果：

```powershell
python -m src.experiments --config configs/walkthrough.json --output output/experiments/my_case_01 --oracle
```

`--oracle` 是與獨立完整搜尋比對的選項，只建議小拓樸與短horizon使用；循環多、contacts多或格點密時，完整搜尋可能非常耗時。本版沒有替它設定估算工作量上限。

先檢查設定、不執行搜尋：

```powershell
python -m src.experiments --config configs/minimal.json --validate-only
```

需要檢查停用dominance後的小案例結果時，可使用 `--no-dominance`。它不會修改永久設定或原始演算法。

## 2. 換拓樸或參數，要改哪裡？

| 要調整的項目 | 設定位置 |
|---|---|
| 新增／刪除節點 | JSON的`nodes` |
| 每個節點buffer上限 | `nodes[].buffer` |
| 連線方向、contact數量 | CSV的`source`、`target`及資料列，或JSON的`contacts` |
| Contact時窗 | `start`、`end` |
| 資料速率 | `rate` |
| 傳播延遲OWLT | `delay` |
| Contact剩餘可分配資料量 | `remaining_capacity` |
| Bundle大小、起點、目的地、生成時間 | JSON的`bundles` |
| Bundle規劃順序 | `bundles`陣列順序，不會自動按release排序 |
| 時間格點／搜尋期限 | `time_step`、`horizon` |

拓樸由contacts的傳送端與接收端建立。每個有方向的contact是獨立資料；若需要雙向，必須另外設定反方向contact。同一對節點可以有多個不同ID的contacts。節點ID可使用中文，也可加入沒有contacts的孤立節點。

## 3. JSON與CSV格式

可直接複製 `configs/minimal.json`，contacts寫在同一個JSON。也可複製 `configs/walkthrough.json` 搭配 `walkthrough_contacts.csv`。

`contacts`與`contacts_file`擇一提供。CSV路徑相對於JSON所在資料夾，不是相對於執行命令所在資料夾。

### Node

```json
{"id": "B", "buffer": "4"}
```

### Contact

```json
{
  "id": "c4",
  "source": "A",
  "target": "B",
  "start": "7",
  "end": "9",
  "rate": "4",
  "delay": "0",
  "remaining_capacity": "8"
}
```

CSV欄位：

```csv
id,source,target,start,end,rate,delay,remaining_capacity
c4,A,B,7,9,4,0,8
```

`delay`可省略，預設0；`remaining_capacity`可省略，預設`rate × (end-start)`，代表整個contact尚可分配。若已有預約或額外的容量限制，必須明列真正的剩餘資料量。本例c7指定2MB，不是由第一包扣除而來。

這是程式的案例輸入格式，將靜態contact資料與查詢初始資源放在同一列，方便設定。`remaining_capacity`仍是資源狀態，不是宣稱NASA contact的原生欄位。

### Bundle

```json
{"id": "bundle2", "source": "A", "destination": "D", "release": "1", "size": "4"}
```

單位固定為秒、MB、MB/s；不自動換算。數值支援整數、小數或`"1/2"`這種有理數字串，內部以Fraction計算。小數JSON literal也以字串讀取，避免匯入時轉成浮點數後四捨五入。

### 格點限制

目前每個contact的start、end、delay，以及**每一包在每一個contact上的S/r**，都必須是`time_step`的整數倍；bundle release也需對齊。這沿用v04的輸入要求，不會偷偷四捨五入。舉例：S=2MB、rate=4MB/s時，duration=0.5秒，不能使用Δ=1秒，可考慮Δ=0.5秒。

## 4. 執行流程

1. 讀取JSON／CSV並檢查欄位、ID、節點、容量與時間格點。
2. 建立初始剩餘資料量與buffer占用。
3. 按bundles陣列順序，每次呼叫原有Label Setting搜尋一包。
4. 有路徑時，以獨立完整排程檢查函式核對；選配完整搜尋比對最早到達。
5. 以兩套獨立資源更新方法核對，再提交選定路徑的容量與buffer占用。
6. 保存結果，才處理下一包。格點上找不到路徑的bundle不占用資源。

同模型的可行性、最優抵達時間或資源更新出現差異時，立即保存`failure.json`與`status.json=STOP`，不處理後續bundles，也不修改演算法。這個停止機制可測試，但不能由測試通過推論一般性正確。

## 5. 輸出

| 檔案 | 內容 |
|---|---|
| `input.json` | 正規化後的完整輸入，可再用`--config`匯入 |
| `summary.csv` | 各包是否接受、抵達時間、延遲、hop數與label數 |
| `schedule.csv` | 每跳contact、起送、送完、開始接收、整包抵達時間 |
| `labels.csv` | Label四欄`c,A,s,pred`，另附node與狀態 |
| `query_0001.json`等 | 單包的labels、Q事件紀錄、檢查與資源更新前後 |
| `results.json` | 全部結果及最終資源狀態 |
| `reservations.json` | 剩餘資料量及分段線性的buffer占用曲線 |
| `nodes.csv`、`contacts.csv` | 匯入案例的節點與contact資料；contacts欄位可再次用於設定CSV |
| `topology.dot` | Graphviz格式的拓樸描述，包含方向、時窗、速率與容量 |
| `status.json` | RUNNING、COMPLETE、ERROR或STOP |

有理數保留精確字串，例如`7/2`代表3.5秒。CSV可用試算表檢視，但不要把分數誤當日期或任意四捨五入。

Q事件中的`queue_before`與`queue_after`記錄label ID；對照同檔的`labels`即可取得四個欄位。佇列中可能仍留有已受支配的label，直到取出時產生`STALE`事件而略過；查看時也要看`active`。

## 6. Label與研究界線

報告用Label表示為 `(c,A,s,pred)`，輸出的`labels.csv`採這四個欄位。起始label沒有實際contact與起送時間，c與s為空值，`is_source_label=True`，對應PPT的虛擬c0。

**內部仍呼叫凍結v04實作**，保留其node、arrival與contact用量cache；本次不改extension、dominance、格點枚舉或回溯規則。完整pred紀錄在輸出中保留，包含已受支配label，供回溯查看。後續若要改成只靠pred計算用量，須另行確認並驗證，不在本次偷偷替換。

此入口也支援原有`contacts/buffers/bundles`格式，例如`output/validation/walkthrough_input.json`。舊格式若帶`background`，它代表匯入的既有buffer預約曲線；會檢查結構及初始容量，但沒有追溯各預約的bundle來源。舊格式的`expected`只是原案例資料，本入口的正確性判斷依獨立檢查及選配完整搜尋。

仍未加入transmission calendar、共用radio互斥、封包遺失、協定開銷或實際BP傳送模擬。`ACCEPTED`只表示在此有限格點與aggregate模型下接受，不等於實際鏈路排程一定無衝突。支援多種拓樸也不表示大規模執行效率已證明。

## 7. 已執行的小型檢查

- PPT案例：第一包c1→c2，A=8秒；第二包c4→c5，A=12秒；完整搜尋比對一致。
- 中文節點與半秒格點案例：up→forward，A=7/2秒；完整搜尋比對一致。
- 輸入錯誤、資源不被搜尋修改、無路徑不扣容量、前驅回溯、停止與失敗資料保存、既有輸出保護，以及原有演算法測試。
- 未執行大型實驗或效能比較。

下一步先自行複製設定檔改一個小拓樸，再考慮批次參數實驗或獨立傳送過程模擬器。

## 8. 輸出路徑圖與排程重播

已有路由結果後，可執行：

```powershell
python -m src.experiments.report --run output/experiments/ppt_topology_run_20261006 --positions configs/walkthrough_positions.json
```

在該次執行的`report/`產生路徑CSV、事件CSV、buffer峰值及事件前後占用、同contact傳輸時段重疊檢查，以及各包路徑PNG／SVG和全部節點buffer圖。該資料夾不能已存在。

省略`--positions`時，以圓形配置節點；座標JSON只控制繪圖，不影響路由。`--no-figures`可只產生數值結果；PNG／SVG繪圖另需matplotlib，本機使用既有的`tmp/validation_plot_dependencies`，沒有改動系統Python或新增套件。

重播直接依完整路徑與發送時間，以精確分段線性占用和事件左右極限計算，沿用既有事件峰值約定。它沒有使用SimPy或實際BP網路。事件表是時刻紀錄，排序不代表新的同時事件資源處理規則。

同模型排程或buffer檢查失敗會保存資料並停止；同contact時段重疊會記為模型界線診斷，不會偷偷移動發送時間或更改演算法。這個案例的事後重疊檢查不代表搜尋核心已支援transmission calendar；仍未檢查共用radio互斥。
