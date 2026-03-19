#!/usr/bin/env python3
"""
Consolidate detection results from all 4 modalities into unified occurrences CSV.

Input:
  - camera_detections.csv (from camera trap pipeline)
  - bioacoustics_detections.csv (or rectified BirdNET annotations)
  - drone_detections.csv (from drone pipeline)
  - citizen_science_observations.csv (from citizen science pipeline)

Output:
  - occurrences_all_modalities.csv (unified with modality_type column)
"""

import csv
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_detections_csv(csv_path: Path) -> Tuple[List[Dict], List[str]]:
    """Load detection CSV and return rows + fieldnames."""
    if not csv_path.exists():
        logger.warning(f"  File not found: {csv_path}")
        return [], []

    rows = []
    fieldnames = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames if reader.fieldnames else []
            for row in reader:
                rows.append(row)
        logger.info(f"  ✓ Loaded {len(rows)} rows from {csv_path.name}")
    except Exception as e:
        logger.error(f"  ✗ Error reading {csv_path.name}: {e}")
        return [], []

    return rows, fieldnames


def add_modality_column(rows: List[Dict], modality: str) -> List[Dict]:
    """Add modality_type column to all rows."""
    for row in rows:
        row['modality_type'] = modality
    return rows


def merge_all_modalities(
    data_directory: Path,
    output_directory: Path
) -> None:
    """
    Consolidate detections from all 4 modalities.

    Expects modality CSV files in data_directory:
    - camera_detections.csv
    - bioacoustics_detections.csv
    - drone_detections.csv
    - citizen_science_observations_stub.csv
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    logger.info("="*70)
    logger.info("CONSOLIDATING ALL MODALITY DETECTIONS")
    logger.info("="*70)
    logger.info(f"Input directory: {data_directory}")
    logger.info(f"Output directory: {output_directory}\n")

    all_rows = []
    all_fieldnames = set()

    # Load detections from each modality
    modalities = [
        ("camera_traps", "camera_detections.csv"),
        ("bioacoustics", "bioacoustics_detections.csv"),
        ("drones", "drone_detections.csv"),
        ("citizen_science", "citizen_science_observations_stub.csv"),
    ]

    modality_counts = {}

    for modality_type, filename in modalities:
        csv_path = data_directory / filename
        logger.info(f"\nLoading {modality_type}:")

        rows, fieldnames = load_detections_csv(csv_path)

        if rows:
            # Add modality column
            rows = add_modality_column(rows, modality_type)
            all_rows.extend(rows)
            all_fieldnames.update(fieldnames)
            all_fieldnames.add('modality_type')
            modality_counts[modality_type] = len(rows)
        else:
            modality_counts[modality_type] = 0

    # Ensure 'modality_type' is first column
    fieldnames_list = ['modality_type'] + sorted([f for f in all_fieldnames if f != 'modality_type'])

    # Write unified CSV
    output_file = output_directory / "occurrences_all_modalities.csv"

    if all_rows:
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames_list)
                writer.writeheader()

                for row in all_rows:
                    # Fill missing fields with empty strings
                    for field in fieldnames_list:
                        if field not in row:
                            row[field] = ''
                    writer.writerow(row)

            logger.info(f"\n✓ Consolidated CSV written: {output_file}")
            logger.info(f"  Total rows: {len(all_rows)}")
        except Exception as e:
            logger.error(f"✗ Error writing output CSV: {e}")

    # Summary statistics
    logger.info(f"\n{'='*70}")
    logger.info("CONSOLIDATION SUMMARY")
    logger.info(f"{'='*70}")

    for modality_type, count in sorted(modality_counts.items()):
        pct = (count / len(all_rows) * 100) if all_rows else 0
        logger.info(f"{modality_type:20s}: {count:6d} occurrences ({pct:5.1f}%)")

    logger.info(f"\n{'='*70}")
    logger.info(f"TOTAL OCCURRENCES: {len(all_rows)}")
    logger.info(f"{'='*70}\n")


def main():
    # Define paths
    data_dir = Path("/fs/ess/PAS2136/TheWilds2025/processing_output/detections_automated")
    output_dir = Path("/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata")

    merge_all_modalities(data_dir, output_dir)


if __name__ == "__main__":
    main()
