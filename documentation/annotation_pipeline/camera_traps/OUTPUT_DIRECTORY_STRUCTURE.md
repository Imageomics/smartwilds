# Output Directory Structure for Camera Trap Processing

Organized directory layout for storing annotated images and Darwin Core metadata files.

## Recommended Directory Structure

```
/fs/ess/PAS2136/TheWilds2025/processing_output/
│
├── annotated_images/              # Detection visualizations (from camera_trap_detections.py)
│   ├── 20250630_20250703/
│   │   ├── TW01-CT02/
│   │   │   ├── IMG_001.jpg        # Original image
│   │   │   ├── IMG_001_annotated.jpg
│   │   │   └── ...
│   │   ├── TW02-CT03/
│   │   └── ...
│   │
│   └── 20250804_20250828/
│       ├── TW01-CT02/
│       ├── TW02-CT01/
│       ├── TW04-CT03/
│       ├── TW06-CT04/
│       ├── TW06-CT05/
│       ├── TW07-CT05/
│       ├── TW09_CT02/
│       ├── TW09-CT05/
│       └── TW11-CT06/
│
├── darwin_core_metadata/          # Consolidated Darwin Core files (per-campaign)
│   ├── 20250630_20250703/
│   │   ├── darwin_core_events.csv
│   │   ├── darwin_core_occurrences.csv
│   │   ├── platform_specifications.json
│   │   └── processing_report.json
│   │
│   └── 20250804_20250828/
│       ├── darwin_core_events.csv
│       ├── darwin_core_occurrences.csv
│       ├── platform_specifications.json
│       └── processing_report.json
│
├── intermediate_processing/       # Intermediate files (optional, for quality assurance)
│   ├── 20250630_20250703/
│   │   ├── TW01-CT02/
│   │   │   ├── index.csv
│   │   │   ├── events_validated.csv
│   │   │   └── detections.csv (raw YOLO output)
│   │   └── ...
│   │
│   └── 20250804_20250828/
│       └── ...
│
├── validation_reports/            # Quality checks and validation logs
│   ├── timestamp_validation_report.csv
│   ├── detection_quality_metrics.json
│   ├── missing_coordinates_report.csv
│   └── processing_errors.log
│
└── metadata.json                  # Master metadata file
```

## Directory Setup Guide

### 1. Create Base Structure

```bash
# Create main output directory
mkdir -p /fs/ess/PAS2136/TheWilds2025/processing_output

# Create campaign subdirectories
mkdir -p /fs/ess/PAS2136/TheWilds2025/processing_output/annotated_images/{20250630_20250703,20250804_20250828}
mkdir -p /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata/{20250630_20250703,20250804_20250828}
mkdir -p /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/{20250630_20250703,20250804_20250828}
mkdir -p /fs/ess/PAS2136/TheWilds2025/processing_output/validation_reports
```

### 2. Create Per-Camera Directories

For each camera deployment, create subdirectories under both campaigns:

```bash
# June-July campaign cameras
for cam in TW01-CT02 TW02-CT03 TW03-CT01 TW04-CT04; do
    mkdir -p /fs/ess/PAS2136/TheWilds2025/processing_output/annotated_images/20250630_20250703/$cam
    mkdir -p /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250630_20250703/$cam
done

# August campaign cameras
for cam in TW01-CT02 TW02-CT01 TW04-CT03 TW06-CT04 TW06-CT05 TW07-CT05 TW09_CT02 TW09-CT05 TW11-CT06; do
    mkdir -p /fs/ess/PAS2136/TheWilds2025/processing_output/annotated_images/20250804_20250828/$cam
    mkdir -p /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828/$cam
done
```

## File Organization Details

### `annotated_images/` Directory

**Purpose**: Store detection visualizations (images with bounding boxes drawn by camera_trap_detections.py)

**Storage**:
- Organized by campaign and camera
- One subdirectory per camera deployment
- Naming: Original JPG + `_annotated.jpg` variant

