# Experiment 5: Storage Savings from Edge Blank Image Filtering

This directory contains the reproducible analysis bundle for **Experiment 5** from the experimental plan:

- **Research question**: What fraction of camera trap images can be filtered out at the edge, and how much does that reduce storage and downstream processing workload?
- **SEC CFP fit**: Storage and data management technologies for edge computing

This analysis is designed to answer the practical systems question, not a human-annotation question. The central result is:

- How much raw camera-trap storage is generated
- How much of that storage remains after the current detection pipeline retains only images with detections
- How much the downstream arrival rate drops when only detector-positive images are passed to later stages

## Experiment Framing

This experiment uses the current camera-trap detection pipeline as the operational definition of filtering:

- A **retained image** is an image that appears in the final `*_detections_filtered.csv` output for a deployment.
- A **filtered-out image** is a raw image file that exists on disk for that deployment but does **not** appear in the retained detection output.

For this experiment, filtered-out images are treated as the images that edge blank-image filtering would prevent from being stored or processed downstream.

This means the results are best described as:

- **images with no retained detections under the current pipeline**
- **detector-based blank filtering savings**
- **storage/workload savings from edge filtering**

This analysis does **not** require human-verified ground truth to support the systems claim.

## What This Produces

Running the pipeline generates:

- A detailed deployment-level summary
- Camera-level, campaign-level, and overall rollups
- A paper-friendly workload table
- A storage savings table
- A hardware/workload comparison table
- Two figures for storage and throughput savings
- A short results report
- Diagnostics about excluded or imperfect inputs

All outputs are written to:

- [`results/`](./results)

## Directory Structure

This experiment now follows a conventional Python layout:

- `run_storage_analysis.sh`
  Shell launcher for rerunning the experiment from the repository root.

- `analyze_blank_image_filtering.py`
  Thin compatibility wrapper. This preserves the original entrypoint name, but
  the real implementation lives in the package below.

- `src/storage_analysis/`
  Main Python package for the experiment.

- `results/`
  Generated outputs. Safe to regenerate.

## Python Package Layout

- [`src/storage_analysis/paths.py`](./src/storage_analysis/paths.py)
  Path resolution and immutable experiment configuration.

- [`src/storage_analysis/deployment_metadata.py`](./src/storage_analysis/deployment_metadata.py)
  Deployment metadata loading and normalization helpers.

- [`src/storage_analysis/inventory.py`](./src/storage_analysis/inventory.py)
  Raw image and retained-detection inventory builders.

- [`src/storage_analysis/metrics.py`](./src/storage_analysis/metrics.py)
  Deployment metrics, rollups, and diagnostics.

- [`src/storage_analysis/reporting.py`](./src/storage_analysis/reporting.py)
  CSV and Markdown output writers.

- [`src/storage_analysis/visualization.py`](./src/storage_analysis/visualization.py)
  Figure generation.

- [`src/storage_analysis/pipeline.py`](./src/storage_analysis/pipeline.py)
  Top-level orchestration.

- [`src/storage_analysis/cli.py`](./src/storage_analysis/cli.py)
  CLI entrypoint used by the launcher.

## Inputs and Data Sources

The analysis uses these inputs:

### 1. Raw camera-trap images

These directories provide the denominator for storage and image-count calculations:

- `/fs/ess/PAS2136/TheWilds2025/thewilds_20250630_20250703/camera_traps`
- `/fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/camera_traps`

For each image file, the script records:

- full path
- deployment/campaign membership
- file size in bytes

### 2. Retained detection outputs

These CSVs define which images survive the edge filter:

- `/fs/ess/PAS2136/TheWilds2025/processing_output/detections/camera_traps/*_detections_filtered.csv`

Each unique `image_path` appearing in one of these files is treated as a retained, detector-positive image.

### 3. Deployment metadata

These files provide deployment duration for rate normalization:

- `/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps/imageomicsthewilds_cameratraps/src/03_metadata/darwin_core_events.csv`
- `/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps/imageomicsthewilds_cameratraps/src/01_events/camera_deployment_metadata.py`

The Darwin Core events table is used first. If a deployment is missing there, the script falls back to `camera_deployment_metadata.py`.

## Important Input Caveat

The file below is intentionally **not** used as a source of truth:

- `/fs/ess/PAS2136/TheWilds2025/processing_output/detections/camera_traps/all_images_summary.csv`

Why it is excluded:

- It repeats every deployment out to the same row count
- It is not a trustworthy denominator for blank-rate estimation
- Using it would bias the storage and workload estimates

The script records this in `results/diagnostics.csv`.

## How To Run

### Option 1: Use the launcher

From the repository root:

```bash
bash processing_output/experimental_results/storage_analysis/run_storage_analysis.sh
```

### Option 2: Run the packaged module directly

From the repository root:

```bash
PYTHONPATH=processing_output/experimental_results/storage_analysis/src \
python -m storage_analysis
```

## Expected Runtime and Resource Use

This analysis is mostly filesystem scanning plus pandas aggregation.

