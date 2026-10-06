# Dominance examples v01

固定規則：同 node/query，a1≤a2、等待全程 O_v(t)+S≤M_v、U1≤U2 componentwise。以下均使用完整接收後轉送、逐 byte 釋放。

## Example A：不能刪（主 walkthrough）

Bundle 1 提交後，B 的 O_B 在 2–3 升至 4、3–6 為 4、6–7 降至 0。

- Label A：B@2，U={c3:4}，沿 c3 於 1–2 接收。
- Label B：B@8，U={c4:4}，沿 c4 於 7–8 接收。
- Comparison state 是同一實體節點 B、同一 bundle 與固定資源快照；不是 arrival/U 必須相同。

不能 dominance 的原因有兩個，不能隱瞞第二個：A 無法在 B 等待跨過 3–6；而且 U_A[c3]=4>U_B[c3]=0，也不滿足 componentwise 用量條件。

Future extension：晚到 B@8 可等至 10，經 c5 傳送 10–11、δ=1，於 12 到 D；早到 B@2 等待時 t=3 總占用 8>4，且 c2 quota 已為 0。C 分支也無解。**若只因早到而把所有晚到 B labels 刪除，原有可行解會消失。**這是對錯誤簡化規則的 counterexample，不是 frozen v04 本身的反例。

## Example A′：隔離 buffer 因素

Validation case 04 使用同一個 A→B contact，window=[1,8]、r=4、quota=4，兩個候選 start=1、7 分別產生 B@2 與 B@8。兩個 labels 的 U 完全相同。沿用上述 O_B，仍然不能用 B@2 刪除 B@8；下一 contact B→D=[9,10]，只有晚到者能完成。因此等待條件本身確實必要，不是只有 quota vector 在阻止刪除。

## Example B：可以刪（主 walkthrough 的 c4）

- Label A：B@8，經 c4 在 7–8 傳送，U={c4:4}。
- Label B：B@9，經同一 c4 在 8–9 傳送，U={c4:4}。

| Resource / State | Label A | Label B | Better |
|---|---|---|---|
| node / query / snapshot | B / bundle2 / 同快照 | 相同 | 可比較 |
| arrival | 8 | 9 | A 不晚到 |
| U[c4] | 4 | 4 | 相同 |
| 其他 U[c] | 0 | 0 | 相同 |
| O_B(t)，8≤t≤9 | 0 | 0 | A 可等待 |
| 等待占用 O_B+S | 4≤4 | 4≤4 | 可行 |

A 等至 9 後，可照抄 B 的任一可行後續排程，quota 不更差，最後 arrival 相同。因此 **Label A dominates Label B；Label B can be safely pruned**（不損失最優值）。不是需要證明 A 的所有後續都能由 B 複製；正確方向是 B 的每個 continuation 都能由 A 取代。

實際 trace：bundle2 的 c4 第二次 start 嘗試產生 L3=(B,9,{c4:4})，被 L2=(B,8,{c4:4}) 取代，不入列。原始記錄在 `output/validation/walkthrough_trace.json`。ON/OFF 的實測 labels 數量另見 oracle_validation_v01.md，不在此預填。
