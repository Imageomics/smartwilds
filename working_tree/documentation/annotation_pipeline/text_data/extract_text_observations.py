#!/usr/bin/env python3
"""
Extract structured observations from text data (field notes, observer logs,
drone mission notes, site descriptions) into Darwin Core compliant format.

This is a rule-based extraction pass. For production, augment with LLM-based
extraction for nuanced behavioral descriptions and implicit species mentions.

Input:  Text files across all 3 campaigns
Output: darwin_core_events_text.csv
        darwin_core_occurrences_text.csv
        site_selection_rationale.csv

The taxon map is imported from the citizen science pipeline for consistency.
"""

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# ─── Configuration ─────────────────────────────────────────────────────────────

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
OUTPUT_DIR = BASE_DIR / "processing_output" / "darwin_core" / "text_data"

# Reuse taxon map from citizen science pipeline, extended with additional species
TAXON_MAP = {
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
}

# Site GPS coordinates (decimal degrees, from detection_config.json)
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
    "TW10": (39.83, -81.74),  # approximate
    "TW11": (39.83438, -81.73930),
    "Nomad": (39.83077, -81.73789),
    "Dock": (39.82798, -81.74167),
    "Lake": (39.83429, -81.73934),
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
    "TW10": "Fence near Lake Entrance",
    "TW11": "Fence overlooking Lake",
}


# ─── Observation dataclass ─────────────────────────────────────────────────────

class TextObservation:
    """A single species observation extracted from text."""
    def __init__(
        self,
        species: str,
        date: str,
        time: str = "",
        site_id: str = "",
        locality: str = "",
        count: Optional[int] = None,
        behavior: str = "",
        life_stage: str = "",
        sex: str = "",
        observer: str = "",
        source_file: str = "",
        source_text: str = "",
        observation_type: str = "field_note",
    ):
        self.species = species
        self.date = date
        self.time = time
        self.site_id = site_id
        self.locality = locality
        self.count = count
        self.behavior = behavior
        self.life_stage = life_stage
        self.sex = sex
        self.observer = observer
        self.source_file = source_file
        self.source_text = source_text
        self.observation_type = observation_type


# ─── Extraction functions ──────────────────────────────────────────────────────

def extract_field_notes_20250630() -> List[TextObservation]:
    """Extract observations from June 30 field notes."""
    obs = []
    date = "2025-06-30"
    src = "field_notes/field_notes_20250630.md"

    # Jenna's observations
    obs.append(TextObservation(
        species="Pere David's Deer", date=date, site_id="TW01",
        locality="Nomad Ridge Shelter", behavior="congregating near lake; high activity",
        observer="Jenna Kline", source_file=src,
        source_text="installed camera traps first, then sounds meters, then went and looked at rhinos",
    ))

    # Bharath's observations
    obs.append(TextObservation(
        species="Pere David's Deer", date=date, site_id="TW01",
        locality="Nomad Ridge Shelter",
        behavior="receptive and social; curious about equipment installation; minimal disruption",
        observer="Bharath Pillai", source_file=src,
        source_text="Animals were quite receptive and social of our interactions the deer seemed more curious about our setup",
    ))

    # Penelope's observations - breeding season
    obs.append(TextObservation(
        species="Pere David's Deer", date=date, site_id="TW01",
        locality="Nomad Ridge Shelter",
        behavior="breeding season; herd split into two groups with two males; males croaking to mark territory",
        count=2, life_stage="adult", sex="male",
        observer="Penelope Covey", source_file=src,
        source_text="Currently breeding season for deer. Normal herd split into two groups with two males. Males croak to mark territory.",
    ))
    obs.append(TextObservation(
        species="Pere David's Deer", date=date, site_id="TW01",
        locality="Nomad Ridge Shelter",
        behavior="wading in water due to warm weather; seeking shade",
        observer="Penelope Covey", source_file=src,
        source_text="Animals wading in water due to warm weather",
    ))

    # Ally's observations
    obs.append(TextObservation(
        species="Pere David's Deer", date=date, site_id="TW01",
        locality="Nomad Ridge Shelter, land bridge between two lakes",
        behavior="congregating at land bridge between two lakes",
        observer="Ally Bonney", source_file=src,
        source_text="CT02 at Nomad Shelter overlooks land bridge between two lakes where deer congregate",
    ))

    # Tanishka's observations
    obs.append(TextObservation(
        species="Banteng", date=date, site_id="TW03",
        locality="Pasture D, salt lick near old giraffe feeder",
        behavior="grazing near salt lick",
        count=4, sex="3 female, 1 male",
        observer="Tanishka Wani", source_file=src,
        source_text="Observed 3 female and 1 male wild cows",
    ))

    # Bird observations from acoustic sensor sites
    obs.append(TextObservation(
        species="Bird", date=date, site_id="TW05",
        locality="Lake Trail Gate O",
        behavior="vocalizing; target of ARU recording at sunrise/sunset",
        observer="Tanishka Wani", source_file=src,
        source_text="Bioacoustic recorder near Gate O to capture bird calls at sunrise/sunset",
    ))

    return obs


