# Validation case catalog v01

資料量 MB、時間秒、rate MB/s。所有案例 Δ=1；T 各表列出。背景曲線每列 (t0,t1,y0,y1) 表示一段線性占用；同一曲線的接點不重複計數。既有曲線是 query snapshot，未列曲線的 node 初始為 0。

Oracle 沒有將這些背景曲線當成新的決策。walkthrough 第二包繼承第一包的完整預約，沒有 reset。完整數值由 oracle_results.json 自動抽取。

## 01_unique

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | B | 0 | 1 | 4 | 0 | 4 |
| b | B | D | 2 | 3 | 4 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| B | 4 |
| D | 4 |

初始背景占用為 0。

### bundle oracle 的所有可行格點排程

| Contact/start sequence | Arrival |
| --- | --- |
| [['a', '0'], ['b', '2']] | 3 |

## 02_multiple

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | B | 0 | 1 | 4 | 0 | 4 |
| b | B | D | 2 | 3 | 4 | 0 | 4 |
| c | A | D | 4 | 5 | 4 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| B | 4 |
| D | 4 |

初始背景占用為 0。

### bundle oracle 的所有可行格點排程

| Contact/start sequence | Arrival |
| --- | --- |
| [['a', '0'], ['b', '2']] | 3 |
| [['c', '4']] | 5 |

## 03_no_route

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | B | 0 | 1 | 4 | 0 | 4 |
| b | B | D | 2 | 3 | 4 | 0 | 3 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| B | 4 |
| D | 4 |

初始背景占用為 0。

### bundle oracle 的所有可行格點排程

沒有可行格點排程；拒絕 witness 見原始 JSON。

## 04_late_label

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | B | 1 | 8 | 4 | 0 | 4 |
| b | B | D | 9 | 10 | 4 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 1 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| B | 4 |
| D | 4 |

| Node | Curve ID | Segments (t0,t1,y0,y1) |
| --- | --- | --- |
| B | 0 | ('2', '3', '0', '4'); ('3', '6', '4', '4'); ('6', '7', '4', '0') |

### bundle oracle 的所有可行格點排程

| Contact/start sequence | Arrival |
| --- | --- |
| [['a', '6'], ['b', '9']] | 10 |
| [['a', '7'], ['b', '9']] | 10 |

## 05_prunable

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | B | 0 | 3 | 4 | 0 | 4 |
| b | B | D | 4 | 5 | 4 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| B | 4 |
| D | 4 |

初始背景占用為 0。

### bundle oracle 的所有可行格點排程

| Contact/start sequence | Arrival |
| --- | --- |
| [['a', '0'], ['b', '4']] | 5 |
| [['a', '1'], ['b', '4']] | 5 |
| [['a', '2'], ['b', '4']] | 5 |

## 06_sequential_walkthrough

Δ=1，T=12。

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

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle1 | X | D | 0 | 4 |
| bundle2 | A | D | 1 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| B | 4 |
| C | 4 |
| D | 4 |
| X | 4 |

初始背景占用為 0。

### bundle1 oracle 的所有可行格點排程

| Contact/start sequence | Arrival |
| --- | --- |
| [['c1', '2'], ['c2', '6']] | 8 |
| [['c1', '2'], ['c5', '10']] | 12 |

### bundle2 oracle 的所有可行格點排程

| Contact/start sequence | Arrival |
| --- | --- |
| [['c4', '7'], ['c5', '10']] | 12 |
| [['c4', '8'], ['c5', '10']] | 12 |

## 07_finish_at_end_nonzero_delay

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | D | 0 | 1 | 4 | 2 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| D | 4 |

初始背景占用為 0。

### bundle oracle 的所有可行格點排程

| Contact/start sequence | Arrival |
| --- | --- |
| [['a', '0']] | 3 |

## 08_receive_overflow

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | D | 0 | 1 | 4 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| D | 4 |

| Node | Curve ID | Segments (t0,t1,y0,y1) |
| --- | --- | --- |
| D | 0 | ('0', '2', '1', '1') |

### bundle oracle 的所有可行格點排程

沒有可行格點排程；拒絕 witness 見原始 JSON。

## 09_sender_drain_overflow

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | D | 0 | 2 | 2 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| D | 4 |

| Node | Curve ID | Segments (t0,t1,y0,y1) |
| --- | --- | --- |
| A | 0 | ('0', '1', '0', '3'); ('1', '2', '3', '0') |

### bundle oracle 的所有可行格點排程

沒有可行格點排程；拒絕 witness 見原始 JSON。

## 10_source_equals_destination

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | A | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |

初始背景占用為 0。

### bundle oracle 的所有可行格點排程

| Contact/start sequence | Arrival |
| --- | --- |
| [] | 0 |

## 11_source_full

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | D | 0 | 1 | 4 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| D | 4 |

| Node | Curve ID | Segments (t0,t1,y0,y1) |
| --- | --- | --- |
| A | 0 | ('0', '2', '1', '1') |

### bundle oracle 的所有可行格點排程

沒有可行格點排程；拒絕 witness 見原始 JSON。

## 12_cycle_needed

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | B | 0 | 1 | 4 | 0 | 4 |
| b | B | A | 3 | 4 | 4 | 0 | 4 |
| c | A | D | 5 | 6 | 4 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| B | 4 |
| D | 4 |

| Node | Curve ID | Segments (t0,t1,y0,y1) |
| --- | --- | --- |
| A | 0 | ('1', '2', '0', '4'); ('2', '3', '4', '0') |

### bundle oracle 的所有可行格點排程

| Contact/start sequence | Arrival |
| --- | --- |
| [['a', '0'], ['b', '3'], ['c', '5']] | 6 |

## 13_quota_reuse

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | B | 0 | 6 | 4 | 0 | 4 |
| b | B | A | 2 | 3 | 4 | 0 | 4 |
| d | B | D | 6 | 7 | 4 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| B | 4 |
| D | 4 |

| Node | Curve ID | Segments (t0,t1,y0,y1) |
| --- | --- | --- |
| A | 0 | ('0', '1', '0', '4'); ('1', '2', '4', '0') |
| B | 0 | ('3', '4', '0', '4'); ('4', '5', '4', '0') |

### bundle oracle 的所有可行格點排程

沒有可行格點排程；拒絕 witness 見原始 JSON。

## 14_destination_event_peak

Δ=1，T=12。

| Contact | From | To | Start | End | Rate | Propagation | Quota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | A | D | 0 | 1 | 4 | 0 | 4 |

| Bundle | Source | Destination | Generation | Size |
| --- | --- | --- | --- | --- |
| bundle | A | D | 0 | 4 |

| Node | Buffer |
| --- | --- |
| A | 4 |
| D | 4 |

| Node | Curve ID | Segments (t0,t1,y0,y1) |
| --- | --- | --- |
| D | 0 | ('1', '1', '1', '1') |

### bundle oracle 的所有可行格點排程

沒有可行格點排程；拒絕 witness 見原始 JSON。