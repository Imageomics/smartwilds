#!/usr/bin/env python3
"""
Generate Darwin Core Events and Occurrences from drone detection CSVs.

Input:  *_detections.csv files from YOLO+BioCLIP pipeline (39 videos, 191K+ detections)
        Filenames encode mission and video: {date}_{platform}_{flight}_{videoID}_detections.csv

Output: darwin_core_events_drones.csv       (hierarchical: project -> mission -> video)
        darwin_core_occurrences_drones.csv   (one row per detection)

Each detection CSV row = one Occurrence record.
"""

import csv
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
DETECTIONS_DIR = BASE_DIR / "processing_output" / "detections" / "drones"
OUTPUT_DIR = BASE_DIR / "processing_output" / "darwin_core" / "drones"

# ─── Drone platform metadata ─────────────────────────────────────────────────

DRONE_PLATFORMS = {
    "parrotanafi": {"name": "Parrot Anafi 4K", "gps_accuracy_m": 2},
    "parrot": {"name": "Parrot Anafi 4K", "gps_accuracy_m": 2},
    "DJI": {"name": "DJI Mavic", "gps_accuracy_m": 2},
    "djiair": {"name": "DJI Air", "gps_accuracy_m": 2},
}

# ─── Mission metadata from telemetry (GPS center + start datetime) ────────────
# GPS: center of flight path from telemetry logs
# Datetime: flight start from telemetry (ISO 8601 with timezone)
# Sources: Parrot proprietary JSON, Parrot GUTMA JSON, DJI Airdata CSV, DJI ExportCSV

MISSION_GPS = {
    # Campaign 1: June 30 – July 3 (Parrot Anafi, proprietary telemetry)
    "20250701_parrotanafi_1": (39.828870, -81.742379),
    "20250703_parrotanafi_1": (39.830640, -81.738074),
    "20250703_parrotanafi_2": (39.835357, -81.730015),
    "20250703_parrotanafi_3": (39.834371, -81.739309),
    "20250703_parrotanafi_4": (39.830679, -81.738344),
    "20250703_parrotanafi_5": (39.830243, -81.738925),
    # Campaign 2: August (DJI + Parrot, mixed telemetry)
    "20250811_DJI_01":        (39.834171, -81.737820),  # DJI CSV (no timestamp)
    "20250811_parrot_01":     (39.834, -81.738),         # No telemetry — approximate
    "20250818_parrot_01":     (39.830623, -81.738001),
    "20250818_parrot_02":     (39.835540, -81.729999),
    "20250825_parrot_01":     (39.829713, -81.740141),
    "20250825_parrot_02":     (39.835984, -81.731347),
    "20250825_parrot_03":     (39.832812, -81.738833),
    "20250825_parrot_04":     (39.833255, -81.739453),
    # Campaign 3: September 8 (DJI Air, Airdata CSV)
    "20250908_djiair_1":      (39.829801, -81.740046),
    "20250908_djiair_2":      (39.831170, -81.736190),
    "20250908_djiair_3":      (39.833986, -81.737854),
    "20250908_djiair_4":      (39.833597, -81.736314),
}

MISSION_DATETIME = {
    # ISO 8601 start times extracted from telemetry
    "20250701_parrotanafi_1": "2025-07-01T08:34:38-04:00",
    "20250703_parrotanafi_1": "2025-07-03T15:50:59-04:00",
    "20250703_parrotanafi_2": "2025-07-03T16:21:04-04:00",
    "20250703_parrotanafi_3": "2025-07-03T16:56:20-04:00",
    "20250703_parrotanafi_4": "2025-07-03T17:23:45-04:00",
    "20250703_parrotanafi_5": "2025-07-03T17:25:55-04:00",
    "20250811_DJI_01":        "2025-08-11T10:29:13-04:00",  # from filename
    "20250811_parrot_01":     "2025-08-11",                   # no telemetry
    "20250818_parrot_01":     "2025-08-18T09:14:06-04:00",
    "20250818_parrot_02":     "2025-08-18T09:43:25-04:00",
    "20250825_parrot_01":     "2025-08-25T09:13:47-04:00",
    "20250825_parrot_02":     "2025-08-25T09:43:01-04:00",
    "20250825_parrot_03":     "2025-08-25T10:15:53-04:00",
    "20250825_parrot_04":     "2025-08-25T10:50:31-04:00",
    "20250908_djiair_1":      "2025-09-08T09:16:25-04:00",
    "20250908_djiair_2":      "2025-09-08T09:29:14-04:00",
    "20250908_djiair_3":      "2025-09-08T10:25:13-04:00",
    "20250908_djiair_4":      "2025-09-08T10:30:05-04:00",
}

