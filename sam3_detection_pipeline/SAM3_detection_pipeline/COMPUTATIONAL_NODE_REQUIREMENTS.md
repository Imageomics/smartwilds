# Computational Node Requirements for SmartWilds Drone SAM3 HF Inference

This document summarizes practical compute requirements for the Hugging Face SAM3 text-prompted drone pipeline in `sam3_predictor_hf`.

## Documentation Bundle Layout

A packaged copy of this material also lives at:

`/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline`

That package is organized as:

- root: markdown documentation
- `src/`: runnable SAM3 pipeline scripts and helper modules
- `misc/`: supporting utilities such as `export_drone_detection_csv.py` and `vid_to_frame_coco.py`

## Executive Summary

- recommended path: one GPU Slurm job using `run_predict_sam3_text.sh`
- default launcher allocation: 1 GPU, 80 GB RAM, 1 hour wall time
- best use case: one drone frame set or one chunked grouped run per job
- BioCLIP is optional and defaults to CPU when SAM3 runs on CUDA

## 1. Baseline Launcher Requirements

The standard launcher requests:

```bash
#SBATCH -N 1
#SBATCH --constraint="gpu"
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --account=PAS2699
#SBATCH --partition=nextgen
#SBATCH --clusters=ascend
#SBATCH --time=01:00:00
#SBATCH --mem=80G
```

This is the current documented baseline because it matches `run_predict_sam3_text.sh`.

## 2. Recommended Hardware Profiles

### Standard GPU run

- GPU: 1 NVIDIA GPU suitable for Hugging Face SAM3 inference
- RAM: 80 GB
- CPU: enough host cores for image decoding and file I/O
- wall time: 1 hour baseline

Best for:

- one COCO image list
- one chunk created by `make_camera_trap_sam3_chunks.py`
- debugging prompt and threshold changes

### GPU run with BioCLIP on CPU

- same GPU allocation as above
- BioCLIP stays on CPU by default when device is CUDA
- safest option when GPU memory is tight

Best for:

- preserving GPU memory for SAM3
- long grouped runs where stability matters more than BioCLIP speed

### GPU run with BioCLIP on GPU

- same base allocation, but with higher memory risk
- consider smaller `BATCH_SIZE`
- consider smaller `BIOCLIP_BATCH_SIZE`

Best for:

- smaller runs where BioCLIP speed matters
- short experiments after a stable CPU-backed run

## 3. Deployment Strategy Options

### Option A: Single launcher job

Use `run_predict_sam3_text.sh` directly.

Pros:

- simplest path
- matches existing defaults
- easiest to debug from one Slurm log

Cons:

- less scalable for many large grouped runs

Example:

```bash
RUN_MODE=coco \
COCO_JSON=/path/to/annotations.json \
IMAGE_ROOT=/path/to/images \
OUTPUT_JSON=/path/to/output.json \
VIZ_DIR=/path/to/viz \
sbatch /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/run_predict_sam3_text.sh
```

In the packaged `SAM3_detection_pipeline` bundle, the equivalent launcher lives under `src/run_predict_sam3_text.sh`.

### Option B: One job per summary record

Use `submit_camera_traps_predict_sam3_text.sh`.

Pros:

- simple fan-out across many grouped runs
- skips already queued jobs
- skips outputs that already exist

Cons:

- depends on an upstream summary JSON
- helper naming is legacy and can be confusing at first glance

### Option C: Chunked parallel jobs

Use `make_camera_trap_sam3_chunks.py` followed by `submit_camera_trap_chunks_predict_sam3_text.sh`.

Pros:

- better control for very large grouped runs
- reduces risk of a single long job failing after substantial progress
- easier to retry one chunk than a full collection

Cons:

- creates more files and symlink trees
- needs chunk-summary bookkeeping

## 4. Throughput and Tuning Considerations

Actual runtime depends on:

- image resolution
- number of images in the COCO list
- number of prompts
- whether masks are returned
- whether BioCLIP is enabled
- visualization frequency

The main tuning knobs are:

- `BATCH_SIZE`
- `PROMPTS`
- `RETURN_MASKS`
- `VIZ_EVERY`
- `BIOCLIP_DEVICE`
- `BIOCLIP_BATCH_SIZE`

### Safe defaults

- keep `PROMPTS="animal person vehicle"`
- keep `RETURN_MASKS=0` unless masks are required downstream
- keep `VIZ_EVERY=10` for QA without writing too many images
- keep BioCLIP on CPU for the first stable production run

## 5. Storage Requirements During Processing

### Inputs

- original drone frames
- COCO image list JSONs when running grouped inference

### Outputs

- prediction JSONs
- visualization JPEGs
- BioCLIP visualization JPEGs when enabled
- Slurm logs

Storage pressure grows when:

- `RETURN_MASKS=1`
- `VIZ_EVERY` is small
- many grouped runs are kept together under the same output root

### Practical recommendation

- keep prediction JSONs permanently
- keep a moderate set of QA visualizations
- reduce visualization frequency for very large runs

## 6. Software Environment

The launcher assumes:

- conda activation via `/fs/ess/PAS2699/harvest_modules/miniconda3/bin/activate`
- environment name `sam3`

Python-side requirements implied by the code:

- `torch`
- `transformers` with `Sam3Model` and `Sam3Processor`
- `Pillow`
- `tqdm`
- `torchvision`
- `opencv-python`
- `numpy`
- optional `bioclip`

If `transformers` lacks SAM3 support, `hf_sam3_detector.py` will fail during import with an explicit message.

## 7. Failure Recovery

### Missing input files

- `predict_sam3_text.py` fails fast for missing primary inputs
- grouped COCO runs skip per-image missing files and continue

### Existing outputs

- submission helpers skip existing outputs unless `OVERWRITE=1`

### Restart strategy

- rerun a single launcher job for isolated failures
- rerun only failed chunk jobs for chunked workflows
- keep Slurm logs under `slurm_logs/` for diagnosis

## 8. Recommended Operational Sequence

1. Run one direct `image` job.
2. Run one direct `coco` job.
3. Enable BioCLIP only after the base SAM3 path is stable.
4. Move to summary-based or chunked submission for larger campaigns.

## 9. Packaged Copy Notes

If you are running from the packaged TheWilds2025 bundle instead of the source tree:

- launchers and Python scripts are under `SAM3_detection_pipeline/src/`
- extra preparation/export helpers are under `SAM3_detection_pipeline/misc/`
- update command paths in examples accordingly
