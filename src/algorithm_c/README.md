# 演算法 C 版

本方法的完整演算法，用 C 重寫：收完才轉和邊收邊轉都支援，每一行都有中文註解。

和 Python 版（`src/algorithm/`）的對應：

| C 檔案 | 對應 Python | 內容 |
|---|---|---|
| `rat.h` | `fractions.Fraction` | 精確分數：64 位元分子與分母，中間運算用 128 位元，溢位時報錯並停止 |
| `dtn.h` | — | 所有結構與函式宣告 |
| `curve.c` | `model.py` | 區間清單、Curve（O_n）、ramp、lag |
| `rules.c` | `validate.py` | stay_ok、三種節點的規則、hop_ok、validate、commit |
| `search.c` | `ours.py` | 區間運算、candidate_range、solve_region、三個 filter、search、backtrack、plan |
| `main.c` | — | 教材例子，以及讀輸入檔逐包規劃 |

和 Python 版唯一的差別是 `commit` 會直接修改 Problem，Python 版則是回傳一個新的。

## 編譯與執行

```
make
./dtn example        # 教材第 4、9 章的例子
./dtn 輸入檔          # 依序規劃輸入檔裡的每一包
```

輸入檔格式寫在 `main.c` 開頭。

## 驗證

`compare_with_python.py` 會用同樣的案例，逐包比對 C 版和 Python 版的排程。

```
python3 compare_with_python.py --small 3000 --random 3
```

2026-11-23 的結果：

| 案例 | 包數 | 不同 |
|---|---|---|
| 小案例，收完才轉 | 5,961 | 0 |
| 小案例，邊收邊轉 | 5,961 | 0 |
| random_20n 3 個種子，收完才轉 | 300 | 0 |
| random_20n 3 個種子，邊收邊轉 | 300 | 0 |

速度：random_20n 的 300 包，Python 約 27 秒，C 約 0.5 秒。

其他檢查：

- 40 節點、1,600 連線、300 包（2 個種子 × 兩種模式），分數沒有溢位，回放全部通過，每組約 1.5～2 秒。
- 用 AddressSanitizer 和 UBSan 跑過，沒有記憶體錯誤。

**注意**：實驗目前仍以 Python 版為準。修改演算法時，Python 版、Python 註解版和 C 版三份都要改，改完要重跑 `compare_with_python.py`。
