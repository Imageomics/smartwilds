#!/usr/bin/env python3
"""
extract_wilds_multimodal.py

Extract timestamps from all sensing modalities in TheWilds2025 dataset
and run cross-modal ADAE arrival rate analysis.

Modalities: camera traps, bioacoustics, drones, citizen science

Usage:
    python extract_wilds_multimodal.py --modality all --analyze --plot
    python extract_wilds_multimodal.py --modality camera_trap --campaign campaign1
    python extract_wilds_multimodal.py --modality bioacoustic --analyze
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Try importing PIL for EXIF extraction
try:
    from PIL import Image, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")

CAMPAIGNS = {
    "campaign1": "thewilds_20250630_20250703",
    "campaign2": "thewilds_20250804_20250828",
    "campaign3": "thewilds_20250908_20250908",
}

BIOACOUSTIC_CSV = BASE_DIR / "BioacousticAnalysis" / "WildsBird_Every_Hour.csv"

DEFAULT_OUTPUT_DIR = BASE_DIR / "documentation" / "adae_model" / "data" / "outputs" / "wilds_multimodal"

# Camera deployment metadata (import for timestamp corrections)
CAMTRAP_PIPELINE = BASE_DIR / "documentation" / "annotation_pipeline" / "camera_traps" / "imageomicsthewilds_cameratraps" / "src" / "01_events"

# ---------------------------------------------------------------------------
# Import camera deployment metadata for timestamp corrections
# ---------------------------------------------------------------------------

sys.path.insert(0, str(CAMTRAP_PIPELINE))
try:
    from camera_deployment_metadata import should_apply_timestamp_correction, DEPLOYMENTS
    HAS_DEPLOYMENT_META = True
except ImportError:
    HAS_DEPLOYMENT_META = False
    logging.warning("Could not import camera_deployment_metadata; timestamp corrections disabled")

# ---------------------------------------------------------------------------
# Import ADAE change point analysis functions
# ---------------------------------------------------------------------------

sys.path.insert(0, str(BASE_DIR / "documentation" / "adae_model"))
from change_points import (
    getChangePoints,
    arrivalRate,
    avgArrivalTimes,
    poisson_process_with_rate_variation,
    error_metrics,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timestamp extraction helpers (adapted from make_events.py)
# ---------------------------------------------------------------------------

# Regex for filenames like NSCF0002_250630121802_0022.JPG -> YYMMDDHHMMSS
RE_TS = re.compile(r"_(\d{12})_")

# Regex for site-camera directory names like TW01-CT02 or TW09_CT02
RE_SITE_CAM = re.compile(r"(TW\d+)[-_](CT\d+)")

# EXIF tag IDs
if HAS_PIL:
    _TAGS = ExifTags.TAGS
    _NAME2ID = {v: k for k, v in _TAGS.items()}
    _DTO_ID = _NAME2ID.get("DateTimeOriginal")
    _DT_ID = _NAME2ID.get("DateTime")


def ts_from_filename(name: str):
    """Extract timestamp from camera trap filename (YYMMDDHHMMSS pattern)."""
    m = RE_TS.search(name)
    if not m:
        return None
    s = m.group(1)
    try:
        year = 2000 + int(s[0:2])
        mo = int(s[2:4])
        d = int(s[4:6])
        hh = int(s[6:8])
        mm = int(s[8:10])
        ss = int(s[10:12])
        return pd.Timestamp(year=year, month=mo, day=d, hour=hh, minute=mm, second=ss)
    except (ValueError, OverflowError):
        return None


def ts_from_exif(path: Path):
    """Extract timestamp from EXIF DateTimeOriginal or DateTime."""
    if not HAS_PIL:
        return None
    try:
        img = Image.open(path)
        exif = img.getexif()
        if not exif:
            return None
        val = None
        if _DTO_ID is not None and _DTO_ID in exif:
            val = exif.get(_DTO_ID)
        elif _DT_ID is not None and _DT_ID in exif:
            val = exif.get(_DT_ID)
        if val is None:
            return None
        return pd.to_datetime(str(val), format="%Y:%m:%d %H:%M:%S", errors="coerce")
    except Exception:
        return None


def extract_site_cam(path: Path):
    """Extract site-camera ID (e.g., TW01-CT02) from directory path."""
    for part in path.parts:
        m = RE_SITE_CAM.match(part)
        if m:
            return f"{m.group(1)}-{m.group(2)}", m.group(1)
    return None, None


def apply_ts_correction(site_cam: str, ts: pd.Timestamp) -> pd.Timestamp:
    """Apply known timestamp corrections for cameras with incorrect clocks."""
    if not HAS_DEPLOYMENT_META or ts is None or pd.isna(ts):
        return ts
    corrected = should_apply_timestamp_correction(
        site_cam, ts.year, ts.month, ts.day
    )
    if corrected is not None:
        cy, cm, cd = corrected
        return ts.replace(year=cy, month=cm, day=cd)
    return ts


# =========================================================================
# MODALITY EXTRACTORS
# =========================================================================


def extract_camera_trap_timestamps(
    campaigns: list[str] | None = None,
    apply_corrections: bool = True,
) -> pd.DataFrame:
    """
    Extract timestamps from camera trap images across campaigns.

    Walks directory tree looking for image files, extracts timestamps
    from filenames (YYMMDDHHMMSS pattern) or EXIF metadata.

    Returns DataFrame with columns:
        timestamp, modality, site, site_cam, source_file, campaign, is_blank
    """
    if campaigns is None:
        campaigns = list(CAMPAIGNS.keys())

    rows = []
    missing = 0
    exif_used = 0
    total = 0

    for campaign_key in campaigns:
        campaign_dir = CAMPAIGNS.get(campaign_key)
        if campaign_dir is None:
            log.warning(f"Unknown campaign: {campaign_key}")
            continue

        ct_root = BASE_DIR / campaign_dir / "camera_traps"
        if not ct_root.exists():
            log.warning(f"Camera trap directory not found: {ct_root}")
            continue

        log.info(f"Scanning camera traps in {ct_root}")

        # Walk recursively for image files
        image_extensions = {".jpg", ".jpeg", ".png", ".avi"}
        for img_path in ct_root.rglob("*"):
            if img_path.suffix.lower() not in image_extensions:
                continue
            if not img_path.is_file():
                continue

            total += 1
            if total % 5000 == 0:
                log.info(f"  Processed {total} images ({len(rows)} with timestamps, {missing} missing)")

            site_cam, site = extract_site_cam(img_path)
            if site_cam is None:
                missing += 1
                continue

            # Try filename first, then EXIF
            ts = ts_from_filename(img_path.name)
            if ts is None:
                ts = ts_from_exif(img_path)
                if ts is not None and not pd.isna(ts):
                    exif_used += 1

            if ts is None or pd.isna(ts):
                missing += 1
                continue

            # Apply timestamp corrections (e.g., TW02-CT01 clock error)
            if apply_corrections:
                ts = apply_ts_correction(site_cam, ts)

            rows.append({
                "timestamp": ts,
                "modality": "camera_trap",
                "site": site,
                "site_cam": site_cam,
                "source_file": str(img_path.relative_to(BASE_DIR)),
                "campaign": campaign_key,
                "is_blank": None,  # To be filled after running detections
            })

    log.info(
        f"Camera traps: {len(rows)} events extracted, "
        f"{missing} missing timestamps, {exif_used} from EXIF"
    )

    if not rows:
        return pd.DataFrame(columns=[
            "timestamp", "modality", "site", "site_cam",
            "source_file", "campaign", "is_blank",
        ])

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


def extract_bioacoustic_timestamps(
    csv_path: Path | None = None,
) -> pd.DataFrame:
    """
    Extract timestamps from BirdNET hourly aggregated CSV.

    Each row represents one hour of recording at a site with species counts.

    Returns DataFrame with columns:
        timestamp, modality, site, source_file, total_birds, num_species
    """
    if csv_path is None:
        csv_path = BIOACOUSTIC_CSV

    if not csv_path.exists():
        log.warning(f"Bioacoustic CSV not found: {csv_path}")
        return pd.DataFrame(columns=[
            "timestamp", "modality", "site", "source_file",
            "total_birds", "num_species",
        ])

    log.info(f"Reading bioacoustic data from {csv_path}")
    df = pd.read_csv(csv_path)

    # Identify species columns (everything that's not metadata)
    meta_cols = {"datetime", "location", "file_ID", "total_birds"}
    species_cols = [c for c in df.columns if c not in meta_cols]

    rows = []
    for _, row in df.iterrows():
        ts = pd.to_datetime(row["datetime"], errors="coerce")
        if pd.isna(ts):
            continue

        # Count non-zero species
        num_species = sum(1 for c in species_cols if pd.notna(row.get(c)) and row.get(c, 0) > 0)
        total = row.get("total_birds", 0)
        if pd.isna(total):
            total = 0

        rows.append({
            "timestamp": ts,
            "modality": "bioacoustic",
            "site": str(row.get("location", "unknown")),
            "source_file": str(row.get("file_ID", "")),
            "total_birds": int(total),
            "num_species": num_species,
        })

    log.info(f"Bioacoustics: {len(rows)} hourly events extracted")
    result = pd.DataFrame(rows)
    if not result.empty:
        result["timestamp"] = pd.to_datetime(result["timestamp"])
    return result.sort_values("timestamp").reset_index(drop=True)


def extract_drone_timestamps(
    campaigns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Extract flight timestamps from drone metadata (Airdata CSVs).

    Returns DataFrame with columns:
        timestamp, modality, site, source_file, platform, flight_duration_sec
    """
    if campaigns is None:
        campaigns = list(CAMPAIGNS.keys())

    rows = []

    for campaign_key in campaigns:
        campaign_dir = CAMPAIGNS.get(campaign_key)
        if campaign_dir is None:
            continue

        drone_root = BASE_DIR / campaign_dir / "drones"
        if not drone_root.exists():
            continue

        log.info(f"Scanning drone metadata in {drone_root}")

        # Look for CSV metadata files
        for csv_path in drone_root.rglob("metadata/*.csv"):
            if not csv_path.is_file():
                continue

            try:
                df = pd.read_csv(csv_path, nrows=5)
            except Exception as e:
                log.warning(f"Could not read {csv_path}: {e}")
                continue

            flight_start = None
            flight_end = None
            platform = "unknown"

            # Detect format: Airdata (has datetime(utc)) vs DJI export
            if "datetime(utc)" in df.columns:
                # Airdata / Parrot format
                full_df = pd.read_csv(csv_path, usecols=["datetime(utc)"])
                times = pd.to_datetime(full_df["datetime(utc)"], errors="coerce").dropna()
                if not times.empty:
                    flight_start = times.iloc[0]
                    flight_end = times.iloc[-1]
                platform = "parrot" if "parrot" in str(csv_path).lower() else "dji"

            elif "count(10HZ)" in df.columns:
                # DJI ExportCSV format — parse timestamp from filename
                # e.g., ExportCSV_2025-08-11_[10-29-13].csv
                fname = csv_path.name
                m = re.search(r"(\d{4}-\d{2}-\d{2})_\[(\d{2})-(\d{2})-(\d{2})\]", fname)
                if m:
                    date_str = m.group(1)
                    h, mi, s = m.group(2), m.group(3), m.group(4)
                    flight_start = pd.to_datetime(f"{date_str} {h}:{mi}:{s}", errors="coerce")
                    # Estimate duration from row count (10 Hz)
                    full_df = pd.read_csv(csv_path, usecols=["count(10HZ)"])
                    duration_sec = len(full_df) / 10.0
                    if flight_start is not None and not pd.isna(flight_start):
                        flight_end = flight_start + pd.Timedelta(seconds=duration_sec)
                platform = "dji"
            else:
                # Try to find any datetime-like column
                for col in df.columns:
                    if "time" in col.lower() or "date" in col.lower():
                        try:
                            full_df = pd.read_csv(csv_path, usecols=[col])
                            times = pd.to_datetime(full_df[col], errors="coerce").dropna()
                            if not times.empty:
                                flight_start = times.iloc[0]
                                flight_end = times.iloc[-1]
                                break
                        except Exception:
                            continue

            if flight_start is not None and not pd.isna(flight_start):
                duration = 0
                if flight_end is not None and not pd.isna(flight_end):
                    duration = (flight_end - flight_start).total_seconds()

                # Determine site from directory name if possible
                parent_name = csv_path.parent.parent.name  # e.g., 20250811_DJI_01
                site = "unknown"

                rows.append({
                    "timestamp": flight_start,
                    "modality": "drone",
                    "site": site,
                    "source_file": str(csv_path.relative_to(BASE_DIR)),
                    "platform": platform,
                    "flight_duration_sec": round(duration, 1),
                })

    log.info(f"Drones: {len(rows)} flights extracted")

    if not rows:
        return pd.DataFrame(columns=[
            "timestamp", "modality", "site", "source_file",
            "platform", "flight_duration_sec",
        ])

    result = pd.DataFrame(rows)
    result["timestamp"] = pd.to_datetime(result["timestamp"])
    return result.sort_values("timestamp").reset_index(drop=True)


