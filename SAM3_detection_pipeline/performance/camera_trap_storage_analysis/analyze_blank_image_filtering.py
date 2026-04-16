from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
RESULTS_DIR = SCRIPT_DIR / "results"
DETECTION_DIR = ROOT / "processing_output" / "detections" / "camera_traps"
DARWIN_EVENTS_CSV = (
    ROOT
    / "documentation"
    / "annotation_pipeline"
    / "camera_traps"
    / "imageomicsthewilds_cameratraps"
    / "src"
    / "03_metadata"
    / "darwin_core_events.csv"
)
DEPLOYMENT_METADATA_PY = (
    ROOT
    / "documentation"
    / "annotation_pipeline"
    / "camera_traps"
    / "imageomicsthewilds_cameratraps"
    / "src"
    / "01_events"
    / "camera_deployment_metadata.py"
)
ALL_IMAGES_SUMMARY_CSV = DETECTION_DIR / "all_images_summary.csv"
CAMERA_TRAP_DIRS = [
    ROOT / "thewilds_20250630_20250703" / "camera_traps",
    ROOT / "thewilds_20250804_20250828" / "camera_traps",
]
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
DEPLOYMENT_RE = re.compile(r"^(?P<camera>.+)_(?P<campaign>\d{8}_\d{8})$")


def parse_deployment_id(deployment_id: str) -> tuple[str, str]:
    match = DEPLOYMENT_RE.match(deployment_id)
    if not match:
        raise ValueError(f"Could not parse deployment id: {deployment_id}")
    return match.group("camera"), match.group("campaign")


