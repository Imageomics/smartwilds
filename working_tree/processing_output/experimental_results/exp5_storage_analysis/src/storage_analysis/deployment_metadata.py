"""Deployment metadata loading and normalization helpers."""

from __future__ import annotations

import importlib.util
import re

import pandas as pd

from .paths import ExperimentPaths

DEPLOYMENT_ID_PATTERN = re.compile(r"^(?P<camera>.+)_(?P<campaign>\d{8}_\d{8})$")


def parse_deployment_id(deployment_id: str) -> tuple[str, str]:
    """Split `<camera>_<campaign>` into its camera and campaign parts."""

    match = DEPLOYMENT_ID_PATTERN.match(deployment_id)
    if not match:
        raise ValueError(f"Could not parse deployment id: {deployment_id}")
    return match.group("camera"), match.group("campaign")


def load_python_deployment_metadata(paths: ExperimentPaths) -> pd.DataFrame:
    """Load deployment durations from `camera_deployment_metadata.py`."""

    spec = importlib.util.spec_from_file_location(
        "camera_deployment_metadata",
        paths.deployment_metadata_py,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load deployment metadata from {paths.deployment_metadata_py}"
        )

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


def load_duration_metadata(paths: ExperimentPaths) -> pd.DataFrame:
    """Load duration metadata, preferring Darwin Core when available."""

    darwin = pd.read_csv(paths.darwin_events_csv)
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
        darwin["deployment_days_darwin"],
        errors="coerce",
    )
    darwin[["camera", "campaign"]] = darwin["deployment_id"].apply(
        lambda value: pd.Series(parse_deployment_id(value))
    )

    fallback = load_python_deployment_metadata(paths)
    metadata = darwin.merge(
        fallback,
        on=["deployment_id", "camera", "campaign"],
        how="outer",
    )
    metadata["deployment_days"] = metadata["deployment_days_darwin"].combine_first(
        metadata["deployment_days_fallback"]
    )
    metadata["duration_source"] = metadata["deployment_days_darwin"].notna().map(
        {
            True: "darwin_core_events",
            False: "camera_deployment_metadata_fallback",
        }
    )
    return metadata


def combine_notes(parts: list[object]) -> str:
    """Combine note fragments while removing blanks and duplicates."""

    cleaned: list[str] = []
    for part in parts:
        if pd.isna(part):
            continue
        text = str(part).strip()
        if not text or text in cleaned:
            continue
        cleaned.append(text)
    return " | ".join(cleaned)
