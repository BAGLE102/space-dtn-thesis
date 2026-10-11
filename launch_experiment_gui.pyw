"""Double-click launcher; can also run with python launch_experiment_gui.pyw."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.experiments.gui import main

if __name__ == '__main__':
    raise SystemExit(main())