def load_fallback_deployment_metadata() -> pd.DataFrame:
    spec = importlib.util.spec_from_file_location(
        "camera_deployment_metadata",
        DEPLOYMENT_METADATA_PY,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load deployment metadata from {DEPLOYMENT_METADATA_PY}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    rows: list[dict[str, object]] = []
    for info in module.DEPLOYMENTS.values():
        deployment_id = f"{info['site_cam']}_{info['campaign']}"
        deploy_date = info["deploy_date"]
        retrieve_date = info["retrieve_date"]
        duration_days = (retrieve_date - deploy_date).total_seconds() / 86400.0
        rows.append(
            {
                "deployment_id": deployment_id,
                "camera": info["site_cam"],
                "campaign": info["campaign"],
                "deployment_days_fallback": duration_days,
                "fallback_issue_note": info.get("issues"),
            }
        )
    return pd.DataFrame(rows)


def load_duration_metadata() -> pd.DataFrame:
    darwin = pd.read_csv(DARWIN_EVENTS_CSV)
    darwin = darwin.rename(
        columns={
            "eventID": "deployment_id",
            "sampleSizeValue": "deployment_days_darwin",
            "eventRemarks": "darwin_event_remarks",
            "fieldNotes": "darwin_field_notes",
        }
    )
    darwin = darwin[
        [
            "deployment_id",
            "deployment_days_darwin",
            "darwin_event_remarks",
            "darwin_field_notes",
        ]
    ].copy()
    darwin["deployment_days_darwin"] = pd.to_numeric(
        darwin["deployment_days_darwin"], errors="coerce"
    )
    darwin[["camera", "campaign"]] = darwin["deployment_id"].apply(
        lambda value: pd.Series(parse_deployment_id(value))
    )

    fallback = load_fallback_deployment_metadata()
    metadata = darwin.merge(
        fallback,
        on=["deployment_id", "camera", "campaign"],
        how="outer",
    )
    metadata["deployment_days"] = metadata["deployment_days_darwin"].combine_first(
        metadata["deployment_days_fallback"]
    )
    metadata["duration_source"] = metadata["deployment_days_darwin"].notna().map(
        {True: "darwin_core_events", False: "camera_deployment_metadata_fallback"}
    )
    return metadata


def build_raw_inventory() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for camera_trap_root in CAMERA_TRAP_DIRS:
        if not camera_trap_root.exists():
            continue

        campaign = camera_trap_root.parent.name.replace("thewilds_", "")
        for dirpath, _, filenames in os.walk(camera_trap_root):
            for filename in filenames:
                if not filename.lower().endswith(IMAGE_SUFFIXES):
                    continue

                image_path = Path(dirpath) / filename
                relative_path = image_path.relative_to(camera_trap_root)
                camera = relative_path.parts[0]
                rows.append(
                    {
                        "image_path": str(image_path),
                        "campaign": campaign,
                        "camera": camera,
                        "deployment_id": f"{camera}_{campaign}",
                        "bytes": image_path.stat().st_size,
                    }
                )

    raw_inventory = pd.DataFrame(rows)
    if raw_inventory.empty:
        raise RuntimeError("No raw camera trap images were found.")
    return raw_inventory


def build_nonblank_inventory() -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for csv_path in sorted(DETECTION_DIR.glob("*_detections_filtered.csv")):
        deployment_id = csv_path.name.replace("_detections_filtered.csv", "")
        detections = pd.read_csv(csv_path, usecols=["image_path"])
        unique_paths = pd.Series(detections["image_path"].dropna().unique(), name="image_path")
        rows.append(
            pd.DataFrame(
                {
                    "image_path": unique_paths.astype(str),
                    "deployment_id": deployment_id,
                    "nonblank": 1,
                }
            )
        )

    if not rows:
        raise RuntimeError(f"No filtered detection CSVs found in {DETECTION_DIR}")
    return pd.concat(rows, ignore_index=True).drop_duplicates(
        subset=["deployment_id", "image_path"]
    )


def combine_notes(parts: list[object]) -> str:
    cleaned: list[str] = []
    for part in parts:
        if pd.isna(part):
            continue
        text = str(part).strip()
        if not text or text in cleaned:
            continue
        cleaned.append(text)
    return " | ".join(cleaned)


def build_deployment_summary(
    raw_inventory: pd.DataFrame,
    nonblank_inventory: pd.DataFrame,
    metadata: pd.DataFrame,
) -> pd.DataFrame:
    merged = raw_inventory.merge(
        nonblank_inventory,
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

    for column in ["total_images", "nonblank_images", "blank_count", "raw_bytes", "filtered_bytes"]:
        deployment[column] = deployment[column].fillna(0)

    deployment["total_images"] = deployment["total_images"].astype(int)
    deployment["nonblank_images"] = deployment["nonblank_images"].astype(int)
    deployment["blank_count"] = deployment["blank_count"].astype(int)
    deployment["raw_bytes"] = deployment["raw_bytes"].astype("int64")
    deployment["filtered_bytes"] = deployment["filtered_bytes"].astype("int64")

    deployment["data_status"] = "ok"
    deployment.loc[deployment["total_images"].eq(0), "data_status"] = "no_raw_images_found"
    deployment["include_in_rollup"] = deployment["total_images"].gt(0)

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
    ).where(deployment["deployment_days"].gt(0))
    deployment["filtered_gb_per_day"] = (
        deployment["filtered_gb"] / deployment["deployment_days"]
    ).where(deployment["deployment_days"].gt(0))
    deployment["raw_rate_per_hour"] = (
        deployment["total_images"] / (deployment["deployment_days"] * 24.0)
    ).where(deployment["deployment_days"].gt(0))
    deployment["tp_rate_per_hour"] = (
        deployment["nonblank_images"] / (deployment["deployment_days"] * 24.0)
    ).where(deployment["deployment_days"].gt(0))
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
        deployment["notes"].where(deployment["notes"].eq(""), deployment["notes"] + " | ")
        + "No raw image files found under campaign directory."
    ).str.strip(" |")
    deployment["notes"] = deployment["notes"].fillna("")

    return deployment.sort_values(["campaign", "camera"]).reset_index(drop=True)


