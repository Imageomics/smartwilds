#!/usr/bin/env python3
"""
Generate Darwin Core Events and Occurrences from camera trap detection CSVs.

Input:  *_detections.csv files from YOLO + BioCLIP pipeline
        (one file per camera deployment per campaign)

Output: darwin_core_events_camera_traps.csv      (hierarchical: project -> deployment events)
        darwin_core_occurrences_camera_traps.csv  (one row per detection)

Each detection row in the input CSV = one Occurrence record.
Each detection CSV file = one deployment Event.
"""

import csv
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
DETECTIONS_DIR = BASE_DIR / "processing_output" / "detections" / "camera_traps"
OUTPUT_DIR = BASE_DIR / "processing_output" / "darwin_core" / "camera_traps"

# --- Site GPS coordinates (decimal degrees) -----------------------------------

SITE_GPS = {
    "TW01": (39.83077, -81.73789),
    "TW02": (39.83066, -81.73792),
    "TW03": (39.83670, -81.73607),
    "TW04": (39.83429, -81.73934),
    "TW05": (39.83537, -81.73842),
    "TW06": (39.83537, -81.73842),
    "TW07": (39.83288, -81.73455),
    "TW08": (39.82900, -81.74378),
    "TW09": (39.82798, -81.74167),
}

SITE_NAMES = {
    "TW01": "Nomad Ridge Shelter (East)",
    "TW02": "Nomad Ridge Shelter (West)",
    "TW03": "Old Giraffe Feeder, Pasture D",
    "TW04": "Lake Trail",
    "TW05": "Lake Trail Gate O",
    "TW06": "Zebra Shelter",
    "TW07": "Zipline Tower",
    "TW08": "Fence with Vegetation",
    "TW09": "Dock",
    "TW11": "Fence overlooking Lake",
}

# --- Taxon lookup (from extract_text_observations.py + BioCLIP labels) --------

