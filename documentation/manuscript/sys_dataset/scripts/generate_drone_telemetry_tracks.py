#!/usr/bin/env python3
"""Build transparent, map-aligned drone tracks from the original flight telemetry."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.patches import FancyArrowPatch


ROOT = Path("/fs/ess/PAS2136/TheWilds2025")
OUT = ROOT / "documentation/manuscript/sys_dataset/figures/drone_telemetry_tracks"

# This is the geographic extent of the current 1564 x 1044 deployment-map
# canvas. It preserves the existing image registration while allowing the
# overlay to remain fully transparent.
CANVAS_WIDTH = 1564
CANVAS_HEIGHT = 1044
WEST, EAST = -81.7486, -81.7244
SOUTH, NORTH = 39.8273, 39.8390


def valid_point(lat: object, lon: object) -> tuple[float, float] | None:
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(lat_f) and math.isfinite(lon_f)):
        return None
    if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
        return None
    # The deployment footprint is intentionally broader than the plotted map,
    # but filters valid-yet-unrelated controller and sentinel coordinates.
    if not (39.80 <= lat_f <= 39.87 and -81.78 <= lon_f <= -81.69):
        return None
    return lat_f, lon_f


def point_distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat_scale = 111_320.0
    lon_scale = lat_scale * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot((a[0] - b[0]) * lat_scale, (a[1] - b[1]) * lon_scale)


def simplify(points: list[tuple[float, float]], min_separation_m: float = 1.25) -> list[tuple[float, float]]:
    """Drop GPS jitter while retaining the sampled flight trajectory."""
    if not points:
        return []
    kept = [points[0]]
    for point in points[1:]:
        if point_distance_m(kept[-1], point) >= min_separation_m:
            kept.append(point)
    if len(kept) > 1 and kept[-1] != points[-1]:
        kept.append(points[-1])
    return kept


def split_on_jump(points: list[tuple[float, float]], max_jump_m: float = 85.0) -> list[list[tuple[float, float]]]:
    """Do not draw a line across occasional logging gaps or GPS outliers."""
    if not points:
        return []
    segments = [[points[0]]]
    for point in points[1:]:
        if point_distance_m(segments[-1][-1], point) > max_jump_m:
            segments.append([point])
        else:
            segments[-1].append(point)
    return [segment for segment in segments if len(segment) >= 2]


def smooth_for_rendering(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Apply a light five-point average for a calmer visual line, not data export."""
    if len(points) < 5:
        return points
    smoothed = [points[0], points[1]]
    for index in range(2, len(points) - 2):
        window = points[index - 2 : index + 3]
        smoothed.append((
            sum(point[0] for point in window) / len(window),
            sum(point[1] for point in window) / len(window),
        ))
    return smoothed + [points[-2], points[-1]]


def direction_arrow(points: list[tuple[float, float]], fraction: float = 0.62) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """Choose one unobtrusive, direction-bearing segment from a flight path."""
    if len(points) < 3:
        return None
    distances = [point_distance_m(a, b) for a, b in zip(points, points[1:])]
    total = sum(distances)
    if total < 60:
        return None
    target = total * fraction
    travelled = 0.0
    start_index = 0
    for index, distance in enumerate(distances):
        travelled += distance
        if travelled >= target:
            start_index = index
            break
    end_index = start_index + 1
    while end_index < len(points) - 1 and point_distance_m(points[start_index], points[end_index]) < 14:
        end_index += 1
    if point_distance_m(points[start_index], points[end_index]) < 5:
        return None
    return points[start_index], points[end_index]


def parrot_track(path: Path) -> list[tuple[float, float]]:
    payload = json.loads(path.read_text())
    headers = payload.get("details_headers", [])
    rows = payload.get("details_data", [])
    try:
        lat_index = headers.index("product_gps_latitude")
        lon_index = headers.index("product_gps_longitude")
    except ValueError:
        return []
    points = []
    for row in rows:
        if len(row) > max(lat_index, lon_index):
            point = valid_point(row[lat_index], row[lon_index])
            if point:
                points.append(point)
    return points


def whitespace_dji_track(path: Path) -> list[tuple[float, float]]:
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if not lines:
        return []
    headers = lines[0].split()
    lat_index, lon_index = headers.index("latitude"), headers.index("longtitude")
    points = []
    for line in lines[1:]:
        fields = line.split()
        if len(fields) > max(lat_index, lon_index):
            point = valid_point(fields[lat_index], fields[lon_index])
            if point:
                points.append(point)
    return points


def airdata_track(path: Path) -> list[tuple[float, float]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            point
            for row in reader
            if (point := valid_point(row.get("latitude"), row.get("longitude")))
        ]


def tracks() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for metadata in sorted((ROOT / "thewilds_20250630_20250703/drones").glob("*/metadata/*.json")):
        points = parrot_track(metadata)
        if points:
            records.append(
                {
                    "id": f"{metadata.parent.parent.name}:{metadata.stem}",
                    "date": metadata.parent.parent.name[:8],
                    "platform": "Parrot Anafi",
                    "source": str(metadata),
                    "points": points,
                }
            )
    for metadata in sorted((ROOT / "thewilds_20250804_20250828/drones").glob("20250818_parrot_*/metadata/*.json")):
        points = parrot_track(metadata)
        if points:
            records.append(
                {
                    "id": f"{metadata.parent.parent.name}:{metadata.stem}",
                    "date": metadata.parent.parent.name[:8],
                    "platform": "Parrot Anafi",
                    "source": str(metadata),
                    "points": points,
                }
            )

    aug11 = ROOT / "thewilds_20250804_20250828/drones/20250811_DJI_01/metadata/ExportCSV_2025-08-11_[10-29-13].csv"
    records.append(
        {
            "id": "20250811_DJI_01",
            "date": "2025-08-11",
            "platform": "DJI",
            "source": str(aug11),
            "points": whitespace_dji_track(aug11),
        }
    )
    for metadata in sorted((ROOT / "thewilds_20250908_20250908/drones").glob("*/metadata/*-Airdata.csv")):
        records.append(
            {
                "id": metadata.parent.parent.name,
                "date": "2025-09-08",
                "platform": "DJI Air",
                "source": str(metadata),
                "points": airdata_track(metadata),
            }
        )
    return [record for record in records if record["points"]]


