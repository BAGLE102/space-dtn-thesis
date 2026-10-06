# Reviewer-style assessment v02

## 核心判斷

**問題具有實務意義，但目前的 M0 演算法尚不足以支撐新的碩論演算法貢獻。** 不能以「CGR 不看容量、Label Setting 加入 capacity」作為主要 novelty。M0 可視為定義清楚的精確 baseline。

| Review question | 判斷 | 證據 / 要求 |
|---|---|---|
| 1. Problem 是否成立？ | 有條件成立 | 不可分割且 size 有限會受剩餘 volume 與 window 限制；但必須區分 quota 和實際可排程時段 |
| 2. Paper A 是否已解掉？ | 沒有直接解本次整包模型，但已涵蓋容量與 buffer 的更廣多 flow 規劃 | A pp.20–25 為連續 flow LP；未強制每 bundle 單一路徑/逐跳整包 serialization |
| 3. Paper B 是否適合？ | 適合當框架使用案例 | B PDF p.27 的 cost+delay SPPRC 有真實取捨；不能把 multiplier cost / SVC tree 搬成 DTN contribution |
| 4. Label Setting 是否必要？ | 單標籤版本可用；多標籤尚無必要 | M0 同 node 早到可模擬晚到 |
| 5. Dijkstra 能否解？ | M0 可以 | FIFO 的 F_c(a)、固定容量篩邊、免費等待；詳見 extension proof |
| 6. 與 existing work 差異？ | 目前主要是明確語意與整理，novelty 未建立 | SABR 已有 non-fragmentable volume filtering；B 已使用 capacity-aware Dijkstra |
| 7. Dominance 正確？ | M0 正確；M0-Lex 需 Pareto；舊稿 finite-buffer 整體不完整 | time/cost waiting counterexample、buffer counterexample 都已給出 |
| 8. Complexity 合理？ | M0 polynomial；multilabel 需 output-sensitive bound | 不能把 physical nodes、contact vertices、labels 的數量混成同一個 n |
| 9. Experiment 能證明 claim？ | 目前只有構造範例，尚不能 | 沒有本方法原始 experiment data 或 implementation；A/B 的結果不是本方法結果 |
| 10. 有無過度宣稱？ | 有高風險 | 新演算法、首次容量感知、finite-buffer optimality、優於 CGR、跨模型 global optimum 均不可先寫 |

## High-Risk Research Issues

### H1：Existing work overlap（高）

CCSDS SABR §3.2.6.9(g) 已處理禁止 fragmentation 時的 route volume admissibility。必須比較明確版本、route enumeration / filtering、資訊假設與選路目標，不能拿未檢查容量的自製演算法代表所有 CGR。

### H2：M0 的 novelty 不足（高）

local R≥S 不產生累積 resource trade-off。改用 Label Setting 名稱或把 labels 改掛 contacts，不會自動產生新的演算法能力。推薦先保留 M0 作 baseline，再決定是否研究 finite-buffer safe intervals 或有明確需求的多資源模型。

### H3：Residual capacity 語意不完整（高）

總剩餘 volume 無法保證存在足夠長的連續 free interval；non-fragmentation 也不必然等於 non-preemption。須確認允不允許同一 contact 中暫停恢復，以及是否已有 reservation calendar。

### H4：Finite buffer 不是加一個 if（高）

必須指定 reception/transmission/custody 的占用生命週期。若等待不可行，較早 arrival 可能不支配晚到，earliest-only extension 也會漏掉延後出發可行的 route。

### H5：候選與真實占用混淆（高）

不能在每次 label expansion 扣全域 R。多 bundle 真正提交的順序會影響結果，單次 route optimality 不保證批次最佳或公平。

### H6：Lex objective 的錯誤 pruning（高）

前綴較早可能在下一 contact 等待後變成同 arrival；較便宜的晚到 prefix 必須保留。queue 的 lex ordering 與 dominance 的 componentwise ordering 是不同功能。

### H7：A 的 flow 模型被當作整包 gold standard（高）

A 允許連續資料量、hot spots 集合與時槽 objective。若直接用 A 的 optimum 當本問題正確答案，模型不同，誤差數值沒有同一意義。需要重建一致的整包 oracle。

## 公平的驗證與實驗計畫 [D]

1. Correctness：小型 contact plan 全路徑/排程列舉，比對 feasibility 與最早到達；測 S=R、finish=end、o=d、不可達、平行 contacts、窗口已過、cost ties、buffer 反例。
2. M0 強 baseline：capacity-filtered time-dependent Dijkstra。與本 Algorithm 1 應給相同 optimum；不能期待有解品質優勢。
3. 弱 baseline：只看時間、或只先算一條 route 再檢查容量。必須標成 ablation / naive baseline，不能稱完整 CGR。
4. SABR 比較：需明確實作版本、route count、priority、fragmentation、EVC overhead、backlog、資源資訊及 re-routing 設定。不同 objective 分開報告。
5. 擴充 M1 後：oracle 與 baseline 必須有相同 calendar、buffer model、知識範圍及非切割/非搶占設定。
6. 指標：feasibility agreement、optimal arrival agreement、delivery ratio、delay、runtime、peak label count、memory。arrival error = A_alg−A_oracle；比例分母用正的 oracle travel duration A_oracle−g；分母為 0 時記 N/A。
7. 統計：多個獨立 seeds、paired instances，報 n、mean/min/max/std、confidence interval；不可把失敗 route 當 0 delay 混平均。沒有 raw data 不補造統計量。
8. 模型錯誤、solver timeout、證明 infeasible 分開計數。不同 bundle size / occupancy / contact count 的敏感度分析要在模型確認後執行。

## 下一步要確認的 scope

選項 A：先接受 M0 作正確 baseline，下一階段簡報主題是問題釐清與研究缺口，不宣稱新演算法。

選項 B：finite buffer 是必須保留的核心需求，則先定義 safe storage intervals、發送可延後的規則與完整 resource state，再重寫 algorithm 和 proof。

選項 C：主要目標其實是多 bundle routing/scheduling，則重新定義全域 objective、admission、reservation、優先權與公平性，不用單 query 結果代替。

這是研究範圍選擇，不是工具權限問題；依使用者要求，等確認 Algorithm / Storyline 後才進入 PPTX 製作。
