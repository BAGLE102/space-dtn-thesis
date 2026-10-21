# 研究進度

更新日期：2026-10-21

## 研究驗證工作規劃（2026-10-21）

- 新增 `docs/research_validation_roadmap_20261021.md`：模型對齊、最小區分案例、獨立正確性對照、模組實作、同模型與不同模型實驗及決策條件。
- 優先驗證同步接收／釋放差異與 quota 需求，包含設備、順序公平性、開端點及搜尋完整性風險；三至四週為初步工作安排，不是完成承諾。
- 僅完成規劃，未改 PPT／演算法或產生效能結果。

## Contact splitting 相關工作比對（2026-10-21）

- 核對使用者提供2410.15546v3的FEAP-CB、contact splitting、forecast buffer tables與edge pruning，確認與目前切割方向高度重疊。
- 原文已處理S/r、前包預約、依bundle暫時切割及避免等待跨越溢位；不能把這些單獨主張新貢獻。
- 逐byte起送集合、允許walk／容量歷史與事件端點列為待核對差異；尚未重現論文原碼或確認效能／新穎性。見 `docs/paper_2410_15546v3_contact_splitting_comparison_20261021.md`；未修改PPT。

## 起送時段候選簡報（2026-10-21）

- 依使用者1013製作32頁 `output/presentations/1021_起送時段修訂版.pptx`，採A3b容量配額與P事件順序，保留具體四欄Label，替換逐秒枚舉／抵達區間Label。
- 補上來源／目的地端點、容量次數支配、incompleteLB結果標記、逐次造訪曲線提交及兩頁英文虛擬碼；方法尚待實作與一般正確性驗證。
- 固定排程核對第一包8秒、第二包12秒與最終容量；32頁逐頁檢查，原1013及舊1021保留。修改詳見 `docs/1021_concrete_start_intervals_ppt_20261021.md`。

## 外部 AI 可持有時段方案審查（2026-10-21）

- 已審查外部第二版：容量次數已納入候選支配；保存Rule B來源事件差異，指出跳變下返回值、切片虛擬碼及commit持有段仍需補齊。見 `docs/ai_safe_interval_revision_review_20261021.md`；未修改PPT或演算法。
- 保留具體時間Label的候選方向有條件成立；對照SIPP一手文獻，尚非原DTN模型的完整證明。
- 核對外部固定排程，保存獨立quota下「同節點＋同持有時段」不足以支配的容量反例。
- 審查見 `docs/ai_safe_interval_review_20261021.md`；不修改PPT、路由定義或網站，不做效能比較。

## 長Contact拓譜簡報（2026-10-21）

- 依1013版型另製32頁長Contact PPT，採完整容量版本，重新推導兩包區間、Q、D的接收缺口及回溯，不直接替換舊時間數字。
- 圖解排程：第一包c1→c2抵達10秒；第二包c6→c8抵達5秒。c3起送 `{1}∪[8,10]`，c8起送 `[4,8]∪[10,13]`；9組固定排程核對符合預期，非區間搜尋或效能驗證。
- 輸出 `output/presentations/1021_長Contact拓譜版.pptx`，說明見 `docs/1021_long_contact_ppt_20261021.md`；保留原1013與1021。

## 長contact拓譜輸入（2026-10-21）

- 沿用原PPT五節點／八連線／兩包需求，另建時窗長10～17秒、上限40秒的人工拓譜，錯開同端點重複contacts。
- 提供完整初始容量與沿用原quota兩份輸入、表格、標楷體拓譜／時間軸圖；輸入格式及時窗邊界檢查通過。
- 僅準備輸入，不執行已廢棄的枚舉或尚未實作的區間方法；未修改1021簡報。說明在 `configs/long_contacts_20261021/README.md`。

## 1021區間方法簡報（2026-10-21）

- 依1013.pptx修訂32頁簡報，正式展示流程移除逐秒枚舉，改為contact可起送區間J、完整持有區間W與區間Label `(c,I,pred,K)`。
- 保留兩包拓譜及原參數，更新區間延伸、Q、等待拒絕、時間回溯、容量共用與英文虛擬碼；暫不做支配刪除。
- 本版是待驗證的候選設計，尚未實作／證明或比較效能；舊網站與程式沒有自動切換成此方法。
- 輸出 `output/presentations/1021.pptx`；修改對照與待完成事項見 `docs/1021_ppt_interval_revision_20261021.md`。