TAXON_MAP = {
    # Species-level from The Wilds collection
    "Pere David's Deer": {
        "scientificName": "Elaphurus davidianus Milne-Edwards, 1866",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Elaphurus", "specificEpithet": "davidianus",
        "taxonRank": "species",
    },
    "Grevy's Zebra": {
        "scientificName": "Equus grevyi Oustalet, 1882",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "grevyi",
        "taxonRank": "species",
    },
    "Sichuan Takin": {
        "scientificName": "Budorcas taxicolor tibetana Milne-Edwards, 1874",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Budorcas", "specificEpithet": "taxicolor",
        "taxonRank": "subspecies",
    },
    "Przewalski's Horse": {
        "scientificName": "Equus ferus przewalskii Poliakov, 1881",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "ferus",
        "taxonRank": "subspecies",
    },
    "Greater One-horned Rhino": {
        "scientificName": "Rhinoceros unicornis Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Rhinocerotidae",
        "genus": "Rhinoceros", "specificEpithet": "unicornis",
        "taxonRank": "species",
    },
    "Southern White Rhino": {
        "scientificName": "Ceratotherium simum simum (Burchell, 1817)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Rhinocerotidae",
        "genus": "Ceratotherium", "specificEpithet": "simum",
        "taxonRank": "subspecies",
    },
    "Fringe-eared Oryx": {
        "scientificName": "Oryx beisa callotis Thomas, 1892",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Oryx", "specificEpithet": "beisa",
        "taxonRank": "subspecies",
    },
    "Scimitar-horned Oryx": {
        "scientificName": "Oryx dammah (Cretzschmar, 1827)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Oryx", "specificEpithet": "dammah",
        "taxonRank": "species",
    },
    "Banteng": {
        "scientificName": "Bos javanicus d'Alton, 1823",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Bos", "specificEpithet": "javanicus",
        "taxonRank": "species",
    },
    "Bison": {
        "scientificName": "Bison bison (Linnaeus, 1758)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Bison", "specificEpithet": "bison",
        "taxonRank": "species",
    },
    "Giraffe": {
        "scientificName": "Giraffa camelopardalis (Linnaeus, 1758)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Giraffidae",
        "genus": "Giraffa", "specificEpithet": "camelopardalis",
        "taxonRank": "species",
    },
    "White-tailed Deer": {
        "scientificName": "Odocoileus virginianus (Zimmermann, 1780)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Odocoileus", "specificEpithet": "virginianus",
        "taxonRank": "species",
    },
    "Bird": {
        "scientificName": "Aves",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "", "family": "",
        "genus": "", "specificEpithet": "",
        "taxonRank": "class",
    },
    "Coyote": {
        "scientificName": "Canis latrans Say, 1823",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Carnivora", "family": "Canidae",
        "genus": "Canis", "specificEpithet": "latrans",
        "taxonRank": "species",
    },
    # Additional BioCLIP label mappings
    "Ostrich": {
        "scientificName": "Struthio camelus Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Struthioniformes", "family": "Struthionidae",
        "genus": "Struthio", "specificEpithet": "camelus",
        "taxonRank": "species",
    },
    "Eland": {
        "scientificName": "Taurotragus oryx (Pallas, 1766)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Taurotragus", "specificEpithet": "oryx",
        "taxonRank": "species",
    },
    "Camel": {
        "scientificName": "Camelus",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Camelidae",
        "genus": "Camelus", "specificEpithet": "",
        "taxonRank": "genus",
    },
    "Elk": {
        "scientificName": "Cervus canadensis Erxleben, 1777",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Cervus", "specificEpithet": "canadensis",
        "taxonRank": "species",
    },
    "Muskox": {
        "scientificName": "Ovibos moschatus (Zimmermann, 1780)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Ovibos", "specificEpithet": "moschatus",
        "taxonRank": "species",
    },
    "Fox": {
        "scientificName": "Vulpes",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Carnivora", "family": "Canidae",
        "genus": "Vulpes", "specificEpithet": "",
        "taxonRank": "genus",
    },
    "Wild Dog": {
        "scientificName": "Lycaon pictus (Temminck, 1820)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Carnivora", "family": "Canidae",
        "genus": "Lycaon", "specificEpithet": "pictus",
        "taxonRank": "species",
    },
    "Donkey": {
        "scientificName": "Equus asinus Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "asinus",
        "taxonRank": "species",
    },
    "Goat": {
        "scientificName": "Capra",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Capra", "specificEpithet": "",
        "taxonRank": "genus",
    },
    "Hawk": {
        "scientificName": "Accipitridae",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Accipitriformes", "family": "Accipitridae",
        "genus": "", "specificEpithet": "",
        "taxonRank": "family",
    },
    "Heron": {
        "scientificName": "Ardeidae",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Pelecaniformes", "family": "Ardeidae",
        "genus": "", "specificEpithet": "",
        "taxonRank": "family",
    },
    "Waterfowl": {
        "scientificName": "Anatidae",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Anseriformes", "family": "Anatidae",
        "genus": "", "specificEpithet": "",
        "taxonRank": "family",
    },
    "Human": {
        "scientificName": "Homo sapiens Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Primates", "family": "Hominidae",
        "genus": "Homo", "specificEpithet": "sapiens",
        "taxonRank": "species",
    },
}

# Alias map: BioCLIP label (lowercased) -> canonical TAXON_MAP key
# Handles variant spellings, genus-level labels, and common names
BIOCLIP_ALIAS = {
    "pere david's deer": "Pere David's Deer",
    "milu deer": "Pere David's Deer",
    "elaphurus": "Pere David's Deer",
    "grevy's zebra": "Grevy's Zebra",
    "zebra": "Grevy's Zebra",
    "sichuan takin": "Sichuan Takin",
    "budorcas": "Sichuan Takin",
    "przewalski's horse": "Przewalski's Horse",
    "horse": "Przewalski's Horse",
    "equus": "Przewalski's Horse",
    "rhinoceros": "Greater One-horned Rhino",
    "ceratotherium": "Southern White Rhino",
    "oryx": "Fringe-eared Oryx",
    "banteng": "Banteng",
    "bos": "Banteng",
    "cattle": "Banteng",
    "bison": "Bison",
    "giraffe": "Giraffe",
    "giraffa": "Giraffe",
    "deer": "White-tailed Deer",
    "white-tailed deer": "White-tailed Deer",
    "odocoileus": "White-tailed Deer",
    "cervus": "Elk",
    "elk": "Elk",
    "bird": "Bird",
    "songbird": "Bird",
    "raptor": "Bird",
    "coyote": "Coyote",
    "canis": "Coyote",
    "ostrich": "Ostrich",
    "struthio": "Ostrich",
    "eland": "Eland",
    "taurotragus": "Eland",
    "antelope": "Eland",
    "camel": "Camel",
    "camelus": "Camel",
    "muskox": "Muskox",
    "fox": "Fox",
    "wild dog": "Wild Dog",
    "lycaon": "Wild Dog",
    "donkey": "Donkey",
    "goat": "Goat",
    "hawk": "Hawk",
    "heron": "Heron",
    "waterfowl": "Waterfowl",
    "human": "Human",
}

