#!/usr/bin/env python3
"""
export_primitives.py

Consume v1 Exp 1 outputs (timestamps_<modality>.csv + change_points_<modality>_*.csv)
and export per-modality JSON primitives files for use by the SmartWilds synthesis
engine (Exp 6.1) and variance envelope (Exp 6.2.A).

Output schema per modality (one JSON file):
    {
        "modality": str,
        "total_events": int,
        "date_range": [iso_start, iso_end],
        "aggregate": {
            "mean_rate_per_hour": float,
            "cv": float,
            "burstiness_B": float,
            "diurnal_profile": [24 floats],  # mean events per hour-of-day
        },
        "rate_model": {
            "thresholds": [0.8, 0.95, 0.99, 0.995],
            "change_points": {threshold: [[t_sec, rate_per_sec], ...]},
        },
        "per_site_variance": [
            {
                "site": str,
                "n_events": int,
                "cv": float,
                "burstiness_B": float,
                "diurnal_ks_vs_aggregate": float,
            },
            ...
        ],
        "provenance": {
            "source_csv": str,
            "change_points_dir": str,
            "generated_at": iso_timestamp,
        },
    }

Usage:
    python export_primitives.py --modality camera_trap
    python export_primitives.py --modality all
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

# --- portable paths: resolved by scripts/paths.py, overridable via env vars ---
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import (  # noqa: E402
    BASE_DIR, TIMESTAMPS_DIR as V1_RESULTS, PRIMITIVES_DIR as V2_OUT,
)

MODALITIES = ["camera_trap", "bioacoustic", "drone", "citizen_science"]
THRESHOLDS = [0.8, 0.95, 0.99, 0.995]
MIN_EVENTS_PER_SITE = 30  # skip sites with too few events for stable stats

# Campaign 2 is the main dataset (Aug 4 – Aug 28). Campaigns 1 and 3 were
# smaller outings; primitives scoped to Campaign 2 give a cleaner characterization
# and make downstream fidelity comparisons (Exp 6.2.B) apples-to-apples with the
# recorded replay window.
CAMPAIGN2_START = pd.Timestamp("2025-08-04 00:00:00")
CAMPAIGN2_END = pd.Timestamp("2025-08-29 00:00:00")

# Per-modality grouping keys. Bioacoustic schedules (hourly vs. sunrise_sunset) produce
# structurally different arrival processes at the same site — see sensor_configurations.md.
# Stratifying by (site, schedule) prevents inflating the natural-variance envelope used
# in Exp 6.2.A with schedule-induced variance that isn't "site-to-site" at all.
GROUP_KEYS = {
    "camera_trap": ["site"],
    "bioacoustic": ["site", "schedule"],
    "drone": ["site"],
    "citizen_science": ["site"],
}

# CV below this threshold with a large n_events indicates a timestamp-reconstruction
# artifact (e.g. drone missions where all frames collapsed to a single timestamp).
# These are excluded from per_site_variance so they don't poison the envelope.
DEGENERATE_CV_EPS = 1e-6

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def compute_burstiness(ts: pd.Series) -> tuple[float, float, float]:
    """Return (mean_rate_per_hour, cv, burstiness_B) from a timestamp series."""
    if len(ts) < 2:
        return 0.0, 0.0, 0.0
    iat = ts.sort_values().diff().dt.total_seconds().dropna()
    iat = iat[iat > 0]
    if len(iat) == 0:
        return 0.0, 0.0, 0.0
    mean_iat = iat.mean()
    std_iat = iat.std()
    mean_rate = 3600.0 / mean_iat if mean_iat > 0 else 0.0
    cv = std_iat / mean_iat if mean_iat > 0 else 0.0
    B = (cv - 1) / (cv + 1) if (cv + 1) > 0 else 0.0
    return mean_rate, cv, B


def diurnal_profile(ts: pd.Series) -> np.ndarray:
    """Return mean events-per-hour-of-day as a 24-element array (normalized by days covered)."""
    if len(ts) == 0:
        return np.zeros(24)
    ts = pd.to_datetime(ts)
    hours = ts.dt.hour
    counts = hours.value_counts().reindex(range(24), fill_value=0).sort_index()
    n_days = max(1, (ts.max() - ts.min()).total_seconds() / 86400.0)
    return (counts.values / n_days).astype(float)


def diurnal_ks(site_ts: pd.Series, agg_ts: pd.Series) -> float:
    """KS distance between a site's hour-of-day empirical CDF and the modality's aggregate."""
    if len(site_ts) < 2 or len(agg_ts) < 2:
        return float("nan")
    h_site = pd.to_datetime(site_ts).dt.hour.values.astype(float)
    h_agg = pd.to_datetime(agg_ts).dt.hour.values.astype(float)
    return float(ks_2samp(h_site, h_agg).statistic)


def load_change_points(
    modality: str,
    recording_start: pd.Timestamp | None = None,
    campaign2_only: bool = True,
) -> dict[str, list[list[float]]]:
    """
    Load per-threshold change-point + rate CSVs from v1 outputs.

    v1 change_point values are seconds since the first recorded timestamp
    (across all three campaigns). To rescope the rate model to Campaign 2,
    we drop segments outside the Aug 4–28 window and re-baseline remaining
    segments to start at t=0 (so downstream synth's
    `_draw_from_change_points` samples over [0, 25d] maps to Aug 4–28).
    """
    cps = {}
    if campaign2_only and recording_start is not None:
        c2_start_sec = (CAMPAIGN2_START - recording_start).total_seconds()
        c2_end_sec = (CAMPAIGN2_END - recording_start).total_seconds()
    else:
        c2_start_sec = None

    for thr in THRESHOLDS:
        cp_file = V1_RESULTS / f"change_points_{modality}_{thr}.csv"
        if not cp_file.exists():
            log.warning(f"  Missing change-point file: {cp_file}")
            continue
        df = pd.read_csv(cp_file)
        pairs = df[["change_point", "arrival_rate"]].values.tolist()
        if c2_start_sec is not None:
            # Keep only change points within Campaign 2 window; re-baseline to t=0.
            filt = [[t - c2_start_sec, r] for t, r in pairs if c2_start_sec <= t <= c2_end_sec]
            # Always include a terminal segment at end-of-Campaign-2 so draw has
            # a proper upper bound (synth uses t_max from last change point).
            if filt and filt[-1][0] < (c2_end_sec - c2_start_sec):
                filt.append([c2_end_sec - c2_start_sec, filt[-1][1]])
            cps[str(thr)] = filt
        else:
            cps[str(thr)] = pairs
    return cps


def export_one(modality: str, campaign2_only: bool = True) -> dict:
    """Build primitives JSON for one modality and write to disk.

    When campaign2_only=True (default per v2.1 pivot), timestamps are
    filtered to Aug 4–28 and change_points are rescoped + re-baselined to
    the same window so the rate model and the observational data align.
    """
    ts_file = V1_RESULTS / f"timestamps_{modality}.csv"
    if not ts_file.exists():
        raise FileNotFoundError(f"Missing timestamps file: {ts_file}")

    log.info(f"Loading {ts_file}")
    df_full = pd.read_csv(ts_file)
    df_full["timestamp"] = pd.to_datetime(df_full["timestamp"], format="ISO8601", errors="coerce")
    df_full = df_full.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    # Capture the pre-filter recording start so we can rebase change_points correctly.
    recording_start = df_full["timestamp"].iloc[0] if len(df_full) else None

    if campaign2_only:
        mask = (df_full["timestamp"] >= CAMPAIGN2_START) & (df_full["timestamp"] < CAMPAIGN2_END)
        df = df_full.loc[mask].copy().reset_index(drop=True)
        log.info(f"  filtered to Campaign 2: {len(df):,} of {len(df_full):,} events")
    else:
        df = df_full

    mean_rate, cv, B = compute_burstiness(df["timestamp"])
    diurnal = diurnal_profile(df["timestamp"])

    # Per-config variance. Config = grouping that makes arrival stats comparable.
    # See GROUP_KEYS: bioacoustic stratifies by (site, schedule); others by site only.
    per_site = []
    excluded_configs = []
    keys = [k for k in GROUP_KEYS.get(modality, ["site"]) if k in df.columns]
    if keys:
        for key_tuple, sdf in df.groupby(keys, sort=True):
            if len(sdf) < MIN_EVENTS_PER_SITE:
                continue
            if not isinstance(key_tuple, tuple):
                key_tuple = (key_tuple,)
            config_id = "|".join(str(v) for v in key_tuple)

            s_rate, s_cv, s_B = compute_burstiness(sdf["timestamp"])
            ks = diurnal_ks(sdf["timestamp"], df["timestamp"])

            entry = {
                "site": config_id,
                "config_keys": dict(zip(keys, [str(v) for v in key_tuple])),
                "n_events": int(len(sdf)),
                "mean_rate_per_hour": round(s_rate, 4),
                "cv": round(s_cv, 4),
                "burstiness_B": round(s_B, 4),
                "diurnal_ks_vs_aggregate": round(ks, 4) if not np.isnan(ks) else None,
            }
            if s_cv < DEGENERATE_CV_EPS and len(sdf) >= 100:
                entry["exclusion_reason"] = "degenerate_cv_likely_reconstructed_timestamps"
                excluded_configs.append(entry)
            else:
                per_site.append(entry)

    cps = load_change_points(modality, recording_start=recording_start, campaign2_only=campaign2_only)

    # date_range[0] anchors synth's t0. When change_points are rebased to t=0
    # at Campaign 2 start (Aug 4 00:00), date_range[0] must match that anchor —
    # otherwise synth time_shift drifts by (first_event − Aug4_00:00) and
    # diurnal hour-of-day alignment breaks (KS → 1.0 on modalities like drone
    # whose first Campaign 2 event is mid-day).
    if campaign2_only:
        date_start_iso = CAMPAIGN2_START.isoformat()
        date_end_iso = (CAMPAIGN2_END - pd.Timedelta(seconds=1)).isoformat()
    else:
        date_start_iso = df["timestamp"].min().isoformat() if len(df) else None
        date_end_iso = df["timestamp"].max().isoformat() if len(df) else None

    out = {
        "modality": modality,
        "total_events": int(len(df)),
        "date_range": [date_start_iso, date_end_iso],
        "campaign_scope": "campaign2_aug4_aug28" if campaign2_only else "all_campaigns",
        "aggregate": {
            "mean_rate_per_hour": round(mean_rate, 4),
            "cv": round(cv, 4),
            "burstiness_B": round(B, 4),
            "diurnal_profile": [round(x, 4) for x in diurnal.tolist()],
        },
        "rate_model": {
            "thresholds": THRESHOLDS,
            "change_points": cps,
        },
        "per_site_variance": per_site,
        "excluded_configs": excluded_configs,
        "provenance": {
            "source_csv": ts_file.name,
            "change_points_dir": str(V1_RESULTS),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "min_events_per_site": MIN_EVENTS_PER_SITE,
            "group_keys": keys,
            "degenerate_cv_eps": DEGENERATE_CV_EPS,
        },
    }

    V2_OUT.mkdir(parents=True, exist_ok=True)
    out_file = V2_OUT / f"{modality}.json"
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)
    log.info(
        f"  wrote {out_file}  (events={out['total_events']}, "
        f"sites/missions={len(per_site)}, B={out['aggregate']['burstiness_B']})"
    )
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--modality", choices=MODALITIES + ["all"], default="all")
    p.add_argument("--all-campaigns", action="store_true",
                   help="Export primitives using all three campaigns instead of the default Campaign 2 scope.")
    args = p.parse_args()

    campaign2_only = not args.all_campaigns
    log.info(f"Campaign scope: {'Campaign 2 only (Aug 4-28)' if campaign2_only else 'ALL campaigns'}")

    targets = MODALITIES if args.modality == "all" else [args.modality]
    for m in targets:
        try:
            export_one(m, campaign2_only=campaign2_only)
        except FileNotFoundError as e:
            log.error(f"Skipping {m}: {e}")


if __name__ == "__main__":
    main()