def geojson(records: Iterable[dict[str, object]]) -> dict[str, object]:
    features = []
    for record in records:
        points = record["points"]
        assert isinstance(points, list)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    key: value
                    for key, value in record.items()
                    if key not in {"points", "source"}
                }
                | {"source_file": record["source"], "raw_point_count": len(points)},
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [[lon, lat] for lat, lon in segment]
                        for segment in split_on_jump(simplify(points))
                    ],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = tracks()
    if len(records) != 14:
        raise RuntimeError(f"Expected 14 telemetry-bearing flights, found {len(records)}")

    (OUT / "drone_flight_tracks.geojson").write_text(json.dumps(geojson(records), indent=2) + "\n")
    manifest = []
    for record in records:
        points = record["points"]
        assert isinstance(points, list)
        manifest.append(
            {
                **{key: value for key, value in record.items() if key != "points"},
                "raw_point_count": len(points),
                "plotted_point_count": sum(len(segment) for segment in split_on_jump(simplify(points))),
                "latitude_min": min(point[0] for point in points),
                "latitude_max": max(point[0] for point in points),
                "longitude_min": min(point[1] for point in points),
                "longitude_max": max(point[1] for point in points),
            }
        )
    (OUT / "drone_flight_tracks_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # Match the placement canvas of the supplied deployment map precisely.
    dpi = 200
    fig = plt.figure(figsize=(CANVAS_WIDTH / dpi, CANVAS_HEIGHT / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(WEST, EAST)
    ax.set_ylim(SOUTH, NORTH)
    ax.set_axis_off()
    for record in records:
        points = record["points"]
        assert isinstance(points, list)
        for segment in split_on_jump(simplify(points)):
            rendered_segment = smooth_for_rendering(segment)
            ax.plot(
                [point[1] for point in rendered_segment],
                [point[0] for point in rendered_segment],
                color="#e63b3b",
                linewidth=1.55,
                alpha=0.82,
                solid_capstyle="round",
                solid_joinstyle="round",
                antialiased=True,
            )
            arrow = direction_arrow(rendered_segment)
            if arrow:
                start, end = arrow
                marker = FancyArrowPatch(
                    (start[1], start[0]),
                    (end[1], end[0]),
                    arrowstyle="Simple,tail_width=0.22,head_width=0.72,head_length=0.82",
                    mutation_scale=10,
                    linewidth=1.15,
                    facecolor="#e63b3b",
                    edgecolor="#e63b3b",
                    alpha=0.98,
                    zorder=4,
                )
                marker.set_path_effects([
                    path_effects.Stroke(linewidth=3.1, foreground="white"),
                    path_effects.Normal(),
                ])
                ax.add_patch(marker)
    fig.savefig(OUT / "drone_flight_tracks_overlay.png", transparent=True, dpi=dpi, pad_inches=0)
    fig.savefig(OUT / "drone_flight_tracks_overlay.svg", transparent=True, format="svg", pad_inches=0)
    plt.close(fig)

    (OUT / "README.md").write_text(
        "# Drone flight tracks\n\n"
        "This directory contains a transparent overlay of recorded drone flight paths for the "
        "SmartWilds deployment map. The overlay is derived from original aircraft telemetry, "
        "not from detection coordinates or manual tracing.\n\n"
        "## Files\n\n"
        "- `drone_flight_tracks_overlay.png`: transparent 1564 x 1044 px overlay for the existing deployment figure.\n"
        "- `drone_flight_tracks_overlay.svg`: equivalent editable vector overlay.\n"
        "- `drone_flight_tracks.geojson`: simplified, map-coordinate flight paths.\n"
        "- `drone_flight_tracks_manifest.json`: source-file and point-count provenance for every plotted flight.\n\n"
        "## Scope and method\n\n"
        "Fourteen flights have usable aircraft GPS telemetry: nine Parrot Anafi mission logs (July 1, July 3, and August 18), "
        "one August 11 DJI export, and four September 8 DJI AirData logs. Coordinates are retained only when finite, valid WGS84, "
        "and within the deployment area. Neighboring points closer than 1.25 m are omitted solely to reduce GPS jitter in the figure; "
        "gaps or jumps over 85 m are not connected. The rendered line receives a light five-point smoothing pass only; exported GeoJSON remains unsmoothed. One compact, white-haloed arrow at 62% of each plotted segment indicates travel direction. The August 25 Parrot sessions have no usable aircraft-GPS stream and are not shown.\n\n"
        "The overlay uses the geographic extent registered to the supplied 1564 x 1044 deployment-map canvas: "
        f"{WEST:.4f} to {EAST:.4f} longitude and {SOUTH:.4f} to {NORTH:.4f} latitude.\n"
    )


if __name__ == "__main__":
    main()
