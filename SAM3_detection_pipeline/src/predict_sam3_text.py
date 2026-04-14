#!/usr/bin/env python3
from __future__ import annotations

"""
Run Hugging Face SAM3 text-prompted inference for one image or a COCO image set.

Example:
    python predict_sam3_text.py --help
"""

import argparse
import gc
import json
from pathlib import Path

import torch
from PIL import Image, UnidentifiedImageError
from tqdm import tqdm

from bioclip_helper import BioClipHelper, SMARTWILDS_ZERO_SHOT_SPECIES
from hf_sam3_detector import HuggingFaceSAM3TextDetector
from utils import draw_detections


PROMPTS = ["animal", "person", "vehicle"]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

MODEL_ID = "facebook/sam3"
CONFIDENCE_THRESHOLD = 0.5
MASK_THRESHOLD = 0.5
NMS_IOU = 0.5
BATCH_SIZE = 12
RETURN_MASKS = False
VIZ_EVERY = 10
ENABLE_BIOCLIP = False
BIOCLIP_ANIMAL_CATEGORY_NAMES = ("animal",)
BIOCLIP_ZERO_SHOT_TOPK = 1
BIOCLIP_CROP_EXPANSION_FACTOR = 1.0
BIOCLIP_ZERO_SHOT_SPECIES = list(SMARTWILDS_ZERO_SHOT_SPECIES)

DEFAULT_RUN_MODE = "coco"
DEFAULT_IMAGE_PATH = "/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250701_parrotanafi_1/20250703_parrotanafi_1_VID_002_frames/VID_002_000001.png"
DEFAULT_COCO_JSON = "/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames/VID_004_annotations.json"
DEFAULT_IMAGE_ROOT = "/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004_frames"
DEFAULT_OUTPUT_JSON = "/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/VID_004_annotations_hf_sam3_text_predictions.json"
DEFAULT_VIZ_DIR = "/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_viz"
DEFAULT_BIOCLIP_VIZ_DIR = "/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/outputs/sam3_hf_outputs/20250703_parrotanafi_5/20250703_parrotanafi_5_VID_004/hf_sam3_text_bioclip_viz"


def _has_bioclip_predictions(detections) -> bool:
    return any("bioclip" in det for det in detections)


def _json_detection(det: dict) -> dict:
    payload = {key: value for key, value in det.items() if key != "mask"}
    if "mask" in det:
        payload["mask"] = det["mask"].astype(int).tolist()
    return payload


def _build_annotation(
    *,
    annotation_id: int,
    image_id: int,
    detection: dict,
) -> dict:
    x1, y1, x2, y2 = detection["xyxy"]
    width = max(0.0, x2 - x1)
    height = max(0.0, y2 - y1)
    annotation = {
        "id": annotation_id,
        "image_id": image_id,
        "category_id": detection["category_id"],
        "category_name": detection["category_name"],
        "bbox": [x1, y1, width, height],
        "area": width * height,
        "score": detection["score"],
        "iscrowd": 0,
    }
    if "bioclip" in detection:
        annotation["bioclip"] = detection["bioclip"]
    if "mask" in detection:
        annotation["mask"] = detection["mask"].astype(int).tolist()
    return annotation


def _open_coco_output(
    output_json: Path,
    *,
    images: list[dict],
    categories: list[dict],
):
    output_json.parent.mkdir(parents=True, exist_ok=True)
    handle = output_json.open("w")
    handle.write("{\n  \"images\": ")
    json.dump(images, handle, indent=2)
    handle.write(",\n  \"categories\": ")
    json.dump(categories, handle, indent=2)
    handle.write(",\n  \"annotations\": [\n")
    return handle


def _write_annotation(handle, annotation: dict, *, is_first: bool) -> bool:
    if not is_first:
        handle.write(",\n")
    json.dump(annotation, handle, indent=2)
    return False


def _build_bioclip_helper(
    *,
    bioclip_device: str,
    bioclip_batch_size: int,
) -> BioClipHelper:
    return BioClipHelper(
        zero_shot_device=bioclip_device,
        zero_shot_species=BIOCLIP_ZERO_SHOT_SPECIES,
        zero_shot_topk=BIOCLIP_ZERO_SHOT_TOPK,
        batch_size=bioclip_batch_size,
        crop_expansion_factor=BIOCLIP_CROP_EXPANSION_FACTOR,
        animal_category_names=BIOCLIP_ANIMAL_CATEGORY_NAMES,
    )


