"""
Merge validated camera trap events with YOLO/SAHI detection results.

This script combines:
1. events_validated.csv - Timestamped images with validation flags
2. detections.csv - YOLO + BioCLIP detections with species labels, confidence scores, and GPS projections

Output: detections_with_validated_timestamps.csv
- Retains all detection data (species, confidence, coordinates, GPS)
- Adds validated timestamp (corrected if needed)
- Adds validation flags for manual review
- Adds timestamp source for transparency
- Enables filtering by validation_flag before downstream analysis

Usage:
    python merge_detections_and_events.py \
        --events events_validated.csv \
        --detections detections.csv \
        --output detections_with_validated_timestamps.csv
"""

import argparse
from pathlib import Path
import pandas as pd


def merge_detections_and_events(events_csv, detections_csv, output_csv):
    """
    Merge validated events with detection results.

    Args:
        events_csv: Path to events_validated.csv
        detections_csv: Path to detections.csv
        output_csv: Path for output merged CSV
    """

    print(f"Loading events from: {events_csv}")
    events = pd.read_csv(events_csv)
    print(f"  Loaded {len(events)} event records")

    print(f"Loading detections from: {detections_csv}")
    detections = pd.read_csv(detections_csv)
    print(f"  Loaded {len(detections)} detection records")

    # Merge on image path
    # Events has 'path' column, Detections has 'image_path' column
    merged = detections.merge(
        events[['path', 'timestamp', 'timestamp_source', 'validation_flag', 'site_cam', 'session']],
        left_on='image_path',
        right_on='path',
        how='left'
    )

    print(f"\nMerge results:")
    print(f"  Total detection records: {len(merged)}")
    print(f"  Records with validated timestamp: {merged['timestamp'].notna().sum()}")
    print(f"  Records without match: {merged['timestamp'].isna().sum()}")

    # Summary of timestamp sources
    if 'timestamp_source' in merged.columns:
        print(f"\nTimestamp sources in merged data:")
        print(merged['timestamp_source'].value_counts())

    # Summary of validation flags
    if 'validation_flag' in merged.columns:
        flagged = merged[merged['validation_flag'].notna()]
        print(f"\nDetections with validation flags: {len(flagged)}")
        if len(flagged) > 0:
            print(f"Flag types:")
            for flag_type in flagged['validation_flag'].str.split(';').str[0].unique():
                count = len(flagged[flagged['validation_flag'].str.startswith(flag_type.strip())])
                print(f"  {flag_type.strip()}: {count}")

    # Reorder columns for usability
    # Put timestamp info early, then detections, then GPS
    col_order = [
        'image', 'image_path', 'site_cam', 'session',
        'timestamp', 'timestamp_source', 'validation_flag',
        'timestamp_file', 'timestamp_from_name',  # original timestamps for reference
        'detection_index', 'bioclip_label', 'bioclip_score', 'yolo_conf',
        'xmin', 'ymin', 'xmax', 'ymax',
        'distance_m', 'angle_deg',
        'camera_lat', 'camera_lon', 'camera_bearing_deg',
        'animal_lat', 'animal_lon', 'animal_absolute_bearing_deg',
    ]

    # Use only columns that exist
    col_order = [c for c in col_order if c in merged.columns]
    merged = merged[col_order]

    # Save output
    print(f"\nWriting merged output to: {output_csv}")
    merged.to_csv(output_csv, index=False)
    print(f"Done! ({len(merged)} records)")

    return merged


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge validated camera trap events with detection results"
    )
    parser.add_argument(
        "--events",
        required=True,
        help="Path to events_validated.csv (from make_events_validated.py)"
    )
    parser.add_argument(
        "--detections",
        required=True,
        help="Path to detections.csv (from camera_trap_detections.py)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for merged CSV"
    )

    args = parser.parse_args()

    merge_detections_and_events(args.events, args.detections, args.output)
