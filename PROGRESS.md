# 研究進度

更新日期：2026-10-13

## 最新審查（2026-10-06）

- 完成 [研究合理性與風險審查](docs/research_reality_audit_v01.md)，列出 26 項風險、Top 10 問題、22 題口試問題，以及假設、參數、比較公平性與文件差異表。
- 新增兩次查詢的可重現模型邊界反例：同一 1 MB/s contact，兩包各 2 MB 皆被排在 [0,2)，aggregate quota 與 buffer 通過，但實際鏈路超載。資料在 `output/research_audit_v01/counterexample_sequential_overlap.json`。
- 此反例否定實際無衝突排程的外推，未推翻已明限 aggregate grid 的同模型命題。未修改演算法、程式、PPT、既有驗證結果或 comparison gate；未進行效能比較或大型實驗。
- 下一個討論優先處理 claim／calendar 範圍，以及逐 byte buffer 釋放與目標 BPA／CLA 的關係；候選修正尚未採用。

## 正式定義整理（2026-10-06）

- 新增 `formal_problem_algorithm_definition_v01.md`，統一現行問題名稱、系統假設、參數、決策變數、可行性限制、label、extension、dominance、單包搜尋與逐包更新流程。
- 定義只對應現行 finite-grid／aggregate-quota v04；沒有加入 transmission calendar，也沒有改動演算法或既有實作。
- 明確將 `U` 定義為 contact-indexed 非負用量向量，區分核心 state、路徑重建資料、全域 query context 與尚未實作的 calendar 狀態。
- 完成 `整包路由_問題參數與演算法定義_v01.pptx`：20 頁，沿用中正大學模板與標楷體，含 4 張可編輯符號表、時間軸、buffer 曲線、extension、dominance、queue、完整流程與 transmission calendar 反例；每頁均附講稿。

## 已完成

- [x] 現行 v04：有限時間格點、aggregate quota、有限 buffer、逐包資源預約。
- [x] 定義 label、extension、dominance、佇列、終止與路徑回溯。
- [x] 完成兩包 walkthrough 與逐 byte buffer 曲線。
- [x] 整理延伸與支配規則的條件式正確性論證。
- [x] 保存 14 個案例、15 次查詢的 oracle 比對結果及 18 項測試紀錄。
- [x] 保存早到不能直接支配、格點與連續時間差異、quota 與傳輸空檔差異的反例。
- [x] 完成符號公式文件、詳細簡報與 20 頁圖解；新增中央架構、研究範圍，以及 Q 中完整 label 與 U 的逐步變化。
- [x] 整理集中式 DTN 的路由位置、資訊分工、執行流程、研究假設與官方依據。

## 已知限制

- 通過有限測試不是一般性正確性證明。
- 只保證明列假設下的格點模型；連續時間完整搜尋尚未完成。
- Aggregate quota 不檢查其他包實際占用的傳輸時段。
- 逐包處理不保證多包聯合最優；處理順序可能影響結果。
- 同時生成／交付採已記錄的保守峰值約定，事件語意仍待正式統一。
- 尚無大規模執行時間、記憶體或優於既有方法的實驗證據。
- 集中式規劃暫時假設控制指令能及時送達，尚未建模控制訊息成本、分散式狀態同步或故障重規劃。

## 接下來依序處理

- [x] 統一現行問題定義、符號、公式、虛擬碼與簡報入口；明確標記舊版。
- [ ] 與指導老師確認第一階段是否採有限時間格點＋aggregate quota。
- [ ] 文獻對照並收斂論文貢獻，不能把使用 Label Setting 本身當作新穎性。
- [ ] 與指導老師確認採批次規劃或中央線上規劃，以及 bundle 的固定處理順序。
- [ ] 擴充同模型小型隨機與邊界測試，持續比對獨立完整搜尋。
- [ ] 無未解正確性差異後，比較 dominance 開／關的標籤數、時間與記憶體。
- [ ] 依確認後的範圍，另行研究 transmission calendar 或連續時間擴充。

