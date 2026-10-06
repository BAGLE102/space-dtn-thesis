# Algorithm walkthrough v01



本次驗證固定 v04，不修改規則。所有數字來自 `output/validation/walkthrough_trace.json`；來源程式 `src/validation/build_walkthrough.py`。

Δ=1 秒、T=12 秒；MB、MB/s。先前五-contact 例子擴為本次固定五節點八-contact 例子，並非改演算法。

## Nodes

X、A、B、C、D。

## Contacts

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c1 | X | B | 2 | 3 | 4 | 0 | 4 |
| c2 | B | D | 6 | 7 | 4 | 1 | 4 |
| c3 | A | B | 1 | 2 | 4 | 0 | 4 |
| c4 | A | B | 7 | 9 | 4 | 0 | 8 |
| c5 | B | D | 10 | 11 | 4 | 1 | 4 |
| c6 | A | C | 1 | 2 | 4 | 1 | 4 |
| c7 | C | D | 4 | 5 | 4 | 0 | 2 |
| c8 | C | D | 2 | 3 | 4 | 0 | 4 |

## Node Buffer

| Node | Buffer Capacity |
| --- | --- |
| A | 4 |
| B | 4 |
| C | 4 |
| D | 4 |
| X | 4 |

## Bundles

| Bundle | Source | Destination | Generation Time | Size |
| --- | --- | --- | --- | --- |
| bundle1 | X | D | 0 | 4 |
| bundle2 | A | D | 1 | 4 |

c4 有兩個 start choices，會產生相同 contact 用量但不同 arrival 的 labels；c7 展示 quota failure、c8 展示 temporal failure。c2/c5 的 propagation=1，使發送完成與完整到達可區分。

## Trace 規則

依 contact ID 與 start time 遞增展開；heap key=(arrival,creation ID)。POP 是取出 label；EXTEND 的 Queue Before 是該次嘗試前的剩餘佇列。SKIP 表示短路後未執行，不偽稱 PASS。先檢 quota 再列舉時間，遵照 v04 pseudocode。每個嘗試各有一列與解釋。

## bundle1 完整逐步執行

初始化：L0=(X,0,{0})

| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | L0 | L0 | — | — | — | — | — | — | 取出並展開；Q after=[∅] |

Step 0：此 label 的 arrival 在佇列最早；節點本身不被永久 settled。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ∅ | L0 | c1 | PASS: s=2≥max(0,2); f=3≤3; h=2, a′=3≤12 | PASS: 0+4≤4 | PASS: sender峰值=4@0; receiver峰值=4@3；兩端上限均4 | L1=(B,3,{c1:4}) | 無 label 可取代；保留 | 加入 Q；Q after=[L1] |

Step 1：全部 extension checks 通過；提交全域預約尚未發生。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | L1 | L1 | — | — | — | — | — | — | 取出並展開；Q after=[∅] |

Step 2：此 label 的 arrival 在佇列最早；節點本身不被永久 settled。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | ∅ | L1 | c2 | PASS: s=6≥max(3,6); f=7≤7; h=7, a′=8≤12 | PASS: 0+4≤4 | PASS: sender峰值=4@3; receiver峰值=4@8；兩端上限均4 | L2=(D,8,{c1:4,c2:4}) | 無 label 可取代；保留 | 加入 Q；Q after=[L2] |

Step 3：全部 extension checks 通過；提交全域預約尚未發生。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | L2 | L1 | c5 | PASS: s=10≥max(3,10); f=11≤11; h=11, a′=12≤12 | PASS: 0+4≤4 | PASS: sender峰值=4@3; receiver峰值=4@12；兩端上限均4 | L3=(D,12,{c1:4,c5:4}) | 無 label 可取代；保留 | 加入 Q；Q after=[L2, L3] |

Step 4：全部 extension checks 通過；提交全域預約尚未發生。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | L2, L3 | L2 | — | — | — | — | — | — | 回傳目的地路徑；Q after=[L3] |

Step 5：有效 destination label 被取出才終止，不在首次產生時終止。



### 全部 label 定義

