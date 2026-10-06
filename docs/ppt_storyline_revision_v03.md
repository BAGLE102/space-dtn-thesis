# PPT storyline revision v03

此文件覆蓋 new_ppt_outline_v02.md 的研究主線。v02 詳細內容仍保留作素材；最新方法採固定有限 buffer、無背景占用與逐 byte 接收／釋放，見 algorithm_design_v03.md。沒有建立 PPTX。

## 主張修正

舊句「現有 CGR 沒有 transmission delay / capacity」不可使用。改為：**明確區分 route-search 的 BDT 與整包 arrival，研究在單 bundle 搜尋中整合 contact window、aggregate quota 與有限 buffer 的一致方法。** 新穎性仍需與現有 buffer-aware routing 比較。

## v02 投影片修改對照

| 原頁 | v03 調整 |
|---|---|
| 1、6 | 主題改為 finite-buffer 單 bundle query；aggregate quota 是目前範圍，calendar 是 future work |
| 4 | 加入 quota 足夠、window 不足的案例，標為模型反例而非完整 CGR 失敗 |
| 5 | 改成 BDT route search / size-aware candidate evaluation 的分階段比較 |
| 7 | 保留 earliest whole-bundle arrival，刪除正文 cost variant；本版可證明採 earliest-start schedule 不劣 |
| 8–10 | A/B 保留；新增高度相關的 capacity-and-buffer CGR 文獻，先查差異再宣稱 contribution |
| 11 | 一般排程允許 s≥max(a,start)，但本版選 earliest-start 即可；加逐 byte occupancy 曲線 |
| 12–15 | 使用 Algorithm 3：先檢查 M_v≥S，再採 (v,a) label；證明固定 buffer 下早到可等待 |
| 16–20 | 既有 5-node 範例保留；加 M_v<S 被拒絕的 node 與完整 byte-level buffer 曲線 |
| 21 | 由本版 reduction 證明 Algorithm 3 同樣為 O((n+m)log n)，不直接搬用未驗證 bound |
| 22 | baseline 納入 size-aware evaluation；分開驗證 window、quota、node buffer filtering |
| 23 | 明確指出目前為正確基礎版本，尚無新演算法 contribution；不為增加複雜度任意加入 cost |
| 附錄 A | lexicographic cost 暫移出主線，留作歷史分析資料 |
| 附錄 B | 舊 delayed-departure / blackout 反例只作 time-varying 背景占用的未來擴充，不當成目前模型 |

## 新增核心頁草稿：BDT and Whole-Bundle Arrival

Slide Content:
- Route search 與 candidate evaluation 分開看
- τ=S/r 會改變 route 的 arrival 排序
- 現有方法的差異須指定階段與版本

Suggested Figure：兩條 route 的 BDT / 整包到達時間對照，數值 1/9 與 2/4 秒。

Speaker Notes：這是自行構造的範例。若候選集合包含兩條 route 且使用正確 projected arrival 評估，就能選出較快者；不能把「只查第一條」的限制套到所有實作。

Source：transmission_time_claim_review_v01.md；SABR §3.2.4 與 §3.2.6。

## 新增核心頁草稿：Byte-Level Buffer Occupancy

Slide Content:
- 接收時增加，等待時維持，發送時釋放
- 完整收完才能轉送，峰值為 S
- 固定上限、無背景占用時檢查 M_v≥S

Suggested Figure：buffer_model_v03.md 的 B occupancy：1–3 秒增加至 4 MB、3–5 秒等待、5–9 秒降至 0。

Speaker Notes：此處已採使用者確認的逐 byte 模型。雖然不是整包預留，完整接收完成時仍須存放 S；本版不用多個 buffer labels，是等價簡化而不是忽略 buffer。若加入 time-varying 背景占用，才需重檢這個結論。

Source：[C/D] buffer_model_v03.md、algorithm_design_v03.md。
