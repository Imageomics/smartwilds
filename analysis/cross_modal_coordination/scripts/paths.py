"""
paths.py — portable path resolution for the cross-modal coordination scripts.

The analysis originally ran from a fixed location on the project's HPC
storage. This module replaces those hardcoded roots so
the scripts run from a checkout anywhere.

Resolution order for every path: environment variable, then a repo-relative
default. Nothing here requires the original cluster layout.

    SMARTWILDS_ROOT          repo root (default: this file's grandparent)
    SMARTWILDS_DATA          shipped derived data      (default: <root>/data)
    SMARTWILDS_PRIMITIVES    Exp-1 workload primitives (default: <data>/primitives)
    SMARTWILDS_TIMESTAMPS    per-modality event tables (default: <data>/timestamps)
    SMARTWILDS_INDEPENDENCE  Exp-2 independence bounds (default: <data>/independence)
    SMARTWILDS_RESULTS       output directory          (default: <root>/results)

Only PRIMITIVES is shipped in the repo. TIMESTAMPS and INDEPENDENCE are
derived from the field archive and are not redistributable; see data/README.md.
"""

from __future__ import annotations

import os
from pathlib import Path


def _resolve(env_var: str, default: Path) -> Path:
    value = os.environ.get(env_var)
    return Path(value).expanduser().resolve() if value else default


REPO_ROOT: Path = _resolve("SMARTWILDS_ROOT", Path(__file__).resolve().parents[1])

DATA_DIR: Path = _resolve("SMARTWILDS_DATA", REPO_ROOT / "data")
PRIMITIVES_DIR: Path = _resolve("SMARTWILDS_PRIMITIVES", DATA_DIR / "primitives")
TIMESTAMPS_DIR: Path = _resolve("SMARTWILDS_TIMESTAMPS", DATA_DIR / "timestamps")
INDEPENDENCE_DIR: Path = _resolve("SMARTWILDS_INDEPENDENCE", DATA_DIR / "independence")
RESULTS_DIR: Path = _resolve("SMARTWILDS_RESULTS", REPO_ROOT / "results")

# Retained for scripts that still express sub-paths relative to a single root.
BASE_DIR: Path = REPO_ROOT


def require(path: Path, what: str, how: str) -> Path:
    """Fail with an actionable message rather than a bare FileNotFoundError."""
    if not path.exists():
        raise SystemExit(
            f"\nMissing {what}: {path}\n"
            f"{how}\n"
            f"Override the location with an environment variable if it lives "
            f"elsewhere -- see scripts/paths.py.\n"
        )
    return path
