# 論文用英文虛擬碼 v01

日期：2026-10-12。LaTeX 原始檔：`docs/thesis_pseudocode_v01.tex`。

本次只整理現行方法的表示法，未修改演算法、程式或重跑實驗。依據為 `sequential_label_setting_v04.md`、`current_algorithm_snapshot_v01.md`、`presentation_1007_definition_revision_v01.md`，並核對 `src/validation/proposed_v04.py` 與 `src/experiments/runner.py`。

## Label 定義

\[
L=(c(L),A(L),s(L),p(L)).
\]

| 符號 | 定義 |
|---|---|
| \(c(L)\) | 此候選路徑最後使用的 Contact |
| \(A(L)\) | 整個 Bundle 完整抵達該 Contact 接收端的時間 |
| \(s(L)\) | 在該 Contact 開始傳送的時間 |
| \(p(L)\) | 前驅 Label；即原先的 pred |

Label 編號與 Contact 編號獨立，例如 \(L_2=(c_4,8,7,L_0)\)。不用 \(c_i\) 表示 \(L_i\) 的欄位，避免誤認兩者共用編號。

起始 Label：\(L_0=(c_\bot,g,\bot,\bot)\)。\(c_\bot\) 是查詢專屬虛擬 Contact，其接收端為來源節點；不占容量、不進入輸出路徑。\(\bot\) 表示無值。

候選路徑在 Contact \(c\) 的累積用量以 \(\operatorname{vol}_L(c)\) 表示：它是「沿前驅鏈計算該 Contact 出現次數，再乘本包大小」。**這是衍生計算，並未把 U 加回 Label。** 現行程式內部仍快取此數值，本文沒有宣稱程式已移除快取。因現行模型允許重訪 Contact，quota 與一般 dominance 仍須考慮這項資訊，不能直接刪掉判別條件。

## 三個演算法的用途

1. **Label Setting for One Bundle on a Finite Time Grid**：取出最早抵達的有效 Label，檢查所有 outgoing Contacts，枚舉各 Contact 的格點起送時間。通過時窗、容量與兩端 Buffer 檢查後，建立候選 Label；再做 dominance，通過者加入 Q。取出目的地 Label 後回溯。
2. **Sequential Planning and Reservation**：依既定順序逐包呼叫搜尋。完整路徑經獨立驗證後，才扣除 Contact 容量並加入整條路徑的 Buffer 預約；失敗驗證立即保留案例並停止。
3. **Route and Departure-Time Reconstruction**：從目的地 Label 沿 pred 回到起點，取得各跳 Contact 與起送時間，再反轉順序。不需預先知道跳數 K。

Dominance 的完整條件列於 LaTeX 式 (7)–(8)：同節點、較早或同時抵達、能在這段時間持有整包，且各 Contact 的路徑用量均不更多。只早到不能直接刪掉晚到的 Label。

## 容易講錯的部分

- **Buffer 在延伸時就檢查**：檢查傳送端從目前抵達、等待到送完，以及接收端從第一個 byte 到整包收完。接收後要等多久尚取決於下一跳，於下一次延伸檢查。
- **Dominance 在新候選加入 Q 前執行**。已展開但仍有效的 Label 也參與比較。被支配紀錄如果仍是其他 Label 的前驅，不得刪掉其回溯資料。
- **Q 是 min-priority queue**，不是依節點只留一筆的集合。active sets 與前驅紀錄另行維護，不增加數學 Label 欄位。
- **保留所有格點時間枚舉**，不是每個 Contact 只試最早時間。Buffer 峰值則檢查完整分段線性函數，不能只抽查格點。
- 來源在 release 時能否容納整包的檢查仍在 frozen v04；這裡如實列出，沒有擅自增加或移除。
- **R 是總資料量，不是可用傳送時段**。本版未排除同 Contact 傳送時間重疊，也未加入 radio 互斥。
- `NO_ROUTE_ON_GRID` 與 `TIMEOUT` 不同。逾時不能當作無路徑。
- 此版本是可供論文方法章使用的表示形式，不代表一般正確性、連續時間最優性或多包聯合最優已完成證明。

## 與程式的對照

| 論文表示 | 程式／語意 |
|---|---|
| \(c(L),s(L)\) | `hop` 中的 Contact ID 與起送時間 |
| \(A(L),p(L)\) | `a`、`pred` |
| \(\operatorname{node}(L)\) | `v`；可由 Contact 接收端取得，起始 Label 例外 |
| \(\operatorname{vol}_L(c)\) | `usage[c]`，由前驅鏈決定的快取 |
| \(\mathcal A_v\) | `active=True` 且目前節點為 v 的 Label，含已展開者 |
| \(\mathcal H\) | 保留可回溯的 Label 紀錄；不要求保存從未入隊的受支配候選 |

LaTeX 使用 `algorithm` 與 `algpseudocode`。合併進學校論文模板時，保留套件、符號／判別式與三個 algorithm 區塊；移除本文的 `documentclass`、`geometry`、標題與人工分頁即可。演算法編號應交由論文模板自動產生。

編譯狀態：已開啟 Codex LaTeX 編輯器並嘗試內建編譯；編譯器回報 `Unable to find standard directories for platform`，未產生成功編譯確認。此為工具執行環境錯誤；目前保留原始檔，PDF 版面尚未驗證。
