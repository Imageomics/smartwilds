# Quick Start Guide: SmartWilds Drone SAM3 HF Pipeline

This guide walks through the most common ways to run the Hugging Face SAM3 drone pipeline and where to place outputs.

The source implementation lives in:

`/fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf`

A packaged copy of the documentation bundle lives in:

`/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline`

In that packaged copy:

- runnable SAM3 scripts are under `src/`
- supporting utility scripts are under `misc/`

## 1. One-Time Setup

### Choose an output root

The launcher defaults to:

`/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs`

Create it before first use if it does not already exist:

```bash
mkdir -p /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/slurm_logs
```

### Activate the expected environment

The Slurm launcher expects the `sam3` conda environment by default:

```bash
source /fs/ess/PAS2699/harvest_modules/miniconda3/bin/activate
conda activate sam3
```

## 2. Run One Drone Frame

```bash
python /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/predict_sam3_text.py \
    --run-mode image \
    --image-path /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250701_parrotanafi_1/20250703_parrotanafi_1_VID_002_frames/VID_002_000000.png \
    --output-json /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/single_image/VID_002_000000_hf_sam3.json \
    --viz-dir /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/single_image/hf_sam3_text_viz \
    --prompts animal person vehicle
```

Key outputs:

- JSON predictions for one frame
- one visualization image with drawn detections

## 3. Run One Drone Video Frame Set from a COCO Image List

```bash
python /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/predict_sam3_text.py \
    --run-mode coco \
    --coco-json /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames/VID_004_annotations.json \
    --image-root /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames \
    --output-json /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/VID_004_annotations_hf_sam3_text_predictions.json \
    --viz-dir /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_viz \
    --viz-every 10 \
    --batch-size 12 \
    --prompts animal person vehicle
```

Key outputs:

- one COCO-style predictions JSON
- visualization images every tenth frame

## 4. Enable BioCLIP Enrichment

```bash
python /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/predict_sam3_text.py \
    --run-mode coco \
    --coco-json /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames/VID_004_annotations.json \
    --image-root /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames \
    --output-json /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/VID_004_annotations_hf_sam3_text_predictions.json \
    --viz-dir /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_viz \
    --bioclip-viz-dir /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_bioclip_viz \
    --enable-bioclip \
    --bioclip-device cpu \
    --bioclip-batch-size 16 \
    --prompts animal person vehicle
```

Additional outputs:

- each eligible `animal` detection gains a `bioclip` field
- BioCLIP-specific QA images are written under `bioclip_viz_dir`

## 5. Submit the Standard Slurm Launcher

The launcher is controlled by environment variables. Override only the values you need:

```bash
IMAGE_PATH=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250701_parrotanafi_1/20250703_parrotanafi_1_VID_002_frames/VID_002_000000.png \
RUN_MODE=image \
OUTPUT_JSON=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/single_image/VID_002_000000_hf_sam3.json \
VIZ_DIR=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/single_image/hf_sam3_text_viz \
sbatch /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/run_predict_sam3_text.sh
```

For COCO mode:

```bash
RUN_MODE=coco \
COCO_JSON=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames/VID_004_annotations.json \
IMAGE_ROOT=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames \
OUTPUT_JSON=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/VID_004_annotations_hf_sam3_text_predictions.json \
VIZ_DIR=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_viz \
sbatch /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/run_predict_sam3_text.sh
```

## 6. Chunk a Large Grouped Run

Use the chunking helper when a grouped image list is too large for one convenient job.

```bash
python /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/make_camera_trap_sam3_chunks.py \
    --summary-json /fs/scratch/PAS2136/smartwilds_detection/camera_trap_coco_image_list_summary.json \
    --chunk-summary-json /fs/scratch/PAS2136/smartwilds_detection/camera_trap_sam3_chunk_summary.json \
    --chunk-size 1000
```

This script:

- reads the grouped-run summary JSON
- creates per-chunk COCO files
- symlinks chunk-local image roots
- writes a chunk summary JSON for submission

## 7. Submit Chunked Jobs

```bash
CHUNK_SUMMARY_JSON=/fs/scratch/PAS2136/smartwilds_detection/camera_trap_sam3_chunk_summary.json \
bash /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/submit_camera_trap_chunks_predict_sam3_text.sh
```

## 8. Submit One Job Per Summary Record

```bash
SUMMARY_JSON=/fs/scratch/PAS2136/smartwilds_detection/camera_trap_coco_image_list_summary.json \
bash /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/submit_camera_traps_predict_sam3_text.sh
```

## 9. Quality Checks

```bash
python /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/predict_sam3_text.py --help
```

```bash
head -40 /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/VID_004_annotations_hf_sam3_text_predictions.json
```

```bash
ls /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_viz | head
```

## 10. Common Adjustments

- Increase `BATCH_SIZE` only after verifying GPU memory headroom.
- Set `RETURN_MASKS=1` or pass `--return-masks` only when mask payload size is acceptable.
- Use `BIOCLIP_DEVICE=cuda` only if you explicitly want BioCLIP to compete with SAM3 for GPU memory.
- Set `VIZ_EVERY=0` when you want predictions only and no QA images during grouped runs.

## 11. Misc Utilities In The Packaged Copy

The packaged `SAM3_detection_pipeline` bundle also includes:

- `misc/export_drone_detection_csv.py`
  - packaged copy of `export_drone_detection_simple_csv.py`

- `misc/vid_to_frame_coco.py`
  - helper for preparing frame directories and COCO image lists from drone videos
