# 按需可行起送時段：隔離驗證方法

日期：2026-10-21。這是資源處理元件 pilot，不是完整路由演算法驗證，也不是 2410.15546v3 的忠實效能重現。

## 研究假設與反證方式

假設：搜尋只查詢 Contact Plan 的少部分時，按需計算 J 可避免無關處理；資源只局部改變時，保留仍有效的結果可省重算。

反面預期：全部 contacts 都查詢、資源大量更新或每包 size 改變時，按需／快取可能沒有速度優勢，還有管理成本。保留這些案例，不只展示優勢。

本次只回答局部元件是否有這些效果，不能回答實際路由探索比例多大、整體交付率是否提高、較原論文是否更快或是否具新穎性。

## 1. 模型與受控範圍

- 原始 contacts：單向、無 self-loop、有限發送時窗、固定 r>0、δ≥0、剩餘 quota 及已預約的發送時段。
- 本包 size S>0，不分割、不暫停；接收逐 byte 增加，送出逐 byte 釋放。已預約時槽不能重疊。
- O_u(t)、O_v(t) 為有理數的**連續**分段線性函式，定義域外延用端值；背景不超上限。
- 本次只求送出與接收 ramp 都可行的起送集合 J。沒有前驅等待、完整路由、Label、dominance、循環、來源／目的地跳變及提交。
- P 事件／NOT_ATTAINED 尚未測：不能把連續曲線子模型結果推廣到完整候選 PPT。
- quota 單次 S≤R 作 query 前置判斷；不測前綴累計用量。效能情境 quota 非瓶頸，解析測例另測 quota 不足。
- 合成背景是合法的局部資源曲線，不宣稱每個快照都由一組完整可重現的前包路由產生。更新亦為快照替換，不假稱完成前包提交。

## 2. J 如何求解：沒有逐秒枚舉

令 d=S/r、f=s+d、h=s+δ、A=s+d+δ。

起送範圍：`start(c) ≤ s ≤ min(end(c)−d, deadline−d−δ)`。
已預約 `[a,b)` 禁止新起送落入開區間 `(a−d,b)`；恰好接續允許。

sender 條件：`O_u(t)+S−r(t−s) ≤ M_u`，整段 `s≤t≤s+d`。
receiver 條件：`O_v(t)+r(t−s−δ) ≤ M_v`，整段 `s+δ≤t≤s+δ+d`。

求解程序：

1. 收集會改變公式的 s 事件：sender 的每個折點 τ 產生 τ、τ−d；receiver 的折點 τ 產生 τ−δ、τ−δ−d；另加時窗端點及時槽的 a−d、b。
2. 相鄰事件之間，ramp 兩端與其內部背景折點的占用約束，對 s 都是仿射函式。
3. 直接解每條線性不等式，取交集；非空部分形成區間。
4. 單獨檢查事件點，避免漏掉恰好一包或孤立起送點。
5. 合併相接區間。時間與資料量全程使用 Python Fraction，不四捨五入。

有限分段的理由：固定 s 的總占用在每個小段為線性，最大值出現在 ramp 端點或背景折點；按上述 s 事件切開後，約束形式不變。這是本連續子模型的求解推導，不是一般路由完備性證明。

## 3. 正確性先行

### 3.1 九個解析案例

所有預期集合在測試前明寫：空背景、同時釋放與接收、sender ramp、已占用中段、傳播延遲、quota 不足、deadline、只能恰好一包、有理數邊界 7/3。

例如 M=4、S=4、r=4，B 在 7～8 秒從 4 MB 降到 0，A→B=[1,10]、δ=0，精確 J=[7,9]；δ=1 時改為 [6,9]。

### 3.2 獨立固定排程檢查

100 個固定 seed 隨機小例，每例選多個有理數 s，另測回傳區間端點、區間中點、端點外 1/1000。
對每個 s，不呼叫 J 的裁切程序，改直接計算該排程在 ramp 端點與背景折點的全時段峰值。

固定 s 的檢查涵蓋整段傳輸時間；但有限個 s 不能證明 J 沒有遺漏任意極窄區間。解析案例、推導與 probes 是互補證據，不能稱為完整 oracle 證書。

檢查器不共用區間裁切邏輯，但也被 solver 用來補檢事件點，因此不是完全隔離的第二個求解器。非事件點 probes 仍能比較直接排程檢查與區間解答；一般完整性需另做獨立 oracle／證明。

### 3.3 快取答案對照與負控制

每個 workload 使用 seeds 1021、1022、1023，將四策略每個實際查詢與直接 fresh solve 比較。
這能測快取管理一致性，因共用 solver，不能額外證明 solver 本身正確。

