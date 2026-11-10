# Quick Start Guide: Using Organized Directory Structure

This guide walks through setting up and using the organized directory structure for camera trap processing.

## 1. Initial Setup (One-time)

### Create the directory structure:

```bash
cd /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps
chmod +x setup_output_directories.sh

./setup_output_directories.sh \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-root /fs/ess/PAS2136/TheWilds2025/processing_output
```

This creates:
- `annotated_images/` - for detection visualizations (13 camera subdirectories)
- `darwin_core_metadata/` - for FAIR² compliant metadata (2 campaign subdirectories)
- `intermediate_processing/` - for temporary/validation files (13 camera subdirectories)
- `validation_reports/` - for quality assurance summaries

## 2. Run Detection Pipeline

Output annotated images to the organized structure:

```bash
# Example: Process TW02-CT01 from August campaign
python camera_trap_detections.py \
    --weights yolov8x.pt \
    --images /fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps/TW02-CT01 \
    --csv-out /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828/TW02-CT01/detections.csv \
    --annotated-dir /fs/ess/PAS2136/TheWilds2025/processing_output/annotated_images/20250804_20250828/TW02-CT01 \
    --depth-estimation \
    --bioclip-labels "white-tailed deer" "deer" "bird"
```

**Key outputs**:
- Annotated images: `processing_output/annotated_images/20250804_20250828/TW02-CT01/`
  - Original JPGs with bounding boxes drawn
- Detection CSV: `processing_output/intermediate_processing/20250804_20250828/TW02-CT01/detections.csv`
  - YOLO predictions, BioCLIP classifications, projected animal locations

## 3. Validate Timestamps

```bash
python make_events_validated.py \
    --images /fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps/TW02-CT01 \
    --output /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828/TW02-CT01/events_validated.csv \
    --deployment-config /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps/detection_config.json
```

**Output**:
- `events_validated.csv`: Extracted and validated timestamps with correction flags

## 4. Generate Darwin Core Metadata

### Option A: Organized by Campaign (Recommended)

```bash
python process_all_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-dir /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata \
    --detections-dir /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing \
    --organized-output
```

**Output structure**:
```
processing_output/darwin_core_metadata/
├── 20250630_20250703/
│   ├── darwin_core_events.csv          (4 events for June cameras)
│   ├── darwin_core_occurrences.csv     (species observations)
│   └── platform_specifications.json
│
└── 20250804_20250828/
    ├── darwin_core_events.csv          (9 events for August cameras)
    ├── darwin_core_occurrences.csv     (species observations)
    └── platform_specifications.json
```

### Option B: Consolidated (Legacy)

```bash
python process_all_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-dir /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata \
    --detections-dir /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing
```

**Output structure**:
```
processing_output/darwin_core_metadata/
├── darwin_core_events.csv              (13 total events)
├── darwin_core_occurrences.csv         (all species observations)
└── platform_specifications.json
```

## 3. Storage Summary

### Typical Usage:

```
processing_output/
├── annotated_images/                   (~500 GB) Optional, for visual QA
├── darwin_core_metadata/               (~50 MB)  Keep permanently
├── intermediate_processing/            (~100 GB) Can delete after QA
└── validation_reports/                 (~10 MB)  Keep for audit trail
```

### Minimal Setup (Space Constrained):

```
processing_output/
├── darwin_core_metadata/               (~50 MB)  Essential
└── validation_reports/                 (~10 MB)  Essential
```

Delete after verification:
- `annotated_images/` (regeneratable)
- `intermediate_processing/` (regeneratable, unless timestamp validation changes)

## 4. Configuration Reference

### Key paths in detection_config.json:

```json
{
  "campaigns": {
    "20250630_20250703": {
      "name": "June-July 2025 Campaign",
      "base_path": "/fs/ess/PAS2136/TheWilds2025/thewilds_20250630_20250703/camera_traps",
      "total_cameras": 4
    },
    "20250804_20250828": {
      "name": "August 2025 Campaign",
      "base_path": "/fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps",
      "total_cameras": 9
    }
  },
  "cameras": {
    "TW02-CT01_20250804_20250828": {
      "image_dir": "/fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps/TW02-CT01",
      "location": {
        "latitude": 39.498394,
        "longitude": -81.442751,
        "bearing_deg": 225
      }
    }
  }
}
```

