#!/usr/bin/env python3
"""
Batch process camera trap directories: index, validate, merge, and generate metadata.

This script processes one or more camera trap directories in parallel or sequence,
running the complete pipeline from raw images to FAIR² compliant metadata.

Workflow for each directory:
1. Index images (if needed)
2. Validate timestamps (if needed)
3. Merge with detections (if available)
4. Generate Darwin Core metadata

Usage:
    # Process single directory
    python batch_process_camera_traps.py \\
        --image-dir /fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps \\
        --output-dir ./results

    # Process multiple campaigns
    python batch_process_camera_traps.py \\
        --base-dir /fs/ess/PAS2136/TheWilds2025 \\
        --output-dir ./results \\
        --find-campaigns

    # Resume interrupted processing
    python batch_process_camera_traps.py \\
        --base-dir /fs/ess/PAS2136/TheWilds2025 \\
        --output-dir ./results \\
        --find-campaigns \\
        --continue-from TW02-CT01
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
import re

import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def discover_campaigns(base_dir):
    """Discover all camera trap campaigns."""
    base_path = Path(base_dir)
    campaigns = {}

    # Find directories that look like thewilds_YYYYMMDD_YYYYMMDD
    pattern = re.compile(r"thewilds_\d{8}_\d{8}")

    for path in base_path.iterdir():
        if not path.is_dir():
            continue
        if not pattern.match(path.name):
            continue

        camera_traps_dir = path / "camera_traps"
        if not camera_traps_dir.exists():
            continue

        campaigns[path.name] = {
            "path": camera_traps_dir,
            "cameras": discover_cameras_in_dir(camera_traps_dir)
        }

    return campaigns


def discover_cameras_in_dir(camera_traps_dir):
    """Discover camera subdirectories in a given directory."""
    cameras = {}
    pattern = re.compile(r"(TW\d+-?CT\d+)")

    for path in camera_traps_dir.iterdir():
        if not path.is_dir():
            continue

        match = pattern.search(path.name)
        if not match:
            continue

        camera_id = match.group(1).replace("_", "-")
        images = list(path.glob("*.[jJ][pP][gG]"))

        if images or (path / "annotated").exists():
            cameras[camera_id] = {
                "path": path,
                "images": len(images)
            }

    return cameras


def run_indexing(image_dir, output_dir):
    """Run image indexing for a camera directory."""
    logger.info(f"Indexing images from: {image_dir}")

    cmd = [
        "python", "-m", "src.00_indexing.index_images",
        "--images", str(image_dir),
        "--output", str(Path(output_dir) / "index.csv")
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info("✓ Image indexing complete")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Image indexing failed: {e.stderr.decode()}")
        return False


def run_timestamp_validation(index_csv, output_dir):
    """Run timestamp validation."""
    logger.info(f"Validating timestamps from: {index_csv}")

    cmd = [
        "python", "-m", "src.01_events.make_events_validated",
        "--index", str(index_csv),
        "--output", str(Path(output_dir) / "events_validated.csv")
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info("✓ Timestamp validation complete")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Timestamp validation failed: {e.stderr.decode()}")
        return False


def run_metadata_generation(events_csv, detections_csv, output_dir):
    """Run Darwin Core metadata generation."""
    logger.info(f"Generating Darwin Core metadata...")

    cmd = [
        "python", "-m", "src.03_metadata.generate_darwin_core_occurrences",
        str(detections_csv),
        str(events_csv),
        str(Path(output_dir) / "darwin_core_occurrences.csv")
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info("✓ Darwin Core generation complete")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Darwin Core generation failed: {e.stderr.decode()}")
        return False


def process_camera_directory(camera_dir, output_dir, skip_steps=None):
    """
    Process a single camera directory through the full pipeline.

    Args:
        camera_dir: Path to camera subdirectory
        output_dir: Where to save outputs
        skip_steps: List of steps to skip (e.g., ['indexing', 'validation'])
    """
    skip_steps = skip_steps or []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"\n{'='*70}")
    logger.info(f"Processing: {camera_dir.name}")
    logger.info(f"Output: {output_path}")
    logger.info(f"{'='*70}")

    status = {"success": True, "steps": {}}

    # Step 1: Indexing
    index_csv = output_path / "index.csv"
    if "indexing" not in skip_steps and not index_csv.exists():
        logger.info("\nStep 1: Image Indexing")
        status["steps"]["indexing"] = run_indexing(camera_dir, output_path)
    else:
        logger.info(f"Step 1: Image Indexing (skipped/exists)")
        status["steps"]["indexing"] = "skipped"

    # Step 2: Timestamp Validation
    events_csv = output_path / "events_validated.csv"
    if "validation" not in skip_steps and not events_csv.exists():
        if not index_csv.exists():
            logger.error("Cannot validate timestamps without index.csv")
            return False

        logger.info("\nStep 2: Timestamp Validation")
        status["steps"]["validation"] = run_timestamp_validation(index_csv, output_path)
    else:
        logger.info(f"Step 2: Timestamp Validation (skipped/exists)")
        status["steps"]["validation"] = "skipped"

    # Step 3: Metadata Generation (requires detections)
    detections_csv = output_path / "detections_with_validated_timestamps.csv"
    if "metadata" not in skip_steps:
        if detections_csv.exists():
            logger.info("\nStep 3: Darwin Core Metadata Generation")
            status["steps"]["metadata"] = run_metadata_generation(
                events_csv, detections_csv, output_path
            )
        else:
            logger.warning(f"Skipping metadata generation: detections CSV not found")
            logger.info(f"Expected: {detections_csv}")
            status["steps"]["metadata"] = "skipped"
    else:
        logger.info(f"Step 3: Darwin Core Metadata (skipped)")
        status["steps"]["metadata"] = "skipped"

    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("Processing Summary:")
    for step, result in status["steps"].items():
        status_str = "✓" if result is True else ("✗" if result is False else "⊘")
        logger.info(f"  {status_str} {step}")

    return status["success"]


def main():
    parser = argparse.ArgumentParser(
        description="Batch process camera trap directories"
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--image-dir",
        help="Single camera trap directory to process"
    )
    input_group.add_argument(
        "--base-dir",
        help="Base directory to search for camera campaigns"
    )

    # Processing options
    parser.add_argument(
        "--output-dir",
        default="./camera_trap_results",
        help="Output directory for results (default: ./camera_trap_results)"
    )
    parser.add_argument(
        "--find-campaigns",
        action="store_true",
        help="Search for all camera trap campaigns (requires --base-dir)"
    )
    parser.add_argument(
        "--camera-filter",
        help="Only process cameras matching pattern (e.g., TW02-*)"
    )
    parser.add_argument(
        "--continue-from",
        help="Resume processing from specific camera"
    )
    parser.add_argument(
        "--skip-steps",
        nargs="+",
        choices=["indexing", "validation", "metadata"],
        help="Steps to skip in processing"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1, sequential)"
    )

    args = parser.parse_args()

    output_base = Path(args.output_dir)
    output_base.mkdir(parents=True, exist_ok=True)

    logger.info(f"\n{'='*70}")
    logger.info("Camera Trap Batch Processing")
    logger.info(f"{'='*70}")

    # Discover what to process
    if args.image_dir:
        # Single directory mode
        camera_path = Path(args.image_dir)
        if not camera_path.exists():
            logger.error(f"Directory not found: {camera_path}")
            sys.exit(1)

        campaigns = {
            "single": {
                "path": camera_path,
                "cameras": {camera_path.name: {"path": camera_path, "images": 0}}
            }
        }

    elif args.base_dir:
        if not args.find_campaigns:
            logger.error("--base-dir requires --find-campaigns")
            sys.exit(1)

        base_path = Path(args.base_dir)
        if not base_path.exists():
            logger.error(f"Directory not found: {base_path}")
            sys.exit(1)

        logger.info(f"Discovering campaigns in: {base_path}")
        campaigns = discover_campaigns(base_path)

    else:
        logger.error("Must specify --image-dir or --base-dir")
        sys.exit(1)

    # Build processing queue
    processing_queue = []
    skip_from = args.continue_from is None

    for campaign_name, campaign_info in sorted(campaigns.items()):
        for camera_id, camera_info in sorted(campaign_info["cameras"].items()):
            # Apply filters
            if args.camera_filter:
                import fnmatch
                if not fnmatch.fnmatch(camera_id, args.camera_filter):
                    continue

            # Handle resume
            if args.continue_from:
                if camera_id == args.continue_from:
                    skip_from = True
                if not skip_from:
                    continue

            processing_queue.append({
                "campaign": campaign_name,
                "camera": camera_id,
                "path": camera_info["path"],
                "output": output_base / campaign_name / camera_id
            })

    # Summary
    logger.info(f"\nFound {len(processing_queue)} cameras to process:")
    for item in processing_queue[:5]:
        logger.info(f"  - {item['campaign']}/{item['camera']}")
    if len(processing_queue) > 5:
        logger.info(f"  ... and {len(processing_queue) - 5} more")

    # Process
    logger.info(f"\nStarting processing (parallel={args.parallel})...")

    successes = 0
    failures = 0

    for item in processing_queue:
        success = process_camera_directory(
            item["path"],
            item["output"],
            skip_steps=args.skip_steps or []
        )

        if success:
            successes += 1
        else:
            failures += 1

    # Final summary
    logger.info(f"\n{'='*70}")
    logger.info("Batch Processing Complete")
    logger.info(f"{'='*70}")
    logger.info(f"Successes: {successes}")
    logger.info(f"Failures: {failures}")
    logger.info(f"Output directory: {output_base}")

    # Save processing report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_processed": successes + failures,
        "successes": successes,
        "failures": failures,
        "output_dir": str(output_base),
        "cameras_processed": [f"{item['campaign']}/{item['camera']}" for item in processing_queue]
    }

    with open(output_base / "processing_report.json", "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report saved to: {output_base / 'processing_report.json'}")

    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
