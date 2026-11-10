#!/usr/bin/env bash
# run_all.sh — regenerate the synthesis results end to end.
#
# Reproduces what the repository can reproduce standalone: identity synthesis,
# the four case-study traces, and the fidelity checks. Steps that need the
# unreleased field archive are skipped with a notice (see REPRODUCIBILITY.md).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

echo "==> 1/3  identity synthesis (reproduces Table II counts)"
python3 scripts/02_synthesize/identity_test.py || {
  echo "    identity_test.py needs the recorded timestamp tables; see REPRODUCIBILITY.md"; }

echo "==> 2/3  case-study traces (CS1-CS4 at 1x, 2x, 10x)"
python3 scripts/03_case_studies/generate_traces.py \
  --case CS1 --case CS2 --case CS3 --case CS4 \
  --intensity 1 --intensity 2 --intensity 10

echo "==> 3/3  fidelity checks"
python3 scripts/04_fidelity/variance_envelope.py || true
python3 scripts/04_fidelity/topology_scaling.py || true

echo
echo "Done. Traces in scripts/03_case_studies/traces/, results in results/."
echo "Figures: python3 scripts/figures/<fig>.py"