# ─── Taxon lookup from BioCLIP labels ────────────────────────────────────────

TAXON_MAP = {
    # Species-level IDs (The Wilds residents)
    "Pere David's deer": {
        "scientificName": "Elaphurus davidianus Milne-Edwards, 1866",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Elaphurus", "specificEpithet": "davidianus",
        "taxonRank": "species", "vernacularName": "Pere David's deer",
    },
    "Milu deer": {
        "scientificName": "Elaphurus davidianus Milne-Edwards, 1866",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Elaphurus", "specificEpithet": "davidianus",
        "taxonRank": "species", "vernacularName": "Pere David's deer",
    },
    "Elaphurus": {
        "scientificName": "Elaphurus davidianus Milne-Edwards, 1866",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Elaphurus", "specificEpithet": "davidianus",
        "taxonRank": "species", "vernacularName": "Pere David's deer",
    },
    "Grevy's zebra": {
        "scientificName": "Equus grevyi Oustalet, 1882",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "grevyi",
        "taxonRank": "species", "vernacularName": "Grevy's zebra",
    },
    "zebra": {
        "scientificName": "Equus grevyi Oustalet, 1882",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "grevyi",
        "taxonRank": "species", "vernacularName": "Grevy's zebra",
    },
    "Sichuan takin": {
        "scientificName": "Budorcas taxicolor tibetana Milne-Edwards, 1874",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Budorcas", "specificEpithet": "taxicolor",
        "taxonRank": "subspecies", "vernacularName": "Sichuan takin",
    },
    "Budorcas": {
        "scientificName": "Budorcas taxicolor tibetana Milne-Edwards, 1874",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Budorcas", "specificEpithet": "taxicolor",
        "taxonRank": "subspecies", "vernacularName": "Sichuan takin",
    },
    "Przewalski's horse": {
        "scientificName": "Equus ferus przewalskii Poliakov, 1881",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "ferus",
        "taxonRank": "subspecies", "vernacularName": "Przewalski's horse",
    },
    "rhinoceros": {
        "scientificName": "Rhinocerotidae",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Rhinocerotidae",
        "genus": "", "specificEpithet": "",
        "taxonRank": "family", "vernacularName": "rhinoceros",
    },
    "Ceratotherium": {
        "scientificName": "Ceratotherium simum simum (Burchell, 1817)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Rhinocerotidae",
        "genus": "Ceratotherium", "specificEpithet": "simum",
        "taxonRank": "subspecies", "vernacularName": "Southern white rhino",
    },
    "Struthio": {
        "scientificName": "Struthio camelus Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Struthioniformes", "family": "Struthionidae",
        "genus": "Struthio", "specificEpithet": "camelus",
        "taxonRank": "species", "vernacularName": "ostrich",
    },
    "ostrich": {
        "scientificName": "Struthio camelus Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Struthioniformes", "family": "Struthionidae",
        "genus": "Struthio", "specificEpithet": "camelus",
        "taxonRank": "species", "vernacularName": "ostrich",
    },
    "oryx": {
        "scientificName": "Oryx beisa callotis Thomas, 1892",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Oryx", "specificEpithet": "beisa",
        "taxonRank": "subspecies", "vernacularName": "Fringe-eared oryx",
    },
    "eland": {
        "scientificName": "Taurotragus oryx (Pallas, 1766)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Taurotragus", "specificEpithet": "oryx",
        "taxonRank": "species", "vernacularName": "common eland",
    },
    "Taurotragus": {
        "scientificName": "Taurotragus oryx (Pallas, 1766)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Taurotragus", "specificEpithet": "oryx",
        "taxonRank": "species", "vernacularName": "common eland",
    },
    "Giraffa": {
        "scientificName": "Giraffa camelopardalis (Linnaeus, 1758)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Giraffidae",
        "genus": "Giraffa", "specificEpithet": "camelopardalis",
        "taxonRank": "species", "vernacularName": "giraffe",
    },
    "Lycaon": {
        "scientificName": "Lycaon pictus (Temminck, 1820)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Carnivora", "family": "Canidae",
        "genus": "Lycaon", "specificEpithet": "pictus",
        "taxonRank": "species", "vernacularName": "African wild dog",
    },
    "wild dog": {
        "scientificName": "Lycaon pictus (Temminck, 1820)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Carnivora", "family": "Canidae",
        "genus": "Lycaon", "specificEpithet": "pictus",
        "taxonRank": "species", "vernacularName": "African wild dog",
    },
    "Camelus": {
        "scientificName": "Camelus",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Camelidae",
        "genus": "Camelus", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "camel",
    },
    "camel": {
        "scientificName": "Camelus",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Camelidae",
        "genus": "Camelus", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "camel",
    },
    "white-tailed deer": {
        "scientificName": "Odocoileus virginianus (Zimmermann, 1780)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Odocoileus", "specificEpithet": "virginianus",
        "taxonRank": "species", "vernacularName": "white-tailed deer",
    },
    "Odocoileus": {
        "scientificName": "Odocoileus virginianus (Zimmermann, 1780)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Odocoileus", "specificEpithet": "virginianus",
        "taxonRank": "species", "vernacularName": "white-tailed deer",
    },
    "Cervus": {
        "scientificName": "Cervus",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Cervus", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "deer",
    },
    "Bos": {
        "scientificName": "Bos",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Bos", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "cattle",
    },
    "banteng": {
        "scientificName": "Bos javanicus d'Alton, 1823",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Bos", "specificEpithet": "javanicus",
        "taxonRank": "species", "vernacularName": "banteng",
    },
    "bison": {
        "scientificName": "Bison bison (Linnaeus, 1758)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Bison", "specificEpithet": "bison",
        "taxonRank": "species", "vernacularName": "American bison",
    },
    "muskox": {
        "scientificName": "Ovibos moschatus (Zimmermann, 1780)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Ovibos", "specificEpithet": "moschatus",
        "taxonRank": "species", "vernacularName": "muskox",
    },
    "Equus": {
        "scientificName": "Equus",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "equid",
    },
    "Canis": {
        "scientificName": "Canis",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Carnivora", "family": "Canidae",
        "genus": "Canis", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "canid",
    },
    "coyote": {
        "scientificName": "Canis latrans Say, 1823",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Carnivora", "family": "Canidae",
        "genus": "Canis", "specificEpithet": "latrans",
        "taxonRank": "species", "vernacularName": "coyote",
    },
    "fox": {
        "scientificName": "Vulpes vulpes (Linnaeus, 1758)",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Carnivora", "family": "Canidae",
        "genus": "Vulpes", "specificEpithet": "vulpes",
        "taxonRank": "species", "vernacularName": "red fox",
    },
    # Generic mammal labels
    "horse": {
        "scientificName": "Equus",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "horse",
    },
    "donkey": {
        "scientificName": "Equus asinus Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Perissodactyla", "family": "Equidae",
        "genus": "Equus", "specificEpithet": "asinus",
        "taxonRank": "species", "vernacularName": "donkey",
    },
    "deer": {
        "scientificName": "Cervidae",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "", "specificEpithet": "",
        "taxonRank": "family", "vernacularName": "deer",
    },
    "elk": {
        "scientificName": "Cervus canadensis Erxleben, 1777",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Cervidae",
        "genus": "Cervus", "specificEpithet": "canadensis",
        "taxonRank": "species", "vernacularName": "elk",
    },
    "antelope": {
        "scientificName": "Bovidae",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "", "specificEpithet": "",
        "taxonRank": "family", "vernacularName": "antelope",
    },
    "goat": {
        "scientificName": "Capra",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Capra", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "goat",
    },
    "cattle": {
        "scientificName": "Bos",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Bos", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "cattle",
    },
    "cow": {
        "scientificName": "Bos",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Artiodactyla", "family": "Bovidae",
        "genus": "Bos", "specificEpithet": "",
        "taxonRank": "genus", "vernacularName": "cattle",
    },
    # Birds
    "bird": {
        "scientificName": "Aves",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "", "family": "",
        "genus": "", "specificEpithet": "",
        "taxonRank": "class", "vernacularName": "bird",
    },
    "songbird": {
        "scientificName": "Passeriformes",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Passeriformes", "family": "",
        "genus": "", "specificEpithet": "",
        "taxonRank": "order", "vernacularName": "songbird",
    },
    "hawk": {
        "scientificName": "Accipitridae",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Accipitriformes", "family": "Accipitridae",
        "genus": "", "specificEpithet": "",
        "taxonRank": "family", "vernacularName": "hawk",
    },
    "raptor": {
        "scientificName": "Accipitriformes",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Accipitriformes", "family": "",
        "genus": "", "specificEpithet": "",
        "taxonRank": "order", "vernacularName": "raptor",
    },
    "heron": {
        "scientificName": "Ardeidae",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Pelecaniformes", "family": "Ardeidae",
        "genus": "", "specificEpithet": "",
        "taxonRank": "family", "vernacularName": "heron",
    },
    "waterfowl": {
        "scientificName": "Anatidae",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Aves",
        "order": "Anseriformes", "family": "Anatidae",
        "genus": "", "specificEpithet": "",
        "taxonRank": "family", "vernacularName": "waterfowl",
    },
    # Other animals
    "fish": {
        "scientificName": "Actinopterygii",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Actinopterygii",
        "order": "", "family": "",
        "genus": "", "specificEpithet": "",
        "taxonRank": "class", "vernacularName": "fish",
    },
    "human": {
        "scientificName": "Homo sapiens Linnaeus, 1758",
        "kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia",
        "order": "Primates", "family": "Hominidae",
        "genus": "Homo", "specificEpithet": "sapiens",
        "taxonRank": "species", "vernacularName": "human",
    },
}

