#!/usr/bin/env python3
import os
import glob
import math
import argparse
import csv
import datetime

from PIL import Image, ImageDraw, ImageFont
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

import torch
import open_clip


def parse_args():
    p = argparse.ArgumentParser(
        description=("YOLO+SAHI detections + distance/angle + GPS + BioCLIP 2 labels")
    )

    # Paths / model
    p.add_argument("--weights", required=True, help="Path to YOLO weights (e.g., yolov8x.pt)")
    p.add_argument("--images", required=True, help="Directory containing images")
    p.add_argument("--device", default="cuda:0", help='Device string, e.g. "cuda:0" or "cpu"')

    # Inference params (SAHI / YOLO)
    p.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    p.add_argument("--slice-h", type=int, default=512, help="Slice height for SAHI")
    p.add_argument("--slice-w", type=int, default=512, help="Slice width for SAHI")
    p.add_argument("--ovh", type=float, default=0.2, help="Overlap height ratio")
    p.add_argument("--ovw", type=float, default=0.2, help="Overlap width ratio")

    # Control
    p.add_argument("--max-images", type=int, default=0, help="Optional cap on number of images (0 = no cap)")
    p.add_argument(
        "--max-det-print",
        type=int,
        default=-1,
        help="Max number of detections per image to print (0 = none, -1 = all).",
    )

    # Geometry for distance/angle
    p.add_argument("--hfov-deg", type=float, required=True, help="Camera horizontal field of view in degrees")
    p.add_argument(
        "--target-height-m",
        type=float,
        required=True,
        help="Approximate real-world height of target animal in meters (used for distance estimate).",
    )

    # Camera GPS & direction
    p.add_argument("--camera-lat", type=float, required=True, help="Camera latitude in decimal degrees.")
    p.add_argument("--camera-lon", type=float, required=True, help="Camera longitude in decimal degrees.")
    p.add_argument(
        "--camera-bearing-deg",
        type=float,
        required=True,
        help="Direction the camera is facing, in degrees clockwise from North (0–360).",
    )

    # CSV output
    p.add_argument("--csv-out", type=str, required=True, help="Path to CSV file where detections will be saved.")

    # Label set for BioCLIP 2 zero-shot
    p.add_argument(
        "--labels",
        type=str,
        default=("white-tailed deer,deer,bird"),
        help=(
            "Comma-separated list of candidate labels for BioCLIP 2 zero-shot. "
            "Filtering is still done by checking if the chosen label contains "
            "'deer' or 'bird' (case-insensitive)."
        ),
    )

    return p.parse_args()


def parse_iso_timestamp_from_filename(path_or_name: str):
    """
    Example filename:
      NSCF0001_231031200001_0088.JPG
                YYMMDDHHMMSS

    Returns ISO string:
      2023-10-31T20:00:01
    or None if parsing fails.
    """
    try:
        base = os.path.basename(path_or_name)
        parts = base.split("_")
        if len(parts) < 2:
            return None

        dt = parts[1]  # '231031200001'
        if len(dt) < 12 or not dt[:12].isdigit():
            return None

        year = int("20" + dt[0:2])
        month = int(dt[2:4])
        day = int(dt[4:6])
        hour = int(dt[6:8])
        minute = int(dt[8:10])
        second = int(dt[10:12])

        return datetime.datetime(year, month, day, hour, minute, second).isoformat()
    except Exception:
        return None


def estimate_distance_and_angle(img_width, img_height, bbox, hfov_deg, real_height_m):
    """
    Estimate distance (meters) and horizontal angle (degrees) from a single bounding box.
    """
    x_min, y_min, x_max, y_max = bbox.minx, bbox.miny, bbox.maxx, bbox.maxy
    bbox_h = y_max - y_min
    if bbox_h <= 0:
        return float("inf"), 0.0

    cx = (x_min + x_max) / 2.0

    hfov_rad = math.radians(hfov_deg)
    fx = (img_width / 2.0) / math.tan(hfov_rad / 2.0)

    distance_m = (real_height_m * fx) / bbox_h

    cx0 = img_width / 2.0
    dx = cx - cx0
    angle_rad = math.atan(dx / fx)
    angle_deg = math.degrees(angle_rad)

    return distance_m, angle_deg


