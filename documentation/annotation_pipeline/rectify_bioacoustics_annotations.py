#!/usr/bin/env python3
"""
Rectify existing BirdNET bioacoustic annotations with Darwin Core metadata.

This script reads existing CSV annotations from /fs/ess/PAS2136/TheWilds2025/BioacousticAnalysis/
and maps them to Darwin Core Events (recording sessions) and Occurrences (bird detections).

Input:
  - BirdNET CSV files: [SensorID]_[YYYYMMDD]_[HHMMSS].BirdNET.results.csv
  - Deployment metadata: Song Meter locations, dates, protocols
  - CSV format: Start (s), End (s), Scientific name, Common name, Confidence

Output:
  - darwin_core_events.csv (one per recording session)
  - darwin_core_occurrences.csv (one per BirdNET detection)
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import csv
import json
import re
from typing import Dict, List, Tuple, Optional

# Sensor ID to Deployment mapping
SENSOR_DEPLOYMENT_MAP = {
    # Sensor ID -> (site_id, full_deployment_id, location, gps_lat, gps_lon)
    "SM04": ("TW02", "TW02-SM04", "Nomad Ridge Shelter, right side", 39.82957, -81.73295),
    "SM05": ("TW06", "TW06-SM05", "Zebra Shelter", 39.82870, -81.73756),
    "SM03": ("TW08", "TW08-SM03", "Fence with Vegetation", 39.82892, -81.74392),
    "SM02": ("TW07", "TW07-SM02", "Zipline Tower", 39.82891, -81.74392),
    "SM06": ("TW05", "TW05-SM06", "Lake Trail Gate O", 39.82866, -81.73758),
    "SM01": ("TW09", "TW09-SM01", "Dock, left side", 39.83418, -81.73783),
    "SM001": ("TW05", "TW05-SM06", "Lake Trail Gate O (alt recorder)", 39.82866, -81.73758),
    "SM002": ("TW06", "TW06-SM05", "Zebra Shelter (alt recorder)", 39.82870, -81.73756),
    "2MM18157": ("TW06", "TW06-SM05", "Zebra Shelter (alt recorder 2)", 39.82870, -81.73756),
}

# Deployment date ranges (from metadata)
DEPLOYMENT_DATES = {
    "TW02-SM04": ("2025-08-04", "2025-08-28"),
    "TW05-SM06": ("2025-08-04", "2025-08-28"),
    "TW06-SM05": ("2025-08-04", "2025-08-28"),
    "TW07-SM02": ("2025-08-04", "2025-08-28"),
    "TW08-SM03": ("2025-08-04", "2025-08-28"),
    "TW09-SM01": ("2025-08-14", "2025-08-28"),
}

# Recording protocols
RECORDING_PROTOCOLS = {
    # Sensor ID -> protocol description
    "SM04": "5 minutes every hour",
    "SM05": "15 minutes every hour",
    "SM03": "Sunrise to sunset recording",
    "SM02": "Sunrise to sunset recording",
    "SM06": "Sunrise to sunset recording",
    "SM01": "Sunrise to sunset recording",
    "SM001": "Sunrise to sunset recording",
    "SM002": "Sunrise to sunset recording",
    "2MM18157": "15 minutes every hour",
}


def parse_filename(filename: str) -> Optional[Tuple[str, datetime]]:
    """
    Parse BirdNET filename to extract sensor ID and timestamp.

    Format: [SensorID]_[YYYYMMDD]_[HHMMSS].BirdNET.results.csv
    Example: SM04_20250812_190000.BirdNET.results.csv

    Returns: (sensor_id, datetime) or None if parse fails
    """
    pattern = r"^([A-Z0-9]+)_(\d{8})_(\d{6})\.BirdNET\.results\.csv$"
    match = re.match(pattern, filename)

    if not match:
        return None

    sensor_id, date_str, time_str = match.groups()

    try:
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(time_str[0:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:6])

        dt = datetime(year, month, day, hour, minute, second)
        return (sensor_id, dt)
    except (ValueError, IndexError):
        return None


def discover_annotation_files(base_dir: Path) -> List[Path]:
    """Find all BirdNET annotation CSV files."""
    files = []

    # Search both subdirectories
    for subdir in ["BirdNet_EveryHour", "BirdnetCSV_SunriseSunset"]:
        search_path = base_dir / subdir
        if search_path.exists():
            files.extend(search_path.glob("*.BirdNET.results.csv"))

    return sorted(files)


def create_event_record(
    sensor_id: str,
    timestamp: datetime,
    deployment_id: str,
    location_name: str,
    lat: float,
    lon: float,
    protocol: str,
) -> Dict:
    """Create a Darwin Core Event record for a recording session."""

    # Deployment dates (if available)
    deploy_start, deploy_end = DEPLOYMENT_DATES.get(deployment_id, ("2025-08-04", "2025-08-28"))

    # Event ID: site_session_date
    event_id = f"{deployment_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

    return {
        "eventID": event_id,
        "parentEventID": "TheWilds_2025_bioacoustics",
        "eventType": "RecordingSession",
        "eventDate": timestamp.strftime("%Y-%m-%d"),
        "eventTime": timestamp.strftime("%H:%M:%S"),
        "eventEndDate": timestamp.strftime("%Y-%m-%d"),
        "eventEndTime": (timestamp + timedelta(minutes=5)).strftime("%H:%M:%S"),  # Assume 5 min recording
        "samplingProtocol": f"Acoustic monitoring ({protocol})",
        "samplingEffort": f"1 recording session, ~5 minutes of audio (protocol: {protocol})",
        "decimalLatitude": lat,
        "decimalLongitude": lon,
        "coordinateUncertaintyInMeters": 5,
        "geodeticDatum": "WGS84",
        "locality": location_name,
        "platformID": f"Song_Meter_4_{sensor_id}",
        "recordedBy": "Automated Song Meter recorder",
        "fieldNotes": f"Sensor ID: {sensor_id}. BirdNET v2 automated analysis.",
        "datasetID": "TheWilds_2025_bioacoustics",
        "datasetName": "The Wilds 2025 Bioacoustic Survey",
    }


def create_occurrence_record(
    event_id: str,
    timestamp: datetime,
    audio_segment_start_sec: float,
    audio_segment_end_sec: float,
    scientific_name: str,
    common_name: str,
    confidence: float,
    sensor_id: str,
    sequence_idx: int,
) -> Dict:
    """Create a Darwin Core Occurrence record for a BirdNET detection."""

    # Occurrence ID: event_sequence
    occurrence_id = f"{event_id}_{sequence_idx:04d}"

    return {
        "occurrenceID": occurrence_id,
        "eventID": event_id,
        "scientificName": scientific_name,
        "commonName": common_name,
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Aves",
        "taxonRank": "species",
        "vernacularName": common_name,
        "occurrenceStatus": "present",
        "basisOfRecord": "MachineObservation",
        "recordedBy": "BirdNET v2 automated audio classifier",
        "identificationVerificationStatus": "unverified",
        "individualCount": 1,
        "eventDate": timestamp.strftime("%Y-%m-%d"),
        "eventTime": timestamp.strftime("%H:%M:%S"),
        "frequency_hz_start": 0,
        "frequency_hz_end": 15000,
        "temporal_location_sec_start": audio_segment_start_sec,
        "temporal_location_sec_end": audio_segment_end_sec,
        "associatedOccurrences": f"Audio segment: {audio_segment_start_sec}-{audio_segment_end_sec} seconds",
        "identificationRemarks": f"BirdNET confidence: {confidence:.4f}",
        "datasetID": "TheWilds_2025_bioacoustics",
        "datasetName": "The Wilds 2025 Bioacoustic Survey",
    }


def process_annotation_file(
    csv_path: Path,
) -> Tuple[Optional[Dict], List[Dict]]:
    """
    Process a single BirdNET CSV annotation file.

    Returns: (event_record, [occurrence_records])
    """

    # Parse filename
    result = parse_filename(csv_path.name)
    if result is None:
        print(f"⚠ Skipping {csv_path.name}: Cannot parse filename")
        return None, []

    sensor_id, timestamp = result

    # Map to deployment
    if sensor_id not in SENSOR_DEPLOYMENT_MAP:
        print(f"⚠ Skipping {csv_path.name}: Unknown sensor ID {sensor_id}")
        return None, []

    site_id, deployment_id, location_name, lat, lon = SENSOR_DEPLOYMENT_MAP[sensor_id]
    protocol = RECORDING_PROTOCOLS.get(sensor_id, "Unknown protocol")

    # Create Event
    event = create_event_record(
        sensor_id=sensor_id,
        timestamp=timestamp,
        deployment_id=deployment_id,
        location_name=location_name,
        lat=lat,
        lon=lon,
        protocol=protocol,
    )

    event_id = event["eventID"]

    # Parse BirdNET CSV
    occurrences = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                print(f"⚠ Skipping {csv_path.name}: Empty CSV")
                return event, []

            # Expected columns: Start (s), End (s), Scientific name, Common name, Confidence
            for idx, row in enumerate(reader, start=1):
                try:
                    start_sec = float(row.get("Start (s)", 0))
                    end_sec = float(row.get("End (s)", 0))
                    scientific_name = row.get("Scientific name", "Unknown")
                    common_name = row.get("Common name", "Unknown")
                    confidence = float(row.get("Confidence", 0))

                    occ = create_occurrence_record(
                        event_id=event_id,
                        timestamp=timestamp,
                        audio_segment_start_sec=start_sec,
                        audio_segment_end_sec=end_sec,
                        scientific_name=scientific_name,
                        common_name=common_name,
                        confidence=confidence,
                        sensor_id=sensor_id,
                        sequence_idx=idx,
                    )
                    occurrences.append(occ)

                except ValueError as e:
                    print(f"⚠ Row {idx} in {csv_path.name}: {e}")
                    continue

    except Exception as e:
        print(f"✗ Error reading {csv_path.name}: {e}")
        return event, []

    return event, occurrences


def main():
    parser = argparse.ArgumentParser(
        description="Rectify existing BirdNET annotations with Darwin Core metadata"
    )
    parser.add_argument(
        "--input-dir",
        default="/fs/ess/PAS2136/TheWilds2025/BioacousticAnalysis",
        help="Directory containing BirdNET CSV files"
    )
    parser.add_argument(
        "--output-dir",
        default="/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata",
        help="Output directory for Darwin Core CSV files"
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=0,
        help="Limit to first N files (0 = all)"
    )

    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)

    if not input_path.exists():
        print(f"✗ Input directory not found: {input_path}")
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print("Rectifying BirdNET Bioacoustic Annotations")
    print(f"{'='*70}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}\n")

    # Discover annotation files
    annotation_files = discover_annotation_files(input_path)

    if args.sample_limit > 0:
        annotation_files = annotation_files[:args.sample_limit]

    print(f"Found {len(annotation_files)} BirdNET annotation files")

    # Process all files
    all_events = {}  # event_id -> event_record (deduplicate)
    all_occurrences = []

    for idx, csv_file in enumerate(annotation_files, start=1):
        event, occurrences = process_annotation_file(csv_file)

        if event:
            event_id = event["eventID"]
            # Use first occurrence of event if duplicates exist
            if event_id not in all_events:
                all_events[event_id] = event

            all_occurrences.extend(occurrences)

            if idx % 100 == 0:
                print(f"Processed {idx}/{len(annotation_files)} files...")

    print(f"\nProcessed {len(annotation_files)} annotation files:")
    print(f"  - {len(all_events)} unique recording session Events")
    print(f"  - {len(all_occurrences)} bird detections (Occurrences)")

    # Write Events CSV
    events_file = output_path / "bioacoustics_darwin_core_events.csv"
    if all_events:
        with open(events_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(all_events[list(all_events.keys())[0]].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for event in all_events.values():
                writer.writerow(event)
        print(f"\n✓ Events written: {events_file}")
        print(f"  Total rows: {len(all_events)}")

    # Write Occurrences CSV
    occurrences_file = output_path / "bioacoustics_darwin_core_occurrences.csv"
    if all_occurrences:
        with open(occurrences_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(all_occurrences[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for occ in all_occurrences:
                writer.writerow(occ)
        print(f"✓ Occurrences written: {occurrences_file}")
        print(f"  Total rows: {len(all_occurrences)}")

    # Summary statistics
    print(f"\n{'='*70}")
    print("Summary Statistics")
    print(f"{'='*70}")

    # Species distribution
    species_counts = {}
    for occ in all_occurrences:
        species = occ.get("scientificName", "Unknown")
        species_counts[species] = species_counts.get(species, 0) + 1

    print(f"\nTop 10 detected species:")
    for species, count in sorted(species_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {species}: {count} detections")

    print(f"\nTotal unique species: {len(species_counts)}")
    print(f"\n✓ Rectification complete!")


if __name__ == "__main__":
    main()
