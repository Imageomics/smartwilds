#!/usr/bin/env bash
set -euo pipefail

# Directory containing this launcher script:
#   .../processing_output/experimental_results/storage_analysis
EXPERIMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Root of the TheWilds2025 workspace:
#   /fs/ess/PAS2136/TheWilds2025
# The script changes into this directory so that all relative paths used by
# the Python analysis resolve exactly the same way every time.
PROJECT_ROOT="$(cd "${EXPERIMENT_DIR}/../../.." && pwd)"

# Python source directory containing the `storage_analysis` package.
SRC_DIR="${EXPERIMENT_DIR}/src"

# Output directory written by the analysis.
RESULTS_DIR="${EXPERIMENT_DIR}/results"

cd "${PROJECT_ROOT}"

echo "Running Experiment 5 storage-analysis pipeline..."
echo "Project root: ${PROJECT_ROOT}"
echo "  This is the TheWilds2025 workspace root."
echo "Experiment directory: ${EXPERIMENT_DIR}"
echo "  This folder stores the Experiment 5 launcher, README, analysis script, and results."
echo "Python source directory: ${SRC_DIR}"
echo "  This contains the storage_analysis package and modular analysis code."
echo "Results directory: ${RESULTS_DIR}"
echo "  This is where CSV tables, figures, diagnostics, and the report will be written."

PYTHONPATH="${SRC_DIR}${PYTHONPATH:+:${PYTHONPATH}}" python -m storage_analysis

echo
echo "Finished. Results written to:"
echo "  ${RESULTS_DIR}"
