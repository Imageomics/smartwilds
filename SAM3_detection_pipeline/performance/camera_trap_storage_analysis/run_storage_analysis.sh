#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

cd "${PROJECT_ROOT}"

echo "Running Experiment 5 storage-analysis pipeline..."
echo "Project root: ${PROJECT_ROOT}"
echo "Analysis directory: ${SCRIPT_DIR}"

python "${SCRIPT_DIR}/analyze_blank_image_filtering.py"

echo
echo "Finished. Results written to:"
echo "  ${SCRIPT_DIR}/results"
