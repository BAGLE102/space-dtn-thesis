# 區間 Label 候選方法：符號與虛擬碼

日期：2026-11-02。狀態：候選方法，尚未完成連續時間實作與正式證明。

模型：依序逐包規劃；只要有資料可送就能開始轉；不同 contact 可同時收送；不採用「不可回到已訪節點」規則，允許 Buffer Detour；同一包的兩次造訪不可在同一節點重疊；不另設獨立配額。

## 符號

### 輸入

| 符號 | 意義 | 單位 |
|---|---|---|
| `Contacts` | 所有 contact 的集合 | |
| `Bundles` | 依固定順序排列的 bundle 集合 | |
| `c` | 一條 contact | |
| `u(c)`、`v(c)` | `c` 的傳送端、接收端 | |
| `a(c)`、`b(c)` | `c` 的開始、結束時間 | 秒 |
| `r(c)` | `c` 的傳輸速率 | MB/s |
| `δ(c)` | `c` 的傳播延遲 | 秒 |
| `n` | 一個節點 | |
| `M`、`M_n` | 所有節點的 buffer 上限；節點 `n` 的上限 | MB |
| `B` | 目前處理的 bundle | |
| `source(B)`、`destination(B)` | `B` 的來源、目的節點 | |
| `S` | `B` 的大小 | MB |
| `g` | `B` 在來源可開始傳送的時間 | 秒 |
| `D*` | `B` 的抵達期限 | 秒 |
| `F[c]` | `c` 已預約的傳送時段集合 | 秒 |
| `[x, y)` | `F[c]` 中的一段預約 | 秒 |
| `O_n(t)` | 前面各包在節點 `n`、時間 `t` 的占用 | MB |

`O_src`、`M_src`、`O_dst`、`M_dst` 分別是來源與目的節點的 `O_n`、`M_n`。

### 時間

| 符號 | 意義 | 算法 |
|---|---|---|
| `s` | 起送時間 | 決策 |
| `d(c)` | 傳完一包所需時間 | `S / r(c)` |
| `f` | 傳完時間 | `s + d(c)` |
| `h` | 第一個 byte 抵達時間 | `s + δ(c)` |
| `A` | 整包收完時間 | `s + d(c) + δ(c)` |
| `t` | 檢查 buffer 時的任意時間 | |

### 兩跳之間

| 符號 | 意義 |
|---|---|
| `c1`、`c2` | 前一跳、下一跳 contact |
| `d1`、`d2`、`δ1` | `d(c1)`、`d(c2)`、`δ(c1)` |
| `s1`、`s2` | 前一跳、下一跳起送時間 |
| `h1`、`A1` | 前一跳的 `h`、`A` |
| `U(s2)` | `s1` 的上限：`s2 − δ1 − max(0, d1 − d2)` |
| `s1*(s2)` | `I1` 中不超過 `U(s2)` 的最大值 |
| `已收(t, s)` | 上一跳以 `s` 起送時，到 `t` 已收到的量，介於 0 和 `S` |
| `已送(t, s)` | 下一跳以 `s` 起送時，到 `t` 已送出的量，介於 0 和 `S` |
| `Occ(t, s2)` | `O_n(t) + 已收(t, s1*(s2)) − 已送(t, s2)` |

### Label 與搜尋

| 符號 | 意義 |
|---|---|
| `L = (c, I, pred, Ch)` | Label |
| `I`；`lo(I)`、`hi(I)` | 可達起送區間；區間的頭、尾 |
| `pred`；`SOURCE` | 前一個 Label；第一跳的前驅標記 |
| `Ch` | 目前邊收邊轉段經過的節點集合 |
| `L1 = (c1, I1, pred1, Ch1)` | 從 `Q` 取出的 Label |
| `L_goal` | 取出時已到目的地的 Label |
| `Q` | 待處理 Label 的優先佇列 |
| `key(L)` | 最早完整抵達時間：`lo(I) + d(c) + δ(c)` |
| `Reached[c, Ch]` | 此狀態已到過的起送時間 |
| `New` | 候選時間扣掉 `Reached` 後的新部分 |
| `mode`；`RELAX`；`TRACK` | 搜尋模式；不記 `Ch`；記 `Ch` |
| `NO_PATH` | 期限內找不到路徑 |

`c(L)`、`I(L)`、`pred(L)` 是 `L` 的各欄位。`δ(L)`、`d(L)` 是 `c(L)` 的 `δ`、`d`。

### 暫存

| 符號 | 意義 |
|---|---|
| `C` | 候選起送時間集合 |
| `Head`、`Tail` | `C` 的最早、最晚候選時間 |
| `Seg` | `C` 切出的小段 |
| `Result` | Buffer 檢查後留下的起送時間 |
| `Stream` | `C` 中 `s2 < s1*(s2) + δ1 + d1` 的部分 |
| `Store` | `C − Stream` |
| `ChS` | `Ch1 ∪ {v(c1)}` |
| `schedule` | 最後路徑：依序的 `(c, s)` |
| `PrevL` | 回溯時目前 Label 的前驅 |
| `s_prev` | 回溯時選出的前一跳起送時間 |

## 虛擬碼

```text
Algorithm 1: RoutePlan(Contacts, Bundles, M)

for each bundle B in 固定規劃順序 do
    L_goal ← SearchBundle(B, RELAX)
    if L_goal = NO_PATH then
        記錄 B 無路徑；continue
    end if

    schedule ← Backtrack(L_goal)

    if HasSelfOverlap(schedule) then
        L_goal ← SearchBundle(B, TRACK)
        if L_goal = NO_PATH then
            記錄 B 無路徑；continue
        end if
        schedule ← Backtrack(L_goal)
    end if

    if ValidateSchedule(schedule, B) = FALSE then
        保存失敗案例並停止
    end if

    Commit(schedule, B)
end for
```