def summarize_group(
    deployment: pd.DataFrame,
    group_col: str,
    value_name: str,
) -> pd.DataFrame:
    rollup_input = deployment.loc[deployment["include_in_rollup"]].copy()
    summary = (
        rollup_input.groupby(group_col, as_index=False)
        .agg(
            deployment_days=("deployment_days", "sum"),
            deployments=("deployment_id", "nunique"),
            total_images=("total_images", "sum"),
            nonblank_images=("nonblank_images", "sum"),
            blank_count=("blank_count", "sum"),
            raw_bytes=("raw_bytes", "sum"),
            filtered_bytes=("filtered_bytes", "sum"),
        )
        .rename(columns={group_col: value_name})
    )
    summary["blank_pct"] = summary["blank_count"] / summary["total_images"] * 100.0
    summary["raw_gb"] = summary["raw_bytes"] / 1e9
    summary["filtered_gb"] = summary["filtered_bytes"] / 1e9
    summary["storage_saved_gb"] = summary["raw_gb"] - summary["filtered_gb"]
    summary["storage_saved_pct"] = summary["storage_saved_gb"] / summary["raw_gb"] * 100.0
    summary["raw_gb_per_day"] = summary["raw_gb"] / summary["deployment_days"]
    summary["filtered_gb_per_day"] = summary["filtered_gb"] / summary["deployment_days"]
    summary["raw_rate_per_hour"] = summary["total_images"] / (summary["deployment_days"] * 24.0)
    summary["tp_rate_per_hour"] = summary["nonblank_images"] / (summary["deployment_days"] * 24.0)
    summary["raw_rate_per_second"] = summary["raw_rate_per_hour"] / 3600.0
    summary["tp_rate_per_second"] = summary["tp_rate_per_hour"] / 3600.0
    summary["throughput_reduction_x"] = summary["raw_rate_per_hour"] / summary["tp_rate_per_hour"]
    return summary.sort_values(value_name).reset_index(drop=True)


def summarize_overall(deployment: pd.DataFrame) -> pd.DataFrame:
    rollup_input = deployment.loc[deployment["include_in_rollup"]].copy()
    total_days = rollup_input["deployment_days"].sum()
    total_images = rollup_input["total_images"].sum()
    nonblank_images = rollup_input["nonblank_images"].sum()
    blank_count = rollup_input["blank_count"].sum()
    raw_bytes = rollup_input["raw_bytes"].sum()
    filtered_bytes = rollup_input["filtered_bytes"].sum()

    overall = pd.DataFrame(
        [
            {
                "scope": "overall",
                "deployment_days": total_days,
                "deployments": rollup_input["deployment_id"].nunique(),
                "total_images": total_images,
                "nonblank_images": nonblank_images,
                "blank_count": blank_count,
                "blank_pct": blank_count / total_images * 100.0,
                "raw_bytes": raw_bytes,
                "filtered_bytes": filtered_bytes,
                "raw_gb": raw_bytes / 1e9,
                "filtered_gb": filtered_bytes / 1e9,
                "storage_saved_gb": (raw_bytes - filtered_bytes) / 1e9,
                "storage_saved_pct": (raw_bytes - filtered_bytes) / raw_bytes * 100.0,
                "raw_gb_per_day": (raw_bytes / 1e9) / total_days,
                "filtered_gb_per_day": (filtered_bytes / 1e9) / total_days,
                "raw_rate_per_hour": total_images / (total_days * 24.0),
                "tp_rate_per_hour": nonblank_images / (total_days * 24.0),
                "raw_rate_per_second": total_images / (total_days * 24.0 * 3600.0),
                "tp_rate_per_second": nonblank_images / (total_days * 24.0 * 3600.0),
                "throughput_reduction_x": total_images / nonblank_images,
            }
        ]
    )
    return overall


def build_diagnostics(deployment: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "severity": "warning",
            "artifact": str(ALL_IMAGES_SUMMARY_CSV),
            "issue": (
                "Excluded from analysis because it repeats every deployment to the same "
                "row count and is not a trustworthy denominator for blank-rate estimates."
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
                    "Deployment duration came from camera_deployment_metadata.py "
                    "because darwin_core_events.csv did not provide a matching row."
                ),
            }
        )

    no_image_rows = deployment.loc[deployment["data_status"].eq("no_raw_images_found")]
    for _, row in no_image_rows.iterrows():
        rows.append(
            {
                "severity": "info",
                "artifact": row["deployment_id"],
                "issue": "Metadata exists for this deployment, but no raw image files were found.",
            }
        )

    return pd.DataFrame(rows)


