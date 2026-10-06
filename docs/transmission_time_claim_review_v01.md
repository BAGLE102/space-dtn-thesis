# Transmission time 研究主張核對 v01

日期：2026-10-04。針對使用者提出「既有方法通常只檢查容量，忽略較大 bundle 的 transmission delay」進行核對。這份記錄區分可以引用的事實與本次推論，不作完整 systematic review。

## 可查證的界線

來源 S：CCSDS 734.3-B-1，*Schedule-Aware Bundle Routing*，July 2019，https://ccsds.org/Pubs/734x3b1.pdf 。

| 階段 | 標準條文 | 核對結果 |
|---|---|---|
| Route computation | §3.2.4.1.1–.2、§3.2.4.2 | BDT 的遞推使用 contact 起始時間、先前 arrival、OWLT / margin，未在此式加入整包 serialization |
| Candidate route evaluation | §3.2.6.3–.7 | 用 EVC/rate 計算 radiation latency，再計算 last-byte arrival / projected bundle arrival |
| Non-fragmentable validation | §3.2.6.9(g) | 排除 RVL<EVC 的 route |

因此，「搜尋階段的 BDT 與整包 PAT 不同」有依據；「完整 SABR 不考慮 transmission delay」不成立。不能由 BDT 直接推論作者假設所有實際 bundles 都很小；它亦可作為 optimistic bound / route enumeration 指標。搜尋與後續驗證必須分開比較。

## 小 bundle 假設的正確表述 [C]

S 小是否能忽略 transmission time，取決於 τ=S/r 和 contact 剩餘時間、相鄰 contact 間距、其他 delay 的相對量級，而不是只看 S 的絕對大小。即使 τ 很小，剛好跨過 contact end 仍會改變可行性。

目前沒有足夠文獻樣本支持「過去通常都假設小 bundle」的統計性說法。若引用某一特定演算法，應逐條指出它的 arrival recurrence 與 validation 流程，不用「通常」取代來源。

## 兩個可使用的構造案例 [D]

### 案例 1：容量足夠但時間窗口不夠

Bundle S=4 MB；contact [0,10)、r=1 MB/s、R=8 MB；bundle 在 8 s 抵達 sender。

- Aggregate quota 通過：8≥4。
- 若立即發送，finish=8+4=12>10。
- 因此不能使用該 contact。

此例只證明「quota-only predicate 不充分」，不證明完整 SABR 或所有 CGR 會錯選。

### 案例 2：BDT 與整包 arrival 的 route 排序不同

Bundle S=4 MB，g=0，buffer 充足，R=Q，所有時間單位秒。

| Contact | Window | Rate MB/s | δ | Q=R MB |
|---|---|---:|---:|---:|
| c1 A→E | [0,20) | 0.5 | 1 | 10 |
| c2 A→B | [0,10) | 4 | 1 | 40 |
| c3 B→E | [0,10) | 4 | 1 | 40 |

本次自行計算：

| Route | 忽略 serialization 的 arrival | 整包 store-and-forward arrival |
|---|---:|---:|
| A→E | 1 | 9 |
| A→B→E | 2 | 4 |

若只保留第一條 BDT route，再做驗證，可能留下較慢但可行的 route。若演算法已列出兩條並按 PAT 選擇，就能選 4 s route。因此實驗必須公開候選 route 數與停止條件；不能將此例當作完整標準必然失敗的證明。

## 更直接的 related-work 風險

外部文獻 C（本次新增，非原來的 Paper A/B）：Tania Alhajj、Vincent Corlay，*Improved Contact Graph Routing in Delay Tolerant Networks with Capacity and Buffer Constraints*，arXiv:2410.15546v1，2024-10-21。
https://arxiv.org/html/2410.15546v1

已核對 §II-C、§III、§IV：該文在搜尋前／中處理容量及 buffer，使用 contact splitting、edge pruning、forecast buffer tables，式 (1) 明列 S/r。這與目前方向高度重疊。[E] 尚未證明它和本次 non-preemption、buffer 占用、propagation 與路徑允許範圍完全等價，也未重現實作；不能斷言已解掉所有版本，但必須優先比較。

## 建議目前的主張 [D]

> 本研究針對單一不可分割、不可中斷且每跳必須在單一 contact 內完成傳輸的 bundle，在 aggregate contact quota 與有限節點 buffer 的模型下，研究如何於路徑搜尋過程中一致處理完整傳輸時間、儲存可行性及必要的延後發送，以求最早整包抵達路徑。

這是目前的 **problem statement**，不是已成立的 novelty claim。「首次納入 transmission time」「首次考慮 buffer」「必須使用多資源 SPPRC」都沒有足夠證據。
