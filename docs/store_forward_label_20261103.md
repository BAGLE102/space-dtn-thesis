# Store-and-forward 區間 Label：現況與虛擬碼（2026-11-03）

候選方法已改為 store-and-forward，節點收完整包才轉送。這是使用者的決定，尚待老師確認。本文不取代 `sequential_label_setting_v04.md`，也不刪除 2026-11-02 的 cut-through 紀錄。

## 與前一版的差異

- 限制改為 `s2 ≥ A1`，`U(s2) = s2 − δ1 − d1`。
- 移除 `RELAX`、`TRACK`、`Ch`、`Stream`、`Store`、`HasSelfOverlap`。每一跳都等上一跳收完，同一包不會自我重疊。
- `Reached` 改以 contact 為索引。
- 原型補上文件已有、先前未實作的 `SourceBufferFilter`。

移除理由是修正前的初步比較中 cut-through 效益不大，且移除後不再需要未完成的 TRACK。該比較受來源端問題影響，修正後尚未重做，不能當成 cut-through 無效的證據。

## 虛擬碼

```text
Algorithm 1: RoutePlan(Contacts, Bundles, M)
for each bundle B in 固定規劃順序 do
    L_goal ← SearchBundle(B)
    if L_goal = NO_PATH then 記錄 B 無路徑；continue
    schedule ← Backtrack(L_goal)
    if ValidateSchedule(schedule, B) = FALSE then 保存失敗案例並停止
    Commit(schedule, B)
end for

Algorithm 2: SearchBundle(B)
Q ← 空的優先佇列，依 key(L) = lo(I) + d(c) + δ(c) 排序
Reached ← 全部清空
for each c with u(c) = source(B) do
    C ← SourceBufferFilter(c, SourceRange(c))
    if v(c) = destination(B) then C ← DestinationFilter(c, C)
    InsertLabels(c, C, SOURCE)
end for
while Q 不是空的 do
    L1 = (c1, I1, pred1) ← 取出 key 最小的 Label
    if v(c1) = destination(B) then return L1
    // 不檢查是否走過，保留 Buffer Detour
    for each c2 with u(c2) = v(c1) do
        C ← BufferFilter(StartRange(c2, L1), L1, c2)
        if v(c2) = destination(B) then C ← DestinationFilter(c2, C)
        InsertLabels(c2, C, L1)
    end for
end while
return NO_PATH

Algorithm 3: StartRange(c2, L1)
C ← [max(a(c2), lo(I1) + δ1 + d1), min(b(c2) − d2, D* − d2 − δ(c2))]
for each [x, y) in F[c2] do C ← C 移除 (x − d2, y)
return C

SourceRange(c)
C ← [max(a(c), g), min(b(c) − d(c), D* − d(c) − δ(c))]
for each [x, y) in F[c] do C ← C 移除 (x − d(c), y)
return C

Algorithm 4: BufferFilter(C, L1, c2)
n ← v(c1)
將 C 依 s1* 卡住的點與 O_n(t) 轉折造成的臨界點切成多個 Seg
Result ← 空集合
for each Seg do
    if s1*(s2) 不存在 then continue
    // 只測最晚的 s1*：它的占用最少
    解 Occ(t, s2) ≤ M_n，t 從 s1*(s2) + δ1 到 s2 + d2
    將可行的 s2 加入 Result
end for
return Result

SourceBufferFilter(c, C)
保留滿足 O_src(t) + S − 已送(t, s) ≤ M_src 的 s，t 從 g 到 s + d(c)

DestinationFilter(c, C)
保留滿足 O_dst(t) + 已收(t, s) ≤ M_dst 的 s，t 從 s + δ(c) 到 s + d(c) + δ(c)

Algorithm 5: InsertLabels(c, C, pred)
New ← C − Reached[c]
Reached[c] ← Reached[c] ∪ New
for each 連通區間 I in New do 將 (c, I, pred) 放進 Q

Algorithm 6: Backtrack(L_goal)
L ← L_goal；s ← lo(I(L))；schedule ← [(c(L), s)]
while pred(L) ≠ SOURCE do
    PrevL ← pred(L)
    s_prev ← I(PrevL) 中不超過 s − δ(PrevL) − d(PrevL) 的最大值
    將 (c(PrevL), s_prev) 加到 schedule 最前面
    L ← PrevL；s ← s_prev
end while
return schedule

Algorithm 7: ValidateSchedule(schedule, B)
檢查路徑相接、時段與期限、與 F 不重疊、s2 ≥ A1、每個節點全程 O + 已收 − 已送 ≤ M

Algorithm 8: Commit(schedule, B)
將每一跳的 [s, s + d(c)) 加入 F[c]；將每次節點造訪的「已收 − 已送」曲線加入 O
```

