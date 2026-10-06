# Transmission calendar gap v01

本階段不實作 calendar、不修改 v04；以下是模型邊界與候選變更。

## Why Aggregate Quota Is Insufficient — CE-CALENDAR-01
Contact A→D：window=[0,6)、r=1 MB/s、δ=0。既有鏈路占用 [1,2)、[3,4)、[5,6)，故剩餘總量 R=3 MB。新 bundle S=2 MB、g=0；node buffer 足夠。

Aggregate 檢查 R≥S、s=0、f=2≤6 都會通過。但剩餘區段是 [0,1)、[2,3)、[4,5)，每段僅能傳 1 MB；不存在連續 2 秒可用時段。因此不可中斷整包無法排入。

這是 aggregate model 對實際 calendar feasibility 不充分的反例，不是同模型 oracle mismatch；oracle 也刻意沒有 busy-interval 檢查。

## What Transmission Calendar Adds
時間位置與連續空檔資訊，要求 [s,s+S/r)∩Ω_c=∅。R 只限制總量，Ω 才指出那些量在哪些時間可用。Quota 與 calendar 若同時存在，必須定義是否是同一資源的兩種表示，或另有獨立 admission limit。

## Required State（候選）
固定 query context 增加 Ω_c（每 contact 的已接受 transmission intervals）；若多 contacts 共用 radio，需另外建資源群組。是否仍需 U 取決於獨立 quota 是否保留；不能先刪除。路徑接受後才更新 Ω，候選分支不互相提交。

## Required Changes to Extension（候選）
除了 quota/window/buffer，要求連續傳送區間不重疊。尋找可用區段後，仍須聯合檢查 sender/receiver buffer；不能只取第一個 free slot，因稍後 arrival 可能有不同可行後續。這與 continuous-time candidate generation 是兩個相關但不同的問題。

## Required Changes to Dominance（候選）
如果 Ω 是固定快照、候選前綴已完成所有傳輸、無額外依路徑歷史的 radio state，早到且可等待的 label 仍可照抄晚到者的 suffix calendar。原 continuation-copy 證明有機會保留，但必須正式確認完整 state、quota 與可用動作相同；不能直接聲稱 calendar 一加上便自動正確。

## Relation to the 2024 paper
該文 §IV-B 在選定路由後移除已使用的 contact 時段，並更新 forecast buffer tables。因此與其比較前，必須對齊預約語意；aggregate-only 的結果不能當成同一問題的優劣證據。[Alhajj & Corlay 原文](https://arxiv.org/html/2410.15546v1)

## 保留的候選修正，未實作
1. 若主張仍是 aggregate model，保留 v04 並明列保證邊界。
2. 若要保證真實 non-preemptive 排程，需增加 Ω 判別式並重新做 walkthrough/oracle。
3. 若要與 2024 比較，先對齊 buffer 占用、鏈路預約、處理次序與相同輸入。

目前沒有將任何一項候選修正套用到演算法。
