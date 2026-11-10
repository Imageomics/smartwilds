#!/usr/bin/env python3
"""Post-process the predicted feasibility grid into the paper's master table.

Input:  results/predicted_feasibility_grid.csv (raw harness output, 80 rows)
        and, if present, the Exp 3.5 calibration anchor (calibration_gap.json;
        override its location with SMARTWILDS_CALIBRATION_GAP)
Output: <results>/feasibility/master_feasibility.csv

Transforms applied:
  - verdict (feasible/degraded/infeasible) -> label (F/D/I)
  - bottleneck "modality:model" -> categorical binding_constraint per the taxonomy
    {queue_overflow, latency_overrun, model_unsupported, near_saturation, none}
  - keeps p95_latency_ms_predicted (renamed p95_ms)
  - slo_pct: 100.0 for F, 0.0 for I cells with p95=inf, else 100*SLO/p95 (clamped 0..100)
  - total_kj: N/A — predicted grid is utilization-based, not energy-replay-based
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import pandas as pd

# --- portable paths: resolved by scripts/paths.py, overridable via env vars ---
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DATA_DIR, RESULTS_DIR  # noqa: E402

ROOT = Path(__file__).resolve().parent
IN_GRID = ROOT / "results" / "predicted_feasibility_grid.csv"
CALIBRATION_GAP = Path(os.environ.get("SMARTWILDS_CALIBRATION_GAP", DATA_DIR / "paper_results" / "calibration_gap.json"))
OUT_DIR = RESULTS_DIR / "feasibility"
OUT_CSV = OUT_DIR / "master_feasibility.csv"

VERDICT_TO_LABEL = {"feasible": "F", "degraded": "D", "infeasible": "I"}

# Manuscript renumbering (2026-05-01): the manuscript leads with the
# Acoustic→CT case as CS1, so the internal CS1 (CT→Drone) and CS2
# (Acoustic→CT) labels are swapped at the paper-facing layer. Internal labels
# in manifest.json / recipes / traces stay unchanged.
CASE_RENAME = {
    "CS1": "CS2",  # internal CT→Drone (5 s SLO)  → manuscript CS2
    "CS2": "CS1",  # internal Acoustic→CT (2 s SLO) → manuscript CS1
    "CS3": "CS3",
    "CS4": "CS4",
}

# Models known to be explicitly unsupported on a tier per
# model_benchmark_notes.md (no feasible deployment path).
# Note: SAM3 rows kept for completeness, but the prediction model now uses
# yolo_sahi for the drone pipeline — SAM3 is out of scope.
UNSUPPORTED = {
    ("sam3", "pi5_coral"),
    ("sam3", "pi4_cpu"),
    ("bioclip", "pi5_coral"),
    ("yolo_world", "pi5_coral"),
    ("megadetector", "pi5_coral"),
}


def _bottleneck_model(bottleneck: str) -> str:
    if not isinstance(bottleneck, str) or ":" not in bottleneck:
        return ""
    return bottleneck.split(":", 1)[1]


def classify(row: pd.Series) -> str:
    """Map a (verdict, p95, bottleneck, tier) row to a categorical taxonomy."""
    verdict = row["verdict"]
    p95 = row["p95_latency_ms_predicted"]
    slo = row["slo_target_ms"]
    tier = row["tier"]
    model = _bottleneck_model(row.get("bottleneck", ""))

    if verdict == "feasible":
        return "none"

    # Model-level unsupported takes priority over throughput symptoms,
    # because the queue blow-up is a *consequence* of the missing deployment.
    if (model, tier) in UNSUPPORTED:
        return "model_unsupported"

    if not math.isfinite(p95):
        return "queue_overflow"

    if p95 > slo:
        return "latency_overrun"

    if verdict == "degraded":
        return "near_saturation"

    return "other"


def slo_pct(row: pd.Series) -> float:
    p95 = row["p95_latency_ms_predicted"]
    slo = row["slo_target_ms"]
    if not math.isfinite(p95):
        return 0.0
    if p95 <= slo:
        return 100.0
    return max(0.0, 100.0 * slo / p95)


def main() -> None:
    df = pd.read_csv(IN_GRID)
    out = pd.DataFrame({
        "case_study": df["case_study"].map(CASE_RENAME),
        "case_study_internal": df["case_study"],
        "policy": df["policy"],
        "tier": df["tier"],
        "label": df["verdict"].map(VERDICT_TO_LABEL),
        "p95_ms": df["p95_latency_ms_predicted"],
        "slo_target_ms": df["slo_target_ms"],
        "slo_pct": df.apply(slo_pct, axis=1).round(2),
        "total_kj": "N/A",
        "binding_constraint": df.apply(classify, axis=1),
        "bottleneck_raw": df["bottleneck"],
        "utilization_pct_predicted": df["utilization_pct_predicted"].round(2),
        "notes": df["modeling_notes"],
    })

    # Default measured/calibration columns (will be overwritten for the
    # specific cell anchored by Exp 3.5).
    out["measured"] = False
    out["measured_p95_ms"] = ""
    out["calibration_gap_pct"] = ""

    if CALIBRATION_GAP.exists():
        cal = json.loads(CALIBRATION_GAP.read_text())
        # Exp 3.5 records uses internal case_study label; remap to manuscript.
        anchored_case_internal = cal["case_study"]
        anchored_case = CASE_RENAME.get(anchored_case_internal, anchored_case_internal)
        anchored_tier = cal["tier"]
        anchored_policy = cal["policy"]
        anchored_p95 = cal["anchored_system"]["anchored_system_p95_ms"]
        anchored_gap = cal["anchored_system"]["system_p95_gap_pct"]
        mask = (
            (out["case_study"] == anchored_case)
            & (out["tier"] == anchored_tier)
            & (out["policy"] == anchored_policy)
        )
        n_matched = int(mask.sum())
        if n_matched != 1:
            raise RuntimeError(
                f"Expected exactly 1 master row to match Exp 3.5 anchor "
                f"({anchored_case}/{anchored_policy}/{anchored_tier}); got {n_matched}"
            )
        out.loc[mask, "measured"] = True
        out.loc[mask, "measured_p95_ms"] = round(anchored_p95, 2)
        out.loc[mask, "calibration_gap_pct"] = round(anchored_gap, 2)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    counts = out["label"].value_counts().to_dict()
    bc_counts = out["binding_constraint"].value_counts().to_dict()
    n_measured = int(out["measured"].sum())
    print(f"wrote {OUT_CSV}")
    print(f"rows: {len(out)} (expected 80)")
    print(f"label counts: {counts}")
    print(f"binding_constraint counts: {bc_counts}")
    print(f"measured rows: {n_measured}")


if __name__ == "__main__":
    main()
