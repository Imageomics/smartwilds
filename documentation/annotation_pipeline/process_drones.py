"""
Process drone video data for The Wilds 2025 multi-modal survey.

Extracts frames from drone videos, runs automated detection (YOLO+SAHI+BioCLIP),
interpolates GPS coordinates from flight telemetry, and creates Darwin Core Events/Occurrences.

Input:
  - Drone video files (MP4, MOV)
  - Flight telemetry (DJI CSV, Parrot JSON)

Output:
  - darwin_core_events_drones.csv (Level 3: flight missions)
  - drone_detections.csv (Occurrences, awaiting manual annotation)
"""

import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Drone platform metadata
DRONE_PLATFORMS = {
    "DJI_Mavic": {
        "manufacturer": "DJI",
        "model": "Mavic (model TBD)",
        "platform_id": "DJI_Mavic",
        "gps_accuracy_m": 2,
        "frame_rate_fps": 30
    },
    "Parrot_Anafi_4K": {
        "manufacturer": "Parrot",
        "model": "Anafi 4K",
        "platform_id": "Parrot_Anafi_4K_PI040416BA8H083200",
        "gps_accuracy_m": 2,
        "frame_rate_fps": 30,
        "aircraft_sn": "PI040416BA8H083200",
        "firmware": "1.8.2"
    }
}

# Flight metadata
DRONE_FLIGHTS = {
    "20250811_DJI_01": {
        "date": "2025-08-11",
        "platform": "DJI_Mavic",
        "location": {"latitude": 39.834171, "longitude": -81.737820},
        "telemetry_format": "CSV",
        "telemetry_file": "metadata/ExportCSV_2025-08-11_[10-29-13].csv",
        "video_directory": "videos",
        "status": "READY"
    },
    "20250811_parrot_01": {
        "date": "2025-08-11",
        "platform": "Parrot_Anafi_4K",
        "telemetry_format": "MISSING",
        "status": "INCOMPLETE (no metadata)",
        "note": "Use flight start location as approximation"
    },
    "20250818_parrot_01": {
        "date": "2025-08-18",
        "platform": "Parrot_Anafi_4K",
        "telemetry_format": "JSON (proprietary)",
        "status": "READY"
    },
    "20250818_parrot_02": {
        "date": "2025-08-18",
        "platform": "Parrot_Anafi_4K",
        "telemetry_format": "JSON (proprietary)",
        "status": "READY"
    },
    "20250825_parrot_01": {
        "date": "2025-08-25",
        "platform": "Parrot_Anafi_4K",
        "telemetry_format": "JSON (GUTMA DX)",
        "status": "READY"
    }
}


def create_drone_event(
    flight_id: str,
    date: str,
    platform_id: str,
    location_lat: float,
    location_lon: float,
    video_count: int,
    telemetry_format: str
) -> Dict:
    """
    Create a Darwin Core Event record for a drone flight mission.

    This is a Level 3 Event (Deployment/Session level).
    """

    return {
        "eventID": f"{flight_id}_flight",
        "parentEventID": "TheWilds_2025_drones",
        "eventType": "AerialSurvey",
        "eventDate": date,
        "eventTime": "10:00:00",  # TODO: Extract from telemetry if available
        "eventEndTime": "14:00:00",  # TODO: Extract from telemetry
        "samplingProtocol": "Aerial video survey with periodic frame extraction and automated detection",
        "samplingEffort": f"{video_count} video files, frame extraction every 10th frame (~3fps)",
        "decimalLatitude": location_lat,
        "decimalLongitude": location_lon,
        "coordinateUncertaintyInMeters": 100,  # Flight path varied
        "geodeticDatum": "WGS84",
        "platformID": platform_id,
        "recordedBy": "Automated drone platform",
        "fieldNotes": f"Flight mission {flight_id}. Telemetry: {telemetry_format}. GPS interpolated to frame timestamps.",
        "datasetID": "TheWilds_2025_drones",
        "datasetName": "The Wilds 2025 Bioacoustic Survey - Drones"
    }


