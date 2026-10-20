# 原PPT拓譜的長contact版本

這是人工測試輸入：沿用X、A、B、C、D五個節點、八條連線及原兩包需求。每包4MB、各節點Buffer上限4MB，速率4MB/s，傳輸需1秒；c2/c5/c6傳播延遲1秒，其餘0。規劃上限40秒。

| Contact | 方向 | 新時窗（秒） | 長度（秒） | 完整初始容量（MB） | 沿用原剩餘容量（MB） |
| --- | --- | --- | ---: | ---: | ---: |
| c1 | X→B | 2～12 | 10 | 40 | 4 |
| c2 | B→D | 8～18 | 10 | 40 | 4 |
| c3 | A→B | 1～11 | 10 | 40 | 4 |
| c4 | A→B | 12～28 | 16 | 64 | 8 |
| c5 | B→D | 20～36 | 16 | 64 | 4 |
| c6 | A→C | 1～18 | 17 | 68 | 4 |
| c7 | C→D | 16～30 | 14 | 56 | 2 |
| c8 | C→D | 4～14 | 10 | 40 | 4 |

不只延長結束時間，也重新安排部分起點：同一對端點的c3/c4、c2/c5、c8/c7不重疊，避免無意間增加平行通道。本次不是只改一個參數的控制實驗。

## 可替換的輸入

- `contacts.csv`、`topology.json`、`experiment.json`：初始容量採速率×時窗長度，表示新的完整可用contact。
- `contacts_same_quota.csv`、`topology_same_quota.json`、`experiment_same_quota.json`：使用相同新時窗，但沿用原剩餘quota。這是隔離容量增加影響的人工資源上限設定；沒有據此捏造其他bundle的時間預約。
- `bundles.json`：第一包X→D、g=0、4MB；第二包A→D、g=1、4MB，依此順序規劃。

兩份experiment的algorithm均明確標記 `interval_candidate_not_implemented`，避免被誤認成已完成的新方法。`time_step=1`只是既有載入器的格式相容欄位，**不代表區間方法逐秒枚舉**；在新方法實作後，須重新定義其輸入schema。

## 圖與檢查

- `output/long_contacts_20261021/long_contact_topology.png`／`.svg`：左為拓譜，右為從0秒開始的完整contact時間軸。
- 同目錄 `contact_comparison.csv`：原始與新時窗、兩種容量設定。
- 同目錄 `input_validation.json`：兩份輸入通過既有格式／數值／參照檢查，另外確認所有時窗至少10秒、相同方向不重疊。

只準備輸入，未執行任何路由、枚舉或效能測試，沒有宣稱已找到路徑、改善接受率或產生多段可行區間。時窗拉長後可能產生較多選時機會，但實際Buffer切割仍依前包接受的排程而定。

重建：`python -m src.experiments.prepare_long_contact_topology`。本次不修改1021簡報及原拓譜。
