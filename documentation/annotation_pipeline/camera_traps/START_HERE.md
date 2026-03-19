# Camera Trap Processing Pipeline - Complete Package

## What's Been Completed

Your three explicit requests from Message 9 have now been fully addressed:

### 1. ✓ Detection Config File
- **File**: `detection_config.json`
- **Status**: Complete and ready for use
- **Contains**: All 13 camera deployments with:
  - Image directory paths
  - Camera hardware specifications (3 models)
  - GPS coordinates (4 cameras complete, 8 need data entry)
  - Known issues and timestamp corrections
  - Expected image counts and deployment dates

### 2. ✓ Organized Directory Structure
- **Created files**:
  - `OUTPUT_DIRECTORY_STRUCTURE.md` - Detailed specification
  - `setup_output_directories.sh` - Automated setup script
  - `ORGANIZED_OUTPUT_QUICKSTART.md` - Usage guide

- **Structure includes**:
  - `annotated_images/` - Detection visualizations (13 cameras × 2 campaigns)
  - `darwin_core_metadata/` - FAIR² compliant metadata (2 campaigns)
  - `intermediate_processing/` - Temporary validation files (13 cameras × 2 campaigns)
  - `validation_reports/` - Quality assurance summaries

- **Setup command**:
  ```bash
  ./setup_output_directories.sh --base-dir /fs/ess/PAS2136/TheWilds2025
  ```

### 3. ✓ Computational Node Allocation
- **File**: `COMPUTATIONAL_NODE_REQUIREMENTS.md`
- **Covers**:
  - Hardware specifications (GPU, CPU, memory, storage)
  - Three deployment strategies with timing estimates
  - HPC submission script templates (Slurm/PBS/SGE)
  - Cloud provider options (AWS, Azure) with cost estimates
  - Performance benchmarks for each component
  - Failure recovery and monitoring strategies

- **Recommended approach**: Single GPU node (1x A100), sequential camera processing
  - Time: 45-60 minutes
  - Cost: $0.75-3 USD
  - Reliability: High (simple, minimal dependencies)

## Documentation Provided

All files in: `/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps/`

### Getting Started (Read First)
1. **`README_COMPLETE_PIPELINE.md`** ← START HERE
   - Overview of entire pipeline
   - Quick start paths
   - Directory structure summary
   - Processing workflow

### Before Running (Detailed References)
2. **`OUTPUT_DIRECTORY_STRUCTURE.md`**
   - Detailed directory layout specification
   - File organization details
   - Workflow integration points

3. **`COMPUTATIONAL_NODE_REQUIREMENTS.md`**
   - Hardware specifications
   - Deployment options with timing/cost
   - HPC submission templates
   - Storage planning

4. **`ORGANIZED_OUTPUT_QUICKSTART.md`**
   - Step-by-step command examples
   - Configuration reference
   - Batch processing examples
   - Publishing workflow

### Processing Pipeline Reference
5. **`BATCH_PROCESSING.md`** - Batch processing guide
6. **`README_PIPELINE.md`** - Complete data flow
7. **`README_METADATA.md`** - Darwin Core standard details
8. **`EVENTS_VS_OCCURRENCES.md`** - Conceptual diagrams
9. **`README_VALIDATION.md`** - Timestamp validation
10. **`README_MERGE.md`** - Detection merge specification

## Files Ready to Use

### Configuration
- **`detection_config.json`**
  - Ready to use for detection pipeline
  - Status: 4/13 cameras with GPS coordinates
  - Action needed: Fill omitted GPS for 8 cameras

### Scripts
- **`process_all_camera_traps.py`** (UPDATED)
  - New `--organized-output` flag for campaign-organized structure
  - Automatically creates campaign subdirectories
  - Still supports consolidated output (legacy mode)

- **`batch_process_camera_traps.py`** - Full pipeline orchestration (existing)
- **`run_batch_processing.sh`** - Shell wrapper (existing)

### Setup
- **`setup_output_directories.sh`** (NEW)
  - One-command setup for entire directory structure
  - Creates all 13 camera subdirectories
  - Sets permissions automatically

## Processing Stages Summary

```
Stage 1: Detection (GPU Required)         ← Computational node allocation needed here
├── Input: 243k raw JPG images
├── Process: YOLO + SAHI + BioCLIP
├── Time: 45-60 min (single A100 GPU)
└── Output: detections.csv + annotated_images/

Stage 2: Validation (CPU, Single Node)
├── Input: detection_config.json + raw images
├── Process: Timestamp extraction + validation
├── Time: 5-10 min
└── Output: events_validated.csv

Stage 3: Metadata (CPU, Single Node)
├── Input: events_validated.csv + detections.csv
├── Process: Generate Darwin Core Events + Occurrences
├── Time: 1-2 min
└── Output: darwin_core_*.csv + platform_specs
```

