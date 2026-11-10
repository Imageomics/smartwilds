#!/bin/bash
#SBATCH -N 1
#SBATCH --constraint="gpu"
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --account=PAS2699
#SBATCH --partition=nextgen
#SBATCH --clusters=ascend
#SBATCH --time=01:00:00
#SBATCH --mem=80G
#SBATCH --output=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_benchmarks/slurm_logs/%x_%j.txt

set -euo pipefail

source /fs/ess/PAS2699/harvest_modules/miniconda3/bin/activate

CONDA_ENV="${CONDA_ENV:-sam3}"
BENCHMARK_SCRIPT="${BENCHMARK_SCRIPT:-/fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf/performance/benchmark_sam3_folder.py}"

COCO_JSON="${COCO_JSON:-/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_005_frames/VID_005_annotations.json}"
IMAGE_ROOT="${IMAGE_ROOT:-/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_005_frames}"
TAG="${TAG:-$(basename "$IMAGE_ROOT")_bs${BATCH_SIZE:-1}_sample${MAX_IMAGES:-100}}"

OUTPUT_ROOT="${OUTPUT_ROOT:-/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_benchmarks}"
OUTPUT_DIR="${OUTPUT_DIR:-$OUTPUT_ROOT/$TAG}"

MAX_IMAGES="${MAX_IMAGES:-100}"
SAMPLE_MODE="${SAMPLE_MODE:-first}"
SAMPLE_STRIDE="${SAMPLE_STRIDE:-1}"
RANDOM_SEED="${RANDOM_SEED:-42}"
WARMUP_BATCHES="${WARMUP_BATCHES:-1}"
BATCH_SIZE="${BATCH_SIZE:-1}"
DEVICE="${DEVICE:-cuda}"
MODEL_ID="${MODEL_ID:-facebook/sam3}"
PROMPTS="${PROMPTS:-animal person vehicle}"
CONFIDENCE_THRESHOLD="${CONFIDENCE_THRESHOLD:-0.5}"
MASK_THRESHOLD="${MASK_THRESHOLD:-0.5}"
NMS_IOU="${NMS_IOU:-0.5}"
RETURN_MASKS="${RETURN_MASKS:-0}"
ENABLE_BIOCLIP="${ENABLE_BIOCLIP:-0}"
BIOCLIP_DEVICE="${BIOCLIP_DEVICE:-cpu}"
BIOCLIP_BATCH_SIZE="${BIOCLIP_BATCH_SIZE:-16}"
GPU_POLL_INTERVAL_S="${GPU_POLL_INTERVAL_S:-1.0}"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_ROOT/slurm_logs"

conda activate "$CONDA_ENV"

nvidia-smi || true

cmd=(
  python "$BENCHMARK_SCRIPT"
  --coco-json "$COCO_JSON"
  --image-root "$IMAGE_ROOT"
  --output-dir "$OUTPUT_DIR"
  --tag "$TAG"
  --max-images "$MAX_IMAGES"
  --sample-mode "$SAMPLE_MODE"
  --sample-stride "$SAMPLE_STRIDE"
  --random-seed "$RANDOM_SEED"
  --warmup-batches "$WARMUP_BATCHES"
  --batch-size "$BATCH_SIZE"
  --device "$DEVICE"
  --model-id "$MODEL_ID"
  --confidence-threshold "$CONFIDENCE_THRESHOLD"
  --mask-threshold "$MASK_THRESHOLD"
  --nms-iou "$NMS_IOU"
  --gpu-poll-interval-s "$GPU_POLL_INTERVAL_S"
  --prompts
)

read -r -a prompt_args <<< "$PROMPTS"
cmd+=("${prompt_args[@]}")

if [[ "$RETURN_MASKS" == "1" ]]; then
  cmd+=(--return-masks)
fi

if [[ "$ENABLE_BIOCLIP" == "1" ]]; then
  cmd+=(--enable-bioclip --bioclip-device "$BIOCLIP_DEVICE" --bioclip-batch-size "$BIOCLIP_BATCH_SIZE")
fi

echo "Running SAM3 performance benchmark:"
printf '  %q' "${cmd[@]}"
printf '\n'

"${cmd[@]}"
