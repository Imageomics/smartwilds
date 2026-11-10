# Multi-Modal Darwin Core Architecture for The Wilds 2025

Complete guide to the hierarchical Event/Occurrence structure supporting camera traps, bioacoustics, drones, and citizen science.

## Table of Contents

1. [Overview](#overview)
2. [4-Level Event Hierarchy](#4-level-event-hierarchy)
3. [Event Structure by Modality](#event-structure-by-modality)
4. [Occurrence Linking](#occurrence-linking)
5. [Platform Specifications](#platform-specifications)
6. [Darwin Core Fields](#darwin-core-fields)
7. [Query Examples](#query-examples)
8. [Data Flow](#data-flow)

---

## Overview

The Wilds 2025 uses a **4-level hierarchical Event structure** to organize biodiversity data across four distinct sampling modalities:

```
STUDY LEVEL
    "The Wilds 2025 Biodiversity Survey"
    ↓
MODALITY LEVEL (one per modality)
    "Camera Trap Survey" / "Acoustic Monitoring" / "Drone Survey" / "Citizen Science"
    ↓
DEPLOYMENT LEVEL (one per physical installation)
    "TW01-CT02 deployment Aug 4-11" / "TW02-SM04 session Aug 4-28" / "Flight 20250818_Parrot_01" / "Submission #1"
    ↓
OCCURRENCE LEVEL (multiple per deployment)
    Species detections/observations with GPS and timestamp
```

**Why this structure?**

- **Study Level**: Unifies all data under one survey identifier; enables cross-modality queries
- **Modality Level**: Groups deployments by data collection type; supports modality-specific analyses
- **Deployment Level**: Individual sampling sessions with fixed location/time; clear provenance
- **Occurrence Level**: Individual observations linked to specific deployments; maintains data integrity

---

## 4-Level Event Hierarchy

### Level 1: Study-Level Event

**One per survey.**

```csv
eventID,eventDate,eventEndDate,decimalLatitude,decimalLongitude,samplingProtocol,coordinateUncertaintyInMeters,datasetID,datasetName
TheWilds_2025,2025-06-30,2025-08-28,39.50,-81.44,"Multi-modal biodiversity survey (camera traps, bioacoustics, drones, citizen science)",1000,TheWilds_2025,"The Wilds 2025 Biodiversity Survey"
```

**Key fields:**
- **eventID**: `TheWilds_2025` (globally unique study identifier)
- **eventDate/eventEndDate**: Span of all data collection (June 30 - Aug 28)
- **decimalLatitude/Longitude**: Study area center (The Wilds Conservation Center)
- **coordinateUncertaintyInMeters**: 1000 m (covers entire study area)
- **samplingProtocol**: "Multi-modal biodiversity survey..." (describes all modalities)

---

### Level 2: Modality-Level Events

**One per modality type. Parent = Study event.**

```csv
eventID,parentEventID,eventDate,eventEndDate,samplingProtocol,eventType
TheWilds_2025_camera_traps,TheWilds_2025,2025-06-30,2025-08-28,"Passive infrared camera trap survey (PIR-triggered + hourly timelapse)","ModularSurvey"
TheWilds_2025_bioacoustics,TheWilds_2025,2025-08-04,2025-08-28,"Continuous acoustic monitoring via stationary Song Meter recorders","ModularSurvey"
TheWilds_2025_drones,TheWilds_2025,2025-08-11,2025-08-25,"Periodic aerial video surveys via DJI and Parrot drones","ModularSurvey"
TheWilds_2025_citizen_science,TheWilds_2025,2025-08-04,2025-08-28,"Opportunistic mobile phone photography from park visitors","ModularSurvey"
```

**Key fields:**
- **eventID**: `TheWilds_2025_[modality]` (unique modality identifier)
- **parentEventID**: `TheWilds_2025` (links to study event)
- **samplingProtocol**: Modality-specific description
- **eventType**: "ModularSurvey" (DWC extension indicating sub-survey)

**Custom fields** (in eventRemarks):
- Total deployments for this modality
- Total data volume
- Detection automation status

---

### Level 3: Deployment/Session Events

**One per physical installation. Parent = Modality event.**

#### Camera Trap Deployments

```csv
eventID,parentEventID,samplingProtocol,decimalLatitude,decimalLongitude,eventDate,eventEndDate,platformID,recordedBy,samplingEffort
TW01-CT02_20250804_20250811,TheWilds_2025_camera_traps,"Passive infrared camera trap (PIR trigger)",39.498459,-81.442737,2025-08-04,2025-08-11,"Garde_Pro_T5NG","Automated camera trap","7 days, continuous 24/7 monitoring"
TW02-CT01_20250804_20250828,TheWilds_2025_camera_traps,"Passive infrared camera trap (PIR trigger)",39.498394,-81.442751,2025-08-04,2025-08-28,"Garde_Pro_T5NG","Automated camera trap","24 days, continuous 24/7 monitoring"
```

**Characteristics:**
- **decimalLatitude/Longitude**: **Camera location** (fixed GPS)
- **coordinateUncertaintyInMeters**: 5 m (GPS placement accuracy)
- **platformID**: Camera model identifier
- **samplingEffort**: Duration + "24/7" note

#### Bioacoustic Recording Sessions

```csv
eventID,parentEventID,samplingProtocol,decimalLatitude,decimalLongitude,eventDate,eventEndDate,platformID,samplingEffort
TW02-SM04_20250804_20250828,TheWilds_2025_bioacoustics,"Continuous acoustic monitoring (5 min recording every hour)",39.82957,-81.73295,2025-08-04,2025-08-28,"Song_Meter_4_TW02SM04","24 days, 5 min recordings per hour (120 min/day)"
TW05-SM06_20250804_20250828,TheWilds_2025_bioacoustics,"Continuous acoustic monitoring (sunrise to sunset)",39.82866,-81.73758,2025-08-04,2025-08-28,"Song_Meter_4_TW05SM06","24 days, sunrise-sunset recording"
```

**Characteristics:**
- **decimalLatitude/Longitude**: **Recorder location** (fixed GPS)
- **coordinateUncertaintyInMeters**: 5 m (recorder placement accuracy)
- **platformID**: "Song_Meter_4_[site]" (specific recorder instance)
- **samplingEffort**: Recording schedule (e.g., "5 min per hour")

#### Drone Flight Missions

```csv
eventID,parentEventID,samplingProtocol,decimalLatitude,decimalLongitude,eventDate,eventEndDate,eventTime,platformID,samplingEffort,fieldNotes
20250818_Parrot_01_flight,TheWilds_2025_drones,"Aerial video survey",39.834171,-81.737820,2025-08-18,2025-08-18,"14:20:00","Parrot_Anafi_4K_PI040416BA8H083200","1 flight, 3 videos, ~15 min flight time","Flight telemetry available. GPS/altitude recorded at ~10Hz."
DJI_20250811_01_flight,TheWilds_2025_drones,"Aerial video survey",39.834171,-81.737820,2025-08-11,2025-08-11,"10:00:00","DJI_Mavic","1 flight, 2 videos","GPS telemetry: 10Hz update rate. Battery tracking included."
```

**Characteristics:**
- **decimalLatitude/Longitude**: Flight start location (or study area center if variable)
- **coordinateUncertaintyInMeters**: 100 m (flight path varied; not fixed location)
- **eventTime**: Flight time/start time
- **platformID**: Specific aircraft (with serial number if available)
- **fieldNotes**: Links to telemetry data availability

#### Citizen Science Submissions

```csv
eventID,parentEventID,samplingProtocol,eventDate,eventTime,decimalLatitude,decimalLongitude,locationName,platformID,recordedBy,samplingEffort
TheWilds_2025_citizen_science_submission_001,TheWilds_2025_citizen_science,"Opportunistic mobile phone photography",2025-08-10,14:30:00,39.50,-81.44,"TheWilds observation area (location TBD)","citizen_smartphone_iPhone_12","John Visitor","Single submission, 5 photos"
TheWilds_2025_citizen_science_submission_002,TheWilds_2025_citizen_science,"Opportunistic mobile phone photography",,,"","","citizen_smartphone_Android","Jane Visitor","Single submission, 3 photos (location metadata missing)"
```

**Characteristics:**
- **decimalLatitude/Longitude**: May be NULL if location not captured
- **locationName**: Text description if coordinates missing
- **platformID**: "citizen_smartphone_[device_type]"
- **recordedBy**: Submitter name (from citizen_science_index.csv)
- **samplingEffort**: "Single submission, X photos"

---

### Level 4: Occurrence Records

**Multiple per deployment event. Foreign key = eventID.**

#### Camera Trap Occurrence

```csv
occurrenceID,eventID,scientificName,commonName,basisOfRecord,identificationVerificationStatus,decimalLatitude,decimalLongitude,coordinateUncertaintyMeters,eventTime,individualCount,associatedMedia,identificationRemarks
TW01-CT02_20250804_120000_001,TW01-CT02_20250804_20250811,"Odocoileus virginianus","White-tailed Deer","MachineObservation","unverified",39.498491,-81.442651,50,2025-08-04T12:00:00Z,1,/path/to/TW01-CT02/IMG_001.JPG,"YOLO: 0.95, BioCLIP: 0.92, Distance: 8.5m, Angle: 45°"
TW01-CT02_20250804_120530_002,TW01-CT02_20250804_20250811,"Aves (unidentified)","Bird","MachineObservation","unverified",39.498502,-81.442618,50,2025-08-04T12:05:30Z,1,/path/to/TW01-CT02/IMG_002.JPG,"YOLO: 0.78, BioCLIP: 0.65"
```

**Key fields:**
- **occurrenceID**: `[deploymentEventID]_[timestamp]_[sequence]` (unique)
- **eventID**: `TW01-CT02_20250804_20250811` (foreign key to deployment event)
- **decimalLatitude/Longitude**: **Animal location** (GPS projected from depth estimation)
  - If depth estimation successful: animal location
  - If depth estimation failed: camera location (fallback)
- **coordinateUncertaintyMeters**: 50 m (depth estimation uncertainty)
- **basisOfRecord**: "MachineObservation" (automated detection)
- **identificationVerificationStatus**: "unverified" (transparency about automation)
- **associatedMedia**: Path to original image
- **identificationRemarks**: Confidence scores (YOLO + BioCLIP)

#### Bioacoustic Occurrence

```csv
occurrenceID,eventID,scientificName,commonName,basisOfRecord,identificationVerificationStatus,eventTime,frequency_hz_start,frequency_hz_end,temporal_location_sec,individualCount,associatedMedia,identificationRemarks
TW02-SM04_20250804_050000_001,TW02-SM04_20250804_20250828,"Turdus migratorius","American Robin","MachineObservation","unverified",2025-08-04T05:00:00Z,1500,3000,5.2,1,/path/to/TW02-SM04/SM04_20250804_050000.wav,"BirdCLIP: 0.89, Call type: territorial"
TW02-SM04_20250804_060000_001,TW02-SM04_20250804_20250828,"Passeriformes","Songbirds (undetermined)","MachineObservation","unverified",2025-08-04T06:00:00Z,2000,4500,12.8,3,/path/to/TW02-SM04/SM04_20250804_060000.wav,"BirdCLIP: 0.72"
```

**Key fields:**
- **eventID**: `TW02-SM04_20250804_20250828` (foreign key to recording session)
- **frequency_hz_start/end**: Detection frequency range (custom Darwin Core extension)
- **temporal_location_sec**: Seconds into the WAV file
- **basisOfRecord**: "MachineObservation" (automated BirdCLIP detection)
- **identificationVerificationStatus**: "unverified"
- **associatedMedia**: Path to WAV file

#### Drone Occurrence

```csv
occurrenceID,eventID,scientificName,commonName,basisOfRecord,identificationVerificationStatus,eventTime,decimalLatitude,decimalLongitude,coordinateUncertaintyMeters,behaviour,identificationRemarks,annotationStatus
20250818_Parrot_01_frame_456_001,20250818_Parrot_01_flight,"Odocoileus virginianus","White-tailed Deer","HumanObservation","verified",2025-08-18T14:23:15Z,39.834301,-81.737542,50,"walking","YOLOv11: 0.88, Manual review: CONFIRMED - single adult deer","manual_reviewed"
20250818_Parrot_01_frame_891_001,20250818_Parrot_01_flight,"Equus caballus","Domestic Horse","HumanObservation","verified",2025-08-18T14:24:32Z,39.834156,-81.737891,100,"grazing","YOLOv11: 0.82, Manual review: CONFIRMED - 2 horses in herd","manual_reviewed"
```

**Key fields:**
- **eventID**: `20250818_Parrot_01_flight` (foreign key to flight mission)
- **basisOfRecord**: "HumanObservation" (manual annotation after automated detection)
- **identificationVerificationStatus**: "verified" (human curator confirmed)
- **decimalLatitude/Longitude**: GPS interpolated to frame timestamp from flight telemetry
- **coordinateUncertaintyMeters**: 50-100 m (flight altitude varies)
- **behaviour**: From annotator notes
- **annotationStatus**: "manual_reviewed" (indicates human curation complete)

#### Citizen Science Occurrence

```csv
occurrenceID,eventID,scientificName,commonName,basisOfRecord,identificationVerificationStatus,eventDate,eventTime,decimalLatitude,decimalLongitude,locationName,individualCount,behaviour,associatedMedia,identificationRemarks
TheWilds_2025_citizen_science_submission_001_001,TheWilds_2025_citizen_science_submission_001,"Odocoileus virginianus","White-tailed Deer","HumanObservation","verified",2025-08-10,14:30:00,39.501,-81.441,"Near north shelter entrance",1,"bedding","citizen_science/UUID_1_105_c.jpeg","Submitter note: Adult doe resting near shelter. GPS approximated from location description."
TheWilds_2025_citizen_science_submission_003_001,TheWilds_2025_citizen_science_submission_003,"Rupicapra rupicapra","Takin","HumanObservation","verified",2025-08-12,16:15:00,39.502,-81.443,"Near takin exhibit",3,"standing","citizen_science/UUID_3_201_c.jpg","Submitter photo: 3 takin standing together. Time/location from submission."
```

**Key fields:**
- **eventID**: `TheWilds_2025_citizen_science_submission_001` (foreign key to submission)
- **basisOfRecord**: "HumanObservation" (human-submitted observation)
- **identificationVerificationStatus**: "verified" (curator confirmed valid species ID)
- **decimalLatitude/Longitude**: Geocoded from location description or submission location
- **locationName**: Text location description from submitter
- **individualCount**: From submitter observation
- **behaviour**: Observed behavior
- **associatedMedia**: Path to submitted photo/video file

---

## Event Structure by Modality

### Camera Traps: Event Linking

```
TheWilds_2025 (Study)
    ↓
TheWilds_2025_camera_traps (Modality)
    ├─→ TW01-CT02_20250804_20250811 (Deployment)
    │    └─→ [100+ Occurrences] (Individual detections)
    │
    ├─→ TW02-CT01_20250804_20250828 (Deployment)
    │    └─→ [800+ Occurrences]
    │
    └─→ [11 more deployments]
         └─→ [~230,000 total Occurrences]
```

### Bioacoustics: Event Linking

```
TheWilds_2025 (Study)
    ↓
TheWilds_2025_bioacoustics (Modality)
    ├─→ TW02-SM04_20250804_20250828 (Recording Session)
    │    └─→ [~5000 Occurrences] (Species call detections)
    │
    ├─→ TW05-SM06_20250804_20250828 (Recording Session)
    │    └─→ [~2000 Occurrences]
    │
    └─→ [4 more sites]
         └─→ [~40,000+ total Occurrences]
```

### Drones: Event Linking

```
TheWilds_2025 (Study)
    ↓
TheWilds_2025_drones (Modality)
    ├─→ 20250811_DJI_01_flight (Flight Mission)
    │    └─→ [~500 Occurrences] (After frame extraction + detection)
    │
    ├─→ 20250818_Parrot_01_flight (Flight Mission)
    │    └─→ [~800 Occurrences]
    │
    └─→ [3 more successful flights]
         └─→ [~3000+ total Occurrences] (Awaiting manual annotation)
```

### Citizen Science: Event Linking

```
TheWilds_2025 (Study)
    ↓
TheWilds_2025_citizen_science (Modality)
    ├─→ TheWilds_2025_citizen_science_submission_001 (Submission)
    │    └─→ [1-5 Occurrences] (Species observations from submission)
    │
    ├─→ TheWilds_2025_citizen_science_submission_002 (Submission)
    │    └─→ [2-3 Occurrences]
    │
    └─→ [~991 submissions total]
         └─→ [~1500-2000 total Occurrences] (Awaiting curation)
```

---

## Occurrence Linking

All Occurrences link to parent deployment Events via `eventID` foreign key.

```
OCCURRENCE
├─ occurrenceID: TW02-CT01_20250804_120000_001
├─ eventID: TW02-CT01_20250804_20250828  ← Foreign key
├─ scientificName: Odocoileus virginianus
├─ decimalLatitude: 39.498491             ← ANIMAL location (projected)
├─ decimalLongitude: -81.442651
├─ coordinateUncertaintyMeters: 50
└─ associatedMedia: /path/to/image.JPG

EVENT (parent)
├─ eventID: TW02-CT01_20250804_20250828
├─ parentEventID: TheWilds_2025_camera_traps
├─ decimalLatitude: 39.498394              ← CAMERA location (fixed)
├─ decimalLongitude: -81.442751
├─ coordinateUncertaintyMeters: 5
└─ samplingProtocol: "Passive infrared camera trap..."
```

**Key principle:**
- **Event**: Survey session metadata (FIXED location + temporal extent)
- **Occurrence**: Observation data (VARIABLE location from detection)

---

## Platform Specifications

Each deployment/session event has a `platformID` linking to platform specification details.

### Camera Platforms

```json
{
  "platform_id": "Garde_Pro_T5NG",
  "platform_type": "camera_trap",
  "manufacturer": "GardePro",
  "model": "Garde Pro T5NG",
  "sensors": {
    "primary_camera": {
      "resolution_mp": 4,
      "field_of_view_degrees": 52,
      "trigger": "PIR (Passive Infrared)"
    }
  },
  "deployments": ["TW01-CT02", "TW02-CT01", "TW09-CT02"],
  "reference": "platform_specifications_all_modalities.json"
}
```

### Bioacoustic Platforms

```json
{
  "platform_id": "Song_Meter_4_TW02SM04",
  "platform_type": "bioacoustics",
  "manufacturer": "Wildlife Acoustics",
  "model": "Song Meter 4",
  "sensors": {
    "microphone": {
      "type": "Microphone array",
      "frequency_response_hz": [200, 12000],
      "sample_rate_hz": 48000
    }
  },
  "deployment_schedule": "5 min every hour",
  "reference": "platform_specifications_all_modalities.json"
}
```

### Drone Platforms

```json
{
  "platform_id": "Parrot_Anafi_4K_PI040416BA8H083200",
  "platform_type": "drone",
  "manufacturer": "Parrot",
  "model": "Anafi 4K",
  "aircraft_sn": "PI040416BA8H083200",
  "sensors": {
    "camera": {
      "resolution_4k": true,
      "frame_rate_fps": 30
    },
    "gps": {
      "accuracy_m": 2,
      "update_rate_hz": 10
    }
  },
  "flights": ["20250818_Parrot_01", "20250818_Parrot_02", "20250825_Parrot_01"],
  "reference": "platform_specifications_all_modalities.json"
}
```

---

## Darwin Core Fields

### Events CSV (All Modalities)

Required columns:

```
eventID
parentEventID (if Level 2, 3, 4)
eventType (Study, ModularSurvey, DeploymentSession)
eventDate
eventEndDate
eventTime (optional)
samplingProtocol
samplingEffort
decimalLatitude
decimalLongitude
coordinateUncertaintyInMeters
geodeticDatum
locality
habitat
platformID (deployment/session level)
recordedBy
fieldNotes
datasetID
datasetName
```

### Occurrences CSV (All Modalities)

Required columns:

```
occurrenceID
eventID (foreign key)
scientificName
scientificNameAuthority
taxonRank
vernacularName
kingdom
phylum
class
order
family
genus
species
occurrenceStatus
basisOfRecord (MachineObservation or HumanObservation)
recordedBy
identificationVerificationStatus
individualCount
lifeStage
sex
behaviour
eventDate
eventTime
decimalLatitude
decimalLongitude
coordinateUncertaintyMeters
geodeticDatum
spatialReferenceSystem
associatedMedia
associatedOccurrences
identificationRemarks
datasetID
datasetName
```

**Modality-specific columns** (optional extensions):

```
# For bioacoustics:
frequency_hz_start, frequency_hz_end, temporal_location_sec

# For drones:
annotationStatus, annotator_id, manual_review_date

# For citizen science:
submitter_name, submission_date, location_description
```

---

## Query Examples

### Query 1: All Deer Observations (Cross-Modality)

```sql
SELECT
  occurrenceID,
  eventID,
  basisOfRecord,
  eventDate,
  decimalLatitude,
  decimalLongitude,
  associatedMedia
FROM darwin_core_occurrences_multi_modal
WHERE scientificName='Odocoileus virginianus'
ORDER BY eventDate;
```

Returns deer from:
- Camera traps (automated detections)
- Drones (manual annotations)
- Citizen science (human observations)

### Query 2: Detection Confidence Comparison

```sql
SELECT
  modality := CASE
    WHEN eventID LIKE 'TW%-CT%' THEN 'camera_trap'
    WHEN eventID LIKE 'TW%-SM%' THEN 'bioacoustics'
    WHEN eventID LIKE '%_flight' THEN 'drone'
    ELSE 'citizen_science'
  END,
  COUNT(*) as occurrence_count,
  basisOfRecord,
  identificationVerificationStatus
FROM darwin_core_occurrences_multi_modal
GROUP BY modality, basisOfRecord, identificationVerificationStatus;
```

**Output:**
```
modality         | occurrence_count | basisOfRecord | identificationVerificationStatus
camera_trap      | 230000           | MachineObservation | unverified
bioacoustics     | 40000            | MachineObservation | unverified
drone            | 3000             | HumanObservation   | verified
citizen_science  | 1800             | HumanObservation   | verified
```

### Query 3: Temporal Coverage

```sql
SELECT
  parentEventID as modality,
  COUNT(DISTINCT eventID) as deployment_count,
  MIN(eventDate) as earliest,
  MAX(eventEndDate) as latest,
  SUM(DATEDIFF(eventEndDate, eventDate)) as total_deployment_days
FROM darwin_core_events_multi_modal
WHERE parentEventID LIKE 'TheWilds_2025_%'
GROUP BY parentEventID;
```

**Output:**
```
modality                    | deployment_count | earliest   | latest     | total_deployment_days
TheWilds_2025_camera_traps  | 13               | 2025-06-30 | 2025-08-28 | 169
TheWilds_2025_bioacoustics  | 6                | 2025-08-04 | 2025-08-28 | 144
TheWilds_2025_drones        | 8                | 2025-08-11 | 2025-08-25 | 8
TheWilds_2025_citizen_science | 991            | 2025-08-04 | 2025-08-28 | variable
```

---

## Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│ RAW DATA (4 Modalities)                                      │
└──────────────────────────────────────────────────────────────┘
    ↓         ↓            ↓               ↓
    │         │            │               │
    ▼         ▼            ▼               ▼
┌────────┐ ┌─────────┐ ┌────────┐ ┌──────────────┐
│ Camera │ │Acoustic │ │ Drone  │ │   Citizen    │
│ Images │ │   WAV   │ │ Videos │ │   Science    │
│ (243k) │ │ (2.1k)  │ │ (13)   │ │   (991)      │
└────────┘ └─────────┘ └────────┘ └──────────────┘
    │         │            │               │
    │ YOLO +  │ BirdCLIP   │ YOLOv11       │ Manual
    │ BioCLIP │ automated  │ + manual      │ curation
    │         │ detection  │ review        │
    ▼         ▼            ▼               ▼
┌────────────────────────────────────────────────────┐
│ DETECTIONS (Intermediate CSVs, per modality)       │
│  - camera_detections_*.csv (230k rows)            │
│  - bioacoustics_detections_*.csv (40k rows)       │
│  - drone_detections_*.csv (3k rows, pending)      │
│  - citizen_science_obs.csv (1.8k rows, pending)   │
└────────────────────────────────────────────────────┘
    │
    │ merge_all_modality_detections.py
    │ (consolidate + add modality_type column)
    ▼
┌────────────────────────────────────────────────────┐
│ UNIFIED DETECTIONS CSV                             │
│  - occurrences_all_modalities.csv (275k rows)     │
│  - modality_type, eventID, occurrence fields       │
└────────────────────────────────────────────────────┘
    │
    │ generate_darwin_core_multi_modal.py
    │ (create hierarchical Events + link Occurrences)
    ▼
┌────────────────────────────────────────────────────┐
│ DARWIN CORE METADATA (Final Output)                │
│  - darwin_core_events_multi_modal.csv              │
│    (1 Study + 4 Modality + 28 Deployment events) │
│  - darwin_core_occurrences_multi_modal.csv         │
│    (275k observations linked via eventID)          │
│  - platform_specifications_all_modalities.json     │
└────────────────────────────────────────────────────┘
    │
    │ FAIR² Compliant Multi-Modal Dataset
    │ Ready for publication (GBIF + Zenodo)
    ▼
```

---

## Related Documentation

- **multi_modal_config.json** - Configuration for all 4 modalities
- **platform_specifications_all_modalities.json** - Hardware/sensor descriptions
- **MODALITY_SPECIFIC.md** files:
  - CAMERA_TRAPS.md
  - BIOACOUSTICS.md
  - DRONES.md
  - CITIZEN_SCIENCE.md

---

## References

- Darwin Core Standard: https://dwc.tdwg.org/
- FAIR² Drones Standard: [Cite standard]
- Event Hierarchy: https://dwc.tdwg.org/terms/#Event
