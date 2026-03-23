#!/usr/bin/env python3
"""
Driver: discover all drone videos and run drone_video_detections.py on each.

Usage:
    python run_drone_detections.py --list          # List all videos
    python run_drone_detections.py --array-index 0  # Process video at index (for SLURM)
    python run_drone_detections.py --all            # Process all sequentially
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
DETECTION_SCRIPT = Path(__file__).parent / "drone_video_detections.py"
WEIGHTS = BASE_DIR / "documentation/annotation_pipeline/camera_traps/yolov8x.pt"
OUTPUT_DIR = BASE_DIR / "processing_output" / "detections" / "drones"

# Load BioCLIP labels from camera trap config
CONFIG_PATH = BASE_DIR / "documentation/annotation_pipeline/camera_traps/detection_config.json"


def discover_videos():
    """Find all drone videos across all campaigns."""
    videos = []
    campaigns = [
        "thewilds_20250630_20250703",
        "thewilds_20250804_20250828",
        "thewilds_20250908_20250908",
    ]

    for campaign in campaigns:
        drone_dir = BASE_DIR / campaign / "drones"
        if not drone_dir.exists():
            continue

        for mission_dir in sorted(drone_dir.iterdir()):
            if not mission_dir.is_dir():
                continue

            # Look for videos in videos/ or video_files/
            for vid_subdir in ["videos", "video_files"]:
                vid_dir = mission_dir / vid_subdir
                if not vid_dir.exists():
                    continue

                for vid_file in sorted(vid_dir.iterdir()):
                    if vid_file.suffix.lower() in (".mp4", ".mov"):
                        size_gb = vid_file.stat().st_size / (1024**3)
                        videos.append({
                            "path": str(vid_file),
                            "filename": vid_file.name,
                            "mission": mission_dir.name,
                            "campaign": campaign,
                            "size_gb": size_gb,
                        })

    return videos


def get_labels():
    """Load BioCLIP labels from detection config."""
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return ",".join(config["metadata"]["bioclip_labels"])
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Drive drone video detections")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--array-index", type=int)
    group.add_argument("--all", action="store_true")

    parser.add_argument("--frame-interval", type=int, default=30,
                        help="Extract every Nth frame (default: 30)")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    videos = discover_videos()

    if args.list:
        print(f"{'Idx':>3}  {'Mission':<25}  {'Video':<20}  {'Size':>6}  Campaign")
        print("-" * 90)
        total_gb = 0
        for i, v in enumerate(videos):
            print(f"{i:>3}  {v['mission']:<25}  {v['filename']:<20}  {v['size_gb']:>5.1f}G  {v['campaign']}")
            total_gb += v["size_gb"]

        est_frames = sum(v["size_gb"] * 300 for v in videos)  # rough estimate
        print(f"\nTotal: {len(videos)} videos, {total_gb:.1f} GB")
        print(f"Estimated frames at 1fps: ~{int(est_frames)} frames")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    labels = get_labels()

    if args.all:
        targets = list(enumerate(videos))
    else:
        idx = args.array_index
        if idx < 0 or idx >= len(videos):
            print(f"Index {idx} out of range (0-{len(videos)-1})")
            sys.exit(1)
        targets = [(idx, videos[idx])]

    for idx, vid in targets:
        mission = vid["mission"]
        filename = vid["filename"]
        stem = os.path.splitext(filename)[0]
        csv_out = OUTPUT_DIR / f"{mission}_{stem}_detections.csv"

        print(f"\n{'='*60}")
        print(f"[{idx}] {mission}/{filename} ({vid['size_gb']:.1f} GB)")
        print(f"{'='*60}")

        cmd = [
            sys.executable, str(DETECTION_SCRIPT),
            "--video", vid["path"],
            "--weights", str(WEIGHTS),
            "--device", "cuda:0",
            "--frame-interval", str(args.frame_interval),
            "--csv-out", str(csv_out),
            "--labels", labels,
        ]

        if args.dry_run:
            print(f"DRY RUN: {' '.join(cmd[:6])} ...")
            continue

        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"FAILED: {mission}/{filename}")
        else:
            if csv_out.exists():
                lines = sum(1 for _ in open(csv_out)) - 1
                print(f"SUCCESS: {lines} detections → {csv_out}")


if __name__ == "__main__":
    main()