- No GPU required
- No network access required
- CPU and disk I/O dominate runtime
- Typical runtime is on the order of 1-2 minutes for the current dataset size

The main cost is rescanning roughly `235K+` image files and summing their sizes.

## Methodology

The script performs the following steps:

1. Scan all raw camera-trap image files on disk.
2. Assign each file to a `deployment_id = <camera>_<campaign>`.
3. Record raw byte size for each image.
4. Load each `*_detections_filtered.csv`.
5. Mark unique `image_path` values in those files as detector-positive.
6. Treat raw images missing from detector-positive outputs as filtered out.
7. Join deployment-duration metadata to normalize rates.
8. Compute storage and arrival-rate metrics at deployment, camera, campaign, and overall levels.
9. Write tables, figures, and a short report.

## Metrics Reported

### Core counts

- `total_images`: total raw images in the deployment
- `true_positive_images`: images retained by the detector pipeline
- `blank_count`: raw images not retained by the detector pipeline
- `blank_pct`: `blank_count / total_images * 100`

### Storage metrics

- `raw_gb`: total raw storage
- `filtered_gb`: storage remaining if only retained images are stored
- `storage_saved_gb`: `raw_gb - filtered_gb`
- `storage_saved_pct`: percent storage reduction
- `raw_gb_per_day`: raw storage generated per deployment day
- `filtered_gb_per_day`: retained storage per deployment day

### Workload / throughput metrics

- `raw_rate_per_hour`: raw images per hour over the deployment duration
- `tp_rate_per_hour`: retained images per hour over the deployment duration
- `raw_rate_per_second`
- `tp_rate_per_second`
- `throughput_reduction_x`: `raw_rate_per_hour / tp_rate_per_hour`

## Output Inventory

After a run, the most useful artifacts are:

### Main summaries

- [`results/deployment_summary.csv`](./results/deployment_summary.csv)
- [`results/camera_summary.csv`](./results/camera_summary.csv)
- [`results/campaign_summary.csv`](./results/campaign_summary.csv)
- [`results/overall_summary.csv`](./results/overall_summary.csv)

### Paper-friendly tables

- [`results/table_camera_campaign_workload.csv`](./results/table_camera_campaign_workload.csv)
  Per deployment: camera, totals, filtered-out counts, and arrival rates

- [`results/table_storage_savings.csv`](./results/table_storage_savings.csv)
  Per deployment: raw vs retained storage and savings

- [`results/table_hardware_comparison.csv`](./results/table_hardware_comparison.csv)
  Per deployment: raw vs retained processing rates and reduction factor

- [`results/table_camera_rollup.csv`](./results/table_camera_rollup.csv)
- [`results/table_campaign_rollup.csv`](./results/table_campaign_rollup.csv)
- [`results/table_overall_rollup.csv`](./results/table_overall_rollup.csv)

### Figures

- [`results/storage_savings_gb.png`](./results/storage_savings_gb.png)
- [`results/throughput_comparison.png`](./results/throughput_comparison.png)

### Narrative summary

- [`results/REPORT.md`](./results/REPORT.md)

### Diagnostics

- [`results/diagnostics.csv`](./results/diagnostics.csv)

## Recommended Paper Language

To keep the claim precise and systems-focused, describe the result as:

- “images with no retained detections under the current edge filtering pipeline”
- “detector-based blank-image filtering”
- “storage and workload savings achievable by edge filtering”

Avoid stronger wording such as:

- “ground-truth blank images”
- “human-verified empty frames”

unless that has been validated separately.

## Current Headline Result

From the current generated outputs:

- `235,778` raw images analyzed
- `229,956` images with no retained detections under the current pipeline
- `236.89 GB` raw storage reduced to `7.39 GB`
- `96.88%` storage savings
- `78.59` raw images/hour reduced to `1.94` retained images/hour
- `40.50x` downstream throughput reduction overall

## Limitations

- This is a detector-based systems analysis, not a human-labeled accuracy study.
- If the detector misses animals, those images will still count as filtered out in this analysis.
- One deployment (`TW07-CT05_20250804_20250828`) has metadata but no raw image files in the scanned directories, so it is excluded from rollups.
- Deployment durations depend on metadata files and may reflect deployment windows rather than exact on/off capture intervals.

## Troubleshooting

### The script says no raw camera trap images were found

Make sure you are running from the repository root and that the expected campaign directories still exist under:

- `thewilds_20250630_20250703/camera_traps`
- `thewilds_20250804_20250828/camera_traps`

### The script says no filtered detection CSVs were found

Check that the per-deployment outputs exist in:

- `processing_output/detections/camera_traps`

### A deployment is missing from the rollups

Check `results/diagnostics.csv`. The most likely causes are:

- no raw image files were found for that deployment
- the deployment is present in metadata but absent from the raw filesystem scan

## Reproducibility Notes

- The analysis is fully file-driven and can be rerun at any time.
- Results will change if new detections are generated or if raw camera-trap files are added/removed.
- Because the script rescans the filesystem, it does not depend on cached inventories.