若出現同模型錯誤，保存失敗案例、停止後續效能比較，指出造成錯誤的定義或式子，提出候選修正；未經使用者確認不直接修改演算法。

## 證據

- [驗證總結](docs/algorithm_validation_summary_v01.md)
- [現行定義摘要](docs/current_algorithm_snapshot_v01.md)
- [原始測試紀錄](output/validation/test_results.txt)
- [已知反例索引](output/validation/counterexamples_index.json)

## 1007 報告簡報定義表示更新（2026-10-06）

- 依使用者提供的 `F:/1007.pptx` 更新21頁圖解簡報，輸出 `output/presentations/1007_定義更新版_v02_20261006.pptx`。
- Label及Q改以 `(c,A,s,pred)` 表示，更新回溯圖、contact參數與講稿，統一以「剩餘可分配資料量」解釋R。
- 調整為可由完整pred鏈還原舊v04資訊的表示方式，未取消quota/dominance中的前綴用量條件，未修改現行演算法或實作。
- 修改說明與報告前核對重點：`docs/presentation_1007_definition_revision_v01.md`。
- 保留原有8秒／12秒到達結果及aggregate模型界線，未進行效能比較或新實驗。

## 可設定拓樸的實驗入口（2026-10-06）

- 新增 `src/experiments/`：JSON案例、CSV contacts、輸入檢查、逐包執行與JSON／CSV結果輸出。
- 可以替換節點與各自buffer、contact方向／時窗／速率／延遲／剩餘資料量、bundle請求與固定處理順序，以及時間格點與horizon。
- 保留原有v04搜尋核心；Label輸出提供 `(c,A,s,pred)`，內部仍保留現有資源用量cache，不擅自更換演算法。
- 有解時使用獨立完整排程及獨立提交核對，另可對小案例啟用完整搜尋比對；發現差異立即保存反例並停止後續處理。
- 新增兩個可編輯範例與 `docs/experiment_framework_v01.md`，34項測試通過；PPT案例8／12秒、半秒格點案例7/2秒，均與完整搜尋一致。
- 未執行大規模效能比較、未加入transmission calendar或實際網路傳送模擬。

## PPT拓樸路由與排程重播（2026-10-06）

- 實際執行五節點、八contacts、兩包案例，第一包c1→c2在8秒到D，第二包c4→c5在12秒到D；完整搜尋比對一致。
- 新增可重複使用的排程重播及報告模組，輸出節點／contact路徑、每跳發送與接收時間、事件紀錄、buffer數值及PNG／SVG圖。
- 分段線性精確計算，各節點buffer峰值X/A/B/D為4MB、C為0；選定傳輸的同contact時段重疊為0筆。
- 保留原有事件峰值約定，目的地完整接收後立即交付，包含horizon末端的釋放。
- 對照修正版1007簡報的contact表、bundle起訖／生成時間／大小及buffer設定；核對紀錄與報告位於 `output/experiments/ppt_topology_run_20261006/`。
- 重播是選定排程的事後檢查，沒有改動v04、啟用calendar搜尋或宣稱實際BP／共用radio驗證。


## Buffer 圖時間軸調整（2026-10-07）

- 依提供圖片重繪，時間軸改為 0–12 秒，使用標楷體。
- 保留 t≥2 的原圖曲線，未推測 0–2 秒數值；不修改演算法或模擬結果。
- 輸出：`output/figures/buffer_chart_axis_zero_20261007/`（PNG、SVG）；已目視檢查。


## 早到候選 Buffer 圖補齊（2026-10-07）

- 補畫第二包於 1–2 秒接收的曲線；第一包於 2–3 秒接收，紅線是兩包合計。
- 圖示為不可行的 c3→c5 候選，不是已接受排程；不修改演算法。
- 核對折點相加與圖片；輸出 `output/figures/buffer_early_arrival_full_timeline_v02_20261007/`，舊圖保留。


## 小型實驗套件（2026-10-11）

