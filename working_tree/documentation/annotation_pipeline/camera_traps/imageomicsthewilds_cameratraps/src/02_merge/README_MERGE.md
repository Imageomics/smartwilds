# Merging Events and Detections

This document describes how to combine validated camera trap event timestamps with YOLO/BioCLIP detection results.

## Overview

After running detections with `camera_trap_detections.py`, you have two separate data streams:

1. **Detections** (from `camera_trap_detections.py`):
   - YOLO object detection results
   - BioCLIP species classification
   - Confidence scores
   - GPS-projected detection coordinates
   - Estimated distance/angle

2. **Validated Events** (from `make_events_validated.py`):
   - Corrected timestamps (with fixes for known camera issues)
   - Validation flags for manual review
   - Evidence of timestamp source (filename vs EXIF)

The merge combines these, enriching detections with validated timestamps and quality flags.

## Output Schema

`detections_with_validated_timestamps.csv` contains:

### Identification Columns
| Column | Source | Description |
|--------|--------|-------------|
| image | Detections | Image filename |
| image_path | Detections | Full path to image |
| site_cam | Events | Camera identifier (e.g., TW02-CT01) |
| session | Events | Deployment session |

### Timestamp Columns (Primary)
| Column | Source | Description |
|--------|--------|-------------|
| timestamp | Events | **Final timestamp** (corrected if needed) |
| timestamp_source | Events | How timestamp was extracted: 'filename', 'exif', or 'corrected' |
| validation_flag | Events | Reason for manual review (if any) |

### Timestamp Columns (Reference)
| Column | Source | Purpose |
|--------|--------|---------|
| timestamp_file | Detections | Original file modification time (mtime) |
| timestamp_from_name | Detections | Timestamp as parsed from filename (may be incorrect) |

### Detection Results
| Column | Source | Description |
|--------|--------|-------------|
| detection_index | Detections | Detection number within image |
| bioclip_label | Detections | Species classification (deer/bird) |
| bioclip_score | Detections | BioCLIP confidence (0-1) |
| yolo_conf | Detections | YOLO detection confidence (0-1) |

### Bounding Box Coordinates
| Column | Source | Description |
|--------|--------|-------------|
| xmin, ymin | Detections | Top-left corner of detection box |
| xmax, ymax | Detections | Bottom-right corner of detection box |

### Distance & Angle
| Column | Source | Description |
|--------|--------|-------------|
| distance_m | Detections | Estimated distance to animal (meters) |
| angle_deg | Detections | Relative horizontal angle from camera center (degrees) |

### GPS Coordinates
| Column | Source | Description |
|--------|--------|-------------|
| camera_lat, camera_lon | Detections | Camera position |
| camera_bearing_deg | Detections | Direction camera is facing (degrees from North) |
| animal_lat, animal_lon | Detections | Estimated animal position (GPS projected) |
| animal_absolute_bearing_deg | Detections | Absolute bearing to animal (degrees from North) |

## Usage

### Basic Merge

```bash
python merge_detections_and_events.py \
    --events ../01_events/events_validated.csv \
    --detections detections_raw.csv \
    --output detections_with_validated_timestamps.csv
```

### In a Pipeline

```bash
# After running camera_trap_detections.py to generate detections_raw.csv
# and make_events_validated.py to generate events_validated.csv:

python merge_detections_and_events.py \
    --events ../01_events/events_validated.csv \
    --detections detections_raw.csv \
    --output detections_with_validated_timestamps.csv
```

## Handling Unmatched Records

If a detection record doesn't match an event:
- This is unusual and indicates a path mismatch
- Check that:
  - Both pipelines processed images from the same directory tree
  - Image paths in the CSV are consistent
  - No images were skipped in the events pipeline

If >1% of records are unmatched, review the merge logs.

## Working with Flagged Detections

Filter for manual review:

```python
import pandas as pd

merged = pd.read_csv('detections_with_validated_timestamps.csv')

# Find all flagged detections
flagged = merged[merged['validation_flag'].notna()]

# Filter by flag type
exif_mismatch = merged[
    merged['validation_flag'].str.contains('EXIF_MISMATCH', na=False)
]

corrected = merged[
    merged['validation_flag'].str.contains('CORRECTED', na=False)
]

# Export for manual review
flagged.to_csv('detections_for_manual_review.csv', index=False)
```

## Quality Checks

The merge provides evidence for quality assessment:

1. **Timestamp Coverage**: How many detections match validated events?
2. **Validation Flags**: How many images had timestamp issues?
3. **Data Consistency**: Do timestamp sources align with expected confidence?

Example analysis:

```python
import pandas as pd

merged = pd.read_csv('detections_with_validated_timestamps.csv')

# Coverage by camera
print("Detection-Event Match Rate by Camera:")
for camera in merged['site_cam'].unique():
    cam_data = merged[merged['site_cam'] == camera]
    matched = cam_data['timestamp'].notna().sum()
    total = len(cam_data)
    pct = 100 * matched / total if total > 0 else 0
    print(f"  {camera}: {matched}/{total} ({pct:.1f}%)")

# Flagged detection statistics
print("\nDetections with Validation Flags:")
print(f"  Total: {merged['validation_flag'].notna().sum()}")
print(f"  By flag type:")
for flag in merged['validation_flag'].str.split(';').str[0].unique():
    if pd.notna(flag):
        count = merged['validation_flag'].str.startswith(flag.strip()).sum()
        print(f"    {flag.strip()}: {count}")
```

## Pipeline Integration

This merge is typically step 2 in the post-processing pipeline:

1. **Index images** → `index.csv` (00_indexing/index_images.py)
2. **Extract & validate events** → `events_validated.csv` (01_events/make_events_validated.py)
3. **Run detections** → `detections_raw.csv` (camera_trap_detections.py - separate tool)
4. **Merge results** → `detections_with_validated_timestamps.csv` (merge_detections_and_events.py)
5. **Analyze** → temporal patterns, species distributions, etc. (02_analysis/)

## Troubleshooting

### Few/No Matches in Merge

**Problem**: Most detections don't match events

**Causes**:
- Image indexing used different directory structure than detections
- Path separators inconsistent (/ vs \)
- Different versions of datasets

**Solution**:
- Print sample paths from both CSV files
- Ensure both pipelines use exact same source directory
- Normalize paths: `df['path'] = df['path'].str.replace('\\', '/')`

### Missing Validation Flags in Key Detections

**Problem**: Some images should be flagged but aren't

**Causes**:
- Image is outside events date range (skipped in events pipeline)
- Camera not in deployment metadata

**Solution**:
- Update `camera_deployment_metadata.py` with all camera info
- Verify that metadata.txt files have been read and processed
- Check events CSV for images in the deployment range

### Timestamp Source Inconsistency

**Problem**: Most detections show `timestamp_source=filename` but you expected EXIF

**Causes**:
- Camera settings stamp filename with timestamp (most cameras do this)
- EXIF parsing may have failed for image format issues

**Solution**:
- Review a sample of images with EXIF readers
- Check logs from `make_events_validated.py` for EXIF errors
- This is usually expected/correct behavior
