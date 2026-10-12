# Label Setting 虛擬碼（繁體中文註解版）

2026-10-13。這是現行 frozen v04 **有限時間格點、aggregate quota** 搜尋及逐包預約的合併流程說明；不是新演算法。對應 [`sequential_label_setting_v04.md`](sequential_label_setting_v04.md)、[`proposed_v04.py`](../src/validation/proposed_v04.py) 與 [`runner.py`](../src/experiments/runner.py)。

```text
輸入：Contact Plan C、目前剩餘容量 R、前包已預約占用 O、節點 Buffer 上限 M、
      Bundle b=(來源 src, 目的地 dst, 產生時間 g, 大小 S)、時間格點 Δ、上限 T

01  固定本包搜尋期間的 R 與 O
    // 候選 Label 只是互斥的路徑選擇；搜尋中不預約全域資源。

02  if O_src(g) + S > M_src: return NO_ROUTE_ON_GRID
    // 來源在 Bundle 產生時須能容納整包。這是現行 v04 的檢查。

03  L0 ← (c⊥, g, ⊥, ⊥); Q ← {L0}; Labels ← {L0}; solution ← none
    // c⊥ 是起點的虛擬 Contact；Q 依完整抵達時間 A 排序。
    // Labels 保留前驅紀錄；未先決定路徑的跳數。

04  while Q is not empty:
05      L ← ExtractMin(Q, A)
        // 每次取出 Q 中完整抵達時間最早的一個 Label。

06      if L is inactive: continue
        // 已被其他 Label 支配的舊項目可能仍在 Q；不再展開。

07      if node(L) = dst:
08          solution ← TraceBack(L); break
            // 取出有效的目的地 Label 才結束搜尋；沿 pred 還原 Contact 與起送時間。
            // 此處尚未更新 R 或 O。

09      for each outgoing Contact c of node(L):
10          if vol_L(c) + S > R[c]: continue
            // vol_L(c) 由 L 的前驅路徑計算，表示本候選已用的 c 資料量。
            // R[c] 是總剩餘資料量，不是時段互斥表。

11          first ← max(A(L), start(c))
12          last  ← end(c) − S / rate(c)
            // 起送不得早於整包抵達或 Contact 開始；最後 byte 要在窗口內送完。

13          for every grid time s ∈ [first, last], step Δ:
            // 保留逐格枚舉；前一個 s 失敗，仍繼續試後一個 s。

14              f ← s + S / rate(c)
15              h ← s + delay(c)
16              Anew ← f + delay(c)
                // f：最後 byte 送出；h：第一個 byte 抵達；Anew：整包抵達。

17              if Anew > T: continue
18              if sender or receiver Buffer check fails: continue
                // 傳送端：A(L)～s 持有 S，s～f 隨發送逐 byte 釋放。
                // 接收端：h～Anew 隨接收逐 byte 增加。
                // 全程加上已接受前包的 O(t)，峰值均不得超過 M。

19              N ← (c, Anew, s, pred=L)
                // 完成本跳檢查後才建立候選 Label；目前尚未加入 Q。

20              compare N with all active Labels at node(N)
                // 包括先前已展開但仍有效的 Label。
                // 支配條件：較早抵達、能持包等到對方抵達、各 Contact 前綴用量不更多。

21              if an existing Label dominates N: register N inactive in Labels; continue
22              mark Labels dominated by N inactive; register N in Labels and Q
                // 保留被支配 Label 的前驅紀錄，避免切斷其他路徑的回溯鏈。

23  if solution is none: return NO_ROUTE_ON_GRID
    // Q 耗盡，只表示此有限格點與現行模型下找不到路徑。

24  if independent complete-route validation fails: STOP_AND_SAVE_CASE
    // 驗證整條路徑及排程；若和同模型獨立檢查不符，不提交資源。

25  commit selected route to R and O; return solution
    // 只對選定的完整路徑扣除 Contact 容量並預約沿途 Buffer。
    // 下一包開始搜尋時，才使用更新後的 R 與 O。
```

## 相對於網站原版的必要更正

網站原版在取出目的地後寫 `return TraceBack(L)`，後面卻另寫「驗證並預約」；直接回傳會使後者無法執行。上面改為 **回溯後跳出搜尋迴圈 → 獨立驗證 → 提交預約 → 回傳**。這是合併展示搜尋與執行層時的控制流程修正，沒有修改 frozen v04 的可行性、枚舉或支配判別式。

接收端的檢查只到本跳整包抵達；接收後能否繼續持包等待，在延伸下一跳時檢查。若日後預先產生「可用開始時間」，它須和第 13～18 行在同一模型下等價，不能只判斷接收點是否完全空閒。