## Codex工作效率設定（2026-10-20）

- 使用者追加允許Skills後，已安裝並驗證token-efficient-workflow；正常按需匹配，來源固定commit，未覆寫ADHD skill。實際整體token節省仍未量測。

- 查核RTK／Serena／Context7與官方上下文設定；安裝RTK OSS 1.0.1並校驗資產digest，設定個別工具歷史輸出預算4000tokens。
- AGENTS新增按需搜尋／讀檔與避免過量輸出的規則；保留原始失敗證據，不修改研究演算法。設定備份與執行檔僅在本機，不上傳。
- 本機兩組唯讀Git查詢stdout分別縮小72.4%與55.6%；不是帳單或帳戶額度節省量測。詳細來源、範圍與回復方式見 `docs/codex_efficiency_setup_20261020.md`。

## 診斷拓譜與情境覆蓋（2026-10-14）

- 新增人工12節點／32 contacts／5 bundles拓譜、contact表與圖，另建12個隔離案例與26項情境清單；分開標示本次核對、既有案例與待測。
- 18次查詢與獨立完整列舉一致；大拓譜4包成功、1包無路徑。晚到才可行、接收途中峰值與邊送邊接收等小案例均符合事先人工預期。
- 未修改路由、Label或支配規則；動態可用contact區間仍是候選方案，不能以此結果宣稱已驗證。17項相關回歸測試通過。
- 細節見 `docs/diagnostic_topology_and_coverage_v01.md`；下一步以案例12檢查動態區間選時是否保留較晚可行方案。

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

- 新增 `docs/annotated_label_setting_pseudocode_v01.md`，保留英文虛擬碼，僅在 Q、容量、枚舉、回溯與提交等關鍵步驟加簡短註解。
- 修正網站虛擬碼原先「到目的地直接 return，後面再驗證／預約」的不可達流程，改為回溯後跳出搜尋、驗證、提交；同步調整執行步驟亮起位置。核心路由判別式未變更。
- JavaScript 語法與重播狀態檢查通過，於瀏覽器核對目的地與提交步驟的亮行。

## PPT 規則補充（2026-10-13）

- 以使用者 PPT 為準，新增 contact 發送時段檢查、Q 次序說明、支配適用範圍與待驗證項目，共25頁。
- 詳見 docs/ppt_1007_revision_20261013.md。未修改程式、網頁或 frozen v04。

## 八節點五包測試資料（2026-10-13）

- 新增 configs/topology_8nodes_5bundles：8節點、18 contacts、5個4MB bundles，含B/D單包Buffer瓶頸與早晚班替代路徑。
- 現有載入器檢查通過，未執行路由。legacy設定明示未加入新版PPT的發送時段互斥，不宣稱新版結果。

## 接收端判斷補充（2026-10-13）

- 完成29頁版PPT，新增4頁符號解釋、接收Buffer公式、數值例子及候選篩選流程；原25頁文字保留。
- 候選流程仍保留枚舉，接收可行後仍須檢查其餘限制；未修改程式、支配規則或執行實驗。
- 詳見 `docs/ppt_1007_revision_20261013.md`；下一步確認候選定義是否符合預期。

## 接收可行起送時間圖解（2026-10-13）

- 完成33頁版PPT，在前段c4流程前加入4頁輸入／候選時間／接收曲線／輸出時間圖解（第11～14頁），保留原29頁內容。
- 以原c4例子確認接收可行開始時間為{7,8}、接收期間峰值均4MB；只補圖解，未修改程式或支配規則。
- 下一步先檢查新增第11～14頁的報告敘述。

## PPT小案例驗證（2026-10-13，使用者同意暫不做支配刪除）

