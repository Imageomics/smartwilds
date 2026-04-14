# SAM3 Performance Benchmarking

This directory contains a small benchmarking workflow for the Hugging Face SAM3 drone pipeline. The goal is not just to measure how long one command takes, but to produce the kinds of numbers you need for an edge-computing feasibility analysis:

- how long SAM3 takes per image
- how throughput changes with batch size
- how much GPU memory and GPU utilization it uses
- how much extra cost is introduced when optional secondary processing is enabled
- whether a single node can keep up with a given arrival rate and latency target

This is designed to support Experiment 3, where you want to ask whether a single edge node can keep up with concurrent multi-modal workloads under SLO constraints.

## Big Picture

The workflow in this folder has three layers:

1. `benchmark_sam3_folder.py`
   This is the core measurement script. It runs SAM3 on one drone frame folder backed by a COCO image list and records latency, throughput, and resource-use metrics.

2. `run_sam3_benchmark.sh`
   This is a Slurm wrapper around the benchmark script. It lets you launch the same benchmark on the cluster without retyping all the Python arguments.

3. `analyze_sam3_edge_capacity.py`
   This is the experiment-analysis layer. It takes one or more measured benchmark summaries and combines them with scenario assumptions such as arrival rate, burst factor, and SLO. The output is a flat CSV you can use in tables or downstream plotting.

So the intended flow is:

1. run one or more SAM3 benchmarks
2. collect the generated `summary.json` files
3. define edge workload scenarios in a CSV
4. turn measurements plus scenarios into a feasibility table

## Files In This Directory

- `benchmark_sam3_folder.py`
  Runs SAM3 on a sampled subset of frames from a COCO-backed image folder and writes measurement outputs.

- `run_sam3_benchmark.sh`
  Slurm launcher for `benchmark_sam3_folder.py`.

- `analyze_sam3_edge_capacity.py`
  Converts benchmark results plus scenario assumptions into a per-scenario capacity table.

- `sam3_edge_scenario_template.csv`
  Starter scenario file for process-all, priority-based, and adaptive policies.

## What `benchmark_sam3_folder.py` Actually Does

The benchmark script is meant to answer a simple question: if you point SAM3 at one drone folder, how expensive is inference on a real machine?

### Inputs

The script expects:

- a COCO JSON file
- an image root containing the frame files referenced by that COCO JSON
- an output directory where results should be written

The COCO file is used only as the image list. The script is not evaluating mAP or comparing predictions to ground truth here. It is using the COCO metadata to know which images to run and in what order.

### Sampling behavior

You usually do not want to benchmark every frame in a large folder while you are still iterating. The script therefore lets you:

- benchmark only the first `N` frames
- benchmark a random subset
- apply a stride before sampling

That gives you a fast first-pass benchmark on a manageable subset such as `100` images.

### Runtime flow

For each run, the script does the following:

1. reads the COCO image list and resolves image paths
2. samples the subset of images you asked for
3. constructs the SAM3 detector and measures model initialization time
4. optionally constructs the BioCLIP helper if secondary processing is enabled
5. performs a small warmup pass if requested
6. processes the benchmark images in batches
7. times each major stage of each batch
8. records resource information such as RSS and CUDA memory
9. writes summary and detailed outputs to disk

### What is timed

Within each batch, the script separately tracks:

- image-read time
- processor/tokenization/preparation time
- host-to-device transfer time
- model forward time
- SAM3 post-processing time
- result-formatting time
- NMS time
- optional BioCLIP time
- total batch wall-clock time

This matters because for an edge study, "the model is slow" is less useful than knowing where the time is going. For example, a system may be model-bound, IO-bound, or post-processing-bound depending on batch size and hardware.

### What is approximated

The script reports approximate per-image latency for batched runs as:

`batch_wall_time / batch_size`

That approximation is fine for throughput-oriented comparisons and early feasibility checks, but it is not the same thing as an independently measured end-to-end latency for each image under a streaming scheduler. If you care most about strict latency, start with `--batch-size 1`.

## What The Benchmark Outputs Mean

Each benchmark run writes three outputs.

### `summary.json`

This is the main artifact for experiment analysis. It contains:

