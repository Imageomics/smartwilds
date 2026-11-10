"""Top-level orchestration for Experiment 5 storage analysis."""

from __future__ import annotations

from .deployment_metadata import load_duration_metadata
from .inventory import build_raw_inventory, build_retained_detection_inventory
from .metrics import (
    build_deployment_summary,
    build_diagnostics,
    summarize_group,
    summarize_overall,
)
from .paths import ExperimentPaths
from .reporting import (
    write_publication_tables,
    write_report,
    write_summary_outputs,
)
from .visualization import write_storage_figure, write_throughput_figure


def run_analysis(paths: ExperimentPaths) -> None:
    """Run the full storage-analysis pipeline."""

    paths.results_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_duration_metadata(paths)
    raw_inventory = build_raw_inventory(paths)
    retained_inventory = build_retained_detection_inventory(paths)

    deployment = build_deployment_summary(
        raw_inventory,
        retained_inventory,
        metadata,
    )
    camera_summary = summarize_group(deployment, "camera", "camera")
    campaign_summary = summarize_group(deployment, "campaign", "campaign")
    overall_summary = summarize_overall(deployment)
    diagnostics = build_diagnostics(deployment, paths)

    write_summary_outputs(
        deployment,
        camera_summary,
        campaign_summary,
        overall_summary,
        diagnostics,
        paths,
    )
    write_publication_tables(
        deployment,
        camera_summary,
        campaign_summary,
        overall_summary,
        paths,
    )
    write_storage_figure(deployment, campaign_summary, overall_summary, paths)
    write_throughput_figure(deployment, campaign_summary, overall_summary, paths)
    write_report(deployment, campaign_summary, overall_summary, paths)