**程式現況：** `store_forward/` 的舊實驗未含目的地 Buffer，`Commit` 只提交中間節點；`dtn_validation/` 已補上，假設 bundle 收完即離開目的地。下方多包數字來自舊實驗。

## 單包驗證

| 檢查 | 結果 |
|---|---|
| 案例總數（`store_check.py`，種子 50000、70000 各 1,500） | 3,000 |
| 兩邊都有解且抵達相同（1/16 秒格點窮舉） | 1,419 |
| 兩邊都無解 | 1,581 |
| 較晚、漏解、多解、回放失敗 | 0 |

負控制「每段只存最早時間」在種子 50000 起的 3,000 例中，1,397 例區間版有解：1,033 例相同、48 例較晚、316 例誤判無路徑。

## 多包初步比較

`sr10` 是在 10 條候選路徑中取第一條通過回放的簡化版 SR-CGR。同一組 seed 只比兩邊都跑到的包；延遲只比兩邊都送達的包。延遲差距為負代表本方法較快。

| 拓樸 | Buffer（MB） | N | 比較包數／預定 | sr10 送達 | 本方法送達 | 延遲差距 |
|---|---:|---:|---:|---:|---:|---:|
| Ring Road ATrack | 3 | 100 | 105／300 | 44.8% | 95.2% | +0.01% |
| Ring Road ATrack | 3 | 300 | 95／900 | 53.7% | 95.8% | +0.01% |
| Ring Road ATrack | 30 | 100 | 154／300 | 96.1% | 96.1% | 0.00% |
| Ring Road ATrack | 30 | 300 | 141／900 | 95.7% | 95.7% | 0.00% |
| Ring Road Walker | 3 | 100 | 135／300 | 87.4% | 100% | +0.72% |
| Ring Road Walker | 3 | 300 | 136／900 | 89.7% | 100% | −2.00% |
| Ring Road Walker | 30 | 100 | 300／300 | 100% | 100% | +0.33% |
| Ring Road Walker | 30 | 300 | 553／900 | 100% | 100% | +0.44% |
| walker16 | 15 | 50 | 150／150 | 31.3% | 89.3% | +3.45% |
| walker16 | 15 | 150 | 259／450 | 25.5% | 73.7% | +2.10% |
| walker16 | 30 | 50 | 150／150 | 74.7% | 100% | −1.71% |
| walker16 | 30 | 150 | 228／450 | 57.9% | 100% | +0.99% |
| relay | 5 | 10 | 200／200 | 33.5% | 52.0% | −4.94% |
| relay | 5 | 20 | 400／400 | 21.2% | 38.0% | −10.09% |
| relay | 5 | 40 | 800／800 | 11.9% | 24.4% | −9.93% |
| relay | 10 | 10 | 200／200 | 60.0% | 77.0% | −2.09% |
| relay | 10 | 20 | 400／400 | 39.8% | 59.5% | −5.96% |
| relay | 10 | 40 | 800／800 | 23.4% | 36.5% | −5.57% |

平均每包計算時間：Ring Road 0.43～4.64 秒，walker16 約 1～1.9 秒，relay 0.04～0.16 秒。

## 限制

- 單包案例小型且為合成資料，不是證明。
- Ring Road 每組限 150 秒且只有 3 個 seed，多數只跑到前段；walker16 N=150 也未跑完。
- Ring Road 的 `δ = 0`；速率與 Buffer 參考學長設定，需求自行生成，不能對照他的結果。
- walker16、relay 是自行生成的情境；`sr10` 用了全域資訊，也不是完整 CGR 實作。
- 來源與目的地占用未完整計入，多包結果可能偏樂觀，目前不是正式結果。

## 未完成

- [ ] 老師確認移除 cut-through 與不設獨立配額
- [ ] 實作 `DestinationFilter`，`Commit` 納入來源與目的地，修正後重跑
- [ ] 跑完完整實驗矩陣
- [ ] 單包最早抵達的正式證明
- [ ] 定義整體最佳，小規模以 ILP 比對
- [ ] cut-through 敏感度實驗（大 bundle、低速率）
- [ ] 比較回溯取值規則對後續各包的影響
- [ ] 實作 Alhajj、Corlay 方法並對跑，核對原文後再引用