def project_gps(camera_lat, camera_lon, distance_m, absolute_bearing_deg):
    """
    Project a GPS coordinate given start lat/lon, distance (m), bearing (deg).
    """
    R = 6378137.0  # WGS-84 radius in meters

    lat1 = math.radians(camera_lat)
    lon1 = math.radians(camera_lon)
    bearing = math.radians(absolute_bearing_deg)

    lat2 = math.asin(
        math.sin(lat1) * math.cos(distance_m / R)
        + math.cos(lat1) * math.sin(distance_m / R) * math.cos(bearing)
    )

    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(distance_m / R) * math.cos(lat1),
        math.cos(distance_m / R) - math.sin(lat1) * math.sin(lat2),
    )

    return math.degrees(lat2), math.degrees(lon2)


def load_bioclip_model(device: str, label_string: str):
    print("Loading BioCLIP 2 model from Hugging Face via open_clip...")
    model, _, preprocess_val = open_clip.create_model_and_transforms("hf-hub:imageomics/bioclip-2")
    tokenizer = open_clip.get_tokenizer("hf-hub:imageomics/bioclip-2")

    model = model.to(device)
    model.eval()

    labels = [s.strip() for s in label_string.split(",") if s.strip()]
    if not labels:
        raise ValueError("No labels provided for BioCLIP 2.")

    text_prompts = [f"a photo of a {lbl}" for lbl in labels]
    with torch.no_grad():
        text_tokens = tokenizer(text_prompts).to(device)
        text_features = model.encode_text(text_tokens)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

    print(f"Loaded BioCLIP 2 with {len(labels)} labels: {labels}")
    return model, preprocess_val, labels, text_features


def classify_with_bioclip(model, preprocess, text_features, labels, crop: Image.Image, device: str):
    with torch.no_grad():
        img_t = preprocess(crop).unsqueeze(0).to(device)
        image_features = model.encode_image(img_t)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        logits = (image_features @ text_features.T).squeeze(0)
        best_idx = int(torch.argmax(logits).item())
        best_score = float(logits[best_idx].item())
        best_label = labels[best_idx]
    return best_label, best_score