- 新增可設定的9案例批次入口：8組參數／順序檢查，加1組aggregate模型重疊示例，共18包。
- 全部與獨立完整搜尋及預期抵達一致；獨立排程與資源更新通過。09保留同contact時段衝突1筆，不宣稱實體可執行。
- 保留時間枚舉與舊內部usage cache，未改路由核心、未使用SimPy或做效能比較。
- 新增失敗即停與證據保留的批次測試；全套40項測試通過。
- 說明：`docs/small_experiment_suite_v01.md`；結果：`output/experiments/small_suite_v01_20261011/`。


## 演算法互動過程（2026-10-11）

- 新增9案例搜尋與已接受排程的互動重播，展示Contact延伸、枚舉、拒絕原因、Dominance、Q及Buffer即時占用。
- 直接讀取既有v04紀錄，未改演算法；持續標示內部usage cache與非SimPy界線。
- 瀏覽器核對9案例／18查詢／179步、播放、事件峰值與釋放，以及320px寬度；保存截圖與browser_checks.json。
- 說明：`docs/process_visualization_v01.md`；產生器：`src/experiments/process_view.py`。


## 桌面實驗 GUI（2026-10-11）

- 新增Tkinter桌面GUI、雙擊啟動入口、既有結果載入與JSON案例執行。
- 支援搜尋步驟／排程播放、Label與Q表、Contact與剩餘容量、Buffer即時占用。
- 以獨立子程序執行原路由，中止保留部分資料與標記；未改凍結v04核心，內部usage cache仍保留。
- 179步GUI操作、播放、背景執行／載入、中止與Buffer事件檢查通過；40項回歸測試通過。
- 共用載入器重構前後的瀏覽器資料完全一致；已檢查Windows DPI畫面。
- 說明：`docs/desktop_gui_v01.md`；檢查與截圖：`output/visualizations/desktop_gui_v01_20261011/`。

## Ring Road 公開資料來源核對（2026-10-11）

- 新增 docs/ring_road_contact_plan_source_v01.md，找到公開 Walker Ring Road Contact Plan；排除額外 Server 後恰為 47 節點、3,172 條 Contact，範圍為一天。
- 原檔速率為 12,500 Bytes/s，與學長論文的 100 KB/s 不同；range 值皆為零。逐筆同一性與真實傳播延遲尚未確認。
- 下載暫存於 Git 忽略的 tmp/topology_sources，未修改演算法、未導入正式實驗。

## Ring Road 初步實驗（2026-10-11）

- 已套用47節點、3,172條Contact的完整一天輸入。12組壓力設定有11組完成；5包、每包1,200 KB組延長至300秒仍只完成前2筆查詢，保留部分路徑，不推論無路徑。
- 12組短窗口設定全部完成。兩個隨機單包全日設定以精簡版重試，皆在120秒逾時；不能用固定來源壓力案例替代一般流量結論。
- 原 frozen v04 未修改，內部仍含 usage cache、保留時間枚舉。新增相同判別式的執行轉接版，僅調整索引及詳細紀錄方式；36次小案例查詢與原版的路徑、抵達、統計、決策事件及Q長度一致。
- 45項測試通過；24組輸出、109筆完整查詢通過摘要／Label／Buffer／重疊紀錄一致性檢查。完整全日組接受45包，其中38包達到最後一跳下界，可就該查詢確認最早抵達；其餘尚未取得最優證明。
- 中繼37 Buffer降至0.3 MB時，後續包由22→37→5改走22→36→5，抵達由1466變2906秒；同Contact傳送重疊仍存在，不是實體可執行排程證明。
- 統一結果：output/experiments/ring_road_study_v01_20261011；圖表：output/figures/ring_road_study_v01_20261011；方法：docs/ring_road_experiment_protocol_v01.md。
- 尚未完成學長50–175條Flow規模、其他方法公平比較、多seed與正式重複計時；下一步先討論重疊排程界線及可保留時間枚舉的搜尋效率改善，不自行新增剪枝判別。

## 論文格式虛擬碼（2026-10-12）

