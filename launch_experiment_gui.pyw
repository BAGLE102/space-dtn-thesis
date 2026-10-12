# Windows 雙擊入口：設定專案匯入路徑，再啟動 GUI；不自行實作搜尋。
"""Double-click launcher; can also run with python launch_experiment_gui.pyw."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.experiments.gui import main

if __name__ == '__main__':
    raise SystemExit(main())