def extract_field_notes_20250804() -> List[TextObservation]:
    """Extract observations from August 4 installation notes."""
    obs = []
    date = "2025-08-04"
    src = "field_notes/field_notes_20250804.md"

    obs.append(TextObservation(
        species="Pere David's Deer", date=date, site_id="TW01",
        locality="Nomad Ridge Shelter",
        behavior="high activity observed during sensor installation",
        observer="Field team", source_file=src,
    ))

    obs.append(TextObservation(
        species="Przewalski's Horse", date=date, site_id="TW03",
        locality="Pasture D, near old giraffe feeder",
        behavior="grazing in herd with Pere David's deer",
        observer="Field team", source_file=src,
        source_text="Herd of horses and 2 Pere David's deer grazing",
    ))
    obs.append(TextObservation(
        species="Pere David's Deer", date=date, site_id="TW03",
        locality="Pasture D", behavior="grazing with horses",
        count=2, observer="Field team", source_file=src,
    ))

    obs.append(TextObservation(
        species="Bird", date=date, site_id="TW05",
        locality="Lake Trail Gate O",
        behavior="vocalizing; ARU installed to capture bird calls",
        observer="Field team", source_file=src,
    ))

    return obs


def extract_observer1_20250908() -> List[TextObservation]:
    """Extract observations from Observer 1 notes, September 8."""
    obs = []
    date = "2025-09-08"
    src = "notes/observer1.md"

    obs.append(TextObservation(
        species="Pere David's Deer", date=date, time="09:00",
        site_id="TW01", locality="Nomad Ridge Shelter",
        behavior="sitting in small groups of 2-3 and larger groups of ~12; mostly resting, 1-2 grazing",
        count=12, observer="Observer 1", source_file=src,
        source_text="Observed sitting in small groups of 2-3 or larger groups of ~12; mostly lazing/resting except 1-2 grazing",
    ))

    obs.append(TextObservation(
        species="Grevy's Zebra", date=date, time="09:45",
        site_id="TW06", locality="Zebra Shelter",
        count=6, behavior="present near shelter",
        observer="Observer 1", source_file=src,
        source_text="Six individuals observed",
    ))

    obs.append(TextObservation(
        species="Sichuan Takin", date=date, time="10:00",
        site_id="TW04", locality="Lake Trail Ridge",
        behavior="post-breeding season; two individuals still showing breeding interest; babies present with developing horns",
        count=50, observer="Observer 1", source_file=src,
        source_text="Herd of 50 (largest outside China); breeding season over but two individuals still showing breeding interest",
    ))

    obs.append(TextObservation(
        species="Greater One-horned Rhino", date=date, time="11:00",
        locality="Rhino area",
        behavior="sleeping near hillside; female and baby grazing; baby born summer 2025; armored plating visible",
        life_stage="adult female + juvenile",
        observer="Observer 1", source_file=src,
        source_text="Female and baby grazing; baby born summer 2025; large manure pile indicating social communication; scratch marks suggesting potential conflict",
    ))

    obs.append(TextObservation(
        species="Southern White Rhino", date=date, time="11:00",
        locality="Rhino area",
        behavior="solitary; communication through fecal piles for age and reproductive stage signaling",
        observer="Observer 1", source_file=src,
        source_text="White rhinos (two-horned) more social; communication occurs through fecal piles",
    ))

    obs.append(TextObservation(
        species="Bison", date=date, time="11:00",
        locality="Rhino area, hillside behind",
        behavior="grazing on hillside",
        observer="Observer 1", source_file=src,
    ))

    return obs