def _parse_prompts(values: list[str]) -> list[str]:
    prompts = [value.strip() for value in values if value.strip()]
    if not prompts:
        raise ValueError("At least one non-empty prompt is required")
    return prompts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Hugging Face SAM3 text inference.")
    parser.add_argument("--run-mode", choices=("image", "coco"), default=DEFAULT_RUN_MODE)
    parser.add_argument("--image-path", default=DEFAULT_IMAGE_PATH)
    parser.add_argument("--coco-json", default=DEFAULT_COCO_JSON)
    parser.add_argument("--image-root", default=DEFAULT_IMAGE_ROOT)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--viz-dir", default=DEFAULT_VIZ_DIR)
    parser.add_argument("--bioclip-viz-dir", default=DEFAULT_BIOCLIP_VIZ_DIR)
    parser.add_argument("--device", default=DEVICE)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--prompts", nargs="+", default=PROMPTS)
    parser.add_argument("--confidence-threshold", type=float, default=CONFIDENCE_THRESHOLD)
    parser.add_argument("--mask-threshold", type=float, default=MASK_THRESHOLD)
    parser.add_argument("--nms-iou", type=float, default=NMS_IOU)
    parser.add_argument("--return-masks", action="store_true", default=RETURN_MASKS)
    parser.add_argument("--viz-every", type=int, default=VIZ_EVERY)
    parser.add_argument("--enable-bioclip", action="store_true", default=ENABLE_BIOCLIP)
    parser.add_argument("--bioclip-device", default=None)
    parser.add_argument("--bioclip-batch-size", type=int, default=None)
    return parser.parse_args()