def write_publication_tables(
    deployment: pd.DataFrame,
    camera_summary: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    overall_summary: pd.DataFrame,
) -> None:
    deployment_included = deployment.loc[deployment["include_in_rollup"]].copy()

    camera_campaign_table = deployment_included[
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
        columns={
            "nonblank_images": "true_positive_images",
        }
    )
    camera_campaign_table.to_csv(RESULTS_DIR / "table_camera_campaign_workload.csv", index=False)

    storage_table = deployment_included[
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
    ]
    storage_table.to_csv(RESULTS_DIR / "table_storage_savings.csv", index=False)

    hardware_table = deployment_included[
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
    ]
    hardware_table.to_csv(RESULTS_DIR / "table_hardware_comparison.csv", index=False)

    camera_rollup = camera_summary[
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
    ].rename(columns={"nonblank_images": "true_positive_images"})
    camera_rollup.to_csv(RESULTS_DIR / "table_camera_rollup.csv", index=False)

    campaign_rollup = campaign_summary[
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
    ].rename(columns={"nonblank_images": "true_positive_images"})
    campaign_rollup.to_csv(RESULTS_DIR / "table_campaign_rollup.csv", index=False)

    overall_rollup = overall_summary[
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
    ].rename(columns={"nonblank_images": "true_positive_images"})
    overall_rollup.to_csv(RESULTS_DIR / "table_overall_rollup.csv", index=False)


def make_storage_figure(
    deployment: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    overall_summary: pd.DataFrame,
) -> None:
    plot_df = deployment.loc[deployment["include_in_rollup"]].copy()
    plot_df = plot_df.sort_values("raw_gb", ascending=True)

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(14, 11),
        gridspec_kw={"height_ratios": [4, 1.4]},
        constrained_layout=True,
    )

    y = range(len(plot_df))
    ax1.barh(y, plot_df["raw_gb"], color="#c8d5b9", label="Raw storage")
    ax1.barh(y, plot_df["filtered_gb"], color="#2d6a4f", label="Post-filter storage")
    ax1.set_yticks(list(y))
    ax1.set_yticklabels(plot_df["deployment_id"])
    ax1.set_xlabel("Storage (GB)")
    ax1.set_title("Experiment 5: Camera Trap Storage Savings from Blank Image Filtering")
    ax1.legend(loc="lower right")

    for idx, (_, row) in enumerate(plot_df.iterrows()):
        ax1.text(
            row["raw_gb"] + max(plot_df["raw_gb"]) * 0.01,
            idx,
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
    )
    rollup = rollup.sort_values("raw_gb", ascending=True)
    y2 = range(len(rollup))
    ax2.barh(y2, rollup["raw_gb"], color="#a9def9", label="Raw storage")
    ax2.barh(y2, rollup["filtered_gb"], color="#1d3557", label="Post-filter storage")
    ax2.set_yticks(list(y2))
    ax2.set_yticklabels(rollup["scope"])
    ax2.set_xlabel("Storage (GB)")
    ax2.set_title("Campaign and Overall Rollups")

    fig.savefig(RESULTS_DIR / "storage_savings_gb.png", dpi=200)


def make_throughput_figure(
    deployment: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    overall_summary: pd.DataFrame,
) -> None:
    plot_df = deployment.loc[deployment["include_in_rollup"]].copy()
    plot_df = plot_df.sort_values("raw_rate_per_hour", ascending=True)

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(14, 11),
        gridspec_kw={"height_ratios": [4, 1.4]},
        constrained_layout=True,
    )

    y = range(len(plot_df))
    ax1.barh(y, plot_df["raw_rate_per_hour"], color="#f4a261", label="Raw image rate")
    ax1.barh(y, plot_df["tp_rate_per_hour"], color="#bc4749", label="True-positive rate")
    ax1.set_yticks(list(y))
    ax1.set_yticklabels(plot_df["deployment_id"])
    ax1.set_xlabel("Images per hour")
    ax1.set_title("Experiment 5: Downstream Throughput Requirement Before vs After Filtering")
    ax1.legend(loc="lower right")

    for idx, (_, row) in enumerate(plot_df.iterrows()):
        label = "n/a" if pd.isna(row["throughput_reduction_x"]) else f"{row['throughput_reduction_x']:.1f}x"
        ax1.text(
            row["raw_rate_per_hour"] + max(plot_df["raw_rate_per_hour"]) * 0.01,
            idx,
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
    )
    rollup = rollup.sort_values("raw_rate_per_hour", ascending=True)
    y2 = range(len(rollup))
    ax2.barh(y2, rollup["raw_rate_per_hour"], color="#ffd166", label="Raw image rate")
    ax2.barh(y2, rollup["tp_rate_per_hour"], color="#6a4c93", label="True-positive rate")
    ax2.set_yticks(list(y2))
    ax2.set_yticklabels(rollup["scope"])
    ax2.set_xlabel("Images per hour")
    ax2.set_title("Campaign and Overall Rollups")

    fig.savefig(RESULTS_DIR / "throughput_comparison.png", dpi=200)


