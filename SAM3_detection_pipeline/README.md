# SmartWilds Drone SAM3 HF Pipeline

This directory contains the Hugging Face SAM3 text-prompted detection pipeline used for SmartWilds drone imagery, with optional BioCLIP enrichment for animal detections.

## Read This First

- `START_HERE.md`: entry point and recommended reading order
- `README_COMPLETE_PIPELINE.md`: end-to-end workflow and script roles
- `ORGANIZED_OUTPUT_QUICKSTART.md`: practical commands for single runs and batch submission
- `OUTPUT_DIRECTORY_STRUCTURE.md`: expected input/output layout
- `COMPUTATIONAL_NODE_REQUIREMENTS.md`: Slurm and hardware guidance

## Packaged Copy Layout

A packaged copy of this documentation and script bundle also lives at:

`/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones/SAM3_detection_pipeline`

In that packaged copy:

- markdown documentation stays in the package root
- runnable pipeline scripts live under `src/`
- supporting utilities live under `misc/`
- benchmarking and edge-capacity analysis tools live under `performance/`

## Core Execution Files

- `predict_sam3_text.py`: main inference entry point for one image or a COCO image list
- `run_predict_sam3_text.sh`: single Slurm launcher that wraps `predict_sam3_text.py`
- `hf_sam3_detector.py`: Hugging Face `Sam3Model` / `Sam3Processor` wrapper
- `bioclip_helper.py`: optional in-process BioCLIP zero-shot enrichment for detections with category `animal`
- `utils.py`: visualization helper for SAM3 and BioCLIP overlays

## Batch Submission Helpers

- `submit_camera_traps_predict_sam3_text.sh`: submits one Slurm job per record in a summary JSON
- `make_camera_trap_sam3_chunks.py`: splits large COCO image lists into chunked jobs and symlinked image roots
- `submit_camera_trap_chunks_predict_sam3_text.sh`: submits one Slurm job per chunk

These helper names still reference `camera_trap`, but they launch the same Hugging Face SAM3 backend and are documented here because they are part of the same inference stack.

## Misc Utilities In The Packaged Copy

- `misc/export_drone_detection_csv.py`: copied from `export_drone_detection_simple_csv.py` and renamed for the package
- `misc/vid_to_frame_coco.py`: helper for building frame directories and COCO image-list inputs from video

## Performance Experiment Bundle

The packaged copy now also includes a `performance/` directory for Experiment 3 style profiling and edge-feasibility analysis.

- `performance/benchmark_sam3_folder.py`: benchmarks SAM3 on a drone frame folder and records latency, throughput, and resource metrics
- `performance/run_sam3_benchmark.sh`: Slurm launcher for the benchmark script
- `performance/analyze_sam3_edge_capacity.py`: combines benchmark summaries with scenario assumptions to estimate single-node feasibility
- `performance/sam3_edge_scenario_template.csv`: starter scenario file for process-all, priority-based, and adaptive policy analysis
- `performance/README_PERFORMANCE.md`: detailed walkthrough of what is measured and how to interpret the outputs

`submit_all_predict_sam3_text.sh` exists in this directory but is intentionally not part of the main documentation package.
