# Algorithm walkthrough plan v02

狀態：僅規劃，等待 Algorithm 與 Storyline 確認後才產生正式 figures / PPTX。

## 統一 topology

來源為 small_topology_v02.md。固定座標建議（normalized）：A=(0.08,0.5)、B=(0.38,0.12)、C=(0.38,0.5)、D=(0.38,0.88)、E=(0.88,0.5)。每幀保持同一位置與同一組 c1–c8 edges；需用小幅彎曲區別交叉邊。

每條 contact 清楚標 cID、[start,end)、r、R；共同 δ=1 s、S=4 MB 放在固定角落。資料與 unit 不省略。Q 可放 contact table，不必塞滿每條 edge。這是 physical-node contact topology，不命名為 contact-as-vertex graph。

| Figure | 規劃檔名 | 對應步驟 | 高亮 / annotation |
|---|---|---|---|
| 1 Initial Contact Topology | algorithm_step_00_initial.png | 輸入 | 所有 contacts 中性灰；c2 標 R=3；右側小 contact table |
| 2 Source Label Initialization | algorithm_step_01_initialization.png | step 0 | A 高亮，L0=(A,0)、U=[A0] |
| 3 First Expansion | algorithm_step_02_expansion.png | steps 1–3 | c1/c3/c5 藍色；B3、C5、D6；U=[B3,C5,D6] |
| 4 Capacity-Infeasible Contact Rejected | algorithm_step_03_capacity_rejection.png | steps 4–5 | c2 紅色叉號 R=3<4；c8 另標 WINDOW 5>4，避免誤認兩者同因 |
| 5 Remaining Labels | algorithm_step_04_remaining_labels.png | step 6 | 高亮 C5 與 c4，顯示 E9 candidate；D6 尚待展開 |
| 6 Dominance / Pruning | algorithm_step_05_dominance.png | steps 7–8 | 虛線 D8、E11 labels；保留 D6、E9；清楚區分 prune label 與刪除 contact |
| 7 Destination Reached | algorithm_step_06_destination.png | step 9 | E9 被 ExtractMin；強調不同於「生成時就回傳」 |
| 8 Final Feasible Route | algorithm_step_07_final_route.png | reconstruction | c3/c4 綠色，其他 edges 灰色；列 [0,4)、[6,8) 與 A*=9 |

目的資料夾：`figures/algorithm_walkthrough/`。目前未生成該資料夾的正式圖檔。以上每一幀用同張 topology 變更狀態，不生成裝飾圖片。

## PPT 的呈現規劃

正文 walkthrough 用 4 頁：初始化與首次 expansion、capacity/window rejection、label dominance、destination extraction / reconstruction。八個 figures 可供動畫步驟或附錄使用。每頁保留 3 個短 bullet，其餘算式放 speaker notes。

另規劃獨立的 lexicographic counterexample 和 finite-buffer timeline，不混入 M0 walkthrough，避免讀者以為 Algorithm 1 已處理那些模型。