## 5. Quality Checks

After generation, validate outputs:

```bash
# Check Events
head -5 /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata/20250804_20250828/darwin_core_events.csv

# Count Occurrences
tail -n +2 /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata/20250804_20250828/darwin_core_occurrences.csv | wc -l

# Verify GPS coordinates
grep -E "^39\." /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata/20250804_20250828/darwin_core_events.csv | cut -d',' -f8,9
```

## 6. Batch Processing Example

Run complete workflow for all cameras:

```bash
# Setup directories
./setup_output_directories.sh --base-dir /fs/ess/PAS2136/TheWilds2025

# Define function to process one camera
process_camera() {
    local campaign=$1
    local camera=$2
    local base_dir="/fs/ess/PAS2136/TheWilds2025"
    local out_dir="$base_dir/processing_output"
    local src_dir="$base_dir/thewilds_${campaign}/camera_traps/$camera"

    echo "Processing $camera in campaign $campaign..."

    # Step 1: Detections
    python camera_trap_detections.py \
        --weights yolov8x.pt \
        --images "$src_dir" \
        --csv-out "$out_dir/intermediate_processing/$campaign/$camera/detections.csv" \
        --annotated-dir "$out_dir/annotated_images/$campaign/$camera" \
        --depth-estimation

    # Step 2: Timestamp validation
    python make_events_validated.py \
        --images "$src_dir" \
        --output "$out_dir/intermediate_processing/$campaign/$camera/events_validated.csv" \
        --deployment-config "$base_dir/documentation/annotation_pipeline/camera_traps/detection_config.json"
}

# Process all August cameras
for camera in TW01-CT02 TW02-CT01 TW04-CT03 TW06-CT04 TW06-CT05 TW07-CT05 TW09_CT02 TW09-CT05 TW11-CT06; do
    process_camera "20250804_20250828" "$camera"
done

# Generate Darwin Core metadata
python process_all_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-dir /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata \
    --detections-dir /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing \
    --organized-output
```

## 7. Publishing Workflow

After generation and QA:

```bash
# Organize for publication
mkdir -p /archive/TheWilds2025_Darwin_Core
cp -r /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata/* /archive/TheWilds2025_Darwin_Core/

# Add metadata file
cat > /archive/TheWilds2025_Darwin_Core/README.md << 'EOF'
# The Wilds 2025 Camera Trap Survey - Darwin Core Records

Generated: $(date)
Campaign 1: June 30 - July 3, 2025 (4 cameras, ~20k images)
Campaign 2: August 4 - 28, 2025 (9 cameras, ~222k images)

Files:
- darwin_core_events.csv: Survey session metadata (13 rows)
- darwin_core_occurrences.csv: Species observations (>100k rows)
- platform_specifications.json: Camera hardware specifications

Darwin Core standard: https://dwc.tdwg.org/
FAIR² Drones standard: [link to standard]
EOF

# Upload to GBIF/Zenodo/HuggingFace
# (instructions depend on chosen platform)
```

## Troubleshooting

### Missing coordinates in Events

Check detection_config.json for cameras without GPS:
```bash
grep -A 10 '"location"' /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps/detection_config.json | grep -B 5 '"latitude": null'
```

Fill in from field notes and update detection_config.json.

### No Occurrences generated

Verify detections file exists:
```bash
ls -lh /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/20250804_20250828/TW02-CT01/detections.csv
```

Re-run camera_trap_detections.py if missing.

### Storage running out

Delete (in order of importance):
1. Annotated images: `rm -rf processing_output/annotated_images/*`
2. Intermediate processing: `rm -rf processing_output/intermediate_processing/*`

Keep permanently:
1. Darwin Core metadata: `processing_output/darwin_core_metadata/`
2. Validation reports: `processing_output/validation_reports/`

## Next Steps

1. ✓ Create directory structure (setup_output_directories.sh)
2. Run detection pipeline (all 13 cameras)
3. Run timestamp validation (all 13 cameras)
4. Generate Darwin Core metadata (--organized-output mode)
5. Review and validate outputs
6. Archive/publish to repository

See `OUTPUT_DIRECTORY_STRUCTURE.md` for detailed structure information.