- run configuration
- dataset counts
- model initialization time
- aggregate benchmark wall time
- throughput in images per second
- latency summaries such as min, mean, p50, p90, p95, and max
- total detection counts
- process RSS
- Torch CUDA peak memory
- sampled `nvidia-smi` utilization and memory summaries

If you only keep one file from each benchmark run, this should be it.

### `batch_records.jsonl`

This is the detailed per-batch trace. Each line is one JSON record with:

- batch index
- image files included in that batch
- batch wall-clock time
- internal SAM3 timing breakdown
- optional BioCLIP time
- approximate per-image latency for that batch
- detection counts
- CUDA memory measurements for that batch

This file is useful if you want to study variability, identify outlier batches, or make timing breakdown plots.

### `per_image_latency.csv`

This is a flattened per-image view. For batched runs, the latency numbers are approximate because they are derived from the containing batch. It is still useful for:

- merging with image metadata
- inspecting detection counts per frame
- building quick tables or plots in R, pandas, or Excel

## Resource Metrics

The benchmark records multiple resource views because no single metric tells the whole story.

### CPU / process memory

The script records:

- RSS before model initialization
- RSS after model initialization
- final RSS
- process max RSS

This is helpful for asking whether the process is becoming too heavy for an edge laptop or field node.

### Torch CUDA memory

The script records:

- current CUDA allocated memory
- current CUDA reserved memory
- peak allocated memory
- peak reserved memory

These are good for comparing batch sizes and for understanding whether a larger batch improves throughput enough to justify the memory cost.

### `nvidia-smi` polling

When running on CUDA, the script also samples `nvidia-smi` periodically and summarizes:

- average GPU utilization
- peak GPU utilization
- average memory used
- peak memory used

This helps answer a different question from Torch memory: not just "how much memory did the framework reserve?" but "how busy did the GPU actually stay during the run?"

## What `run_sam3_benchmark.sh` Does

The Slurm launcher is a convenience wrapper. It exists so that:

- you can submit benchmarks in the same style as the rest of your pipeline
- you can sweep settings by changing environment variables
- outputs land in a consistent benchmark directory structure

The script:

1. activates the `sam3` conda environment
2. sets defaults for benchmark configuration
3. creates output directories and log directories
4. builds the Python command for `benchmark_sam3_folder.py`
5. submits the benchmark on one GPU node

It does not perform extra analysis by itself. Its job is simply to launch the measurement run reproducibly.

## What `analyze_sam3_edge_capacity.py` Does

This script is the bridge from system benchmarking to Experiment 3.

It reads:

- one or more `summary.json` benchmark outputs
- a scenario CSV describing workload assumptions

It then computes, for each benchmark and each scenario:

- required throughput
- measured throughput
- estimated utilization
- chosen latency metric
- whether throughput is feasible
- whether latency is feasible
- whether the scenario is feasible on a single node overall

### Scenario CSV columns

The included template file has these columns:

- `scenario_id`
  A short label for the scenario.

- `policy`
  A human-readable policy label such as `process-all`, `priority-based`, or `adaptive`.

- `arrival_rate_images_per_sec`
  The incoming image rate that SAM3 would need to handle.

- `activation_fraction`
  The fraction of arrivals that actually trigger SAM3. This is especially useful for adaptive pipelines where only a subset of events proceed to the next stage.

- `burst_factor`
  A multiplicative factor for bursty periods. For example, `1.5` means the benchmark should be judged against a workload 50 percent heavier than the steady-state rate.

- `slo_seconds`
  The latency target you want the system to satisfy.

- `notes`
  Free-form explanation for the row.

### Required throughput formula

The analysis script computes:

`required_throughput_images_per_sec = arrival_rate_images_per_sec * activation_fraction * burst_factor`

It then compares that required throughput against the measured images-per-second from the benchmark.

### Feasibility logic

- `throughput_feasible` is true when measured throughput is at least the required throughput
- `latency_feasible` is true when the chosen latency metric is at or below the SLO
- `single_node_feasible` is true only when both are true

This makes it easy to produce the "can one edge node handle this?" table for the paper.

## How This Maps To Your Experiment 3 Policies

Here is the intended interpretation for the policy ideas you described.

### Process-all

Every relevant event is processed by SAM3. In the scenario CSV, this usually means:

