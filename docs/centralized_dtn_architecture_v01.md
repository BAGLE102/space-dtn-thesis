# 集中式 Space DTN 架構與研究假設 v01

更新日期：2026-10-06  
文件狀態：論文「系統模型與研究假設」章節草稿  
演算法狀態：本文件整理執行環境，不修改現行 v04 演算法

## 1. 這份文件要回答的問題

本文件釐清下列問題：

1. 集中式管理能否作為 Space DTN 的研究環境？
2. 路由計算、傳送排程與實際轉送分別在哪裡執行？
3. 中央端更新 contact 資源後，是否必須把完整狀態廣播給所有節點？
4. 多個 bundle 依序規劃時，前一個 bundle 如何影響後一個 bundle？
5. 哪些內容有標準或 NASA 資料支持，哪些只是本研究採用的假設？

## 2. 核心結論

本研究可以採用「中央規劃、節點依排程執行」的 Space DTN 模型。中央規劃器保存完整的 contact plan 與已預約資源，依序替 bundle 計算路徑；節點只需取得與自己有關的轉送指令及本地 contact 資訊，不需要各自保存完整的全網資源狀態。

這個架構是合理的研究假設，但不是所有 DTN 系統都必須遵守的標準。論文中應明確限制為「已知或可預測 contact、可在傳輸前完成規劃、控制指令能及時送達」的任務型 Space DTN。

## 3. 證據層級

| 標記 | 意義 | 論文中的用法 |
|---|---|---|
| **[標準]** | IETF RFC 或 CCSDS 標準明確定義的行為 | 可作為通訊架構與名詞依據 |
| **[NASA 實作資料]** | NASA 技術報告或軟體需求文件描述的做法 | 可證明此類設計具有實際系統依據，但不能寫成強制標準 |
| **[本研究假設]** | 為了定義研究問題而採用的限制 | 必須在系統模型中明列，不能宣稱是 DTN 的一般事實 |

### 3.1 標準與官方資料支持的部分

- **[標準]** Bundle Protocol 可用於間歇連線、長延遲，以及預先排定或預測的連線環境，並以 store-carry-forward 方式運作。
- **[標準]** BPv7 不規定 bundle route computation algorithm，也不規定如何建立節點的 routing 或 forwarding information base。因此，路由可採集中式或分散式設計，取決於系統實作。
- **[標準]** CCSDS Schedule-Aware Bundle Routing（SABR）處理拓撲穩定、連線時間隨排程改變的網路，這與已知 contact plan 的 Space DTN 相符。
- **[NASA 實作資料]** NASA 的 Contact Graph Routing（CGR）資料說明，任務通訊通常事先規劃，可由 contact plan 推導路由。
- **[NASA 實作資料]** NASA HDTN 的需求文件允許 router 自行計算多跳路徑，也允許使用預先計算的路由；contact plan 改變時可重新計算。

### 3.2 必須明列為本研究假設的部分

- **[本研究假設]** 系統有一個可取得全域資訊的中央規劃器。
- **[本研究假設]** 在本次規劃時間範圍內，contact plan 已知且不發生未預期中斷。
- **[本研究假設]** 中央端知道每個節點的 buffer 上限，以及先前已接受 bundle 所造成的資源占用。
- **[本研究假設]** bundle 按固定順序逐一規劃；先接受者先預約資源。
- **[本研究假設]** 路徑與傳送指令能在相關 contact 開始前送達節點。
- **[本研究假設]** 現階段不計入控制訊息的傳送延遲、頻寬成本與失敗重規劃成本。

## 4. 系統角色與資訊分工

### 4.1 中央規劃器

中央規劃器負責：

- 保存原始 contact plan，包括傳送端、接收端、開始時間、結束時間與傳輸速率。
- 保存已接受 bundle 的資源預約紀錄。
- 依固定順序替每個不可分割 bundle 計算可行路徑與傳送時間。
- 檢查 contact 剩餘容量、完整傳輸時間與逐 byte buffer 占用。
- 接受路徑後更新資源狀態，再處理下一個 bundle。
- 將每個節點需要執行的局部傳送指令送往相關節點。

### 4.2 Bundle 節點

相關節點負責：

- 在 bundle 到達後保存資料。
- 依中央端提供的局部指令，於指定 contact 與時間送出 bundle。
- 透過 Bundle Protocol Agent（BPA）與 convergence-layer adapter（CLA）完成實際收送。
- 保有執行本地排程所需的資訊，但不必知道其他不相關 contact 的全域預約狀態。

因此，「中央管理」不代表節點完全不需要 contact 或排程資訊；它代表全域路由決策與資源衝突處理由中央端統一完成。

## 5. 路由、排程與轉送的位置

