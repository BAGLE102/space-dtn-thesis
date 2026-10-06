# Previous PPT review v01

來源：`F:/temp/0922.pptx`，共 27 頁。依 presentation relationships 核對實際頁序，解析文字、公式 XML 與 notes，再以 PowerPoint 唯讀開啟輸出所有頁面 PNG 目視檢查。沒有修改原檔。頁碼以投影片實際順序為準；舊 notes 中的數字不是目前頁碼。

## 逐頁審查

| Slide | Current Topic | Status | Problem | Recommended Fix |
|---:|---|---|---|---|
| 1 | Problem P | REBUILD | node continuity 寫成 u_(c_k)=v_(c_(k+1))，方向錯；含 buffer 卻與後面算法不一致；未交代 residual snapshot / scheduling | 改 v_(c_k)=u_(c_(k+1))；先列 M0/M1 假設，再呈現精簡 formulation |
| 2 | 全域符號表 | REVISE | 多 bundle 集合 B 容易讓人誤會正在解聯合 routing；此時尚未建立背景 | 本文只列單 query 必要符號，多 bundle 放 future work；完整表移附錄 |
| 3 | Contact 符號 | REVISE | tuple 列 Q 卻未納 R，和第 11 頁 tuple 不同 | 統一 (u,v,start,end,r,δ,Q,R)，加 units 和 Q 可推得的說明 |
| 4 | Bundle / buffer 符號 | REBUILD | 已把 finite buffer 納入但無一致 extension；傳輸中 occupancy 未定義 | 明確區分已成立 M0 與待設計 M1，不得保留 buffer 保證卻使用 M0 code |
| 5 | Route / timing 符號 | REVISE | 傳輸時間 subscript 與 k 的一致性不佳；符號量大 | 統一 c_i、s_i、x_i、a_i，完整表移附錄 |
| 6 | Feasible 判定 | REBUILD | node continuity 同第 1 頁寫反；buffer 只描述等待期，非完整占用模型 | 修正式子；按 continuity / window / quota 列 M0；buffer 另頁列未解問題 |
| 7 | 五欄 Label | REBUILD | 儲存 full path、all start times 及 predecessor 重複；contact state 必要性未證明 | 改核心 (v,a) 加 pred、c_in、可選 s；不要把 metadata 當 resource |
| 8 | Dominance with buffer | REBUILD | 此頁確實有 [A_i,A_j) buffer bridge 條件，不可說全篇完全沒考慮；但 time inequality 重複，未證明 extension 完整性 | 保留其問題意識，補條件與反例；M0 與 M1 分開 |
| 9 | Physical topology / expanded graph | REBUILD | 同頁兩種 graph 未定義 mapping；S4/B4 重複標示，時間/速率/容量資訊不足 | 用唯一 contact IDs；physical multigraph 與 contact-as-vertex 分頁講解 |
| 10 | Routing pseudo-code | REBUILD | 完全沒有 buffer 檢查；dominance 黑盒；global R 語意、stale entries 未說明 | 用 Algorithm 1 或明確完成後的 M1；同頁不要縮小塞整套 code |
| 11 | Network and Contact | REVISE | vertex=node、edge=contact 可用，但不能同時稱為 A 的 contact-as-vertex graph；符號與前頁不統一 | 明確稱 temporal directed multigraph；統一符號 |
| 12 | Capacity and Bundle | REVISE | residual 的解釋表有「Contact 集合」誤填；Q−used 沒區分已傳/預約；單位不足 | 改為剩餘 volume，補 snapshot 及 busy interval 缺口 |
| 13 | Algorithm / dominance 公式 | REMOVE | resident equality 和 arrival inequality 與其他頁重複；沒有獨立說明 | 合併到 dominance 正式定義 |
| 14 | 第二份 Algorithm | REMOVE | 幾乎重複第 10 頁，仍未修正 buffer 與 state | 統一只留一個版本，再分 initialization / extension 展示 |
| 15 | Route Definition | REVISE | 此頁 receiver(c_k)=sender(c_(k+1)) 是正確方向，與第 1/6 頁互相矛盾；缺 o=d 空路徑 | 保留正確定義並統一全稿，補空 route 特例 |
| 16 | Transmission Time | REVISE | S/r 與 max(a,start) 在無排隊 M0 下成立；未寫 residual reservations 的占時假設 | 加 sender-window、constant rate、無 busy intervals 限制 |
| 17 | Feasibility | REVISE | window 和 capacity 條件本身合理，但只有兩條件不能支撐原本有限 buffer 問題 | 標示 M0；補 continuity，清楚排除未處理的條件 |
| 18 | Arrival Time | REVISE | s+S/r+δ 在 last-byte store-and-forward 下可用，沒有證據指出此式本身錯；文字 typo / 索引不一致 | 明確 last-byte arrival 與 sender end，可晚於 contact end |
| 19 | Objective | KEEP | earliest feasible arrival 與目前核心問題吻合，但尚未限定 M0/M1，也無 cost tie-break | 保留主目標，補 feasible set 定義；cost 版只能作為獨立可選版本 |
| 20 | 四欄 Label | REBUILD | 和第 7 頁五欄不一致；算法又使用未列的 node 欄位；incoming contact 不是必要核心 state | 使用 label_design_v02.md 單一 schema |
| 21 | 四節點 topology | REBUILD | 僅 contact windows，缺 S/r/δ/R，不能真的驗證大小 bundle routing | 使用 small_topology_v02.md 的完整 contact plan |
| 22 | Expanded graph | REBUILD | 右方 topology 與 contact 文字超出畫面被裁切；重複 IDs，state 意義不明 | 改為唯一 IDs 與可核算狀態，保留清楚留白與模板 footer |
| 23 | Expanded graph 重複 | REMOVE | 重複前頁，沒有新增 algorithm step，仍裁切 | 改用同 topology 的不同高亮狀態，不重複無註解圖 |
| 24 | SPPRC tutorial / pseudo-code | REVISE | source 是教學網站而非 Paper B 本文；成本最小 time-window 問題與本次 objective 不同；截圖字太小 | 引用 B p.17 及其 reference [11]；重寫簡潔 framework，標記哪些是 adaptation |
| 25 | Extension feasibility | REBUILD | 敘述同時列 window / R 是合理基礎；但 start 符號沒有就地明確 max，buffer 不在條件內，符號 B/R 与前文不同 | 依 extension_rule_v02.md 統一 8 步，標明模型範圍 |
| 26 | Dominance 修改 | REBUILD | 從 same-node 改 same-contact 未論證必要性；「可以等待」缺 buffer 前提；完全未處理 cost variant | M0 改 same-node 並附證明；M0-Lex 用 Pareto；有限 buffer 給反例 |
| 27 | Dominance 重複 | REMOVE | 與第 26 頁相同核心內容，未新增例子或證據 | 換成 dominance counterexample 或移除 |

