"""Metric computation and rollup logic."""

from __future__ import annotations

import pandas as pd

from .deployment_metadata import combine_notes
from .paths import ExperimentPaths


def _add_common_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach storage and rate metrics to a summary dataframe."""

    frame["blank_pct"] = frame["blank_count"] / frame["total_images"] * 100.0
    frame["raw_gb"] = frame["raw_bytes"] / 1e9
    frame["filtered_gb"] = frame["filtered_bytes"] / 1e9
    frame["storage_saved_gb"] = frame["raw_gb"] - frame["filtered_gb"]
    frame["storage_saved_pct"] = (
        frame["storage_saved_gb"] / frame["raw_gb"] * 100.0
    )
    frame["raw_gb_per_day"] = frame["raw_gb"] / frame["deployment_days"]
    frame["filtered_gb_per_day"] = frame["filtered_gb"] / frame["deployment_days"]
    frame["raw_rate_per_hour"] = frame["total_images"] / (frame["deployment_days"] * 24.0)
    frame["tp_rate_per_hour"] = (
        frame["nonblank_images"] / (frame["deployment_days"] * 24.0)
    )
    frame["raw_rate_per_second"] = frame["raw_rate_per_hour"] / 3600.0
    frame["tp_rate_per_second"] = frame["tp_rate_per_hour"] / 3600.0
    frame["throughput_reduction_x"] = (
        frame["raw_rate_per_hour"] / frame["tp_rate_per_hour"]
    )
    return frame


def build_deployment_summary(
    raw_inventory: pd.DataFrame,
    retained_inventory: pd.DataFrame,
    metadata: pd.DataFrame,
) -> pd.DataFrame:
    """Join raw images with retained detections and compute deployment metrics."""

    merged = raw_inventory.merge(
        retained_inventory,
        on=["deployment_id", "image_path"],
        how="left",
    )
    merged["nonblank"] = merged["nonblank"].fillna(0).astype(int)
    merged["blank"] = 1 - merged["nonblank"]

    deployment = (
        merged.groupby(["deployment_id", "campaign", "camera"], as_index=False)
        .agg(
            total_images=("image_path", "size"),
            nonblank_images=("nonblank", "sum"),
            blank_count=("blank", "sum"),
            raw_bytes=("bytes", "sum"),
        )
        .copy()
    )

    filtered_bytes = (
        merged.loc[merged["nonblank"].eq(1)]
        .groupby("deployment_id")["bytes"]
        .sum()
        .rename("filtered_bytes")
    )
    deployment = deployment.merge(filtered_bytes, on="deployment_id", how="left")
    deployment["filtered_bytes"] = deployment["filtered_bytes"].fillna(0).astype("int64")

    deployment = metadata.merge(
        deployment,
        on=["deployment_id", "campaign", "camera"],
        how="outer",
    )

    for column in (
        "total_images",
        "nonblank_images",
        "blank_count",
        "raw_bytes",
        "filtered_bytes",
    ):
        deployment[column] = deployment[column].fillna(0)

    deployment["total_images"] = deployment["total_images"].astype(int)
    deployment["nonblank_images"] = deployment["nonblank_images"].astype(int)
    deployment["blank_count"] = deployment["blank_count"].astype(int)
    deployment["raw_bytes"] = deployment["raw_bytes"].astype("int64")
    deployment["filtered_bytes"] = deployment["filtered_bytes"].astype("int64")

    deployment["data_status"] = "ok"
    deployment.loc[
        deployment["total_images"].eq(0),
        "data_status",
    ] = "no_raw_images_found"
    deployment["include_in_rollup"] = deployment["total_images"].gt(0)

    positive_duration = deployment["deployment_days"].gt(0)
    deployment["blank_pct"] = (
        deployment["blank_count"] / deployment["total_images"] * 100.0
    ).where(deployment["total_images"].gt(0))
    deployment["raw_gb"] = deployment["raw_bytes"] / 1e9
    deployment["filtered_gb"] = deployment["filtered_bytes"] / 1e9
    deployment["storage_saved_gb"] = deployment["raw_gb"] - deployment["filtered_gb"]
    deployment["storage_saved_pct"] = (
        deployment["storage_saved_gb"] / deployment["raw_gb"] * 100.0
    ).where(deployment["raw_gb"].gt(0))
    deployment["raw_gb_per_day"] = (
        deployment["raw_gb"] / deployment["deployment_days"]
    ).where(positive_duration)
    deployment["filtered_gb_per_day"] = (
        deployment["filtered_gb"] / deployment["deployment_days"]
    ).where(positive_duration)
    deployment["raw_rate_per_hour"] = (
        deployment["total_images"] / (deployment["deployment_days"] * 24.0)
    ).where(positive_duration)
    deployment["tp_rate_per_hour"] = (
        deployment["nonblank_images"] / (deployment["deployment_days"] * 24.0)
    ).where(positive_duration)
    deployment["raw_rate_per_second"] = deployment["raw_rate_per_hour"] / 3600.0
    deployment["tp_rate_per_second"] = deployment["tp_rate_per_hour"] / 3600.0
    deployment["throughput_reduction_x"] = (
        deployment["raw_rate_per_hour"] / deployment["tp_rate_per_hour"]
    ).where(deployment["tp_rate_per_hour"].gt(0))

    deployment["notes"] = deployment.apply(
        lambda row: combine_notes(
            [
                row.get("darwin_event_remarks"),
                row.get("darwin_field_notes"),
                row.get("fallback_issue_note"),
            ]
        ),
        axis=1,
    )
    deployment.loc[
        deployment["data_status"].eq("no_raw_images_found"),
        "notes",
    ] = (
        deployment["notes"].where(
            deployment["notes"].eq(""),
            deployment["notes"] + " | ",
        )
        + "No raw image files found under campaign directory."
    ).str.strip(" |")
    deployment["notes"] = deployment["notes"].fillna("")

    return deployment.sort_values(["campaign", "camera"]).reset_index(drop=True)


def summarize_group(
    deployment: pd.DataFrame,
    group_column: str,
    value_name: str,
) -> pd.DataFrame:
    """Summarize deployment metrics at the requested grouping level."""

    rollup_input = deployment.loc[deployment["include_in_rollup"]].copy()
    summary = (
        rollup_input.groupby(group_column, as_index=False)
        .agg(
            deployment_days=("deployment_days", "sum"),
            deployments=("deployment_id", "nunique"),
            total_images=("total_images", "sum"),
            nonblank_images=("nonblank_images", "sum"),
            blank_count=("blank_count", "sum"),
            raw_bytes=("raw_bytes", "sum"),
            filtered_bytes=("filtered_bytes", "sum"),
        )
        .rename(columns={group_column: value_name})
    )
    summary = _add_common_metrics(summary)
    return summary.sort_values(value_name).reset_index(drop=True)


def summarize_overall(deployment: pd.DataFrame) -> pd.DataFrame:
    """Build a single-row overall summary."""

    rollup_input = deployment.loc[deployment["include_in_rollup"]].copy()
    overall = pd.DataFrame(
        [
            {
                "scope": "overall",
                "deployment_days": rollup_input["deployment_days"].sum(),
                "deployments": rollup_input["deployment_id"].nunique(),
                "total_images": rollup_input["total_images"].sum(),
                "nonblank_images": rollup_input["nonblank_images"].sum(),
                "blank_count": rollup_input["blank_count"].sum(),
                "raw_bytes": rollup_input["raw_bytes"].sum(),
                "filtered_bytes": rollup_input["filtered_bytes"].sum(),
            }
        ]
    )
    return _add_common_metrics(overall)


def build_diagnostics(deployment: pd.DataFrame, paths: ExperimentPaths) -> pd.DataFrame:
    """Describe ignored or imperfect inputs used by the analysis."""

    rows = [
        {
            "severity": "warning",
            "artifact": str(paths.all_images_summary_csv),
            "issue": (
                "Excluded from analysis because it repeats every deployment to "
                "the same row count and is not a trustworthy denominator for "
                "blank-rate estimates."
            ),
        }
    ]

    missing_from_darwin = deployment.loc[
        deployment["duration_source"].eq("camera_deployment_metadata_fallback")
        & deployment["include_in_rollup"]
    ]
    for _, row in missing_from_darwin.iterrows():
        rows.append(
            {
                "severity": "info",
                "artifact": row["deployment_id"],
                "issue": (
                    "Deployment duration came from "
                    "camera_deployment_metadata.py because "
                    "darwin_core_events.csv did not provide a matching row."
                ),
            }
        )

    no_image_rows = deployment.loc[deployment["data_status"].eq("no_raw_images_found")]
    for _, row in no_image_rows.iterrows():
        rows.append(
            {
                "severity": "info",
                "artifact": row["deployment_id"],
                "issue": (
                    "Metadata exists for this deployment, but no raw image "
                    "files were found."
                ),
            }
        )

    return pd.DataFrame(rows)
