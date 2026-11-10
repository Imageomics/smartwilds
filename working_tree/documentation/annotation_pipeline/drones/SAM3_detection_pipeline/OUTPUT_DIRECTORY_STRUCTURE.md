# Output Directory Structure for SmartWilds Drone SAM3 HF Inference

This document describes the expected input and output layout for the Hugging Face SAM3 drone detection pipeline.

## Documentation Bundle Layout

The packaged documentation bundle at:

`/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline`

is organized as:

```
SAM3_detection_pipeline/
|-- README.md
|-- START_HERE.md
|-- README_COMPLETE_PIPELINE.md
|-- ORGANIZED_OUTPUT_QUICKSTART.md
|-- OUTPUT_DIRECTORY_STRUCTURE.md
|-- COMPUTATIONAL_NODE_REQUIREMENTS.md
|-- src/
|   |-- predict_sam3_text.py
|   |-- hf_sam3_detector.py
|   |-- bioclip_helper.py
|   |-- utils.py
|   |-- run_predict_sam3_text.sh
|   |-- submit_camera_traps_predict_sam3_text.sh
|   |-- make_camera_trap_sam3_chunks.py
|   `-- submit_camera_trap_chunks_predict_sam3_text.sh
`-- misc/
    |-- export_drone_detection_csv.py
    `-- vid_to_frame_coco.py
```

The `misc/` scripts are supporting utilities and are not part of the main SAM3 inference path.

## Recommended Directory Structure

```
/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/
|
|-- 20250701_parrotanafi_1/
|   |-- 20250703_parrotanafi_1_VID_002_frames/
|   |   |-- VID_002_000000.png
|   |   |-- VID_002_000015.png
|   |   `-- VID_002_annotations.json
|   `-- ...
|
|-- 20250703_parrotanafi_5/
|   `-- 20250703_parrotanafi_5_VID_004_frames/
|       |-- VID_004_000000.png
|       |-- VID_004_000015.png
|       `-- VID_004_annotations.json
|
`-- outputs/
    |-- sam3_hf_outputs/
    |   |-- slurm_logs/
    |   |-- single_image/
|   |   |-- VID_002_000000_hf_sam3.json
    |   |   `-- hf_sam3_text_viz/
    |   |
    |   |-- 20250703_parrotanafi_5/
    |   |   `-- 20250703_parrotanafi_5_VID_004/
    |   |       |-- VID_004_annotations_hf_sam3_text_predictions.json
    |   |       |-- hf_sam3_text_viz/
    |   |       `-- hf_sam3_text_bioclip_viz/
    |   |
    |   `-- grouped_runs/
    |       `-- ...
    |
    |-- sam3_outputs/
    |-- yoloe_outputs/
    `-- image_based_outputs/
```

## Input Layout

### Image mode

`predict_sam3_text.py --run-mode image` expects:

- one image path passed to `--image-path`

### COCO mode

`predict_sam3_text.py --run-mode coco` expects:

- a COCO JSON passed to `--coco-json`
- an image root passed to `--image-root`
- image entries whose `file_name` values are relative to the image root

The script joins them as:

```text
image_root / image_info["file_name"]
```

## Output Layout

### Single-image outputs

Recommended:

```
outputs/sam3_hf_outputs/single_image/
|-- <image_stem>_hf_sam3.json
`-- hf_sam3_text_viz/
    `-- <image_stem>_hf_sam3_text.jpg
```

If BioCLIP is enabled:

```
outputs/sam3_hf_outputs/single_image/
`-- hf_sam3_text_bioclip_viz/
    `-- <image_stem>_hf_sam3_text_bioclip.jpg
```

### COCO/grouped outputs

Recommended:

```
outputs/sam3_hf_outputs/<collection>/<video_or_group>/
|-- <group>_annotations_hf_sam3_text_predictions.json
|-- hf_sam3_text_viz/
|   `-- <relative image tree preserved>
`-- hf_sam3_text_bioclip_viz/
    `-- <relative image tree preserved>
```

The visualization paths preserve the relative directory structure from the COCO `file_name` field.

## Chunked Grouped Runs

`make_camera_trap_sam3_chunks.py` creates a second organized tree under `BASE_OUTPUT_ROOT`, which defaults to:

`/fs/scratch/PAS2136/smartwilds_detection`

Expected structure:

```
/fs/scratch/PAS2136/smartwilds_detection/
|-- camera_trap_coco_image_list_summary.json
|-- camera_trap_sam3_chunk_summary.json
|
|-- <collection>/
|   |-- ... original grouped COCO output ...
|   |
|   `-- detections/
|       `-- camera_traps/
|           `-- <camera_trap>/
|               |-- chunks/
|               |   `-- <camera_trap>_chunk_00000_annotations_hf_sam3_text_predictions.json
|               `-- hf_sam3_text_viz/
|                   `-- chunks/
|                       `-- <camera_trap>_chunk_00000_viz/
|
`-- slurm_logs/
```

For each chunk, the helper also creates:

```
<original coco dir>/sam3_chunks/<camera_trap>_chunk_00000/
|-- <camera_trap>_chunk_00000_annotations.json
`-- images/
    `-- ... symlinks back to original images ...
```

## File Semantics

### Prediction JSON

Purpose:

- persistent machine-readable detection output
- input to downstream filtering, review, or conversion scripts

Contains:

- prompt categories and category IDs
- bounding boxes
- confidence scores
- optional masks
- optional BioCLIP predictions

### Visualization directories

Purpose:

- spot-check detection quality without re-running inference
- compare SAM3-only outputs against BioCLIP-enriched outputs

### Slurm logs

Purpose:

- keep launcher command lines
- capture stack traces and missing-file warnings
- record `nvidia-smi` output from the launcher

## Practical Notes

- The default `sam3_hf_outputs` directory is a planned output location and may not exist yet.
- Chunking and batch submission helpers write to `/fs/scratch/PAS2136/smartwilds_detection` unless overridden.
- The helper script names still mention `camera_trap`, but the output layout is simply an organized grouped-run layout for the same SAM3 backend.