- `activation_fraction = 1.0`
- `burst_factor` reflects how aggressive you want the stress case to be

### Priority-based

SAM3 is applied to the drone stream under a stricter latency target, while other modalities may be delayed or simplified elsewhere in the full system. For the SAM3-specific table, this mostly changes:

- the arrival rate you assign to the drone stream
- the SLO you expect for the drone path

### Adaptive

Only a subset of events triggers secondary or downstream work. In the SAM3-specific analysis, this is often represented through:

- a lower `activation_fraction`

If you want to quantify the additional cost of a secondary stage such as BioCLIP, you can rerun the benchmark with `--enable-bioclip` and compare those summaries directly.

## Recommended Benchmarking Strategy

For a clean first pass, use the following sequence.

1. Run `batch-size 1` on `100` images.
   This gives you the most interpretable per-image latency baseline.

2. Run a small batch-size sweep such as `1, 2, 4, 8`.
   This shows how throughput and memory scale.

3. Decide whether you care more about latency or throughput.
   For edge real-time analysis, latency is usually the more important baseline.

4. Optionally rerun with `--enable-bioclip`.
   This helps quantify the cost of adaptive secondary processing.

5. Edit `sam3_edge_scenario_template.csv` using real arrival-rate estimates from Experiment 1.

6. Run the capacity-analysis script to produce the edge feasibility table.

## Practical Interpretation Tips

- Use `per_image_total_p95_s` when you want a conservative latency summary for SLO-style arguments.
- Use `per_image_sam3_p95_s` if you want to isolate SAM3 time from image-read overhead.
- Use `images_per_second` for throughput comparisons across batch sizes.
- Use Torch peak CUDA memory and `nvidia-smi` peak memory together when discussing resource pressure.
- Be careful comparing small random subsets against full-run production behavior; the benchmark is designed for controlled profiling, not for exact end-to-end field emulation.

## Local Example

```bash
source /fs/ess/PAS2699/harvest_modules/miniconda3/bin/activate
conda activate sam3

python /fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf/performance/benchmark_sam3_folder.py \
    --coco-json /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_005_frames/VID_005_annotations.json \
    --image-root /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_005_frames \
    --output-dir /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_benchmarks/vid005_bs1_100img \
    --tag vid005_bs1_100img \
    --max-images 100 \
    --batch-size 1 \
    --warmup-batches 1
```

## Batch-Size Sweep Example

```bash
for bs in 1 2 4 8; do
  python /fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf/performance/benchmark_sam3_folder.py \
      --coco-json /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_005_frames/VID_005_annotations.json \
      --image-root /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_005_frames \
      --output-dir /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_benchmarks/vid005_bs${bs}_100img \
      --tag vid005_bs${bs}_100img \
      --max-images 100 \
      --batch-size "$bs" \
      --warmup-batches 1
done
```

## Slurm Example

```bash
TAG=vid005_bs1_100img \
MAX_IMAGES=100 \
BATCH_SIZE=1 \
COCO_JSON=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_005_frames/VID_005_annotations.json \
IMAGE_ROOT=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_005_frames \
sbatch /fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf/performance/run_sam3_benchmark.sh
```

## Capacity Analysis Example

```bash
python /fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf/performance/analyze_sam3_edge_capacity.py \
    --benchmark-summaries "/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_benchmarks/*/summary.json" \
    --scenario-csv /fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf/performance/sam3_edge_scenario_template.csv \
    --output-csv /fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_benchmarks/sam3_edge_capacity_table.csv
```

## Suggested Output Structure

One clean pattern is:

- one benchmark directory per batch-size or configuration
- one `summary.json` per benchmark directory
- one final merged CSV for the edge-capacity table

That makes it easy to compare:

- `batch-size 1` versus `batch-size 4`
- SAM3-only versus SAM3-plus-BioCLIP
- steady-state versus burst scenarios

## Caveats

- The per-image latency in batched runs is approximate, not queue-aware streaming latency.
- This benchmark measures inference performance, not detection accuracy.
- Results depend on the exact GPU, driver, environment, and storage path.
- If you want publication-quality claims about an actual ruggedized edge laptop, rerun the same scripts on that target machine rather than only on cluster hardware.
