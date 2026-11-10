"""Raw-image and retained-detection inventory builders."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from .paths import ExperimentPaths, IMAGE_SUFFIXES


def build_raw_inventory(paths: ExperimentPaths) -> pd.DataFrame:
    """Scan raw camera-trap image files and record size metadata."""

    rows: list[dict[str, object]] = []
    for camera_trap_root in paths.camera_trap_dirs:
        if not camera_trap_root.exists():
            continue

        campaign = camera_trap_root.parent.name.replace("thewilds_", "")
        for dirpath, _, filenames in os.walk(camera_trap_root):
            for filename in filenames:
                if not filename.lower().endswith(IMAGE_SUFFIXES):
                    continue

                image_path = Path(dirpath) / filename
                relative_path = image_path.relative_to(camera_trap_root)
                camera = relative_path.parts[0]
                rows.append(
                    {
                        "image_path": str(image_path),
                        "campaign": campaign,
                        "camera": camera,
                        "deployment_id": f"{camera}_{campaign}",
                        "bytes": image_path.stat().st_size,
                    }
                )

    raw_inventory = pd.DataFrame(rows)
    if raw_inventory.empty:
        raise RuntimeError("No raw camera trap images were found.")
    return raw_inventory


def build_retained_detection_inventory(paths: ExperimentPaths) -> pd.DataFrame:
    """Build a unique inventory of detector-retained image paths."""

    frames: list[pd.DataFrame] = []
    for csv_path in sorted(paths.detection_dir.glob("*_detections_filtered.csv")):
        deployment_id = csv_path.name.replace("_detections_filtered.csv", "")
        detections = pd.read_csv(csv_path, usecols=["image_path"])
        unique_paths = pd.Series(
            detections["image_path"].dropna().unique(),
            name="image_path",
        )
        frames.append(
            pd.DataFrame(
                {
                    "image_path": unique_paths.astype(str),
                    "deployment_id": deployment_id,
                    "nonblank": 1,
                }
            )
        )

    if not frames:
        raise RuntimeError(
            f"No filtered detection CSVs found in {paths.detection_dir}"
        )

    return pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["deployment_id", "image_path"]
    )
