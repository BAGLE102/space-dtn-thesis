# 依序預約的 Label Setting：兩包例子與初版規則

2026-10-05。依使用者最新澄清：多個 bundles 依固定順序處理，每次搜尋一包；已接受的前包會占用後包可用資源。沒有額外外生流量，不等於沒有前包預約。本文件為 [D] 方法草稿與 [C] 模型推導，尚非文獻中的現成演算法，也未宣稱新穎性。

## 1. 本步範圍

- 保留 earliest whole-bundle arrival、不可分割、不可暫停、每跳單 contact、完整接收後才能轉送。
- Buffer 固定上限 M_v，但既有占用 O_v(t) 由已接受 bundles 的排程累加而來。
- 逐 byte 接收／釋放，已送 byte 不保留副本，destination 整包交付即釋放。
- **初版仍用 aggregate contact quota R_c**。記錄已接受的傳輸時段，供後續 calendar 版本使用；本版不因此自動宣稱能避免所有鏈路時間衝突。
- 搜尋中，各候選 labels 是互斥方案，不直接修改全域預約。只有完整路徑接受後才提交。
- 本步用有限時間格點枚舉發送時間，先驗證 extension、buffer 與保守 dominance；連續時間版另行推導。

每次搜尋開始時，R 與 O 都是固定快照。所謂每包最優，只相對於此前已接受的排程及固定處理次序，不是所有 bundles 的聯合最優。

## 2. 可直接手算的 contact plan

所有時間為秒、資料量為 MB、rate 為 MB/s。所有節點 buffer 上限 4 MB，propagation delay 均為 0。每個 contact 初始 quota 都是 4 MB，rate 都是 4 MB/s。

| ID | Contact | 發送 window | 傳一包所需時間 |
|---|---|---|---|
| c1 | X→B | [2,3) | 1 秒 |
| c2 | B→D | [6,7) | 1 秒 |
| c3 | A→B | [1,2) | 1 秒 |
| c4 | A→B | [7,8) | 1 秒 |
| c5 | B→D | [9,10) | 1 秒 |

Bundle 1：X→D，S=4，release=0。Bundle 2：A→D，S=4，release=1。**依生成順序先規劃 bundle 1，再規劃 bundle 2**；第二包搜尋時，第一包尚未實際到 B，但已預約未來的占用。

刻意讓每個 window 恰好只能容納一包，因此本例不涉及同一 contact 內選不同 start time；一般情境仍需枚舉延後發送。

## 3. 先規劃 bundle 1

最早路徑 X→B→D：c1 發送 2–3、c2 發送 6–7，整包在 D 的 arrival=7。改用 c5 則 arrival=10，因此選 c2。

接受後 R_c1=R_c2=0，其餘 R=4。B 的預約占用：

    O_B(t) = 0             t < 2
             4(t−2)       2 ≤ t ≤ 3
             4            3 ≤ t ≤ 6
             4(7−t)       6 ≤ t ≤ 7
             0            t ≥ 7

X 在 t=0 已有整包，等待至 2，2–3 逐 byte 釋放；D 在 6–7 接收，t=7 完整交付後釋放。這些也要提交到各節點的占用表。

**預約表可在規劃時立即更新，實際占用則只發生於上述時段。**

## 4. 再搜尋 bundle 2：兩個 B labels 都有必要先保留

| 步驟 | Label / 動作 | 判定 |
|---|---|---|
| 初始化 | L0=(A,1) | A 可持有 4 MB |
| 延伸 c3 | L1=(B,2)，A 發送 1–2 | 接收期間 B 尚無前包占用，可建立 label |
| 延伸 c4 | L2=(B,8)，A 等至 7，發送 7–8 | B 的前包占用已釋放，可建立 label |
| 嘗試 L1→c2 | quota=0 | 不可用 |
| 嘗試 L1→c5 | B 必須等待 2–9 | t=2.5 時 4+2=6 MB>4 MB，不可行 |
| 嘗試 L2→c5 | B 等待 8–9、發送 9–10 | 全程≤4 MB，可行 |
| 結果 | c4→c5 | D 完整 arrival=10 |

L1 到 B 時可行，不代表它能安全留在 B 到任意未來時間。因此建立 label 時檢查已完成的前綴；等待與送出的占用在下一次 extension 才完整檢查。

如果建立 L1 後就用「2<8」刪除 L2，會錯失可行解。這是本題需要重新設計 dominance 的直接例子，不需要加入 cost。

## 5. Label：先使用不漏資訊的版本

核心：

    L = (v, a, U)
    v：目前節點
    a：整包完整到達時間
    U[c]：本候選前綴已使用 contact c 的資料量（稀疏記錄）

重建欄位：pred、incoming_contact、transmission_start。

全域 query context：本包 S、固定的 R_c、O_v(t)、M_v、contact plan。不要在每個 label 複製整份全域占用表。

U 的原因：本版仍有 aggregate quota，且不預先禁止重訪節點；同一路徑再次使用同一 contact 時不能重複花掉相同 quota。U 不表示其他候選路徑已占用的容量。本小例沒有重訪，所以表格省略 U；一般演算法先保留，之後有證明才能刪除。

本版不額外要求 simple path。時間相依 buffer 下，離開後再回來可能避開不能等待的時段，不能沿用 v03 的「循環一定可由等待取代」。如要禁止循環，需記 visited set 並重做 dominance。

## 6. Extension：算一跳，但檢查整段占用

從 L=(u,a,U) 經 c=(u,v,start,end,r,δ)，令 x=S/r。對每個候選發送時間 s：

