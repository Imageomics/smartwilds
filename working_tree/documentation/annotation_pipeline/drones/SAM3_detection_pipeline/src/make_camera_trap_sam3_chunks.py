#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


BASE_OUTPUT_ROOT = Path("/fs/scratch/PAS2136/smartwilds_detection")
SUMMARY_JSON = BASE_OUTPUT_ROOT / "camera_trap_coco_image_list_summary.json"
CHUNK_SUMMARY_JSON = BASE_OUTPUT_ROOT / "camera_trap_sam3_chunk_summary.json"
CHUNK_SIZE = 1000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create chunked COCO JSONs and symlink image roots for camera-trap SAM3 jobs."
    )
    parser.add_argument("--summary-json", type=Path, default=SUMMARY_JSON)
    parser.add_argument("--base-output-root", type=Path, default=BASE_OUTPUT_ROOT)
    parser.add_argument("--chunk-summary-json", type=Path, default=CHUNK_SUMMARY_JSON)
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def _relative_to_base(path: Path, base: Path) -> Path:
    try:
        return path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"{path} is not under {base}") from exc


def _ensure_symlink(source: Path, target: Path, *, overwrite: bool) -> None:
    if target.exists() or target.is_symlink():
        if target.is_symlink() and target.readlink() == source:
            return
        if not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing path: {target}")
        target.unlink()

    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source)


def _link_chunk_images(
    *,
    original_image_root: Path,
    chunk_image_root: Path,
    images: list[dict],
    overwrite: bool,
) -> None:
    for image_info in images:
        relative_path = Path(image_info["file_name"])
        if relative_path.is_absolute():
            raise ValueError(f"Expected relative COCO file_name, got: {relative_path}")

        source = original_image_root / relative_path
        target = chunk_image_root / relative_path
        if not source.exists():
            raise FileNotFoundError(f"Missing source image for symlink: {source}")
        _ensure_symlink(source, target, overwrite=overwrite)


def main() -> None:
    args = parse_args()
    if args.chunk_size <= 0:
        raise ValueError("--chunk-size must be greater than 0")

    with args.summary_json.open("r") as handle:
        summary_records = json.load(handle)

    chunk_records = []
    for record in summary_records:
        if record.get("status") != "written":
            continue

        coco_json = Path(record["output_path"])
        original_image_root = Path(record["group_root"])
        camera_trap = original_image_root.name

        relative_coco = _relative_to_base(coco_json, args.base_output_root)
        collection = relative_coco.parts[0]
        chunk_root = coco_json.parent / "sam3_chunks"
        prediction_root = (
            args.base_output_root
            / collection
            / "detections"
            / "camera_traps"
            / camera_trap
            / "chunks"
        )
        viz_root = (
            args.base_output_root
            / collection
            / "detections"
            / "camera_traps"
            / camera_trap
            / "hf_sam3_text_viz"
            / "chunks"
        )
        chunk_root.mkdir(parents=True, exist_ok=True)
        prediction_root.mkdir(parents=True, exist_ok=True)

        with coco_json.open("r") as handle:
            coco = json.load(handle)

        images = coco.get("images", [])
        categories = coco.get("categories", [])
        annotations = coco.get("annotations", [])
        if annotations:
            raise ValueError(f"Expected image-list COCO with no annotations: {coco_json}")

        num_chunks = math.ceil(len(images) / args.chunk_size)
        for chunk_index in range(num_chunks):
            start = chunk_index * args.chunk_size
            end = min(start + args.chunk_size, len(images))
            chunk_images = images[start:end]
            chunk_stem = f"{camera_trap}_chunk_{chunk_index:05d}"
            chunk_dir = chunk_root / chunk_stem
            chunk_image_root = chunk_dir / "images"
            chunk_json = chunk_dir / f"{chunk_stem}_annotations.json"
            output_json = prediction_root / f"{chunk_stem}_annotations_hf_sam3_text_predictions.json"
            viz_dir = viz_root / f"{chunk_stem}_viz"

            _link_chunk_images(
                original_image_root=original_image_root,
                chunk_image_root=chunk_image_root,
                images=chunk_images,
                overwrite=args.overwrite,
            )

            if args.overwrite or not chunk_json.exists():
                chunk_json.parent.mkdir(parents=True, exist_ok=True)
                with chunk_json.open("w") as handle:
                    json.dump(
                        {
                            "images": chunk_images,
                            "annotations": [],
                            "categories": categories,
                        },
                        handle,
                        indent=2,
                    )

            chunk_records.append(
                {
                    "collection": collection,
                    "camera_trap": camera_trap,
                    "chunk_index": chunk_index,
                    "chunk_count": num_chunks,
                    "image_count": len(chunk_images),
                    "original_image_root": str(original_image_root),
                    "image_root": str(chunk_image_root),
                    "coco_json": str(chunk_json),
                    "output_json": str(output_json),
                    "viz_dir": str(viz_dir),
                }
            )

    args.chunk_summary_json.parent.mkdir(parents=True, exist_ok=True)
    with args.chunk_summary_json.open("w") as handle:
        json.dump(chunk_records, handle, indent=2)

    total_images = sum(record["image_count"] for record in chunk_records)
    print(
        f"Wrote {len(chunk_records)} chunks covering {total_images} images "
        f"to {args.chunk_summary_json}"
    )


if __name__ == "__main__":
    main()