## Immediate Action Items

### Step 1: Create Directory Structure
```bash
cd /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps
./setup_output_directories.sh --base-dir /fs/ess/PAS2136/TheWilds2025
```

Result: Full directory tree created at `/fs/ess/PAS2136/TheWilds2025/processing_output/`

### Step 2: Plan Computational Resources
1. Read: `COMPUTATIONAL_NODE_REQUIREMENTS.md`
2. Determine: Which HPC cluster/cloud provider?
3. Decide: Single GPU (sequential) or Multi-GPU (parallel)?
4. Create: Slurm/PBS job submission script using provided templates

### Step 3: Prepare Detection Pipeline
1. Obtain: YOLOv8X model weights (`yolov8x.pt`)
2. Ensure: camera_trap_detections.py script is available
3. Configure: BioCLIP labels in detection_config.json (already done)

### Step 4: Submit Compute Job
Use template from COMPUTATIONAL_NODE_REQUIREMENTS.md:
```bash
sbatch camera_detections.slurm
# Monitor with: squeue -u $USER
```

### Step 5: Generate Metadata
After detections complete:
```bash
python process_all_camera_traps.py \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-dir /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata \
    --detections-dir /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing \
    --organized-output
```

Result: Darwin Core CSVs organized by campaign in `darwin_core_metadata/`

## Storage Estimate

After full pipeline completion:

| Component | Size | Keep? |
|-----------|------|-------|
| Annotated images | ~500 GB | Optional (visual QA) |
| Darwin Core metadata | ~50 MB | **Yes** (publication) |
| Intermediate files | ~100 GB | Optional (audit trail) |
| Validation reports | ~10 MB | **Yes** (QA documentation) |
| **Total** | **~650 GB** | |

Minimal setup keeps only: Darwin Core + Validation reports = ~60 MB

## Key Documents by Use Case

| Goal | Read This |
|------|-----------|
| Understand overall pipeline | `README_COMPLETE_PIPELINE.md` |
| Set up directories | `OUTPUT_DIRECTORY_STRUCTURE.md` + `setup_output_directories.sh` |
| Request GPU compute time | `COMPUTATIONAL_NODE_REQUIREMENTS.md` |
| Run full workflow | `ORGANIZED_OUTPUT_QUICKSTART.md` |
| Understand Darwin Core format | `README_METADATA.md` + `EVENTS_VS_OCCURRENCES.md` |
| Debug timestamp issues | `README_VALIDATION.md` |
| Plan storage/architecture | `OUTPUT_DIRECTORY_STRUCTURE.md` |

## What's Ready vs. What's Next

### Ready Today ✓
- Configuration file (detection_config.json)
- Directory structure template (setup_output_directories.sh)
- Documentation (all guides and reference material)
- Enhanced batch scripts (process_all_camera_traps.py with --organized-output)

### Next: Requires Your Action
- Confirm which HPC cluster/cloud provider to use
- Fill in missing GPS coordinates (8 cameras) in detection_config.json
- Request compute allocation (GPU node time)
- Run detection pipeline (camera_trap_detections.py)
- Run metadata generation (process_all_camera_traps.py)

## Estimated Timeline

Once GPU access is confirmed:

| Task | Time | Who |
|------|------|-----|
| Setup directories | 2 min | Automated (script) |
| Fill missing GPS coords | 30 min | Manual |
| Submit detection job | 5 min | You |
| Run detections | 60 min | HPC cluster |
| Generate metadata | 2 min | Single CPU |
| **Total Wall Time** | **~2 hours** | **Mostly waiting** |

## Questions?

Each component has detailed documentation:

- **"How do I set up directories?"** → `OUTPUT_DIRECTORY_STRUCTURE.md`
- **"What hardware do I need?"** → `COMPUTATIONAL_NODE_REQUIREMENTS.md`
- **"What do the output CSVs look like?"** → `README_METADATA.md` + `EVENTS_VS_OCCURRENCES.md`
- **"How do I run the full workflow?"** → `ORGANIZED_OUTPUT_QUICKSTART.md`
- **"Why are Events and Occurrences separate?"** → `EVENTS_VS_OCCURRENCES.md`

---

**Status**: All explicit requests from Message 9 completed
**Ready for**: GPU node allocation and detection execution
**Documentation**: Comprehensive (11 markdown files + shell script)
**Next step**: Confirm HPC cluster and GPU allocation