1. s≥max(a,start)，f=s+x≤end，h=s+δ，a′=f+δ。
2. U[c]+S≤R_c；通過後 U′=U+S·e_c。
3. Sender 新增占用：a≤t≤s 時為 S；s≤t≤f 時為 S−r(t−s)。檢查 O_u(t)+新增占用≤M_u，全時段皆成立。
4. Receiver 新增占用：h≤t≤a′ 時為 r(t−h)。檢查 O_v(t)+新增占用≤M_v，全接收期間皆成立。
5. 建立 L′=(v,a′,U′)，保存 pred 與 s。若 v 是 destination，檢查交付前的接收峰值，交付後不再保留本包。

每個 label 的前綴均已完成傳輸且釋放先前節點的本包資料，因此在目前到達時間之後，前綴不另占 future buffer。這使用 δ≥0、無副本及完整接收後轉送的假設；self-loop contacts 先排除。

**若未來啟用 transmission calendar，還需 [s,f) 不與已接受 bundles 在該 contact 的預約重疊。** 若多 contacts 共用同一 radio，還需額外資源互斥資料；目前沒有將此硬體限制納入模型。

O(t) 為分段線性時，固定 s 後可在 O 的折點、接收／發送起訖點與跳躍點兩側求最大值；因每小段為線性，不需要逐毫秒取樣。Release 與 delivery 的瞬間要明定事件順序：檢查接收完成／交付前峰值，再釋放，不能漏掉整包容量需求。

## 7. 先採保守且可論證的 dominance

同一次 query、同節點，L1=(v,a1,U1) 可刪除 L2=(v,a2,U2) 的充分條件：

    a1 ≤ a2
    O_v(t)+S ≤ M_v，對所有 t∈[a1,a2]
    U1[c] ≤ U2[c]，對所有 contacts c

理由：L1 可安全等待至 a2；到那時同樣持有 S，且已耗 quota 不更多，因此能複製 L2 的任一可行後續排程。較早抵達本身不夠，必須連等待與 quota 都可取代。

此規則可能保留很多其實不必要的 labels，但適合先建立正確 baseline。它不是已證明最強的 dominance，也不保證高效率。相同 a 與 U 的等價 labels 只保留一個穩定代表。

本例 a1=2、a2=8，B 在 [3,6] 已有 4 MB 預約，等待條件失敗，因此不能以早到為由刪除 L2。

## 8. 可執行規格層級的 pseudocode（有限時間格點版）

設定 Δ>0、有限 horizon T，release times、contact boundaries、S/r、δ 都對齊 Δ；本例 Δ=1、T=10。若原始數據不對齊，不可偷偷四捨五入並宣稱仍解原問題。

```text
Algorithm 4Q: Sequential Label Setting with Quota and Buffer Reservations
Input: contacts C, quotas R, buffers M, ordered bundles, time grid Δ, horizon T
O <- zero occupancy functions, or consistent accepted reservations

for each bundle b in the given order:
    Freeze the current R and O for this query
    if source cannot hold S at release g: report NO_ROUTE_ON_GRID; continue
    Q <- min-priority queue containing label (source, g, zero usage)
    Labels <- label registry; store all accepted labels by node
    solution <- none

    while Q is not empty:
        L <- ExtractMin by complete arrival time
        if L is marked dominated: continue
        if L.node = destination:
            solution <- Reconstruct(L); break

        for each outgoing contact c of L.node:
            if L.usage[c] + S > R[c]: continue
            for every grid start s satisfying s >= max(L.arrival, c.start)
                and s + S/c.rate <= c.end:
                a_new <- s + S/c.rate + c.delay
                if a_new > T: continue
                if sender waiting/draining or receiver filling overflows: continue
                N <- new label with updated usage and predecessor
                if an existing active label safely dominates N: continue
                Mark labels safely dominated by N; keep predecessor records
                Register N and insert N into Q

    if solution is none:
        report NO_ROUTE_ON_GRID; do not change R or O
    else:
        Independently validate the complete route and schedule
        R[c] <- R[c] - total volume used on contact c by solution
        O[v](t) <- O[v](t) + complete byte-level occupancy of solution at v
        Record transmission intervals for later calendar-mode use
        report route, schedule and complete arrival
```

路徑確認前不提交任何資源。接收方 label 只預示「此刻整包在這裡」；最後接受完整 route 才重建其整段等待占用並提交，避免重複計入。

正確性限於上述 grid 問題：所有候選 start 都枚舉、每次延伸嚴格增加 arrival、有限 horizon 且最小 hop duration>0，使候選前綴有限；安全 dominance 不刪掉不可取代的後綴。按 arrival 取出第一個 destination 可得到該格點上最早解。這不代表多項式效率，也不代表連續時間版已證明。

NO_ROUTE_ON_GRID 只表示格點上找不到解，不能直接寫成原連續時間問題無解。下一步需把枚舉改成精確可行 departure 集合的生成，並證明不漏掉必要到達狀態。

## 9. 本步結論與尚缺的工作

已建立：前包預約→後包受限的例子、byte-level extension、保守 dominance、有限格點 pseudocode。無需新增 cost，也未強制採 safe intervals。

驗證：以有理數算術檢查本例分段線性曲線的全部折點；第二包走早班時 B 總占用峰值 8 MB、t=2.5 時為 6 MB，走晚班則峰值 4 MB。兩包採用路徑的 arrival 分別為 7 與 10。這是構造例的算術驗證，沒有實作完整 routing algorithm 或統計效能測試。

尚缺：連續時間 successor 完整性、labels 數量控制、與 2024 相同 calendar 語意的比較版本，以及統計效能實驗。本例對聚合容量與 calendar 都可行，是因選定路徑沒有鏈路預約衝突，不能由此推論兩種模型一般等價。

暫定方法主張：在已接受 bundles 的 buffer 預約下，於 label extension 檢查整段占用，並以「可安全等待且剩餘資源不較差」判斷 dominance。
