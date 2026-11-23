# 演算法程式（註解版）

只包含本方法的演算法，不含對照組、窮舉 oracle、拓樸產生與實驗程式。

邏輯與 `src/experiments/dtn_validation/dtn/` 完全相同（去掉註解後的語法樹一致），只加上中文註解。實驗仍以原資料夾為準；**修改演算法時要兩邊一起改**。

## 建議閱讀順序

1. `model.py`：資料結構。
   - Contact、Problem
   - Curve（O_n 的 ts、ls、rs，以及 left、right、peak、add）
   - ramp、lag
2. `validate.py`：規則本身。
   - 三種節點的 Buffer 規則：source_ok、relay_ok、destination_ok
   - 連線規則：hop_ok
   - 整條排程的檢查：validate
   - 排定後寫入狀態：commit
3. `ours.py`：搜尋，依呼叫順序排列。
   - candidate_range
   - 三個 filter 與 solve_region
   - search
   - backtrack、plan
4. `example.py`：教材第 4、9 章的例子，可以直接執行。

## 執行例子

```
cd src
python3 -m algorithm.example
```

輸出（收完才轉）：c1 在 115 出發、c2 在 125 出發、135 到 C。

輸出（邊收邊轉）：c1、c2 都在 110 出發、120 到 C，B 的 O_n 不變。