# Non-animal labels to skip (background/scenery)
NON_ANIMAL_LABELS = {"grass", "rock", "sky", "tree", "vegetation", "water", "c"}

# Video identifier patterns: VID_xxx, DJI_xxxx, Pxxxxxxx
VIDEO_ID_RE = re.compile(r"_(VID_\d+|DJI_\d+|P\d+)$")


def parse_filename(stem):
    """Parse mission name and video name from detection filename stem.

    Examples:
        20250701_parrotanafi_1_VID_001 -> ("20250701_parrotanafi_1", "VID_001")
        20250811_DJI_01_DJI_0001       -> ("20250811_DJI_01", "DJI_0001")
        20250811_parrot_01_P5180524     -> ("20250811_parrot_01", "P5180524")
    """
    m = VIDEO_ID_RE.search(stem)
    if m:
        video_name = m.group(1)
        mission = stem[:m.start()]
        # Strip trailing underscore
        mission = mission.rstrip("_")
        return mission, video_name
    # Fallback: last component is video
    parts = stem.rsplit("_", 1)
    return parts[0], parts[1] if len(parts) > 1 else stem


def get_platform_key(mission):
    """Extract platform key from mission name (second component)."""
    parts = mission.split("_")
    if len(parts) >= 2:
        return parts[1]
    return ""


