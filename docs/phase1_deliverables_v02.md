# Phase 1 deliverables v02

> 最新進度（2026-10-05）：[sequential_label_setting_v04.md](sequential_label_setting_v04.md) 依多 bundles 逐包預約的澄清，建立兩包例子、label/extension/dominance 與有限格點 pseudocode；尚未完成連續時間演算法與效能實驗。

> 研究延伸建議（尚未取代已確認 scope）：見 [research_extension_recommendation_v01.md](research_extension_recommendation_v01.md)，提出以 buffer safe intervals 與按需 transition 搜尋替代預先展開的候選方向，包含文獻比較、兩個小例子、證明義務及公平實驗設計。

> 後續更新：使用者已確認 finite buffer 必須保留、先做 aggregate quota、每跳單 contact 內不可分割且不中斷、單 bundle earliest arrival、無次要 cost。最新範圍見 [research_scope_v03.md](research_scope_v03.md)，文獻主張核對見 [transmission_time_claim_review_v01.md](transmission_time_claim_review_v01.md)，大綱修正見 [ppt_storyline_revision_v03.md](ppt_storyline_revision_v03.md)。以下為原第一階段歷史交付記錄，M0 僅作 baseline；原五項待確認問題已由使用者回答，不需重問。

> Buffer 細節亦已確認：各 node 固定上限、無背景占用、逐 byte 接收及釋放。見 [buffer_model_v03.md](buffer_model_v03.md) 與 [algorithm_design_v03.md](algorithm_design_v03.md)。本版可證明 buffer feasibility 等價於 M_v≥S，加入 node filter 後仍能用單 label 的 time-dependent Dijkstra；不能把舊 time-varying buffer 反例當作本版的多標籤必要性證明。

完成日期：2026-10-04。第一階段止於 Algorithm / Storyline 審查，等待使用者確認後才製作 PPTX。

## 先讀結論

1. M0（單 bundle、固定 residual quota、無有限 buffer / busy intervals）可由 time-dependent Dijkstra 精確求解；一般 multi-label SPPRC 不是必要條件。
2. SABR 已有禁止 fragmentation 時的 route volume filtering，因此不能把「CGR 不考慮容量」當 novelty。
3. Paper A 已做容量 / buffer 多 flow LP，但不等同 non-fragmented 整包路由。
4. Paper B 的 Label Setting 是 delay-constrained min-cost 子問題工具；其完整 label implementation 未提供。
5. 舊 PPT node continuity 公式與 buffer / algorithm scope 不一致；已逐頁列出。
6. 目前只能提出一致、可核算的 baseline，不能宣稱已完成新的有限 buffer 演算法。

## 生成文件

| 文件 | 內容 |
|---|---|
| [paper_method_mapping_v01.md](paper_method_mapping_v01.md) | 兩篇全文分析、來源標記與 concept mapping |
| [problem_formulation_v02.md](problem_formulation_v02.md) | 正式定義、假設、目標、reservation / buffer 缺口 |
| [label_design_v02.md](label_design_v02.md) | 必要 state 與 metadata |
| [extension_rule_v02.md](extension_rule_v02.md) | 8-step extension 與 FIFO 證明 |
| [dominance_rule_v02.md](dominance_rule_v02.md) | M0 / M0-Lex 規則與反例 |
| [algorithm_design_v02.md](algorithm_design_v02.md) | 搜尋設計、正確性、complexity、限制 |
| [algorithm_pseudocode_v02.md](algorithm_pseudocode_v02.md) | Algorithm 1 與 lex variant，非 Python |
| [small_topology_v02.md](small_topology_v02.md) | 完整 contact plan、label evolution、算術驗證 |
| [algorithm_walkthrough_plan_v02.md](algorithm_walkthrough_plan_v02.md) | 同 topology 的 8 張逐步圖規劃 |
| [previous_ppt_review_v01.md](previous_ppt_review_v01.md) | 舊 PPT 27 頁逐頁 KEEP / REVISE / REMOVE / REBUILD |
| [new_ppt_outline_v02.md](new_ppt_outline_v02.md) | 23 頁正文與 3 頁附錄：每頁 bullet、figure、notes、sources |
| [template_inspection_v01.md](template_inspection_v01.md) | 範本尺寸、母片、字型、色彩、頁尾 |
| [reviewer_assessment_v02.md](reviewer_assessment_v02.md) | 10 個 reviewer 問題、高風險與公平實驗計畫 |
| phase1_deliverables_v02.md | 本索引 |

## 檢查與限制

- 讀取兩篇 PDF 的全部頁面文字，另核對核心模型與 SPPRC 頁面影像。局部文字映射錯誤未當作可靠符號依據。
- 舊 PPT 全 27 頁以 PowerPoint 唯讀 render 及 XML/notes 對照；模板為 1 頁、12 layouts。
- 使用有理數算術獨立列舉小拓樸所有 route；結果與逐步表相符。沒有進行本方法統計效能實驗。
- 所有根目錄 `docs/` 文件都是本次新建；原始兩份 PDF 與兩份 PPTX 未修改。
- 中間抽取文字、XML 與檢查用 PNG/JPG 位於 `tmp/source_inspection/`，不是正式 walkthrough figures。
- 專案根目錄沒有實體 AGENTS.md，本次依使用者訊息中提供的 AGENTS.md 指示執行。
- 沒有建立新 PPTX、正式演算法圖片、Python routing implementation 或實驗結果曲線。

## 需要確認

1. 先以 M0 做正確 baseline，還是 finite buffer 必須留在本次核心問題？
2. Residual capacity 是 aggregate quota，還是有其他 bundle 的已知 transmission calendar？
3. Non-fragmented 是否還要求 non-preemptive，以及每跳只能用一個 contact？
4. Objective 只 earliest arrival，還是有具體定義的次要 cost？
5. 研究範圍是單 bundle query、依序 admission，還是多 bundle 的聯合最佳化？

完成項目：兩篇分析、模型與演算法草稿、例子、舊稿審查、新大綱。

生成文件：上述 14 份 Markdown。

修改文件：無既有檔案修改。

輸出位置：`C:/Users/聖克里斯多福/Desktop/碩士/docs/`。

建議下一步：先確認以上 scope 問題；若選 M1，先修算法再製作 PPT。
