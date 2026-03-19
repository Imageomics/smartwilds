#!/usr/bin/env python3
"""
Systematically generate Darwin Core Events and Occurrences for all camera trap deployments.

This script discovers camera trap data in subdirectories, processes each camera deployment,
and generates FAIR² compliant metadata files.

Usage:
    python process_all_camera_traps.py \
        --base-dir /path/to/TheWilds2025 \
        --output-dir ./results

This will:
1. Discover all camera trap directories (TW##-CT##)
2. For each camera, generate:
   - darwin_core_events.csv (survey session metadata)
   - darwin_core_occurrences.csv (species observations)
   - platform_specifications.json (hardware specs)
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import csv
import json

# Add src directories to path for imports
import os
sys.path.insert(0, str(Path(__file__).parent / "src" / "01_events"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "03_metadata"))

try:
    from camera_deployment_metadata import DEPLOYMENTS, get_deployment_info
except ImportError as e:
    print(f"Error importing camera_deployment_metadata: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


def discover_camera_directories(base_dir):
    """
    Discover all camera trap directories recursively.

    Returns dict mapping camera_id -> (directory_path, campaign_name)
    """
    base_path = Path(base_dir)
    cameras = {}

    # Pattern: TW##-CT## or TW##_CT##
    import re
    camera_pattern = re.compile(r"(TW\d+-?CT\d+)")

    for path in base_path.rglob("*"):
        if not path.is_dir():
            continue

        match = camera_pattern.search(path.name)
        if not match:
            continue

        camera_id = match.group(1)
        # Normalize naming (TW##_CT## -> TW##-CT##)
        camera_id = camera_id.replace("_", "-")

        # Determine campaign from path
        campaign = "unknown"
        path_str = str(path)
        if "20250630" in path_str or "20250703" in path_str:
            campaign = "20250630_20250703"
        elif "20250804" in path_str or "20250828" in path_str:
            campaign = "20250804_20250828"
        elif "20250908" in path_str:
            campaign = "20250908_20250908"

        cameras[camera_id] = {
            "path": path,
            "campaign": campaign,
            "images": list(path.glob("*.[jJ][pP][gG]"))
        }

    return cameras


def generate_events_csv(output_dir):
    """
    Generate darwin_core_events.csv from deployment metadata.
    """
    output_path = Path(output_dir) / "darwin_core_events.csv"

    events = []
    processed = set()

    for site_cam, info in DEPLOYMENTS.items():
        # Create unique key (camera + campaign)
        campaign = info.get("campaign", "unknown")
        key = f"{site_cam}_{campaign}"

        if key in processed:
            continue
        processed.add(key)

        deploy_date = info["deploy_date"]
        retrieve_date = info["retrieve_date"]
        event_id = f"{site_cam}_{campaign}"

        event_record = {
            "eventID": event_id,
            "eventDate": deploy_date.strftime("%Y-%m-%d"),
            "eventEndDate": retrieve_date.strftime("%Y-%m-%d"),
            "eventTime": deploy_date.strftime("%H:%M:%S") if deploy_date.hour > 0 else "00:00:00",
            "eventEndTime": "23:59:59",
            "samplingProtocol": "Passive infrared camera trap (PIR trigger)",
            "samplingEffort": f"{(retrieve_date - deploy_date).days} days, continuous 24/7 monitoring",
            "decimalLatitude": info.get("lat", ""),
            "decimalLongitude": info.get("lon", ""),
            "coordinateUncertaintyInMeters": 5,
            "geodeticDatum": "WGS84",
            "locality": f"TheWilds Site TW{site_cam.split('-')[0][-2:]}",
            "habitat": "Mixed deciduous forest",
            "sampleSizeValue": (retrieve_date - deploy_date).days,
            "sampleSizeUnit": "days",
            "fieldNotes": info.get("issues", "No known issues"),
            "eventRemarks": f"Camera {site_cam}, deployed {deploy_date.strftime('%Y-%m-%d')} to {retrieve_date.strftime('%Y-%m-%d')}",
        }

        events.append(event_record)

    # Write events CSV
    if events:
        fieldnames = [
            "eventID", "eventDate", "eventEndDate", "eventTime", "eventEndTime",
            "samplingProtocol", "samplingEffort",
            "decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters",
            "geodeticDatum", "locality", "habitat",
            "sampleSizeValue", "sampleSizeUnit",
            "fieldNotes", "eventRemarks"
        ]

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(events)

        print(f"✓ Generated {len(events)} Event records: {output_path}")
        return events
    else:
        print("⚠ No events generated")
        return []


def generate_occurrences_csv(detections_csv, events_csv, output_dir):
    """
    Generate darwin_core_occurrences.csv from detections.
    """
    import pandas as pd

    output_path = Path(output_dir) / "darwin_core_occurrences.csv"

    if not Path(detections_csv).exists():
        print(f"⚠ Detections file not found: {detections_csv}")
        return

    print(f"Loading detections from: {detections_csv}")
    detections = pd.read_csv(detections_csv)

    # Read events to get event IDs
    events = pd.read_csv(events_csv) if Path(events_csv).exists() else pd.DataFrame()

    occurrences = []

    for idx, row in detections.iterrows():
        site_cam = row.get("site_cam", "unknown")
        timestamp = row.get("timestamp", "")

        # Find matching event
        matching_events = events[
            (events['eventRemarks'].str.contains(site_cam, na=False)) &
            (pd.to_datetime(events['eventDate']) <= pd.to_datetime(str(timestamp)[:10])) &
            (pd.to_datetime(events['eventEndDate']) >= pd.to_datetime(str(timestamp)[:10]))
        ] if not events.empty else pd.DataFrame()

        if len(matching_events) > 0:
            event_id = matching_events.iloc[0]['eventID']
        else:
            event_id = f"{site_cam}_unknown"

        detection_index = row.get("detection_index", 0)
        occurrence_id = f"{event_id}_{str(timestamp).replace(':', '').replace(' ', 'T').replace('-', '')}_{detection_index:03d}"

        # Map species
        bioclip_label = str(row.get("bioclip_label", "unknown")).lower()
        if "deer" in bioclip_label:
            scientific_name = "Odocoileus virginianus (Zimmermann, 1780)"
            genus = "Odocoileus"
            species = "virginianus"
            family = "Cervidae"
            common_name = "White-tailed Deer"
        else:
            scientific_name = "Aves (unidentified)"
            genus = "Unknown"
            species = "Unknown"
            family = "Unknown"
            common_name = "Bird (unidentified)"

        # Use animal location if available, fallback to camera
        lat = row.get("animal_lat") if pd.notna(row.get("animal_lat")) else row.get("camera_lat", "")
        lon = row.get("animal_lon") if pd.notna(row.get("animal_lon")) else row.get("camera_lon", "")

        occurrence_record = {
            "occurrenceID": occurrence_id,
            "eventID": event_id,
            "scientificName": scientific_name,
            "kingdom": "Animalia",
            "phylum": "Chordata",
            "class": "Mammalia" if "deer" in bioclip_label else "Aves",
            "order": "Artiodactyla" if "deer" in bioclip_label else "Unknown",
            "family": family,
            "genus": genus,
            "species": species,
            "taxonRank": "species",
            "vernacularName": common_name,
            "occurrenceStatus": "present",
            "individualCount": 1,
            "eventDate": str(timestamp)[:10] if pd.notna(timestamp) else "",
            "eventTime": str(timestamp)[11:19] if pd.notna(timestamp) else "",
            "decimalLatitude": lat,
            "decimalLongitude": lon,
            "coordinateUncertaintyMeters": 50,
            "spatialReferenceSystem": "WGS84",
            "associatedMedia": row.get("image_path", ""),
            "associatedOccurrences": f"Distance: {row.get('distance_m', 'unknown')}m, Angle: {row.get('angle_deg', 'unknown')}°",
            "recordedBy": "Automated camera trap detection (YOLO + BioCLIP)",
            "basisOfRecord": "MachineObservation",
            "identificationVerificationStatus": "unverified",
            "identificationRemarks": f"BioCLIP: {row.get('bioclip_score', 'N/A')}, YOLO: {row.get('yolo_conf', 'N/A')}",
            "datasetID": "TheWilds_2025_camera_traps",
            "datasetName": "The Wilds 2025 Camera Trap Survey",
            "validationFlag": row.get("validation_flag", ""),
        }

        occurrences.append(occurrence_record)

    # Write occurrences CSV
    if occurrences:
        fieldnames = [
            "occurrenceID", "eventID", "scientificName",
            "kingdom", "phylum", "class", "order", "family", "genus", "species",
            "taxonRank", "vernacularName",
            "occurrenceStatus", "individualCount",
            "eventDate", "eventTime",
            "decimalLatitude", "decimalLongitude", "coordinateUncertaintyMeters",
            "spatialReferenceSystem", "associatedMedia", "associatedOccurrences",
            "recordedBy", "basisOfRecord",
            "identificationVerificationStatus", "identificationRemarks",
            "datasetID", "datasetName", "validationFlag"
        ]

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(occurrences)

        print(f"✓ Generated {len(occurrences)} Occurrence records: {output_path}")
    else:
        print("⚠ No occurrences generated")


def generate_platform_specs(output_dir):
    """Generate platform_specifications.json"""
    output_path = Path(output_dir) / "platform_specifications.json"

    platform_specs = {
        "metadata": {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "standard": "FAIR² Drones Data Standard",
            "description": "Camera trap platform specifications for The Wilds 2025 survey"
        },
        "platforms": {
            "Garde Pro T5NG": {
                "manufacturer": "Gardepro",
                "model": "Garde Pro T5NG",
                "type": "Passive Infrared Camera Trap",
                "resolution_mp": 4,
                "resolution_pixels": [2560, 1920],
                "field_of_view_degrees": 55,
                "deployments": 6
            },
            "Trail Camera G600": {
                "manufacturer": "Trail Camera",
                "model": "G600",
                "type": "Passive Infrared Camera Trap",
                "resolution_mp": 4,
                "field_of_view_degrees": 55,
                "deployments": 1
            },
            "Garde Pro A3": {
                "manufacturer": "Gardepro",
                "model": "Garde Pro A3",
                "type": "Passive Infrared Camera Trap with Video",
                "resolution_mp": 8,
                "video_resolution": "1920x1080p",
                "field_of_view_degrees": 55,
                "deployments": 1
            }
        },
        "campaigns": {
            "20250630_20250703": {
                "name": "June-July 2025 Campaign",
                "total_cameras": 4,
                "total_images_approximate": 20000
            },
            "20250804_20250828": {
                "name": "August 2025 Campaign",
                "total_cameras": 9,
                "total_images_approximate": 222000
            }
        }
    }

    with open(output_path, "w") as f:
        json.dump(platform_specs, f, indent=2)

    print(f"✓ Generated platform specifications: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Systematically generate Darwin Core metadata for all camera trap deployments"
    )
    parser.add_argument(
        "--base-dir",
        required=True,
        help="Base directory containing camera trap data (e.g., /path/to/TheWilds2025)"
    )
    parser.add_argument(
        "--output-dir",
        default="./camera_trap_metadata",
        help="Output directory for generated CSV files (default: ./camera_trap_metadata)"
    )
    parser.add_argument(
        "--detections-dir",
        help="Directory containing detections_with_validated_timestamps.csv files"
    )
    parser.add_argument(
        "--organized-output",
        action="store_true",
        help="Organize output files by campaign subdirectories under --output-dir"
    )

    args = parser.parse_args()

    base_path = Path(args.base_dir)
    output_base = Path(args.output_dir)

    if not base_path.exists():
        print(f"Error: Base directory not found: {base_path}")
        sys.exit(1)

    output_base.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print("Camera Trap Metadata Generation")
    print(f"{'='*70}")
    print(f"Base directory: {base_path}")
    print(f"Output directory: {output_base}")
    if args.organized_output:
        print(f"Output mode: Organized by campaign")

    # Discover cameras
    print(f"\nDiscovering camera trap directories...")
    cameras = discover_camera_directories(base_path)

    print(f"Found {len(cameras)} camera deployments:")
    for cam_id, cam_info in sorted(cameras.items()):
        print(f"  - {cam_id} ({cam_info['campaign']}): {len(cam_info['images'])} images")

    # Group cameras by campaign
    campaigns = {}
    for cam_id, cam_info in cameras.items():
        campaign = cam_info.get("campaign", "unknown")
        if campaign not in campaigns:
            campaigns[campaign] = []
        campaigns[campaign].append(cam_id)

    # Process each campaign if organized output is enabled
    if args.organized_output:
        print(f"\n{'='*70}")
        print("Processing by campaign (organized output mode)")
        print(f"{'='*70}")

        for campaign in sorted(campaigns.keys()):
            output_path = output_base / campaign
            output_path.mkdir(parents=True, exist_ok=True)

            print(f"\n📁 Campaign: {campaign}")
            print(f"   Output: {output_path}")

            # Generate Events
            print(f"   Generating Darwin Core Events...")
            events = generate_events_csv(output_path)

            # Generate Occurrences (if detections available)
            if args.detections_dir:
                detections_path = Path(args.detections_dir) / campaign / "detections_with_validated_timestamps.csv"
                if detections_path.exists():
                    print(f"   Generating Darwin Core Occurrences...")
                    events_path = output_path / "darwin_core_events.csv"
                    generate_occurrences_csv(str(detections_path), str(events_path), output_path)
                else:
                    print(f"   ⚠ Detections file not found: {detections_path}")

            # Generate Platform Specs
            print(f"   Generating platform specifications...")
            generate_platform_specs(output_path)

        # Summary
        print(f"\n{'='*70}")
        print("✓ Metadata generation complete!")
        print(f"{'='*70}")
        print(f"\nOutput organized by campaign in {output_base}:")
        for campaign in sorted(campaigns.keys()):
            print(f"\n  📁 {campaign}/")
            campaign_dir = output_base / campaign
            if (campaign_dir / "darwin_core_events.csv").exists():
                with open(campaign_dir / "darwin_core_events.csv") as f:
                    num_events = len(f.readlines()) - 1
                print(f"     - darwin_core_events.csv ({num_events} events)")
            if (campaign_dir / "darwin_core_occurrences.csv").exists():
                with open(campaign_dir / "darwin_core_occurrences.csv") as f:
                    num_occurrences = len(f.readlines()) - 1
                print(f"     - darwin_core_occurrences.csv ({num_occurrences} occurrences)")
            if (campaign_dir / "platform_specifications.json").exists():
                print(f"     - platform_specifications.json")

    else:
        # Original workflow: consolidated output
        output_path = output_base

        print(f"\nGenerating Darwin Core Events...")
        events = generate_events_csv(output_path)

        # Generate Occurrences (if detections available)
        if args.detections_dir:
            detections_path = Path(args.detections_dir) / "detections_with_validated_timestamps.csv"
            if detections_path.exists():
                print(f"\nGenerating Darwin Core Occurrences from: {detections_path}")
                events_path = output_path / "darwin_core_events.csv"
                generate_occurrences_csv(str(detections_path), str(events_path), output_path)
            else:
                print(f"⚠ Detections file not found: {detections_path}")
                print("  Skipping Occurrence generation. Run camera_trap_detections.py first.")
        else:
            print(f"\n⚠ No detections directory specified.")
            print("  Use --detections-dir to generate Occurrence records.")

        # Generate Platform Specs
        print(f"\nGenerating platform specifications...")
        generate_platform_specs(output_path)

        # Summary
        print(f"\n{'='*70}")
        print("✓ Metadata generation complete!")
        print(f"{'='*70}")
        print(f"\nOutput files in {output_path}:")
        print(f"  - darwin_core_events.csv: {len(events)} survey sessions")
        print(f"  - darwin_core_occurrences.csv: species observations (if detections provided)")
        print(f"  - platform_specifications.json: hardware specifications")

    print(f"\nNext steps:")
    print(f"1. Review events and occurrences for accuracy")
    print(f"2. Fill in missing GPS coordinates for cameras without metadata")
    print(f"3. Submit events to GBIF and occurrences to EBird (if applicable)")


if __name__ == "__main__":
    main()
