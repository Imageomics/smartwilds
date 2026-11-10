#!/usr/bin/env python3
"""
Post-process camera trap detection CSVs:
1. Remove overlapping bounding boxes (IoU-based NMS within each image)
2. Filter non-animal detections using BioCLIP confidence threshold
3. Track empty images (no detections) for blank image analysis
4. Add is_blank column for arrival rate calculations

Input:  *_detections.csv files from camera_trap_detections.py
Output: *_detections_filtered.csv (cleaned detections)
        *_image_summary.csv (one row per image: detection count, is_blank)

Usage:
    # Process all detection CSVs in a directory
    python postprocess_detections.py --input-dir /path/to/detection_results

    # Process a single file
    python postprocess_detections.py --input /path/to/TW01_detections.csv
"""

import argparse
import csv
import os
import glob
from collections import defaultdict


def compute_iou(box1, box2):
    """Compute IoU between two boxes [xmin, ymin, xmax, ymax]."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter == 0:
        return 0.0

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter

    return inter / union if union > 0 else 0.0


def nms_within_image(detections, iou_threshold=0.5):
    """Apply NMS within a single image's detections. Keep highest YOLO conf."""
    if len(detections) <= 1:
        return detections

    # Sort by YOLO confidence descending
    sorted_dets = sorted(detections, key=lambda d: float(d.get("yolo_conf", 0) or 0), reverse=True)

    keep = []
    suppressed = set()

    for i, det_i in enumerate(sorted_dets):
        if i in suppressed:
            continue
        keep.append(det_i)

        box_i = [float(det_i["xmin"]), float(det_i["ymin"]),
                 float(det_i["xmax"]), float(det_i["ymax"])]

        for j in range(i + 1, len(sorted_dets)):
            if j in suppressed:
                continue
            box_j = [float(sorted_dets[j]["xmin"]), float(sorted_dets[j]["ymin"]),
                     float(sorted_dets[j]["xmax"]), float(sorted_dets[j]["ymax"])]

            if compute_iou(box_i, box_j) >= iou_threshold:
                suppressed.add(j)

    return keep


BACKGROUND_LABELS = {"background", "vegetation", "tree", "grass", "rock", "water", "sky", "vehicle"}
HUMAN_LABELS = {"human", "person"}


def postprocess_file(input_path, bioclip_threshold=0.15, iou_threshold=0.5):
    """
    Post-process a single detection CSV.

    Filters:
    1. NMS to remove overlapping boxes (IoU >= threshold)
    2. Remove detections classified as background/vegetation/etc by BioCLIP
    3. Flag human detections separately

    Returns:
        filtered_rows: list of filtered detection dicts
        image_summary: list of per-image summary dicts
        stats: dict with processing statistics
    """
    # Read all detections
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        all_rows = list(reader)

    # Group by image
    by_image = defaultdict(list)
    all_images = set()

    for row in all_rows:
        img = row["image"]
        by_image[img].append(row)
        all_images.add(img)

    # Also discover images that had 0 detections by scanning annotated dir
    # (These are the "blank" images not in the CSV at all)
    base_dir = os.path.dirname(input_path)
    annotated_dir = os.path.join(base_dir, "annotated")

    # Get camera key from filename
    csv_name = os.path.basename(input_path)
    camera_key = csv_name.replace("_detections.csv", "").replace("_detections_filtered.csv", "")

    # Try to find the image directory from detection config
    # For now, use annotated images as proxy for all processed images
    annotated_images = set()
    if os.path.isdir(annotated_dir):
        for f in os.listdir(annotated_dir):
            if f.endswith("_annotated.jpg"):
                orig_name = f.replace("_annotated.jpg", ".JPG")
                annotated_images.add(orig_name)
                # Also try lowercase
                annotated_images.add(f.replace("_annotated.jpg", ".jpg"))

    # All images = those with detections + those in annotated dir without detections
    blank_images = annotated_images - all_images

    stats = {
        "total_images_with_detections": len(by_image),
        "total_blank_images": len(blank_images),
        "total_detections_before": len(all_rows),
        "removed_by_nms": 0,
        "removed_by_bioclip": 0,
        "removed_as_background": 0,
        "removed_as_human": 0,
        "kept": 0,
    }

    filtered_rows = []
    image_summary = []

    # Process each image
    for img, dets in by_image.items():
        # Step 1: NMS to remove overlapping boxes
        after_nms = nms_within_image(dets, iou_threshold)
        stats["removed_by_nms"] += len(dets) - len(after_nms)

        # Step 2: Filter by BioCLIP label and confidence
        after_filter = []
        for det in after_nms:
            label = det.get("bioclip_label", "").lower().strip()
            score = float(det.get("bioclip_score", 0) or 0)

            # Remove background/vegetation/non-animal detections
            if label in BACKGROUND_LABELS:
                stats["removed_as_background"] += 1
                continue

            # Separate human detections (don't count as animals, but track)
            if label in HUMAN_LABELS:
                stats["removed_as_human"] += 1
                continue

            # Apply confidence threshold
            if score < bioclip_threshold:
                stats["removed_by_bioclip"] += 1
                continue

            after_filter.append(det)

        filtered_rows.extend(after_filter)
        stats["kept"] += len(after_filter)

        # Image summary
        image_summary.append({
            "image": img,
            "image_path": dets[0].get("image_path", ""),
            "timestamp_file": dets[0].get("timestamp_file", ""),
            "timestamp_from_name": dets[0].get("timestamp_from_name", ""),
            "camera_key": camera_key,
            "raw_detections": len(dets),
            "after_nms": len(after_nms),
            "after_bioclip_filter": len(after_filter),
            "is_blank": 1 if len(after_filter) == 0 else 0,
            "species_detected": "; ".join(sorted(set(
                d["bioclip_label"] for d in after_filter
            ))) if after_filter else "",
        })

    # Add blank images (no detections at all)
    for img in sorted(blank_images):
        image_summary.append({
            "image": img,
            "image_path": "",
            "timestamp_file": "",
            "timestamp_from_name": "",
            "camera_key": camera_key,
            "raw_detections": 0,
            "after_nms": 0,
            "after_bioclip_filter": 0,
            "is_blank": 1,
            "species_detected": "",
        })

    return filtered_rows, image_summary, stats, fieldnames


