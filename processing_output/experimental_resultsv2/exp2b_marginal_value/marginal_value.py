#!/usr/bin/env python3
"""
marginal_value.py — Exp 2.B: Sensor marginal value (non-redundancy hypothesis test).

Computes unique-coverage percentages across three dimensions:
  * Temporal: hour-of-day bins where modality M is the sole source of detections
  * Spatial: site × 24h-window cells where M is the sole active modality
  * Event-context (optional): confidence-tier bins uniquely covered by M

Feeds paper §V.C pillar result and Figure 7 (small multiples).

Inputs:
    processing_output/experimental_results/exp1_cross_modal_arrival_rates/results/
        timestamps_combined.csv   (cols: timestamp, modality, site, ...)

Outputs (under results/):
    temporal_unique_coverage.csv      (modality, bins_active, bins_unique, pct_unique)
    spatial_unique_coverage.csv       (modality, cells_active, cells_unique, pct_unique)
    spatial_coverage_matrix.csv       (site × modality active days; heatmap input)
    marginal_value_summary.json       (headline numbers)

Usage:
    python marginal_value.py                  # full analysis
    python marginal_value.py --overlap-only   # restrict to shared overlap window
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
V1_RESULTS = BASE_DIR / "processing_output" / "experimental_results" / "exp1_cross_modal_arrival_rates" / "results"
OUT_DIR = BASE_DIR / "processing_output" / "experimental_resultsv2" / "exp2b_marginal_value" / "results"

# REPORT.md flags 2025-07-01 → 2025-08-28 as the multi-modal overlap window
OVERLAP_START = pd.Timestamp("2025-07-01")
OVERLAP_END = pd.Timestamp("2025-08-28")

MODALITIES = ["camera_trap", "bioacoustic", "drone", "citizen_science"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def load_combined(overlap_only: bool) -> pd.DataFrame:
    path = V1_RESULTS / "timestamps_combined.csv"
    log.info(f"Loading {path}")
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", errors="coerce")
    before = len(df)
    df = df.dropna(subset=["timestamp"])
    if before != len(df):
        log.info(f"  dropped {before - len(df)} rows with unparseable timestamps")
    if overlap_only:
        before = len(df)
        df = df[(df["timestamp"] >= OVERLAP_START) & (df["timestamp"] <= OVERLAP_END)]
        log.info(f"  Overlap filter [{OVERLAP_START.date()} .. {OVERLAP_END.date()}]: {before} → {len(df)} rows")
    return df.reset_index(drop=True)


def temporal_unique_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each (date, hour-of-day) cell, record which modalities fired.
    A cell is 'uniquely covered by M' iff M is the sole modality active in that cell.
    Report per modality: active cells, uniquely-covered cells, pct_unique.
    """
    df = df.copy()
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour

    # Boolean presence matrix: (date, hour) × modality
    pres = (
        df.groupby(["date", "hour", "modality"]).size()
        .unstack(fill_value=0) > 0
    ).astype(int)
    pres = pres.reindex(columns=MODALITIES, fill_value=0)

    # Count modalities active per cell
    n_active = pres.sum(axis=1)

    rows = []
    for mod in MODALITIES:
        active = pres[mod] == 1
        unique = active & (n_active == 1)
        n_act = int(active.sum())
        n_uniq = int(unique.sum())
        pct = (n_uniq / n_act * 100.0) if n_act else 0.0
        rows.append({
            "modality": mod,
            "cells_active": n_act,
            "cells_unique": n_uniq,
            "pct_unique": round(pct, 2),
        })
    return pd.DataFrame(rows)


def spatial_unique_coverage(df: pd.DataFrame, window_hours: int = 24) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Spatial unique coverage. Bin events into (site, window) cells.
    'Site' here uses the TW## prefix where available so drone missions that
    cross a site contribute to that site; unclassifiable rows are dropped.

    Returns (summary_df, site_by_modality_matrix).
    """
    df = df.copy()
    # Extract TW## prefix from site field. Drone site=mission_id has no TW## prefix;
    # TODO: if drone mission → TW## mapping lands via 200m assignment, join here.
    df["site_prefix"] = df["site"].astype(str).str.extract(r"(TW\d+)", expand=False)
    df = df.dropna(subset=["site_prefix"])

    bin_h = f"{window_hours}h"
    df["window"] = df["timestamp"].dt.floor(bin_h)

    pres = (
        df.groupby(["site_prefix", "window", "modality"]).size()
        .unstack(fill_value=0) > 0
    ).astype(int)
    pres = pres.reindex(columns=MODALITIES, fill_value=0)

    n_active = pres.sum(axis=1)

    rows = []
    for mod in MODALITIES:
        active = pres[mod] == 1
        unique = active & (n_active == 1)
        n_act = int(active.sum())
        n_uniq = int(unique.sum())
        pct = (n_uniq / n_act * 100.0) if n_act else 0.0
        rows.append({
            "modality": mod,
            "cells_active": n_act,
            "cells_unique": n_uniq,
            "pct_unique": round(pct, 2),
            "window_hours": window_hours,
        })

    # Site × modality total active days (for heatmap figure)
    matrix = pres.groupby(level="site_prefix").sum().astype(int)
    return pd.DataFrame(rows), matrix


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--overlap-only", action="store_true",
                   help="Restrict to 2025-07-01..2025-08-28 shared overlap window")
    p.add_argument("--window-hours", type=int, default=24,
                   help="Window size for spatial binning (default 24h)")
    args = p.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_combined(overlap_only=args.overlap_only)

    temp = temporal_unique_coverage(df)
    temp_path = OUT_DIR / "temporal_unique_coverage.csv"
    temp.to_csv(temp_path, index=False)
    log.info(f"  wrote {temp_path}")

    spat, site_matrix = spatial_unique_coverage(df, window_hours=args.window_hours)
    spat_path = OUT_DIR / "spatial_unique_coverage.csv"
    spat.to_csv(spat_path, index=False)
    site_matrix.to_csv(OUT_DIR / "spatial_coverage_matrix.csv")
    log.info(f"  wrote {spat_path}")
    log.info(f"  wrote {OUT_DIR / 'spatial_coverage_matrix.csv'}")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overlap_only": args.overlap_only,
        "window_hours": args.window_hours,
        "temporal": temp.to_dict(orient="records"),
        "spatial": spat.to_dict(orient="records"),
    }
    with open(OUT_DIR / "marginal_value_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"  wrote {OUT_DIR / 'marginal_value_summary.json'}")

    # Console summary
    print("\n=== Temporal unique coverage (hour-of-day × date cells) ===")
    print(temp.to_string(index=False))
    print("\n=== Spatial unique coverage (TW## × 24h-window cells) ===")
    print(spat.to_string(index=False))


if __name__ == "__main__":
    main()
