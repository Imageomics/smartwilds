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
#SBATCH --output=/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/slurm_logs/%j.txt

set -euo pipefail

source /fs/ess/PAS2699/harvest_modules/miniconda3/bin/activate

# Edit these variables for your run.
CONDA_ENV="${CONDA_ENV:-sam3}"
PYTHON_SCRIPT="${PYTHON_SCRIPT:-/fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf/predict_sam3_text.py}"
RUN_MODE="${RUN_MODE:-coco}"
DEVICE="${DEVICE:-cuda}"
BATCH_SIZE="${BATCH_SIZE:-1}"
MODEL_ID="${MODEL_ID:-facebook/sam3}"
PROMPTS="${PROMPTS:-animal person vehicle}"
CONFIDENCE_THRESHOLD="${CONFIDENCE_THRESHOLD:-0.5}"
MASK_THRESHOLD="${MASK_THRESHOLD:-0.5}"
NMS_IOU="${NMS_IOU:-0.5}"
RETURN_MASKS="${RETURN_MASKS:-0}"
VIZ_EVERY="${VIZ_EVERY:-10}"
ENABLE_BIOCLIP="${ENABLE_BIOCLIP:-0}"
BIOCLIP_DEVICE="${BIOCLIP_DEVICE:-cpu}"
BIOCLIP_BATCH_SIZE="${BIOCLIP_BATCH_SIZE:-16}"

IMAGE_PATH="${IMAGE_PATH:-/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250701_parrotanafi_1/20250703_parrotanafi_1_VID_002_frames/VID_002_000001.png}"
COCO_JSON="${COCO_JSON:-/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames/VID_004_annotations.json}"
IMAGE_ROOT="${IMAGE_ROOT:-/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames}"
OUTPUT_JSON="${OUTPUT_JSON:-/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/VID_004_annotations_hf_sam3_text_predictions.json}"
VIZ_DIR="${VIZ_DIR:-/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_viz}"
BIOCLIP_VIZ_DIR="${BIOCLIP_VIZ_DIR:-/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_bioclip_viz}"

conda activate "$CONDA_ENV"

nvidia-smi

cmd=(
  python "$PYTHON_SCRIPT"
  --run-mode "$RUN_MODE"
  --device "$DEVICE"
  --batch-size "$BATCH_SIZE"
  --model-id "$MODEL_ID"
  --confidence-threshold "$CONFIDENCE_THRESHOLD"
  --mask-threshold "$MASK_THRESHOLD"
  --nms-iou "$NMS_IOU"
  --viz-every "$VIZ_EVERY"
  --bioclip-device "$BIOCLIP_DEVICE"
  --bioclip-batch-size "$BIOCLIP_BATCH_SIZE"
  --image-path "$IMAGE_PATH"
  --coco-json "$COCO_JSON"
  --image-root "$IMAGE_ROOT"
  --output-json "$OUTPUT_JSON"
  --viz-dir "$VIZ_DIR"
  --bioclip-viz-dir "$BIOCLIP_VIZ_DIR"
  --prompts
)

read -r -a prompt_args <<< "$PROMPTS"
cmd+=("${prompt_args[@]}")

if [[ "$RETURN_MASKS" == "1" ]]; then
  cmd+=(--return-masks)
fi

if [[ "$ENABLE_BIOCLIP" == "1" ]]; then
  cmd+=(--enable-bioclip)
fi

echo "Running script with launcher settings:"
printf '  %q' "${cmd[@]}"
printf '\n'

"${cmd[@]}"
