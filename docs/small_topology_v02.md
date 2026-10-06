# Small topology validation v02

[D] 人工構造的 M0 單元範例，非衛星實測資料，也不是 Paper A/B 的實驗結果。固定 topology：A 為 source、E 為 destination；B/C/D 為中繼。b=(A,E,0,4 MB)，所有 propagation delay=1 s，buffer 不限制。R 是 M0 admission quota，並非未提供 busy calendar 的實際預約模型。

## Contact plan

| Contact | Sender | Receiver | Start s | End s | Rate MB/s | δ s | Q MB | R MB |
|---|---|---|---:|---:|---:|---:|---:|---:|
| c1 | A | B | 0 | 4 | 2 | 1 | 8 | 8 |
| c2 | B | E | 3 | 6 | 2 | 1 | 6 | 3 |
| c3 | A | C | 0 | 5 | 1 | 1 | 5 | 5 |
| c4 | C | E | 6 | 10 | 2 | 1 | 8 | 8 |
| c5 | A | D | 1 | 6 | 1 | 1 | 5 | 5 |
| c6 | D | E | 8 | 12 | 2 | 1 | 8 | 8 |
| c7 | C | D | 5 | 8 | 2 | 1 | 6 | 6 |
| c8 | B | C | 0 | 4 | 2 | 1 | 8 | 8 |

## 路徑比較

| Route | Contact sequence | Arrival | 結果 |
|---|---|---:|---|
| 1 | c1,c2（A→B→E） | 6 s，僅忽略 capacity 時 | c2 的 R=3<4，不可行 |
| 2 | c3,c4（A→C→E） | 9 s | 最早 feasible |
| 3 | c5,c6（A→D→E） | 11 s | 可行但較晚 |
| 4 | c3,c7,c6（A→C→D→E） | 11 s | 可行；D 的晚到 label 被支配 |

c1,c8,c4 不算時間可行 route：A→B 在 3 抵達，c8 傳送 2 秒會到 5，超過 c8 end=4。

## Label evolution

U 使用 arrival 由小到大。同一次 expansion 按 contact ID 排序；未被接受的候選用帶星號 label 記錄，沒有放入 U。

| Step | Current Label | Candidate Contact | s | x | f | Arrival | Capacity Check | Result / U after step |
|---|---|---|---:|---:|---:|---:|---|---|
| 0 | — | — | — | — | — | 0 | — | 初始化 L0=(A,0)；U=[A0] |
| 1 | L0=(A,0) | c1 A→B | 0 | 2 | 2 | 3 | 8≥4 | 接受 L1=(B,3)；U=[B3] |
| 2 | L0=(A,0) | c3 A→C | 0 | 4 | 4 | 5 | 5≥4 | 接受 L2=(C,5)；U=[B3,C5] |
| 3 | L0=(A,0) | c5 A→D | 1 | 4 | 5 | 6 | 5≥4 | 接受 L3=(D,6)；U=[B3,C5,D6] |
| 4 | L1=(B,3) | c2 B→E | 3 | 2 | 5 | (6) | 3<4，FAIL | 拒絕；不建立 E6；U=[C5,D6] |
| 5 | L1=(B,3) | c8 B→C | 3 | 2 | 5 | — | 未執行；已於 window 失敗 | 5>4，拒絕；U=[C5,D6] |
| 6 | L2=(C,5) | c4 C→E | 6 | 2 | 8 | 9 | 8≥4 | 接受 L4=(E,9)；U=[D6,E9] |
| 7 | L2=(C,5) | c7 C→D | 5 | 2 | 7 | 8 | 6≥4 | L5*=(D,8) 被 L3=(D,6) 支配；U=[D6,E9] |
| 8 | L3=(D,6) | c6 D→E | 8 | 2 | 10 | 11 | 8≥4 | L6*=(E,11) 被 L4=(E,9) 支配；U=[E9] |
| 9 | L4=(E,9) | — | — | — | — | 9 | — | ExtractMin 到目的地，回傳 c3,c4；U=[] |

step 4 的括號 (6) 是用於說明的 hypothetical arrival；正式 Extend 在 capacity 失敗處即返回，不生成 label。

## 最終排程

| Contact | 等待 | Transmission interval | Last-byte arrival |
|---|---|---|---:|
| c3 A→C | 無 | [0,4) | 5 |
| c4 C→E | C 等待 [5,6) | [6,8) | 9 |

搜尋期間 R 沒改變。若最後獨立提交成功，c3 的 quota 由 5 降至 1、c4 由 8 降至 4；這只是說明提交語意，不是本階段真的操作任何網路。

## 獨立算術核對

本次以有理數算術列舉此 acyclic topology 的所有 source-destination contact sequences：忽略 R 時四條時間可行 route 的 arrival 為 6、9、11、11；加入 quota 後三條可行 route 為 9、11、11，最優為 9。所有輸入 R≤Q；每個表格時間均由 max(a,start)+S/r+δ 算出。

這是確定性單一案例，無隨機樣本；平均、標準差與 confidence interval 不適用於演算法效能評估。尚無 runtime / delivery ratio 實驗；不要把此表標為 Preliminary Performance Results。
