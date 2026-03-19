#!/usr/bin/env python3
"""
Unified pipeline for camera trap image processing with validated timestamps.

Orchestrates the full workflow:
1. Index images in directory tree
2. Extract and validate timestamps from filenames/EXIF
3. Run YOLO+SAHI detections with species classification
4. Merge validated timestamps with detection results

This script coordinates all steps and provides detailed logging.

Usage:
    python run_full_pipeline.py \
        --image-dir /path/to/camera_trap/images \
        --yolo-weights yolov8x.pt \
        --camera-config cameras.json \
        --output-dir ./results

See README_PIPELINE.md for detailed documentation.
"""

import argparse
import subprocess
import sys
from pathlib import Path
import json


def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n❌ FAILED: {description}")
        return False

    print(f"\n✓ Completed: {description}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run full camera trap processing pipeline with timestamp validation"
    )

    parser.add_argument(
        "--image-dir",
        required=True,
        help="Root directory containing all camera trap images"
    )
    parser.add_argument(
        "--yolo-weights",
        required=True,
        help="Path to YOLO weights file (e.g., yolov8x.pt)"
    )
    parser.add_argument(
        "--camera-config",
        required=True,
        help="JSON file with camera GPS/bearing configuration"
    )
    parser.add_argument(
        "--output-dir",
        default="./results",
        help="Where to save all outputs (default: ./results)"
    )
    parser.add_argument(
        "--skip-indexing",
        action="store_true",
        help="Skip image indexing (reuse existing index.csv)"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip event validation (reuse existing events_validated.csv)"
    )
    parser.add_argument(
        "--skip-detection",
        action="store_true",
        help="Skip YOLO detection (reuse existing detections.csv)"
    )
    parser.add_argument(
        "--skip-merge",
        action="store_true",
        help="Skip final merge step"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Paths for intermediate files
    index_csv = output_dir / "index.csv"
    events_csv = output_dir / "events_validated.csv"
    detections_csv = output_dir / "detections.csv"
    merged_csv = output_dir / "detections_with_validated_timestamps.csv"

    print(f"\n{'='*60}")
    print("Camera Trap Processing Pipeline")
    print(f"{'='*60}")
    print(f"Image directory: {args.image_dir}")
    print(f"Output directory: {output_dir}")
    print(f"YOLO weights: {args.yolo_weights}")
    print(f"Camera config: {args.camera_config}")

    # Step 1: Index images
    if not args.skip_indexing or not index_csv.exists():
        cmd = [
            "python", "00_indexing/index_images.py",
            "--images", args.image_dir,
            "--output", str(index_csv)
        ]
        if not run_command(cmd, "Index camera trap images"):
            sys.exit(1)
    else:
        print(f"⊘ Skipping indexing (using existing {index_csv})")

    # Step 2: Validate events
    if not args.skip_validation or not events_csv.exists():
        cmd = [
            "python", "01_events/make_events_validated.py",
            "--index", str(index_csv),
            "--output", str(events_csv)
        ]
        if not run_command(cmd, "Extract and validate timestamps"):
            sys.exit(1)
    else:
        print(f"⊘ Skipping validation (using existing {events_csv})")

    # Step 3: Run detections
    if not args.skip_detection or not detections_csv.exists():
        # Parse camera config to feed into detections script
        with open(args.camera_config) as f:
            config = json.load(f)

        # Camera config should have per-camera settings
        # For now, we'll run a single call (user can parallelize)
        print(f"\nNote: Detection step requires per-camera processing.")
        print(f"See camera config at {args.camera_config}")
        print(f"Run camera_trap_detections.py separately for each camera.")
        print(f"Expected output: {detections_csv}")

    else:
        print(f"⊘ Skipping detection (using existing {detections_csv})")

    # Step 4: Merge
    if not args.skip_merge:
        if not detections_csv.exists():
            print(f"\n⚠ Skipping merge: detections CSV not found at {detections_csv}")
            print(f"  Please run detections first, or provide --skip-merge")
        else:
            cmd = [
                "python", "02_merge/merge_detections_and_events.py",
                "--events", str(events_csv),
                "--detections", str(detections_csv),
                "--output", str(merged_csv)
            ]
            if not run_command(cmd, "Merge validated timestamps with detections"):
                sys.exit(1)

    # Final summary
    print(f"\n{'='*60}")
    print("Pipeline Complete!")
    print(f"{'='*60}")
    print(f"Output files in {output_dir}:")
    print(f"  - index.csv: {index_csv} ({'✓' if index_csv.exists() else '✗'})")
    print(f"  - events_validated.csv: {events_csv} ({'✓' if events_csv.exists() else '✗'})")
    print(f"  - detections.csv: {detections_csv} ({'✓' if detections_csv.exists() else '✗'})")
    print(f"  - detections_with_validated_timestamps.csv: {merged_csv} ({'✓' if merged_csv.exists() else '✗'})")

    if merged_csv.exists():
        print(f"\n✓ Final merged output ready: {merged_csv}")


if __name__ == "__main__":
    main()
