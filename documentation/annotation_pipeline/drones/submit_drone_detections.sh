#!/bin/bash
#SBATCH --job-name=drone-detect
#SBATCH --account=PAS2136
#SBATCH --partition=gpu
#SBATCH --gpus-per-node=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --array=0-38
#SBATCH --output=logs/drone-detect_%A_%a.out
#SBATCH --error=logs/drone-detect_%A_%a.err

# Drone video detection SLURM array job
# Each array task processes one video file
#
# Usage:
#   # List all videos
#   bash submit_drone_detections.sh --list
#
#   # Submit all 39 videos
#   sbatch submit_drone_detections.sh
#
#   # Test with one small video
#   sbatch --partition=gpudebug --time=1:00:00 --array=0 submit_drone_detections.sh

SCRIPT_DIR="/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/drones"
CONDA_DIR="/users/PAS2136/kline377/miniconda3"
ENV_NAME="ultralytics_env"
PYTHON="${CONDA_DIR}/envs/${ENV_NAME}/bin/python"

# Handle non-SLURM invocations
if [[ "$1" == "--list" ]]; then
    ${PYTHON} "${SCRIPT_DIR}/run_drone_detections.py" --list
    exit 0
fi

# ---- SLURM execution ----

echo "============================================"
echo "Drone Detection - Array Task ${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'unknown')"
echo "Start: $(date)"
echo "============================================"

module load cuda/12.4.1

mkdir -p "${SCRIPT_DIR}/logs"

${PYTHON} "${SCRIPT_DIR}/run_drone_detections.py" \
    --array-index ${SLURM_ARRAY_TASK_ID} \
    --frame-interval 30

echo ""
echo "============================================"
echo "Finished: $(date)"
echo "============================================"
