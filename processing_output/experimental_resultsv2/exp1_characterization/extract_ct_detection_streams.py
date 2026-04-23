#!/usr/bin/env python3
"""
extract_ct_detection_streams.py

Builds two additional camera-trap event streams (beyond the raw-JPG stream in
timestamps_camera_trap.csv), so Exp 1 characterization can distinguish:

  1. raw JPG       — storage/bandwidth workload   (existing, unchanged)
  2. YOLO detections — raw inference workload     (this script, _detections)
  3. filtered       — post-filter inference /     (this script, _filtered)
                      downstream coordination

Inputs:
    processing_output/detections/camera_traps/*_detections.csv
    processing_output/detections/camera_traps/*_detections_filtered.csv

Per-row event is one YOLO detection (= one bounding box in one image). Multiple
detections per image produce multiple event rows, which is the correct unit for
inference-workload characterization.

Outputs (written into the same dir as v1 Exp 1 results so export_primitives.py
can find them by the modality-name convention):
    V1_RESULTS/timestamps_camera_trap_detections.csv
    V1_RESULTS/timestamps_camera_trap_filtered.csv
    V1_RESULTS/change_points_camera_trap_{detections,filtered}_{thr}.csv

Usage:
    python extract_ct_detection_streams.py
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
DET_DIR = BASE_DIR / "processing_output" / "detections" / "camera_traps"
V1_RESULTS = BASE_DIR / "processing_output" / "experimental_results" / "exp1_cross_modal_arrival_rates" / "results"

# Import ADAE change-point helpers (same module extract_wilds_multimodal.py uses)
sys.path.insert(0, str(BASE_DIR / "documentation" / "adae_model"))
from change_points import getChangePoints, avgArrivalTimes  # noqa: E402

THRESHOLDS = [0.8, 0.95, 0.99, 0.995]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def parse_filename(path: Path) -> dict:
    """
    Parse site / site_cam / campaign from filenames like:
      TW01-CT02_20250804_20250828_detections.csv
      TW09_CT02_20250804_20250828_detections_filtered.csv  (note underscore form)
    """
    stem = path.stem  # strip .csv
    # Site_cam uses either TW##-CT## or TW##_CT## (both exist in the repo)
    m = re.match(r"^(TW\d+)[_-](CT\d+)_(\d{8})_(\d{8})_detections(?:_filtered)?$", stem)
    if not m:
        raise ValueError(f"Unparseable detection filename: {path.name}")
    site, cam, start, end = m.groups()
    return {
        "site": site,
        "site_cam": f"{site}-{cam}",
        "campaign": f"{start}_{end}",
    }


def extract_stream(suffix: str, out_name: str) -> pd.DataFrame:
    """Aggregate one detection stream into a timestamps CSV."""
    pattern = f"*_detections{suffix}.csv"
    files = sorted(DET_DIR.glob(pattern))
    log.info(f"[{out_name}] {len(files)} source CSVs")

    frames = []
    for f in files:
        try:
            meta = parse_filename(f)
        except ValueError as e:
            log.warning(f"  skip {f.name}: {e}")
            continue
        df = pd.read_csv(f, usecols=["timestamp_from_name", "camera_lat", "camera_lon"])
        df = df.rename(columns={"timestamp_from_name": "timestamp"})
        df["modality"] = f"camera_trap_{out_name}"
        df["site"] = meta["site"]
        df["site_cam"] = meta["site_cam"]
        df["campaign"] = meta["campaign"]
        df["source_file"] = f.name
        frames.append(df)

    if not frames:
        raise RuntimeError(f"No files matched {pattern}")

    combined = pd.concat(frames, ignore_index=True)
    combined["timestamp"] = pd.to_datetime(combined["timestamp"], format="ISO8601", errors="coerce")
    before = len(combined)
    combined = combined.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    if before != len(combined):
        log.warning(f"[{out_name}] dropped {before - len(combined)} rows with unparseable timestamps")

    cols = ["timestamp", "modality", "site", "site_cam", "source_file", "campaign", "camera_lat", "camera_lon"]
    combined = combined[cols]

    out_path = V1_RESULTS / f"timestamps_camera_trap_{out_name}.csv"
    combined.to_csv(out_path, index=False)
    log.info(f"[{out_name}] wrote {out_path}  ({len(combined)} events, {combined.site.nunique()} sites)")

    return combined


def run_change_points(df: pd.DataFrame, stream_name: str) -> None:
    """Same ADAE change-point logic as extract_wilds_multimodal.py, per stream."""
    if len(df) < 10:
        log.warning(f"[{stream_name}] only {len(df)} events; skipping change-point analysis")
        return

    t0 = df["timestamp"].min()
    time_df = pd.DataFrame({"time": (df["timestamp"] - t0).dt.total_seconds()})
    time_df = time_df.sort_values("time").reset_index(drop=True)

    for thr in THRESHOLDS:
        try:
            change_points_df, _ = getChangePoints(time_df, thr)
            cp = change_points_df["time"].tolist()
            cp.insert(0, 0)
            cp.append(time_df["time"].max())
            cp = sorted(set(cp))
            rates_dict = avgArrivalTimes(time_df, cp)

            out = pd.DataFrame({
                "change_point": list(rates_dict.keys()),
                "arrival_rate": list(rates_dict.values()),
            })
            out_path = V1_RESULTS / f"change_points_camera_trap_{stream_name}_{thr}.csv"
            out.to_csv(out_path, index=False)
            log.info(f"[{stream_name}] threshold={thr}: {len(cp)-2} change points → {out_path.name}")
        except Exception as e:
            log.warning(f"[{stream_name}] change-point threshold={thr} failed: {e}")


def main():
    for suffix, name in [("", "detections"), ("_filtered", "filtered")]:
        df = extract_stream(suffix=suffix, out_name=name)
        run_change_points(df, name)


if __name__ == "__main__":
    main()