```text
Algorithm 2: SearchBundle(B, mode)

Q ← 空的優先佇列，依 key(L) 排序
Reached ← 全部清空

for each c with u(c) = source(B) do
    C ← SourceRange(c)
    C ← SourceBufferFilter(c, C)
    if v(c) = destination(B) then
        C ← DestinationFilter(c, C)
    end if
    Ch ← {source(B)} if mode = TRACK else ∅
    InsertLabels(c, C, SOURCE, Ch)
end for

while Q 不是空的 do
    L1 = (c1, I1, pred1, Ch1) ← 取出 key 最小的 Label

    if v(c1) = destination(B) then
        return L1
    end if

    for each c2 with u(c2) = v(c1) do      // 不檢查 v(c2) 是否走過
        C ← StartRange(c2, L1)
        C ← BufferFilter(C, L1, c2)
        if v(c2) = destination(B) then
            C ← DestinationFilter(c2, C)
        end if

        if mode = RELAX then
            InsertLabels(c2, C, L1, ∅)
        else
            Stream ← C 中滿足 s2 < s1*(s2) + δ1 + d1 的部分
            Store  ← C − Stream

            ChS ← Ch1 ∪ {v(c1)}
            if v(c2) ∉ ChS then
                InsertLabels(c2, Stream, L1, ChS)
            end if
            InsertLabels(c2, Store, L1, {v(c1)})
        end if
    end for
end while

return NO_PATH
```

```text
Algorithm 3: StartRange(c2, L1)

Head ← max(a(c2), lo(I1) + δ1 + max(0, d1 − d2))
Tail ← min(b(c2) − d2, D* − d2 − δ(c2))
C ← [Head, Tail]

for each [x, y) in F[c2] do
    C ← C 移除 (x − d2, y)
end for

return C


SourceRange(c)

Head ← max(a(c), g)
Tail ← min(b(c) − d(c), D* − d(c) − δ(c))
C ← [Head, Tail]

for each [x, y) in F[c] do
    C ← C 移除 (x − d(c), y)
end for

return C
```

```text
Algorithm 4: BufferFilter(C, L1, c2)

n ← v(c1)

將 C 依以下時間點切成多個 Seg：
    · s1* 開始卡住的點
    · O_n(t) 轉折點造成的臨界點

Result ← 空集合
for each Seg do
    if s1*(s2) 不存在 then
        continue
    end if

    解 Occ(t, s2) ≤ M_n，t 從 s1*(s2) + δ1 到 s2 + d2
    將可行的 s2 加入 Result
end for

return Result


SourceBufferFilter(c, C)

保留滿足 O_src(t) + S − 已送(t, s) ≤ M_src 的 s
t 從 g 到 s + d(c)


DestinationFilter(c, C)

保留滿足 O_dst(t) + 已收(t, s) ≤ M_dst 的 s
t 從 s + δ(c) 到 s + d(c) + δ(c)
```

```text
Algorithm 5: InsertLabels(c, C, pred, Ch)

New ← C − Reached[c, Ch]
Reached[c, Ch] ← Reached[c, Ch] ∪ New

for each 連通區間 I in New do
    L ← (c, I, pred, Ch)
    將 L 放進 Q
end for
```

```text
Algorithm 6: Backtrack(L_goal)

L ← L_goal
s ← lo(I(L))
schedule ← [(c(L), s)]

while pred(L) ≠ SOURCE do
    PrevL ← pred(L)
    s_prev ← I(PrevL) 中不超過 s − δ(PrevL) − max(0, d(PrevL) − d(L)) 的最大值
    將 (c(PrevL), s_prev) 加到 schedule 最前面
    L ← PrevL
    s ← s_prev
end while

return schedule
```

```text
Algorithm 7: HasSelfOverlap(schedule)

對 schedule 中每個節點的每兩次造訪：
    if 後一次的 h < 前一次的 f then
        return TRUE
    end if
end for

return FALSE
```

```text
Algorithm 8: ValidateSchedule(schedule, B)

檢查：
    · 路徑從 source(B) 到 destination(B)，中間節點首尾相接
    · a(c) ≤ s，s + d(c) ≤ b(c)，抵達 ≤ D*
    · 與 F 不重疊
    · s2 ≥ h1 且 s2 + d2 ≥ A1
    · 同一節點的造訪不重疊
    · 每個節點全程 O + 已收 − 已送 ≤ M

全部通過回傳 TRUE，否則回傳 FALSE
```

```text
Algorithm 9: Commit(schedule, B)

for each hop (c, s) do
    將 [s, s + d(c)) 加入 F[c]
end for

for each 節點造訪 do
    將 B 的「已收 − 已送」曲線加入 O
end for
```

## 尚未定案

- `TRACK` 使用簡化規則，收完整包才清空 `Ch`，可能比只禁止真正重疊更保守；區間版未測試、未證明。
- `BufferFilter` 的切段細節要處理背景跳變與開區間。
- 來源與目的地的同時事件都採先釋放再接納，尚未整合進篩選計算。
- 上述虛擬碼假設所有節點都支援邊收邊轉。不支援的節點，`U(s2)` 改成 `s2 − δ1 − d1`。