## 跨頁一致性與研究問題

1. **Background 不是太多，而是缺乏連貫鋪陳。** 這份 27 頁檔案從公式與符號表開始，沒有完整 motivation、related work、實驗設計 / 結果段落。不能假設提供的是包含所有研究背景與實驗的舊版完整報告。
2. **Model 比 algorithm 更強。** 第 1/4/6/8 頁有 buffer，第 10/14 頁 pseudo-code 沒有。即使添加等待檢查，也需解決延後發送可改善 buffer 可行性的情形。
3. **Residual volume 不等於可用發送時間。** 若用真實背景流量產生 residual，必須明確其 transmission calendar，或承认現在只做 aggregate admission model。
4. **Graph 混用。** 實體 node、contact vertex、時展開 state 需要不同定義；不能只把 dominance 的比較名稱從 node 換 contact 就當完成 adaptation。
5. **傳輸時間與 propagation 公式並非全部錯。** 在 M0 語意下第 16–18 頁可保留重述；主要錯誤是適用假設未講，以及其他頁與其不一致。
6. **沒有可支持 performance claim 的資料。** 舊檔沒有實驗結果圖表與原始 data。不能以範例或 A/B 結果取代本方法成果。
7. **文獻缺口。** 「capacity-aware 是新方法」會遇 SABR §3.2.6.9(g) 與 B capacity-aware Dijkstra；需重新界定差異。

KEEP 表示核心內容適合沿用，不表示原始排版或所有 notation 已符合最後交付要求。
