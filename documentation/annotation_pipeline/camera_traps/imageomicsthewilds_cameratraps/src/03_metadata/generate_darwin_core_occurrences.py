"""
Generate Darwin Core Occurrence records from camera trap detections.

Occurrences represent individual observations of species. In camera trap data:
- Each detection (bounding box) = 1+ occurrences
- Multiple individuals in one image = multiple occurrences
- Links to Event (session/deployment) via eventID
- Links to images via image path

This follows Darwin Core standards for biodiversity observation records.
See: https://dwc.tdwg.org/terms/
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def generate_darwin_core_occurrences(
    detections_csv,
    events_csv,
    output_path="darwin_core_occurrences.csv"
):
    """
    Generate Darwin Core Occurrence records from detection results.

    Each row represents one species observation (detection box).
    Multiple detections per image = multiple occurrences.

    Args:
        detections_csv: Path to detections_with_validated_timestamps.csv
        events_csv: Path to darwin_core_events.csv
        output_path: Where to save output CSV
    """

    print(f"Loading detections from: {detections_csv}")
    detections = pd.read_csv(detections_csv)
    print(f"  Loaded {len(detections)} detection records")

    print(f"Loading events from: {events_csv}")
    events = pd.read_csv(events_csv)

    occurrences = []

    for idx, row in detections.iterrows():
        # Extract event ID from site_cam and timestamp
        site_cam = row.get("site_cam", "unknown")
        timestamp = row.get("timestamp", "")

        # Create eventID by matching to events table
        # For now, use simple matching; in production would do proper join
        matching_events = events[
            (events['eventRemarks'].str.contains(site_cam, na=False)) &
            (events['eventDate'] <= str(timestamp)[:10]) &
            (events['eventEndDate'] >= str(timestamp)[:10])
        ]

        if len(matching_events) > 0:
            event_id = matching_events.iloc[0]['eventID']
        else:
            event_id = f"{site_cam}_unknown"

        # Create unique occurrence ID
        detection_index = row.get("detection_index", 0)
        occurrence_id = f"{event_id}_{str(timestamp).replace(':', '').replace(' ', 'T')}_{detection_index:03d}"

        # Map species labels to scientific names
        bioclip_label = row.get("bioclip_label", "unknown").lower()

        taxon_map = {
            "deer": {
                "scientificName": "Odocoileus virginianus (Zimmermann, 1780)",
                "kingdom": "Animalia",
                "phylum": "Chordata",
                "class": "Mammalia",
                "order": "Artiodactyla",
                "family": "Cervidae",
                "genus": "Odocoileus",
                "species": "virginianus",
                "commonName": "White-tailed Deer"
            },
            "bird": {
                "scientificName": "Aves (unidentified)",
                "kingdom": "Animalia",
                "phylum": "Chordata",
                "class": "Aves",
                "order": "Unknown",
                "family": "Unknown",
                "genus": "Unknown",
                "species": "Unknown",
                "commonName": "Bird (unidentified)"
            }
        }

        # Default to bird if unrecognized
        if "deer" in bioclip_label:
            taxon_info = taxon_map["deer"]
        else:
            taxon_info = taxon_map["bird"]

        occurrence_record = {
            # Darwin Core required/recommended identifier fields
            "occurrenceID": occurrence_id,
            "eventID": event_id,
            "catalogNumber": f"{site_cam}_{str(timestamp).replace(':','').replace(' ','T')}",

            # Taxonomic information
            "scientificName": taxon_info["scientificName"],
            "kingdom": taxon_info["kingdom"],
            "phylum": taxon_info["phylum"],
            "class": taxon_info["class"],
            "order": taxon_info["order"],
            "family": taxon_info["family"],
            "genus": taxon_info["genus"],
            "species": taxon_info["species"],
            "taxonRank": "species",
            "vernacularName": taxon_info["commonName"],

            # Taxonomic authority (GBIF, NCBI, etc.)
            "scientificNameAuthority": "GBIF Taxonomic Backbone",
            "scientificNameID": f"urn:lsid:gbif.org:usages:{bioclip_label}",

            # Observation details
            "occurrenceStatus": "present",
            "occurrenceRemarks": f"Detection from camera trap image: {row.get('image', 'unknown')}",

            # Individual count (inferred from single detection)
            "individualCount": 1,  # One detection = at least 1 individual (conservative estimate)
            "lifeStage": "unknown",  # Could be inferred from size if available
            "sex": "unknown",

            # Behavior and attributes
            "behavior": "",  # Could be extracted from image context
            "establishmentMeans": "wild",
            "degreeOfEstablishment": "native",

            # Observation details
            "recordedBy": "Automated camera trap detection (YOLO + BioCLIP)",
            "basisOfRecord": "MachineObservation",  # All detections are automated

            # Detection confidence
            "identificationVerificationStatus": "unverified",  # Automated, not manually verified
            "identificationRemarks": f"BioCLIP confidence: {row.get('bioclip_score', 'N/A')}, YOLO confidence: {row.get('yolo_conf', 'N/A')}",

            # Data quality fields
            "datasetID": "TheWilds_2025_camera_traps",
            "datasetName": "The Wilds 2025 Camera Trap Survey",

            # Temporal information
            "eventDate": str(timestamp)[:10] if pd.notna(timestamp) else "",
            "eventTime": str(timestamp)[11:19] if pd.notna(timestamp) else "",

            # Location from camera with depth estimation
            # Use GPS-projected animal location if available, fallback to camera location
            "decimalLatitude": row.get("animal_lat") if pd.notna(row.get("animal_lat")) else row.get("camera_lat", ""),
            "decimalLongitude": row.get("animal_lon") if pd.notna(row.get("animal_lon")) else row.get("camera_lon", ""),
            "spatialReferenceSystem": "WGS84",
            "coordinateUncertaintyMeters": 50,  # Approximate: 50m uncertainty from depth estimation

            # Detection-specific metadata
            "associatedMedia": row.get("image_path", ""),
            "associatedOccurrences": f"Detection box: ({row.get('xmin', '')}, {row.get('ymin', '')}, {row.get('xmax', '')}, {row.get('ymax', '')}), Distance: {row.get('distance_m', 'unknown')}m, Angle: {row.get('angle_deg', 'unknown')}°",

            # Validation flags from timestamp processing
            "validationFlag": row.get("validation_flag", ""),
        }

        occurrences.append(occurrence_record)

    # Create DataFrame
    df = pd.DataFrame(occurrences)

    # Reorder columns (Darwin Core standard order)
    core_cols = [
        'occurrenceID', 'eventID', 'catalogNumber',
        'scientificName', 'scientificNameAuthority', 'scientificNameID',
        'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species',
        'taxonRank', 'vernacularName',
        'occurrenceStatus', 'occurrenceRemarks',
        'individualCount', 'lifeStage', 'sex',
        'behavior', 'establishmentMeans', 'degreeOfEstablishment',
        'eventDate', 'eventTime',
        'decimalLatitude', 'decimalLongitude', 'spatialReferenceSystem',
        'associatedMedia', 'associatedOccurrences',
        'recordedBy', 'basisOfRecord',
        'identificationVerificationStatus', 'identificationRemarks',
        'datasetID', 'datasetName',
        'validationFlag'
    ]

    # Keep only existing columns in correct order
    existing_cols = [c for c in core_cols if c in df.columns]
    df = df[existing_cols]

    # Save
    df.to_csv(output_path, index=False)

    print(f"\n✓ Generated {len(df)} Darwin Core Occurrence records")
    print(f"  Output: {output_path}")
    print(f"\n  Detections by species:")
    species_counts = df['vernacularName'].value_counts()
    for species, count in species_counts.items():
        print(f"    {species}: {count}")
    print(f"\n  Detections by camera:")
    camera_counts = df['eventID'].value_counts()
    for camera, count in camera_counts.items():
        print(f"    {camera}: {count}")

    return df


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        detections_csv = sys.argv[1]
        events_csv = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else "darwin_core_occurrences.csv"
    else:
        detections_csv = "detections_with_validated_timestamps.csv"
        events_csv = "darwin_core_events.csv"
        output = "darwin_core_occurrences.csv"

    generate_darwin_core_occurrences(detections_csv, events_csv, output)
