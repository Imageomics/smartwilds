#!/usr/bin/env python3
"""Project drone detection boxes to approximate animal ground coordinates.

This post-processes the per-video SAM3 + BioCLIP Tree-of-Life prediction CSVs.
It joins each prediction row back to the processed drone detection CSV to recover
pose fields, then projects the bbox bottom-center ray onto a flat ground plane.

The output is intentionally provenance-heavy. Drone georeferencing is sensitive
to FOV, gimbal pitch convention, altitude source, and terrain, so rows are
statused instead of silently pretending every projection is equally trustworthy.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None


EARTH_RADIUS_M = 6_378_137.0


@dataclass(frozen=True)
class ProjectionConfig:
    pattern: str
    hfov_deg: float
    vfov_deg: float
    fallback_pitch_deg: float
    use_fallback_when_pitch_abs_lt: float
    notes: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate animal ground coordinates from drone Tree-of-Life detections."
    )
    parser.add_argument(
        "--prediction-dir",
        type=Path,
        default=Path("/fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_output_as_coco/predictions_by_video"),
        help="Directory containing per-video *.treeoflife_predictions.csv files.",
    )
    parser.add_argument(
        "--detection-dir",
        type=Path,
        default=Path("/fs/ess/PAS2136/TheWilds2025/processing_output/detections/drones"),
        help="Directory containing processed *_detections.csv files with pose metadata.",
    )
    parser.add_argument(
        "--config-csv",
        type=Path,
        required=True,
        help="Projection config CSV with FOV and pitch fallback rules.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--min-altitude-m",
        type=float,
        default=1.0,
        help="Rows below this AGL/altitude are marked invalid_altitude.",
    )
    parser.add_argument(
        "--max-ground-range-m",
        type=float,
        default=300.0,
        help="Projected ranges above this are marked out_of_range.",
    )
    parser.add_argument(
        "--min-depression-deg",
        type=float,
        default=2.0,
        help="Rows with rays too close to the horizon are marked horizon_ray.",
    )
    return parser.parse_args()


def progress(items: Iterable, **kwargs):
    if tqdm is None:
        return items
    return tqdm(items, **kwargs)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def load_projection_config(path: Path) -> list[ProjectionConfig]:
    rows = read_csv(path)
    configs = []
    for row in rows:
        if row.get("enabled", "1").strip() in {"0", "false", "False", "no"}:
            continue
        configs.append(
            ProjectionConfig(
                pattern=row["pattern"].strip(),
                hfov_deg=float(row["hfov_deg"]),
                vfov_deg=float(row["vfov_deg"]),
                fallback_pitch_deg=float(row["fallback_pitch_deg"]),
                use_fallback_when_pitch_abs_lt=float(row["use_fallback_when_pitch_abs_lt"]),
                notes=row.get("notes", "").strip(),
            )
        )
    return configs


def choose_projection_config(configs: list[ProjectionConfig], prediction_name: str, flight: str) -> ProjectionConfig | None:
    key = f"{prediction_name} {flight}".lower()
    matches = [cfg for cfg in configs if cfg.pattern.lower() in key]
    if not matches:
        return None
    return max(matches, key=lambda cfg: len(cfg.pattern))


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


def norm_bearing(deg: float) -> float:
    return deg % 360.0


def project_gps(lat: float, lon: float, distance_m: float, bearing_deg: float) -> tuple[float, float]:
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    bearing = math.radians(bearing_deg)
    angular_dist = distance_m / EARTH_RADIUS_M
    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_dist)
        + math.cos(lat1) * math.sin(angular_dist) * math.cos(bearing)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angular_dist) * math.cos(lat1),
        math.cos(angular_dist) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


def detection_key(row: dict[str, str]) -> tuple[str, str]:
    return row.get("detection_csv", ""), row.get("row_index", "")


def load_detection_rows(detection_dir: Path, detection_csv: str) -> list[dict[str, str]]:
    path = detection_dir / detection_csv
    if not path.exists():
        return []
    return read_csv(path)


def build_detection_lookup(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    by_index = {}
    by_id = {}
    for idx, row in enumerate(rows):
        by_index[str(idx)] = row
        if row.get("id"):
            by_id[row["id"]] = row
    return by_index, by_id


def select_altitude_m(det: dict[str, str], pred: dict[str, str]) -> tuple[float | None, str]:
    sonar_ft = float_or_none(det.get("height_sonar(feet)"))
    if sonar_ft is not None and sonar_ft > 1.0:
        return sonar_ft * 0.3048, "height_sonar_feet"
    alt_m = float_or_none(det.get("altitude (m)"))
    if alt_m is not None:
        return alt_m, "altitude_m_detection_csv"
    alt_m = float_or_none(pred.get("altitude_m"))
    if alt_m is not None:
        return alt_m, "altitude_m_treeoflife"
    return None, ""


def select_pose(det: dict[str, str], cfg: ProjectionConfig) -> tuple[float | None, float | None, str]:
    heading = float_or_none(det.get("gimbal_heading(degrees)"))
    if heading is None:
        heading = float_or_none(det.get("compass_heading(degrees)"))
    pitch = float_or_none(det.get("gimbal_pitch(degrees)"))
    pitch_source = "gimbal_pitch"
    if pitch is None:
        pitch = float_or_none(det.get("pitch(degrees)"))
        pitch_source = "body_pitch"
    if pitch is not None and abs(pitch) < cfg.use_fallback_when_pitch_abs_lt:
        pitch = cfg.fallback_pitch_deg
        pitch_source = f"fallback_pitch_abs_lt_{cfg.use_fallback_when_pitch_abs_lt:g}"
    return heading, pitch, pitch_source


def project_row(
    pred: dict[str, str],
    det: dict[str, str] | None,
    cfg: ProjectionConfig | None,
    args: argparse.Namespace,
) -> dict[str, str]:
    out = dict(pred)
    added = {
        "animal_lat_projected": "",
        "animal_lon_projected": "",
        "animal_ground_range_m": "",
        "animal_bearing_deg": "",
        "animal_offset_east_m": "",
        "animal_offset_north_m": "",
        "pixel_horizontal_angle_deg": "",
        "pixel_vertical_angle_deg": "",
        "ray_depression_deg": "",
        "drone_altitude_used_m": "",
        "drone_altitude_source": "",
        "drone_heading_used_deg": "",
        "drone_pitch_used_deg": "",
        "drone_pitch_source": "",
        "drone_hfov_deg": "",
        "drone_vfov_deg": "",
        "drone_georef_status": "",
        "drone_georef_note": "",
        "drone_georef_config_notes": "",
    }
    out.update(added)

    if cfg is None:
        out["drone_georef_status"] = "missing_projection_config"
        return out
    if det is None:
        out["drone_georef_status"] = "missing_detection_pose"
        return out

    lat = float_or_none(pred.get("latitude_y")) or float_or_none(det.get("latitude_y"))
    lon = float_or_none(pred.get("longitude_y")) or float_or_none(det.get("longitude_y"))
    if lat is None or lon is None:
        out["drone_georef_status"] = "missing_drone_gps"
        return out

    altitude_m, altitude_source = select_altitude_m(det, pred)
    if altitude_m is None or altitude_m < args.min_altitude_m:
        out["drone_georef_status"] = "invalid_altitude"
        out["drone_altitude_used_m"] = "" if altitude_m is None else f"{altitude_m:.3f}"
        out["drone_altitude_source"] = altitude_source
        return out

    heading, pitch_deg, pitch_source = select_pose(det, cfg)
    if heading is None or pitch_deg is None:
        out["drone_georef_status"] = "missing_pose"
        return out

    image_width = float_or_none(pred.get("image_width"))
    image_height = float_or_none(pred.get("image_height"))
    bbox_x = float_or_none(pred.get("bbox_x"))
    bbox_y = float_or_none(pred.get("bbox_y"))
    bbox_w = float_or_none(pred.get("bbox_width"))
    bbox_h = float_or_none(pred.get("bbox_height"))
    if None in {image_width, image_height, bbox_x, bbox_y, bbox_w, bbox_h}:
        out["drone_georef_status"] = "invalid_bbox"
        return out

    u = bbox_x + bbox_w / 2.0
    v = bbox_y + bbox_h
    hfov_rad = math.radians(cfg.hfov_deg)
    vfov_rad = math.radians(cfg.vfov_deg)
    fx = (image_width / 2.0) / math.tan(hfov_rad / 2.0)
    fy = (image_height / 2.0) / math.tan(vfov_rad / 2.0)
    h_angle = math.degrees(math.atan((u - image_width / 2.0) / fx))
    v_angle = math.degrees(math.atan((v - image_height / 2.0) / fy))

    # DJI uses -90 deg as nadir and 0 deg as horizon. For sources with missing
    # or body-like pitch, the config can force a fallback negative pitch.
    depression = -pitch_deg + v_angle
    bearing = norm_bearing(heading + h_angle)

    out.update(
        {
            "pixel_horizontal_angle_deg": f"{h_angle:.3f}",
            "pixel_vertical_angle_deg": f"{v_angle:.3f}",
            "ray_depression_deg": f"{depression:.3f}",
            "drone_altitude_used_m": f"{altitude_m:.3f}",
            "drone_altitude_source": altitude_source,
            "drone_heading_used_deg": f"{norm_bearing(heading):.3f}",
            "drone_pitch_used_deg": f"{pitch_deg:.3f}",
            "drone_pitch_source": pitch_source,
            "drone_hfov_deg": f"{cfg.hfov_deg:.3f}",
            "drone_vfov_deg": f"{cfg.vfov_deg:.3f}",
            "drone_georef_config_notes": cfg.notes,
        }
    )

    if depression <= args.min_depression_deg:
        out["drone_georef_status"] = "horizon_ray"
        out["drone_georef_note"] = f"ray_depression_deg<={args.min_depression_deg:g}"
        return out
    if depression >= 89.5:
        # Near-nadir: clamp just below vertical to avoid tan(90) instability.
        depression = 89.5

    ground_range_m = altitude_m / math.tan(math.radians(depression))
    if ground_range_m < 0:
        out["drone_georef_status"] = "behind_camera"
        return out

    target_lat, target_lon = project_gps(lat, lon, ground_range_m, bearing)
    east = ground_range_m * math.sin(math.radians(bearing))
    north = ground_range_m * math.cos(math.radians(bearing))
    status = "ok" if ground_range_m <= args.max_ground_range_m else "out_of_range"
    note = "" if status == "ok" else f"animal_ground_range_m>{args.max_ground_range_m:g}"
    out.update(
        {
            "animal_lat_projected": f"{target_lat:.8f}",
            "animal_lon_projected": f"{target_lon:.8f}",
            "animal_ground_range_m": f"{ground_range_m:.3f}",
            "animal_bearing_deg": f"{bearing:.3f}",
            "animal_offset_east_m": f"{east:.3f}",
            "animal_offset_north_m": f"{north:.3f}",
            "drone_georef_status": status,
            "drone_georef_note": note,
        }
    )
    return out


def process_file(
    pred_csv: Path,
    out_csv: Path,
    detection_dir: Path,
    configs: list[ProjectionConfig],
    args: argparse.Namespace,
    detection_cache: dict[str, tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]],
) -> dict[str, int]:
    if out_csv.exists() and not args.overwrite:
        return {"skipped_existing": 1}
    rows = read_csv(pred_csv)
    if not rows:
        return {"rows": 0}
    cfg = choose_projection_config(configs, pred_csv.name, rows[0].get("flight", ""))
    counts: dict[str, int] = {"rows": 0}
    out_rows = []
    for row in rows:
        det = None
        detection_csv = row.get("detection_csv", "")
        if detection_csv:
            if detection_csv not in detection_cache:
                det_rows = load_detection_rows(detection_dir, detection_csv)
                detection_cache[detection_csv] = build_detection_lookup(det_rows)
            by_index, by_id = detection_cache[detection_csv]
            det = by_index.get(row.get("row_index", "")) or by_id.get(row.get("detection_id", ""))
        projected = project_row(row, det, cfg, args)
        status = projected.get("drone_georef_status", "")
        counts["rows"] += 1
        counts[status] = counts.get(status, 0) + 1
        out_rows.append(projected)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(out_rows[0].keys())
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)
    return counts


def main() -> int:
    args = parse_args()
    configs = load_projection_config(args.config_csv)
    files = sorted(args.prediction_dir.glob("*.treeoflife_predictions.csv"))
    if not files:
        raise FileNotFoundError(f"No prediction CSVs found under {args.prediction_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    detection_cache: dict[str, tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]] = {}

    summaries = {}
    totals: dict[str, int] = {}
    for pred_csv in progress(files, desc="Projecting drone detections", unit="file"):
        out_csv = args.output_dir / pred_csv.name.replace(".treeoflife_predictions.csv", ".drone_geolocated.csv")
        counts = process_file(pred_csv, out_csv, args.detection_dir, configs, args, detection_cache)
        summaries[pred_csv.name] = counts
        for key, value in counts.items():
            totals[key] = totals.get(key, 0) + value

    with (args.output_dir / "drone_geolocation_summary.json").open("w", encoding="utf-8") as handle:
        json.dump({"totals": totals, "files": summaries}, handle, indent=2)
    with (args.output_dir / "drone_geolocation_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["file"] + sorted({k for c in summaries.values() for k in c})
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for file_name, counts in summaries.items():
            row = {"file": file_name}
            row.update(counts)
            writer.writerow(row)

    print(f"Wrote drone geolocation outputs to: {args.output_dir}")
    print(f"Totals: {totals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
