# Camera Trap Annotation & Analysis Pipeline

Complete workflow for processing camera trap images with validated timestamps, species detection, and GPS localization.

## Overview

This pipeline combines multiple components to produce publication-ready camera trap detection data:

1. **Image Indexing** - Organize images by camera and session
2. **Timestamp Validation** - Extract timestamps with corrections for known camera clock issues
3. **Species Detection** - YOLO+SAHI for detection, BioCLIP for species classification
4. **Merge & Enrich** - Combine detections with validated timestamps and quality flags
5. **Analysis** - Temporal patterns, spatial distribution, species presence

## Directory Structure

```
imageomicsthewilds_cameratraps/
├── run_full_pipeline.py          # Entry point for orchestrating all steps
├── README.md                      # This file
│
├── src/
│   ├── 00_indexing/
│   │   └── index_images.py       # Index images by camera/session
│   │
│   ├── 01_events/
│   │   ├── make_events_validated.py      # Extract & validate timestamps
│   │   ├── camera_deployment_metadata.py # Camera metadata + corrections
│   │   └── README_VALIDATION.md          # Timestamp validation docs
│   │
│   ├── 02_merge/
│   │   ├── merge_detections_and_events.py # Merge detections with events
│   │   └── README_MERGE.md                 # Merge documentation
│   │
│   ├── 03_metadata/
│   │   ├── generate_darwin_core_events.py # Darwin Core Event records
│   │   ├── generate_darwin_core_occurrences.py # Darwin Core Occurrences
│   │   ├── create_platform_specs.py       # Platform/sensor specs
│   │   └── README_METADATA.md             # FAIR² Drones docs
│   │
│   ├── 02_analysis/
│   │   ├── analyze_arrivals.py
│   │   ├── plot_counts.py
│   │   └── plot_gaps_heatmap.py
│   │
│   └── 03_plots/
│       └── sanity_vis.py
└── ../bharaths_scripts/
    └── camera_trap_detections.py  # YOLO+SAHI+BioCLIP detections (external)
```

## Pipeline Steps

### Step 1: Image Indexing (00_indexing)

Recursively finds all camera trap images and creates a manifest with camera/session info.

```bash
python src/00_indexing/index_images.py
```

**Output**: `index.csv`
- path: Image file path
- site_cam: Camera identifier (e.g., TW02-CT01)
- session: Deployment session

### Step 2: Event Extraction & Validation (01_events) ⭐ NEW

Extracts timestamps from filenames and EXIF, applies corrections for known camera issues, and flags images for manual review.

```bash
python src/01_events/make_events_validated.py
```

**Inputs**:
- `index.csv` (from step 1)
- Deployment metadata (embedded in `camera_deployment_metadata.py`)

**Outputs**:
- `events_validated.csv` - Timestamped images with quality flags

**Key Features**:
- ✓ Date range validation against known deployment periods
- ✓ Filename vs EXIF timestamp cross-checking
- ✓ Automatic corrections for cameras with clock issues (e.g., TW02-CT01)
- ✓ Comprehensive manual review flags
- ✓ Detailed processing statistics

**Known Issues Handled**:
- **TW02-CT01** (Aug 2025): Camera clock initially set to Oct 31, 2023, then Sept 2023 instead of Aug 2025 → Correction mapping applied
- **TW04-CT03** (Aug 2025): Equipment failure after Aug 25 → Flagged for review
- **TW09_CT02** (Aug 2025): Battery failure Aug 18-25 → Documented in metadata

See `src/01_events/README_VALIDATION.md` for details.

### Step 3: Species Detection (bharaths_scripts)

Runs YOLO object detection + SAHI sliced inference + BioCLIP species classification. This is handled by an external script.

```bash
python camera_trap_detections.py \
    --weights yolov8x.pt \
    --images /path/to/images \
    --conf 0.25 \
    --hfov-deg 52 \
    --target-height-m 1.0 \
    --camera-lat 39.49 \
    --camera-lon -81.44 \
    --camera-bearing-deg 270 \
    --csv-out detections.csv
```

**Output**: `detections.csv`
- Bounding boxes, confidence scores
- BioCLIP species classification
- Estimated distance and angle
- GPS-projected animal coordinates

