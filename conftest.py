"""Test bootstrap.

The library modules under src/ install as top-level imports via
`pip install -e .`, so no test needs a sys.path hack of its own. The two
entry-point scripts (run_eval.py, make_report_plots.py) live at the repo root
and are intentionally not packaged; this makes them importable in tests.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
