# Cut-through 共存版（2026-11-11）

老師堅持要支援 cut-through。依使用者決定：
- 起送規則：邊收邊送，第一個 byte 到達後任何時間都可起送，但送不能比收快。
- 實作方式：與 store-and-forward 共存，用 `Problem.ct` 切換，預設 store-and-forward。
- 本文件記錄模型、程式改動、驗證結果與未決事項。

## 模型

中繼節點的符號：
- h = s₁ + δ₁：開始收
- A = h + S/r₁：收完
- f = s₂ + S/r₂：送完

| | store-and-forward（預設） | cut-through（`ct=True`） |
|---|---|---|
| 起送條件 | s₂ ≥ A | s₂ ≥ h 且 f ≥ A，即 s₂ ≥ max(h, A − S/r₂) |
| 前一跳到下一跳的最小間隔 lag | S/r₁ | max(0, S/r₁ − S/r₂) |
| 中繼占用 own(t) | 已收 − 已送 | 同左；最高點可能小於 S |

O_n 的資料結構（ts／ls／rs）不變。來源、目的地的規則不變。

## 程式改動

| 檔案 | 改動 |
|---|---|
| `dtn/model.py` | `Problem` 新增欄位 `ct`（預設 False）；新增 `lag(P, c1, c2)` |
| `dtn/validate.py` | `relay_ok`：依 `ct` 檢查起送條件；`commit`：cut-through 時中繼曲線改用 h、A、s₂、f 的已收 − 已送 |
| `dtn/ours.py` | 下一跳最早起送 head = L1.lo + δ₁ + lag；s₁\* = min(L1.hi, s₂ − δ₁ − lag)；backtrack 同規則 |
| `dtn/ours.py` `buffer_filter` | 檢查點改為 own 的一般式；切點改為 x、x − S/r₂、x + lag、x + lag − S/r₁、clamp，以及 L1.hi + δ₁ + S/r₁（clamp 後 s₂ 越過固定的 A） |
| `dtn/srcgr.py` | 對照組 SR-CGR 跟隨同一轉送模型（每跳盡早起送用同一個 lag） |
| `run_validation.py`、`run_performance.py`、`walker/walker_run.py` | 新增 `--cut-through` 參數 |

store-and-forward 時，lag = S/r₁，新的切點集合與檢查點和舊版相同。

## 驗證（測試，非證明）

1. **store-and-forward 回歸**：300 個小案例、596 包，依序規劃並提交。新舊程式的本方法、sr1、sr10 排程完全相同（0 差異）。
2. **store-and-forward 對窮舉**（1/16 秒格點，3,000 案例、5,961 包）：較晚 0、漏解 0、多解 0，回放全部通過。
3. **cut-through 對窮舉**（同上設定）：
   - 相同 2,352、較早 6（格點外的解）、較晚 1。
   - 回放全部通過。
4. **cut-through 對 store-and-forward**（各案例第一包，背景相同）：
   - cut-through 較早 289 包，平均早 0.92 秒。
   - 只有 cut-through 有解 58 包。
   - cut-through 較晚 0 包。

### 開發中修正的錯誤

第一版漏了切點 L1.hi + δ₁ + S/r₁。clamp 之後 h、A 固定，s₂ 越過 A 時，own(A)、own(s₂) 會折彎。這造成案例 126 比窮舉晚 0.25 秒，加入切點後改為相同。store-and-forward 不受影響，因為該點等於 clamp。

### 剩下 1 個較晚（案例 2663）：驗證器在超載背景下的寬鬆處理

窮舉找到的排程，新包開始進入節點 2 的時刻 h，背景占用的右極限是 3，已經超過 M = 2。

`stay_ok` 在起點只在 own(h) > 0 時才檢查；own(h) = 0，所以略過。但 h 之後一瞬間 own > 0，背景仍接近 3，上確界超過 M。本方法的細緻檢查在段內是用上確界解，所以排除了這個排程。

這只會在背景本身超過 M 時發生。測試用的 `small_case` 背景是隨機梯形，可能超過 M；正常逐包提交的背景不會超過 M。

**待決定**：要不要把 `stay_ok` 起點改為不論 own 是否為 0 都檢查 O.right(start) ≤ M。這會改變限制的定義，需要使用者確認。

## 尚未完成

- 單包最早性的正式證明（store-and-forward 與 cut-through 都還沒有）。
- 隨機拓樸與 Iridium 的 cut-through 效能比較（進行中）。
- 協定依據：RFC 9171 沒有明定 cut-through，見 `cut_through_literature_and_advisor_brief_20261102.md`。