- 新增 `docs/thesis_pseudocode_v01.tex` 與中文對照 `docs/thesis_pseudocode_v01.md`；已核對 frozen v04、四欄位 Label 表示法與現行程式。
- 包含參數定義、延伸／Buffer／dominance 判別式，以及單包搜尋、依序預約與回溯三個演算法。未修改演算法或重跑實驗。
- 明列 aggregate 容量、有限格點、來源 Buffer、已展開 Label 仍參與 dominance、保留前驅紀錄及逾時不等於無路徑等界線。
- 已開啟 LaTeX 編輯器；內建編譯器回報平台目錄錯誤，PDF 版面尚未驗證。下一步為確認論文模板與演算法內容，再於可用編譯環境確認排版。

## PPT 拓樸與可替換演算法架構（2026-10-12）

- 將執行設定、拓樸、Contact CSV、Bundle需求分開；新增演算法入口，可選內建方法或本機 module:function，共用逐包預約與獨立驗證。
- 沿用 frozen v04，未改動演算法判別式。PPT 兩包結果為 c1→c2（8秒）、c4→c5（12秒），與獨立完整搜尋一致。
- 新增 departure_candidates.csv，可直接查看各起送時間的延伸結果與支配者；另保存人工「前段不可用、後段可用」案例。
- 50項測試通過；此次沒有進行大型或效能比較實驗。說明：docs/modular_routing_v01.md；PPT結果：output/experiments/ppt_modular_20261012/。

## 中文程式註解與流程圖（2026-10-12）

- 為既有37個Python檔案及網頁重播模板補上中文註解；核心逐段說明時間枚舉、Buffer、dominance、Q、前驅保留與預約提交。
- 新增系統架構、逐包預約、單包Label Setting三張圖，提供PNG／SVG及Mermaid原稿；圖稿產生器位於src/experiments/render_code_diagrams.py。
- 註解前後Python語法樹一致；新增圖稿產生器不執行路由。導讀：docs/code_reading_guide_v01.md。驗證紀錄另存output/validation/code_comments_20261012/，不覆寫原有凍結紀錄。

## GitHub Pages 逐步圖解（2026-10-12）

- 新增 web/ 靜態網站，顯示拓樸、候選路徑、Q 前後、四欄位 Label、Buffer 曲線與峰值、支配比較、前驅回溯及同步虛擬碼。
- PPT 兩包與人工後段可行案例直接匯出既有 trace，匯出前重新獨立驗證排程；沒有改動 frozen v04 或重跑大型實驗。
- 支援逐步、倒退、播放、進度條、節點篩選及匯入匯出格式 JSON；屬於已保存搜尋紀錄重播，不在瀏覽器重新求解。
- 52 項 Python 測試與前端狀態檢查通過；瀏覽器逐步走完三個查詢無 console error。
- 網站 https://bagle102.github.io/space-dtn-thesis/ 由 GitHub Actions 部署 web/，詳細操作見 docs/github_walkthrough_website.md。

## 現行演算法待釐清問題（2026-10-12）

- 新增 [待釐清問題清單](docs/open_questions_v01.md)：先定論文 claim、固定的延伸與支配 SOP、接收端可用開始時間的精確定義。
- 分開整理格點模型內正確性、aggregate 與實際傳送的差距，以及完成定義後才做的效率／公平比較。
- 已保存的同 Contact 重疊反例屬模型外推失效；此次未搜尋新的同模型反例，未修改 frozen v04 或執行效能比較。

## 網站虛擬碼註解與流程修正（2026-10-13）

- 新增 `docs/annotated_label_setting_pseudocode_v01.md`，逐行註解現行有限格點搜尋與依序預約；明列來源 Buffer、全部起送時間枚舉、延伸時 Buffer、支配、獨立驗證及提交。
- 修正網站虛擬碼原先「到目的地直接 return，後面再驗證／預約」的不可達流程，改為回溯後跳出搜尋、驗證、提交；同步調整執行步驟亮起位置。核心路由判別式未變更。
- JavaScript 語法與重播狀態檢查通過，於瀏覽器核對目的地與提交步驟的亮行。
