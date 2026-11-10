#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP3_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-exp3}"

python "$EXP3_DIR/3.1/benchmark_table.py"
python "$SCRIPT_DIR/prediction_model.py"
python "$SCRIPT_DIR/plot_predicted_grid.py"
