from __future__ import annotations

"""Thin compatibility entrypoint for Experiment 5 storage analysis.

The implementation now lives in `src/storage_analysis/` so the analysis uses a
conventional Python package layout.
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from storage_analysis.cli import main


if __name__ == "__main__":
    main()