def extract_citizen_science_timestamps(
    campaigns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Extract timestamps from citizen science submissions.

    Tries EXIF from JPEG files first, falls back to filesystem mtime.

    Returns DataFrame with columns:
        timestamp, modality, site, source_file, file_type
    """
    if campaigns is None:
        campaigns = ["campaign2"]  # citizen science only in Campaign 2

    rows = []
    exif_used = 0
    mtime_used = 0

    for campaign_key in campaigns:
        campaign_dir = CAMPAIGNS.get(campaign_key)
        if campaign_dir is None:
            continue

        cs_root = BASE_DIR / campaign_dir / "citizen_science"
        if not cs_root.exists():
            continue

        log.info(f"Scanning citizen science in {cs_root}")

        media_extensions = {".jpg", ".jpeg", ".heic", ".png", ".mov", ".mp4"}
        for f in cs_root.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() not in media_extensions:
                continue

            ts = None

            # Try EXIF for JPEG files
            if f.suffix.lower() in {".jpg", ".jpeg"} and HAS_PIL:
                ts = ts_from_exif(f)
                if ts is not None and not pd.isna(ts):
                    exif_used += 1

            # Fall back to filesystem modification time
            if ts is None or pd.isna(ts):
                try:
                    mtime = os.path.getmtime(f)
                    ts = pd.Timestamp.fromtimestamp(mtime)
                    mtime_used += 1
                except Exception:
                    continue

            rows.append({
                "timestamp": ts,
                "modality": "citizen_science",
                "site": "unknown",
                "source_file": str(f.relative_to(BASE_DIR)),
                "file_type": f.suffix.lower(),
            })

    log.info(
        f"Citizen science: {len(rows)} files ({exif_used} EXIF, {mtime_used} mtime)"
    )

    if not rows:
        return pd.DataFrame(columns=[
            "timestamp", "modality", "site", "source_file", "file_type",
        ])

    result = pd.DataFrame(rows)
    result["timestamp"] = pd.to_datetime(result["timestamp"])
    return result.sort_values("timestamp").reset_index(drop=True)


# =========================================================================
# COMBINE AND ANALYZE
# =========================================================================


def combine_all_modalities(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate all modality DataFrames and sort by timestamp."""
    combined = pd.concat(dfs, ignore_index=True)
    combined["timestamp"] = pd.to_datetime(combined["timestamp"])
    combined = combined.sort_values("timestamp").reset_index(drop=True)

    modality_map = {
        "camera_trap": 0,
        "bioacoustic": 1,
        "drone": 2,
        "citizen_science": 3,
    }
    combined["modality_id"] = combined["modality"].map(modality_map)

    log.info(f"Combined: {len(combined)} total events across {combined['modality'].nunique()} modalities")
    return combined


def run_adae_analysis(
    combined_df: pd.DataFrame,
    output_dir: Path,
    thresholds: list[float] | None = None,
) -> pd.DataFrame:
    """
    Run per-modality ADAE change point analysis.

    For each modality:
    1. Convert timestamps to seconds from first event
    2. Detect change points at multiple thresholds
    3. Compute arrival rates between change points
    4. Fit time-varying Poisson process
    5. Compute error metrics (MAE, MSE, MAPE)

    Returns summary DataFrame.
    """
    if thresholds is None:
        thresholds = [0.8, 0.95, 0.99, 0.995]

    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []

    for modality in combined_df["modality"].unique():
        mod_df = combined_df[combined_df["modality"] == modality].copy()
        if len(mod_df) < 10:
            log.warning(f"Skipping {modality}: only {len(mod_df)} events")
            continue

        log.info(f"ADAE analysis for {modality} ({len(mod_df)} events)")

        # Convert to relative seconds
        t0 = mod_df["timestamp"].min()
        mod_df["time"] = (mod_df["timestamp"] - t0).dt.total_seconds()
        mod_df = mod_df.sort_values("time").reset_index(drop=True)

        # Compute inter-arrival times for statistics
        inter_arrivals = mod_df["time"].diff().dropna()
        inter_arrivals = inter_arrivals[inter_arrivals > 0]

        if len(inter_arrivals) == 0:
            mean_rate = 0
            cv = 0
            burstiness = 0
        else:
            mean_iat = inter_arrivals.mean()
            std_iat = inter_arrivals.std()
            mean_rate = 3600.0 / mean_iat if mean_iat > 0 else 0  # events per hour
            cv = std_iat / mean_iat if mean_iat > 0 else 0
            burstiness = (cv - 1) / (cv + 1) if (cv + 1) > 0 else 0

        date_range_str = f"{mod_df['timestamp'].min()} to {mod_df['timestamp'].max()}"
        num_sites = mod_df["site"].nunique() if "site" in mod_df.columns else 0

        summaries.append({
            "modality": modality,
            "total_events": len(mod_df),
            "date_range": date_range_str,
            "mean_arrival_rate_per_hour": round(mean_rate, 2),
            "cv": round(cv, 4),
            "burstiness": round(burstiness, 4),
            "num_sites": num_sites,
        })

        # Run change point analysis for each threshold
        time_df = mod_df[["time"]].copy()

        for threshold in thresholds:
            try:
                change_points_df, _ = getChangePoints(time_df, threshold)
                cp = change_points_df["time"].tolist()
                cp.insert(0, 0)
                cp.append(time_df["time"].max())

                # Calculate arrival rates
                rates_dict = avgArrivalTimes(time_df, cp)

                # Save change points and rates
                cp_out = pd.DataFrame({
                    "change_point": list(rates_dict.keys()),
                    "arrival_rate": list(rates_dict.values()),
                })
                cp_file = output_dir / f"change_points_{modality}_{threshold}.csv"
                cp_out.to_csv(cp_file, index=False)

                # Simulate Poisson process
                rates = list(rates_dict.values())
                change_pts = list(rates_dict.keys())
                if len(rates) > 0 and time_df["time"].max() > 0:
                    simulated = poisson_process_with_rate_variation(
                        time_df["time"].max(), rates, change_pts
                    )
                    log.info(
                        f"  {modality} threshold={threshold}: "
                        f"{len(cp)-2} change points, "
                        f"{len(simulated)} simulated events"
                    )
            except Exception as e:
                log.warning(f"  Change point analysis failed for {modality} threshold={threshold}: {e}")

    summary_df = pd.DataFrame(summaries)
    summary_file = output_dir / "summary_table.csv"
    summary_df.to_csv(summary_file, index=False)
    log.info(f"Summary saved to {summary_file}")

    return summary_df


def compute_cross_modal_correlation(
    combined_df: pd.DataFrame,
    output_dir: Path,
    time_windows: list[int] | None = None,
) -> dict[int, pd.DataFrame]:
    """
    Compute temporal co-occurrence between modalities at co-located sites.

    Co-located sensors share the same site prefix (TW##).
    For each time window, bins events and computes Jaccard similarity
    between modality pairs.

    Returns dict mapping window_hours -> correlation matrix DataFrame.
    """
    if time_windows is None:
        time_windows = [1, 6, 24]

    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract site prefix (TW##) for co-location matching
    df = combined_df.copy()
    df["site_prefix"] = df["site"].apply(
        lambda s: re.match(r"(TW\d+)", str(s)).group(1)
        if re.match(r"(TW\d+)", str(s))
        else None
    )

    # Filter to rows with known site prefixes
    df = df.dropna(subset=["site_prefix"])

    # Find sites with multiple modalities
    site_modalities = df.groupby("site_prefix")["modality"].apply(set).to_dict()
    multi_modal_sites = {
        site: mods for site, mods in site_modalities.items() if len(mods) > 1
    }

    if not multi_modal_sites:
        log.warning("No co-located multi-modal sites found")
        return {}

    log.info(f"Co-located sites with multiple modalities: {multi_modal_sites}")

    modalities = sorted(df["modality"].unique())
    results = {}

    for window_h in time_windows:
        log.info(f"Computing cross-modal correlation (window={window_h}h)")

        # Create time bins
        t_min = df["timestamp"].min()
        t_max = df["timestamp"].max()
        bins = pd.date_range(start=t_min, end=t_max, freq=f"{window_h}h")

        if len(bins) < 2:
            log.warning(f"  Not enough time range for {window_h}h bins")
            continue

        # Build correlation matrix
        corr_matrix = pd.DataFrame(
            np.zeros((len(modalities), len(modalities))),
            index=modalities,
            columns=modalities,
        )

        pair_counts = pd.DataFrame(
            np.zeros((len(modalities), len(modalities))),
            index=modalities,
            columns=modalities,
        )

        for site, mods in multi_modal_sites.items():
            site_df = df[df["site_prefix"] == site]

            for i, mod_a in enumerate(modalities):
                for j, mod_b in enumerate(modalities):
                    if j <= i:
                        continue
                    if mod_a not in mods or mod_b not in mods:
                        continue

                    events_a = site_df[site_df["modality"] == mod_a]["timestamp"]
                    events_b = site_df[site_df["modality"] == mod_b]["timestamp"]

                    if events_a.empty or events_b.empty:
                        continue

                    # Bin both into time windows
                    bins_a = set(pd.cut(events_a, bins=bins, labels=False).dropna().astype(int))
                    bins_b = set(pd.cut(events_b, bins=bins, labels=False).dropna().astype(int))

                    intersection = len(bins_a & bins_b)
                    union = len(bins_a | bins_b)

                    if union > 0:
                        jaccard = intersection / union
                        corr_matrix.loc[mod_a, mod_b] += jaccard
                        corr_matrix.loc[mod_b, mod_a] += jaccard
                        pair_counts.loc[mod_a, mod_b] += 1
                        pair_counts.loc[mod_b, mod_a] += 1

        # Average over sites
        pair_counts = pair_counts.replace(0, np.nan)
        corr_matrix = corr_matrix / pair_counts
        corr_matrix = corr_matrix.fillna(0)

        # Set diagonal to 1
        for mod in modalities:
            corr_matrix.loc[mod, mod] = 1.0

        corr_file = output_dir / f"cross_modal_correlation_{window_h}h.csv"
        corr_matrix.to_csv(corr_file)
        log.info(f"  Saved {corr_file}")

        results[window_h] = corr_matrix

    return results


# =========================================================================
# PLOTTING
# =========================================================================


def plot_overlaid_arrival_rates(
    combined_df: pd.DataFrame,
    output_dir: Path,
):
    """
    Plot cumulative event count over time for all modalities (overlaid).

    Produces a figure analogous to Fig 3 from the 2024 SEC paper.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    modality_colors = {
        "camera_trap": "#1f77b4",
        "bioacoustic": "#ff7f0e",
        "drone": "#2ca02c",
        "citizen_science": "#d62728",
    }
    modality_labels = {
        "camera_trap": "Camera Traps",
        "bioacoustic": "Bioacoustics",
        "drone": "Drones",
        "citizen_science": "Citizen Science",
    }

    fig, ax = plt.subplots(figsize=(12, 6))

    for modality in combined_df["modality"].unique():
        mod_df = combined_df[combined_df["modality"] == modality].sort_values("timestamp")
        if mod_df.empty:
            continue

        # Normalize time to [0, 1] for comparison
        t0 = mod_df["timestamp"].min()
        t1 = mod_df["timestamp"].max()
        total_sec = (t1 - t0).total_seconds()
        if total_sec == 0:
            continue

        normalized_time = (mod_df["timestamp"] - t0).dt.total_seconds() / total_sec
        cumulative = np.arange(1, len(mod_df) + 1)

        color = modality_colors.get(modality, "gray")
        label = modality_labels.get(modality, modality)

        ax.plot(normalized_time, cumulative, label=label, color=color, linewidth=1.5)

    ax.set_xlabel("Normalized Time", fontsize=12)
    ax.set_ylabel("Cumulative Event Count", fontsize=12)
    ax.set_title("Multi-Modal Arrival Rates — The Wilds 2025", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    for ext in ["png", "pdf"]:
        out_path = output_dir / f"overlaid_arrival_rates.{ext}"
        fig.savefig(out_path, dpi=150)
        log.info(f"Saved {out_path}")
    plt.close(fig)


def plot_correlation_heatmap(
    corr_matrices: dict[int, pd.DataFrame],
    output_dir: Path,
):
    """Plot heatmap of cross-modal Jaccard correlation for each time window."""
    output_dir.mkdir(parents=True, exist_ok=True)

    modality_labels = {
        "camera_trap": "Camera Traps",
        "bioacoustic": "Bioacoustics",
        "drone": "Drones",
        "citizen_science": "Citizen Science",
    }

    for window_h, corr_matrix in corr_matrices.items():
        fig, ax = plt.subplots(figsize=(8, 6))

        # Rename for display
        display = corr_matrix.rename(
            index=modality_labels, columns=modality_labels
        )

        im = ax.imshow(display.values, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(display.columns)))
        ax.set_yticks(range(len(display.index)))
        ax.set_xticklabels(display.columns, rotation=45, ha="right", fontsize=10)
        ax.set_yticklabels(display.index, fontsize=10)

        # Add text annotations
        for i in range(len(display.index)):
            for j in range(len(display.columns)):
                val = display.values[i, j]
                color = "white" if val > 0.5 else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=color, fontsize=10)

        ax.set_title(f"Cross-Modal Temporal Correlation (Jaccard, {window_h}h bins)", fontsize=12)
        fig.colorbar(im, ax=ax, label="Jaccard Similarity")
        plt.tight_layout()

        for ext in ["png", "pdf"]:
            out_path = output_dir / f"cross_modal_heatmap_{window_h}h.{ext}"
            fig.savefig(out_path, dpi=150)
        plt.close(fig)
        log.info(f"Saved correlation heatmap for {window_h}h window")


# =========================================================================
# MAIN
# =========================================================================


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract timestamps and run cross-modal ADAE analysis for TheWilds2025"
    )
    parser.add_argument(
        "--modality",
        choices=["camera_trap", "bioacoustic", "drone", "citizen_science", "all"],
        default="all",
        help="Which modality to extract (default: all)",
    )
    parser.add_argument(
        "--campaign",
        choices=list(CAMPAIGNS.keys()) + ["all"],
        default="all",
        help="Which campaign to process (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for results",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run ADAE change point analysis after extraction",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate plots",
    )
    parser.add_argument(
        "--time-windows",
        type=int,
        nargs="+",
        default=[1, 6, 24],
        help="Time windows (hours) for cross-modal correlation (default: 1 6 24)",
    )
    parser.add_argument(
        "--no-corrections",
        action="store_true",
        help="Skip camera trap timestamp corrections",
    )
    parser.add_argument(
        "--bioacoustic-mode",
        choices=["aggregated", "per_species"],
        default="aggregated",
        help="How to treat bioacoustic rows (default: aggregated)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    campaigns = list(CAMPAIGNS.keys()) if args.campaign == "all" else [args.campaign]
    modalities_to_run = (
        ["camera_trap", "bioacoustic", "drone", "citizen_science"]
        if args.modality == "all"
        else [args.modality]
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # ---- Extract timestamps ----
    dfs = []

    if "camera_trap" in modalities_to_run:
        ct_df = extract_camera_trap_timestamps(
            campaigns=campaigns,
            apply_corrections=not args.no_corrections,
        )
        ct_file = args.output_dir / "timestamps_camera_trap.csv"
        ct_df.to_csv(ct_file, index=False)
        log.info(f"Saved {ct_file} ({len(ct_df)} rows)")
        dfs.append(ct_df)

    if "bioacoustic" in modalities_to_run:
        bio_df = extract_bioacoustic_timestamps()
        bio_file = args.output_dir / "timestamps_bioacoustic.csv"
        bio_df.to_csv(bio_file, index=False)
        log.info(f"Saved {bio_file} ({len(bio_df)} rows)")
        dfs.append(bio_df)

    if "drone" in modalities_to_run:
        drone_df = extract_drone_timestamps(campaigns=campaigns)
        drone_file = args.output_dir / "timestamps_drone.csv"
        drone_df.to_csv(drone_file, index=False)
        log.info(f"Saved {drone_file} ({len(drone_df)} rows)")
        dfs.append(drone_df)

    if "citizen_science" in modalities_to_run:
        cs_df = extract_citizen_science_timestamps(campaigns=campaigns)
        cs_file = args.output_dir / "timestamps_citizen_science.csv"
        cs_df.to_csv(cs_file, index=False)
        log.info(f"Saved {cs_file} ({len(cs_df)} rows)")
        dfs.append(cs_df)

    if not dfs:
        log.error("No data extracted")
        return

    # ---- Combine ----
    combined = combine_all_modalities(dfs)
    combined_file = args.output_dir / "timestamps_combined.csv"
    combined.to_csv(combined_file, index=False)
    log.info(f"Saved {combined_file} ({len(combined)} rows)")

    # ---- Analyze ----
    if args.analyze:
        log.info("Running ADAE analysis...")
        summary = run_adae_analysis(combined, args.output_dir)
        print("\n=== Summary ===")
        print(summary.to_string(index=False))

        log.info("Computing cross-modal correlation...")
        corr_matrices = compute_cross_modal_correlation(
            combined, args.output_dir, time_windows=args.time_windows
        )

        if args.plot and corr_matrices:
            plot_correlation_heatmap(corr_matrices, args.output_dir)

    # ---- Plot ----
    if args.plot:
        log.info("Generating plots...")
        plot_overlaid_arrival_rates(combined, args.output_dir)

    log.info("Done.")


if __name__ == "__main__":
    main()