| 階段 | 本研究使用的中文 | 執行位置 | 內容 |
|---|---|---|---|
| Route computation | 路由計算 | 中央規劃器 | 選擇 bundle 經過哪些 contact |
| Transmission scheduling | 傳送排程 | 中央規劃器 | 決定各 contact 的開始與結束傳送時間 |
| Resource reservation | 資源預約 | 中央規劃器 | 更新剩餘容量與 buffer 占用紀錄 |
| Forwarding | 實際轉送 | 各 bundle 節點 | 在 contact 發生時實際送出與接收資料 |
| Simulation | 模擬執行 | 實驗程式 | 用虛擬時間重現上述狀態變化，不代表路由只能在模擬器中執行 |

論文中建議固定使用「路由計算」、「傳送排程」、「資源預約」、「實際轉送」四個詞，避免混用「routing」來同時指稱計算與資料傳送。

## 6. 多 bundle 的中央依序規劃流程

假設 bundle 的處理順序為 \(b_1,b_2,\ldots,b_m\)。中央端維護原始 contact plan \(C\) 及可變動的資源狀態：

- \(R_c\)：contact \(c\) 的剩餘 aggregate quota。
- \(O_v(t)\)：節點 \(v\) 在時間 \(t\) 的已預約 buffer 占用量。
- \(M_v\)：節點 \(v\) 的固定 buffer 上限。
- \(\Omega_c\)：contact \(c\) 已預約的實際傳輸時間區間；此項為未來 transmission calendar 版本使用。

處理流程如下：

1. 根據軌道、任務與鏈路資料建立原始 contact plan \(C\)。
2. 讀取下一個 bundle \(b_k=(o_k,d_k,S_k,g_k)\)，其中包含來源、目的地、大小與生成時間。
3. 以處理 \(b_k\) 前的 \(R_c\) 與 \(O_v(t)\) 作為固定資源狀態，執行 Label Setting 搜尋。
4. 搜尋每次延伸 label 時，檢查 contact 時窗、完整傳輸時間、剩餘 quota 與逐 byte buffer 可行性。
5. 若找到可接受路徑，回溯 contact 序列及各跳傳送時間。
6. 將該路徑正式寫入 \(R_c\) 與 \(O_v(t)\)；若未來啟用 transmission calendar，再同步寫入 \(\Omega_c\)。
7. 以更新後的資源狀態處理 \(b_{k+1}\)。

以兩個 bundle 為例，A 的路徑一旦被接受，中央端先登記 A 的資源占用；B 隨後搜尋時看到的是「已扣除 A 預約」的資源狀態。這不是修改 contact 的可見時間或物理速率，而是在原始 contact plan 之外維護一份可變動的預約紀錄。

## 7. Contact plan 與資源狀態應分開

為避免論文表達混亂，建議把資料分為兩層：

### 7.1 原始 contact plan

描述可預測的連線條件，例如：

\[
c=(u_c,v_c,\alpha_c,\omega_c,r_c,\delta_c)
\]

其中 \(u_c\) 與 \(v_c\) 為傳送端與接收端，\(\alpha_c\) 與 \(\omega_c\) 為 contact 時窗起點與終點，\(r_c\) 為傳輸速率，\(\delta_c\) 為傳播延遲。

### 7.2 可變動的資源預約狀態

描述已接受 bundle 對資源的占用，包括：

- contact 剩餘 aggregate quota；
- 各節點隨時間變化的 buffer 占用量；
- 未來版本中各 contact 已預約的傳輸時段。

因此，較精確的說法是「B 使用相同的原始 contact plan，但查詢已被 A 更新的資源預約狀態」，而不是「B 使用一張被 A 改過的 contact plan」。

## 8. 現行 v04 的精確範圍

現行 v04 已包含：

- 中央端依序處理單一 bundle query；
- 不可分割 bundle；
- contact 時窗與完整 transmission delay；
- aggregate quota；
- 固定 buffer 上限與逐 byte 接收／釋放量；
- 有限時間格點上的 Label Setting 搜尋；
- 每包以最早完整到達為目標。

現行 v04 尚未包含：

- 以 transmission calendar 檢查已預約傳輸時段是否重疊；
- 連續時間上的完整搜尋；
- 多 bundle 聯合最佳化；
- 動態故障、contact 臨時取消或狀態過期；
- 控制指令的傳送成本與送達失敗；
- 分散式節點間的資源同步協定。

所以目前的貢獻不能只寫成「把容量不足的 contact 過濾掉」。較完整的研究內容是：在中央依序預約的 Space DTN 中，以 Label Setting 同時處理 contact 時窗、不可忽略的完整傳輸時間、不可分割 bundle、aggregate quota 與逐 byte buffer 占用，並尋找有限時間格點上的最早完整到達路徑。

## 9. 可直接放入論文的系統模型草稿