**Example**:
```
annotated_images/20250804_20250828/TW02-CT01/
├── IMG_20250804_120000_annotated.jpg
├── IMG_20250804_120530_annotated.jpg
├── IMG_20250804_121100_annotated.jpg
└── ...
```

**Note**: Annotated images can be excluded if storage is constrained; they're primarily for visual QA. Raw detection data is in darwin_core_occurrences.csv.

### `darwin_core_metadata/` Directory

**Purpose**: Store FAIR² compliant Darwin Core metadata (consolidated per campaign)

**Files**:
- `darwin_core_events.csv`: Survey session metadata (13 rows for 13 deployments)
- `darwin_core_occurrences.csv`: Species observation records (one per detection)
- `platform_specifications.json`: Hardware specifications and deployment details
- `processing_report.json`: Execution summary (successes, failures, timestamps)

**Storage**: One subdirectory per campaign containing all cameras' merged metadata

**Example content** (20250804_20250828):
```
darwin_core_events.csv: 9 rows (one per camera)
darwin_core_occurrences.csv: ~100,000+ rows (one per detection)
platform_specifications.json: Hardware specs for 3 camera models across 2 campaigns
processing_report.json: Batch processing execution details
```

### `intermediate_processing/` Directory

**Purpose**: Optional storage of intermediate pipeline files for quality assurance and debugging

**Contents**:
- `index.csv`: All images with EXIF extraction and filename parsing
- `events_validated.csv`: Extracted timestamps with validation flags and corrections applied
- `detections.csv`: Raw YOLO+BioCLIP output before merge

**When to keep**: For validation and error investigation
**When to delete**: After successful completion if storage is limited (easily regenerated)

### `validation_reports/` Directory

**Purpose**: Summary reports and quality metrics

**Files**:
- `timestamp_validation_report.csv`: Summary of validation results per camera
  - Cameras, total images, validation pass rate, corrections applied
- `detection_quality_metrics.json`: YOLO confidence distributions, species breakdown
- `missing_coordinates_report.csv`: Cameras lacking GPS data (action items)
- `processing_errors.log`: Any warnings or errors encountered during processing

## Workflow Integration

### Step 1: Run Detections (camera_trap_detections.py)

Output to: `annotated_images/{campaign}/{camera}/`

```bash
python camera_trap_detections.py \
    --weights yolov8x.pt \
    --images /fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps/TW02-CT01 \
    --csv-out /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828/TW02-CT01/detections.csv \
    --annotated-dir /fs/ess/PAS2136/TheWilds2025/processing_output/annotated_images/20250804_20250828/TW02-CT01 \
    --depth-estimation
```

### Step 2: Run Timestamp Validation (make_events_validated.py)

Reads images from original location, outputs to intermediate_processing:

```bash
python make_events_validated.py \
    --images /fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps/TW02-CT01 \
    --output /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828/TW02-CT01/events_validated.csv \
    --deployment-metadata /path/to/detection_config.json
```

### Step 3: Merge Detections and Events

```bash
python merge_detections_and_events.py \
    --detections /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828/TW02-CT01/detections.csv \
    --events /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828/TW02-CT01/events_validated.csv \
    --output /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828/TW02-CT01/merged.csv
```

### Step 4: Generate Darwin Core Metadata

```bash
python process_all_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-dir /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata/20250804_20250828 \
    --detections-dir /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828
```

## File Specifications

### darwin_core_events.csv

```csv
eventID,eventDate,eventEndDate,eventTime,eventEndTime,samplingProtocol,samplingEffort,decimalLatitude,decimalLongitude,coordinateUncertaintyInMeters,geodeticDatum,locality,habitat,sampleSizeValue,sampleSizeUnit,fieldNotes,eventRemarks
TW01-CT02_20250804_20250828,2025-08-04,2025-08-11,09:00:00,23:59:59,Passive infrared camera trap (PIR trigger),7 days continuous 24/7 monitoring,39.498459,-81.442737,5,WGS84,TheWilds Site TW01,Mixed deciduous forest,7,days,Camera facing southeast/lake,Camera TW01-CT02 deployed 2025-08-04 to 2025-08-11
...
```

