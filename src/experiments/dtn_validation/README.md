# Space DTN 路由驗證

比較三種方法，輸出 Excel 與圖片：

- **本方法**：區間 Label（`dtn/ours.py`），兩種轉送模型共存：store-and-forward（預設）與 cut-through（`--cut-through`，`Problem.ct=True`）
- **窮舉**：1/16 秒格點，單包（`dtn/oracle.py`）
- **SR-CGR**：簡化版，`sr1` 與 `sr10`（`dtn/srcgr.py`）

## 執行（Linux、Python 3.8 以上）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run_all.sh
```

建議用 `nohup ./run_all.sh > run.log 2>&1 &` 放背景跑。中斷後再執行同一個指令，會接著跑未完成的部分（已完成的一組或一個案例不會重跑；進行中的那一組會重來）。實驗 B 依序跑，別同時開多份，否則計算時間會互相干擾。

先試跑：

```bash
python3 run_validation.py --cases 50 --out results_test/validation.jsonl
python3 run_performance.py --seeds 2 --bundles 30 --out results_test/performance.jsonl
python3 make_report.py --results results_test
```

要改參數請改 `config.json`，並換一個結果資料夾；同一資料夾只用同一份參數，不然舊結果會被當成已完成。

## 輸出

`results/report.xlsx`：

| 工作表 | 內容 |
|---|---|
| `Summary` | 實驗 B 依條件彙整 |
| `Pairwise` | 本方法對 `sr1`、`sr10` 的配對比較 |
| `Bundles` | 每一包的結果 |
| `Oracle`、`Oracle_Summary` | 實驗 A 逐筆與彙整 |
| `Resources` | 節點 Buffer 峰值、contact 使用率 |
| `Config` | 環境、參數、拓樸 SHA-256 |

`results/figures/`（PNG、SVG；圖上文字為英文，避免 Linux 缺中文字型）：

| 圖 | 內容 |
|---|---|
| `fig1` | 送達率對 Buffer |
| `fig2` | 送達率對負載 |
| `fig3` | 所有方法都送達的包之平均延遲 |
| `fig4` | 與 `sr10` 的逐包延遲差 |
| `fig5` | 每包計算時間 |
| `fig6` | 本方法與窮舉的比對 |

種子數至少 5 時，圖上是 95% 信賴區間；較少時改畫每個種子的點。

## 怎麼看結果

先看 `Oracle_Summary`：`later`、`missed`、`extra`、回放失敗都要是 0。`Summary` 的 `Validation failures` 也要是 0。不是 0 就代表程式或模型有問題，先別用效能數字。

`earlier` 不一定是錯：最佳解可能落在格點之間，但要逐筆確認。

未跑到的包不算未送達。比較延遲時請用 `Pairwise`：`Summary` 的延遲只統計各方法自己送達的包，送得多的方法可能因此看起來較慢。

## 模型假設

- 轉送模型：預設收完整包才轉送（s₂ ≥ A）；`--cut-through` 時中繼可邊收邊送，條件 s₂ ≥ max(h, A − S/r_out)（已開始收，且送不能比收快）。同一節點可同時收送。
- 來源：從 `g` 起持有整包，邊送邊釋放。
- 中間節點：邊收累積，邊送釋放（占用 = 已收 − 已送）；store-and-forward 時收完後才開始送。
- 目的地：邊收累積，**收完的瞬間交付並離開**。交付後的資料不再占用 Buffer。
- 依固定順序逐包規劃，前面的包不會改動。
- 窮舉只驗證單包在目前背景下的最早抵達，不是所有包的整體最佳。

`sr1`、`sr10` 是依定義實作的簡化版，不是完整 CGR：來源一次算完整路徑，選路時不看 Buffer，失敗就試下一條，沒有實際運作時的逐跳重算。

拓樸與需求都是隨機生成，相同種子結果相同。參數是研究假設，論文要明確寫出，也不能當成真實網路的代表。
