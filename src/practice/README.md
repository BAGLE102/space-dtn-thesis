# 重寫練習

目標：不靠 AI，自己把演算法寫出來。

- `my_dtn.py`：每個函式都只有名稱、說明和例子，內容要你自己寫。
- `check.py`：檢查程式。每一關先跑教材例子，再拿隨機小案例和原本的程式逐一比對。
- 答案在 `src/algorithm/`，真的卡住再看。

## 怎麼做

```
cd src/practice
python3 check.py 1      # 寫完關卡 1 就跑
python3 check.py 1-3    # 一次檢查好幾關
python3 check.py all
```

答錯時，檢查程式會印出哪一題、你的答案和正確答案。

## 關卡

| 關 | 內容 | 對應教材 |
|---|---|---|
| 1 | ramp、lag | 第 3、5 章 |
| 2 | Curve 查詢：left、right、top、between、peak | 第 4 章 |
| 3 | Curve.add | 第 4 章 |
| 4 | 規則：stay_ok、三種節點、hop_ok、validate | 第 4、5、11 章 |
| 5 | 區間：subtract_open、merge、candidate_range | 第 6、11 章 |
| 6 | commit | 第 11 章 |
| 7 | 簡單版搜尋：格點上試出發時間，和窮舉比對 | 第 7 章 |
| 8 | 正式版搜尋：區間 Label、Buffer 篩選、回推，和原版比對 | 第 9、11 章 |

關卡 7 先求「對」：概念最直接，速度慢沒關係。關卡 8 才求「快」，可以先用格點逐一試，再換成 solve_region。

全部 8 關都通過時，代表你寫出來的程式和原版在測試案例上結果完全相同。
