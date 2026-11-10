#!/bin/bash
#SBATCH --job-name=xmodal-arrival
#SBATCH --account=PAS2136
#SBATCH --partition=cpu
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=3:00:00
#SBATCH --output=logs/xmodal-arrival_%j.out
#SBATCH --error=logs/xmodal-arrival_%j.err

# Cross-Modal Arrival Rates Analysis (Experiment 1)
# Runs extract_wilds_multimodal.py to extract timestamps from all 4 modalities,
# perform ADAE change point analysis, and generate plots.
#
# Usage:
#   # Submit full analysis (all modalities, analyze + plot)
#   sbatch submit_arrival_rates.sh
#
#   # Run a single modality
#   sbatch submit_arrival_rates.sh --modality camera_trap
#
#   # Run specific campaign only
#   sbatch submit_arrival_rates.sh --campaign campaign1
#
#   # Dry run locally (just extraction, no analysis)
#   bash submit_arrival_rates.sh --no-analyze
#
#   # Quick test on debug partition
#   sbatch --partition=debug-cpu --time=0:30:00 submit_arrival_rates.sh --modality bioacoustic

set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_DIR="/fs/ess/PAS2136/TheWilds2025"
SCRIPT_DIR="${PROJECT_DIR}/processing_output/experimental_results/exp1_cross_modal_arrival_rates"
ADAE_DIR="${PROJECT_DIR}/documentation/adae_model"
EXTRACT_SCRIPT="${ADAE_DIR}/extract_wilds_multimodal.py"
OUTPUT_DIR="${SCRIPT_DIR}/results"
CONDA_DIR="/users/PAS2136/kline377/miniconda3"
ENV_NAME="cv_processing_env"
PYTHON="${CONDA_DIR}/envs/${ENV_NAME}/bin/python"

# ---------------------------------------------------------------------------
# Parse wrapper arguments
# ---------------------------------------------------------------------------
MODALITY="all"
CAMPAIGN="all"
DO_ANALYZE=true
DO_PLOT=true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --modality)
            MODALITY="$2"; shift 2 ;;
        --campaign)
            CAMPAIGN="$2"; shift 2 ;;
        --no-analyze)
            DO_ANALYZE=false; shift ;;
        --no-plot)
            DO_PLOT=false; shift ;;
        *)
            echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${SCRIPT_DIR}/logs"

echo "============================================"
echo "Cross-Modal Arrival Rates Analysis"
echo "Node: $(hostname)"
echo "Modality: ${MODALITY}"
echo "Campaign: ${CAMPAIGN}"
echo "Analyze: ${DO_ANALYZE}"
echo "Plot: ${DO_PLOT}"
echo "Output: ${OUTPUT_DIR}"
echo "Start: $(date)"
echo "============================================"

echo "Python: ${PYTHON}"
${PYTHON} --version

# ---------------------------------------------------------------------------
# Build command
# ---------------------------------------------------------------------------
CMD="${PYTHON} ${EXTRACT_SCRIPT}"
CMD+=" --modality ${MODALITY}"
CMD+=" --campaign ${CAMPAIGN}"
CMD+=" --output-dir ${OUTPUT_DIR}"

if [[ "${DO_ANALYZE}" == true ]]; then
    CMD+=" --analyze"
fi

if [[ "${DO_PLOT}" == true ]]; then
    CMD+=" --plot"
fi

echo ""
echo "Running: ${CMD}"
echo ""

eval ${CMD}

echo ""
echo "============================================"
echo "Finished: $(date)"
echo "============================================"
echo ""
echo "Results in: ${OUTPUT_DIR}"
ls -lh "${OUTPUT_DIR}/"
