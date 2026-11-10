"""Figure generation for storage-analysis outputs."""

from __future__ import annotations

import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .paths import ExperimentPaths


def write_storage_figure(
    deployment: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    overall_summary: pd.DataFrame,
    paths: ExperimentPaths,
) -> None:
    """Write the raw-vs-filtered storage figure."""

    plot_df = deployment.loc[deployment["include_in_rollup"]].copy()
    plot_df = plot_df.sort_values("raw_gb", ascending=True)

    figure, (axis_main, axis_rollup) = plt.subplots(
        2,
        1,
        figsize=(14, 11),
        gridspec_kw={"height_ratios": [4, 1.4]},
        constrained_layout=True,
    )

    y_positions = range(len(plot_df))
    axis_main.barh(
        y_positions,
        plot_df["raw_gb"],
        color="#c8d5b9",
        label="Raw storage",
    )
    axis_main.barh(
        y_positions,
        plot_df["filtered_gb"],
        color="#2d6a4f",
        label="Post-filter storage",
    )
    axis_main.set_yticks(list(y_positions))
    axis_main.set_yticklabels(plot_df["deployment_id"])
    axis_main.set_xlabel("Storage (GB)")
    axis_main.set_title(
        "Experiment 5: Camera Trap Storage Savings from Blank Image Filtering"
    )
    axis_main.legend(loc="lower right")

    raw_max = max(plot_df["raw_gb"]) if not plot_df.empty else 0.0
    for index, (_, row) in enumerate(plot_df.iterrows()):
        axis_main.text(
            row["raw_gb"] + raw_max * 0.01,
            index,
            f"{row['storage_saved_pct']:.1f}% saved",
            va="center",
            fontsize=8,
        )

    rollup = pd.concat(
        [
            campaign_summary.rename(columns={"campaign": "scope"})[
                ["scope", "raw_gb", "filtered_gb"]
            ],
            overall_summary[["scope", "raw_gb", "filtered_gb"]],
        ],
        ignore_index=True,
    ).sort_values("raw_gb", ascending=True)

    rollup_positions = range(len(rollup))
    axis_rollup.barh(
        rollup_positions,
        rollup["raw_gb"],
        color="#a9def9",
        label="Raw storage",
    )
    axis_rollup.barh(
        rollup_positions,
        rollup["filtered_gb"],
        color="#1d3557",
        label="Post-filter storage",
    )
    axis_rollup.set_yticks(list(rollup_positions))
    axis_rollup.set_yticklabels(rollup["scope"])
    axis_rollup.set_xlabel("Storage (GB)")
    axis_rollup.set_title("Campaign and Overall Rollups")

    figure.savefig(paths.results_dir / "storage_savings_gb.png", dpi=200)


def write_throughput_figure(
    deployment: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    overall_summary: pd.DataFrame,
    paths: ExperimentPaths,
) -> None:
    """Write the raw-vs-retained throughput figure."""

    plot_df = deployment.loc[deployment["include_in_rollup"]].copy()
    plot_df = plot_df.sort_values("raw_rate_per_hour", ascending=True)

    figure, (axis_main, axis_rollup) = plt.subplots(
        2,
        1,
        figsize=(14, 11),
        gridspec_kw={"height_ratios": [4, 1.4]},
        constrained_layout=True,
    )

    y_positions = range(len(plot_df))
    axis_main.barh(
        y_positions,
        plot_df["raw_rate_per_hour"],
        color="#f4a261",
        label="Raw image rate",
    )
    axis_main.barh(
        y_positions,
        plot_df["tp_rate_per_hour"],
        color="#bc4749",
        label="True-positive rate",
    )
    axis_main.set_yticks(list(y_positions))
    axis_main.set_yticklabels(plot_df["deployment_id"])
    axis_main.set_xlabel("Images per hour")
    axis_main.set_title(
        "Experiment 5: Downstream Throughput Requirement Before vs After Filtering"
    )
    axis_main.legend(loc="lower right")

    raw_rate_max = max(plot_df["raw_rate_per_hour"]) if not plot_df.empty else 0.0
    for index, (_, row) in enumerate(plot_df.iterrows()):
        label = (
            "n/a"
            if pd.isna(row["throughput_reduction_x"])
            else f"{row['throughput_reduction_x']:.1f}x"
        )
        axis_main.text(
            row["raw_rate_per_hour"] + raw_rate_max * 0.01,
            index,
            label,
            va="center",
            fontsize=8,
        )

    rollup = pd.concat(
        [
            campaign_summary.rename(columns={"campaign": "scope"})[
                ["scope", "raw_rate_per_hour", "tp_rate_per_hour"]
            ],
            overall_summary[["scope", "raw_rate_per_hour", "tp_rate_per_hour"]],
        ],
        ignore_index=True,
    ).sort_values("raw_rate_per_hour", ascending=True)

    rollup_positions = range(len(rollup))
    axis_rollup.barh(
        rollup_positions,
        rollup["raw_rate_per_hour"],
        color="#ffd166",
        label="Raw image rate",
    )
    axis_rollup.barh(
        rollup_positions,
        rollup["tp_rate_per_hour"],
        color="#6a4c93",
        label="True-positive rate",
    )
    axis_rollup.set_yticks(list(rollup_positions))
    axis_rollup.set_yticklabels(rollup["scope"])
    axis_rollup.set_xlabel("Images per hour")
    axis_rollup.set_title("Campaign and Overall Rollups")

    figure.savefig(paths.results_dir / "throughput_comparison.png", dpi=200)
