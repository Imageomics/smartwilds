# TheWilds 2025 Camera Trap Processing Pipeline - Complete Documentation

Comprehensive documentation for processing 243,000 camera trap images across 13 deployments into FAIR² compliant Darwin Core biodiversity metadata.

## Overview

This pipeline processes raw camera trap images through three main stages:

1. **Detection Phase**: YOLO + SAHI + BioCLIP (object detection, species classification, depth estimation)
2. **Validation Phase**: Timestamp extraction, EXIF validation, camera clock correction
3. **Metadata Phase**: Darwin Core Events (survey sessions) + Occurrences (species observations) generation

## What's Been Created

### Core Configuration

- **`detection_config.json`** (NEW)
  - Comprehensive configuration for all 13 camera deployments
  - Includes device specifications, geometry, GPS coordinates, known issues
  - Ready for feeding into YOLO detection pipeline
  - Status: 4 cameras with complete GPS, 8 cameras need coordinate extraction

### Output Directory Structure (NEW)

- **`OUTPUT_DIRECTORY_STRUCTURE.md`**
  - Detailed specification of organized directory layout
  - Recommended structure for storing:
    - Annotated images (detection visualizations)
    - Darwin Core metadata (FAIR² compliant)
    - Intermediate processing files
    - Validation reports

- **`setup_output_directories.sh`** (NEW)
  - Automated script to create entire directory structure
  - Creates per-camera subdirectories for 13 deployments × 2 campaigns
  - Sets proper permissions and creates inventory manifest

- **`ORGANIZED_OUTPUT_QUICKSTART.md`** (NEW)
  - Step-by-step guide for using organized directories
  - Includes example commands for each pipeline stage
  - Batch processing examples
  - Publishing workflow

### Computational Infrastructure (NEW)

- **`COMPUTATIONAL_NODE_REQUIREMENTS.md`** (NEW)
  - Detailed hardware specifications for GPU and CPU processing
  - Three deployment options:
    - Single GPU (sequential): 45-60 minutes
    - Multi-GPU (parallel): 15-20 minutes
    - Job array (distributed): scales with available nodes
  - HPC submission script templates (Slurm/PBS/SGE)
  - Cloud provider options (AWS/Azure) with cost estimates
  - Storage requirements and optimization strategies

### Enhanced Scripts

- **`process_all_camera_traps.py`** (UPDATED)
  - Added `--organized-output` flag
  - Creates campaign-organized subdirectories automatically
  - Now supports both consolidated and organized output modes
  - Properly connects to detection pipeline results

### Documentation

- **`README_PIPELINE.md`** - Complete pipeline workflow
- **`README_VALIDATION.md`** - Timestamp validation system
- **`README_MERGE.md`** - Events-detections merge specification
- **`README_METADATA.md`** - Darwin Core standard + FAIR² compliance
- **`EVENTS_VS_OCCURRENCES.md`** - Conceptual diagrams and examples
- **`BATCH_PROCESSING.md`** - Batch processing workflow guide
- **`BATCH_PROCESSING_GUIDE.md`** - Quick start paths

## Quick Start Paths

### Path 1: Setup and Execute (Recommended)

```bash
# 1. Create directory structure
cd /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps
./setup_output_directories.sh --base-dir /fs/ess/PAS2136/TheWilds2025

# 2. Request GPU node (see COMPUTATIONAL_NODE_REQUIREMENTS.md)
sbatch camera_detections.slurm

# 3. Generate Darwin Core metadata
python process_all_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-dir /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata \
    --detections-dir /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing \
    --organized-output
```

### Path 2: Understand Structure First

Read in order:
1. `OUTPUT_DIRECTORY_STRUCTURE.md` - Understand the layout
2. `ORGANIZED_OUTPUT_QUICKSTART.md` - See example workflows
3. `COMPUTATIONAL_NODE_REQUIREMENTS.md` - Plan your compute resources
4. Run `setup_output_directories.sh`

