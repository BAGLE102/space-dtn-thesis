#!/usr/bin/env bash
# 實驗 A → 實驗 B → 報表。可重複執行，已完成的部分會略過。
set -e
python3 run_validation.py
python3 run_performance.py
python3 make_report.py