# Non-animal labels to skip (background / environment)
SKIP_LABELS = {"rock", "sky", "tree", "vegetation", "water"}


def lookup_taxon(bioclip_label):
    """Look up taxon info from a BioCLIP label. Returns (canonical_name, taxon_dict) or None."""
    label_lower = bioclip_label.strip().lower()

    if label_lower in SKIP_LABELS:
        return None

    canonical = BIOCLIP_ALIAS.get(label_lower)
    if canonical:
        return canonical, TAXON_MAP[canonical]

    # Try title-case direct lookup in TAXON_MAP
    for key in TAXON_MAP:
        if key.lower() == label_lower:
            return key, TAXON_MAP[key]

    # Unknown animal label -- return generic entry
    return bioclip_label, {
        "scientificName": "",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "",
        "order": "", "family": "",
        "genus": "", "specificEpithet": "",
        "taxonRank": "",
    }


def parse_filename(filename):
    """Parse site_cam and campaign dates from a detection CSV filename.

    Handles both hyphen and underscore separators between site and camera:
        TW01-CT02_20250630_20250703_detections.csv
        TW09_CT02_20250804_20250828_detections.csv
    """
    stem = filename.replace("_detections.csv", "")
    # Match: site (TW##) separator cam (CT##) _ start_date _ end_date
    m = re.match(r"(TW\d+)[-_](CT\d+)_(\d{8})_(\d{8})", stem)
    if not m:
        return None, None, None, None
    site = m.group(1)
    cam = m.group(2)
    site_cam = f"{site}-{cam}"
    start_date = m.group(3)
    end_date = m.group(4)
    campaign = f"{start_date}_{end_date}"
    return site, site_cam, campaign, f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}/{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"


def process_detection_csv(csv_path):
    """Process a single detection CSV into occurrences. Returns (rows, species_counts)."""
    occurrences = []
    species_counts = defaultdict(int)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bioclip_label = row.get("bioclip_label", "").strip()
            result = lookup_taxon(bioclip_label)
            if result is None:
                continue  # skip non-animal labels

            canonical_name, taxon = result
            species_counts[canonical_name] += 1

            # Timestamp
            timestamp = row.get("timestamp_file", "") or row.get("timestamp_from_name", "")
            date_str = timestamp[:10] if timestamp else ""
            time_str = timestamp[11:19] if len(timestamp) > 10 else ""

            # Coordinates: prefer animal_lat/animal_lon if available
            animal_lat = row.get("animal_lat", "").strip()
            animal_lon = row.get("animal_lon", "").strip()
            camera_lat = row.get("camera_lat", "").strip()
            camera_lon = row.get("camera_lon", "").strip()

            if animal_lat and animal_lon:
                occ_lat = animal_lat
                occ_lon = animal_lon
            else:
                occ_lat = camera_lat
                occ_lon = camera_lon

            # Confidence scores
            bioclip_score = row.get("bioclip_score", "")
            yolo_conf = row.get("yolo_conf", "")

            occurrences.append({
                "bioclip_label": bioclip_label,
                "canonical_name": canonical_name,
                "taxon": taxon,
                "date": date_str,
                "time": time_str,
                "lat": occ_lat,
                "lon": occ_lon,
                "bioclip_score": bioclip_score,
                "yolo_conf": yolo_conf,
                "image": row.get("image", ""),
                "image_path": row.get("image_path", ""),
                "detection_index": row.get("detection_index", ""),
                "distance_m": row.get("distance_m", ""),
            })

    return occurrences, species_counts


def main():
    print("=" * 60)
    print("Camera Trap Darwin Core Generation")
    print("=" * 60)

    # Collect unfiltered detection CSVs
    detection_files = sorted(
        p for p in DETECTIONS_DIR.glob("*_detections.csv")
        if "_detections_filtered.csv" not in p.name
    )
    print(f"\nFound {len(detection_files)} detection CSV files")

    all_events = []
    all_occurrences = []
    all_species = defaultdict(int)
    occ_num = 0

    # --- Project-level event --------------------------------------------------
    all_events.append({
        "eventID": "TheWilds_2025_camera_traps",
        "parentEventID": "TheWilds_2025",
        "eventType": "Project",
        "eventDate": "2025-06-30/2025-08-28",
        "samplingProtocol": (
            "Camera trap monitoring using trail cameras; "
            "Detections by YOLOv8x object detection + BioCLIP zero-shot classification; "
            "Animal positions estimated via monocular depth estimation"
        ),
        "sampleSizeValue": "",
        "sampleSizeUnit": "",
        "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
        "locationID": "",
        "decimalLatitude": 39.83,
        "decimalLongitude": -81.74,
        "coordinateUncertaintyInMeters": 5000,
        "geodeticDatum": "WGS84",
        "country": "United States",
        "stateProvince": "Ohio",
        "county": "Muskingum",
        "datasetID": "TheWilds_2025_camera_traps",
        "datasetName": "The Wilds 2025 Multi-Modal Survey - Camera Traps",
        "recordedBy": "Jenna Kline",
        "fieldNotes": (
            f"{len(detection_files)} camera trap deployments across multiple sites, 2 campaigns. "
            "Images analyzed with YOLOv8x + BioCLIP pipeline."
        ),
    })

    # --- Process each detection file ------------------------------------------
    for csv_path in detection_files:
        site, site_cam, campaign, event_date_range = parse_filename(csv_path.name)
        if site is None:
            print(f"  WARNING: Could not parse filename: {csv_path.name}")
            continue

        site_lat, site_lon = SITE_GPS.get(site, (39.83, -81.74))
        site_name = SITE_NAMES.get(site, site)

        deployment_event_id = f"TheWilds_2025_CT_deployment_{site_cam}_{campaign}"

        print(f"\nProcessing {csv_path.name}")
        print(f"  Site: {site} ({site_name}), Camera: {site_cam}, Campaign: {campaign}")

        det_rows, sp_counts = process_detection_csv(str(csv_path))
        print(f"  {len(det_rows)} detections (excluding non-animal labels)")

        # Deployment event
        dep_event = {
            "eventID": deployment_event_id,
            "parentEventID": "TheWilds_2025_camera_traps",
            "eventType": "SensorDeployment",
            "eventDate": event_date_range,
            "samplingProtocol": (
                f"Trail camera ({site_cam}); "
                f"Campaign: {campaign}; "
                f"Detections by YOLOv8x + BioCLIP zero-shot classification"
            ),
            "sampleSizeValue": len(det_rows),
            "sampleSizeUnit": "detections",
            "locality": f"The Wilds - {site_name}",
            "locationID": site,
            "decimalLatitude": site_lat,
            "decimalLongitude": site_lon,
            "coordinateUncertaintyInMeters": 5,
            "geodeticDatum": "WGS84",
            "country": "United States",
            "stateProvince": "Ohio",
            "county": "Muskingum",
            "datasetID": "TheWilds_2025_camera_traps",
            "datasetName": "The Wilds 2025 Multi-Modal Survey - Camera Traps",
            "recordedBy": "Jenna Kline",
            "fieldNotes": (
                f"Camera: {site_cam}; Campaign: {campaign}; "
                f"Total detections: {len(det_rows)}"
            ),
        }
        all_events.append(dep_event)

        # Occurrence records
        for det in det_rows:
            occ_num += 1
            taxon = det["taxon"]
            canonical_name = det["canonical_name"]
            all_species[canonical_name] += 1

            occ = {
                "occurrenceID": f"TheWilds_2025_CT_{occ_num:06d}",
                "eventID": deployment_event_id,
                "catalogNumber": f"CT_{site_cam}_{det['image']}_{det['detection_index']}",

                # Taxonomy
                "scientificName": taxon.get("scientificName", ""),
                "kingdom": taxon.get("kingdom", "Animalia"),
                "phylum": taxon.get("phylum", "Chordata"),
                "class": taxon.get("class", ""),
                "order": taxon.get("order", ""),
                "family": taxon.get("family", ""),
                "genus": taxon.get("genus", ""),
                "specificEpithet": taxon.get("specificEpithet", ""),
                "taxonRank": taxon.get("taxonRank", ""),
                "vernacularName": canonical_name,

                # Observation
                "occurrenceStatus": "present",
                "individualCount": 1,
                "basisOfRecord": "MachineObservation",
                "recordedBy": f"Trail camera ({site_cam})",
                "identifiedBy": "YOLOv8x + BioCLIP",
                "identificationVerificationStatus": "unverified",
                "identificationRemarks": (
                    f"BioCLIP label: {det['bioclip_label']}; "
                    f"BioCLIP score: {det['bioclip_score']}; "
                    f"YOLO confidence: {det['yolo_conf']}"
                ),

                # Temporal
                "eventDate": det["date"],
                "eventTime": det["time"],

                # Spatial
                "decimalLatitude": det["lat"],
                "decimalLongitude": det["lon"],
                "coordinateUncertaintyInMeters": 50,
                "geodeticDatum": "WGS84",
                "locality": f"The Wilds - {site_name}",
                "locationID": site,
                "country": "United States",
                "stateProvince": "Ohio",
                "county": "Muskingum",

                # Provenance
                "establishmentMeans": "managed",
                "degreeOfEstablishment": "captive",
                "occurrenceRemarks": (
                    f"Estimated distance: {det['distance_m']}m"
                    if det["distance_m"] else ""
                ),
                "associatedMedia": det["image_path"],

                # Dataset
                "datasetID": "TheWilds_2025_camera_traps",
                "datasetName": "The Wilds 2025 Multi-Modal Survey - Camera Traps",
            }
            all_occurrences.append(occ)

        for sp, ct in sp_counts.items():
            all_species[sp] += 0  # ensure key exists (already counted above)

    # --- Write output files ---------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Events
    events_path = OUTPUT_DIR / "darwin_core_events_camera_traps.csv"
    all_keys = []
    seen = set()
    for e in all_events:
        for k in e.keys():
            if k not in seen:
                all_keys.append(k)
                seen.add(k)
    with open(events_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_events)
    print(f"\nWrote {len(all_events)} Events to {events_path}")

    # Occurrences
    occ_path = OUTPUT_DIR / "darwin_core_occurrences_camera_traps.csv"
    if all_occurrences:
        fieldnames = list(all_occurrences[0].keys())
        with open(occ_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_occurrences)
    print(f"Wrote {len(all_occurrences)} Occurrences to {occ_path}")

    # --- Summary --------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("Camera Trap Darwin Core Summary")
    print(f"{'=' * 60}")
    deployment_events = len([e for e in all_events if e["eventType"] == "SensorDeployment"])
    print(f"  Event hierarchy:")
    print(f"    1 Project event")
    print(f"    {deployment_events} Deployment events (one per camera+campaign)")
    print(f"  Occurrence records: {len(all_occurrences)}")
    print(f"  Unique taxa:        {len(all_species)}")

    print(f"\n  Top 20 taxa by detection count:")
    for sp, count in sorted(all_species.items(), key=lambda x: -x[1])[:20]:
        print(f"    {sp:<35} {count:>7}")

    total_det = sum(all_species.values())
    print(f"\n  Total detections: {total_det:,}")


if __name__ == "__main__":
    main()
