"""
Process citizen science data for The Wilds 2025 multi-modal survey.

Creates Darwin Core Events for citizen submissions and stub Occurrences,
awaiting user-provided submission index metadata and manual annotation.

Input:
  - 991 media files (UUID-named photos/videos)
  - citizen_science_index.csv (user-provided metadata)

Output:
  - darwin_core_events_citizen_science.csv (Level 3: submission events)
  - citizen_science_observations_stub.csv (Occurrences, awaiting annotation)
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_citizen_science_submission_event(
    submission_id: str,
    submitter_name: Optional[str] = None,
    submission_date: Optional[str] = None,
    file_count: int = 1,
    location_coords: Optional[tuple] = None,
    location_description: Optional[str] = None
) -> Dict:
    """
    Create a Darwin Core Event record for a citizen science submission.

    This is a Level 3 Event (Deployment/Session level).
    """

    lat, lon = location_coords if location_coords else (None, None)

    return {
        "eventID": f"TheWilds_2025_citizen_science_submission_{submission_id}",
        "parentEventID": "TheWilds_2025_citizen_science",
        "eventType": "ObservationSubmission",
        "eventDate": submission_date or "2025-08-04",
        "eventTime": "12:00:00",  # TODO: Extract from submission metadata if available
        "samplingProtocol": "Opportunistic mobile phone photography",
        "samplingEffort": f"Single submission, {file_count} photo(s)/video(s)",
        "decimalLatitude": lat,
        "decimalLongitude": lon,
        "coordinateUncertaintyInMeters": 100 if lat else None,
        "geodeticDatum": "WGS84",
        "locality": location_description or "The Wilds observation area",
        "platformID": "citizen_smartphone_generic",
        "recordedBy": submitter_name or "Citizen observer",
        "fieldNotes": f"Citizen science submission {submission_id}. Location and timestamp from submission form.",
        "datasetID": "TheWilds_2025_citizen_science",
        "datasetName": "The Wilds 2025 Bioacoustic Survey - Citizen Science"
    }


def create_citizen_science_occurrence_stub(
    event_id: str,
    file_uuid: str,
    file_index: int,
    file_path: str,
    file_type: str,
    observation_date: Optional[str] = None,
    observation_time: Optional[str] = None,
    gps_lat: Optional[float] = None,
    gps_lon: Optional[float] = None,
    location_description: Optional[str] = None
) -> Dict:
    """
    Create a Darwin Core Occurrence record stub for citizen science observation.

    Awaiting manual curation and species identification.
    """

    occurrence_id = f"{event_id}_{file_index:03d}"

    return {
        "occurrenceID": occurrence_id,
        "eventID": event_id,
        "scientificName": "Unknown",
        "commonName": "Unknown",
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Unknown",
        "taxonRank": "species",
        "vernacularName": "Unknown",
        "occurrenceStatus": "present",
        "basisOfRecord": "HumanObservation",
        "recordedBy": "Citizen observer",
        "identificationVerificationStatus": "unverified",
        "individualCount": 1,
        "behaviour": "Unknown",
        "eventDate": observation_date or "2025-08-04",
        "eventTime": observation_time or "12:00:00",
        "decimalLatitude": gps_lat,
        "decimalLongitude": gps_lon,
        "coordinateUncertaintyMeters": 100 if gps_lat else None,
        "geodeticDatum": "WGS84",
        "locality": location_description or "Unknown",
        "associatedMedia": file_path,
        "associatedOccurrences": f"File: {file_uuid}, Type: {file_type}",
        "identificationRemarks": (
            "AWAITING MANUAL CURATION: Species identification, behavior, location verification required. "
            "Compare with reference species list (BioCLIP config) for identification guidance."
        ),
        "annotationStatus": "pending_curation",
        "datasetID": "TheWilds_2025_citizen_science",
        "datasetName": "The Wilds 2025 Bioacoustic Survey - Citizen Science"
    }


def create_stub_submission_events(file_count: int = 991) -> List[Dict]:
    """
    Create stub submission events without the user-provided index.

    These are placeholders showing the expected structure.
    User must provide citizen_science_index.csv to populate real metadata.
    """

    events = []

    # Create stub events for each submission (just structure, no real metadata yet)
    for submission_num in range(1, file_count + 1):
        event = create_citizen_science_submission_event(
            submission_id=str(submission_num).zfill(3),
            submitter_name=f"Observer_{submission_num}",
            submission_date="2025-08-04",  # TODO: Replace with actual date from index
            file_count=1,  # TODO: Replace with actual count from index
            location_coords=(39.50, -81.44),  # TODO: Replace with actual coords from index
            location_description="The Wilds observation area"  # TODO: Replace with description from index
        )
        events.append(event)

    return events


def create_stub_occurrences(file_count: int = 991) -> List[Dict]:
    """
    Create stub occurrences for all citizen science files.

    These are placeholders showing the expected structure.
    User must provide citizen_science_index.csv and perform manual annotation.
    """

    occurrences = []

    for submission_num in range(1, min(file_count + 1, 100)):  # Limit for demo
        submission_id = f"TheWilds_2025_citizen_science_submission_{str(submission_num).zfill(3)}"

        # Create 1 stub occurrence per submission (assuming 1 file per submission)
        occurrence = create_citizen_science_occurrence_stub(
            event_id=submission_id,
            file_uuid=f"UUID-{submission_num:04d}",
            file_index=1,
            file_path=f"citizen_science/UUID-{submission_num:04d}_image.jpg",
            file_type="JPEG",
            observation_date="2025-08-04",
            observation_time="12:00:00",
            gps_lat=39.50,
            gps_lon=-81.44,
            location_description="The Wilds observation area"
        )
        occurrences.append(occurrence)

    return occurrences


def process_citizen_science(
    data_directory: Path,
    output_directory: Path,
    index_file: Optional[Path] = None
) -> tuple:
    """
    Process citizen science data and generate Events + Occurrences.

    If index_file is provided, use actual metadata.
    Otherwise, generate stubs pending user-provided index.

    Returns: (events_list, occurrences_list)
    """

    logger.info("="*70)
    logger.info("CITIZEN SCIENCE PROCESSING PIPELINE")
    logger.info("="*70)

    # Count media files in directory
    if data_directory.exists():
        media_files = list(data_directory.glob("*.*"))
        jpeg_count = len(list(data_directory.glob("*.jpeg"))) + len(list(data_directory.glob("*.jpg")))
        heic_count = len(list(data_directory.glob("*.heic"))) + len(list(data_directory.glob("*.HEIC")))
        mov_count = len(list(data_directory.glob("*.MOV"))) + len(list(data_directory.glob("*.mov")))
        mp4_count = len(list(data_directory.glob("*.MP4"))) + len(list(data_directory.glob("*.mp4")))

        logger.info(f"Found {len(media_files)} media files:")
        logger.info(f"  - JPEG/JPG: {jpeg_count}")
        logger.info(f"  - HEIC: {heic_count}")
        logger.info(f"  - MOV: {mov_count}")
        logger.info(f"  - MP4: {mp4_count}\n")

    if index_file and index_file.exists():
        logger.info(f"Using index file: {index_file}")
        # TODO: Parse index file and create real events/occurrences
        events = []
        occurrences = []
    else:
        logger.warning("citizen_science_index.csv NOT PROVIDED")
        logger.warning("Creating STUB events/occurrences with placeholder metadata")
        logger.info("ACTION REQUIRED: User must provide citizen_science_index.csv\n")

        file_count = len(media_files) if data_directory.exists() else 991
        events = create_stub_submission_events(file_count)
        occurrences = create_stub_occurrences(file_count)

    return events, occurrences


def write_outputs(
    events: List[Dict],
    occurrences: List[Dict],
    output_directory: Path
) -> None:
    """Write Events and Occurrences to CSV files."""

    output_directory.mkdir(parents=True, exist_ok=True)

    # Write Events
    events_file = output_directory / "citizen_science_events.csv"
    if events:
        with open(events_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(events[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for event in events:
                writer.writerow(event)
        logger.info(f"✓ Written {len(events)} events to {events_file}")

    # Write Occurrences
    occurrences_file = output_directory / "citizen_science_observations_stub.csv"
    if occurrences:
        with open(occurrences_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(occurrences[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for occ in occurrences:
                writer.writerow(occ)
        logger.info(f"✓ Written {len(occurrences)} observation stubs to {occurrences_file}")
        logger.info(f"  STATUS: Awaiting manual curation and species identification")


def main():
    data_dir = Path("/fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/citizen_science")
    output_dir = Path("/fs/ess/PAS2136/TheWilds2025/processing_output/detections_manual")
    index_file = Path("/fs/ess/PAS2136/TheWilds2025/citizen_science_index.csv")

    logger.info(f"Input: {data_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Index file: {index_file}\n")

    events, occurrences = process_citizen_science(data_dir, output_dir, index_file)

    logger.info(f"\nGenerated:")
    logger.info(f"  - {len(events)} submission events")
    logger.info(f"  - {len(occurrences)} observation stubs\n")

    write_outputs(events, occurrences, output_dir)

    logger.info("="*70)
    logger.info("NEXT STEPS:")
    logger.info("1. Provide citizen_science_index.csv mapping files to submission metadata")
    logger.info("2. Run manual curation to identify species in submitted photos/videos")
    logger.info("3. Update citizen_science_observations_stub.csv with verified identifications")
    logger.info("="*70)


if __name__ == "__main__":
    main()
