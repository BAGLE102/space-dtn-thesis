# Research scope v03

> 2026-10-05 更新：使用者澄清是多 bundles 依序規劃，前包接受後形成後包的 buffer 占用。下文「無背景占用」只保留作舊 baseline，不能用來否定新情境的多 label 必要性。最新例子、extension、dominance 與格點 pseudocode 見 [sequential_label_setting_v04.md](sequential_label_setting_v04.md)。該初版仍保留 aggregate quota，calendar 為明列的後續版本。

2026-10-04，依使用者後續回覆更新。此版本的研究方向優先於 v02 的 M0 提案；v02 仍作無限 buffer baseline，不是目前主研究問題。

## 已確認的五項決定

| 項目 | 使用者確認的範圍 |
|---|---|
| Buffer | 有限 buffer 必須保留 |
| Contact 資源 | 目前先採 aggregate quota；Known transmission calendar 後續擴充 |
| Bundle | 不分割、不暫停／恢復傳輸；每一跳必須在一個 contact 內連續完成 |
| Objective | Earliest whole-bundle arrival；目前沒有次要 cost |
| 工作負載 | 單 bundle query，不是多 bundle 聯合最佳化 |

沒有成本項也可以是有意義的問題，不為了套用 Paper B 而加入人工 cost。

## 問題定義的立即修正 [D]

輸入保留 c=(u,v,start,end,r,δ,Q,R)、b=(o,d,g,S)。增加有限 buffer 的明確輸入與占用語意，見下一節。

Route 的決策須包含 **contact sequence 與 transmission schedule**：

\[
\min_{P,\mathbf s} a_K,\qquad
s_i\ge\max(a_{i-1},start_{c_i}),\qquad
f_i=s_i+S/r_{c_i}\le end_{c_i},\qquad
a_i=f_i+\delta_{c_i}.
\]

每 hop 要求 R_(c_i)≥S。上式允許延後發送；但依下述已確認的固定 buffer、無背景占用條件，存在採 s_i=max(...) 的最優解。只有擴充到時間相依的背景占用等條件後，才可能必須延後前一跳發送。

R 僅代表本次可分配的總量快照，不額外指定其他 bundles 占用鏈路的區間。本階段的 feasible 是此抽象模型下的 feasible，不保證在未提供的真實 transmission calendar 上也可排入。

候選路徑在搜尋中互斥，不應逐 label 扣全域 R。一般而言，重複使用同一 contact 要累計 quota；本版則由下述「循環可由等待取代」論證確保存在無循環最優解，因此不需為尋求任一最優解額外保存歷史資源。此論證不能直接延用到時間相依背景占用的擴充版本。

## Buffer 輸入：使用者已確認

**固定上限 M_v，無任何背景占用。** 使用者已明確選擇此版本，並要求逐 byte 接收與釋放。即使逐 byte 計算，在完整接收才能轉送的前提下，峰值仍為 S，因此 finite buffer 成為 M_v≥S 的 node filter。證明與 occupancy functions 見 [buffer_model_v03.md](buffer_model_v03.md)。

**Time-varying residual buffer B_v^res(t) 不在目前範圍。** 它是不同擴充，需要另外提供時間資料，不能由 aggregate contact R 推得。沒有背景占用時，不應為了讓問題更複雜而自行製造 buffer blackout intervals。

目前不需 buffer forecast calendar，也不需加入 cost。

## Buffer 占用規則：逐 byte 版本已確認

使用者選擇逐 byte 計算，而非整包提前預留。每接收一個 byte 就增加一個 byte；整包收完才能開始下一跳；每發送一個 byte 即釋放該 byte 的 buffer 空間。

令中繼 v_i 接收第一 bit 的時刻 h_i=s_i+δ_(c_i)，整包到達 a_i=f_i+δ_(c_i)。下一跳發送從 s_(i+1) 開始；由 a_i≤s_(i+1)，buffer occupancy 為：

\[
b_{v_i}(t)=\min\{S,\max\{0,r_{c_i}(t-h_i)\}\}
-\min\{S,\max\{0,r_{c_{i+1}}(t-s_{i+1})\}\},\qquad b_{v_i}(t)\le M_{v_i}.
\]

Source 在 g 已有 S，發送開始後逐 byte 減少。Destination 逐 byte 接收，整包交付後釋放；其接收峰值同樣為 S。不默認 source / destination 無限 buffer。

本次模型假設不保留已發送 byte 的 custody / retransmission copy，也忽略 processing delay；若實務需要這些機制，需另定義占用，不能以目前逐 byte 釋放模型代替。

## Label、extension 與 dominance 的修正結論

- 不加入 cost。完整占用曲線由最後路徑與排程重建，不必塞進每一個 label。
- 先過濾 M_v<S 的 nodes 與 R_c<S 的 contacts，再以核心 state (v,a) 搜尋。
- 在目前固定 buffer、無背景占用下，只要 M_v≥S 就可任意等待，故 early-arrival dominance 成立。
- 目前最優解可採 earliest-start extension。延後發送仍是允許的動作，但不會改善 earliest arrival 或已通過的 buffer 可行性。
- 循環可由同 node 等待取代，因等待占用不超過 S，並減少 transmission / quota 使用；因此存在無循環最優解，不需為尋求任一最優解保存 visited set。
- 詳見 [algorithm_design_v03.md](algorithm_design_v03.md)。finite buffer 被保留，其作用由可證明的 node filter 完整表達，而不是被忽略。

## 先前反例的適用範圍

v02 的早到遇上 buffer blackout、必須延後發送反例，都依賴 time-varying 背景占用。使用者本次排除此條件，所以這些反例只可作 future-work 說明，不作當前多標籤必要性的證據。

## 本階段狀態

研究範圍與 buffer 輸入／占用方式已確認。v03 已補上 node buffer filtering、逐 byte occupancy 與適用條件下的正確性說明；它仍屬於 Dijkstra / label-setting 的直接適用，尚未建立新的演算法貢獻。仍不建立 PPTX。