> 本研究考慮一個具有可預測 contact 的 Space DTN。系統採中央規劃架構，由中央規劃器保存完整 contact plan、節點 buffer 上限，以及先前已接受 bundle 的資源預約紀錄。每個 bundle 不可分割，並依既定順序逐一進行路由計算；當一條路徑被接受後，中央規劃器立即更新相關 contact 的剩餘 aggregate quota 與沿途節點的逐 byte buffer 占用，後續 bundle 再以更新後的資源狀態進行搜尋。中央規劃器負責產生路徑與傳送排程，節點則依事先取得的局部指令執行 store-and-forward。本文假設 contact plan 在規劃時間範圍內已知、控制指令可在 contact 開始前送達，且不考慮未預期的鏈路中斷與控制訊息成本。

## 10. 論文中應避免的過度主張

- 不要寫「DTN 的路由一定由中央控制」。BPv7 並未規定路由演算法或 routing information 的建立方式。
- 不要寫「所有節點完全不需要 contact plan」。節點仍須有足以執行本地轉送的 contact 與排程資訊。
- 不要寫「中央端更新後不需要任何通訊」。中央端仍須在執行前把相關指令送到節點，只是不需要把完整全域狀態廣播給所有節點。
- 不要把 NASA 技術報告寫成 CCSDS 強制規定。NASA 文件是實作與系統設計依據；CCSDS 與 IETF 文件才是標準依據。
- 不要宣稱目前已解決多包聯合最佳化。現行做法是固定順序的 sequential reservation，結果可能受處理順序影響。
- 不要宣稱 aggregate quota 等同 transmission calendar。aggregate quota 只能表示累積可用量，無法單獨排除同一 contact 上的傳輸時段衝突。

## 11. 與 2024 年論文的關係

2024 年相關研究可用來說明「全域 contact 與 buffer 資訊」的理想化集中式模型，但它不是 DTN 架構標準。本研究若採集中式規劃，應自行明列資訊可得性、控制指令送達與無突發中斷等假設，而不是直接把該論文的假設當作現實網路的一般事實。

目前的區別可表達為：該研究是 related work；本研究則在明確的中央依序預約架構下，聚焦不可分割 bundle 的 transmission delay、contact 資源與逐 byte buffer 可行性，並以 Label Setting 求解。

## 12. 主要參考資料

1. IETF, [RFC 9171: Bundle Protocol Version 7](https://www.rfc-editor.org/rfc/rfc9171.html). 參考重點：store-carry-forward、scheduled/predicted connectivity，以及 route computation 與 routing information 建立方式不在 BPv7 規範範圍內。
2. IRTF, [RFC 4838: Delay-Tolerant Networking Architecture](https://www.rfc-editor.org/rfc/rfc4838.html). 參考重點：DTN 架構與持久儲存概念。
3. CCSDS, [CCSDS 734.3-B-1: Schedule-Aware Bundle Routing](https://ccsds.org/publications/allpubs/entry/3167/). 參考重點：已排定 contact 下的路由架構。
4. NASA NTRS, [Contact Graph Routing](https://ntrs.nasa.gov/search.jsp?R=20120006508). 參考重點：由任務通訊規劃與 contact plan 推導路由。
5. NASA NTRS, [Contact Multigraph Routing](https://ntrs.nasa.gov/api/citations/20230002637/downloads/AeroConf_2023___Contact_Multigraph_Routing-20230221.pdf). 參考重點：contact plan 的產生與散布，以及以 contact 為基礎的路由。
6. NASA, [HDTN Software Requirements Specification](https://ntrs.nasa.gov/api/citations/20240011318/downloads/TM-20240011318.pdf). 參考重點：動態計算或預先計算路由、contact plan 變更與路由重算。
7. NASA, [HDTN: A High-Rate Delay Tolerant Networking Implementation](https://ntrs.nasa.gov/api/citations/20220019062/downloads/HDTNSimSPACOMMApril2023_Italy.pdf). 參考重點：router、scheduler、storage 與 egress 的實作分工。
8. T. Alhajj and V. Corlay, [Improved Contact Graph Routing in Delay Tolerant Networks with Capacity and Buffer Constraints](https://arxiv.org/html/2410.15546). 僅用作 2024 年相關研究比較，不作為標準或官方架構依據。

## 13. 尚待與指導老師確認

1. 第一階段是否正式採用「所有待處理 bundle 在規劃前已知」的批次規劃，或改為中央端逐筆收到請求後的線上規劃。
2. bundle 固定處理順序由何種規則決定，例如到達順序、優先權或 deadline。
3. 是否把控制指令必定及時送達列為範圍假設，將控制平面延遲留作未來工作。
4. 第一階段是否維持 aggregate quota，將 transmission calendar 明確列為下一版本擴充。
