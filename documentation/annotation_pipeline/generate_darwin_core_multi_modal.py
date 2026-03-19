#!/usr/bin/env python3
"""
Generate unified Darwin Core multi-modal metadata with 4-level Event hierarchy.

This script creates:
1. Study-level Event: "The Wilds 2025"
2. Modality-level Events: One per modality (4 events)
3. Deployment/Session-level Events: One per physical installation (28+ events)
4. Links all Occurrences via eventID foreign key

Output:
  - darwin_core_events_multi_modal.csv (33+ rows: 1 study + 4 modality + 28 deployment events)
  - darwin_core_occurrences_multi_modal.csv (all modalities linked via eventID)
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# LEVEL 1: STUDY-LEVEL EVENT
# ============================================================================

def create_study_event() -> Dict:
    """Create root study-level Event for entire survey."""
    return {
        "eventID": "TheWilds_2025",
        "eventType": "Study",
        "eventDate": "2025-06-30",
        "eventEndDate": "2025-08-28",
        "samplingProtocol": "Multi-modal biodiversity survey (camera traps, bioacoustics, drones, citizen science)",
        "samplingEffort": "13 camera deployments + 6 bioacoustic sites + 8 drone flights + 991 citizen science submissions",
        "decimalLatitude": 39.50,
        "decimalLongitude": -81.44,
        "coordinateUncertaintyInMeters": 1000,
        "geodeticDatum": "WGS84",
        "locality": "The Wilds Conservation Center, Southeastern Ohio",
        "countryCode": "USA",
        "stateProvince": "Ohio",
        "recordedBy": "Multi-modal research team",
        "fieldNotes": "Comprehensive biodiversity survey using 4 distinct data collection modalities",
        "datasetID": "TheWilds_2025",
        "datasetName": "The Wilds 2025 Biodiversity Survey",
    }


# ============================================================================
# LEVEL 2: MODALITY-LEVEL EVENTS
# ============================================================================

def create_modality_events() -> List[Dict]:
    """Create modality-level Events (one per modality type)."""
    return [
        {
            "eventID": "TheWilds_2025_camera_traps",
            "parentEventID": "TheWilds_2025",
            "eventType": "ModularSurvey",
            "eventDate": "2025-06-30",
            "eventEndDate": "2025-08-28",
            "samplingProtocol": "Passive infrared camera trap survey (PIR-triggered + hourly timelapse)",
            "samplingEffort": "13 deployments, 2 campaigns, ~225,000 images collected",
            "decimalLatitude": 39.50,
            "decimalLongitude": -81.44,
            "coordinateUncertaintyInMeters": 1000,
            "geodeticDatum": "WGS84",
            "recordedBy": "Automated camera trap platforms",
            "fieldNotes": "Detection: YOLO+BioCLIP; Automated occurrences awaiting manual verification",
            "datasetID": "TheWilds_2025",
            "datasetName": "The Wilds 2025 Biodiversity Survey - Camera Traps",
        },
        {
            "eventID": "TheWilds_2025_bioacoustics",
            "parentEventID": "TheWilds_2025",
            "eventType": "ModularSurvey",
            "eventDate": "2025-08-04",
            "eventEndDate": "2025-08-28",
            "samplingProtocol": "Continuous acoustic monitoring via stationary Song Meter recorders",
            "samplingEffort": "6 recording sites, 2,142 WAV files (209 GB total)",
            "decimalLatitude": 39.50,
            "decimalLongitude": -81.44,
            "coordinateUncertaintyInMeters": 1000,
            "geodeticDatum": "WGS84",
            "recordedBy": "Wildlife Acoustics Song Meter 4 recorders",
            "fieldNotes": "Detection: BirdCLIP automated species classification; Pre-existing annotations being rectified",
            "datasetID": "TheWilds_2025",
            "datasetName": "The Wilds 2025 Biodiversity Survey - Bioacoustics",
        },
        {
            "eventID": "TheWilds_2025_drones",
            "parentEventID": "TheWilds_2025",
            "eventType": "ModularSurvey",
            "eventDate": "2025-08-11",
            "eventEndDate": "2025-08-25",
            "samplingProtocol": "Periodic aerial video surveys via DJI and Parrot drones",
            "samplingEffort": "8 flight missions (5 with video), 13 video files (33 GB total)",
            "decimalLatitude": 39.50,
            "decimalLongitude": -81.44,
            "coordinateUncertaintyInMeters": 1000,
            "geodeticDatum": "WGS84",
            "recordedBy": "DJI Mavic and Parrot Anafi 4K platforms",
            "fieldNotes": "Detection: YOLO+SAHI+BioCLIP; GPS interpolated from flight telemetry; Awaiting manual curator review",
            "datasetID": "TheWilds_2025",
            "datasetName": "The Wilds 2025 Biodiversity Survey - Drones",
        },
        {
            "eventID": "TheWilds_2025_citizen_science",
            "parentEventID": "TheWilds_2025",
            "eventType": "ModularSurvey",
            "eventDate": "2025-08-04",
            "eventEndDate": "2025-08-28",
            "samplingProtocol": "Opportunistic mobile phone photography from park visitors",
            "samplingEffort": "991 submissions (853 photos + 138 videos, 8.9 GB total)",
            "decimalLatitude": 39.50,
            "decimalLongitude": -81.44,
            "coordinateUncertaintyInMeters": 1000,
            "geodeticDatum": "WGS84",
            "recordedBy": "Crowdsourced park visitors",
            "fieldNotes": "Highly heterogeneous in equipment/technique; Awaiting manual curation and species annotation",
            "datasetID": "TheWilds_2025",
            "datasetName": "The Wilds 2025 Biodiversity Survey - Citizen Science",
        },
    ]


# ============================================================================
# LEVEL 3: DEPLOYMENT/SESSION EVENTS (from modality-specific outputs)
# ============================================================================

def load_deployment_events(data_directory: Path) -> List[Dict]:
    """
    Load Level 3 (deployment/session) Events from modality-specific CSV files.

    Expected sources:
    - camera_trap_events.csv (from camera trap pipeline)
    - bioacoustics_darwin_core_events.csv (from bioacoustics rectification)
    - drone_events.csv (from drone pipeline)
    - citizen_science_events.csv (from citizen science pipeline)
    """

    deployment_events = []

    # Add camera trap deployment events
    camera_events_file = data_directory / "detections_automated" / "camera_traps" / "camera_trap_events.csv"
    if camera_events_file.exists():
        try:
            with open(camera_events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Ensure parentEventID links to camera traps modality
                    row['parentEventID'] = 'TheWilds_2025_camera_traps'
                    deployment_events.append(row)
            logger.info(f"✓ Loaded {len(deployment_events)} camera trap deployment events")
        except Exception as e:
            logger.warning(f"Could not load camera events: {e}")

    # Add bioacoustic session events
    bioacoustics_events_file = data_directory / "detections_automated" / "bioacoustics" / "bioacoustics_darwin_core_events.csv"
    if bioacoustics_events_file.exists():
        try:
            with open(bioacoustics_events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['parentEventID'] = 'TheWilds_2025_bioacoustics'
                    deployment_events.append(row)
            logger.info(f"✓ Loaded {len(deployment_events) - len(deployment_events)} additional bioacoustics events")
        except Exception as e:
            logger.warning(f"Could not load bioacoustics events: {e}")

    # Add drone flight mission events
    drone_events_file = data_directory / "detections_manual" / "drone_events.csv"
    if drone_events_file.exists():
        try:
            with open(drone_events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['parentEventID'] = 'TheWilds_2025_drones'
                    deployment_events.append(row)
            logger.info(f"✓ Loaded drone flight mission events")
        except Exception as e:
            logger.warning(f"Could not load drone events: {e}")

    # Add citizen science submission events
    cs_events_file = data_directory / "detections_manual" / "citizen_science_events.csv"
    if cs_events_file.exists():
        try:
            with open(cs_events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['parentEventID'] = 'TheWilds_2025_citizen_science'
                    deployment_events.append(row)
            logger.info(f"✓ Loaded citizen science submission events")
        except Exception as e:
            logger.warning(f"Could not load citizen science events: {e}")

    return deployment_events


# ============================================================================
# OCCURRENCE LINKING
# ============================================================================

def load_occurrences(
    data_directory: Path,
    unified_occurrences_file: Path
) -> List[Dict]:
    """
    Load all unified occurrences from consolidated CSV.

    Each occurrence should have:
    - occurrenceID (unique identifier)
    - eventID (foreign key to Level 3 deployment event)
    - modality_type (camera_traps, bioacoustics, drones, citizen_science)
    - All other Darwin Core fields
    """

    occurrences = []

    if unified_occurrences_file.exists():
        try:
            with open(unified_occurrences_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    occurrences.append(row)
            logger.info(f"✓ Loaded {len(occurrences)} unified occurrence records")
        except Exception as e:
            logger.error(f"✗ Error loading occurrences: {e}")
    else:
        logger.warning(f"Unified occurrences file not found: {unified_occurrences_file}")

    return occurrences


# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_darwin_core_multi_modal(
    data_directory: Path,
    output_directory: Path
) -> None:
    """
    Generate complete multi-modal Darwin Core Events and Occurrences hierarchy.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    logger.info("="*70)
    logger.info("GENERATING MULTI-MODAL DARWIN CORE METADATA")
    logger.info("="*70)
    logger.info(f"Input: {data_directory}")
    logger.info(f"Output: {output_directory}\n")

    # ========================================================================
    # EVENTS
    # ========================================================================

    logger.info("Generating Event hierarchy:")
    logger.info("-" * 70)

    # Level 1: Study event
    study_event = create_study_event()
    logger.info(f"✓ Created study-level Event: {study_event['eventID']}")

    events = [study_event]

    # Level 2: Modality events
    modality_events = create_modality_events()
    events.extend(modality_events)
    logger.info(f"✓ Created 4 modality-level Events")

    # Level 3: Deployment/session events
    deployment_events = load_deployment_events(data_directory)
    events.extend(deployment_events)
    logger.info(f"✓ Loaded {len(deployment_events)} deployment/session-level Events")

    # Write Events CSV
    events_file = output_directory / "darwin_core_events_multi_modal.csv"
    if events:
        try:
            # Get all unique fieldnames
            fieldnames = set()
            for event in events:
                fieldnames.update(event.keys())
            fieldnames_list = sorted(list(fieldnames))

            with open(events_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames_list)
                writer.writeheader()
                for event in events:
                    # Fill missing fields
                    for field in fieldnames_list:
                        if field not in event:
                            event[field] = ''
                    writer.writerow(event)

            logger.info(f"\n✓ Events CSV written: {events_file}")
            logger.info(f"  Total events: {len(events)} (1 study + 4 modality + {len(deployment_events)} deployment/session)")
        except Exception as e:
            logger.error(f"✗ Error writing events CSV: {e}")
            return

    # ========================================================================
    # OCCURRENCES
    # ========================================================================

    logger.info(f"\n{'='*70}")
    logger.info("Generating Occurrence records:")
    logger.info("-" * 70)

    unified_occurrences_file = output_directory / "occurrences_all_modalities.csv"
    occurrences = load_occurrences(data_directory, unified_occurrences_file)

    if not occurrences:
        logger.warning("No occurrence records to process")
        return

    # Write Occurrences CSV
    occurrences_file = output_directory / "darwin_core_occurrences_multi_modal.csv"
    try:
        # Get all unique fieldnames
        fieldnames = set()
        for occ in occurrences:
            fieldnames.update(occ.keys())
        fieldnames_list = sorted(list(fieldnames))

        with open(occurrences_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames_list)
            writer.writeheader()
            for occ in occurrences:
                # Fill missing fields
                for field in fieldnames_list:
                    if field not in occ:
                        occ[field] = ''
                writer.writerow(occ)

        logger.info(f"✓ Occurrences CSV written: {occurrences_file}")
        logger.info(f"  Total occurrences: {len(occurrences)}")
    except Exception as e:
        logger.error(f"✗ Error writing occurrences CSV: {e}")
        return

    # ========================================================================
    # SUMMARY STATISTICS
    # ========================================================================

    logger.info(f"\n{'='*70}")
    logger.info("SUMMARY STATISTICS")
    logger.info(f"{'='*70}")

    modality_counts = {}
    for occ in occurrences:
        modality = occ.get('modality_type', 'unknown')
        modality_counts[modality] = modality_counts.get(modality, 0) + 1

    for modality, count in sorted(modality_counts.items()):
        pct = (count / len(occurrences) * 100) if occurrences else 0
        logger.info(f"{modality:20s}: {count:6d} occurrences ({pct:5.1f}%)")

    logger.info(f"\n{'='*70}")
    logger.info(f"EVENT HIERARCHY:")
    logger.info(f"  Study Level:       1 event")
    logger.info(f"  Modality Level:    4 events")
    logger.info(f"  Deployment Level:  {len(deployment_events)} events")
    logger.info(f"  TOTAL EVENTS:      {len(events)} events")
    logger.info(f"\nOCCURRENCES:")
    logger.info(f"  TOTAL OCCURRENCES: {len(occurrences)} records")
    logger.info(f"{'='*70}\n")


def main():
    data_directory = Path("/fs/ess/PAS2136/TheWilds2025/processing_output")
    output_directory = Path("/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata")

    generate_darwin_core_multi_modal(data_directory, output_directory)


if __name__ == "__main__":
    main()
