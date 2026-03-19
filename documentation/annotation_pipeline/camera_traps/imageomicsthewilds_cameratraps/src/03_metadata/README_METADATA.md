# Camera Trap FAIR² Drones Metadata Documentation

This directory contains scripts and documentation for generating FAIR² Drones compliant metadata for The Wilds 2025 Camera Trap survey.

## Overview

The FAIR² Drones Data Standard ensures that camera trap datasets are:
- **Findable**: Unique identifiers and comprehensive metadata
- **Accessible**: Open data formats and clear documentation
- **Interoperable**: Darwin Core biodiversity standards
- **Reusable**: Complete platform, sensor, and mission specifications
- **AI-Ready**: Structured annotations and metadata
- **Ecologically Compliant**: Darwin Core + TDWG standards for biodiversity research

## Key Concepts

### Events vs. Occurrences

The standard separates data into two key Darwin Core concepts:

#### **Events** = Sessions/Deployments
Each camera deployment is one **Event**:
- What: Passive camera trap survey
- Where: One camera location
- When: One deployment period (e.g., Aug 4 - Aug 11, 2025)
- Who: Survey team
- How long: Duration in days

**File**: `darwin_core_events.csv`

**Example Event**:
```
eventID: TW02-CT01_20250804_20250828
eventDate: 2025-08-04
eventEndDate: 2025-08-28
location: The Wilds Site TW02
samplingProtocol: Passive infrared camera trap (PIR trigger)
samplingEffort: 24 days, continuous 24/7 monitoring
```

#### **Occurrences** = Individual Observations
Each detection (bounding box) in photos is one **Occurrence**:
- What: Species observation (e.g., white-tailed deer)
- Where: GPS-projected location (if available)
- When: Timestamp from image
- Count: Number of individuals detected
- Evidence: Image file, bbox, confidence scores

**File**: `darwin_core_occurrences.csv`

**Example Occurrence**:
```
occurrenceID: TW02-CT01_20250810_0001
eventID: TW02-CT01_20250804_20250828
scientificName: Odocoileus virginianus
occurrenceStatus: present
recordedBy: Automated camera trap detection (YOLO + BioCLIP)
individualCount: 1
basisOfRecord: MachineObservation
```

### Linkage Structure: Events vs. Occurrences

**Events** = Camera Trap Survey Sessions (where the camera is placed)
**Occurrences** = Species Observations (where animals were detected)

```
┌─────────────────────────────────────────────────────────────────┐
│ darwin_core_events.csv (SURVEY SESSIONS - Camera Locations)     │
├─────────────────────────────────────────────────────────────────┤
│ eventID: TW02-CT01_20250804_20250828                            │
│ eventDate: 2025-08-04 to 2025-08-28                             │
│ decimalLatitude: 39.498394  ← CAMERA LOCATION                   │
│ decimalLongitude: -81.442751 ← CAMERA LOCATION                  │
│ samplingProtocol: Passive infrared camera trap                  │
│ samplingEffort: 24 days continuous monitoring                   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Links via eventID
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│ darwin_core_occurrences.csv (SPECIES OBSERVATIONS - Animal Locs) │
├─────────────────────────────────────────────────────────────────┤
│ occurrenceID: TW02-CT01_20250810T134530_001                     │
│ eventID: TW02-CT01_20250804_20250828 ← Links to event           │
│ scientificName: Odocoileus virginianus                          │
│ individualCount: 1                                              │
│ decimalLatitude: 39.4985  ← ANIMAL LOCATION (GPS projected)     │
│ decimalLongitude: -81.4422 ← ANIMAL LOCATION (GPS projected)    │
│ coordinateUncertaintyMeters: 50 ← Depth estimation uncertainty  │
│ associatedOccurrences: Distance: 2.3m, Angle: 15°               │
└─────────────────────────────────────────────────────────────────┘
           ↓
           └──→ Also links to image file and detection box
                Provides evidence for the observation
```

**Key Distinction**:
- **Event** decimalLatitude/Longitude = Camera position (survey location)
- **Occurrence** decimalLatitude/Longitude = Projected animal position (observation location)


## Files in This Directory

### 1. **generate_darwin_core_events.py**
Creates Event records for each camera deployment.

**Input**: `camera_deployment_metadata.py` (deployment dates)
**Output**: `darwin_core_events.csv`

**Usage**:
```bash
python generate_darwin_core_events.py
```

**Produces**: One row per camera deployment (session)

**Key Fields**:
- eventID: Unique session identifier
- eventDate / eventEndDate: Deployment period
- decimalLatitude/Longitude: Camera location
- samplingProtocol: "Passive infrared camera trap"
- samplingEffort: Deployment duration
- habitat, locality, fieldNotes: Location/site info

### 2. **generate_darwin_core_occurrences.py**
Creates Occurrence records for each detection.

**Input**:
- `detections_with_validated_timestamps.csv` (detections)
- `darwin_core_events.csv` (to link occurrences to events)

**Output**: `darwin_core_occurrences.csv`