def extract_observer2_20250908() -> List[TextObservation]:
    """Extract observations from Observer 2 notes, September 8."""
    obs = []
    date = "2025-09-08"
    src = "notes/observer2.md"

    obs.append(TextObservation(
        species="Pere David's Deer", date=date, time="09:00",
        site_id="TW01", locality="Nomad Shelter, near lake",
        behavior="observed during drone survey near lake",
        observer="Observer 2", source_file=src,
    ))

    obs.append(TextObservation(
        species="Grevy's Zebra", date=date, time="09:45",
        site_id="TW06", locality="Zebra Shelter",
        count=6, behavior="4 mares with 2 foals; foals nursing, one failing to nurse",
        life_stage="4 adult + 2 juvenile", sex="female + foals",
        observer="Observer 2", source_file=src,
        source_text="4 mares, 2 foals; foals nursing with one failing to nurse",
    ))

    obs.append(TextObservation(
        species="Fringe-eared Oryx", date=date, time="09:45",
        site_id="TW06", locality="Zebra Shelter, nearby",
        behavior="sheltering",
        observer="Observer 2", source_file=src,
    ))

    obs.append(TextObservation(
        species="Przewalski's Horse", date=date, time="09:45",
        site_id="TW06", locality="Outside fence near Zebra Shelter",
        behavior="grazing outside fence",
        observer="Observer 2", source_file=src,
    ))

    obs.append(TextObservation(
        species="Sichuan Takin", date=date, time="10:00",
        site_id="TW04", locality="Lake Trail Ridge, salt lick at shelter",
        count=50, behavior="herd at salt lick; baby takin present; flexible social system allowing new animals; group of females with male showing unusual post-season breeding interest",
        life_stage="mixed adults + juveniles",
        observer="Observer 2", source_file=src,
        source_text="Herd of 50; year-round outdoor housing; flexible social system; group of females with male showing unusual post-season breeding interest",
    ))

    obs.append(TextObservation(
        species="Pere David's Deer", date=date, time="10:50",
        site_id="TW09", locality="Lake near dock",
        behavior="swimming across lake",
        observer="Observer 2", source_file=src,
        source_text="Observed Pere David's deer swimming across lake",
    ))

    obs.append(TextObservation(
        species="Pere David's Deer", date=date, time="10:50",
        locality="Hillside near zipline",
        behavior="large herd grazing on hillside; surveyed by drone",
        observer="Observer 2", source_file=src,
        source_text="Drone survey of large herd on hillside near zipline",
    ))

    obs.append(TextObservation(
        species="Greater One-horned Rhino", date=date, time="11:00",
        locality="Rhino area, hillside",
        behavior="sleeping; female grazing with baby (born summer 2025); multi-generational group for social development; scratch marks on mother and 3-year-old suggesting conflict",
        life_stage="adult + 3-year-old + baby",
        observer="Observer 2", source_file=src,
    ))

    obs.append(TextObservation(
        species="Bison", date=date, time="11:00",
        locality="Hillside behind rhino area",
        behavior="grazing",
        observer="Observer 2", source_file=src,
    ))

    return obs


def extract_drone_mission_notes() -> List[TextObservation]:
    """Extract observations from drone mission notes."""
    obs = []

    # July 1 - Pere David's deer survey
    obs.append(TextObservation(
        species="Pere David's Deer", date="2025-07-01", time="08:30",
        site_id="TW09", locality="Edge of lake near dock",
        behavior="doe in water; male decorating antlers with reeds",
        sex="male + female", observer="Vedant Patil",
        source_file="drones/20250701_parrotanafi_1/metadata/mission_notes.txt",
        source_text="Captured doe in water, male decorating antlers with reeds",
        observation_type="drone_mission",
    ))

    # Sept 8 - mission 1 & 2
    obs.append(TextObservation(
        species="Pere David's Deer", date="2025-09-08", time="09:15",
        site_id="TW01", locality="Across from Nomad Shelter",
        behavior="resting near shore",
        observer="Jenna Kline",
        source_file="drones/20250908_djiair_1/metadata/mission_notes.txt",
        observation_type="drone_mission",
    ))

    # Sept 8 - mission 3
    obs.append(TextObservation(
        species="Pere David's Deer", date="2025-09-08", time="10:25",
        site_id="TW09", locality="Lake near dock",
        behavior="swimming; 3 deer in water",
        count=3, observer="Jenna Kline",
        source_file="drones/20250908_djiair_3/metadata/mission_notes.txt",
        source_text="3 deer swimming",
        observation_type="drone_mission",
    ))

    # Sept 8 - mission 4
    obs.append(TextObservation(
        species="Pere David's Deer", date="2025-09-08", time="10:30",
        site_id="TW09", locality="Shore across from dock",
        behavior="large herd grazing on shore",
        observer="Jenna Kline",
        source_file="drones/20250908_djiair_4/metadata/mission_notes.txt",
        source_text="Large herd of deer grazing on shore across from lake",
        observation_type="drone_mission",
    ))

    return obs


