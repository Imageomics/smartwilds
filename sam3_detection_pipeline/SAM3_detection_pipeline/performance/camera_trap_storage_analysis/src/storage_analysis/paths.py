"""Filesystem paths and immutable analysis configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


@dataclass(frozen=True)
class ExperimentPaths:
    """Resolved filesystem paths used by the storage-analysis pipeline."""

    experiment_dir: Path
    project_root: Path
    src_dir: Path
    results_dir: Path
    detection_dir: Path
    darwin_events_csv: Path
    deployment_metadata_py: Path
    all_images_summary_csv: Path
    camera_trap_dirs: tuple[Path, ...]


def build_paths(experiment_dir: Path) -> ExperimentPaths:
    """Build all canonical paths relative to the experiment directory."""

    project_root = experiment_dir.parents[2]
    src_dir = experiment_dir / "src"
    detection_dir = project_root / "processing_output" / "detections" / "camera_traps"

    return ExperimentPaths(
        experiment_dir=experiment_dir,
        project_root=project_root,
        src_dir=src_dir,
        results_dir=experiment_dir / "results",
        detection_dir=detection_dir,
        darwin_events_csv=(
            project_root
            / "documentation"
            / "annotation_pipeline"
            / "camera_traps"
            / "imageomicsthewilds_cameratraps"
            / "src"
            / "03_metadata"
            / "darwin_core_events.csv"
        ),
        deployment_metadata_py=(
            project_root
            / "documentation"
            / "annotation_pipeline"
            / "camera_traps"
            / "imageomicsthewilds_cameratraps"
            / "src"
            / "01_events"
            / "camera_deployment_metadata.py"
        ),
        all_images_summary_csv=detection_dir / "all_images_summary.csv",
        camera_trap_dirs=(
            project_root / "thewilds_20250630_20250703" / "camera_traps",
            project_root / "thewilds_20250804_20250828" / "camera_traps",
        ),
    )