- 新增獨立`src/ppt_validation/`，使用四欄Label、有限格點、容量、同contact發送時段及逐byte Buffer；DAG範圍，不修改frozen v04／網站／PPT。
- PPT兩包抵達8、12秒；八節點五包前4包抵達12、12、13、20秒，第5包無解。全部7次查詢與完整列舉核對一致。
- 第5包9個起送候選皆接收Buffer峰值8MB大於4MB，未為成功率改參數。
- 6項新驗證測試＋5項既有模組回歸測試，共11項通過。輸出路徑、各跳時間、Label/Q事件、拒絕原因、逐包預約、統計與Buffer／contact圖。
- 定義、結果、重現命令：`docs/ppt_validation_experiments_20261013.md`；資料：`output/ppt_validation_20261013/`。
- 這是人工小案例驗證，不是一般正確性證明或效能比較。下一步先核對五包排程，再定案支配規則。

## 選用學長Ring Road情境（2026-10-13）

- 使用者選擇沿用學長拓樸。準備公開Walker Ring Road＋論文參數：47節點／3,172 contacts／一天／100KB/s／30,000KB Buffer，十進位單位假設明列。
- 完成轉換程式、參數設定、來源SHA核對及格式驗證，保留循環與短contact；2項轉換測試通過。資料在`tmp/ring_road_ppt_thesis/`本機存放。
- `configs/ring_road_thesis/README.md`記錄重建方法與限制。未確認與學長實際輸入逐筆相同，δ=0暫為假設，未選五包需求、未跑新版路由。
- 現有驗證版僅DAG，下一步先定案循環／前綴資源處理，不直接刪除DAG防護。

## 允許循環的驗證版（2026-10-13，使用者確認修改）

- 移除DAG限制，允許重訪節點與contact，沿pred臨時計算已用容量；四欄Label、時間枚舉、Q排序、Buffer與無支配策略保留。
- 完整列舉核對改以正每跳耗時界定walk深度，保留循環；上限超出仍為INCOMPLETE而非無解。
- 繞圈案例ab→ba→ab→bd在5秒抵達，ab容量扣兩次；ab容量只夠一次時雙方皆判定無解。
- 原PPT兩包及八節點五包結果不變；16項相關測試通過，未跑整天Ring Road或效能比較。
- 虛擬碼與符號：`docs/ppt_label_setting_cycles_pseudocode_v01.md`；新資料：`output/ppt_cycles_20261013/`。

## Ring Road五包短時窗測試（2026-10-13）

- 保留47節點，截取1342～1352秒的10個活動contacts，5包各100KB，來源9、目的地2、生成1342秒；沿用學長100KB/s／30MB Buffer，δ=0假設。
- 5包皆走9→41→2，抵達1344～1348秒，延遲2～6秒；先前預約使後包依序晚送。
- 每包完整排程及獨立時間順序完整列舉核對一致；18項相關測試通過。待測路由規則未改，只增加可替換核對器與測試入口。
- 結果：`output/ring_road_pilot_20261013/`；設定／限制：`docs/ring_road_pilot_20261013.md`。
- 本輪Buffer非瓶頸，未測整天或實體收發器互斥，未進行效能比較。

## Ring Road擴充批次（2026-10-13）

- 事先列明14組／330包：包數10、20、50、100；大小200KB、500KB、1MB；4個其他來源／目的地；混合來源、低Buffer診斷與20秒窗口。
- 每組驗證上限20秒。9組完整完成，5組超時；206包完成獨立核對（87可行、119無路徑），124包未處理。超時不是無路徑，沒有整天或演算法效能結論。
- load_20的20包查詢皆核對完成，但彙整前超時，仍保留整組未完成狀態。完整列舉與輸出也計入時間上限，不能歸因為搜尋耗時。
- 待測search.py未修改；20項相關測試通過。資料與圖：`output/ring_road_batch_20261013/`；全部設定：`configs/ring_road_batch_20261013/`。

## 一萬包規劃與對照組（2026-10-13）

- 新增單節點最早一個Label的貪婪對照，沿用相同延伸限制，非完整CGR／SABR，不聲稱完整性。
- PPT案例：你的方法2/2、對照1/2；Ring Road原五包：兩組皆5/5且抵達時間相同。成功路徑與提交資源皆獨立核對；22項相關測試通過。
- 比較資料：`output/single_label_baseline_20261013/comparison.json`；規劃：`docs/ten_thousand_bundle_comparison_protocol_v01.md`。
- 尚未執行一萬包；生成方式（一日分散／同時壓力）待使用者選擇。大規模需將完整列舉與搜尋量測分開，且不得把未完成當作無路徑。