See `bharaths_scripts/README.md` for full documentation.

### Step 4: Merge Results (02_merge) ⭐ NEW

Combines validated timestamps with detection results.

```bash
python src/02_merge/merge_detections_and_events.py \
    --events events_validated.csv \
    --detections detections.csv \
    --output detections_with_validated_timestamps.csv
```

**Output**: `detections_with_validated_timestamps.csv`

Includes:
- All detection fields (species, confidence, coordinates)
- Validated timestamp (corrected if needed)
- Timestamp quality flags
- Evidence trails (filename_timestamp, exif_timestamp, timestamp_source)

See `src/02_merge/README_MERGE.md` for schema and usage.

### Step 5: FAIR² Metadata Generation (03_metadata) ⭐ NEW

Generate Darwin Core biodiversity records and platform specifications for publication.

```bash
# Generate Event records (camera deployments/sessions)
python src/03_metadata/generate_darwin_core_events.py

# Generate Occurrence records (species observations from detections)
python src/03_metadata/generate_darwin_core_occurrences.py \
    src/02_merge/detections_with_validated_timestamps.csv \
    src/03_metadata/darwin_core_events.csv \
    src/03_metadata/darwin_core_occurrences.csv

# Create platform and sensor specifications
python src/03_metadata/create_platform_specs.py
```

**Output**:
- `darwin_core_events.csv` - Survey sessions (one per camera deployment)
- `darwin_core_occurrences.csv` - Species observations (one per detection)
- `platform_specifications.json` - Camera hardware and mission parameters

See `src/03_metadata/README_METADATA.md` for detailed documentation.

### Step 6: Analysis (02_analysis, 03_plots)

Temporal analysis, gap detection, spatial visualization.

```bash
python src/02_analysis/analyze_arrivals.py
python src/03_plots/plot_counts.py
python src/03_plots/plot_gaps_heatmap.py
```

## Quick Start

### Using the Full Pipeline Script

```bash
# Prepare camera configuration JSON
cat > cameras.json << 'EOF'
{
  "cameras": {
    "TW02-CT01": {
      "lat": 39.49,
      "lon": -81.44,
      "bearing": 270,
      "hfov": 52,
      "target_height": 1.0
    }
  }
}
EOF

# Run full pipeline
python run_full_pipeline.py \
    --image-dir /fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps \
    --yolo-weights yolov8x.pt \
    --camera-config cameras.json \
    --output-dir ./results
```

### Running Steps Individually

```bash
# Index images
cd src/00_indexing
python index_images.py

# Validate timestamps
cd ../01_events
python make_events_validated.py

# Run detections separately per camera (parallelizable)
cd ../../bharaths_scripts
python camera_trap_detections.py --weights yolov8x.pt --images /path/to/images ...

# Merge results
cd ../src/02_merge
python merge_detections_and_events.py \
    --events ../01_events/events_validated.csv \
    --detections detections.csv \
    --output detections_with_validated_timestamps.csv

# Analyze
cd ../02_analysis
python analyze_arrivals.py
```

## Deployment Data

### Campaign 1: June 30 - July 3, 2025
- **Data**: ~20K camera trap images
- **Cameras**: TW01-CT02, TW02-CT03, TW03-CT01, TW04-CT04
- **Location**: `/fs/ess/PAS2136/TheWilds2025/thewilds_20250630_20250703/camera_traps/`
- **Known Issues**: None documented

### Campaign 2: August 4 - August 28, 2025
- **Data**: ~222K camera trap images
- **Cameras**: TW01-CT02, TW02-CT01, TW04-CT03, TW06-CT04, TW06-CT05, TW07-CT05, TW09_CT02, TW09-CT05, TW11-CT06
- **Location**: `/fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps/`
- **Known Issues**:
  - TW02-CT01: Camera clock set incorrectly (Oct 31, 2023 → Aug 4, 2025; Sept 2023 → Aug 2025)
  - TW04-CT03: No data after Aug 25 (equipment failure)
  - TW09_CT02: Data gap Aug 18-25 (battery died)

### Campaign 3: September 8, 2025
- **Data**: Drone videos only (no camera traps)
- **Location**: `/fs/ess/PAS2136/TheWilds2025/thewilds_20250908_20250908/`