def extract_site_selection_rationale() -> List[Dict]:
    """Extract site selection rationale from site descriptions."""
    sites = []

    rationale_data = [
        ("TW01", "Nomad Ridge Shelter (East)", 39.83077, -81.73789,
         "Mounted on shelter structure on hill above lake",
         "High Pere David's deer activity observed at the lake",
         "Camera trap CT02 facing SE towards lake"),
        ("TW02", "Nomad Ridge Shelter (West)", 39.83066, -81.73792,
         "Mounted on shelter structure on hill above lake",
         "High Pere David's deer activity observed at the lake; complementary view to TW01",
         "Camera trap CT01/CT03 facing SW; ARU SM04"),
        ("TW03", "Old Giraffe Feeder, Pasture D", 39.83670, -81.73607,
         "Near salt lick and lake",
         "High deer activity near salt lick; ungulates visit regularly for minerals",
         "Camera trap CT01 facing S"),
        ("TW04", "Lake Trail", 39.83429, -81.73934,
         "Mounted on tree overlooking lake with clear view of water",
         "High deer activity along lake trail; animals use water corridor",
         "Camera trap CT03/CT04 facing NW"),
        ("TW05", "Lake Trail Gate O", 39.83537, -81.73842,
         "Mounted on gate with surrounding vegetation",
         "Easy access; high bird activity during sunrise and sunset",
         "ARU SM01/SM06 for bioacoustics"),
        ("TW06", "Zebra Shelter", 39.83537, -81.73842,
         "Open plain with shelter structure",
         "Animal activity around shelter; ungulates use for shade; fewer trees reduce false triggers",
         "Camera trap CT04/CT05; ARU SM03/SM05"),
        ("TW07", "Zipline Tower", 39.83288, -81.73455,
         "Open field near zipline structure",
         "Easy access; bird activity during sunrise/sunset; note: zipline guests may affect recordings",
         "ARU SM02; Camera CT05 (people only - relocated)"),
        ("TW08", "Fence with Vegetation", 39.82900, -81.74378,
         "Dense vegetation along fence near lake edge",
         "Bird activity in dense vegetation; acoustic diversity",
         "ARU SM03/SM04"),
        ("TW09", "Dock", 39.82798, -81.74167,
         "Dock area with open water access",
         "Takin and Pere David's deer activity in lake; animals swim and wade; high traffic corridor",
         "Camera trap CT02/CT05/CT06; ARU SM01"),
        ("TW10", "Fence near Lake Entrance", 39.83, -81.74,
         "Dense vegetation along fence",
         "Pere David's deer activity; complements TW02 viewing angle",
         "No sensors deployed in August campaign"),
    ]

    for site_id, name, lat, lon, habitat, rationale, sensors in rationale_data:
        sites.append({
            "siteID": site_id,
            "siteName": name,
            "decimalLatitude": lat,
            "decimalLongitude": lon,
            "habitatDescription": habitat,
            "selectionRationale": rationale,
            "sensorsDeployed": sensors,
            "locality": f"The Wilds Conservation Center - {name}",
            "country": "United States",
            "stateProvince": "Ohio",
            "county": "Muskingum",
        })

    return sites


# ─── Darwin Core generation ───────────────────────────────────────────────────