def get_date_from_mission(mission):
    """Extract date string from mission name (first component YYYYMMDD -> YYYY-MM-DD)."""
    parts = mission.split("_")
    if parts and len(parts[0]) == 8 and parts[0].isdigit():
        d = parts[0]
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return ""


def main():
    print("=" * 60)
    print("Drone Darwin Core Generation")
    print("=" * 60)

    # Discover all detection CSVs
    det_files = sorted(DETECTIONS_DIR.glob("*_detections.csv"))
    print(f"\nFound {len(det_files)} detection CSV files")

    # Group files by mission
    missions = defaultdict(list)
    for f in det_files:
        stem = f.stem.replace("_detections", "")
        mission, video_name = parse_filename(stem)
        missions[mission].append((f, video_name, stem))

    print(f"Found {len(missions)} missions:")
    for m in sorted(missions):
        print(f"  {m}: {len(missions[m])} videos")

    # ─── Build events ─────────────────────────────────────────────────────────

    all_events = []

    # 1) Project-level event
    all_events.append({
        "eventID": "TheWilds_2025_drones",
        "parentEventID": "TheWilds_2025",
        "eventType": "Project",
        "eventDate": "2025-07-01/2025-09-08",
        "samplingProtocol": (
            "Aerial drone survey using multiple UAS platforms (Parrot Anafi 4K, DJI Mavic, DJI Air); "
            "Video recorded at varying altitudes over managed wildlife areas; "
            "Detections by YOLOv8 object detection + BioCLIP zero-shot classification"
        ),
        "sampleSizeValue": len(det_files),
        "sampleSizeUnit": "video recordings",
        "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
        "locationID": "",
        "decimalLatitude": 39.83,
        "decimalLongitude": -81.74,
        "coordinateUncertaintyInMeters": 5000,
        "geodeticDatum": "WGS84",
        "country": "United States",
        "stateProvince": "Ohio",
        "county": "Muskingum",
        "datasetID": "TheWilds_2025_drones",
        "datasetName": "The Wilds 2025 Multi-Modal Survey - Drone Imagery",
        "recordedBy": "Jenna Kline; Tanishka Wani",
        "fieldNotes": (
            f"{len(missions)} drone missions across {len(det_files)} video files. "
            "Platforms: Parrot Anafi 4K, DJI Mavic, DJI Air. "
            "Detections by YOLOv8 + BioCLIP pipeline."
        ),
    })

    # 2) Mission-level events
    for mission in sorted(missions):
        platform_key = get_platform_key(mission)
        platform = DRONE_PLATFORMS.get(platform_key, {"name": platform_key, "gps_accuracy_m": 2})
        lat, lon = MISSION_GPS.get(mission, (39.83, -81.74))
        date_str = get_date_from_mission(mission)
        n_videos = len(missions[mission])

        # Get telemetry datetime if available
        telemetry_dt = MISSION_DATETIME.get(mission, "")
        if telemetry_dt and "T" in telemetry_dt:
            event_date = telemetry_dt[:10]
            event_time = telemetry_dt[11:19]
        else:
            event_date = telemetry_dt if telemetry_dt else date_str
            event_time = ""

        mission_event = {
            "eventID": f"TheWilds_2025_drone_{mission}",
            "parentEventID": "TheWilds_2025_drones",
            "eventType": "DroneMission",
            "eventDate": event_date,
            "eventTime": event_time,
            "samplingProtocol": (
                f"Aerial drone survey; Platform: {platform['name']}; "
                f"GPS accuracy: {platform['gps_accuracy_m']}m; "
                f"{n_videos} video(s) recorded"
            ),
            "sampleSizeValue": n_videos,
            "sampleSizeUnit": "video recordings",
            "locality": "The Wilds Conservation Center",
            "locationID": mission,
            "decimalLatitude": lat,
            "decimalLongitude": lon,
            "coordinateUncertaintyInMeters": 100,
            "geodeticDatum": "WGS84",
            "country": "United States",
            "stateProvince": "Ohio",
            "county": "Muskingum",
            "datasetID": "TheWilds_2025_drones",
            "datasetName": "The Wilds 2025 Multi-Modal Survey - Drone Imagery",
            "recordedBy": platform["name"],
            "fieldNotes": (
                f"Mission: {mission}; Platform: {platform['name']}; "
                f"Telemetry start: {telemetry_dt or 'not available'}; "
                f"GPS from flight telemetry center point"
            ),
        }
        all_events.append(mission_event)

    # 3) Video-level events (one per detection CSV) — built during occurrence processing
    video_events = {}  # stem -> event dict
    all_occurrences = []
    occ_num = 0
    label_counts = defaultdict(int)
    skipped_non_animal = 0

    print(f"\nProcessing detections...")

    for mission in sorted(missions):
        platform_key = get_platform_key(mission)
        platform = DRONE_PLATFORMS.get(platform_key, {"name": platform_key, "gps_accuracy_m": 2})
        lat, lon = MISSION_GPS.get(mission, (39.83, -81.74))
        date_str = get_date_from_mission(mission)

        for csv_path, video_name, stem in missions[mission]:
            video_event_id = f"TheWilds_2025_drone_{stem}"
            mission_event_id = f"TheWilds_2025_drone_{mission}"

            # Count detections per video for field notes
            det_count = 0
            animal_count = 0

            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    det_count += 1
                    bioclip_label = row.get("bioclip_label", "")

                    # Skip non-animal labels
                    if bioclip_label in NON_ANIMAL_LABELS:
                        skipped_non_animal += 1
                        continue

                    animal_count += 1
                    label_counts[bioclip_label] += 1
                    occ_num += 1

                    # Taxonomy lookup
                    taxon = TAXON_MAP.get(bioclip_label, {})

                    bioclip_score = row.get("bioclip_score", "")
                    yolo_conf = row.get("yolo_conf", "")
                    frame_number = row.get("frame_number", "")
                    frame_time = row.get("frame_time_sec", "")
                    frame_ts = row.get("frame_timestamp", "")
                    det_idx = row.get("detection_index", "")
                    video_file = row.get("video", "")
                    bbox = (
                        f"[{row.get('xmin','')},{row.get('ymin','')},"
                        f"{row.get('xmax','')},{row.get('ymax','')}]"
                    )
                    frame_dims = f"{row.get('frame_width','')}x{row.get('frame_height','')}"

                    occ = {
                        "occurrenceID": f"TheWilds_2025_drone_{occ_num:06d}",
                        "eventID": video_event_id,
                        "catalogNumber": f"drone_{stem}_f{frame_number}_d{det_idx}",

                        # Taxonomy
                        "scientificName": taxon.get("scientificName", bioclip_label),
                        "kingdom": taxon.get("kingdom", "Animalia"),
                        "phylum": taxon.get("phylum", "Chordata"),
                        "class": taxon.get("class", ""),
                        "order": taxon.get("order", ""),
                        "family": taxon.get("family", ""),
                        "genus": taxon.get("genus", ""),
                        "specificEpithet": taxon.get("specificEpithet", ""),
                        "taxonRank": taxon.get("taxonRank", ""),
                        "vernacularName": taxon.get("vernacularName", bioclip_label),

                        # Observation
                        "occurrenceStatus": "present",
                        "individualCount": 1,
                        "basisOfRecord": "MachineObservation",
                        "recordedBy": f"{platform['name']} (drone)",
                        "identifiedBy": "YOLOv8 + BioCLIP",
                        "identificationVerificationStatus": "unverified",
                        "identificationRemarks": (
                            f"BioCLIP label: {bioclip_label}; "
                            f"BioCLIP score: {bioclip_score}; "
                            f"YOLO confidence: {yolo_conf}; "
                            f"Frame: {frame_number} ({frame_ts}); "
                            f"Detection index: {det_idx}; "
                            f"Bounding box (px): {bbox}; "
                            f"Frame size: {frame_dims}"
                        ),

                        # Temporal
                        "eventDate": date_str,
                        "eventTime": "",

                        # Spatial
                        "decimalLatitude": lat,
                        "decimalLongitude": lon,
                        "coordinateUncertaintyInMeters": 100,
                        "geodeticDatum": "WGS84",
                        "locality": "The Wilds Conservation Center",
                        "locationID": mission,
                        "country": "United States",
                        "stateProvince": "Ohio",
                        "county": "Muskingum",

                        # Provenance
                        "establishmentMeans": "managed",
                        "degreeOfEstablishment": "captive",
                        "occurrenceRemarks": "",
                        "associatedMedia": video_file,

                        # Dataset
                        "datasetID": "TheWilds_2025_drones",
                        "datasetName": "The Wilds 2025 Multi-Modal Survey - Drone Imagery",
                    }
                    all_occurrences.append(occ)

            # Build video-level event
            video_events[stem] = {
                "eventID": video_event_id,
                "parentEventID": mission_event_id,
                "eventType": "DroneVideo",
                "eventDate": date_str,
                "samplingProtocol": (
                    f"Aerial drone video; Platform: {platform['name']}; "
                    f"Video: {video_name}; "
                    f"Analyzed with YOLOv8 + BioCLIP"
                ),
                "sampleSizeValue": 1,
                "sampleSizeUnit": "video recording",
                "locality": "The Wilds Conservation Center",
                "locationID": mission,
                "decimalLatitude": lat,
                "decimalLongitude": lon,
                "coordinateUncertaintyInMeters": 100,
                "geodeticDatum": "WGS84",
                "country": "United States",
                "stateProvince": "Ohio",
                "county": "Muskingum",
                "datasetID": "TheWilds_2025_drones",
                "datasetName": "The Wilds 2025 Multi-Modal Survey - Drone Imagery",
                "recordedBy": "",
                "fieldNotes": (
                    f"Video: {video_name}; Mission: {mission}; "
                    f"Total detections: {det_count}; Animal detections: {animal_count}"
                ),
            }

    # Add video events to all_events
    for stem in sorted(video_events):
        all_events.append(video_events[stem])

    # ─── Write output CSVs ────────────────────────────────────────────────────

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Events
    events_path = OUTPUT_DIR / "darwin_core_events_drones.csv"
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
    occ_path = OUTPUT_DIR / "darwin_core_occurrences_drones.csv"
    if all_occurrences:
        fieldnames = list(all_occurrences[0].keys())
        with open(occ_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_occurrences)
    print(f"Wrote {len(all_occurrences)} Occurrences to {occ_path}")

    # ─── Summary ──────────────────────────────────────────────────────────────

    print(f"\n{'=' * 60}")
    print("Drone Darwin Core Summary")
    print(f"{'=' * 60}")
    mission_events = len([e for e in all_events if e["eventType"] == "DroneMission"])
    video_event_count = len([e for e in all_events if e["eventType"] == "DroneVideo"])
    print(f"  Event hierarchy:")
    print(f"    1 Project event")
    print(f"    {mission_events} Mission events")
    print(f"    {video_event_count} Video events")
    print(f"  Total events: {len(all_events)}")
    print(f"  Occurrence records: {len(all_occurrences)}")
    print(f"  Non-animal detections skipped: {skipped_non_animal}")
    print(f"  Unique BioCLIP labels (animal): {len(label_counts)}")

    print(f"\n  Top 20 labels by detection count:")
    for label, count in sorted(label_counts.items(), key=lambda x: -x[1])[:20]:
        taxon = TAXON_MAP.get(label, {})
        sci = taxon.get("scientificName", "(unmapped)")
        print(f"    {label:<30} {count:>8}  -> {sci}")

    total_det = sum(label_counts.values())
    print(f"\n  Total animal detections: {total_det:,}")
    print(f"  Total detections (incl. non-animal): {total_det + skipped_non_animal:,}")

    # Check for unmapped labels
    unmapped = [l for l in label_counts if l not in TAXON_MAP]
    if unmapped:
        print(f"\n  WARNING: {len(unmapped)} unmapped BioCLIP label(s):")
        for l in sorted(unmapped):
            print(f"    {l} ({label_counts[l]} detections)")


if __name__ == "__main__":
    main()
