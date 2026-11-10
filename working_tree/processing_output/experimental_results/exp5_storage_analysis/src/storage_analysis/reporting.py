"""Writers for CSV tables and markdown summaries."""

from __future__ import annotations

import pandas as pd

from .paths import ExperimentPaths


def write_summary_outputs(
    deployment: pd.DataFrame,
    camera_summary: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    overall_summary: pd.DataFrame,
    diagnostics: pd.DataFrame,
    paths: ExperimentPaths,
) -> None:
    """Write core CSV outputs."""

    deployment.to_csv(paths.results_dir / "deployment_summary.csv", index=False)
    camera_summary.to_csv(paths.results_dir / "camera_summary.csv", index=False)
    campaign_summary.to_csv(paths.results_dir / "campaign_summary.csv", index=False)
    overall_summary.to_csv(paths.results_dir / "overall_summary.csv", index=False)
    diagnostics.to_csv(paths.results_dir / "diagnostics.csv", index=False)


def write_publication_tables(
    deployment: pd.DataFrame,
    camera_summary: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    overall_summary: pd.DataFrame,
    paths: ExperimentPaths,
) -> None:
    """Write paper-oriented CSV tables."""

    included = deployment.loc[deployment["include_in_rollup"]].copy()

    included[
        [
            "campaign",
            "camera",
            "deployment_id",
            "total_images",
            "blank_count",
            "blank_pct",
            "nonblank_images",
            "raw_rate_per_hour",
            "tp_rate_per_hour",
        ]
    ].rename(
        columns={"nonblank_images": "true_positive_images"}
    ).to_csv(paths.results_dir / "table_camera_campaign_workload.csv", index=False)

    included[
        [
            "campaign",
            "camera",
            "deployment_id",
            "raw_gb",
            "filtered_gb",
            "storage_saved_gb",
            "storage_saved_pct",
            "raw_gb_per_day",
            "filtered_gb_per_day",
        ]
    ].to_csv(paths.results_dir / "table_storage_savings.csv", index=False)

    included[
        [
            "campaign",
            "camera",
            "deployment_id",
            "raw_rate_per_hour",
            "tp_rate_per_hour",
            "raw_rate_per_second",
            "tp_rate_per_second",
            "throughput_reduction_x",
        ]
    ].to_csv(paths.results_dir / "table_hardware_comparison.csv", index=False)

    camera_summary[
        [
            "camera",
            "deployments",
            "deployment_days",
            "total_images",
            "blank_count",
            "blank_pct",
            "nonblank_images",
            "raw_gb",
            "filtered_gb",
            "storage_saved_pct",
            "raw_rate_per_hour",
            "tp_rate_per_hour",
            "throughput_reduction_x",
        ]
    ].rename(
        columns={"nonblank_images": "true_positive_images"}
    ).to_csv(paths.results_dir / "table_camera_rollup.csv", index=False)

    campaign_summary[
        [
            "campaign",
            "deployments",
            "deployment_days",
            "total_images",
            "blank_count",
            "blank_pct",
            "nonblank_images",
            "raw_gb",
            "filtered_gb",
            "storage_saved_pct",
            "raw_rate_per_hour",
            "tp_rate_per_hour",
            "throughput_reduction_x",
        ]
    ].rename(
        columns={"nonblank_images": "true_positive_images"}
    ).to_csv(paths.results_dir / "table_campaign_rollup.csv", index=False)

    overall_summary[
        [
            "scope",
            "deployments",
            "deployment_days",
            "total_images",
            "blank_count",
            "blank_pct",
            "nonblank_images",
            "raw_gb",
            "filtered_gb",
            "storage_saved_pct",
            "raw_rate_per_hour",
            "tp_rate_per_hour",
            "throughput_reduction_x",
        ]
    ].rename(
        columns={"nonblank_images": "true_positive_images"}
    ).to_csv(paths.results_dir / "table_overall_rollup.csv", index=False)


def write_report(
    deployment: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    overall_summary: pd.DataFrame,
    paths: ExperimentPaths,
) -> None:
    """Write the human-readable markdown report."""

    overall = overall_summary.iloc[0]
    top_storage = deployment.loc[deployment["include_in_rollup"]].sort_values(
        "storage_saved_gb",
        ascending=False,
    )
    top_storage = top_storage[
        ["deployment_id", "storage_saved_gb", "storage_saved_pct"]
    ].head(3)

    lines = [
        "# Experiment 5: Storage Savings from Edge Blank Image Filtering",
        "",
        "## Key Results",
        "",
        f"- Total raw images analyzed: {int(overall['total_images']):,}",
        (
            "- Images with no retained detections under the current "
            f"camera-trap pipeline: {int(overall['blank_count']):,} "
            f"({overall['blank_pct']:.2f}%)"
        ),
        f"- Raw storage volume: {overall['raw_gb']:.2f} GB",
        f"- Post-filter storage volume: {overall['filtered_gb']:.2f} GB",
        (
            "- Storage saved by filtering: "
            f"{overall['storage_saved_gb']:.2f} GB "
            f"({overall['storage_saved_pct']:.2f}%)"
        ),
        f"- Average raw arrival rate: {overall['raw_rate_per_hour']:.2f} images/hour",
        (
            "- Average true-positive arrival rate: "
            f"{overall['tp_rate_per_hour']:.2f} images/hour"
        ),
        (
            "- Downstream throughput reduction: "
            f"{overall['throughput_reduction_x']:.2f}x"
        ),
        "",
        "## Campaign Rollup",
        "",
    ]

    for _, row in campaign_summary.sort_values("campaign").iterrows():
        lines.append(
            f"- {row['campaign']}: {int(row['total_images']):,} images, "
            f"{row['blank_pct']:.2f}% blank, "
            f"{row['storage_saved_pct']:.2f}% storage saved, "
            f"{row['throughput_reduction_x']:.2f}x throughput reduction"
        )

    lines.extend(["", "## Largest Absolute Storage Savings", ""])

    for _, row in top_storage.iterrows():
        lines.append(
            f"- {row['deployment_id']}: {row['storage_saved_gb']:.2f} GB "
            f"saved ({row['storage_saved_pct']:.2f}%)"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            (
                "- Raw-image counts and storage volumes come from rescanning "
                "the camera trap directories on disk."
            ),
            (
                "- In this experiment, a filtered-out image is operationally "
                "treated as blank: it has no retained detections in the current "
                "YOLO/SAHI/BioCLIP pipeline outputs."
            ),
            (
                "- True-positive arrival rate refers to images retained by the "
                "detector pipeline, not human-verified ground truth events."
            ),
            (
                "- The combined `all_images_summary.csv` file was not used "
                "because it duplicates rows and would bias blank-rate estimates."
            ),
        ]
    )

    (paths.results_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