| ID | State | Active | Processed |
| --- | --- | --- | --- |
| L0 | L0=(X,0,{0}) | True | True |
| L1 | L1=(B,3,{c1:4}) | True | True |
| L2 | L2=(D,8,{c1:4,c2:4}) | True | False |
| L3 | L3=(D,12,{c1:4,c5:4}) | True | False |

### Selected Route

c1 → c2

### Arrival Time

8 秒

### Contact Usage

| Contact | Start | Finish | Complete arrival |
| --- | --- | --- | --- |
| c1 | 2 | 3 | 3 |
| c2 | 6 | 7 | 8 |

### Quota Update

| Contact | Before | Used | After |
| --- | --- | --- | --- |
| c1 | 4 | 4 | 0 |
| c2 | 4 | 4 | 0 |
| c3 | 4 | 0 | 4 |
| c4 | 8 | 0 | 8 |
| c5 | 4 | 0 | 4 |
| c6 | 4 | 0 | 4 |
| c7 | 2 | 0 | 2 |
| c8 | 4 | 0 | 4 |

### Buffer Reservation / Occupancy

| Node | Time Interval | Bundle | Occupied Buffer |
| --- | --- | --- | --- |
| X | [0,2] | bundle1 | 4 → 4 MB（線性） |
| X | [2,3] | bundle1 | 4 → 0 MB（線性） |
| B | [2,3] | bundle1 | 0 → 4 MB（線性） |
| B | [3,6] | bundle1 | 4 → 4 MB（線性） |
| B | [6,7] | bundle1 | 4 → 0 MB（線性） |
| D | [7,8] | bundle1 | 0 → 4 MB（線性） |

同一條曲線相鄰段的共用端點只計一次。Source 從 generation 占 S；destination 在完整交付前檢查峰值、交付後釋放。

## bundle2 完整逐步執行

初始化：L0=(A,1,{0})

| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | L0 | L0 | — | — | — | — | — | — | 取出並展開；Q after=[∅] |

Step 0：此 label 的 arrival 在佇列最早；節點本身不被永久 settled。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ∅ | L0 | c3 | PASS: s=1≥max(1,1); f=2≤2; h=1, a′=2≤12 | PASS: 0+4≤4 | PASS: sender峰值=4@1; receiver峰值=4@2；兩端上限均4 | L1=(B,2,{c3:4}) | 無 label 可取代；保留 | 加入 Q；Q after=[L1] |

Step 1：全部 extension checks 通過；提交全域預約尚未發生。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | L1 | L0 | c4 | PASS: s=7≥max(1,7); f=8≤9; h=7, a′=8≤12 | PASS: 0+4≤8 | PASS: sender峰值=4@1; receiver峰值=4@8；兩端上限均4 | L2=(B,8,{c4:4}) | 無 label 可取代；保留 | 加入 Q；Q after=[L1, L2] |

Step 2：全部 extension checks 通過；提交全域預約尚未發生。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | L1, L2 | L0 | c4 | PASS: s=8≥max(1,7); f=9≤9; h=8, a′=9≤12 | PASS: 0+4≤8 | PASS: sender峰值=4@1; receiver峰值=4@9；兩端上限均4 | L3=(B,9,{c4:4}) | 被 L2 取代 | 不入列；Q after=[L1, L2] |

Step 3：同節點的保留 label 不晚到、可等待且 U 不更多。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | L1, L2 | L0 | c6 | PASS: s=1≥max(1,1); f=2≤2; h=2, a′=3≤12 | PASS: 0+4≤4 | PASS: sender峰值=4@1; receiver峰值=4@3；兩端上限均4 | L4=(C,3,{c6:4}) | 無 label 可取代；保留 | 加入 Q；Q after=[L1, L4, L2] |

Step 4：全部 extension checks 通過；提交全域預約尚未發生。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | L1, L4, L2 | L1 | — | — | — | — | — | — | 取出並展開；Q after=[L4, L2] |

Step 5：此 label 的 arrival 在佇列最早；節點本身不被永久 settled。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | L4, L2 | L1 | c2 | SKIP | FAIL: 0+4>0 | SKIP | — | — | 不產生 label；Q after=[L4, L2] |

