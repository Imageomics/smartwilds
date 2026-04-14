# SmartWilds Drone Processing Pipeline - Complete Documentation

Comprehensive documentation for the Hugging Face SAM3 text-prompted detection workflow used on SmartWilds drone imagery, including optional BioCLIP enrichment and Slurm-based batch execution.

## Overview

This pipeline processes either a single drone frame or a COCO image list through three main stages:

1. `predict_sam3_text.py` runs Hugging Face SAM3 text-guided instance segmentation and converts detections into JSON output.
2. `bioclip_helper.py` optionally adds zero-shot BioCLIP predictions for detections whose prompt category is `animal`.
3. `utils.py` renders visualization images for periodic quality checks.

## What Is Included

### Core inference path

- `predict_sam3_text.py`
  - accepts `image` or `coco` run modes
  - validates input paths before execution
  - writes either a single-image JSON payload or a COCO-style predictions file
  - supports configurable prompts, thresholds, masks, and visualization cadence

- `hf_sam3_detector.py`
  - wraps `transformers.Sam3Model` and `Sam3Processor`
  - runs each prompt independently across the batch
  - merges prompt-level detections with NMS

- `bioclip_helper.py`
  - lazily loads `bioclip.CustomLabelsClassifier`
  - crops only `animal` detections by default
  - adds top-k zero-shot predictions under each detection's `bioclip` field

- `utils.py`
  - draws bounding boxes
  - overlays masks when available
  - adds BioCLIP label text when enrichment is present

### Launch and orchestration

- `run_predict_sam3_text.sh`
  - standard Slurm launcher for the Python entry point
  - sets the conda environment, device, prompts, thresholds, input paths, and output paths through environment variables

- `submit_camera_traps_predict_sam3_text.sh`
  - submits one Slurm job per summary record
  - skips missing inputs, existing outputs, and already queued jobs

- `make_camera_trap_sam3_chunks.py`
  - splits large COCO image lists into fixed-size chunks
  - creates symlinked chunk-local image roots
  - writes a chunk summary JSON used for downstream submission

- `submit_camera_trap_chunks_predict_sam3_text.sh`
  - submits one Slurm job per chunk record
  - uses the same Slurm launcher as the single-run path

### Packaged documentation bundle

A packaged copy of this material lives at:

`/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline`

That package is organized as:

- root: markdown documentation
- `src/`: runnable SAM3 pipeline scripts and helper modules
- `misc/`: extra supporting utilities copied into the package

### Misc utilities in the packaged copy

- `misc/export_drone_detection_csv.py`
  - packaged copy of `export_drone_detection_simple_csv.py`
  - useful for exporting simplified drone detection CSV views alongside SAM3 outputs

- `misc/vid_to_frame_coco.py`
  - utility for turning drone video inputs into frame directories and COCO image-list inputs for grouped runs

## Quick Start Paths

### Path 1: Run one drone image

```bash
python /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/predict_sam3_text.py \
    --run-mode image \
    --image-path /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250701_parrotanafi_1/20250703_parrotanafi_1_VID_002_frames/VID_002_000000.png \
    --output-json /tmp/VID_002_000000_hf_sam3.json \
    --viz-dir /tmp/hf_sam3_viz \
    --prompts animal person vehicle
```

### Path 2: Run one COCO image list directly

```bash
python /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/predict_sam3_text.py \
    --run-mode coco \
    --coco-json /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames/VID_004_annotations.json \
    --image-root /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames \
    --output-json /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/VID_004_annotations_hf_sam3_text_predictions.json \
    --viz-dir /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_viz \
    --prompts animal person vehicle
```

### Path 3: Submit one Slurm job with the standard launcher

```bash
sbatch /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/run_predict_sam3_text.sh
```

### Path 4: Chunk and submit a large grouped run

```bash
python /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/make_camera_trap_sam3_chunks.py \
    --summary-json /fs/scratch/PAS2136/smartwilds_detection/camera_trap_coco_image_list_summary.json \
    --chunk-summary-json /fs/scratch/PAS2136/smartwilds_detection/camera_trap_sam3_chunk_summary.json \
    --chunk-size 1000

bash /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/submit_camera_trap_chunks_predict_sam3_text.sh
```

## Data Flow

```
Drone frame or COCO image list
        |
        v
predict_sam3_text.py
        |
        +-- HuggingFaceSAM3TextDetector
        |     - prompt-wise SAM3 inference
        |     - thresholding
        |     - NMS merge
        |
        +-- optional BioClipHelper
        |     - crop animal detections
        |     - zero-shot classification
        |
        +-- optional draw_detections
              - SAM3 overlays
              - BioCLIP overlays
        |
        v
JSON predictions + QA visualizations
```

## Output Formats

### Single-image mode

`predict_sam3_text.py --run-mode image` writes a JSON object with:

- `image`
- `model_id`
- `prompts`
- `detections`

Each detection contains:

- `xyxy`
- `score`
- `category_id`
- `category_name`
- optional `mask`
- optional `bioclip`

### COCO mode

`predict_sam3_text.py --run-mode coco` writes a COCO-like JSON document with:

- `images`
- `categories`
- `annotations`

Each output annotation contains:

- `id`
- `image_id`
- `category_id`
- `category_name`
- `bbox`
- `area`
- `score`
- `iscrowd`
- optional `mask`
- optional `bioclip`

## Important Operational Behavior

### Prompt handling

- prompts default to `animal person vehicle`
- each prompt is run independently against the whole batch
- category IDs are assigned in prompt order, starting at `1`

### Visualization cadence

- image mode writes one SAM3 visualization when `viz_dir` is provided
- COCO mode writes visualizations every `viz_every` images
- BioCLIP visualizations are only written when enrichment is enabled and predictions were attached

### BioCLIP defaults

- enabled only when requested
- default species list:
  - `aves with common name bird`
  - `Mammalia with common name mammal`
- GPU SAM3 runs default BioCLIP onto CPU unless overridden

### Fault tolerance

- missing images in COCO mode are skipped with a message
- unreadable images are skipped with a message
- detector and BioCLIP resources are cleaned up in `finally` blocks

## Batch Helpers With Legacy Names

The scripts `submit_camera_traps_predict_sam3_text.sh`, `make_camera_trap_sam3_chunks.py`, and `submit_camera_trap_chunks_predict_sam3_text.sh` still carry `camera_trap` in their names. In this directory they act as generic grouped-run orchestration helpers around the same SAM3 entry point.

They assume an upstream summary JSON schema with records that contain image-root and COCO-path information, and they write outputs under a grouped directory rooted at `BASE_OUTPUT_ROOT`.
