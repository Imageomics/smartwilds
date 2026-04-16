# SmartWilds Drone SAM3 Pipeline - Documentation Package

## What This Package Covers

This documentation describes the Hugging Face SAM3 text-prompted inference pipeline in:

`/fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf`

A packaged copy of the documentation bundle lives at:

`/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline`

It covers:

- single-image inference
- COCO image-list inference
- Slurm launch via `run_predict_sam3_text.sh`
- optional BioCLIP enrichment
- chunk creation for large grouped runs
- batch submission helpers
- performance benchmarking and edge-capacity analysis for Experiment 3 style studies
- camera-trap storage/workload analysis for Experiment 5 style edge filtering studies

It does not focus on `submit_all_predict_sam3_text.sh`.

## Recommended Reading Order

1. `README_COMPLETE_PIPELINE.md`
2. `ORGANIZED_OUTPUT_QUICKSTART.md`
3. `OUTPUT_DIRECTORY_STRUCTURE.md`
4. `COMPUTATIONAL_NODE_REQUIREMENTS.md`

## Packaged Bundle Layout

Inside the packaged `SAM3_detection_pipeline` copy:

- docs stay in the package root
- core scripts live in `src/`
- supporting utilities live in `misc/`
- benchmarking tools live in `performance/`

Packaged utility scripts:

- `misc/export_drone_detection_csv.py`
- `misc/vid_to_frame_coco.py`

Packaged performance scripts:

- `performance/benchmark_sam3_folder.py`
- `performance/run_sam3_benchmark.sh`
- `performance/analyze_sam3_edge_capacity.py`
- `performance/sam3_edge_scenario_template.csv`
- `performance/README_PERFORMANCE.md`

Packaged experiment-analysis bundle:

- `performance/camera_trap_storage_analysis/README.md`
- `performance/camera_trap_storage_analysis/run_storage_analysis.sh`
- `performance/camera_trap_storage_analysis/src/storage_analysis/`
- `performance/camera_trap_storage_analysis/results/`

## Pipeline Summary

### Stage 1: SAM3 text-prompted detection

- backend: Hugging Face `facebook/sam3`
- prompts default to `animal person vehicle`
- outputs COCO-style annotations for grouped runs
- optional mask export

### Stage 2: optional BioCLIP enrichment

- only runs when `--enable-bioclip` or `ENABLE_BIOCLIP=1`
- only annotates detections whose category is `animal`
- default zero-shot labels are:
  - `aves with common name bird`
  - `Mammalia with common name mammal`

### Stage 3: visualization export

- SAM3 overlays are written to `viz_dir`
- BioCLIP-enriched overlays are written to `bioclip_viz_dir`
- grouped runs save visualizations every `viz_every` images

## Main Scripts

### Primary scripts

- `predict_sam3_text.py`: core Python entry point
- `run_predict_sam3_text.sh`: standard Slurm launcher

In the packaged copy, these live under `src/`.

### Batch orchestration scripts

- `submit_camera_traps_predict_sam3_text.sh`
- `make_camera_trap_sam3_chunks.py`
- `submit_camera_trap_chunks_predict_sam3_text.sh`

### Helper modules

- `hf_sam3_detector.py`
- `bioclip_helper.py`
- `utils.py`

In the packaged copy, these also live under `src/`.

### Performance and experiment-analysis scripts

- `benchmark_sam3_folder.py`: measures initialization time, latency, throughput, and resource usage for one drone folder
- `run_sam3_benchmark.sh`: launches the benchmark on Slurm
- `analyze_sam3_edge_capacity.py`: turns benchmark summaries plus scenario CSV inputs into a feasibility table

In the packaged copy, these live under `performance/`.

## Quick Start

### Single image

```bash
python /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/predict_sam3_text.py \
    --run-mode image \
    --image-path /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250701_parrotanafi_1/20250703_parrotanafi_1_VID_002_frames/VID_002_000000.png \
    --output-json /tmp/VID_002_000000_hf_sam3.json \
    --viz-dir /tmp/hf_sam3_viz \
    --prompts animal person vehicle
```

### Slurm launch

```bash
sbatch /fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline/src/run_predict_sam3_text.sh
```

## Operational Notes

- The default launcher paths point to `smartwilds_drones`.
- The expected output root under `smartwilds_drones/outputs/sam3_hf_outputs` may need to be created on first use.
- The batch helper scripts still use `camera_trap` in their names because they were adapted from a grouped image-list workflow, but they call the same SAM3 inference entry point.
- The packaged TheWilds2025 copy is organized as docs in the root, pipeline scripts in `src/`, extra utilities in `misc/`, and benchmarking tools in `performance/`.