### Path 3: Deep Dive

Read these for complete context:
1. `COMPUTATIONAL_NODE_REQUIREMENTS.md` - Hardware spec details
2. `detection_config.json` - Camera-specific configuration
3. `BATCH_PROCESSING.md` - Full batch pipeline details
4. `README_PIPELINE.md` - Complete data flow
5. `EVENTS_VS_OCCURRENCES.md` - Darwin Core standard reference

## Directory Structure Summary

After running `setup_output_directories.sh`:

```
/fs/ess/PAS2136/TheWilds2025/processing_output/
├── annotated_images/            [~500 GB] Detection visualizations
│   ├── 20250630_20250703/       [4 cameras]
│   └── 20250804_20250828/       [9 cameras]
│
├── darwin_core_metadata/        [~50 MB] FAIR² compliant metadata
│   ├── 20250630_20250703/
│   │   ├── darwin_core_events.csv
│   │   ├── darwin_core_occurrences.csv
│   │   └── platform_specifications.json
│   └── 20250804_20250828/
│       ├── darwin_core_events.csv
│       ├── darwin_core_occurrences.csv
│       └── platform_specifications.json
│
├── intermediate_processing/     [~100 GB] Temporary/validation files
│   ├── 20250630_20250703/
│   └── 20250804_20250828/
│
└── validation_reports/          [~10 MB] Quality metrics
    ├── timestamp_validation_report.csv
    ├── detection_quality_metrics.json
    ├── missing_coordinates_report.csv
    └── processing_errors.log
```

## Node Allocation Summary

### Quick Reference Table

| Approach | Hardware | Time | Cost | Best For |
|----------|----------|------|------|----------|
| Single GPU | 1x A100 + 16 CPU | 45-60 min | $0.75-3 | Simple, reliable |
| Multi-GPU | 4x A100 + 32 CPU | 15-20 min | $3-12 | Faster execution |
| CPU-only | 32-64 cores | 4-8 hours | $2-4 | Budget-conscious |
| Job array | 13 GPUs (distributed) | ~12 min | $10-15 | Maximum parallelism |

### Recommended: Single GPU on HPC

**Why**:
- Simple to submit and debug
- Reliable execution
- Cost-effective (~$1-3 total)
- Reasonable wall time (1 hour)

**Submission Template** (Slurm):
```bash
#!/bin/bash
#SBATCH --job-name=camera_detections
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=2:00:00

# Your detection script here
python camera_trap_detections.py ...
```

See `COMPUTATIONAL_NODE_REQUIREMENTS.md` for full details.

## Processing Workflow

### Stage 1: Detections (GPU Required)

Input: Raw JPG images from 13 camera locations
Processing: YOLO object detection + BioCLIP species classification + depth estimation
Output: Detection CSV + annotated images (bounding boxes drawn)
Time: ~45-60 minutes on single A100 GPU
Location: `processing_output/intermediate_processing/{campaign}/{camera}/`

### Stage 2: Timestamp Validation

Input: Raw images + detection_config.json
Processing: Extract timestamps, validate against deployment dates, apply corrections
Output: events_validated.csv with validation flags
Time: ~5-10 minutes (CPU)
Location: `processing_output/intermediate_processing/{campaign}/{camera}/`

### Stage 3: Metadata Generation

Input: detection_config.json + events_validated.csv + detections.csv
Processing: Generate Darwin Core Events (survey sessions) + Occurrences (observations)
Output: darwin_core_events.csv + darwin_core_occurrences.csv + platform_specifications.json
Time: ~1-2 minutes
Location: `processing_output/darwin_core_metadata/{campaign}/`

## Data Flow Diagram

