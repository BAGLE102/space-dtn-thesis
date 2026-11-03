# Store-and-forward 區間 Label 實驗

`store_label.py` 是現行候選搜尋；其餘是驗證、實驗與分析程式。此資料夾的 `interval_label_validation.py` 是實驗用副本（`buffer_filter` 多了 `EX` 參數），不取代 `src/experiments/` 的同名檔。

Contact Plan 原檔依 `docs/ring_road_contact_plan_source_v01.md` 下載，再用環境變數 `TOPOLOGY_DIR` 指定其資料夾的絕對路徑（原檔不納入 Git）：

```bash
cd src/experiments/store_forward
python3 ex_store.py                          # 文件三個手算範例
python3 store_check.py 1500 50000            # 與 1/16 秒格點窮舉比對（另一批種子 70000）
python3 neg_earliest.py                      # 只存最早時間的負控制
python3 rr_run3.py results_sf.jsonl 150      # 新版與缺少的對照組
python3 an3.py ../../../output/store_forward_20261103   # 彙整
```

`rr_run2.py` 是舊 `ours`／`store`／SR-CGR 的執行器；第一輪 relay、walker16 當時由未加硬性時限的前一版執行。
