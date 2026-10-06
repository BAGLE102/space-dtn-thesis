# 1007 報告簡報：定義表示更新

日期：2026-10-06；報告日期：2026-10-07。

來源為使用者提供的 `F:/1007.pptx`。另存修正版，保留原始檔與21頁圖解版型。

輸出：`output/presentations/1007_定義更新版_v02_20261006.pptx`。

## 更新內容

- Label 改以 `L_i=(c_i,A_i,s_i,pred_i)` 呈現：最後使用的 contact、整包完整抵達時間、實際起送時間、前一個 label。
- 目前實體節點由最後 contact 的 receiver 取得；初始化使用查詢專屬虛擬 contact c0，其 receiver 為 source，A0=g，s0無值，pred0為空。
- 全部 Q 中的完整 labels 與回溯圖同步更新，按 A 取出。
- R_c 用「剩餘可分配資料量」解釋，歸類為中央維護的資源狀態；不當成靜態 contact 欄位，也不當成可用傳輸時間。
- 補上 r=4 MB/s、各 contact 的傳播延遲、初始 R、Δ=1秒與T=12秒。
- 修正「只有7或8秒可起送」的敘述，明列它是Δ=1秒格點模型的候選時間。
- 支配範例改用相同前驅、相同 contact 說明路徑用量相同，仍保留整段等待可行性的檢查。
- 更新講者備註並修正來源簡報插入contact表後的重複頁碼。全篇使用標楷體。

## 與現行研究基準的關係

此更新是**資料表示調整**，未改動 `sequential_label_setting_v04.md`、`current_algorithm_snapshot_v01.md` 或驗證程式。

舊核心狀態 `(v,a,U)` 可由新版 `(c,A,s,pred)` 的前驅鏈取得：

- v = receiver(c)，起始label例外使用source。
- a = A。
- U[d] = S × 前驅鏈中實際 contact d 的出現次數；不計虛擬contact。

因此未直接刪除路徑用量的資訊或 quota/dominance 的必要條件，只是不再額外顯示、儲存一份 U 欄位。這個對應依賴保留完整前驅鏈，包含已受支配但仍為其他label前驅的紀錄；不得刪掉這些重建資料。

Extension 仍須比較「前綴在下一 contact 的用量 + S ≤ R_c」。一般 dominance 仍須同 receiver、A1≤A2、整段持包等待可行，且第一個前綴每個 contact 用量不更多。上述路徑用量可回溯計算。本例第12頁只示範同前驅與同contact的充分情形，不能把它誤寫成所有label的完整支配規則。

本次未重新證明一般演算法、未改變搜尋時間集合、未做效能比較，也未加入 transmission calendar。

## 案例資料與保留的界線

數值對照 `output/validation/walkthrough_input.json`：第一包c1→c2在8秒完整抵達，第二包c4→c5在12秒完整抵達。最後 R=(0,0,4,4,0,4,2,4) MB。

c7 的理論 volume 為4MB，但案例輸入指定剩餘可分配資料量2MB。其減少原因未建模，不能說是第一包扣除所致，也不能假設所有R均初始化為完整volume。

Aggregate容量未檢查已接受bundles的鏈路時段重疊。保留既有buffer預約、逐byte接收與釋放、完整接收後轉送、無副本假設。沒有新增實際鏈路無衝突或多包聯合最優的claim。

## 檢查

- 保留21頁、原生contact表與模板尺寸。
- 檔案結構、字型政策、原生表格及Artifact Tool重新匯入檢查。
- 所有頁面渲染後逐頁查看，舊的U式label與Q用量字串已從投影片正文移除。
- 自動版面檢查仍可能標記拓樸中的文字框交疊，人工查看其與既有圖一致；未宣稱所有圖元完全不交疊。
- 未在原生Microsoft PowerPoint中操作驗證。

## 明天報告前優先確認

第4頁的四個label欄位、第6頁的contact及資源輸入、第12頁等待與支配條件、第20頁pred回溯，以及第3頁aggregate容量模型的限制。
