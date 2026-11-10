"""CLI entrypoint for Experiment 5 storage analysis."""

from __future__ import annotations

from pathlib import Path

from .paths import build_paths
from .pipeline import run_analysis


def main() -> None:
    """Run the analysis using the current experiment directory."""

    experiment_dir = Path(__file__).resolve().parents[2]
    paths = build_paths(experiment_dir)
    run_analysis(paths)
    print(f"Wrote results to {paths.results_dir}")
