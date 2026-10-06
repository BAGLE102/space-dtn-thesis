# 建議延伸：以 buffer safe intervals 為狀態的整包 earliest-arrival 搜尋

日期：2026-10-04。這是待討論的研究提案，沒有取代 [research_scope_v03.md](research_scope_v03.md) 的已確認範圍，也沒有完成實作或效能驗證。

標記：[C] 模型推導；[D] 本研究提案；[E] 尚待證明／查證。外部文獻以作者、章節及連結標明，避免與原 Paper A/B 混淆。

## 1. 給老師的一段話 [D]

本研究探討已知 contact plan 與既有資源預約下，不可分割 bundle 的 earliest-arrival routing。擬以節點的 buffer safe intervals 建立搜尋狀態，在搜尋時直接判定整段傳輸與逐 byte buffer 占用的可行性，避免為每次查詢預先展開全部 contact 切割結果。研究目標是在完整接收後才能轉送的條件下，證明搜尋的正確性，並評估其查詢時間與記憶體成本。

這段話是研究目標；完成證明與實驗前，不能改寫成「已提出更快且最優的新演算法」。

## 2. 文獻已做到哪裡

- Alhajj 與 Corlay（2024），§IV：利用 contact splitting、buffer forecast 與 edge pruning 限制可搜尋解，已包含 S/r 傳輸時間。§VII 分開測試容量與 buffer，後者令速率無限大。[原文](https://arxiv.org/html/2410.15546v1)
- 原文 §V 的比較基準接收時先預留整包、發送時逐步釋放；這一段不能直接當成 §IV 提案的完整逐 byte 實作規格。[同一原文](https://arxiv.org/html/2410.15546v1)
- Phillips 與 Likhachev（2011）的 SIPP 已使用「位置＋安全時間區間」壓縮動態路徑搜尋狀態；此概念本身不是本研究首創。[作者論文](https://www.cs.cmu.edu/~maxim/files/sipp_icra11.pdf)
- NASA 的 CMR 已研究以實體節點 multigraph 替代 contact graph；單純更換圖表示法不能直接主張新穎性。[NASA 原始來源](https://ntrs.nasa.gov/citations/20230002637)

本次定向檢索未確認完全相同的 DTN 演算法，但這不構成「首次提出」的證據。需進一步沿 SIPP、CMR、buffer-aware temporal routing 的引用鏈查核。[E]

## 3. 必須明講的 scope 調整 [C/D]

目前固定 M_v、無背景占用、單 bundle、store-and-forward 的模型，buffer 峰值就是 S；因此 M_v≥S 後可以任意等待，單 label 已足夠。維持這些條件，不能用多 labels 包裝新的必要性。

建議保留目前版本作 baseline，將原定後續的 Known transmission calendar 推進為主研究版本，並增加一致的既有 buffer 占用曲線 O_v(t)：

| 項目 | 現有 baseline | 建議主研究版本 |
|---|---|---|
| 查詢 | 一次一個 bundle | 仍一次一個 bundle |
| 既有工作 | 無背景 buffer | 已排定且固定，不重新最佳化 |
| Contact | aggregate quota | 可用傳輸時段 calendar |
| Buffer | 固定 M_v | 固定 M_v，加上已知 O_v(t) |
| 目標 | earliest whole-bundle arrival | 相同，不加入人工 cost |
| 傳輸 | 不分割、不暫停、每跳單 contact | 相同 |

「有既有預約」不等於「同時最佳化多 bundle」。可先讀取固定資源快照，求一個新 bundle；日後才測依序 admission。後者不保證全體流量的聯合最優。

calendar 與 buffer 曲線必須由相同既有排程產生或經一致性檢查。單一 aggregate quota 無法推回忙碌時段。若另外保留獨立 quota 上限，需另證明重複使用 contact 的資源計數與 dominance，不能直接套下面的精簡 state。

## 4. 方法差異：搜尋狀態與 transition [D]

令可用 buffer 為 F_v(t)=M_v−O_v(t)，定義可完整存放本 bundle 的 maximal intervals：

    I_v,k ⊆ {t : F_v(t) ≥ S}

候選 label：

    L = (v, k, a)
    v：目前節點
    k：完整接收時所在的 buffer safe interval
    a：整包到達時間

搜尋在原 contacts 與 calendar 上按需產生 successors，不必先建立所有 bundle-specific split contacts。允許同一節點不同 intervals 各保留 label；同一 interval 則爭取只留最早到達者。

對 contact c=(u,v,start,end,r,δ)，從完整到達 u 的時刻 a 延伸，令 x=S/r，尋找 start≤s、a≤s、s+x≤end，且 [s,s+x) 全落在可用鏈路時段。

還須同時驗證：

1. sender 在 [a,s] 等待的 S bytes，以及 [s,s+x] 逐步釋放量，皆不超過 F_u(t)。
2. receiver 從 h=s+δ 起的接收量 min(S,max(0,r(t−h))) 皆不超過 F_v(t)。
3. 完整到達 a′=s+x+δ 落在某個目標 safe interval；每個可達目標 interval 都要考慮，不能只取該節點全域最早 a′。

**Safe interval 限制整包可停留的時段，不要求整個接收／發送過程都在同一個 safe interval 內。** 部分 bytes 可能在 F_v(t)<S 時安全接收或釋放；全部禁止會過度保守。

若 O_v(t) 為分段線性，應解分段線性可行性條件，或導出等價的可行 departure intervals。只檢查原始 calendar 的事件時間、或用固定秒數採樣，都尚不足以保證 exactness；邊界也可能由 S/r、δ 與曲線交點產生。

## 5. Dominance 的論證骨架與限制 [C/E]

同一 v、同一 safe interval 內，若 a₁≤a₂，較早抵達者可持有 S bytes 等至 a₂，再照抄晚到者的所有後續動作。因此在以下條件下，較早 label 可取代較晚者：

- 已有預約在本次搜尋中固定；候選分支不互相扣資源。
- 完整接收後才能轉送，送出的 bytes 即釋放，不保留 custody/retransmission copies。
- 前綴在到達目前節點時已無尚待占用的傳輸／buffer 資源；傳播中資料不占已釋放的 sender buffer。
- 不額外要求 simple path、hop budget、獨立累積 quota 或其他依路徑歷史而定的限制。若要求，需補 state 與證明。
- 所有等待、接收、發送曲線已驗證；區間端點採一致的事件前後順序。

這提供 dominance 的可行性理由；完整演算法仍須證明 successor enumeration 不漏解、連續時間最小 departure 存在或端點可處理，以及 label-setting 的終止與最優性。不能直接繼承機器人 SIPP 的全部定理。

## 6. 兩個先做的小例子 [D]

### 例一：為什麼同一節點可能需要不同 interval labels

令 S=4 MB、δ=0、M_B=4 MB，B 在 [4,6) 有 1 MB 背景占用，其餘為零。

| Contact | 可用時段（秒） | Rate |
|---|---|---|
| A→B，早班 | [2,3) | 4 MB/s |
| A→B，晚班 | [6,7) | 4 MB/s |
| B→D | [8,9) | 4 MB/s |

源點在 t=2 已有 bundle，其他資源充足。早班 t=3 到 B，但等至 t=8 會在 [4,6) 超量；晚班 t=7 到 B，可 t=8–9 送到 D。沒有其他 contacts 可離開 B。只留 B 的全域最早到達會錯刪可行解；保留不同 safe intervals 的 labels 可區分兩者。

### 例二：逐 byte 接收能否減少過度保守的拒絕

S=4 MB，B 上限 4 MB，背景占用 O_B(t)=max(0,2−t) MB（t≥0）。A→B 唯一可用時段 [0,4)，rate=1 MB/s、δ=0。

從 t=0 接收，新增占用為 t MB（0≤t≤4）。因此 0≤t≤2 的總占用為 2 MB；2≤t≤4 的總占用為 t MB，皆≤4 MB。整包 t=4 收完，之後有可用 B→D contact。

若 t=0 就要求 B 預留全部 4 MB，會因背景 2 MB 而拒絕；等到 t=2 才開始又無法在 t=4 前送完。這是兩種占用語意的可行域差異，**不是已證明 2024 作者程式會錯誤的反例**。假設背景傳出與新接收使用可同時運作的資源，沒有未建模的 radio contention。

以上是手工構造與代數核算，尚非模擬實驗結果。

## 7. 可以成立的貢獻與不能先宣稱的結果

| 候選貢獻 [D] | 需要交付的證據 [E] |
|---|---|
| 對逐 byte occupancy 的精確 transition | sender/receiver 曲線、傳播延遲與 contact calendar 的聯合可行性證明 |
| interval labels 的安全壓縮 | dominance、完備性、最優性及明確適用條件 |
| lazy generation 減少建圖成本 | 相同語意下的建圖＋搜尋總時間、記憶體、生成狀態數 |
| 有限 rate 與有限 buffer 的聯合作用 | 不只分開測試，量化瓶頸交互影響 |

只有改名、改成 Dijkstra/A* 或同樣方法換語言，不足以作上述貢獻。也不能預先宣稱本法一定更快：interval 數量與 transition 判定成本可能抵消省下的建圖成本。

## 8. 實驗必須分開「演算法」與「模型」效果 [D]

1. **同模型方法比較**：對相同資源快照與相同 occupancy 語意，比較 explicit interval/split graph 與 proposed lazy search；earliest arrival 應一致，主要比較計算成本。若重作 2024 方法但變更其語意，須標示 adapted baseline。
2. **占用語意消融**：整包提前預留 vs 逐 byte 接收／釋放；比較可行 query 比例與共同可行 queries 的 arrival time。可行域放寬的效果不能算成搜尋演算法本身變快或更優。
3. **正確性 oracle**：小型網路採 route 枚舉配合精確 schedule feasibility，或經證明等價的事件模型；任意固定時間格點只能檢查離散模型，不能證明連續時間最優。

改變：contact 數、既有預約事件數、bundle size、S/(rate×contact duration)、buffer/S、背景負載、異質 rate。測查詢＋必要前處理總時間、峰值記憶體、labels／transitions、可行率、相對 oracle 的 arrival error；計算時間報平均與 P95，另保存 min/max/std。不得把 network delivery delay 當成 CPU runtime。

先固定快照比較。若加依序 admission，固定 bundle 次序，說明不同路由決策會改變後續資源狀態；不能當作同一快照的查詢速度比較。

## 9. 最小可行推進順序 [D]

1. 保留 v03 baseline，不製造額外 cost。
2. 決定是否採「已知既有預約」的主研究範圍；這是本提案唯一重要的背景擴充。
3. 先完成上述兩個例子的圖、排程與 buffer 曲線，明確定義資源端點和 radio 假設。
4. 寫精確 extension oracle 與 interval dominance 的證明，再定 pseudocode。
5. 小型 exact oracle 通過後，再做大規模 runtime／memory 實驗。

暫定題目：**考慮逐位元組緩衝占用之非分割 Bundle 安全區間路由**。

英文工作題目：**Safe-Interval Earliest-Arrival Routing for Non-Fragmented Bundles with Byte-Level Buffer Occupancy**。

這是可執行且值得驗證的方向，不是已確立的新穎性結論；若無法證明精確 transition，應縮小假設，不宜先畫完整演算法流程宣稱成立。