**Key fields**:
- `eventID`: Unique identifier per deployment
- `decimalLatitude/Longitude`: **CAMERA location** (not animal)
- `coordinateUncertaintyInMeters`: 5 (camera placement uncertainty)
- `samplingEffort`: Duration in days and 24/7 note
- `fieldNotes`: Known issues (timestamp corrections, equipment problems)

### darwin_core_occurrences.csv

```csv
occurrenceID,eventID,scientificName,kingdom,phylum,class,order,family,genus,species,taxonRank,vernacularName,occurrenceStatus,individualCount,eventDate,eventTime,decimalLatitude,decimalLongitude,coordinateUncertaintyMeters,spatialReferenceSystem,associatedMedia,associatedOccurrences,recordedBy,basisOfRecord,identificationVerificationStatus,identificationRemarks,datasetID,datasetName,validationFlag
TW02-CT01_20250804_20250828_20250804T120000_001,TW02-CT01_20250804_20250828,Odocoileus virginianus (Zimmermann 1780),Animalia,Chordata,Mammalia,Artiodactyla,Cervidae,Odocoileus,virginianus,species,White-tailed Deer,present,1,2025-08-04,12:00:00,39.498394,-81.442751,50,WGS84,/path/to/image.jpg,Distance: 8.5m Angle: 45°,Automated camera trap detection (YOLO + BioCLIP),MachineObservation,unverified,BioCLIP: 0.92 YOLO: 0.95,TheWilds_2025_camera_traps,The Wilds 2025 Camera Trap Survey,valid
...
```

**Key fields**:
- `occurrenceID`: Unique per detection (eventID + timestamp + index)
- `eventID`: Foreign key to Event (survey session)
- `decimalLatitude/Longitude`: **ANIMAL location** (GPS projected from depth estimation)
- `coordinateUncertaintyMeters`: 50 (depth estimation uncertainty)
- `scientificName`: With taxonomic authority
- `basisOfRecord`: "MachineObservation" (automated detection)
- `identificationVerificationStatus`: "unverified" (transparency about automation)
- `validationFlag`: timestamp correction status

## Storage Recommendations

### Production Setup (All Processing Results)

Total estimated storage:
- **Annotated images**: ~500 GB (skippable if space is limited)
- **Darwin Core CSVs**: ~50 MB (keep permanently)
- **Intermediate files**: ~100 GB (optional, usually deleted after QA)
- **Total**: ~650 GB

Recommended: Storage on fast filesystem with daily backups of darwin_core_metadata/

### Minimum Setup (Darwin Core Only - Recommended)

Archive structure:
```
/fs/ess/PAS2136/TheWilds2025/processing_output/
├── darwin_core_metadata/              # Keep permanently (~50 MB)
├── validation_reports/                 # Keep permanently (~10 MB)
└── annotated_images/                  # Archive or delete after QA
```

## Access Permissions

```bash
# Set appropriate permissions
chmod 755 /fs/ess/PAS2136/TheWilds2025/processing_output
chmod 755 /fs/ess/PAS2136/TheWilds2025/processing_output/*
chmod 644 /fs/ess/PAS2136/TheWilds2025/processing_output/*/*.csv
chmod 644 /fs/ess/PAS2136/TheWilds2025/processing_output/*/*.json
```

## Next Steps

1. Create directory structure using provided scripts
2. Run detection pipeline, outputting to `annotated_images/`
3. Run timestamp validation to `intermediate_processing/`
4. Run batch metadata generation to `darwin_core_metadata/`
5. Review validation reports
6. Archive or delete intermediate files after QA verification
7. Upload darwin_core_metadata to archival repository