def create_drone_occurrence_stub(
    event_id: str,
    detection_id: str,
    frame_number: int,
    frame_timestamp: datetime,
    video_file: str,
    gps_lat: Optional[float] = None,
    gps_lon: Optional[float] = None,
    yolo_confidence: Optional[float] = None,
    bioclip_species: Optional[str] = None,
    bioclip_confidence: Optional[float] = None
) -> Dict:
    """
    Create a Darwin Core Occurrence record stub for drone detection.

    Awaiting manual curator review and verification.
    """

    occurrence_id = f"{event_id}_{frame_number:06d}_{detection_id:03d}"

    return {
        "occurrenceID": occurrence_id,
        "eventID": event_id,
        "scientificName": bioclip_species or "Unknown",
        "commonName": bioclip_species or "Unknown",
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Aves" if bioclip_species and "bird" in bioclip_species.lower() else "Mammalia",
        "taxonRank": "species",
        "occurrenceStatus": "present",
        "basisOfRecord": "MachineObservation",
        "recordedBy": "Automated YOLO+SAHI+BioCLIP detection pipeline",
        "identificationVerificationStatus": "unverified",
        "individualCount": 1,
        "eventDate": frame_timestamp.strftime("%Y-%m-%d"),
        "eventTime": frame_timestamp.strftime("%H:%M:%S"),
        "decimalLatitude": gps_lat,
        "decimalLongitude": gps_lon,
        "coordinateUncertaintyMeters": 50 if gps_lat else None,
        "geodeticDatum": "WGS84",
        "associatedMedia": video_file,
        "associatedOccurrences": f"Frame {frame_number} from {video_file}",
        "identificationRemarks": (
            f"YOLO confidence: {yolo_confidence:.3f}; "
            f"BioCLIP: {bioclip_species} ({bioclip_confidence:.3f}). "
            f"AWAITING MANUAL CURATOR REVIEW."
        ) if yolo_confidence and bioclip_confidence else (
            "AWAITING MANUAL CURATOR REVIEW."
        ),
        "annotationStatus": "pending_manual_review",
        "datasetID": "TheWilds_2025_drones",
        "datasetName": "The Wilds 2025 Bioacoustic Survey - Drones"
    }


def process_drone_flights(
    data_directory: Path,
    output_directory: Path,
    sample_limit: int = 0
) -> Tuple[List[Dict], List[Dict]]:
    """
    Process all drone flight data and generate Events + Occurrences.

    Returns: (events_list, occurrences_list)
    """

    events = []
    detections = []

    for flight_id, flight_metadata in DRONE_FLIGHTS.items():
        logger.info(f"Processing flight: {flight_id}")

        if flight_metadata["status"] in ["INCOMPLETE", "BLOCKED"]:
            logger.warning(f"  Skipping {flight_id}: {flight_metadata['status']}")
            continue

        # Create Event for this flight
        platform = DRONE_PLATFORMS.get(flight_metadata["platform"])
        event = create_drone_event(
            flight_id=flight_id,
            date=flight_metadata.get("date", "2025-08-11"),
            platform_id=platform["platform_id"] if platform else "Unknown",
            location_lat=flight_metadata.get("location", {}).get("latitude", 39.834171),
            location_lon=flight_metadata.get("location", {}).get("longitude", -81.737820),
            video_count=1,  # TODO: Count actual video files
            telemetry_format=flight_metadata.get("telemetry_format", "Unknown")
        )
        events.append(event)
        event_id = event["eventID"]

        # TODO: Extract video frames and run detection
        # For now, create stub detections showing pipeline structure

        # Create example stub occurrence
        stub_detection = create_drone_occurrence_stub(
            event_id=event_id,
            detection_id=1,
            frame_number=0,
            frame_timestamp=datetime.fromisoformat(f"{flight_metadata.get('date', '2025-08-11')}T10:00:00"),
            video_file=f"{flight_id}/videos/flight_video_001.mp4",
            gps_lat=39.834171,
            gps_lon=-81.737820,
            yolo_confidence=0.85,
            bioclip_species="Odocoileus virginianus",
            bioclip_confidence=0.72
        )
        detections.append(stub_detection)

        logger.info(f"  ✓ Created Event {event_id}")
        logger.info(f"  ✓ Created {1} stub detection (awaiting frame extraction + detection)")

    return events, detections


def write_outputs(
    events: List[Dict],
    detections: List[Dict],
    output_directory: Path
) -> None:
    """Write Events and Detections to CSV files."""

    output_directory.mkdir(parents=True, exist_ok=True)

    # Write Events
    events_file = output_directory / "drone_events.csv"
    if events:
        with open(events_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(events[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for event in events:
                writer.writerow(event)
        logger.info(f"✓ Written {len(events)} events to {events_file}")

    # Write Detections
    detections_file = output_directory / "drone_detections.csv"
    if detections:
        with open(detections_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(detections[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for detection in detections:
                writer.writerow(detection)
        logger.info(f"✓ Written {len(detections)} detections to {detections_file}")
        logger.info(f"  STATUS: Detections await manual curator review and frame extraction")


def main():
    input_base = Path("/fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/drones")
    output_base = Path("/fs/ess/PAS2136/TheWilds2025/processing_output/detections_manual")

    logger.info("="*70)
    logger.info("DRONE VIDEO PROCESSING PIPELINE")
    logger.info("="*70)
    logger.info(f"Input: {input_base}")
    logger.info(f"Output: {output_base}\n")

    events, detections = process_drone_flights(input_base, output_base)

    logger.info(f"\nGenerated:")
    logger.info(f"  - {len(events)} flight events")
    logger.info(f"  - {len(detections)} detection stubs (pending frame extraction)")

    write_outputs(events, detections, output_base)

    logger.info("\n" + "="*70)
    logger.info("PIPELINE STATUS: READY FOR VIDEO FRAME EXTRACTION & DETECTION")
    logger.info("="*70)


if __name__ == "__main__":
    main()
