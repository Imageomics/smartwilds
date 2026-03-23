#!/usr/bin/env python3
"""
Generate Darwin Core Events and Occurrences from manually annotated citizen science data.

Input:  wilds_species_datetime.csv (564 annotated photos with species + datetime)
Output: darwin_core_events_citizen_science.csv
        darwin_core_occurrences_citizen_science.csv

Multi-species entries (semicolon-delimited) produce one Occurrence per species per image.
"""

import csv
import re
from datetime import datetime
from pathlib import Path

# ─── Taxonomic lookup ──────────────────────────────────────────────────────────
# Common name → Darwin Core taxonomy
# Species at The Wilds + native wildlife observed in citizen science photos

TAXON_MAP = {
    "African Wild Dog": {
        "scientificName": "Lycaon pictus (Temminck, 1820)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Carnivora", "family": "Canidae",
        "genus": "Lycaon", "specificEpithet": "pictus",
        "taxonRank": "species",
    },
    "Bactrian Camel": {
        "scientificName": "Camelus bactrianus Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Camelidae",
        "genus": "Camelus", "specificEpithet": "bactrianus",
        "taxonRank": "species",
    },
    "Bactrian Deer": {
        "scientificName": "Cervus hanglu bactrianus Lydekker, 1900",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Cervus", "specificEpithet": "hanglu",
        "taxonRank": "subspecies",
    },
    "Banteng": {
        "scientificName": "Bos javanicus d'Alton, 1823",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Bos", "specificEpithet": "javanicus",
        "taxonRank": "species",
    },
    "Bird": {
        "scientificName": "Aves",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "", "family": "",
        "genus": "", "specificEpithet": "",
        "taxonRank": "class",
    },
    "Bison": {
        "scientificName": "Bison bison (Linnaeus, 1758)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Bison", "specificEpithet": "bison",
        "taxonRank": "species",
    },
    "Eland": {
        "scientificName": "Taurotragus oryx (Pallas, 1766)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Taurotragus", "specificEpithet": "oryx",
        "taxonRank": "species",
    },
    "Fish": {
        "scientificName": "Actinopterygii",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Actinopterygii",
        "order": "", "family": "",
        "genus": "", "specificEpithet": "",
        "taxonRank": "class",
    },
    "Fringe-eared Oryx": {
        "scientificName": "Oryx beisa callotis Thomas, 1892",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Oryx", "specificEpithet": "beisa",
        "taxonRank": "subspecies",
    },
    "Giraffe": {
        "scientificName": "Giraffa camelopardalis (Linnaeus, 1758)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Giraffidae",
        "genus": "Giraffa", "specificEpithet": "camelopardalis",
        "taxonRank": "species",
    },
    "Greater One-horned Rhino": {
        "scientificName": "Rhinoceros unicornis Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Rhinocerotidae",
        "genus": "Rhinoceros", "specificEpithet": "unicornis",
        "taxonRank": "species",
    },
    "Grevy's Zebra": {
        "scientificName": "Equus grevyi Oustalet, 1882",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "grevyi",
        "taxonRank": "species",
    },
    "Ostrich": {
        "scientificName": "Struthio camelus Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Struthioniformes", "family": "Struthionidae",
        "genus": "Struthio", "specificEpithet": "camelus",
        "taxonRank": "species",
    },
    "Pere David's Deer": {
        "scientificName": "Elaphurus davidianus Milne-Edwards, 1866",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Elaphurus", "specificEpithet": "davidianus",
        "taxonRank": "species",
    },
    "Persian Onager": {
        "scientificName": "Equus hemionus onager Boddaert, 1785",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "hemionus",
        "taxonRank": "subspecies",
    },
    "Przewalski's Horse": {
        "scientificName": "Equus ferus przewalskii Poliakov, 1881",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "ferus",
        "taxonRank": "subspecies",
    },
    "Scimitar-horned Oryx": {
        "scientificName": "Oryx dammah (Cretzschmar, 1827)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Oryx", "specificEpithet": "dammah",
        "taxonRank": "species",
    },
    "Sichuan Takin": {
        "scientificName": "Budorcas taxicolor tibetana Milne-Edwards, 1874",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Budorcas", "specificEpithet": "taxicolor",
        "taxonRank": "subspecies",
    },
    "Southern White Rhino": {
        "scientificName": "Ceratotherium simum simum (Burchell, 1817)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Rhinocerotidae",
        "genus": "Ceratotherium", "specificEpithet": "simum",
        "taxonRank": "subspecies",
    },
    "Unknown": {
        "scientificName": "Animalia",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "",
        "order": "", "family": "",
        "genus": "", "specificEpithet": "",
        "taxonRank": "kingdom",
    },
}


