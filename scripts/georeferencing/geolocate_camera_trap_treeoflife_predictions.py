#!/usr/bin/env python3
"""Estimate animal GPS positions from camera-trap detection boxes.

This is a thin post-processing wrapper around the pinhole geometry used by
Imageomics/camera-trap-geolocation. It expects the SAM3 + BioCLIP Tree-of-Life
prediction CSVs produced for SmartWilds camera traps.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None


# Optional: a checkout of Imageomics/camera-trap-geolocation (its src/ dir).
EXTERNAL_REPO = Path(os.environ.get("CAMERA_TRAP_GEOLOCATION_SRC", ""))
if EXTERNAL_REPO.name and EXTERNAL_REPO.exists():
    sys.path.insert(0, str(EXTERNAL_REPO))

try:
    from camera_trap_geolocation.geometry import estimate_distance_and_angle, project_gps
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Could not import the Imageomics camera-trap-geolocation geometry module. "
        "Install it, or set CAMERA_TRAP_GEOLOCATION_SRC to the src/ directory of a checkout."
    ) from exc


@dataclass(frozen=True)
class CameraConfig:
    collection: str
    camera_id: str
    path_contains: str
    camera_lat: float
    camera_lon: float
    hfov_deg: float
    bearing_deg: float
    target_height_m: float
    config_source: str
    notes: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Geolocate camera-trap detection boxes using camera GPS, bearing, and HFOV."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing per-camera Tree-of-Life prediction CSVs.",
    )
    parser.add_argument(
        "--config-csv",
        type=Path,
        required=True,
        help="Camera geolocation config CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory for geolocated CSVs and summary files.",
    )
    parser.add_argument(
        "--top1-score-min",
        type=float,
        default=None,
        help="Optional minimum top1_score to geolocate.",
    )
    parser.add_argument(
        "--rank",
        default=None,
        help="Optional Tree-of-Life rank filter, e.g. species, genus, family.",
    )
    parser.add_argument(
        "--max-distance-m",
        type=float,
        default=500.0,
        help="Flag estimates beyond this distance as out_of_range but still write them.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output CSVs.",
    )
    return parser.parse_args()


def load_config(path: Path) -> list[CameraConfig]:
    configs: list[CameraConfig] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {
            "collection",
            "camera_id",
            "camera_lat",
            "camera_lon",
            "hfov_deg",
            "bearing_deg",
            "target_height_m",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing required config columns: {sorted(missing)}")
        for row in reader:
            if row.get("enabled", "1").strip() in {"0", "false", "False", "no"}:
                continue
            configs.append(
                CameraConfig(
                    collection=row["collection"].strip(),
                    camera_id=row["camera_id"].strip(),
                    path_contains=row.get("path_contains", "").strip(),
                    camera_lat=float(row["camera_lat"]),
                    camera_lon=float(row["camera_lon"]),
                    hfov_deg=float(row["hfov_deg"]),
                    bearing_deg=float(row["bearing_deg"]) % 360.0,
                    target_height_m=float(row["target_height_m"]),
                    config_source=row.get("config_source", "").strip(),
                    notes=row.get("notes", "").strip(),
                )
            )
    return configs


def iter_prediction_csvs(input_dir: Path) -> list[Path]:
    return sorted(input_dir.glob("*/*/*.treeoflife_predictions.csv"))


def camera_from_csv_path(csv_path: Path) -> tuple[str, str]:
    # Expected layout: predictions/<collection>/<camera_id>/<file>.csv
    camera_id = csv_path.parent.name
    collection = csv_path.parent.parent.name
    return collection, camera_id


def choose_config(
    configs: list[CameraConfig], collection: str, camera_id: str, frame_path: str
) -> CameraConfig | None:
    candidates = [
        c for c in configs if c.collection == collection and c.camera_id == camera_id
    ]
    if not candidates:
        return None

    matching = [
        c for c in candidates if not c.path_contains or c.path_contains in frame_path
    ]
    if not matching:
        return None

    # Prefer the most specific path rule.
    return max(matching, key=lambda c: len(c.path_contains))


def float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if math.isnan(parsed):
        return None
    return parsed


def should_skip(row: dict[str, str], args: argparse.Namespace) -> bool:
    if args.rank and row.get("rank", "").strip().lower() != args.rank.lower():
        return True
    if args.top1_score_min is not None:
        score = float_or_none(row.get("top1_score"))
        if score is None or score < args.top1_score_min:
            return True
    return False


def geolocate_row(
    row: dict[str, str],
    cfg: CameraConfig,
    max_distance_m: float,
) -> dict[str, str]:
    image_width = int(float(row["image_width"]))
    image_height = int(float(row["image_height"]))
    x_min = float(row["bbox_x"])
    y_min = float(row["bbox_y"])
    x_max = x_min + float(row["bbox_width"])
    y_max = y_min + float(row["bbox_height"])

    distance_m, angle_deg = estimate_distance_and_angle(
        image_width=image_width,
        image_height=image_height,
        x_min=x_min,
        y_min=y_min,
        x_max=x_max,
        y_max=y_max,
        hfov_deg=cfg.hfov_deg,
        real_height_m=cfg.target_height_m,
    )
    absolute_bearing = (cfg.bearing_deg + angle_deg) % 360.0

    status = "ok"
    note = ""
    animal_lat = ""
    animal_lon = ""
    if not math.isfinite(distance_m):
        status = "invalid_bbox"
        note = "bbox height was zero or invalid"
    else:
        animal_lat_f, animal_lon_f = project_gps(
            cfg.camera_lat, cfg.camera_lon, distance_m, absolute_bearing
        )
        animal_lat = f"{animal_lat_f:.8f}"
        animal_lon = f"{animal_lon_f:.8f}"
        if distance_m > max_distance_m:
            status = "out_of_range"
            note = f"distance_m>{max_distance_m:g}; check bbox/height assumption"

    row.update(
        {
            "camera_lat": f"{cfg.camera_lat:.8f}",
            "camera_lon": f"{cfg.camera_lon:.8f}",
            "camera_bearing_deg": f"{cfg.bearing_deg:.3f}",
            "camera_hfov_deg": f"{cfg.hfov_deg:.3f}",
            "target_height_m": f"{cfg.target_height_m:.3f}",
            "animal_distance_m": f"{distance_m:.3f}" if math.isfinite(distance_m) else "",
            "animal_angle_deg": f"{angle_deg:.3f}",
            "animal_absolute_bearing_deg": f"{absolute_bearing:.3f}",
            "animal_lat": animal_lat,
            "animal_lon": animal_lon,
            "geolocation_status": status,
            "geolocation_note": note,
            "geolocation_config_source": cfg.config_source,
            "geolocation_config_notes": cfg.notes,
        }
    )
    return row


def process_csv(
    csv_path: Path,
    output_csv: Path,
    configs: list[CameraConfig],
    args: argparse.Namespace,
) -> dict[str, int]:
    collection, camera_id = camera_from_csv_path(csv_path)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if output_csv.exists() and not args.overwrite:
        return {"skipped_existing": 1}

    counts = {
        "rows": 0,
        "geolocated": 0,
        "filtered": 0,
        "missing_config": 0,
        "invalid_bbox": 0,
        "out_of_range": 0,
    }

    extra_fields = [
        "camera_lat",
        "camera_lon",
        "camera_bearing_deg",
        "camera_hfov_deg",
        "target_height_m",
        "animal_distance_m",
        "animal_angle_deg",
        "animal_absolute_bearing_deg",
        "animal_lat",
        "animal_lon",
        "geolocation_status",
        "geolocation_note",
        "geolocation_config_source",
        "geolocation_config_notes",
    ]

    with csv_path.open(newline="", encoding="utf-8-sig") as in_handle:
        reader = csv.DictReader(in_handle)
        if reader.fieldnames is None:
            raise ValueError(f"No header found in {csv_path}")
        fieldnames = list(reader.fieldnames) + [
            field for field in extra_fields if field not in reader.fieldnames
        ]

        with output_csv.open("w", newline="", encoding="utf-8") as out_handle:
            writer = csv.DictWriter(out_handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                counts["rows"] += 1
                if should_skip(row, args):
                    counts["filtered"] += 1
                    continue

                cfg = choose_config(
                    configs, collection, camera_id, row.get("frame_path", "")
                )
                if cfg is None:
                    counts["missing_config"] += 1
                    row.update(
                        {
                            "geolocation_status": "missing_config",
                            "geolocation_note": f"no config for {collection}/{camera_id}",
                        }
                    )
                else:
                    row = geolocate_row(row, cfg, args.max_distance_m)
                    counts["geolocated"] += 1
                    if row["geolocation_status"] in counts:
                        counts[row["geolocation_status"]] += 1

                writer.writerow(row)

    return counts


def progress(items: Iterable[Path], **kwargs):
    if tqdm is None:
        return items
    return tqdm(items, **kwargs)


def main() -> int:
    args = parse_args()
    configs = load_config(args.config_csv)
    csvs = iter_prediction_csvs(args.input_dir)
    if not csvs:
        raise FileNotFoundError(f"No Tree-of-Life prediction CSVs found under {args.input_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = {}
    totals: dict[str, int] = {}

    for csv_path in progress(csvs, desc="Geolocating camera CSVs", unit="file"):
        rel = csv_path.relative_to(args.input_dir)
        out_csv = args.output_dir / rel
        out_csv = out_csv.with_name(out_csv.name.replace(".treeoflife_predictions.csv", ".geolocated.csv"))
        counts = process_csv(csv_path, out_csv, configs, args)
        summaries[str(rel)] = counts
        for key, value in counts.items():
            totals[key] = totals.get(key, 0) + value

    with (args.output_dir / "geolocation_summary.json").open("w", encoding="utf-8") as handle:
        json.dump({"totals": totals, "files": summaries}, handle, indent=2)

    with (args.output_dir / "geolocation_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["file"] + sorted({k for counts in summaries.values() for k in counts})
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for file_name, counts in summaries.items():
            row = {"file": file_name}
            row.update(counts)
            writer.writerow(row)

    print(f"Wrote geolocated CSVs to: {args.output_dir}")
    print(f"Totals: {totals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
