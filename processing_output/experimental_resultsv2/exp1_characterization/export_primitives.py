#!/usr/bin/env python3
"""
export_primitives.py

Consume v1 Exp 1 outputs (timestamps_<modality>.csv + change_points_<modality>_*.csv)
and export per-modality JSON primitives files for use by the MOSAIC synthesis
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
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
V1_RESULTS = BASE_DIR / "processing_output" / "experimental_results" / "exp1_cross_modal_arrival_rates" / "results"
V2_OUT = BASE_DIR / "processing_output" / "experimental_resultsv2" / "exp1_characterization" / "primitives"

MODALITIES = ["camera_trap", "bioacoustic", "drone", "citizen_science"]
THRESHOLDS = [0.8, 0.95, 0.99, 0.995]
MIN_EVENTS_PER_SITE = 30  # skip sites with too few events for stable stats

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


def load_change_points(modality: str) -> dict[str, list[list[float]]]:
    """Load per-threshold change-point + rate CSVs from v1 outputs."""
    cps = {}
    for thr in THRESHOLDS:
        cp_file = V1_RESULTS / f"change_points_{modality}_{thr}.csv"
        if not cp_file.exists():
            log.warning(f"  Missing change-point file: {cp_file}")
            continue
        df = pd.read_csv(cp_file)
        cps[str(thr)] = df[["change_point", "arrival_rate"]].values.tolist()
    return cps


def export_one(modality: str) -> dict:
    """Build primitives JSON for one modality and write to disk."""
    ts_file = V1_RESULTS / f"timestamps_{modality}.csv"
    if not ts_file.exists():
        raise FileNotFoundError(f"Missing timestamps file: {ts_file}")

    log.info(f"Loading {ts_file}")
    df = pd.read_csv(ts_file)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

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

    cps = load_change_points(modality)

    out = {
        "modality": modality,
        "total_events": int(len(df)),
        "date_range": [
            df["timestamp"].min().isoformat() if len(df) else None,
            df["timestamp"].max().isoformat() if len(df) else None,
        ],
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
            "source_csv": str(ts_file.relative_to(BASE_DIR)),
            "change_points_dir": str(V1_RESULTS.relative_to(BASE_DIR)),
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
    args = p.parse_args()

    targets = MODALITIES if args.modality == "all" else [args.modality]
    for m in targets:
        try:
            export_one(m)
        except FileNotFoundError as e:
            log.error(f"Skipping {m}: {e}")


if __name__ == "__main__":
    main()
