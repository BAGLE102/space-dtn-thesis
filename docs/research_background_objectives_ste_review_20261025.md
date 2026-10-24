# 背景、動機、目的文件：STE 寫作與事實檢查

日期：2026-10-25。

## 寫作依據與適用範圍

採 ASD-STE100 Issue 9（2025-01-15）的 descriptive writing 原則，而非操作程序寫法。

- 官方 Section 6 索引可讀到 Rules 6.1～6.6：循序提供資訊、邏輯連接、每句至多 25 words、每段一個主題、每段至多六句。
- 本稿自訂更保守的英文正文上限：每句至多 20 個空白分隔 token、每段至多四句。數字／縮寫／連字符保留為單一 token，並非完整官方計字實作；另記錄將連字符拆開的詞數。
- 採主動語態與直述句，避免將 descriptive text 寫成命令。
- 技術名詞固定，另列英中對照。bundle、contact、Label、snapshot 不任意互換；整體目標與候選延伸分開。
- 中文按英文段落順序翻譯；不以中文句長冒充英文 STE 規則，也不宣稱中文通過 STE 認證。

官方原件直接開啟回覆 403，但官方搜尋索引可讀到 Section 6 與部分說明。官方 FAQ 可核對主動語態、技術名詞、受控詞彙與 STE 適用範圍。

**尚未完成一般詞彙逐詞的 approved meaning／part of speech 核對，因此標為依 STE 原則撰寫的草稿，不能宣稱完全符合 ASD-STE100。** 句長與術語檢查不等同完整合規審查。

## 已檢查的寫法

- 不使用動詞 check；以名詞 checks／comparisons 敘述檢查結果。
- 以 start 表達開始，不使用 begin／commence 等同義詞替換。
- 未用進行式敘述；Networking、routing、splitting、waiting、planning 等字詞用於術語或名詞位置。existing、during 等一般字詞的字典核對仍未完成，不能僅憑詞尾判定合規。
- 每段集中一個說明主題；以 Background → Motivation → Existing Work → Objectives → Progress → Scope 排列。

以上為人工寫作檢查，不是假稱執行官方語法／字典檢查器。

## 事實追溯

| 正文項目 | 依據 | 審查判斷 |
|---|---|---|
| 不可切分、完整接收後轉送、逐包預約 | 專案 v04／snapshot 與最新候選簡報紀錄 | 保留主問題，不改成整批聯合最佳化 |
| 以可行起送區間取代時間格點 | 1021 起送時段候選與區間元件 | 候選搜尋尚未完成，元件已實作 |
| Contact splitting 等與既有方法重疊 | 2410.15546v3 §III／IV、專案比較筆記 | 不主張首次提出 |
| 計算成本可作候選延伸 | 原文 §IX 與本次元件紀錄 | 不當作新穎性證明 |
| 9／9,307／22,320 | correctness.json、verification_manifest.json | 來自 2026-10-21 的測試，不是假稱本次重跑 |
| 96 contacts、五快照、七次計時 | metadata.json、timings.csv | 元件實驗，不是完整路由實驗 |
| 28.443／228.056 ms | summary.csv 的 sparse_local 中位數 | 五快照總時間；非每包、非原文比較 |
| 全查詢無穩定優勢 | full_local／full_global 的計時與結果分析 | 同時保留負面結果 |
| 一般正確性／貢獻未確認 | 目前未完成事項與版本紀錄 | 不宣稱最優、完備或確定可發表 |

最近一次已確認數值實驗日期為 2026-10-21；本次整理日期為 2026-10-25。沒有新增模擬或修改算法。

## 機械檢查產物

英文正文的逐句 token／word 計數、逐段句數與兩語段落對齊結果，另存：

`output/writing_review_20261025/research_background_objectives_checks.json`

檢查區間為英文檔的 REVIEW_START／REVIEW_END，不含術語表、來源與 metadata。術語表人工確認中英均有相同項目。沒有以正則表達式宣稱驗證全部語態、字義或翻譯正確性。

## 參考來源

- [ASD-STE100 Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)，Section 6。
- [STEMG 官方 FAQ](https://www.asd-ste100.org/STE_faq.html)。
- [Alhajj 與 Corlay 原文](https://arxiv.org/html/2410.15546v3)。
- `docs/1021_concrete_start_intervals_ppt_20261021.md`。
- `docs/demand_interval_validation_results_20261021.md`。
- `output/demand_interval_validation_20261021/correctness.json`、`summary.csv`、`metadata.json`。