```
Raw Camera Images (243k JPGs)
         ↓
    [DETECTION PIPELINE]
    YOLO + SAHI + BioCLIP
         ↓
Detections {detection_config.json}
- Bounding boxes (YOLO)
- Species classifications (BioCLIP)
- Annotated images
- Animal locations (depth estimation)
         ↓
    [VALIDATION PIPELINE]
    Timestamp extraction & correction
         ↓
Validated Events + Detections
- Images with corrected timestamps
- Validation flags
- Handling of known camera issues
         ↓
    [METADATA PIPELINE]
    Darwin Core generation
         ↓
Publication-Ready FAIR² Metadata
- darwin_core_events.csv (13 survey sessions)
- darwin_core_occurrences.csv (100k+ observations)
- platform_specifications.json (hardware specs)
```

## Key Decisions Made

### 1. Organized Output by Campaign

Output files hierarchical under campaign directories rather than monolithic consolidated CSVs.

**Why**: Better organization for publication, easier to re-process individual campaigns, aligned with data collection timeline.

### 2. Separate Events and Occurrences

Events = camera deployment sessions with survey-level metadata (camera location)
Occurrences = individual species observations (animal location projected from depth)

**Why**: Darwin Core standard, enables spatial analysis, transparent about what data comes from where.

### 3. GPU-Accelerated Detection

Recommend single GPU node for sequential camera processing.

**Why**: 45-60 minutes is acceptable, GPU cost is low ($0.75-3), simple to manage, easy to debug.

### 4. Preserved Intermediate Files

Keep validation CSVs but can safely delete:
- Annotated images (regeneratable)
- Detection CSVs (redundant with darwin_core_occurrences)

**Why**: Preserves audit trail, enables troubleshooting, while managing storage efficiently.

## Next Immediate Steps

### For User:

1. **Confirm HPC access**
   - Which cluster? (OSC, campus cluster, cloud provider?)
   - How much GPU time available?

2. **Initialize directory structure**
   ```bash
   ./setup_output_directories.sh --base-dir /fs/ess/PAS2136/TheWilds2025
   ```

3. **Prepare compute environment**
   - Download YOLOv8X weights: `yolov8x.pt`
   - Prepare detection script (camera_trap_detections.py)
   - Create HPC submission script

4. **Submit detection job**
   - Use template from COMPUTATIONAL_NODE_REQUIREMENTS.md
   - Monitor GPU usage during execution

5. **Generate Darwin Core metadata**
   ```bash
   python process_all_camera_traps.py --organized-output ...
   ```

6. **Validate outputs**
   - Check CSV row counts
   - Verify GPS coordinates populated
   - Review taxonomic names

7. **Publish to repository**
   - Upload darwin_core_metadata/ to Zenodo/GBIF/etc.
   - Archive with UUID and timestamp
   - Create dataset DOI

## File Locations

All files in: `/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps/`

### Configuration
- `detection_config.json` - Camera specs + deployment metadata

### Setup
- `setup_output_directories.sh` - Initialize directory structure

### Documentation
- `OUTPUT_DIRECTORY_STRUCTURE.md` - Detailed directory layout specification
- `ORGANIZED_OUTPUT_QUICKSTART.md` - Step-by-step usage guide
- `COMPUTATIONAL_NODE_REQUIREMENTS.md` - Hardware specs + HPC templates
- `BATCH_PROCESSING.md` - Full workflow documentation
- `README_PIPELINE.md` - Complete pipeline overview

### Scripts
- `process_all_camera_traps.py` (updated with --organized-output)
- `batch_process_camera_traps.py` (existing batch orchestration)
- `run_batch_processing.sh` (shell wrapper)

## Contact & Support

For questions about:
- **Directory structure**: See `OUTPUT_DIRECTORY_STRUCTURE.md`
- **Computational requirements**: See `COMPUTATIONAL_NODE_REQUIREMENTS.md`
- **Data format**: See `README_METADATA.md` and `EVENTS_VS_OCCURRENCES.md`
- **Processing workflow**: See `BATCH_PROCESSING.md`
- **Camera-specific issues**: See `detection_config.json` "known_issues" section

---

**Generated**: 2026-03-17
**Status**: Ready for deployment
**Next phase**: GPU node allocation and detection execution