## Key Improvements in This Version

### Timestamp Validation (NEW)
- Cross-checks filename vs EXIF timestamps
- Validates against deployment date ranges
- Applies automatic corrections for known camera issues
- Flags images for manual review

### Metadata Integration (NEW)
- Centralized camera deployment metadata
- Timestamp correction mappings
- Known data gaps and equipment failures documented
- Easy to update as new issues are discovered

### Detection-Event Merge (NEW)
- Links temporal context with detections
- Preserves evidence trails (original timestamps)
- Enables filtering by validation quality
- Supports downstream data quality assessment

### FAIR² Drones Compliance (NEW) ⭐
- **Darwin Core Event Records**: One per camera deployment (session)
- **Darwin Core Occurrence Records**: One per species detection (observation)
- **Platform Specifications**: Complete hardware and sensor documentation
- **Taxonomic Authority**: Scientific names verified with GBIF
- **Interoperability**: TDWG standards for biodiversity data

See `src/03_metadata/README_METADATA.md` for complete FAIR² documentation.

### Better Documentation
- Comprehensive README for each component
- Schema documentation for all CSV outputs
- Known issues and corrections clearly documented
- Troubleshooting guides

## Output Files

All outputs go to the specified output directory:

```
results/
├── index.csv                                    # Image manifest
├── events_validated.csv                        # Timestamped images with flags
├── detections.csv                              # Raw YOLO+BioCLIP output (from bharaths_scripts)
├── detections_with_validated_timestamps.csv    # Detections + validated timestamps
├── darwin_core_events.csv                      # ⭐ Survey sessions (Darwin Core)
├── darwin_core_occurrences.csv                 # ⭐ Species observations (Darwin Core)
├── platform_specifications.json                # ⭐ Hardware/sensor specifications
├── counts_over_time.csv                        # Arrival rate analysis
├── gaps.csv                                    # Data gaps by camera
├── counts_over_time_1h_fullgrid.csv           # Hourly grid
├── gaps_1h_fullrange.csv                       # Full-range gaps
└── annotated/                                  # Images with detection boxes
    ├── image_001_annotated.jpg
    └── ...
```

## CSV Column Reference

### events_validated.csv (NEW)
- `timestamp`: Corrected timestamp (YYYY-MM-DD HH:MM:SS)
- `site_cam`: Camera ID (e.g., TW02-CT01)
- `session`: Deployment session
- `path`: Image file path
- `timestamp_source`: 'filename', 'exif', or 'corrected'
- `validation_flag`: Manual review reason (if any)
- `filename_timestamp`: Original filename timestamp
- `exif_timestamp`: Original EXIF timestamp

### detections_with_validated_timestamps.csv (NEW)
- All columns from `events_validated.csv`
- All columns from raw detections.csv:
  - `detection_index`, `bioclip_label`, `bioclip_score`, `yolo_conf`
  - `xmin`, `ymin`, `xmax`, `ymax` (bounding box)
  - `distance_m`, `angle_deg` (estimated distance/angle)
  - `camera_lat`, `camera_lon`, `camera_bearing_deg`
  - `animal_lat`, `animal_lon`, `animal_absolute_bearing_deg` (GPS projection)

### darwin_core_events.csv (NEW) ⭐ FAIR²
**One row per camera deployment (survey session) — CAMERA LOCATIONS**

- `eventID`: Unique session identifier (e.g., `TW02-CT01_20250804_20250828`)
- `eventDate`: Deployment start date (YYYY-MM-DD)
- `eventEndDate`: Deployment end date (YYYY-MM-DD)
- `eventTime`: Start time (HH:MM:SS)
- `eventEndTime`: End time (HH:MM:SS)
- `samplingProtocol`: "Passive infrared camera trap (PIR trigger)"
- `samplingEffort`: Duration and frequency (e.g., "24 days, continuous 24/7")
- `decimalLatitude`: **CAMERA location** latitude (WGS84)
- `decimalLongitude`: **CAMERA location** longitude (WGS84)
- `coordinateUncertaintyInMeters`: GPS accuracy (typical ±5m)
- `geodeticDatum`: "WGS84"
- `locality`: Named location (e.g., "TheWilds Site TW02")
- `habitat`: Habitat description
- `sampleSizeValue`: Days deployed
- `sampleSizeUnit`: "days"
- `minimumElevationInMeters`: Ground elevation
- `maximumElevationInMeters`: Ground elevation
- `weather`: Conditions observed
- `fieldNotes`: Issues and observations
- `eventRemarks`: Summary of deployment