def parse_datetime_est(dt_str):
    """
    Parse datetime strings like 'Aug 28, 2025, 10:47:01 PM EST'
    Returns (date_str, time_str) in ISO format, or (None, None) on failure.
    """
    if not dt_str or not dt_str.strip():
        return None, None

    dt_str = dt_str.strip().rstrip(" EST").rstrip(" EDT")

    formats = [
        "%b %d, %Y, %I:%M:%S %p",
        "%b %d, %Y, %I:%M %p",
        "%Y-%m-%d %H:%M:%S",
        "%Y:%m:%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
        except ValueError:
            continue

    return None, None


def infer_campaign(date_str):
    """Infer which campaign a date belongs to."""
    if not date_str:
        return "unknown"
    if date_str < "2025-07-04":
        return "20250630_20250703"
    elif date_str < "2025-09-01":
        return "20250804_20250828"
    else:
        return "20250908_20250908"


def generate_darwin_core(input_csv, output_dir, photos_dir=None):
    """
    Generate Darwin Core Events and Occurrences from citizen science annotations.

    Args:
        input_csv: Path to wilds_species_datetime.csv
        output_dir: Where to write output CSVs
        photos_dir: Optional path to photos directory for media references
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read annotations
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} annotated photos from {input_csv}")

    # ─── Build Events ──────────────────────────────────────────────────────
    # Group photos by date to create observation session events
    date_groups = {}
    for row in rows:
        date_str, time_str = parse_datetime_est(row.get("datetime_EST", ""))
        if date_str not in date_groups:
            date_groups[date_str] = []
        date_groups[date_str].append(row)

    events = []
    # Level 1: Project event
    events.append({
        "eventID": "TheWilds_2025_citizen_science",
        "parentEventID": "TheWilds_2025",
        "eventType": "Project",
        "eventDate": "2025-06-30/2025-09-08",
        "samplingProtocol": "Opportunistic photography by visiting researchers and students",
        "sampleSizeValue": len(rows),
        "sampleSizeUnit": "photographs",
        "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
        "decimalLatitude": 39.83,
        "decimalLongitude": -81.74,
        "coordinateUncertaintyInMeters": 5000,
        "geodeticDatum": "WGS84",
        "country": "United States",
        "stateProvince": "Ohio",
        "county": "Muskingum",
        "datasetID": "TheWilds_2025_citizen_science",
        "datasetName": "The Wilds 2025 Multi-Modal Survey - Citizen Science",
        "recordedBy": "Multiple citizen observers",
        "fieldNotes": (
            "564 wildlife photos from 791 total submissions after filtering "
            "(excluded 137 with humans, 77 equipment-only, 225 without species). "
            "20 species identified via manual annotation."
        ),
    })

    # Level 2: Per-date session events
    for date_str in sorted(date_groups.keys()):
        group = date_groups[date_str]
        campaign = infer_campaign(date_str)

        # Get time range
        times = []
        for r in group:
            _, t = parse_datetime_est(r.get("datetime_EST", ""))
            if t:
                times.append(t)
        times.sort()

        events.append({
            "eventID": f"TheWilds_2025_citizen_science_{date_str}",
            "parentEventID": "TheWilds_2025_citizen_science",
            "eventType": "ObservationSession",
            "eventDate": date_str if date_str else "2025-08-04",
            "eventTime": f"{times[0]}/{times[-1]}" if len(times) >= 2 else (times[0] if times else ""),
            "samplingProtocol": "Opportunistic photography",
            "sampleSizeValue": len(group),
            "sampleSizeUnit": "photographs",
            "locality": "The Wilds Conservation Center",
            "decimalLatitude": 39.83,
            "decimalLongitude": -81.74,
            "coordinateUncertaintyInMeters": 5000,
            "geodeticDatum": "WGS84",
            "country": "United States",
            "stateProvince": "Ohio",
            "county": "Muskingum",
            "datasetID": "TheWilds_2025_citizen_science",
            "datasetName": "The Wilds 2025 Multi-Modal Survey - Citizen Science",
            "recordedBy": "Citizen observers",
            "fieldNotes": f"Campaign: {campaign}. {len(group)} photos on {date_str}.",
        })

    # ─── Build Occurrences ─────────────────────────────────────────────────
    occurrences = []
    species_counts = {}
    occurrence_num = 0

    for row in rows:
        filename = row.get("filename", "")
        species_str = row.get("species", "")
        dt_str = row.get("datetime_EST", "")

        date_str, time_str = parse_datetime_est(dt_str)
        event_id = f"TheWilds_2025_citizen_science_{date_str}" if date_str else "TheWilds_2025_citizen_science"

        # Split multi-species entries
        species_list = [s.strip() for s in species_str.split(";") if s.strip()]

        for sp_idx, common_name in enumerate(species_list):
            occurrence_num += 1
            taxon = TAXON_MAP.get(common_name, TAXON_MAP["Unknown"])

            # Track counts
            species_counts[common_name] = species_counts.get(common_name, 0) + 1

            # Build media path
            media_path = ""
            if photos_dir:
                media_path = str(Path(photos_dir) / filename)

            occ = {
                # Identifiers
                "occurrenceID": f"TheWilds_2025_CS_{occurrence_num:04d}",
                "eventID": event_id,
                "catalogNumber": f"CS_{filename}_{sp_idx}",

                # Taxonomy
                "scientificName": taxon["scientificName"],
                "kingdom": taxon["kingdom"],
                "phylum": taxon["phylum"],
                "class": taxon["class"],
                "order": taxon["order"],
                "family": taxon["family"],
                "genus": taxon["genus"],
                "specificEpithet": taxon["specificEpithet"],
                "taxonRank": taxon["taxonRank"],
                "vernacularName": common_name,

                # Observation
                "occurrenceStatus": "present",
                "individualCount": 1,
                "basisOfRecord": "HumanObservation",
                "recordedBy": "Citizen observer (manual annotation)",
                "identifiedBy": "Jenna Kline",
                "identificationVerificationStatus": "verified by expert",
                "identificationRemarks": "Manual species identification from citizen science photograph",

                # Temporal
                "eventDate": date_str if date_str else "",
                "eventTime": time_str if time_str else "",

                # Spatial — The Wilds general area (no per-photo GPS)
                "decimalLatitude": 39.83,
                "decimalLongitude": -81.74,
                "coordinateUncertaintyInMeters": 5000,
                "geodeticDatum": "WGS84",
                "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
                "country": "United States",
                "stateProvince": "Ohio",
                "county": "Muskingum",

                # Establishment
                "establishmentMeans": "managed",
                "degreeOfEstablishment": "captive",
                "occurrenceRemarks": (
                    f"Photographed during guided visit to The Wilds. "
                    f"{'Multi-species photo: ' + species_str if len(species_list) > 1 else ''}"
                ).strip(),

                # Media
                "associatedMedia": media_path or filename,

                # Dataset
                "datasetID": "TheWilds_2025_citizen_science",
                "datasetName": "The Wilds 2025 Multi-Modal Survey - Citizen Science",
            }

            occurrences.append(occ)

    # ─── Write Events CSV ──────────────────────────────────────────────────
    events_path = output_dir / "darwin_core_events_citizen_science.csv"
    if events:
        # Collect all keys across all events (project event may lack some fields)
        all_keys = []
        seen = set()
        for e in events:
            for k in e.keys():
                if k not in seen:
                    all_keys.append(k)
                    seen.add(k)
        with open(events_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(events)
        print(f"\nWrote {len(events)} Events to {events_path}")

    # ─── Write Occurrences CSV ─────────────────────────────────────────────
    occ_path = output_dir / "darwin_core_occurrences_citizen_science.csv"
    if occurrences:
        fieldnames = list(occurrences[0].keys())
        with open(occ_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(occurrences)
        print(f"Wrote {len(occurrences)} Occurrences to {occ_path}")

    # ─── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("Citizen Science Darwin Core Summary")
    print(f"{'='*60}")
    print(f"  Photos annotated:    {len(rows)}")
    print(f"  Occurrence records:  {len(occurrences)} (multi-species photos expand to multiple rows)")
    print(f"  Event records:       {len(events)} (1 project + {len(events)-1} daily sessions)")
    print(f"  Species detected:    {len(species_counts)}")
    print(f"\n  Species counts:")
    for sp, count in sorted(species_counts.items(), key=lambda x: -x[1]):
        print(f"    {sp:<30} {count:>5}")
    print(f"\n  Date range: {min(d for d in date_groups if d) or '?'} to {max(d for d in date_groups if d) or '?'}")
    print(f"  Observation days: {len([d for d in date_groups if d])}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Darwin Core from citizen science annotations")
    parser.add_argument(
        "--input",
        default="/fs/ess/PAS2136/TheWilds2025/processing_output/detections_manual/wilds_species_datetime.csv",
        help="Path to wilds_species_datetime.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core/citizen_science",
        help="Output directory for Darwin Core CSVs",
    )
    parser.add_argument(
        "--photos-dir",
        default="/fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/citizen_science/photos_videos",
        help="Path to citizen science photos directory",
    )

    args = parser.parse_args()
    generate_darwin_core(args.input, args.output_dir, args.photos_dir)
