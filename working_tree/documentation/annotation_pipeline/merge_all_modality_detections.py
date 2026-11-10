#!/usr/bin/env python3
"""
Consolidate Darwin Core occurrences from all 5 modalities into unified table.

Input (from processing_output/darwin_core/):
  - bioacoustics/darwin_core_occurrences_bioacoustics.csv
  - camera_traps/darwin_core_occurrences_camera_traps.csv
  - citizen_science/darwin_core_occurrences_citizen_science.csv
  - drones/darwin_core_occurrences_drones.csv
  - text_data/darwin_core_occurrences_text.csv

Output:
  - occurrences_all_modalities.csv (unified with modality_type column)
  - events_all_modalities.csv (unified event hierarchy)
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
    Consolidate Darwin Core occurrences from all 5 modalities.

    Expects modality-specific Darwin Core CSVs under data_directory/
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    logger.info("="*70)
    logger.info("CONSOLIDATING ALL MODALITY DETECTIONS")
    logger.info("="*70)
    logger.info(f"Input directory: {data_directory}")
    logger.info(f"Output directory: {output_directory}\n")

    all_rows = []
    all_fieldnames = set()

    # Load Darwin Core occurrences from each modality
    modalities = [
        ("bioacoustics", "bioacoustics/darwin_core_occurrences_bioacoustics.csv"),
        ("camera_traps", "camera_traps/darwin_core_occurrences_camera_traps.csv"),
        ("citizen_science", "citizen_science/darwin_core_occurrences_citizen_science.csv"),
        ("drones", "drones/darwin_core_occurrences_drones.csv"),
        ("text_data", "text_data/darwin_core_occurrences_text.csv"),
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


def merge_all_events(data_directory: Path, output_directory: Path) -> None:
    """Merge all modality event CSVs into unified event hierarchy."""
    output_directory.mkdir(parents=True, exist_ok=True)

    logger.info("\n" + "=" * 70)
    logger.info("MERGING EVENT HIERARCHIES")
    logger.info("=" * 70)

    # Study-level event
    study_event = {
        "eventID": "TheWilds_2025",
        "parentEventID": "",
        "eventType": "Study",
        "eventDate": "2025-06-30/2025-09-08",
        "samplingProtocol": "Multi-modal biodiversity survey (camera traps, bioacoustics, drones, citizen science, text observations)",
        "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
        "decimalLatitude": "39.83",
        "decimalLongitude": "-81.74",
        "coordinateUncertaintyInMeters": "5000",
        "geodeticDatum": "WGS84",
        "country": "United States",
        "stateProvince": "Ohio",
        "county": "Muskingum",
        "datasetID": "TheWilds_2025",
        "datasetName": "The Wilds 2025 Multi-Modal Biodiversity Survey",
    }

    all_events = [study_event]
    all_fieldnames = set(study_event.keys())

    event_files = [
        ("bioacoustics", "bioacoustics/darwin_core_events_bioacoustics.csv"),
        ("camera_traps", "camera_traps/darwin_core_events_camera_traps.csv"),
        ("citizen_science", "citizen_science/darwin_core_events_citizen_science.csv"),
        ("drones", "drones/darwin_core_events_drones.csv"),
        ("text_data", "text_data/darwin_core_events_text.csv"),
    ]

    for modality, filename in event_files:
        csv_path = data_directory / filename
        rows, fieldnames = load_detections_csv(csv_path)
        if rows:
            all_events.extend(rows)
            all_fieldnames.update(fieldnames)

    # Write unified events
    fieldnames_list = sorted(all_fieldnames)
    # Put key fields first
    priority = ["eventID", "parentEventID", "eventType", "eventDate", "samplingProtocol"]
    fieldnames_list = [f for f in priority if f in all_fieldnames] + \
                      [f for f in fieldnames_list if f not in priority]

    output_file = output_directory / "events_all_modalities.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_list, extrasaction='ignore')
        writer.writeheader()
        for event in all_events:
            for field in fieldnames_list:
                if field not in event:
                    event[field] = ''
            writer.writerow(event)

    logger.info(f"✓ Unified events written: {output_file}")
    logger.info(f"  Total events: {len(all_events)} (1 study + {len(all_events)-1} modality/deployment)")


def main():
    data_dir = Path("/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core")
    output_dir = Path("/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core")

    merge_all_modalities(data_dir, output_dir)
    merge_all_events(data_dir, output_dir)


if __name__ == "__main__":
    main()