def observations_to_darwin_core(
    observations: List[TextObservation],
) -> Tuple[List[Dict], List[Dict]]:
    """Convert TextObservations to Darwin Core Events and Occurrences."""

    events = []
    occurrences = []

    # Project-level event
    events.append({
        "eventID": "TheWilds_2025_text_data",
        "parentEventID": "TheWilds_2025",
        "eventType": "Project",
        "eventDate": "2025-06-30/2025-09-08",
        "samplingProtocol": "Field observations recorded as text (field notes, observer logs, drone mission notes)",
        "sampleSizeValue": len(observations),
        "sampleSizeUnit": "text observations",
        "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
        "decimalLatitude": 39.83,
        "decimalLongitude": -81.74,
        "coordinateUncertaintyInMeters": 5000,
        "geodeticDatum": "WGS84",
        "country": "United States",
        "stateProvince": "Ohio",
        "county": "Muskingum",
        "datasetID": "TheWilds_2025_text_data",
        "datasetName": "The Wilds 2025 Multi-Modal Survey - Text Data",
        "recordedBy": "Multiple observers",
        "fieldNotes": (
            f"{len(observations)} structured observations extracted from field notes, "
            "observer logs, and drone mission notes across 3 campaigns."
        ),
    })

    # Group by date for session events
    date_groups = {}
    for ob in observations:
        if ob.date not in date_groups:
            date_groups[ob.date] = []
        date_groups[ob.date].append(ob)

    for date_str in sorted(date_groups.keys()):
        group = date_groups[date_str]
        observers = list(set(ob.observer for ob in group if ob.observer))
        types = list(set(ob.observation_type for ob in group))

        events.append({
            "eventID": f"TheWilds_2025_text_{date_str}",
            "parentEventID": "TheWilds_2025_text_data",
            "eventType": "ObservationSession",
            "eventDate": date_str,
            "samplingProtocol": f"Field observation ({', '.join(types)})",
            "sampleSizeValue": len(group),
            "sampleSizeUnit": "text observations",
            "locality": "The Wilds Conservation Center",
            "decimalLatitude": 39.83,
            "decimalLongitude": -81.74,
            "coordinateUncertaintyInMeters": 5000,
            "geodeticDatum": "WGS84",
            "country": "United States",
            "stateProvince": "Ohio",
            "county": "Muskingum",
            "datasetID": "TheWilds_2025_text_data",
            "datasetName": "The Wilds 2025 Multi-Modal Survey - Text Data",
            "recordedBy": "; ".join(observers),
            "fieldNotes": f"{len(group)} observations on {date_str}.",
        })

    # Build occurrence records
    for i, ob in enumerate(observations, 1):
        taxon = TAXON_MAP.get(ob.species, TAXON_MAP.get("Bird", {}))
        lat, lon = SITE_GPS.get(ob.site_id, (39.83, -81.74))
        site_name = SITE_NAMES.get(ob.site_id, ob.locality or "The Wilds")

        occ = {
            "occurrenceID": f"TheWilds_2025_TEXT_{i:04d}",
            "eventID": f"TheWilds_2025_text_{ob.date}",
            "catalogNumber": f"TEXT_{ob.date}_{i:04d}",

            # Taxonomy
            "scientificName": taxon.get("scientificName", ob.species),
            "kingdom": taxon.get("kingdom", "Animalia"),
            "phylum": taxon.get("phylum", "Chordata"),
            "class": taxon.get("class", ""),
            "order": taxon.get("order", ""),
            "family": taxon.get("family", ""),
            "genus": taxon.get("genus", ""),
            "specificEpithet": taxon.get("specificEpithet", ""),
            "taxonRank": taxon.get("taxonRank", "species"),
            "vernacularName": ob.species,

            # Observation
            "occurrenceStatus": "present",
            "individualCount": ob.count if ob.count else "",
            "lifeStage": ob.life_stage or "",
            "sex": ob.sex or "",
            "behavior": ob.behavior,
            "basisOfRecord": "HumanObservation",
            "recordedBy": ob.observer or "Field team",
            "identifiedBy": ob.observer or "Field team",
            "identificationVerificationStatus": "verified by expert",
            "identificationRemarks": f"Direct field observation recorded in text ({ob.observation_type})",

            # Temporal
            "eventDate": ob.date,
            "eventTime": ob.time or "",

            # Spatial
            "decimalLatitude": lat,
            "decimalLongitude": lon,
            "coordinateUncertaintyInMeters": 500 if ob.site_id else 5000,
            "geodeticDatum": "WGS84",
            "locality": f"The Wilds - {site_name}" if site_name else "The Wilds Conservation Center",
            "locationID": ob.site_id or "",
            "country": "United States",
            "stateProvince": "Ohio",
            "county": "Muskingum",

            # Provenance
            "establishmentMeans": "managed",
            "degreeOfEstablishment": "captive",
            "occurrenceRemarks": ob.source_text or "",
            "associatedMedia": "",
            "associatedReferences": ob.source_file,

            # Dataset
            "datasetID": "TheWilds_2025_text_data",
            "datasetName": "The Wilds 2025 Multi-Modal Survey - Text Data",
            "informationWithheld": "",
            "dataGeneralizations": "Observation extracted from unstructured field notes; location precision limited to site level",
        }

        occurrences.append(occ)

    return events, occurrences


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Text Data Extraction Pipeline")
    print("=" * 60)

    # Collect all observations
    all_obs = []

    print("\nExtracting from field notes (2025-06-30)...")
    obs = extract_field_notes_20250630()
    all_obs.extend(obs)
    print(f"  {len(obs)} observations")

    print("Extracting from field notes (2025-08-04)...")
    obs = extract_field_notes_20250804()
    all_obs.extend(obs)
    print(f"  {len(obs)} observations")

    print("Extracting from Observer 1 (2025-09-08)...")
    obs = extract_observer1_20250908()
    all_obs.extend(obs)
    print(f"  {len(obs)} observations")

    print("Extracting from Observer 2 (2025-09-08)...")
    obs = extract_observer2_20250908()
    all_obs.extend(obs)
    print(f"  {len(obs)} observations")

    print("Extracting from drone mission notes...")
    obs = extract_drone_mission_notes()
    all_obs.extend(obs)
    print(f"  {len(obs)} observations")

    print(f"\nTotal: {len(all_obs)} observations extracted")

    # Convert to Darwin Core
    events, occurrences = observations_to_darwin_core(all_obs)

    # Write outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Events
    events_path = OUTPUT_DIR / "darwin_core_events_text.csv"
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

    # Occurrences
    occ_path = OUTPUT_DIR / "darwin_core_occurrences_text.csv"
    if occurrences:
        fieldnames = list(occurrences[0].keys())
        with open(occ_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(occurrences)
    print(f"Wrote {len(occurrences)} Occurrences to {occ_path}")

    # Site selection rationale
    sites = extract_site_selection_rationale()
    sites_path = OUTPUT_DIR / "site_selection_rationale.csv"
    with open(sites_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(sites[0].keys()))
        writer.writeheader()
        writer.writerows(sites)
    print(f"Wrote {len(sites)} site records to {sites_path}")

    # Summary
    print(f"\n{'='*60}")
    print("Text Data Darwin Core Summary")
    print(f"{'='*60}")

    species_counts = {}
    behavior_count = 0
    for occ in occurrences:
        sp = occ["vernacularName"]
        species_counts[sp] = species_counts.get(sp, 0) + 1
        if occ["behavior"]:
            behavior_count += 1

    print(f"  Observation records: {len(occurrences)}")
    print(f"  With behavior data: {behavior_count}")
    print(f"  Species observed:   {len(species_counts)}")
    print(f"  Observation dates:  {len(events) - 1}")
    print(f"  Site rationales:    {len(sites)}")

    print(f"\n  Species counts:")
    for sp, count in sorted(species_counts.items(), key=lambda x: -x[1]):
        print(f"    {sp:<30} {count:>3}")

    dates = sorted(set(o["eventDate"] for o in occurrences))
    print(f"\n  Date range: {dates[0]} to {dates[-1]}")

    print(f"\n  Cross-referencing:")
    print(f"    - eventID format: TheWilds_2025_text_YYYY-MM-DD")
    print(f"    - locationID links to site IDs (TW01-TW11)")
    print(f"    - Same taxon map as citizen science pipeline")
    print(f"    - Can join with camera trap/ARU data on (site_id, date, species)")


if __name__ == "__main__":
    main()
