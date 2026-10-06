# 研究進度

更新日期：2026-10-06

## 最新審查（2026-10-06）

- 完成 [研究合理性與風險審查](docs/research_reality_audit_v01.md)，列出 26 項風險、Top 10 問題、22 題口試問題，以及假設、參數、比較公平性與文件差異表。
- 新增兩次查詢的可重現模型邊界反例：同一 1 MB/s contact，兩包各 2 MB 皆被排在 [0,2)，aggregate quota 與 buffer 通過，但實際鏈路超載。資料在 `output/research_audit_v01/counterexample_sequential_overlap.json`。
- 此反例否定實際無衝突排程的外推，未推翻已明限 aggregate grid 的同模型命題。未修改演算法、程式、PPT、既有驗證結果或 comparison gate；未進行效能比較或大型實驗。
- 下一個討論優先處理 claim／calendar 範圍，以及逐 byte buffer 釋放與目標 BPA／CLA 的關係；候選修正尚未採用。

## 正式定義整理（2026-10-06）

- 新增 `formal_problem_algorithm_definition_v01.md`，統一現行問題名稱、系統假設、參數、決策變數、可行性限制、label、extension、dominance、單包搜尋與逐包更新流程。
- 定義只對應現行 finite-grid／aggregate-quota v04；沒有加入 transmission calendar，也沒有改動演算法或既有實作。
- 明確將 `U` 定義為 contact-indexed 非負用量向量，區分核心 state、路徑重建資料、全域 query context 與尚未實作的 calendar 狀態。

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

- [ ] 統一現行問題定義、符號、公式、虛擬碼與簡報入口；明確標記舊版。
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
