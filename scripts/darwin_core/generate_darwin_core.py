#!/usr/bin/env python3
"""
Generate the Darwin Core Event and Occurrence tables for The Wilds 2025.

This script uses the existing modality-specific Darwin Core generators as the
schema/style reference, but writes a fresh non-destructive set of tables under
``SMARTWILDS_DWC_OUT`` (default ``<archive>/processing_output/darwin_core_release``).
The field archive root is read from ``SMARTWILDS_ARCHIVE``; the external
SAM3/BioCLIP detection workspace from ``SMARTWILDS_DETECTIONS``.

Key updates relative to the earlier outputs:
  - camera traps are regenerated from SAM3 + BioCLIP Tree-of-Life prediction
    CSVs with geolocated animal-position estimates
  - camera-trap timestamps use the current camera_image_timestamp_map.csv
  - bioacoustic scientificName/genus/specificEpithet fields are filled from
    raw BirdNET result files
  - drone occurrences are regenerated from the labeled drone detection CSVs
  - citizen science and text Darwin Core outputs are copied into the snapshot
  - all modality-specific files are merged into events_all_modalities.csv and
    occurrences_all_modalities.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path


BASE_DIR = Path(os.environ.get("SMARTWILDS_ARCHIVE", ".")).resolve()
OUT_DIR = Path(os.environ.get("SMARTWILDS_DWC_OUT", BASE_DIR / "processing_output" / "darwin_core_release"))
SMARTWILDS_DIR = Path(os.environ.get("SMARTWILDS_DETECTIONS", BASE_DIR / "detections_external"))

EVENT_FIELDS = [
    "eventID", "parentEventID", "eventType", "eventDate", "samplingProtocol",
    "sampleSizeValue", "sampleSizeUnit", "locality", "locationID",
    "decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters",
    "geodeticDatum", "country", "stateProvince", "county", "datasetID",
    "datasetName", "recordedBy", "fieldNotes", "eventTime",
]

OCC_FIELDS = [
    "occurrenceID", "eventID", "catalogNumber", "scientificName", "kingdom",
    "phylum", "class", "order", "family", "genus", "specificEpithet",
    "taxonRank", "vernacularName", "occurrenceStatus", "individualCount",
    "lifeStage", "sex", "behavior", "basisOfRecord", "recordedBy",
    "identifiedBy", "identificationVerificationStatus", "identificationRemarks",
    "eventDate", "eventTime", "decimalLatitude", "decimalLongitude",
    "coordinateUncertaintyInMeters", "geodeticDatum", "locality", "locationID",
    "country", "stateProvince", "county", "establishmentMeans",
    "degreeOfEstablishment", "occurrenceRemarks", "associatedMedia",
    "associatedReferences", "datasetID", "datasetName", "informationWithheld",
    "dataGeneralizations",
]

SITE_GPS = {
    "TW01": ("39.83077", "-81.73789"),
    "TW02": ("39.83066", "-81.73792"),
    "TW03": ("39.83670", "-81.73607"),
    "TW04": ("39.83429", "-81.73934"),
    "TW05": ("39.83537", "-81.73842"),
    "TW06": ("39.83554", "-81.73000"),
    "TW07": ("39.83288", "-81.73455"),
    "TW08": ("39.82900", "-81.74378"),
    "TW09": ("39.82798", "-81.74167"),
    "TW11": ("39.83438", "-81.73930"),
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

STUDY_ROOT_EVENT = {
    "eventID": "TheWilds_2025",
    "parentEventID": "",
    "eventType": "Project",
    "eventDate": "2025-06-30/2025-09-08",
    "samplingProtocol": "Multi-modal biodiversity survey across camera traps, bioacoustics, drone video, citizen science, and text observations.",
    "sampleSizeValue": "5",
    "sampleSizeUnit": "modality projects",
    "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
    "locationID": "",
    "decimalLatitude": "39.83",
    "decimalLongitude": "-81.74",
    "coordinateUncertaintyInMeters": "5000",
    "geodeticDatum": "WGS84",
    "country": "United States",
    "stateProvince": "Ohio",
    "county": "Muskingum",
    "datasetID": "TheWilds_2025",
    "datasetName": "The Wilds 2025 Multi-Modal Survey",
    "recordedBy": "Field team",
    "fieldNotes": "Study-level root event for all modality project events.",
    "eventTime": "",
}

EXCLUDED_DRONE_MEDIA_EVENT = {
    "eventID": "TheWilds_2025_drone_20250703_parrotanafi_4_VID_001",
    "parentEventID": "TheWilds_2025_drone_20250703_parrotanafi_4",
    "eventType": "MediaEvent",
    "eventDate": "2025-07-03",
    "samplingProtocol": "Drone video VID_001; intentionally excluded from SAM3 and Tree-of-Life processing after review found no significant content.",
    "sampleSizeValue": "0",
    "sampleSizeUnit": "classified detection crops",
    "locality": "The Wilds Conservation Center",
    "locationID": "20250703_parrotanafi_4",
    "decimalLatitude": "39.830678500000175",
    "decimalLongitude": "-81.73834333333349",
    "coordinateUncertaintyInMeters": "100",
    "geodeticDatum": "WGS84",
    "country": "United States",
    "stateProvince": "Ohio",
    "county": "Muskingum",
    "datasetID": "TheWilds_2025_drones",
    "datasetName": "The Wilds 2025 Multi-Modal Survey - Drone Imagery",
    "recordedBy": "Drone field team",
    "fieldNotes": "Collection: thewilds_20250630_20250703; flight/session: 20250703_parrotanafi_4; video: VID_001; processingStatus: intentionally_excluded; reason: tiny video reviewed with no significant content; raw media: thewilds_20250630_20250703/drones/20250703_parrotanafi_4/video_files/VID_001.MP4",
    "eventTime": "",
}

TAXA = {
    "African Wild Dog": ("Lycaon pictus (Temminck, 1820)", "Animalia", "Chordata", "Mammalia", "Carnivora", "Canidae", "Lycaon", "pictus", "species"),
    "Bactrian Camel": ("Camelus bactrianus Linnaeus, 1758", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Camelidae", "Camelus", "bactrianus", "species"),
    "Bactrian Deer": ("Cervus hanglu bactrianus Lydekker, 1900", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Cervidae", "Cervus", "hanglu", "subspecies"),
    "Banteng": ("Bos javanicus d'Alton, 1823", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Bovidae", "Bos", "javanicus", "species"),
    "Bird": ("Aves", "Animalia", "Chordata", "Aves", "", "", "", "", "class"),
    "Bison": ("Bison bison (Linnaeus, 1758)", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Bovidae", "Bison", "bison", "species"),
    "Canada Goose": ("Branta canadensis (Linnaeus, 1758)", "Animalia", "Chordata", "Aves", "Anseriformes", "Anatidae", "Branta", "canadensis", "species"),
    "Camel": ("Camelus", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Camelidae", "Camelus", "", "genus"),
    "Coyote": ("Canis latrans Say, 1823", "Animalia", "Chordata", "Mammalia", "Carnivora", "Canidae", "Canis", "latrans", "species"),
    "Donkey": ("Equus asinus Linnaeus, 1758", "Animalia", "Chordata", "Mammalia", "Perissodactyla", "Equidae", "Equus", "asinus", "species"),
    "Eland": ("Taurotragus oryx (Pallas, 1766)", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Bovidae", "Taurotragus", "oryx", "species"),
    "Elk": ("Cervus canadensis Erxleben, 1777", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Cervidae", "Cervus", "canadensis", "species"),
    "Fish": ("Actinopterygii", "Animalia", "Chordata", "Actinopterygii", "", "", "", "", "class"),
    "Fox": ("Vulpes", "Animalia", "Chordata", "Mammalia", "Carnivora", "Canidae", "Vulpes", "", "genus"),
    "Fringe-eared Oryx": ("Oryx beisa callotis Thomas, 1892", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Bovidae", "Oryx", "beisa", "subspecies"),
    "Giraffe": ("Giraffa camelopardalis (Linnaeus, 1758)", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Giraffidae", "Giraffa", "camelopardalis", "species"),
    "Goat": ("Capra", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Bovidae", "Capra", "", "genus"),
    "Greater One-horned Rhino": ("Rhinoceros unicornis Linnaeus, 1758", "Animalia", "Chordata", "Mammalia", "Perissodactyla", "Rhinocerotidae", "Rhinoceros", "unicornis", "species"),
    "Grevy's Zebra": ("Equus grevyi Oustalet, 1882", "Animalia", "Chordata", "Mammalia", "Perissodactyla", "Equidae", "Equus", "grevyi", "species"),
    "Hawk": ("Accipitridae", "Animalia", "Chordata", "Aves", "Accipitriformes", "Accipitridae", "", "", "family"),
    "Heron": ("Ardeidae", "Animalia", "Chordata", "Aves", "Pelecaniformes", "Ardeidae", "", "", "family"),
    "Human": ("Homo sapiens Linnaeus, 1758", "Animalia", "Chordata", "Mammalia", "Primates", "Hominidae", "Homo", "sapiens", "species"),
    "Muskox": ("Ovibos moschatus (Zimmermann, 1780)", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Bovidae", "Ovibos", "moschatus", "species"),
    "Osprey": ("Pandion haliaetus (Linnaeus, 1758)", "Animalia", "Chordata", "Aves", "Accipitriformes", "Pandionidae", "Pandion", "haliaetus", "species"),
    "Ostrich": ("Struthio camelus Linnaeus, 1758", "Animalia", "Chordata", "Aves", "Struthioniformes", "Struthionidae", "Struthio", "camelus", "species"),
    "Pere David's Deer": ("Elaphurus davidianus Milne-Edwards, 1866", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Cervidae", "Elaphurus", "davidianus", "species"),
    "Persian Onager": ("Equus hemionus onager Boddaert, 1785", "Animalia", "Chordata", "Mammalia", "Perissodactyla", "Equidae", "Equus", "hemionus", "subspecies"),
    "Przewalski's Horse": ("Equus ferus przewalskii Poliakov, 1881", "Animalia", "Chordata", "Mammalia", "Perissodactyla", "Equidae", "Equus", "ferus", "subspecies"),
    "Scimitar-horned Oryx": ("Oryx dammah (Cretzschmar, 1827)", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Bovidae", "Oryx", "dammah", "species"),
    "Sichuan Takin": ("Budorcas taxicolor tibetana Milne-Edwards, 1874", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Bovidae", "Budorcas", "taxicolor", "subspecies"),
    "Southern White Rhino": ("Ceratotherium simum simum (Burchell, 1817)", "Animalia", "Chordata", "Mammalia", "Perissodactyla", "Rhinocerotidae", "Ceratotherium", "simum", "subspecies"),
    "Waterfowl": ("Anatidae", "Animalia", "Chordata", "Aves", "Anseriformes", "Anatidae", "", "", "family"),
    "White-tailed Deer": ("Odocoileus virginianus (Zimmermann, 1780)", "Animalia", "Chordata", "Mammalia", "Artiodactyla", "Cervidae", "Odocoileus", "virginianus", "species"),
}

ALIASES = {
    "african wild dog": "African Wild Dog",
    "antelope": "Eland",
    "banteng": "Banteng",
    "bird": "Bird",
    "bison": "Bison",
    "bos": "Banteng",
    "budorcas": "Sichuan Takin",
    "camel": "Camel",
    "camelus": "Camel",
    "canada goose": "Canada Goose",
    "canis": "Coyote",
    "cattle": "Banteng",
    "ceratotherium": "Southern White Rhino",
    "cervus": "Elk",
    "coyote": "Coyote",
    "deer": "White-tailed Deer",
    "donkey": "Donkey",
    "eland": "Eland",
    "elaphurus": "Pere David's Deer",
    "equus": "Przewalski's Horse",
    "fox": "Fox",
    "giraffa": "Giraffe",
    "giraffe": "Giraffe",
    "goat": "Goat",
    "grevy's zebra": "Grevy's Zebra",
    "hawk": "Hawk",
    "heron": "Heron",
    "horse": "Przewalski's Horse",
    "human": "Human",
    "lycaon": "African Wild Dog",
    "elk": "Elk",
    "milu deer": "Pere David's Deer",
    "muskox": "Muskox",
    "odocoileus": "White-tailed Deer",
    "oryx": "Fringe-eared Oryx",
    "osprey": "Osprey",
    "ostrich": "Ostrich",
    "pere david's deer": "Pere David's Deer",
    "persian onager": "Persian Onager",
    "person": "Human",
    "przewalski's horse": "Przewalski's Horse",
    "raptor": "Bird",
    "rhinoceros": "Greater One-horned Rhino",
    "sichuan takin": "Sichuan Takin",
    "songbird": "Bird",
    "struthio": "Ostrich",
    "taurotragus": "Eland",
    "waterfowl": "Waterfowl",
    "white-tailed deer": "White-tailed Deer",
    "wild dog": "African Wild Dog",
    "zebra": "Grevy's Zebra",
}


def clean_label(label: str) -> str:
    return (label or "").replace("Père", "Pere").strip()


def taxon_for(label: str) -> dict[str, str]:
    clean = clean_label(label)
    canonical = ALIASES.get(clean.lower(), clean)
    if canonical == "vehicle":
        return {
            "scientificName": "",
            "kingdom": "",
            "phylum": "",
            "class": "",
            "order": "",
            "family": "",
            "genus": "",
            "specificEpithet": "",
            "taxonRank": "",
            "vernacularName": "vehicle",
        }
    sci, kingdom, phylum, klass, order, family, genus, epithet, rank = TAXA.get(
        canonical, ("", "Animalia", "Chordata", "", "", "", "", "", "")
    )
    return {
        "scientificName": sci,
        "kingdom": kingdom,
        "phylum": phylum,
        "class": klass,
        "order": order,
        "family": family,
        "genus": genus,
        "specificEpithet": epithet,
        "taxonRank": rank,
        "vernacularName": canonical,
    }


def ensure_clean_output(force: bool) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "scripts").mkdir(parents=True, exist_ok=True)
    outputs = [
        OUT_DIR / "camera_traps",
        OUT_DIR / "bioacoustics_complete",
        OUT_DIR / "drones",
        OUT_DIR / "citizen_science",
        OUT_DIR / "text_data",
        OUT_DIR / "events_all_modalities.csv",
        OUT_DIR / "occurrences_all_modalities.csv",
        OUT_DIR / "QC_SUMMARY.md",
    ]
    existing = [p for p in outputs if p.exists()]
    if existing and not force:
        names = "\n".join(str(p) for p in existing)
        raise SystemExit(f"Refusing to overwrite existing outputs. Re-run with --force.\n{names}")
    if force:
        for p in existing:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


DATE_SENTINELS = {"", "nan", "nat", "none", "null", "n/a", "na", "-1", "1970-01-01"}

# The only original-video locations used as a fallback for invalid drone CSV coordinates.
# Values are read directly from each MP4's QuickTime ISO-6709 metadata.
DRONE_ORIGINAL_VIDEO_PATHS = {
    ("20250811_parrot_01", "P5180524"): BASE_DIR / "thewilds_20250804_20250828/drones/20250811_parrot_01/videos/P5180524.MP4",
    ("20250811_parrot_01", "P5190525"): BASE_DIR / "thewilds_20250804_20250828/drones/20250811_parrot_01/videos/P5190525.MP4",
    ("20250811_parrot_01", "P5190526"): BASE_DIR / "thewilds_20250804_20250828/drones/20250811_parrot_01/videos/P5190526.MP4",
    ("20250703_parrotanafi_5", "VID_001"): BASE_DIR / "thewilds_20250630_20250703/drones/20250703_parrotanafi_5/videos/VID_001.MP4",
    ("20250703_parrotanafi_5", "VID_002"): BASE_DIR / "thewilds_20250630_20250703/drones/20250703_parrotanafi_5/videos/VID_002.MP4",
}
QUICKTIME_ISO6709_RE = re.compile(
    rb"([+-]\d{1,3}(?:\.\d+)?)([+-]\d{1,3}(?:\.\d+)?)(?:[+-]\d+(?:\.\d+)?)?/"
)
DRONE_VIDEO_LOCATION_CACHE: dict[tuple[str, str], tuple[str, str] | None] = {}


def valid_wgs84_coordinates(latitude: str, longitude: str) -> bool:
    """Return whether a pair is finite and inside WGS84 latitude/longitude bounds."""
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False
    return math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180


def valid_wilds_video_location(latitude: str, longitude: str) -> bool:
    """Limit binary QuickTime matches to the documented study area before use."""
    if not valid_wgs84_coordinates(latitude, longitude):
        return False
    lat = float(latitude)
    lon = float(longitude)
    return 39.6 <= lat <= 40.1 and -82.1 <= lon <= -81.4


def original_video_location(flight: str, video_stem: str) -> tuple[str, str] | None:
    """Read one valid QuickTime ISO-6709 location from a whitelisted original MP4."""
    key = (flight, video_stem)
    if key in DRONE_VIDEO_LOCATION_CACHE:
        return DRONE_VIDEO_LOCATION_CACHE[key]

    path = DRONE_ORIGINAL_VIDEO_PATHS.get(key)
    if path is None or not path.is_file():
        DRONE_VIDEO_LOCATION_CACHE[key] = None
        return None

    size = path.stat().st_size
    window = 16 * 1024 * 1024
    with path.open("rb") as handle:
        chunks = [handle.read(window)]
        if size > window:
            handle.seek(max(0, size - window))
            chunks.append(handle.read(window))

    locations = {
        (match.group(1).decode("ascii").lstrip("+"), match.group(2).decode("ascii").lstrip("+"))
        for chunk in chunks
        for match in QUICKTIME_ISO6709_RE.finditer(chunk)
        if valid_wilds_video_location(
            match.group(1).decode("ascii"), match.group(2).decode("ascii")
        )
    }
    # A video-level fallback is defensible only when its metadata contains one location.
    location = next(iter(locations)) if len(locations) == 1 else None
    DRONE_VIDEO_LOCATION_CACHE[key] = location
    return location


def resolve_drone_occurrence_coordinates(row: dict, flight: str, video_stem: str) -> tuple[str, str, str, str]:
    """Resolve occurrence coordinates without allowing invalid CSV values into DwC."""
    if row.get("drone_georef_status") == "ok":
        lat = row.get("animal_lat_projected", "")
        lon = row.get("animal_lon_projected", "")
        if valid_wgs84_coordinates(lat, lon):
            return lat, lon, "50", "projected_animal_position"

    lat = row.get("latitude_y", "")
    lon = row.get("longitude_y", "")
    if valid_wgs84_coordinates(lat, lon):
        return lat, lon, "100", "frame_or_drone_telemetry"

    fallback = original_video_location(flight, video_stem)
    if fallback:
        return fallback[0], fallback[1], "500", "original_video_quicktime_location_static"
    return "", "", "", "unavailable_no_valid_source_coordinate"


def resolve_drone_event_coordinates(row: dict, flight: str, video_stem: str) -> tuple[str, str, str, str]:
    """Resolve a video Event position from telemetry or a static original-video fallback."""
    lat = row.get("latitude_y", "")
    lon = row.get("longitude_y", "")
    if valid_wgs84_coordinates(lat, lon):
        return lat, lon, "100", "frame_or_drone_telemetry"

    fallback = original_video_location(flight, video_stem)
    if fallback:
        return fallback[0], fallback[1], "500", "original_video_quicktime_location_static"
    return "", "", "", "unavailable_no_valid_source_coordinate"


def drone_coordinate_generalization(source: str) -> str:
    if source == "projected_animal_position":
        return "Approximate animal ground-position projection from drone telemetry and bbox bottom-center."
    if source == "frame_or_drone_telemetry":
        return "Frame/drone telemetry coordinate; not a projected animal position."
    if source == "original_video_quicktime_location_static":
        return "Static video-level location read from original-video QuickTime ISO-6709 metadata after the CSV coordinate failed WGS84 validation; it is not a frame- or animal-level position."
    return "No valid WGS84 coordinate was available from the geolocation CSV or original-video metadata."


DRONE_VIDEO_MEDIA_CACHE: dict[tuple[str, str, str, str], str] = {}


def resolve_drone_associated_media(row: dict, collection: str, flight: str, video_stem: str) -> tuple[str, str]:
    """Keep an extant extracted frame, otherwise link to its retained source video."""
    frame_path = row.get("frame_path", "")
    if frame_path and Path(frame_path).is_file():
        return frame_path, "extracted_frame"

    key = (collection, flight, row.get("subdir", ""), video_stem)
    if key not in DRONE_VIDEO_MEDIA_CACHE:
        video_dir = BASE_DIR / collection / "drones" / flight / row.get("subdir", "")
        candidates = sorted(item for item in video_dir.glob(video_stem + ".*") if item.is_file())
        DRONE_VIDEO_MEDIA_CACHE[key] = str(candidates[0]) if len(candidates) == 1 else ""
    video_path = DRONE_VIDEO_MEDIA_CACHE[key]
    if video_path:
        return video_path, "original_video_fallback_missing_scratch_frame"
    return "", "unavailable_no_retained_media"


def split_datetime(value: str) -> tuple[str, str]:
    """Return an ISO date/time only for a parseable timestamp."""
    value = (value or "").strip()
    if value.lower() in DATE_SENTINELS:
        return "", ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return "", ""
    return parsed.date().isoformat(), parsed.time().replace(microsecond=0).isoformat()


def date_from_identifier(identifier: str) -> str:
    """Extract and validate a YYYYMMDD date token from a flight identifier."""
    match = re.search(r"(?<!\d)(20\d{6})(?!\d)", identifier or "")
    if not match:
        return ""
    try:
        return date.fromisoformat(
            f"{match.group(1)[:4]}-{match.group(1)[4:6]}-{match.group(1)[6:]}"
        ).isoformat()
    except ValueError:
        return ""


def load_camera_timestamp_map() -> dict[str, dict]:
    path = BASE_DIR / "processing_output/detections/drone_camera_analysis/camera_time_mapping/camera_image_timestamp_map.csv"
    corrections = {}
    for row in read_csv(path):
        image_path = row.get("image_path", "")
        if image_path and row.get("corrected_timestamp"):
            corrections[image_path] = row
    return corrections


def load_camera_geolocation_config() -> list[dict]:
    path = BASE_DIR / "processing_output/detections/camera_traps/methods_paper/annotations/sam3/treeoflife_sam3/geolocation/camera_geolocation_config.csv"
    return [row for row in read_csv(path) if row.get("enabled", "1") not in {"0", "false", "False"}]


def choose_camera_config(configs: list[dict], collection: str, camera_id: str, frame_path: str) -> dict:
    candidates = [
        row for row in configs
        if row.get("collection") == collection and row.get("camera_id") == camera_id
    ]
    matching = [
        row for row in candidates
        if not row.get("path_contains") or row.get("path_contains") in frame_path
    ]
    if not matching:
        return {}
    return max(matching, key=lambda row: len(row.get("path_contains", "")))


def camera_csv_parts(csv_path: Path) -> tuple[str, str, str, str]:
    collection = csv_path.parent.parent.name
    camera_id = csv_path.parent.name
    if collection == "thewilds_20250630_20250703":
        event_range = "2025-06-30/2025-07-03"
    elif collection == "thewilds_20250804_20250828":
        event_range = "2025-08-04/2025-08-28"
    else:
        event_range = ""
    return collection, camera_id, collection.replace("thewilds_", ""), event_range


def site_from_camera(camera_id: str) -> str:
    return camera_id.replace("_", "-").split("-", 1)[0]


def taxon_from_treeoflife(row: dict) -> dict[str, str]:
    scientific = (
        row.get("top1_scientific_name")
        or row.get("top1_species")
        or row.get("top1_genus")
        or row.get("top1_family")
        or row.get("top1_order")
        or row.get("top1_class")
        or row.get("top1_common_name")
        or ""
    )
    genus = row.get("top1_genus", "")
    epithet = ""
    if row.get("top1_species"):
        parts = row["top1_species"].split()
        if len(parts) >= 2:
            epithet = parts[-1]
    elif scientific and len(scientific.split()) >= 2:
        epithet = scientific.split()[1]
    return {
        "scientificName": scientific,
        "kingdom": row.get("top1_kingdom", ""),
        "phylum": row.get("top1_phylum", ""),
        "class": row.get("top1_class", ""),
        "order": row.get("top1_order", ""),
        "family": row.get("top1_family", ""),
        "genus": genus,
        "specificEpithet": epithet,
        "taxonRank": row.get("top1_rank") or row.get("rank", ""),
        "vernacularName": row.get("top1_common_name", ""),
    }


def generate_camera_traps() -> tuple[int, int]:
    det_dir = BASE_DIR / "processing_output/detections/camera_traps/methods_paper/annotations/sam3/treeoflife_sam3/geolocation/geolocated_predictions"
    files = sorted(det_dir.glob("*/*/*.geolocated.csv"))
    corrections = load_camera_timestamp_map()
    geo_configs = load_camera_geolocation_config()
    events = [{
        "eventID": "TheWilds_2025_camera_traps",
        "parentEventID": "TheWilds_2025",
        "eventType": "Project",
        "eventDate": "2025-06-30/2025-08-28",
        "samplingProtocol": "Camera trap monitoring; detections by SAM3, Tree-of-Life classification by BioCLIP, animal position estimated from camera GPS/FOV/bearing and detection boxes.",
        "sampleSizeValue": str(len(files)),
        "sampleSizeUnit": "camera Tree-of-Life geolocation CSVs",
        "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
        "locationID": "",
        "decimalLatitude": "39.83",
        "decimalLongitude": "-81.74",
        "coordinateUncertaintyInMeters": "5000",
        "geodeticDatum": "WGS84",
        "country": "United States",
        "stateProvince": "Ohio",
        "county": "Muskingum",
        "datasetID": "TheWilds_2025_camera_traps",
        "datasetName": "The Wilds 2025 Multi-Modal Survey - Camera Traps",
        "recordedBy": "Field team",
        "fieldNotes": "Regenerated from SAM3 + BioCLIP Tree-of-Life detections using the latest timestamp mapping and geolocation outputs.",
        "eventTime": "",
    }]
    occurrences = []
    occ_num = 0
    for csv_path in files:
        collection, site_cam, campaign, event_range = camera_csv_parts(csv_path)
        site = site_from_camera(site_cam)
        rows = read_csv(csv_path)
        first_cfg = choose_camera_config(geo_configs, collection, site_cam, rows[0].get("frame_path", "") if rows else "")
        lat = first_cfg.get("camera_lat") or SITE_GPS.get(site, ("39.83", "-81.74"))[0]
        lon = first_cfg.get("camera_lon") or SITE_GPS.get(site, ("39.83", "-81.74"))[1]
        site_name = SITE_NAMES.get(site, site)
        event_id = f"TheWilds_2025_CT_deployment_{site_cam}_{campaign}"
        events.append({
            "eventID": event_id,
            "parentEventID": "TheWilds_2025_camera_traps",
            "eventType": "SensorDeployment",
            "eventDate": event_range,
            "samplingProtocol": f"Trail camera ({site_cam}); SAM3 detections with BioCLIP Tree-of-Life labels and geolocation estimates",
            "sampleSizeValue": str(len(rows)),
            "sampleSizeUnit": "detections",
            "locality": f"The Wilds - {site_name}",
            "locationID": site,
            "decimalLatitude": lat,
            "decimalLongitude": lon,
            "coordinateUncertaintyInMeters": "5",
            "geodeticDatum": "WGS84",
            "country": "United States",
            "stateProvince": "Ohio",
            "county": "Muskingum",
            "datasetID": "TheWilds_2025_camera_traps",
            "datasetName": "The Wilds 2025 Multi-Modal Survey - Camera Traps",
            "recordedBy": "Field team",
            "fieldNotes": f"Camera: {site_cam}; Campaign: {campaign}; detections: {len(rows)}; geolocation config source: {first_cfg.get('config_source', '')}",
            "eventTime": "",
        })
        for row in rows:
            occ_num += 1
            frame_path = row.get("frame_path", "")
            time_row = corrections.get(frame_path, {})
            taxon = taxon_from_treeoflife(row)
            timestamp = time_row.get("corrected_timestamp") or row.get("date_time", "")
            event_date, event_time = split_datetime(timestamp)
            occ_lat = row.get("animal_lat") or row.get("camera_lat") or lat
            occ_lon = row.get("animal_lon") or row.get("camera_lon") or lon
            bbox = f"[{row.get('bbox_x','')},{row.get('bbox_y','')},{row.get('bbox_width','')},{row.get('bbox_height','')}]"
            associated_media, media_source = resolve_drone_associated_media(
                row, collection, flight, video_stem
            )
            rank = row.get("rank", "")
            score = row.get("top1_score", "")
            source_label = row.get("source_label", "")
            correction_note = "; ".join(part for part in [
                f"timestamp_method: {time_row.get('correction_method', '')}" if time_row else "",
                f"timestamp_confidence: {time_row.get('correction_confidence', '')}" if time_row else "",
                f"geolocation_status: {row.get('geolocation_status', '')}",
                f"geolocation_source: {row.get('geolocation_config_source', '')}",
            ] if part)
            occurrences.append({
                "occurrenceID": f"TheWilds_2025_CT_{occ_num:06d}",
                "eventID": event_id,
                "catalogNumber": f"CT_{site_cam}_image{row.get('image_id','')}_ann{row.get('annotation_id','')}",
                **taxon,
                "occurrenceStatus": "present",
                "individualCount": "1",
                "basisOfRecord": "MachineObservation",
                "recordedBy": f"Trail camera ({site_cam})",
                "identifiedBy": "SAM3 + BioCLIP Tree of Life",
                "identificationVerificationStatus": "unverified",
                "identificationRemarks": f"Tree-of-Life rank: {rank}; top1 score: {score}; detector label: {source_label}; bbox xywh(px): {bbox}",
                "eventDate": event_date,
                "eventTime": event_time,
                "decimalLatitude": occ_lat,
                "decimalLongitude": occ_lon,
                "coordinateUncertaintyInMeters": "50",
                "geodeticDatum": "WGS84",
                "locality": f"The Wilds - {time_row.get('location') or site_name}",
                "locationID": site,
                "country": "United States",
                "stateProvince": "Ohio",
                "county": "Muskingum",
                "establishmentMeans": "managed",
                "degreeOfEstablishment": "captive",
                "occurrenceRemarks": f"Estimated distance: {row.get('animal_distance_m','')}m; estimated bearing: {row.get('animal_absolute_bearing_deg','')} deg; {correction_note}",
                "associatedMedia": frame_path,
                "datasetID": "TheWilds_2025_camera_traps",
                "datasetName": "The Wilds 2025 Multi-Modal Survey - Camera Traps",
                "informationWithheld": "",
                "dataGeneralizations": "Animal coordinates are model-derived estimates from camera position, camera bearing, HFOV, bbox height, and assumed target height; not GPS collars or direct observations.",
            })
    out = OUT_DIR / "camera_traps"
    write_csv(out / "darwin_core_events_camera_traps.csv", events, EVENT_FIELDS)
    write_csv(out / "darwin_core_occurrences_camera_traps.csv", occurrences, OCC_FIELDS)
    return len(events), len(occurrences)


def build_birdnet_scientific_map() -> dict[str, str]:
    mapping = {}
    roots = [
        BASE_DIR / "processing_output/detections/acoustics/BirdnetCSV_SunriseSunset",
        BASE_DIR / "processing_output/detections/acoustics/BirdNet_EveryHour",
    ]
    for root in roots:
        for path in root.glob("*.BirdNET.results.csv"):
            for row in read_csv(path):
                common = (row.get("Common name") or row.get("Common Name") or "").strip()
                sci = (row.get("Scientific name") or row.get("Scientific Name") or "").strip()
                if common and sci:
                    mapping.setdefault(common, sci)
    return mapping


BIOACOUSTIC_FILE_ID_MAP = {
    "SM001": "SM01",
    "SM002": "SM02",
    "2MM18157": "SM05",
    "2MM18027": "SM06",
}
BIOACOUSTIC_RESULT_SOURCES = [
    (BASE_DIR / "processing_output/detections/acoustics/BirdNet_EveryHour", "every_hour"),
    (BASE_DIR / "BioacousticAnalysis/BirdnetCSV_SunriseSunset", "sunrise_sunset"),
]
BIOACOUSTIC_RESULT_NAME_RE = re.compile(r"^([A-Za-z0-9]+)_(\d{8})_(\d{6})\.BirdNET\.results\.csv$")


def add_header_only_birdnet_events(events: list[dict[str, str]]) -> int:
    """Represent processed recordings with empty BirdNET result files as Events."""
    existing_ids = {row["eventID"] for row in events}
    deployments = []
    recording_protocols = {}
    for row in events:
        if row.get("eventType") == "SensorDeployment":
            match = re.search(r"Recorder: (SM\d+)", row.get("fieldNotes", ""))
            if match:
                start, end = row["eventDate"].split("/")
                deployments.append((match.group(1), date.fromisoformat(start), date.fromisoformat(end), row))
        elif row.get("eventType") == "AudioRecording":
            recording_protocols.setdefault(row.get("parentEventID", ""), row.get("samplingProtocol", ""))

    additions = []
    for result_dir, schedule_type in BIOACOUSTIC_RESULT_SOURCES:
        for path in sorted(result_dir.glob("*.BirdNET.results.csv")):
            if read_csv(path):
                continue
            match = BIOACOUSTIC_RESULT_NAME_RE.match(path.name)
            if not match:
                continue
            raw_recorder, ymd, hms = match.groups()
            recorder = BIOACOUSTIC_FILE_ID_MAP.get(raw_recorder, raw_recorder)
            recording_date = date.fromisoformat(f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}")
            deployment = next(
                (row for rec, start, end, row in deployments
                 if rec == recorder and start <= recording_date <= end),
                None,
            )
            if deployment is None:
                raise ValueError(f"No deployment for header-only BirdNET result: {path}")
            file_id = f"{recorder}_{ymd}_{hms}"
            event_id = f"TheWilds_2025_ARU_{file_id}"
            if event_id in existing_ids:
                continue
            protocol = recording_protocols.get(deployment["eventID"], deployment["samplingProtocol"])
            additions.append({
                "eventID": event_id,
                "parentEventID": deployment["eventID"],
                "eventType": "AudioRecording",
                "eventDate": recording_date.isoformat(),
                "samplingProtocol": protocol,
                "sampleSizeValue": "1",
                "sampleSizeUnit": "WAV recording",
                "locality": deployment["locality"],
                "locationID": deployment["locationID"],
                "decimalLatitude": deployment["decimalLatitude"],
                "decimalLongitude": deployment["decimalLongitude"],
                "coordinateUncertaintyInMeters": deployment["coordinateUncertaintyInMeters"],
                "geodeticDatum": deployment["geodeticDatum"],
                "country": deployment["country"],
                "stateProvince": deployment["stateProvince"],
                "county": deployment["county"],
                "datasetID": deployment["datasetID"],
                "datasetName": deployment["datasetName"],
                "recordedBy": deployment["recordedBy"],
                "fieldNotes": (
                    f"Recording: {file_id}.wav; Recorder: {recorder}; "
                    "Total BirdNET detections: 0; "
                    f"Schedule type: {schedule_type}; "
                    f"Provenance: header-only BirdNET result {path.name}."
                ),
                "eventTime": f"{hms[:2]}:{hms[2:4]}:{hms[4:]}",
            })
            existing_ids.add(event_id)
    if len(additions) != 64:
        raise ValueError(f"Expected 64 header-only BirdNET Events, found {len(additions)}")
    events.extend(sorted(additions, key=lambda row: row["eventID"]))
    return len(additions)


def patch_bioacoustics() -> tuple[int, int]:
    src = BASE_DIR / "processing_output/darwin_core/bioacoustics_complete"
    out = OUT_DIR / "bioacoustics_complete"
    out.mkdir(parents=True, exist_ok=True)
    events = read_csv(src / "darwin_core_events_bioacoustics_complete.csv")
    occ = read_csv(src / "darwin_core_occurrences_bioacoustics_complete.csv")
    added_empty_events = add_header_only_birdnet_events(events)
    mapping = build_birdnet_scientific_map()
    for row in occ:
        sci = row.get("scientificName") or mapping.get(row.get("vernacularName", ""), "")
        row["scientificName"] = sci
        if sci:
            parts = sci.split()
            row["kingdom"] = row.get("kingdom") or "Animalia"
            row["phylum"] = row.get("phylum") or "Chordata"
            row["class"] = row.get("class") or "Aves"
            row["genus"] = row.get("genus") or parts[0]
            row["specificEpithet"] = row.get("specificEpithet") or (parts[1] if len(parts) > 1 else "")
            row["taxonRank"] = row.get("taxonRank") or ("species" if len(parts) > 1 else "")
    write_csv(out / "darwin_core_events_bioacoustics_complete.csv", events, list(events[0].keys()))
    write_csv(out / "darwin_core_occurrences_bioacoustics_complete.csv", occ, list(occ[0].keys()))
    results = src / "RESULTS.md"
    if results.exists():
        summary = results.read_text(encoding="utf-8")
        summary = summary.replace("**2,307 recordings**", "**2,371 recordings**")
        summary = summary.replace("| Campaign 1 | Jun 30 – Jul 3 | 300 |", "| Campaign 1 | Jun 30 – Jul 3 | 311 |")
        summary = summary.replace("| Campaign 2 | Aug 4 – Aug 28 | 2,007 |", "| Campaign 2 | Aug 4 – Aug 28 | 2,060 |")
        summary = summary.replace("| TW02 | Nomad Ridge Shelter | Aug 4–28 | 561 |", "| TW02 | Nomad Ridge Shelter | Aug 4–28 | 581 |")
        summary = summary.replace("| TW06 | Zebra Shelter | Jun 30–Aug 28 | 550 |", "| TW06 | Zebra Shelter | Jun 30–Aug 28 | 585 |")
        summary = summary.replace("| TW08 | Fence with Vegetation | Jun 30–Aug 28 | 410 |", "| TW08 | Fence with Vegetation | Jun 30–Aug 28 | 419 |")
        summary += "\n\n## Recording Completeness Repair\n\nThe corrected snapshot includes 64 processed recordings whose BirdNET result CSVs contain only a header and therefore have zero detections. They are represented as `AudioRecording` Events with no Occurrences.\n"
        (out / "RESULTS.md").write_text(summary, encoding="utf-8")
    return len(events), len(occ)


def generate_drones() -> tuple[int, int]:
    det_dir = BASE_DIR / "processing_output/detections/drones/geolocation/geolocated_predictions"
    files = sorted(det_dir.glob("*.drone_geolocated.csv"))
    if not files:
        raise FileNotFoundError(f"No drone geolocated Tree-of-Life prediction CSVs found under {det_dir}")

    project_event = {
        "eventID": "TheWilds_2025_drones",
        "parentEventID": "TheWilds_2025",
        "eventType": "Project",
        "eventDate": "2025-07-01/2025-09-08",
        "samplingProtocol": "Drone video surveys; detections by SAM3, Tree-of-Life classification by BioCLIP, and first-pass animal ground-position projection from drone telemetry.",
        "sampleSizeValue": str(len(files)),
        "sampleSizeUnit": "drone video geolocated Tree-of-Life prediction CSVs",
        "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
        "locationID": "",
        "decimalLatitude": "39.83",
        "decimalLongitude": "-81.74",
        "coordinateUncertaintyInMeters": "5000",
        "geodeticDatum": "WGS84",
        "country": "United States",
        "stateProvince": "Ohio",
        "county": "Muskingum",
        "datasetID": "TheWilds_2025_drones",
        "datasetName": "The Wilds 2025 Multi-Modal Survey - Drone Imagery",
        "recordedBy": "Drone field team",
        "fieldNotes": "38 videos regenerated from per-video SAM3 + BioCLIP Tree-of-Life prediction CSVs with approximate animal ground-position projections where possible; VID_001 from 20250703_parrotanafi_4 is retained as an intentionally excluded raw-media Event.",
        "eventTime": "",
    }
    events = [project_event]
    flight_events: dict[str, dict] = {}
    occurrences = []
    occ_num = 0
    for path in files:
        rows = read_csv(path)
        if not rows:
            continue

        first = rows[0]
        collection = first.get("collection", "")
        flight = first.get("flight", "")
        video_stem = first.get("video_stem", "") or path.stem.split("_")[-1]
        fallback_date = date_from_identifier(flight)
        date_values = sorted(
            {
                parsed_date
                for row in rows
                if (parsed_date := split_datetime(row.get("date_time", ""))[0])
            }
        )
        event_date = (
            date_values[0]
            if len(date_values) == 1
            else f"{date_values[0]}/{date_values[-1]}" if date_values else fallback_date
        )
        event_date_derived = not date_values and bool(fallback_date)
        event_times = sorted(
            {
                parsed_time
                for row in rows
                if (parsed_time := split_datetime(row.get("date_time", ""))[1])
            }
        )
        event_time = (
            event_times[0]
            if len(event_times) == 1
            else f"{event_times[0]}/{event_times[-1]}" if event_times else ""
        )
        event_lat, event_lon, event_uncertainty, event_coordinate_source = resolve_drone_event_coordinates(
            first, flight, video_stem
        )
        # A static location is valid for a single video, but not necessarily for a flight
        # with multiple videos; keep the parent Event blank in that situation.
        if event_coordinate_source == "frame_or_drone_telemetry":
            flight_lat, flight_lon, flight_uncertainty = event_lat, event_lon, event_uncertainty
        else:
            flight_lat = flight_lon = flight_uncertainty = ""
        flight_event_id = f"TheWilds_2025_drone_{flight}"
        video_event_id = f"TheWilds_2025_drone_{flight}_{video_stem}"

        if flight and flight_event_id not in flight_events:
            flight_events[flight_event_id] = {
                "eventID": flight_event_id,
                "parentEventID": "TheWilds_2025_drones",
                "eventType": "SensorDeployment",
                "eventDate": event_date,
                "samplingProtocol": f"Drone flight/session {flight}; SAM3 detections with BioCLIP Tree-of-Life labels and projected animal positions where available",
                "sampleSizeValue": "",
                "sampleSizeUnit": "detections",
                "locality": "The Wilds Conservation Center",
                "locationID": flight,
                "decimalLatitude": flight_lat,
                "decimalLongitude": flight_lon,
                "coordinateUncertaintyInMeters": flight_uncertainty,
                "geodeticDatum": "WGS84",
                "country": "United States",
                "stateProvince": "Ohio",
                "county": "Muskingum",
                "datasetID": "TheWilds_2025_drones",
                "datasetName": "The Wilds 2025 Multi-Modal Survey - Drone Imagery",
                "recordedBy": "Drone field team",
                "fieldNotes": f"Collection: {collection}; flight/session: {flight}; coordinate_source={event_coordinate_source}",
                "eventTime": "",
            }

        events.append({
            "eventID": video_event_id,
            "parentEventID": flight_event_id,
            "eventType": "MediaEvent",
            "eventDate": event_date,
            "samplingProtocol": f"Drone video {video_stem}; SAM3 detections with BioCLIP Tree-of-Life labels and projected animal positions where available",
            "sampleSizeValue": str(len(rows)),
            "sampleSizeUnit": "classified detection crops",
            "locality": "The Wilds Conservation Center",
            "locationID": flight,
            "decimalLatitude": event_lat,
            "decimalLongitude": event_lon,
            "coordinateUncertaintyInMeters": event_uncertainty,
            "geodeticDatum": "WGS84",
            "country": "United States",
            "stateProvince": "Ohio",
            "county": "Muskingum",
            "datasetID": "TheWilds_2025_drones",
            "datasetName": "The Wilds 2025 Multi-Modal Survey - Drone Imagery",
            "recordedBy": "Drone field team",
            "fieldNotes": f"Collection: {collection}; flight/session: {flight}; video: {video_stem}; detections: {len(rows)}; source CSV: {path.name}; coordinate_source={event_coordinate_source}",
            "eventTime": event_time,
        })

        for row in rows:
            occ_num += 1
            taxon = taxon_from_treeoflife(row)
            event_date, event_time = split_datetime(row.get("date_time", ""))
            event_date_derived_for_row = not event_date and bool(fallback_date)
            if event_date_derived_for_row:
                event_date = fallback_date
            lat, lon, coord_uncertainty, coordinate_source = resolve_drone_occurrence_coordinates(
                row, flight, video_stem
            )
            coordinate_withheld = (
                "Coordinate unavailable: no valid WGS84 geolocation CSV value or original-video metadata location."
                if coordinate_source == "unavailable_no_valid_source_coordinate" else ""
            )
            information_withheld = "; ".join(part for part in [
                "Intra-day timestamp unavailable; eventDate derived from flight identifier."
                if event_date_derived_for_row else "",
                coordinate_withheld,
            ] if part)
            bbox = f"[{row.get('bbox_x','')},{row.get('bbox_y','')},{row.get('bbox_width','')},{row.get('bbox_height','')}]"
            rank = row.get("rank", "")
            score = row.get("top1_score", "")
            source_label = row.get("source_label", "")
            occurrences.append({
                "occurrenceID": f"TheWilds_2025_drone_{occ_num:06d}",
                "eventID": video_event_id,
                "catalogNumber": f"drone_{flight}_{video_stem}_image{row.get('image_id','')}_ann{row.get('annotation_id','')}",
                **taxon,
                "occurrenceStatus": "present",
                "individualCount": "1",
                "basisOfRecord": "MachineObservation",
                "recordedBy": "Drone imagery",
                "identifiedBy": "SAM3 + BioCLIP Tree of Life",
                "identificationVerificationStatus": "unverified",
                "identificationRemarks": f"Tree-of-Life rank: {rank}; top1 score: {score}; detector label: {source_label}; bbox xywh(px): {bbox}; altitude_m: {row.get('altitude_m','')}",
                "eventDate": event_date,
                "eventTime": event_time,
                "decimalLatitude": lat,
                "decimalLongitude": lon,
                "coordinateUncertaintyInMeters": coord_uncertainty,
                "geodeticDatum": "WGS84",
                "locality": "The Wilds Conservation Center",
                "locationID": flight,
                "country": "United States",
                "stateProvince": "Ohio",
                "county": "Muskingum",
                "establishmentMeans": "managed",
                "degreeOfEstablishment": "captive",
                "occurrenceRemarks": "; ".join(part for part in [
                    "Frame-level drone detection crop",
                    "event_date_source=flight_identifier" if event_date_derived_for_row else "event_date_source=source_datetime",
                    f"source={row.get('source','')}",
                    f"mission_id={row.get('mission_id','')}",
                    f"detection_id={row.get('detection_id','')}",
                    f"drone_georef_status={row.get('drone_georef_status','')}",
                    f"coordinate_source={coordinate_source}",
                    f"associated_media_source={media_source}",
                    f"projected_ground_range_m={row.get('animal_ground_range_m','')}" if row.get("animal_ground_range_m") else "",
                    f"projected_bearing_deg={row.get('animal_bearing_deg','')}" if row.get("animal_bearing_deg") else "",
                    f"drone_altitude_used_m={row.get('drone_altitude_used_m','')}" if row.get("drone_altitude_used_m") else "",
                    f"drone_pitch_source={row.get('drone_pitch_source','')}" if row.get("drone_pitch_source") else "",
                ] if part),
                "associatedMedia": associated_media,
                "datasetID": "TheWilds_2025_drones",
                "datasetName": "The Wilds 2025 Multi-Modal Survey - Drone Imagery",
                "informationWithheld": information_withheld,
                "dataGeneralizations": drone_coordinate_generalization(coordinate_source),
            })
    # Represent the reviewed-but-intentionally-unprocessed raw video explicitly.
    if not any(row.get("eventID") == EXCLUDED_DRONE_MEDIA_EVENT["eventID"] for row in events):
        events.append(dict(EXCLUDED_DRONE_MEDIA_EVENT))
    # Insert flight/session events before the per-video events.
    events = [project_event] + list(flight_events.values()) + events[1:]
    out = OUT_DIR / "drones"
    write_csv(out / "darwin_core_events_drones.csv", events, list(events[0].keys()))
    write_csv(out / "darwin_core_occurrences_drones.csv", occurrences, OCC_FIELDS)
    return len(events), len(occurrences)


def copy_existing_modality(modality: str, files: list[str]) -> tuple[int, int]:
    src = BASE_DIR / "processing_output/darwin_core" / modality
    dst = OUT_DIR / modality
    dst.mkdir(parents=True, exist_ok=True)
    events_n = occ_n = 0
    for filename in files:
        src_file = src / filename
        dst_file = dst / filename
        shutil.copy2(src_file, dst_file)
        if filename.endswith(".csv"):
            n = len(read_csv(dst_file))
            if "events" in filename:
                events_n += n
            elif "occurrences" in filename:
                occ_n += n
    return events_n, occ_n


def patch_citizen_science_provenance() -> tuple[int, int]:
    """Clarify citizen-science raw, curated, and external-album media provenance."""
    events_path = OUT_DIR / "citizen_science/darwin_core_events_citizen_science.csv"
    occurrences_path = OUT_DIR / "citizen_science/darwin_core_occurrences_citizen_science.csv"
    raw_dir = BASE_DIR / "thewilds_20250804_20250828/citizen_science/photos_videos"
    events = read_csv(events_path)
    for row in events:
        if row.get("eventID") == "TheWilds_2025_citizen_science":
            row["sampleSizeValue"] = "564"
            row["sampleSizeUnit"] = "curated wildlife photographs"
            row["fieldNotes"] = ("Raw-folder inventory: 1,103 media files (965 still images and 138 videos). "
                                 "Manual annotations cover 791 photos; curation retained 564 wildlife photos. "
                                 "Multi-taxon photos yield 622 Darwin Core Occurrences across 13 observation sessions. "
                                 "Fifty curated Sep. 8 photos are sourced from the Google Photos album export rather "
                                 "than the photos_videos folder; their media references state that source explicitly.")
    write_csv(events_path, events, EVENT_FIELDS)
    occurrences = read_csv(occurrences_path)
    external = 0
    for row in occurrences:
        filename = Path(row.get("associatedMedia", "")).name
        if filename and not (raw_dir / filename).is_file():
            row["associatedMedia"] = f"Google Photos Takeout/The Wilds 9-8-25/{filename}"
            note = "media_source=Google Photos Takeout/The Wilds 9-8-25; not in photos_videos raw-folder inventory"
            if note not in row.get("occurrenceRemarks", ""):
                row["occurrenceRemarks"] = "; ".join(part for part in [row.get("occurrenceRemarks", ""), note] if part)
            external += 1
    if external != 50:
        raise ValueError(f"Expected 50 externally sourced citizen-science media references, found {external}")
    write_csv(occurrences_path, occurrences, OCC_FIELDS)
    audit = {
        "reconciliation": "citizen-science media populations and provenance",
        "raw_folder": "thewilds_20250804_20250828/citizen_science/photos_videos",
        "raw_folder_media_files": 1103,
        "raw_folder_file_types": {"jpeg": 507, "jpg": 346, "heic": 112, "mov": 91, "mp4": 47},
        "raw_folder_still_images": 965,
        "raw_folder_videos": 138,
        "manual_annotation_input_photos": 791,
        "curated_wildlife_photos": 564,
        "darwin_core_occurrences": 622,
        "observation_sessions": 13,
        "curated_media_in_raw_folder": 514,
        "curated_media_from_google_photos_album_only": 50,
        "external_album_media_date": "2025-09-08",
        "external_album_media_reference_prefix": "Google Photos Takeout/The Wilds 9-8-25/",
        "retired_unreproducible_counts": ["~991 submissions", "1,128 photographs"],
    }
    (OUT_DIR / "citizen_science_media_reconciliation_20261008.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    return len(events), len(occurrences)


def merge_outputs() -> tuple[int, int]:
    event_files = [
        OUT_DIR / "camera_traps/darwin_core_events_camera_traps.csv",
        OUT_DIR / "bioacoustics_complete/darwin_core_events_bioacoustics_complete.csv",
        OUT_DIR / "drones/darwin_core_events_drones.csv",
        OUT_DIR / "citizen_science/darwin_core_events_citizen_science.csv",
        OUT_DIR / "text_data/darwin_core_events_text.csv",
    ]
    occ_files = [
        ("camera_traps", OUT_DIR / "camera_traps/darwin_core_occurrences_camera_traps.csv"),
        ("bioacoustics", OUT_DIR / "bioacoustics_complete/darwin_core_occurrences_bioacoustics_complete.csv"),
        ("drones", OUT_DIR / "drones/darwin_core_occurrences_drones.csv"),
        ("citizen_science", OUT_DIR / "citizen_science/darwin_core_occurrences_citizen_science.csv"),
        ("text_data", OUT_DIR / "text_data/darwin_core_occurrences_text.csv"),
    ]
    events = [dict(STUDY_ROOT_EVENT)]
    for path in event_files:
        events.extend(read_csv(path))
    occ = []
    fields = ["modality_type"] + OCC_FIELDS
    for modality, path in occ_files:
        for row in read_csv(path):
            out = {field: row.get(field, "") for field in OCC_FIELDS}
            out["modality_type"] = modality
            occ.append(out)
    write_csv(OUT_DIR / "events_all_modalities.csv", events, EVENT_FIELDS)
    write_csv(OUT_DIR / "occurrences_all_modalities.csv", occ, fields)
    return len(events), len(occ)


def valid_event_date(value: str) -> bool:
    """Accept one ISO date or an ISO date interval, rejecting known sentinels."""
    value = (value or "").strip()
    if value.lower() in DATE_SENTINELS:
        return False
    parts = value.split("/")
    if not parts or len(parts) > 2:
        return False
    try:
        for part in parts:
            if part.lower() in DATE_SENTINELS:
                return False
            date.fromisoformat(part)
    except ValueError:
        return False
    return True


def validate_snapshot() -> list[str]:
    notes = []
    event_ids = set()
    for path in OUT_DIR.glob("*/darwin_core_events*.csv"):
        rows = read_csv(path)
        event_ids.update(row.get("eventID", "") for row in rows)
        missing_date = sum(1 for row in rows if not row.get("eventDate"))
        invalid_date = sum(1 for row in rows if not valid_event_date(row.get("eventDate", "")))
        notes.append(
            f"- `{path.relative_to(OUT_DIR)}`: rows={len(rows)}, "
            f"missing_eventDate={missing_date}, invalid_eventDate={invalid_date}"
        )
    for path in OUT_DIR.glob("*/darwin_core_occurrences*.csv"):
        rows = read_csv(path)
        missing_event = sum(1 for row in rows if row.get("eventID") not in event_ids)
        missing_taxon = sum(1 for row in rows if not (row.get("scientificName") or row.get("vernacularName")))
        missing_date = sum(1 for row in rows if not row.get("eventDate"))
        invalid_date = sum(1 for row in rows if not valid_event_date(row.get("eventDate", "")))
        dup_ids = len(rows) - len({row.get("occurrenceID") for row in rows})
        notes.append(
            f"- `{path.relative_to(OUT_DIR)}`: rows={len(rows)}, "
            f"missing_event_links={missing_event}, missing_taxon={missing_taxon}, "
            f"missing_eventDate={missing_date}, invalid_eventDate={invalid_date}, "
            f"duplicate_occurrenceID={dup_ids}"
        )
    return notes

def write_qc_summary(counts: dict[str, tuple[int, int]], merged: tuple[int, int]) -> None:
    lines = [
        "# Darwin Core QC Summary",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Counts",
        "",
    ]
    for modality, (events, occ) in counts.items():
        lines.append(f"- {modality}: events={events}, occurrences={occ}")
    lines.append(f"- merged: events={merged[0]}, occurrences={merged[1]}")
    lines.extend([
        "",
        "## Validation",
        "",
        *validate_snapshot(),
        "",
        "## Notes",
        "",
        "- Camera traps use SAM3 detections, BioCLIP Tree-of-Life labels, the current camera timestamp map, and model-derived animal geolocation estimates.",
        "- Bioacoustic scientific names are filled from BirdNET result CSV common-name mappings.",
        "- Drone occurrences use per-video SAM3 + BioCLIP Tree-of-Life prediction CSVs after first-pass drone ground-position projection.",
        "- Drone decimalLatitude/decimalLongitude use projected animal coordinates only when `drone_georef_status=ok`; otherwise they fall back to frame/drone telemetry coordinates.",
        "- Citizen-science and text-data outputs are copied from the existing Darwin Core outputs.",
        "- Camera-trap animal coordinates are estimated positions, not direct GPS observations; see `dataGeneralizations` and geolocation provenance columns in the archived prediction CSVs.",
    ])
    (OUT_DIR / "QC_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated snapshot outputs under OUT_DIR.")
    args = parser.parse_args()

    ensure_clean_output(args.force)
    counts = {}
    counts["camera_traps"] = generate_camera_traps()
    counts["bioacoustics_complete"] = patch_bioacoustics()
    counts["drones"] = generate_drones()
    counts["citizen_science"] = copy_existing_modality("citizen_science", [
        "darwin_core_events_citizen_science.csv",
        "darwin_core_occurrences_citizen_science.csv",
    ])
    counts["citizen_science"] = patch_citizen_science_provenance()
    counts["text_data"] = copy_existing_modality("text_data", [
        "darwin_core_events_text.csv",
        "darwin_core_occurrences_text.csv",
        "site_selection_rationale.csv",
    ])
    merged = merge_outputs()
    write_qc_summary(counts, merged)
    print(f"Wrote Darwin Core tables to {OUT_DIR}")
    for modality, (events, occ) in counts.items():
        print(f"  {modality}: events={events}, occurrences={occ}")
    print(f"  merged: events={merged[0]}, occurrences={merged[1]}")


if __name__ == "__main__":
    main()