Step 6：前綴用量加整包大小超過 snapshot quota。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | L4, L2 | L1 | c5 | PASS: s=10≥max(2,10); f=11≤11; h=11, a′=12≤12 | PASS: 0+4≤4 | FAIL: sender峰值=8@3; receiver峰值=4@12；兩端上限均4 | — | — | 拒絕；Q after=[L4, L2] |

Step 7：失敗類別 BUFFER；不建立 label。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | L4, L2 | L4 | — | — | — | — | — | — | 取出並展開；Q after=[L2] |

Step 8：此 label 的 arrival 在佇列最早；節點本身不被永久 settled。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | L2 | L4 | c7 | SKIP | FAIL: 0+4>2 | SKIP | — | — | 不產生 label；Q after=[L2] |

Step 9：前綴用量加整包大小超過 snapshot quota。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | L2 | L4 | c8 | FAIL: earliest=3>latest=2 | PASS | SKIP | — | — | 沒有候選 start；Q after=[L2] |

Step 10：即使 quota 足夠，也無法在 contact 結束前傳完。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | L2 | L2 | — | — | — | — | — | — | 取出並展開；Q after=[∅] |

Step 11：此 label 的 arrival 在佇列最早；節點本身不被永久 settled。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | ∅ | L2 | c2 | SKIP | FAIL: 0+4>0 | SKIP | — | — | 不產生 label；Q after=[∅] |

Step 12：前綴用量加整包大小超過 snapshot quota。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | ∅ | L2 | c5 | PASS: s=10≥max(8,10); f=11≤11; h=11, a′=12≤12 | PASS: 0+4≤4 | PASS: sender峰值=4@8; receiver峰值=4@12；兩端上限均4 | L5=(D,12,{c4:4,c5:4}) | 無 label 可取代；保留 | 加入 Q；Q after=[L5] |

Step 13：全部 extension checks 通過；提交全域預約尚未發生。



| Step | Queue Before | Selected Label | Candidate Contact | Temporal | Quota | Buffer | New Label | Dominance | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | L5 | L5 | — | — | — | — | — | — | 回傳目的地路徑；Q after=[∅] |

Step 14：有效 destination label 被取出才終止，不在首次產生時終止。



### 全部 label 定義

| ID | State | Active | Processed |
| --- | --- | --- | --- |
| L0 | L0=(A,1,{0}) | True | True |
| L1 | L1=(B,2,{c3:4}) | True | True |
| L2 | L2=(B,8,{c4:4}) | True | True |
| L3 | L3=(B,9,{c4:4}) | False | False |
| L4 | L4=(C,3,{c6:4}) | True | True |
| L5 | L5=(D,12,{c4:4,c5:4}) | True | False |

### Selected Route

c4 → c5

### Arrival Time

12 秒

### Contact Usage

| Contact | Start | Finish | Complete arrival |
| --- | --- | --- | --- |
| c4 | 7 | 8 | 8 |
| c5 | 10 | 11 | 12 |

### Quota Update

| Contact | Before | Used | After |
| --- | --- | --- | --- |
| c1 | 0 | 0 | 0 |
| c2 | 0 | 0 | 0 |
| c3 | 4 | 0 | 4 |
| c4 | 8 | 4 | 4 |
| c5 | 4 | 4 | 0 |
| c6 | 4 | 0 | 4 |
| c7 | 2 | 0 | 2 |
| c8 | 4 | 0 | 4 |

### Buffer Reservation / Occupancy

| Node | Time Interval | Bundle | Occupied Buffer |
| --- | --- | --- | --- |
| B | [7,8] | bundle2 | 0 → 4 MB（線性） |
| B | [8,10] | bundle2 | 4 → 4 MB（線性） |
| B | [10,11] | bundle2 | 4 → 0 MB（線性） |
| D | [11,12] | bundle2 | 0 → 4 MB（線性） |
| A | [1,7] | bundle2 | 4 → 4 MB（線性） |
| A | [7,8] | bundle2 | 4 → 0 MB（線性） |

同一條曲線相鄰段的共用端點只計一次。Source 從 generation 占 S；destination 在完整交付前檢查峰值、交付後釋放。

## 驗證狀態

本文件先由 frozen proposed implementation 產生。是否與 independent oracle 一致，另見 oracle_validation_v01.md；本 trace 本身不是獨立正確性證據。