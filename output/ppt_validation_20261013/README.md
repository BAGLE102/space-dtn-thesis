# 第一輪PPT小案例驗證

詳細定義、失敗原因與重現方式見 [驗證紀錄](../../docs/ppt_validation_experiments_20261013.md)。

- [PPT兩包結果](ppt_2bundles/report.md)：抵達8、12秒，符合PPT。
- [八節點五包結果](8nodes_5bundles/report.md)：前4包抵達12、12、13、20秒，第5包無解。
- [五包各跳時間](8nodes_5bundles/schedule.csv)。
- [五包Buffer曲線](8nodes_5bundles/figures/buffer_occupancy.png)。
- [五包contact預約](8nodes_5bundles/figures/contact_reservations.png)。

7次單包查詢的可行性／最早抵達時間皆與完整列舉一致。這是有限格點、DAG、固定規劃順序及無支配刪除的驗證結果，不是效能比較或一般證明。