**Usage**:
```bash
python generate_darwin_core_occurrences.py \
    detections_with_validated_timestamps.csv \
    darwin_core_events.csv \
    darwin_core_occurrences.csv
```

**Produces**: One row per detection (observation)

**Key Fields**:
- occurrenceID: Unique observation identifier
- eventID: Links to event (session)
- scientificName: Species (with authority)
- taxonRank, kingdom, phylum, ..., species: Complete taxonomy
- individualCount: Number of individuals observed
- recordedBy: "Automated camera trap detection"
- basisOfRecord: "MachineObservation" (automated)
- associatedMedia: Image file path
- identificationRemarks: Detection confidence scores

### 3. **create_platform_specs.py**
Documents camera hardware, sensors, and mission parameters.

**Output**: `platform_specifications.json`

**Usage**:
```bash
python create_platform_specs.py
```

**Contents**:
- Camera models used (Garde Pro T5NG, Trail Camera G600, Garde Pro A3)
- Sensor specifications (resolution, FOV, thermal, etc.)
- Physical specs (weight, power, weatherproofing)
- Recording modes (photo, timelapse, video)
- Mission parameters (altitude, speed, patterns)
- Geometric calibration (for distance estimation)
- Data format specifications
- Known issues by deployment

### 4. **README_METADATA.md** (this file)
Guide to understanding FAIR² Drones compliance for camera traps.

## Architecture of FAIR² Compliance

### Tier 1: Core Data
```
images/ → Raw camera trap photos
annotations/ → Detection results (YOLO + BioCLIP)
```

### Tier 2: Temporal Metadata
```
detections_with_validated_timestamps.csv → Images + corrections + quality flags
```

### Tier 3: Darwin Core Biodiversity Metadata
```
darwin_core_events.csv → Sessions/deployments/surveys
darwin_core_occurrences.csv → Individual species observations
```

### Tier 4: Platform & Mission Specifications
```
platform_specifications.json → Hardware, sensors, operational details
```

## Workflow Integration

This is typically step 3 in the complete pipeline:

```
1. Image Indexing (00_indexing)
   └→ index.csv

2. Event Extraction & Validation (01_events)
   └→ events_validated.csv

3. Detection (external: camera_trap_detections.py)
   └→ detections.csv

4. Merge (02_merge)
   └→ detections_with_validated_timestamps.csv

5. FAIR² Metadata Generation (03_metadata) ← YOU ARE HERE
   ├→ darwin_core_events.csv
   ├→ darwin_core_occurrences.csv
   ├→ platform_specifications.json
   └→ README_METADATA.md
```

## Usage in Full Pipeline

```bash
# After running steps 1-4, generate FAIR² metadata:

# Generate event records (sessions/deployments)
python generate_darwin_core_events.py

# Generate occurrence records (detections/observations)
python generate_darwin_core_occurrences.py \
    ../../02_merge/detections_with_validated_timestamps.csv \
    darwin_core_events.csv \
    darwin_core_occurrences.csv

# Create platform specifications
python create_platform_specs.py

# Result: Complete FAIR² compliant dataset ready for publication!
```

## Output Files Structure

```
metadata/
├── darwin_core_events.csv           # Sessions (deployments)
├── darwin_core_occurrences.csv      # Detections (observations)
├── platform_specifications.json     # Hardware/sensor specs
└── README_METADATA.md              # This file
```

## Key FAIR² Metadata Fields

### Events (darwin_core_events.csv)

**Minimal Required**:
- eventID: Unique session identifier
- eventDate: When survey started
- eventEndDate: When survey ended
- samplingProtocol: Survey method
- samplingEffort: Duration/effort
- locality: Named location

**Darwin Core Recommended**:
- decimalLatitude/Longitude: Camera position
- coordinateUncertaintyInMeters: GPS accuracy (±5m typical)
- habitat: Habitat type
- sampleSizeValue/Unit: Area/duration
- fieldNotes: Deployment notes
- weather: Conditions observed

### Occurrences (darwin_core_occurrences.csv)

**Minimal Required**:
- occurrenceID: Unique observation ID
- eventID: Links to event
- scientificName: Species with authority
- kingdom, ..., species: Complete taxonomy
- occurrenceStatus: "present"

**Darwin Core Recommended**:
- individualCount: Number of animals
- basisOfRecord: "MachineObservation" (automated)
- recordedBy: Detection method
- eventDate: Observation timestamp
- decimalLatitude/Longitude: Animal location
- associatedMedia: Image file

### Platform Specs (platform_specifications.json)

**Required**:
- Camera model and manufacturer
- Sensor type and resolution
- Field of view and focal length
- Temporal resolution (trigger-based vs. timelapse)
- Storage and file formats

**Recommended**:
- Physical specs (weight, power)
- Recording modes available
- Date/time accuracy
- Known issues and limitations
- Deployment configuration details

## Animal Location Estimation (GPS Projection)

Each detection includes an **estimated animal location** computed from depth estimation:

**How it works**:
1. **Bounding box height** is compared to typical animal size (e.g., 1.0m for white-tailed deer)
2. **Distance to animal** is estimated: `distance = (animal_height × focal_length) / bbox_height`
3. **Horizontal angle** is computed from bbox center position
4. **GPS coordinates** are projected from camera location using vincenty geodetics

**Fields in darwin_core_occurrences.csv**:
- `decimalLatitude`, `decimalLongitude`: Projected animal location (GPS)
- `coordinateUncertaintyMeters`: 50m (approximate uncertainty from depth estimation)
- `associatedOccurrences`: Distance and angle details for reference

**Limitations**:
- Height estimate assumes animals are upright and fully visible
- Partially occluded animals may yield poor distance estimates
- Dense groups appear as single detection with average distance
- No altitude information (2D projection only)

**Example**:
```
camera_location: 39.49°N, 81.44°W
animal_at_bbox: detected 2.3m away, 15° right of center
projected_animal_location: 39.4901°N, 81.4398°W ± 50m
```

See `camera_trap_detections.py` lines 112-156 for implementation details.

## Taxonomic Authority

The standard requires complete scientific names with taxonomic authority:

**Example - White-tailed Deer**:
```
scientificName: Odocoileus virginianus (Zimmermann, 1780)
kingdom: Animalia
phylum: Chordata
class: Mammalia
order: Artiodactyla
family: Cervidae
genus: Odocoileus
species: virginianus
taxonRank: species
scientific name Authority: GBIF Taxonomic Backbone
```

Verify species names at: https://www.gbif.org/species/search

## Known Data Issues & How They're Documented

All known issues are documented in both:

1. **camera_deployment_metadata.py**: Issue descriptions and timestamp corrections
2. **darwin_core_events.csv**: fieldNotes column documents issues
3. **darwin_core_occurrences.csv**: validationFlag column flags affected detections

**Example**: TW02-CT01 camera clock issue
```
Issue: Camera clock set to Oct 31 2023 initially, then Sept 2023 instead of Aug 2025
Status: Automatic correction applied in timestamp processing
Evidence: `timestamp_corrections` mapping in camera_deployment_metadata.py
Flagged: validationFlag="CORRECTED: camera clock was set incorrectly"
```

## Data Quality Indicators

The generated CSV files include fields for data quality assessment:

```python
# Filter for manual review in occurrence data:
occurrences = pd.read_csv('darwin_core_occurrences.csv')

# Find flagged detections
flagged = occurrences[occurrences['validationFlag'].notna()]

# Most detections should have "high" quality:
high_quality = occurrences[occurrences['identificationVerificationStatus'] == 'unverified']
```

## Publishing and Sharing

Once complete, these FAIR² compliant files can be:

1. **Published to Zenodo**: With DOI for citation
2. **Shared with GBIF**: Occurrence data for biodiversity database
3. **Released on HuggingFace**: ML/AI research community
4. **Included in Data Repositories**: For long-term preservation

## Compliance Checklist

- [ ] darwin_core_events.csv created with all camera deployments
- [ ] darwin_core_occurrences.csv created linking detections to events
- [ ] All scientific names verified with GBIF authority
- [ ] platform_specifications.json documents all hardware/sensors
- [ ] eventID and occurrenceID follow consistent format
- [ ] All timestamps validated and corrections applied
- [ ] Known issues documented in fieldNotes/validationFlag
- [ ] Geographic coordinates documented with uncertainty
- [ ] Sampling protocol clearly described
- [ ] Taxonomic hierarchy complete (to species level minimum)
- [ ] BasisOfRecord set to 'MachineObservation' for automated detections
- [ ] Dataset has DOI or is prepared for publication

## Troubleshooting

### Missing eventID Links
- Ensure deployment metadata has all cameras and date ranges
- Check that timestamps in detections fall within event periods
- Verify site_cam naming matches between files

### Incorrect Species Names
- Validate all species names at https://www.gbif.org/species/search
- Include name authority (year, author) from GBIF
- Use scientificName field with full authority

### Incomplete Taxonomy
- All records should include kingdom through species
- Use "Unknown" only if really unknown (rare for these datasets)
- Query GBIF for complete taxonomic hierarchy

### Timezone Issues
- All timestamps should be in ISO 8601 format: YYYY-MM-DDTHH:MM:SS±HH:MM
- Specify timezone in eventTime field
- Camera clocks are in USA Eastern Time (note in metadata)

## References

- **Darwin Core Standard**: https://dwc.tdwg.org/
- **GBIF Species Search**: https://www.gbif.org/species/search
- **FAIR Principles**: https://www.go-fair.org/fair-principles/
- **FAIR² Drones Paper**: [Citation to be added]
- **Imageomics Dataset Card**: https://imageomics.github.io/Imageomics-guide/

## Contact

For questions about:
- **Metadata generation**: See comments in Python scripts
- **Darwin Core compliance**: Consult TDWG standards
- **GBIF submission**: Contact GBIF helpdesk
- **The Wilds dataset**: Contact researchers or project lead
