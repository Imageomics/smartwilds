#!/usr/bin/env python3
"""
Driver script: reads detection_config.json and runs camera_trap_detections.py
for a single camera (by key) or all cameras.

Designed for use with SLURM array jobs:
    SLURM_ARRAY_TASK_ID selects which camera to process.

Usage:
    # Run a specific camera by key
    python run_detections.py --camera-key TW01-CT02_20250630_20250703

    # Run by array index (for SLURM)
    python run_detections.py --array-index 0

    # List all cameras (dry run)
    python run_detections.py --list

    # Run all cameras sequentially
    python run_detections.py --all
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "detection_config.json")
DETECTION_SCRIPT = os.path.join(
    os.path.dirname(__file__), "bharaths_scripts", "camera_trap_detections.py"
)
OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "detection_results")


def load_config(config_path):
    with open(config_path) as f:
        return json.load(f)


def get_camera_list(config):
    """Return sorted list of (key, camera_dict) tuples, skipping cameras with 0 expected images."""
    cameras = []
    for key, cam in sorted(config["cameras"].items()):
        expected = cam.get("expected_images", 0)
        if expected == 0:
            continue
        cameras.append((key, cam))
    return cameras


def find_image_dir(cam):
    """Find the actual directory containing images, searching subdirectories."""
    base = cam["image_dir"]
    if not os.path.isdir(base):
        return None

    # Check if images are directly in the base dir
    for ext in ("*.jpg", "*.JPG", "*.jpeg", "*.JPEG"):
        import glob
        if glob.glob(os.path.join(base, ext)):
            return base

    # Search one level deep for images/ or SD*/images/ or SD*/ or chunk*/
    for root, dirs, files in os.walk(base):
        jpg_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg'))]
        if jpg_files:
            return root
        # Don't go too deep
        depth = root[len(base):].count(os.sep)
        if depth >= 3:
            dirs.clear()

    return base


def build_command(cam, camera_key, output_dir, global_config):
    """Build the command-line invocation for camera_trap_detections.py."""
    image_dir = find_image_dir(cam)
    if image_dir is None:
        return None, f"Image directory not found: {cam['image_dir']}"

    # Get geometry
    geometry = cam.get("geometry", {})
    hfov = geometry.get("hfov_deg")
    target_height = geometry.get("target_height_m", 1.0)

    # Also check top-level camera_model for HFOV lookup
    if hfov is None:
        model = cam.get("camera_model", geometry.get("camera_model", ""))
        hfov_map = {
            "GardePro T5NG": 56.5,
            "GardePro A3": 63,
            "Trail Camera G600": 120,
            "Reveal Pro 3.0": 55,
        }
        for name, val in hfov_map.items():
            if name.lower() in model.lower():
                hfov = val
                break
        if hfov is None:
            hfov = 56.5  # default

    # Get location
    location = cam.get("location", {})
    lat = location.get("latitude")
    lon = location.get("longitude")
    bearing = location.get("bearing_deg")

    if lat is None or lon is None or bearing is None:
        return None, f"Missing GPS/bearing for {camera_key}: lat={lat}, lon={lon}, bearing={bearing}"

    # Get labels from config or use defaults
    labels = ",".join(global_config.get("metadata", {}).get("bioclip_labels", [
        "white-tailed deer", "deer", "bird", "horse", "cow", "zebra",
        "giraffe", "rhinoceros", "ostrich", "human"
    ]))

    # Build CSV output path
    csv_out = os.path.join(output_dir, f"{camera_key}_detections.csv")

    cmd = [
        sys.executable, DETECTION_SCRIPT,
        "--weights", global_config["global_config"].get("yolo_weights", "yolov8x.pt"),
        "--images", image_dir,
        "--device", global_config["global_config"].get("device", "cuda:0"),
        "--conf", str(global_config["global_config"].get("confidence_threshold", 0.25)),
        "--slice-h", str(global_config["global_config"].get("slice_height", 512)),
        "--slice-w", str(global_config["global_config"].get("slice_width", 512)),
        "--ovh", str(global_config["global_config"].get("overlap_height", 0.2)),
        "--ovw", str(global_config["global_config"].get("overlap_width", 0.2)),
        "--hfov-deg", str(hfov),
        "--target-height-m", str(target_height),
        "--camera-lat", str(lat),
        "--camera-lon", str(lon),
        "--camera-bearing-deg", str(bearing),
        "--csv-out", csv_out,
        "--labels", labels,
        "--max-det-print", "0",  # suppress per-detection output in batch mode
    ]

    return cmd, None


def main():
    parser = argparse.ArgumentParser(description="Drive camera trap detections from config")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--camera-key", help="Process a specific camera by config key")
    group.add_argument("--array-index", type=int, help="Process camera at this index (for SLURM arrays)")
    group.add_argument("--list", action="store_true", help="List all cameras and exit")
    group.add_argument("--all", action="store_true", help="Process all cameras sequentially")

    parser.add_argument("--config", default=CONFIG_PATH, help="Path to detection_config.json")
    parser.add_argument("--output-dir", default=OUTPUT_BASE, help="Output directory for detection CSVs")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")

    args = parser.parse_args()

    config = load_config(args.config)
    cameras = get_camera_list(config)

    if args.list:
        print(f"{'Idx':>3}  {'Camera Key':<45}  {'Expected Images':>15}  {'Model':<20}")
        print("-" * 90)
        for i, (key, cam) in enumerate(cameras):
            model = cam.get("camera_model", cam.get("geometry", {}).get("camera_model", "unknown"))
            expected = cam.get("expected_images", "?")
            print(f"{i:>3}  {key:<45}  {expected:>15}  {model:<20}")
        print(f"\nTotal: {len(cameras)} cameras")
        total_imgs = sum(c.get("expected_images", 0) for _, c in cameras)
        print(f"Total expected images: {total_imgs:,}")
        return

    os.makedirs(args.output_dir, exist_ok=True)

    if args.all:
        targets = cameras
    elif args.camera_key:
        targets = [(k, c) for k, c in cameras if k == args.camera_key]
        if not targets:
            print(f"Camera key '{args.camera_key}' not found in config")
            sys.exit(1)
    elif args.array_index is not None:
        idx = args.array_index
        if idx < 0 or idx >= len(cameras):
            print(f"Array index {idx} out of range (0-{len(cameras)-1})")
            sys.exit(1)
        targets = [cameras[idx]]

    for key, cam in targets:
        print(f"\n{'='*70}")
        print(f"Camera: {key}")
        print(f"Site: {cam.get('site_name', 'unknown')}")
        print(f"Expected images: {cam.get('expected_images', '?')}")
        print(f"{'='*70}")

        cmd, error = build_command(cam, key, args.output_dir, config)
        if error:
            print(f"SKIP: {error}")
            continue

        if args.dry_run:
            print(f"DRY RUN: {' '.join(cmd)}")
            continue

        print(f"Running detection...")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"FAILED: {key} (exit code {result.returncode})")
        else:
            csv_out = os.path.join(args.output_dir, f"{key}_detections.csv")
            if os.path.exists(csv_out):
                # Count detections
                with open(csv_out) as f:
                    det_count = sum(1 for _ in f) - 1  # subtract header
                print(f"SUCCESS: {det_count} detections saved to {csv_out}")


if __name__ == "__main__":
    main()
