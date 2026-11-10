#!/bin/bash
#SBATCH --job-name=ct-detect
#SBATCH --account=PAS2136
#SBATCH --partition=gpu
#SBATCH --gpus-per-node=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --array=0-11
#SBATCH --output=logs/ct-detect_%A_%a.out
#SBATCH --error=logs/ct-detect_%A_%a.err

# Camera trap detection SLURM array job
# Each array task processes one camera from detection_config.json
#
# Usage:
#   # First time: set up environment
#   bash submit_detections.sh --setup-env
#
#   # Submit all cameras (array 0-11, 12 cameras with images)
#   sbatch submit_detections.sh
#
#   # Submit specific cameras
#   sbatch --array=0-3 submit_detections.sh
#
#   # Dry run (list cameras without processing)
#   bash submit_detections.sh --list
#
#   # Test with one camera on debug partition
#   sbatch --partition=gpudebug --time=1:00:00 --array=0 submit_detections.sh

set -e

SCRIPT_DIR="/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/camera_traps"
ENV_NAME="ultralytics_env"
OUTPUT_DIR="${SCRIPT_DIR}/detection_results"
CONDA_DIR="/users/PAS2136/kline377/miniconda3"

# Handle non-SLURM invocations
if [[ "$1" == "--setup-env" ]]; then
    echo "Setting up conda environment: ${ENV_NAME}"

    module load cuda/12.4.1

    # Create env from spec if it exists, otherwise from scratch
    if conda env list | grep -q "${ENV_NAME}"; then
        echo "Environment ${ENV_NAME} already exists"
    else
        echo "Creating new environment..."
        conda create -n ${ENV_NAME} python=3.10 -y

        conda activate ${ENV_NAME}

        # Install PyTorch with CUDA
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

        # Install detection stack
        pip install ultralytics sahi open-clip-torch Pillow

        echo "Environment created. Activate with: conda activate ${ENV_NAME}"
    fi
    exit 0
fi

if [[ "$1" == "--list" ]]; then
    conda activate ${ENV_NAME} 2>/dev/null || true
    python "${SCRIPT_DIR}/run_detections.py" --list
    exit 0
fi

# ---- SLURM execution starts here ----

echo "============================================"
echo "Camera Trap Detection - Array Task ${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'unknown')"
echo "Start: $(date)"
echo "============================================"

# Load modules
module load cuda/12.4.1

# Use Python binary directly (conda activation broken due to hardcoded path in conda.sh)
PYTHON="${CONDA_DIR}/envs/${ENV_NAME}/bin/python"

echo "Python: ${PYTHON}"
${PYTHON} --version

# Create output and log directories
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${SCRIPT_DIR}/logs"

# Run detection for this array task
${PYTHON} "${SCRIPT_DIR}/run_detections.py" \
    --array-index ${SLURM_ARRAY_TASK_ID} \
    --output-dir "${OUTPUT_DIR}"

echo ""
echo "============================================"
echo "Finished: $(date)"
echo "============================================"