def main():
    args = parse_args()

    if args.batch_size <= 0:
        raise ValueError("batch-size must be greater than 0")
    if args.viz_every < 0:
        raise ValueError("viz-every must be greater than or equal to 0")

    prompts = _parse_prompts(args.prompts)
    run_mode = args.run_mode
    device = args.device
    batch_size = args.batch_size
    bioclip_device = args.bioclip_device or ("cpu" if str(device).startswith("cuda") else device)
    bioclip_batch_size = args.bioclip_batch_size or (1 if str(bioclip_device).startswith("cuda") else 16)
    image_path = Path(args.image_path)
    coco_path = Path(args.coco_json)
    image_root = Path(args.image_root)
    output_json = Path(args.output_json)
    viz_dir = Path(args.viz_dir) if args.viz_dir else None
    bioclip_viz_dir = Path(args.bioclip_viz_dir) if args.bioclip_viz_dir else None

    if run_mode == "image" and not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if run_mode == "coco":
        if not coco_path.exists():
            raise FileNotFoundError(f"COCO JSON not found: {coco_path}")
        if not image_root.exists():
            raise FileNotFoundError(f"Image root not found: {image_root}")

    print(f"Mode: {run_mode}")
    print("Backend: Hugging Face Transformers SAM3")
    print(f"Model id: {args.model_id}")
    print(f"Device: {device}")
    print(f"Prompts: {prompts}")
    print(f"Batch size: {batch_size}")
    print(f"Confidence threshold: {args.confidence_threshold}")
    print(f"Mask threshold: {args.mask_threshold}")
    print(f"NMS IoU: {args.nms_iou}")
    print(f"Return masks: {args.return_masks}")
    if args.enable_bioclip:
        print("BioCLIP in-process enrichment: enabled")
        print(f"BioCLIP device: {bioclip_device}")
        print(f"BioCLIP batch size: {bioclip_batch_size}")
    else:
        print("BioCLIP in-process enrichment: disabled")

    detector = HuggingFaceSAM3TextDetector(
        prompts=prompts,
        device=device,
        model_id=args.model_id,
        confidence_threshold=args.confidence_threshold,
        mask_threshold=args.mask_threshold,
        nms_iou=args.nms_iou,
        return_masks=args.return_masks,
    )
    bioclip_helper = None

    try:
        if args.enable_bioclip:
            bioclip_helper = _build_bioclip_helper(
                bioclip_device=bioclip_device,
                bioclip_batch_size=bioclip_batch_size,
            )
            print("BioCLIP: enabled for animal detections")

        if run_mode == "image":
            try:
                with Image.open(image_path) as opened_image:
                    image = opened_image.convert("RGB")
            except (OSError, UnidentifiedImageError) as exc:
                raise RuntimeError(f"Failed to read image: {image_path}") from exc

            sam_detections = detector.detect_image(image)
            detections = sam_detections
            if bioclip_helper is not None:
                detections = bioclip_helper.annotate_detections(image, sam_detections)

            output_json.parent.mkdir(parents=True, exist_ok=True)
            with output_json.open("w") as handle:
                json.dump(
                    {
                        "image": str(image_path),
                        "model_id": args.model_id,
                        "prompts": prompts,
                        "detections": [_json_detection(det) for det in detections],
                    },
                    handle,
                    indent=2,
                )

            if viz_dir is not None:
                draw_detections(
                    image_path,
                    sam_detections,
                    viz_dir / f"{image_path.stem}_hf_sam3_text.jpg",
                )
            if (
                bioclip_viz_dir is not None
                and bioclip_helper is not None
                and _has_bioclip_predictions(detections)
            ):
                draw_detections(
                    image_path,
                    detections,
                    bioclip_viz_dir / f"{image_path.stem}_hf_sam3_text_bioclip.jpg",
                )

            print(f"Saved detections to {output_json}")
            print(f"Found {len(detections)} detections")
            return

        with coco_path.open("r") as handle:
            coco = json.load(handle)

        categories = [{"id": index + 1, "name": prompt} for index, prompt in enumerate(prompts)]
        records = []

        for image_info in coco.get("images", []):
            image_path = image_root / image_info["file_name"]
            if not image_path.exists():
                print(f"Skipping missing image: {image_path}")
                continue
            records.append((image_info, image_path))

        annotation_count = 0
        next_annotation_id = 1
        is_first_annotation = True
        output_handle = _open_coco_output(
            output_json,
            images=coco.get("images", []),
            categories=categories,
        )

        try:
            for start in tqdm(
                range(0, len(records), batch_size),
                desc="HF SAM3",
                total=(len(records) + batch_size - 1) // batch_size,
            ):
                batch_records = records[start:start + batch_size]
                valid_records: list[tuple[dict, Path]] = []
                batch_images: list[Image.Image] = []

                for image_info, image_path in batch_records:
                    try:
                        with Image.open(image_path) as opened_image:
                            batch_images.append(opened_image.convert("RGB"))
                        valid_records.append((image_info, image_path))
                    except (OSError, UnidentifiedImageError) as exc:
                        print(f"Skipping unreadable image: {image_path} ({exc})")

                if not batch_images:
                    continue

                batch_sam_detections = detector.detect_batch(batch_images)
                batch_detections = batch_sam_detections
                if bioclip_helper is not None:
                    batch_detections = bioclip_helper.annotate_batch(
                        batch_images,
                        batch_sam_detections,
                    )

                for offset, ((image_info, image_path), sam_detections, detections) in enumerate(
                    zip(valid_records, batch_sam_detections, batch_detections)
                ):
                    for detection in detections:
                        is_first_annotation = _write_annotation(
                            output_handle,
                            _build_annotation(
                                annotation_id=next_annotation_id,
                                image_id=image_info["id"],
                                detection=detection,
                            ),
                            is_first=is_first_annotation,
                        )
                        next_annotation_id += 1
                        annotation_count += 1

                    global_index = start + offset
                    if viz_dir is not None and args.viz_every > 0 and global_index % args.viz_every == 0:
                        relative = Path(image_info["file_name"])
                        draw_detections(
                            image_path,
                            sam_detections,
                            viz_dir / relative.parent / f"{relative.stem}_hf_sam3_text.jpg",
                        )
                    if (
                        bioclip_viz_dir is not None
                        and args.viz_every > 0
                        and global_index % args.viz_every == 0
                        and _has_bioclip_predictions(detections)
                    ):
                        relative = Path(image_info["file_name"])
                        draw_detections(
                            image_path,
                            detections,
                            bioclip_viz_dir / relative.parent / f"{relative.stem}_hf_sam3_text_bioclip.jpg",
                        )

                del batch_images
                del batch_sam_detections
                del batch_detections
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        finally:
            output_handle.write("\n  ]\n}\n")
            output_handle.close()

        print(f"Saved predictions to {output_json}")
        print(f"Processed {len(records)} images")
        print(f"Saved {annotation_count} annotations")
    finally:
        if bioclip_helper is not None:
            bioclip_helper.close()
        detector.close()


if __name__ == "__main__":
    main()