def write_report(
    deployment: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    overall_summary: pd.DataFrame,
) -> None:
    overall = overall_summary.iloc[0]
    top_storage = deployment.loc[deployment["include_in_rollup"]].sort_values(
        "storage_saved_gb", ascending=False
    )
    top_storage = top_storage[["deployment_id", "storage_saved_gb", "storage_saved_pct"]].head(3)

    lines = [
        "# Experiment 5: Storage Savings from Edge Blank Image Filtering",
        "",
        "## Key Results",
        "",
        f"- Total raw images analyzed: {int(overall['total_images']):,}",
        (
            f"- Images with no retained detections under the current camera-trap pipeline: "
            f"{int(overall['blank_count']):,} ({overall['blank_pct']:.2f}%)"
        ),
        f"- Raw storage volume: {overall['raw_gb']:.2f} GB",
        f"- Post-filter storage volume: {overall['filtered_gb']:.2f} GB",
        f"- Storage saved by filtering: {overall['storage_saved_gb']:.2f} GB ({overall['storage_saved_pct']:.2f}%)",
        f"- Average raw arrival rate: {overall['raw_rate_per_hour']:.2f} images/hour",
        f"- Average true-positive arrival rate: {overall['tp_rate_per_hour']:.2f} images/hour",
        f"- Downstream throughput reduction: {overall['throughput_reduction_x']:.2f}x",
        "",
        "## Campaign Rollup",
        "",
    ]

    for _, row in campaign_summary.sort_values("campaign").iterrows():
        lines.append(
            f"- {row['campaign']}: {int(row['total_images']):,} images, "
            f"{row['blank_pct']:.2f}% blank, {row['storage_saved_pct']:.2f}% storage saved, "
            f"{row['throughput_reduction_x']:.2f}x throughput reduction"
        )

    lines.extend(
        [
            "",
            "## Largest Absolute Storage Savings",
            "",
        ]
    )

    for _, row in top_storage.iterrows():
        lines.append(
            f"- {row['deployment_id']}: {row['storage_saved_gb']:.2f} GB saved "
            f"({row['storage_saved_pct']:.2f}%)"
        )

    lines.extend(
        [
            "",
        "## Notes",
        "",
        "- Raw-image counts and storage volumes come from rescanning the camera trap directories on disk.",
        (
            "- In this experiment, a filtered-out image is operationally treated as blank: "
            "it has no retained detections in the current YOLO/SAHI/BioCLIP pipeline outputs."
        ),
        "- True-positive arrival rate refers to images retained by the detector pipeline, not human-verified ground truth events.",
        "- The combined `all_images_summary.csv` file was not used because it duplicates rows and would bias blank-rate estimates.",
        ]
    )

    (RESULTS_DIR / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    metadata = load_duration_metadata()
    raw_inventory = build_raw_inventory()
    nonblank_inventory = build_nonblank_inventory()
    deployment = build_deployment_summary(raw_inventory, nonblank_inventory, metadata)
    camera_summary = summarize_group(deployment, "camera", "camera")
    campaign_summary = summarize_group(deployment, "campaign", "campaign")
    overall_summary = summarize_overall(deployment)
    diagnostics = build_diagnostics(deployment)

    deployment.to_csv(RESULTS_DIR / "deployment_summary.csv", index=False)
    camera_summary.to_csv(RESULTS_DIR / "camera_summary.csv", index=False)
    campaign_summary.to_csv(RESULTS_DIR / "campaign_summary.csv", index=False)
    overall_summary.to_csv(RESULTS_DIR / "overall_summary.csv", index=False)
    diagnostics.to_csv(RESULTS_DIR / "diagnostics.csv", index=False)
    write_publication_tables(deployment, camera_summary, campaign_summary, overall_summary)

    make_storage_figure(deployment, campaign_summary, overall_summary)
    make_throughput_figure(deployment, campaign_summary, overall_summary)
    write_report(deployment, campaign_summary, overall_summary)

    print(f"Wrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
