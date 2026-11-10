#!/usr/bin/env python3
"""
identity_test.py — Exp 6.1 sanity check.

Invariant: synthesize(identity_recipe, full_primitives) should reproduce
recorded-trace statistics (B, CV, 24h diurnal KS) within tight tolerance.

This is the gate at end of Day 3 before handing off to Anirudh/Yuanyang.
Run it after export_primitives.py produces the primitives JSONs.

Usage:
    python identity_test.py                     # 80-day horizon (covers all modalities' recorded spans)
    python identity_test.py --duration-days 24  # short window — comparison will be apples-to-oranges
                                                # because real_ts is the FULL recorded series

Pass thresholds (same values as Exp 6.2.A trace fidelity):
    |B_synth - B_real|          ≤ 0.05   (primary: bounded in [0,1], robust)
    diurnal KS distance         ≤ 0.15   (primary: hour-of-day structure)
    |CV_synth - CV_real| / CV   ≤ 0.15   (informational for B < 0.9)

CV is reported but is not a pass condition when B_real > 0.85. CV and B are
coupled via CV = (1+B)/(1-B), so dCV/dB = 2/(1-B)² blows up as B→1: at B=0.85
a compliant ΔB of 0.022 already forces ΔCV/CV ≈ 16%, exceeding the 15%
threshold purely by arithmetic. Above this boundary, the B metric and the
diurnal KS metric are the binding ones; CV is reported for diagnostics only.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from schemas import identity_recipe
from synthesize import load_primitives, synthesize

HIGH_BURST_B_THRESHOLD = 0.85

# --- portable paths: resolved by scripts/paths.py, overridable via env vars ---
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import BASE_DIR, TIMESTAMPS_DIR as V1_RESULTS  # noqa: E402

BURSTINESS_TOL = 0.05
CV_REL_TOL = 0.15
DIURNAL_KS_TOL = 0.15

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def compute_stats(ts: pd.Series) -> tuple[float, float]:
    """Returns (cv, B) from a timestamp series."""
    iat = ts.sort_values().diff().dt.total_seconds().dropna()
    iat = iat[iat > 0]
    if len(iat) == 0:
        return 0.0, 0.0
    cv = iat.std() / iat.mean() if iat.mean() > 0 else 0.0
    B = (cv - 1) / (cv + 1) if (cv + 1) > 0 else 0.0
    return cv, B


CAMPAIGN2_START = pd.Timestamp("2025-08-04 00:00:00")
CAMPAIGN2_END = pd.Timestamp("2025-08-29 00:00:00")


def load_recorded(modality: str, campaign2_only: bool = True) -> pd.Series:
    path = V1_RESULTS / f"timestamps_{modality}.csv"
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
    if campaign2_only:
        df = df[(df["timestamp"] >= CAMPAIGN2_START) & (df["timestamp"] < CAMPAIGN2_END)]
    return df["timestamp"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--duration-days", type=int, default=25,
                   help="Synth horizon in days. Default 25 matches Campaign 2 span (Aug 4-28).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--all-campaigns", action="store_true",
                   help="Compare against all-campaigns recorded data instead of Campaign 2 only.")
    args = p.parse_args()

    campaign2_only = not args.all_campaigns

    duration_s = args.duration_days * 86400.0
    recipe = identity_recipe(duration_seconds=duration_s, seed=args.seed)
    primitives = load_primitives(recipe.modality_mix)

    log.info(f"Synthesizing identity recipe (horizon={args.duration_days}d, seed={args.seed})")
    synth = synthesize(recipe, primitives=primitives)
    log.info(f"Synthesized {len(synth)} total events across {synth['modality'].nunique()} modalities")

    print(f"\n{'Modality':<16} {'B_real':>8} {'B_synth':>8} {'ΔB':>8} {'CV_real':>10} {'CV_synth':>10} {'ΔCV/CV':>9} {'KS':>7}  verdict")
    all_pass = True
    for m in recipe.modality_mix:
        real_ts = load_recorded(m, campaign2_only=campaign2_only)
        synth_ts = pd.to_datetime(synth[synth["modality"] == m]["timestamp"])
        if len(real_ts) < 2 or len(synth_ts) < 2:
            print(f"{m:<16} insufficient data")
            all_pass = False
            continue

        cv_r, B_r = compute_stats(real_ts)
        cv_s, B_s = compute_stats(synth_ts)
        dB = abs(B_s - B_r)
        dCV = abs(cv_s - cv_r) / cv_r if cv_r > 0 else float("inf")
        ks = ks_2samp(real_ts.dt.hour.values.astype(float), synth_ts.dt.hour.values.astype(float)).statistic

        cv_gates = B_r <= HIGH_BURST_B_THRESHOLD  # CV only binding for moderate-burstiness modalities
        ok = (dB <= BURSTINESS_TOL) and (ks <= DIURNAL_KS_TOL) and (not cv_gates or dCV <= CV_REL_TOL)
        verdict = "PASS" if ok else "FAIL"
        all_pass &= ok
        print(f"{m:<16} {B_r:>8.4f} {B_s:>8.4f} {dB:>8.4f} {cv_r:>10.2f} {cv_s:>10.2f} {dCV:>9.2%} {ks:>7.3f}  {verdict}")

    print(f"\nOverall: {'PASS — identity invariant holds' if all_pass else 'FAIL — investigate before handoff'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