### darwin_core_occurrences.csv (NEW) ⭐ FAIR²
**One row per species detection (observation) — ANIMAL OBSERVATION LOCATIONS**

- `occurrenceID`: Unique observation identifier (e.g., `TW02-CT01_20250810T134530_001`)
- `eventID`: Links to event (deployment session)
- `catalogNumber`: Internal reference number
- `scientificName`: Species with authority (e.g., `Odocoileus virginianus (Zimmermann, 1780)`)
- `scientificNameAuthority`: Authority for name (e.g., "GBIF Taxonomic Backbone")
- `kingdom`: "Animalia"
- `phylum`: "Chordata"
- `class`: "Mammalia" or "Aves"
- `order`: Taxonomic order
- `family`: Taxonomic family (e.g., "Cervidae")
- `genus`: Genus name
- `species`: Species epithet
- `taxonRank`: "species"
- `vernacularName`: Common name (e.g., "White-tailed Deer")
- `occurrenceStatus`: "present"
- `occurrenceRemarks`: Notes about observation
- `individualCount`: Number of animals detected
- `lifeStage`: "adult", "juvenile", or "unknown"
- `sex`: "male", "female", or "unknown"
- `behavior`: Behavioral state if observable
- `establishmentMeans`: "wild"
- `degreeOfEstablishment`: "native"
- `eventDate`: Observation date (from image timestamp)
- `eventTime`: Observation time (from image timestamp)
- `decimalLatitude`: **ANIMAL location** (GPS projected from depth estimation)
- `decimalLongitude`: **ANIMAL location** (GPS projected from depth estimation)
- `coordinateUncertaintyMeters`: ~50m (uncertainty from depth estimation)
- `spatialReferenceSystem`: "WGS84"
- `associatedMedia`: Path to image file
- `associatedOccurrences`: Detection bounding box coordinates + distance + angle
- `recordedBy`: "Automated camera trap detection (YOLO + BioCLIP)"
- `basisOfRecord`: "MachineObservation"
- `identificationVerificationStatus`: "unverified" (automated, not manually reviewed)
- `identificationRemarks`: Detection confidence scores
- `datasetID`: "TheWilds_2025_camera_traps"
- `datasetName`: "The Wilds 2025 Camera Trap Survey"
- `validationFlag`: Timestamp quality issues (if any)

## Data Quality Checks

Filter merged output for analysis:

```python
import pandas as pd

data = pd.read_csv('detections_with_validated_timestamps.csv')

# Only use detections with validated timestamps
clean_data = data[data['validation_flag'].isna()]

# Find flagged detections
flagged = data[data['validation_flag'].notna()]

# Check timestamp sources
print(data['timestamp_source'].value_counts())

# Verify coverage by camera
print(data.groupby('site_cam').size())
```

## Troubleshooting

See the README files in each src/ subdirectory:
- `src/01_events/README_VALIDATION.md` - Timestamp issues
- `src/02_merge/README_MERGE.md` - Merge problems
- `bharaths_scripts/README.md` - Detection issues

## Future Enhancements

- [ ] Automatic gap detection from image sequences
- [ ] Integration with field deployment logs (CSV import)
- [ ] Batch processing across multiple cameras/deployments
- [ ] Quality metrics dashboard (timestamp accuracy, detection coverage, etc.)
- [ ] Export to Zenodo/HuggingFace compatible format
- [ ] Darwin Core compliance for species data

## Citation

If you use this pipeline, please cite:
- Bharath Pillai et al. - Camera trap detection pipeline (YOLO+SAHI+BioCLIP)
- SongSage bioacoustics pipeline
- Original imageomics thewilds camera trap code

## Contact

For issues with:
- **Timestamp validation**: See `camera_deployment_metadata.py`
- **Detection pipeline**: See `bharaths_scripts/README.md`
- **Merge/integration**: See `src/02_merge/README_MERGE.md`
