#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import export_drone_detection_csv as base


DEFAULT_OUTPUT_DIR = Path(
    "/fs/ess/PAS2136/TheWilds2025/processing_output/detections/drones"
)

CSV_COLUMNS = [
    "frame",
    "id",
    "date_time",
    "latitude_y",
    "longitude_y",
    "height_sonar(feet)",
    "compass_heading(degrees)",
    "pitch(degrees)",
    "roll(degrees)",
    "gimbal_heading(degrees)",
    "gimbal_pitch(degrees)",
    "gimbal_roll(degrees)",
    "xtl",
    "ytl",
    "xbr",
    "ybr",
    "label",
    "behaviour",
    "source",
    "mission id",
    "altitude (m)",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export simplified SmartWilds drone detection CSVs."
    )
    parser.add_argument(
        "--collection-root",
        dest="collection_roots",
        action="append",
        default=[],
        help="Collection root containing a drones directory. Can be passed multiple times.",
    )
    parser.add_argument(
        "--detection-root",
        default=base.DEFAULT_DETECTION_ROOT,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument(
        "--filename-suffix",
        default="_detections.csv",
        help="Suffix to append to each flight directory name when writing CSVs.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
    )
    return parser.parse_args()


def mission_id_for_assignment(
    flight_dir_name: str,
    assignment: base.VideoAssignment | None,
) -> str:
    if assignment is None or assignment.telemetry_log is None or assignment.telemetry_log.start_dt is None:
        return flight_dir_name
    local_start = assignment.telemetry_log.start_dt.astimezone(base.LOCAL_TZ)
    return f"{flight_dir_name}_{local_start.strftime('%Y%m%dT%H%M%S')}"


def source_label(prediction_backend: str) -> str:
    if prediction_backend == "hf_sam3":
        return "deep learning (hf_sam3)"
    return "deep learning (sam3)"


def label_for_annotation(annotation: dict, bioclip_label: str) -> str:
    if bioclip_label:
        return bioclip_label
    return str(annotation.get("category_name", "")).strip()


def build_rows_for_prediction(
    *,
    prediction_path: Path,
    source_collection_root: Path,
    detection_root: Path,
    collection_name: str,
) -> list[dict[str, str | float | int]]:
    prediction_data = base.load_json(prediction_path)
    prediction_backend = base.parse_prediction_backend(prediction_path)
    collection_detection_root = Path(detection_root) / collection_name / "detections"
    relative_prediction = prediction_path.relative_to(collection_detection_root)

    video_stem = relative_prediction.parent.name
    relative_video_parent = relative_prediction.parent.parent
    flight_dir_name = relative_prediction.parts[1]
    flight_dir = source_collection_root / "drones" / flight_dir_name

    frame_dir = Path(detection_root) / collection_name / relative_video_parent / f"{video_stem}_frames"
    frame_json = frame_dir / f"{video_stem}_annotations.json"
    source_frame_data = base.load_json(frame_json)
    source_video = base.resolve_video(source_collection_root, relative_video_parent, video_stem)

    all_videos = base.video_lookup(source_collection_root, relative_video_parent)
    assignments = base.build_video_assignments(flight_dir, all_videos)
    assignment = assignments.get(video_stem)
    mission_id = mission_id_for_assignment(flight_dir_name, assignment)

    images_by_id = {image["id"]: image for image in source_frame_data.get("images", [])}
    annotations_by_image_id: dict[int, list[dict]] = {}
    for annotation in prediction_data.get("annotations", []):
        annotations_by_image_id.setdefault(annotation["image_id"], []).append(annotation)

    rows: list[dict[str, str | float | int]] = []
    for image_id in sorted(images_by_id):
        image_info = images_by_id[image_id]
        frame_number = base.parse_frame_number(image_info["file_name"])
        telemetry_point = None
        if assignment is not None and assignment.telemetry_log is not None:
            frame_time_sec = (frame_number / source_video.fps) if source_video.fps else 0.0
            telemetry_point = assignment.telemetry_log.sample(
                assignment.video_start_ms + int(round(frame_time_sec * 1000.0))
            )

        for detection_index, annotation in enumerate(
            sorted(annotations_by_image_id.get(image_id, []), key=lambda item: item["id"]),
            start=1,
        ):
            bioclip_label, _ = base.parse_bioclip(annotation)
            x, y, width, height = annotation["bbox"]
            row_id = f"{video_stem}_{frame_number:06d}_{detection_index:03d}"
            rows.append(
                {
                    "frame": frame_number,
                    "id": row_id,
                    "date_time": "" if telemetry_point is None else telemetry_point.timestamp_local,
                    "latitude_y": "" if telemetry_point is None or telemetry_point.latitude is None else telemetry_point.latitude,
                    "longitude_y": "" if telemetry_point is None or telemetry_point.longitude is None else telemetry_point.longitude,
                    "height_sonar(feet)": "" if telemetry_point is None or telemetry_point.height_sonar_ft is None else telemetry_point.height_sonar_ft,
                    "compass_heading(degrees)": "" if telemetry_point is None or telemetry_point.heading_deg is None else telemetry_point.heading_deg,
                    "pitch(degrees)": "" if telemetry_point is None or telemetry_point.pitch_deg is None else telemetry_point.pitch_deg,
                    "roll(degrees)": "" if telemetry_point is None or telemetry_point.roll_deg is None else telemetry_point.roll_deg,
                    "gimbal_heading(degrees)": "" if telemetry_point is None or telemetry_point.gimbal_heading_deg is None else telemetry_point.gimbal_heading_deg,
                    "gimbal_pitch(degrees)": "" if telemetry_point is None or telemetry_point.gimbal_pitch_deg is None else telemetry_point.gimbal_pitch_deg,
                    "gimbal_roll(degrees)": "" if telemetry_point is None or telemetry_point.gimbal_roll_deg is None else telemetry_point.gimbal_roll_deg,
                    "xtl": x,
                    "ytl": y,
                    "xbr": x + width,
                    "ybr": y + height,
                    "label": label_for_annotation(annotation, bioclip_label),
                    "behaviour": "",
                    "source": source_label(prediction_backend),
                    "mission id": mission_id,
                    "altitude (m)": "" if telemetry_point is None or telemetry_point.altitude_m is None else telemetry_point.altitude_m,
                }
            )

    return rows


def write_csv(output_path: Path, rows: list[dict[str, str | float | int]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    collection_roots = [Path(path) for path in (args.collection_roots or base.DEFAULT_COLLECTION_ROOTS)]
    detection_root = Path(args.detection_root)

    for source_collection_root in collection_roots:
        collection_name = source_collection_root.name
        prediction_root = detection_root / collection_name / "detections" / "drones"
        if not prediction_root.exists():
            print(f"Skipping {collection_name}: no drone detections found under {prediction_root}")
            continue

        prediction_files = base.pick_prediction_files(prediction_root)
        rows_by_flight: dict[str, list[dict[str, str | float | int]]] = {}
        for prediction_path in prediction_files:
            prediction_rows = build_rows_for_prediction(
                prediction_path=prediction_path,
                source_collection_root=source_collection_root,
                detection_root=detection_root,
                collection_name=collection_name,
            )
            if not prediction_rows:
                continue
            flight_dir = prediction_path.relative_to(detection_root / collection_name / "detections").parts[1]
            rows_by_flight.setdefault(flight_dir, []).extend(prediction_rows)

        written_files = 0
        total_rows = 0
        for flight_dir, rows in sorted(rows_by_flight.items()):
            output_path = args.output_dir / f"{flight_dir}{args.filename_suffix}"
            if output_path.exists() and not args.overwrite:
                print(f"Skipping existing CSV for {flight_dir}: {output_path}")
                continue
            write_csv(output_path, rows)
            written_files += 1
            total_rows += len(rows)
            print(f"Wrote {len(rows)} rows to {output_path}")

        print(
            f"Finished {collection_name}: wrote {written_files} simplified flight CSVs "
            f"({total_rows} rows)"
        )


if __name__ == "__main__":
    main()
