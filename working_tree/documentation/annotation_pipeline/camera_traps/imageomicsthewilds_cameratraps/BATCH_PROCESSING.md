# Batch Processing Camera Trap Data

Two scripts for systematic processing of camera trap directories:

## 1. process_all_camera_traps.py

**Purpose**: Generate Darwin Core Events and Occurrences from all camera deployment metadata.

This script:
- Discovers all camera trap deployments in the dataset
- Generates `darwin_core_events.csv` (survey sessions)
- Generates `darwin_core_occurrences.csv` (species observations) from detections
- Creates `platform_specifications.json` (hardware specs)

### Quick Start

```bash
# Generate metadata from deployment information
python process_all_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-dir ./metadata_output

# Include detection data for occurrences
python process_all_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-dir ./metadata_output \
    --detections-dir ./detections_results
```

### Output

```
metadata_output/
├── darwin_core_events.csv          # All survey sessions
├── darwin_core_occurrences.csv     # All species observations
└── platform_specifications.json    # Hardware specifications
```

### What It Does

1. **Discovers all cameras** by finding directories matching `TW##-CT##`
2. **Maps campaigns** by examining directory names (20250630_20250703, 20250804_20250828, etc.)
3. **Generates events** from `camera_deployment_metadata.py`:
   - One row per camera deployment
   - Camera location (GPS), deployment dates, sampling protocol
   - Known issues and special notes

4. **Generates occurrences** from detections (if available):
   - One row per species detection
   - Animal location (GPS projected from depth estimation)
   - Links back to event via `eventID`
   - Detection confidence scores

## 2. batch_process_camera_traps.py

**Purpose**: Process camera trap directories through the complete pipeline in batch.

This script runs the full workflow for each camera:
1. Index images
2. Validate timestamps
3. Merge with detections
4. Generate metadata

### Quick Start - Single Directory

```bash
python batch_process_camera_traps.py \
    --image-dir /fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps \
    --output-dir ./results
```

### Quick Start - All Campaigns

```bash
python batch_process_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --find-campaigns \
    --output-dir ./results
```

### Advanced Options

```bash
# Process specific cameras matching pattern
python batch_process_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --find-campaigns \
    --camera-filter "TW02-*" \
    --output-dir ./results

# Resume from interrupted processing
python batch_process_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --find-campaigns \
    --continue-from TW06-CT05 \
    --output-dir ./results

# Skip certain processing steps
python batch_process_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --find-campaigns \
    --skip-steps indexing validation \
    --output-dir ./results

# Parallel processing (experimental)
python batch_process_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --find-campaigns \
    --parallel 4 \
    --output-dir ./results
```

### Output Structure

```
results/
├── thewilds_20250630_20250703/
│   ├── TW01-CT02/
│   │   ├── index.csv
│   │   ├── events_validated.csv
│   │   ├── detections_with_validated_timestamps.csv
│   │   ├── darwin_core_events.csv
│   │   ├── darwin_core_occurrences.csv
│   │   └── annotated/
│   ├── TW02-CT03/
│   │   └── ...
│   └── ...
├── thewilds_20250804_20250828/
│   ├── TW01-CT02/
│   │   └── ...
│   └── ...
└── processing_report.json
```

## Processing Report

Each batch run generates `processing_report.json`:

```json
{
  "timestamp": "2026-03-17T12:34:56.789...",
  "total_processed": 13,
  "successes": 12,
  "failures": 1,
  "cameras_processed": [
    "thewilds_20250630_20250703/TW01-CT02",
    "thewilds_20250630_20250703/TW02-CT03",
    ...
  ]
}
```

## Workflow Comparison

### process_all_camera_traps.py
- **Input**: Deployment metadata + detections CSVs
- **Output**: Single consolidated Events/Occurrences CSVs
- **Use case**: Final metadata generation for publication
- **Speed**: Very fast (minutes)
- **Outputs per directory**: 1 combined CSV

### batch_process_camera_traps.py
- **Input**: Raw camera directories
- **Output**: Per-camera index, events, occurrences
- **Use case**: Complete workflow from images to metadata
- **Speed**: Slower (hours for large datasets)
- **Outputs per directory**: Multiple CSVs

## Typical Workflow

### Option 1: Quick Metadata Generation (Recommended)

Use `process_all_camera_traps.py` if you already have:
- Validated timestamp CSVs
- Detections CSVs
- Deployment metadata

```bash
python process_all_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-dir ./final_metadata \
    --detections-dir /path/to/detections_results
```

**Time**: ~5 minutes
**Output**: Publication-ready CSVs

### Option 2: Complete Workflow

Use `batch_process_camera_traps.py` if you need to:
- Start from raw images
- Run full validation pipeline
- Generate all intermediate files

```bash
python batch_process_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --find-campaigns \
    --output-dir ./complete_results
```

**Time**: ~1-2 hours (depending on image count)
**Output**: All intermediate + final files per camera

## Troubleshooting

### Missing Deployments in Events

Check that deployments are defined in:
```python
/src/01_events/camera_deployment_metadata.py
```

Add missing deployments with GPS coordinates and date ranges.

### No Occurrences Generated

Ensure detections file exists with correct name:
```
detections_with_validated_timestamps.csv
```

If detections haven't been run yet, use:
```bash
python bharaths_scripts/camera_trap_detections.py \
    --weights yolov8x.pt \
    --images /path/to/images \
    --csv-out detections.csv \
    ...
```

### Reprocessing Specific Cameras

To regenerate metadata for specific cameras:

```bash
# Reprocess just august campaign
python batch_process_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --find-campaigns \
    --camera-filter "TW*" \
    --skip-steps indexing validation \
    --output-dir ./results_v2
```

## Performance

- **Image indexing**: ~1000 images/minute
- **Timestamp validation**: ~500 images/minute
- **Metadata generation**: ~1000 records/minute

For ~243k images across all campaigns:
- Sequential: ~30 minutes
- With parallel workers: ~5-10 minutes (depending on hardware)

## Next Steps After Generation

1. **Review**: Check generated CSVs for accuracy
2. **Validate**: Run GBIF validation on occurrences
3. **Publish**: Upload to Zenodo/GBIF/HuggingFace
4. **Document**: Add to dataset card

See `EVENTS_VS_OCCURRENCES.md` for output format details.