def main():
    parser = argparse.ArgumentParser(description="Post-process camera trap detections")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="Single detection CSV to process")
    group.add_argument("--input-dir", help="Directory containing detection CSVs")

    parser.add_argument("--bioclip-threshold", type=float, default=0.15,
                        help="Minimum BioCLIP score to keep (default: 0.15)")
    parser.add_argument("--iou-threshold", type=float, default=0.5,
                        help="IoU threshold for NMS (default: 0.5)")
    parser.add_argument("--output-dir", help="Output directory (default: same as input)")

    args = parser.parse_args()

    # Find input files
    if args.input:
        input_files = [args.input]
    else:
        input_files = sorted(glob.glob(os.path.join(args.input_dir, "*_detections.csv")))
        # Exclude already-filtered files
        input_files = [f for f in input_files if "_filtered" not in f and "_summary" not in f]

    if not input_files:
        print("No detection CSVs found")
        return

    output_dir = args.output_dir or os.path.dirname(input_files[0])

    print(f"{'='*60}")
    print(f"Camera Trap Detection Post-Processing")
    print(f"{'='*60}")
    print(f"BioCLIP threshold: {args.bioclip_threshold}")
    print(f"IoU NMS threshold: {args.iou_threshold}")
    print(f"Files to process: {len(input_files)}")

    total_stats = {
        "total_images_with_detections": 0,
        "total_blank_images": 0,
        "total_detections_before": 0,
        "removed_by_nms": 0,
        "removed_by_bioclip": 0,
        "kept": 0,
    }

    all_image_summaries = []

    for input_path in input_files:
        camera_key = os.path.basename(input_path).replace("_detections.csv", "")
        print(f"\n  Processing: {camera_key}")

        filtered, summaries, stats, fieldnames = postprocess_file(
            input_path, args.bioclip_threshold, args.iou_threshold
        )

        # Accumulate stats
        for k in total_stats:
            total_stats[k] += stats[k]
        all_image_summaries.extend(summaries)

        # Write filtered detections
        out_path = os.path.join(output_dir, f"{camera_key}_detections_filtered.csv")
        if filtered:
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(filtered)

        blank_count = sum(1 for s in summaries if s["is_blank"])
        print(f"    Before: {stats['total_detections_before']} detections")
        print(f"    NMS removed: {stats['removed_by_nms']}")
        print(f"    BioCLIP filtered: {stats['removed_by_bioclip']}")
        print(f"    After: {stats['kept']} detections")
        print(f"    Blank images: {blank_count}")
        print(f"    → {out_path}")

    # Write combined image summary
    summary_path = os.path.join(output_dir, "all_images_summary.csv")
    if all_image_summaries:
        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_image_summaries[0].keys()))
            writer.writeheader()
            writer.writerows(all_image_summaries)

    # Final summary
    total_images = total_stats["total_images_with_detections"] + total_stats["total_blank_images"]
    blank_rate = total_stats["total_blank_images"] / total_images * 100 if total_images > 0 else 0

    print(f"\n{'='*60}")
    print(f"Post-Processing Summary")
    print(f"{'='*60}")
    print(f"  Total images processed:  {total_images}")
    print(f"  Images with detections:  {total_stats['total_images_with_detections']}")
    print(f"  Blank images:            {total_stats['total_blank_images']} ({blank_rate:.1f}%)")
    print(f"  Raw detections:          {total_stats['total_detections_before']}")
    print(f"  Removed by NMS:          {total_stats['removed_by_nms']}")
    print(f"  Removed by BioCLIP:      {total_stats['removed_by_bioclip']}")
    print(f"  Final detections:        {total_stats['kept']}")
    print(f"\n  Outputs:")
    print(f"    Filtered CSVs: {output_dir}/*_filtered.csv")
    print(f"    Image summary: {summary_path}")


if __name__ == "__main__":
    main()
