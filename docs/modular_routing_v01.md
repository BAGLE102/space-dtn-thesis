# PPT 拓樸與可替換演算法架構

日期：2026-10-12。本次以使用者提供的 `F:/1007_定義更新版_20261006.pptx` 為來源，已核對五節點、八個 Contact、兩個 Bundle 的文字資料。沒有修改 PPT、frozen v04 的搜尋判別式或跑大型實驗。

## 架構與設定檔

```text
configs/ppt_modular/experiment.json   執行設定與演算法選擇
            ├── topology.json       節點 Buffer 與 Contact 資料位置
            │       └── ../walkthrough_contacts.csv
            └── bundles.json        Bundle 需求與處理順序

src/experiments/config.py            載入、組合與驗證輸入
src/experiments/algorithms.py        取得演算法（內建或本機 Python 函式）
src/experiments/runner.py            依序呼叫、獨立驗證、統一預約與輸出
src/validation/proposed_v04.py       既有 Label Setting 核心，未改動
```

拓樸路徑相對於 experiment.json；Contact CSV 路徑相對於 topology.json。所有資料使用 s、MB、MB/s，數值以有理數計算，不偷偷四捨五入。既有 schema v1 與舊設定檔仍可使用。schema v2 目前不提供外生初始占用欄位；既有已接受 Bundle 的占用由 runner 累加，必要時仍可使用支援背景曲線的舊格式。

## 執行 PPT 案例

在專案根目錄執行，output 必須是新的資料夾：

```powershell
python -m src.experiments --config configs/ppt_modular/experiment.json --output output/experiments/my_ppt_run --oracle
```

`--oracle` 是小案例用的獨立完整搜尋比對，不適合直接套在大型拓樸。執行器另外對接受路徑做獨立完整排程檢查與預約更新比對。出現不一致時保存 failure.json，停止處理後續 Bundle。搜尋不能直接修改全域 R 或 O；只有完整路徑通過檢查後才提交。

本次實際結果：

| Bundle | 節點路徑 | Contact 與起送時間 | 完整抵達 |
|---|---|---|---:|
| bundle1 | X→B→D | c1:2 秒；c2:6 秒 | 8 秒 |
| bundle2 | A→B→D | c4:7 秒；c5:10 秒 | 12 秒 |

資料：`output/experiments/ppt_modular_20261012/`。人可讀報告：`report/report.md`。

## 換拓樸、需求或演算法

- **換拓樸**：另存 topology.json 與對應 Contact CSV，修改 experiment.json 的 topology_file。節點、Buffer、Contact ID、傳送端、接收端、起訖、速率、傳播延遲與初始剩餘容量皆可調整。
- **換需求**：另存 bundles.json，修改 bundles_file。陣列順序就是規劃順序，不會自動依 release 排序。
- **換演算法**：修改 algorithm，或在命令列加 `--algorithm` 覆蓋設定。

```powershell
python -m src.experiments --config configs/ppt_modular/experiment.json --algorithm label_setting_no_dominance --output output/experiments/my_ppt_without_dominance --oracle
```

內建 `label_setting_v04` 使用現行演算法；`label_setting_no_dominance` 只關閉支配剪枝，方便核對小案例，不是新的比較方法，也沒有比較效能主張。

新增自己的方法時，可提供受信任的本機 Python 入口，例如 `--algorithm my_package.my_router:search`。這會匯入並執行本機 Python 程式，不是資料檔。介面為：

```python
def search(case, bundle, quota, background, dominance=True):
    # Read-only search for ONE bundle in the same resource model.
    # Use exact rational times and data volumes.
    return {
        "arrival": arrival_or_none,
        "hops": [(contact_id, departure_time), ...],
        "labels": {},
        "trace": [],
        "stats": {
            "created": 0, "enqueued": 0, "expanded": 0,
            "pruned_new": 0, "pruned_old": 0,
        },
    }
```

這是回傳契約示意，不是能直接執行的路由實作。沒有 Label 的方法可以回傳空 labels／trace，但不可假造統計；無適用計數時應在方法說明明列。非空 labels 若需要匯出，必須提供既有 `label_view` 所需的 id、v、a、hop、pred、active、processed。trace 若包含 EXTEND 事件，須遵守既有事件格式，否則使用空 trace。自訂方法須以相同容量、Buffer 與時間語意求解；不同模型不能直接接入後當作公平比較。選路成功的可行性由共用檢查器核對；未啟用完整搜尋時，不保證自訂方法的拒絕結果或最優性。

直接從 Python 呼叫亦可：

```python
from src.experiments.config import load_scenario
from src.experiments.runner import run_scenario

case = load_scenario("configs/ppt_modular/experiment.json")
run_scenario(case, "output/experiments/my_python_run",
             algorithm="label_setting_v04", verify_oracle=True)
```

既有 GUI 可載入 schema v2 設定，runner 會使用其中的 algorithm；目前沒有新增 GUI 的演算法選單。GUI 逐步 Label 播放需要符合既有 trace 格式的演算法。

## 可查看的輸出

- summary.csv：每包結果、抵達、延遲與 Label 數。
- schedule.csv：選定路徑的各跳傳送與接收時間。
- departure_candidates.csv：實際嘗試過的起送時間、判別結果與支配者；不是所有數學上可能的時間，也不包含搜尋提前結束後未展開的候選。
- labels.csv、query_*.json：四欄位 Label、前驅及搜尋事件。受支配不代表前驅紀錄可以刪除。
- reservations.json：兩包規劃後的剩餘容量與 Buffer 預約。
- report/：完整路徑與 Buffer 的數值重播資料。

PPT 第二包的 c4 在 7、8 秒皆通過可行性檢查；8 秒起送的 Label 被較早 Label 支配。`PASS` 表示通過延伸檢查，不等於最後選用。

另外保存一個**人工構造、非 PPT 資料**的回歸檢查：單一 A→D Contact 為 [0,4)，S=4、r=4；D 的既有占用在 0–2 秒為 4，2–3 秒線性降到 0。0、1 秒起送接收會超限，2 秒起送可與釋放量相抵，在第 3 秒抵達。逐 byte 模型下不必等到占用完全歸零才開始接收。結果位於 `output/experiments/ppt_modular_later_start_check_20261012/`，與獨立完整搜尋一致。

## 為什麼研究會跑很多筆？

「很多筆」至少要區分：

1. **同一情境有很多 Bundle／Flow**：增加需求負載，觀察 Contact 容量與 Buffer 的競爭。依序規劃時，一包成功不能代表後面幾十包仍可行。
2. **同一設定用不同亂數種子重複產生需求**：避免結論只來自碰巧容易或困難的來源、目的地與 release 組合，才有樣本變異及信賴區間可報告。
3. **改變節點數、Buffer、大小或負載等設定**：觀察方法在哪些條件下可行、變慢或失效。

目前未重新核對學長論文的實驗段落，因此不把他的 Flow 數當成重複次數，也不指定他到底重跑幾次。確定性演算法對完全相同輸入重跑，路由結果通常不變；重跑只適合評估執行時間波動，不能冒充不同流量樣本。之後比較方法時應使用同一組需求與順序，而非各自抽不同流量。

目前先完成 PPT 案例與上述時間枚舉檢查，沒有執行負載掃描或新的大型實驗。50 項測試通過，涵蓋拆分輸入、相對路徑、替換演算法、原有案例及失敗起送時間後繼續枚舉。這是案例與程式檢查，不是一般正確性證明。aggregate 模型仍未排除同 Contact 傳送重疊，也不模擬實際 Bundle Protocol 或共用 radio。