獨立單元測試檢查 sender／receiver 版本、contact 版本、S、deadline 變動皆使舊結果失效。
另故意不更新 receiver 版本，確認測例能觀察到 stale answer，證明失效檢查有辨識力。正式 benchmark 都遵守版本更新契約。

任一解析、probe 或快取一致性失敗：寫 FAILURE.json 並立即停止效能比較；不靜默更改研究定義。

## 4. 四個對照策略

| ID | 何時求 J | 是否保留跨快照快取 |
|---|---|---|
| eager_rebuild | 每個快照全部 contacts | 否 |
| lazy_roundcache | 僅實際查詢的 contacts，同輪重用 | 否 |
| eager_incremental | 每個快照掃過全部 contacts，只重算版本失效者 | 是 |
| lazy_incremental | 僅實際查詢者，版本有效直接重用 | 是 |

四者使用完全相同的 Fraction 求解器、輸入與查詢順序；eager_incremental 是避免弱化對照的關鍵。不能只和每包全部重建的版本比較。

cache 每個 contact 僅存最後一個 context，stamp 包含 contact 版本、兩端 node 版本、size、deadline。模型與 limits 在這組測試內固定；若未來可改，必須進一步加入版本。節點更新採保守 node-level 失效，不是精細時間範圍更新。

## 5. 七個情境與受控參數

| 情境 | 查詢 contacts 比例 | 每輪資源變動比例 | Size／背景 |
|---|---|---|---|
| sparse_local | 10%（向上取整） | 2%（node 與 contact 分別向上取整） | 同大小 |
| half_local | 50% | 2% | 同大小 |
| full_local | 100% | 2% | 同大小 |
| sparse_global | 10% | 100% | 同大小 |
| full_global | 100% | 100% | 同大小 |
| varying_sizes | 10% | 2% | 2／4／6 輪替 |
| fragmented | 10% | 2% | 每條背景折點從 5 增為 9 |

同一情境跨快照沿用所選 contacts 集合，觀察跨輪 reuse；同輪另重複約三分之一查詢。這是可控的 query trace，不是實際搜尋輸出的 trace。不同策略所有實際查詢都完全相同。

node 數為 max(8, contacts//4)，端點隨機無 self-loop。contact 速率為 2 或 4、δ為 0 或 1，背景值介於 0～8，上限 8，deadline=32。更新包含 node 曲線與 contact busy slots；一個 node 更新會使多條鄰接 contact 失效，實際失效比例可能高於 2%。

## 6. 時間與記憶體測量

- correctness 在所有效能量測前完成。
- 每策略先暖機一次；每次實測建立全新的 Engine，避免前一 run 的 cache 影響下一 run。
- 同一 repeat 內用固定 seed 打亂四策略順序，減少固定先後的系統偏差。
- perf_counter_ns 測量初始化、查詢、版本檢查、cache 寫入及所有快照處理。輸入生成與 correctness 不納入時間。
- 每 run 前 gc.collect；蒐集呼叫本身不計時，執行期間 GC 保持一般啟用。
- memory 另跑一次 tracemalloc，避免污染時間。數字為新增 Python 追蹤配置峰值，不是整個 process RSS，不包含已建好的共同輸入。
- 保存 mean、median、min、max、sample stddev、P95、solve 次數、產生片段數及 cache entries。七次重複的 P95 等於最大觀察值，解讀時不能當穩定尾部估計。
- correctness 多 seeds；重複計時使用同一個 seed 1021。時間重複不是獨立流量樣本，不能直接推論真實 workload 的信賴區間。

本次不報 delivery rate、earliest-arrival optimality 或真實 contact 利用率，因沒有執行路徑搜尋。

## 7. 重現與證據

標準 Python 3 可執行，不需額外 solver：

```powershell
python -m unittest tests.test_demand_interval_validation -v
python -m src.experiments.demand_interval_validation --contacts 96 --epochs 5 --repeats 7
```

輸出目錄預設 `output/demand_interval_validation_20261021/`：

- correctness.json：解析預期／實際、獨立固定 s 檢查數、快取對照數。
- inputs.json：計時 seed 的完整快照與 query trace，不只提供隨機 seed。
- timings.csv：每次原始計時。
- summary.csv：各策略統計與 memory／計數。
- metadata.json：Python、OS、參數、輸入及實驗腳本 SHA256。

擴大樣本可指定獨立 `--output`，避免覆寫現有研究結果。讀取結果以對應 metadata 為準。

下一步門檻：若只有少量人工查詢時才受益，結論應限制為元件 work avoidance；必須再取得完整搜尋 trace 才能評估端到端效益。此 benchmark 不等於既有論文的優劣比較。