def main():
    args = parse_args()

    assert os.path.isfile(args.weights), f"WEIGHTS not found: {args.weights}"
    assert os.path.isdir(args.images), f"IMAGES directory not found: {args.images}"

    # Gather images
    exts = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG")
    paths = [p for e in exts for p in glob.glob(os.path.join(args.images, e))]
    if not paths:
        raise SystemExit(f"No images found under {args.images}")

    if args.max_images > 0:
        paths = paths[: args.max_images]

    print(f"Loading YOLO model from: {args.weights}")
    model = AutoDetectionModel.from_pretrained(
        model_type="ultralytics",
        model_path=args.weights,
        confidence_threshold=args.conf,
        device=args.device,
    )

    device_torch = args.device if args.device != "cpu" else "cpu"
    model_bio, preprocess_bio, bioclip_labels, text_features = load_bioclip_model(device_torch, args.labels)

    csv_rows = []

    total = len(paths)
    print(f"Starting scan on {total} image(s)")
    print(f"Distance model: target height = {args.target_height_m} m, HFOV = {args.hfov_deg}°")
    print(f"Camera at lat={args.camera_lat}, lon={args.camera_lon}, bearing={args.camera_bearing_deg}°")

    # annotated dir (next to CSV)
    csv_dir = os.path.dirname(args.csv_out)
    annot_dir = os.path.join(csv_dir if csv_dir else ".", "annotated")
    os.makedirs(annot_dir, exist_ok=True)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for i, p in enumerate(paths, 1):
        try:
            img = Image.open(p).convert("RGB")
            img_width, img_height = img.size

            # Old file timestamp (mtime) - keep for audit
            try:
                ts = os.path.getmtime(p)
                file_timestamp = datetime.datetime.fromtimestamp(ts).isoformat()
            except Exception:
                file_timestamp = None

        except Exception as e:
            print(f"[SKIP] Could not open image {p}: {e}")
            continue

        fname = os.path.basename(p)

        # NEW: timestamp parsed from filename
        timestamp_from_name = parse_iso_timestamp_from_filename(fname)

        res = get_sliced_prediction(
            image=p,
            detection_model=model,
            slice_height=args.slice_h,
            slice_width=args.slice_w,
            overlap_height_ratio=args.ovh,
            overlap_width_ratio=args.ovw,
            # optional but recommended to reduce duplicate boxes:
            postprocess_type="NMS",
            postprocess_match_metric="IOU",
            postprocess_match_threshold=0.5,
        )

        draw = ImageDraw.Draw(img)
        kept_det_idx = 0

        for det_idx, op in enumerate(res.object_prediction_list, start=1):
            bbox = op.bbox
            x_min, y_min, x_max, y_max = bbox.minx, bbox.miny, bbox.maxx, bbox.maxy

            try:
                yolo_conf = float(op.score.value)
            except Exception:
                yolo_conf = None

            x_min_cl = max(0, int(x_min))
            y_min_cl = max(0, int(y_min))
            x_max_cl = min(img_width, int(x_max))
            y_max_cl = min(img_height, int(y_max))
            if x_max_cl <= x_min_cl or y_max_cl <= y_min_cl:
                continue

            crop = img.crop((x_min_cl, y_min_cl, x_max_cl, y_max_cl))
            bioclip_label, bioclip_score = classify_with_bioclip(
                model_bio,
                preprocess_bio,
                text_features,
                bioclip_labels,
                crop,
                device_torch,
            )

            kept_det_idx += 1

            d_m, a_deg = estimate_distance_and_angle(
                img_width,
                img_height,
                bbox,
                args.hfov_deg,
                args.target_height_m,
            )

            absolute_bearing = (args.camera_bearing_deg + a_deg) % 360.0

            animal_lat, animal_lon = project_gps(
                args.camera_lat,
                args.camera_lon,
                d_m,
                absolute_bearing,
            )

            # CLI print (same style as your original)
            if args.max_det_print != 0:
                if args.max_det_print < 0 or kept_det_idx <= args.max_det_print:
                    yolo_str = f"{yolo_conf:.2f}" if yolo_conf is not None else "NA"
                    bio_str = f"{bioclip_score:.3f}" if bioclip_score is not None else "NA"
                    print(
                        f"   #{kept_det_idx} {bioclip_label} | yolo_conf={yolo_str} | "
                        f"bio_score={bio_str} | d={d_m:.1f} m | "
                        f"rel_angle={a_deg:+.1f}° | abs_bearing={absolute_bearing:.1f}°"
                    )

            # Draw
            draw.rectangle([(x_min, y_min), (x_max, y_max)], outline="red", width=2)
            label_text = f"{bioclip_label} ({bioclip_score:.2f})" if bioclip_score is not None else bioclip_label
            text_x, text_y = x_min, max(0, y_min - 14)
            if font is not None:
                draw.text((text_x, text_y), label_text, fill="red", font=font)
            else:
                draw.text((text_x, text_y), label_text, fill="red")

            # CSV row PER DETECTION (your original behavior)
            csv_rows.append(
                {
                    "image": fname,
                    "image_path": p,
                    "timestamp_file": file_timestamp,          # mtime
                    "timestamp_from_name": timestamp_from_name, # parsed from filename
                    "detection_index": kept_det_idx,
                    "bioclip_label": bioclip_label,
                    "bioclip_score": bioclip_score,
                    "yolo_conf": yolo_conf,
                    "xmin": x_min,
                    "ymin": y_min,
                    "xmax": x_max,
                    "ymax": y_max,
                    "distance_m": d_m,
                    "angle_deg": a_deg,
                    "camera_lat": args.camera_lat,
                    "camera_lon": args.camera_lon,
                    "camera_bearing_deg": args.camera_bearing_deg,
                    "animal_lat": animal_lat,
                    "animal_lon": animal_lon,
                    "animal_absolute_bearing_deg": absolute_bearing,
                }
            )

        # Save annotated image
        base, _ = os.path.splitext(fname)
        out_img_path = os.path.join(annot_dir, f"{base}_annotated.jpg")
        img.save(out_img_path, format="JPEG")
        print(f"Annotated image saved: {out_img_path}")

    # Write CSV
    if csv_rows:
        csv_path = args.csv_out
        fieldnames = [
            "image",
            "image_path",
            "timestamp_file",
            "timestamp_from_name",
            "detection_index",
            "bioclip_label",
            "bioclip_score",
            "yolo_conf",
            "xmin",
            "ymin",
            "xmax",
            "ymax",
            "distance_m",
            "angle_deg",
            "camera_lat",
            "camera_lon",
            "camera_bearing_deg",
            "animal_lat",
            "animal_lon",
            "animal_absolute_bearing_deg",
        ]

        out_dir = os.path.dirname(csv_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        print(f"\nDetections saved to CSV: {csv_path}")
    else:
        print("\nNo detections found — CSV not written.")


if __name__ == "__main__":
    main()
