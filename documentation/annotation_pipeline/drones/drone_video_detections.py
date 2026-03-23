#!/usr/bin/env python3
"""
Drone video annotation: extract frames and run YOLO+SAHI+BioCLIP detection.

Adapts the camera trap detection pipeline for drone video:
1. Extract frames at configurable interval (default: every 30th frame ≈ 1 fps)
2. Run YOLO+SAHI sliced detection on each frame
3. Classify detections with BioCLIP using the full Wilds species label set
4. Output one CSV per video with frame-level detections

Usage:
    # Process a single video
    python drone_video_detections.py --video /path/to/DJI_0001.MP4 --csv-out detections.csv

    # Process with custom frame interval
    python drone_video_detections.py --video /path/to/video.MP4 --frame-interval 15 --csv-out out.csv
"""

import os
import sys
import argparse
import csv
import math
import datetime
import tempfile

from PIL import Image, ImageDraw, ImageFont

import torch
import cv2


def parse_args():
    p = argparse.ArgumentParser(
        description="YOLO+SAHI+BioCLIP detection on drone video frames"
    )
    p.add_argument("--video", required=True, help="Path to video file (MP4/MOV)")
    p.add_argument("--weights", required=True, help="Path to YOLO weights (e.g., yolov8x.pt)")
    p.add_argument("--device", default="cuda:0", help="Device (cuda:0 or cpu)")

    # Frame extraction
    p.add_argument("--frame-interval", type=int, default=30,
                   help="Extract every Nth frame (default: 30, ~1fps for 30fps video)")
    p.add_argument("--max-frames", type=int, default=0,
                   help="Max frames to process (0 = all)")
    p.add_argument("--start-frame", type=int, default=0,
                   help="Frame number to start from")

    # SAHI / YOLO params
    p.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold")
    p.add_argument("--slice-h", type=int, default=640, help="SAHI slice height")
    p.add_argument("--slice-w", type=int, default=640, help="SAHI slice width")
    p.add_argument("--ovh", type=float, default=0.2, help="Overlap height ratio")
    p.add_argument("--ovw", type=float, default=0.2, help="Overlap width ratio")

    # BioCLIP labels
    p.add_argument("--labels", type=str,
                   default=(
                       "Pere David's deer,Milu deer,Elaphurus,"
                       "white-tailed deer,Odocoileus,deer,Cervus,elk,"
                       "banteng,Bos,cow,cattle,bison,Bison,"
                       "Przewalski's horse,Equus,horse,donkey,"
                       "Sichuan takin,Budorcas,goat,muskox,"
                       "Grevy's zebra,zebra,oryx,Oryx,antelope,"
                       "eland,Taurotragus,giraffe,Giraffa,"
                       "rhinoceros,Rhinoceros,Ceratotherium,"
                       "camel,Camelus,ostrich,Struthio,"
                       "wild dog,Lycaon,coyote,Canis,fox,"
                       "bird,raptor,heron,hawk,songbird,waterfowl,"
                       "fish,human,person,vehicle,"
                       "background,vegetation,tree,grass,rock,water,sky"
                   ),
                   help="Comma-separated BioCLIP labels")

    # Output
    p.add_argument("--csv-out", required=True, help="Output CSV path")
    p.add_argument("--save-frames", action="store_true",
                   help="Save annotated frames to disk")
    p.add_argument("--frames-dir", default="", help="Directory for annotated frames")

    return p.parse_args()


def load_bioclip_model(device, label_string):
    """Load BioCLIP 2 model and encode text labels."""
    import open_clip

    print("Loading BioCLIP 2 model...")
    model, _, preprocess_val = open_clip.create_model_and_transforms(
        "hf-hub:imageomics/bioclip-2"
    )
    tokenizer = open_clip.get_tokenizer("hf-hub:imageomics/bioclip-2")

    model = model.to(device)
    model.eval()

    labels = [s.strip() for s in label_string.split(",") if s.strip()]
    text_prompts = [f"a photo of a {lbl}" for lbl in labels]

    with torch.no_grad():
        text_tokens = tokenizer(text_prompts).to(device)
        text_features = model.encode_text(text_tokens)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

    print(f"BioCLIP loaded with {len(labels)} labels")
    return model, preprocess_val, labels, text_features


def classify_with_bioclip(model, preprocess, text_features, labels, crop, device):
    """Classify a cropped detection with BioCLIP."""
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
    from sahi import AutoDetectionModel
    from sahi.predict import get_sliced_prediction

    args = parse_args()

    assert os.path.isfile(args.video), f"Video not found: {args.video}"
    assert os.path.isfile(args.weights), f"Weights not found: {args.weights}"

    # Open video
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open video: {args.video}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    video_name = os.path.basename(args.video)
    frames_to_process = (total_frames - args.start_frame) // args.frame_interval
    if args.max_frames > 0:
        frames_to_process = min(frames_to_process, args.max_frames)

    print(f"Video: {video_name}")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps}")
    print(f"  Total frames: {total_frames}")
    print(f"  Duration: {total_frames/fps:.1f}s")
    print(f"  Extracting every {args.frame_interval}th frame ({fps/args.frame_interval:.1f} fps effective)")
    print(f"  Frames to process: {frames_to_process}")

    # Load models
    print(f"\nLoading YOLO model from: {args.weights}")
    yolo_model = AutoDetectionModel.from_pretrained(
        model_type="ultralytics",
        model_path=args.weights,
        confidence_threshold=args.conf,
        device=args.device,
    )

    device_torch = args.device if args.device != "cpu" else "cpu"
    bio_model, bio_preprocess, bio_labels, text_features = load_bioclip_model(
        device_torch, args.labels
    )

    # Setup output
    if args.save_frames:
        frames_dir = args.frames_dir or os.path.join(
            os.path.dirname(args.csv_out), "annotated_frames"
        )
        os.makedirs(frames_dir, exist_ok=True)

    csv_rows = []
    frame_summaries = []
    frame_count = 0

    # Seek to start frame
    if args.start_frame > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, args.start_frame)

    current_frame = args.start_frame

    print(f"\nProcessing frames...")

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break

        if (current_frame - args.start_frame) % args.frame_interval != 0:
            current_frame += 1
            continue

        frame_count += 1
        if args.max_frames > 0 and frame_count > args.max_frames:
            break

        # Frame timestamp
        frame_time_sec = current_frame / fps
        frame_timestamp = str(datetime.timedelta(seconds=frame_time_sec))

        # Convert BGR to RGB PIL Image
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)

        # Save frame to temp file for SAHI (it needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
            pil_img.save(tmp_path, format="JPEG", quality=95)

        # Run SAHI detection
        res = get_sliced_prediction(
            image=tmp_path,
            detection_model=yolo_model,
            slice_height=args.slice_h,
            slice_width=args.slice_w,
            overlap_height_ratio=args.ovh,
            overlap_width_ratio=args.ovw,
            postprocess_type="NMS",
            postprocess_match_metric="IOU",
            postprocess_match_threshold=0.5,
        )

        os.unlink(tmp_path)

        det_count = 0
        frame_labels = []

        draw = ImageDraw.Draw(pil_img) if args.save_frames else None

        for op in res.object_prediction_list:
            bbox = op.bbox
            x_min, y_min, x_max, y_max = bbox.minx, bbox.miny, bbox.maxx, bbox.maxy

            try:
                yolo_conf = float(op.score.value)
            except Exception:
                yolo_conf = None

            # Crop and classify
            x_min_cl = max(0, int(x_min))
            y_min_cl = max(0, int(y_min))
            x_max_cl = min(width, int(x_max))
            y_max_cl = min(height, int(y_max))
            if x_max_cl <= x_min_cl or y_max_cl <= y_min_cl:
                continue

            crop = pil_img.crop((x_min_cl, y_min_cl, x_max_cl, y_max_cl))
            bioclip_label, bioclip_score = classify_with_bioclip(
                bio_model, bio_preprocess, text_features, bio_labels, crop, device_torch
            )

            det_count += 1
            frame_labels.append(bioclip_label)

            csv_rows.append({
                "video": video_name,
                "frame_number": current_frame,
                "frame_time_sec": f"{frame_time_sec:.2f}",
                "frame_timestamp": frame_timestamp,
                "detection_index": det_count,
                "bioclip_label": bioclip_label,
                "bioclip_score": f"{bioclip_score:.4f}",
                "yolo_conf": f"{yolo_conf:.4f}" if yolo_conf else "",
                "xmin": int(x_min),
                "ymin": int(y_min),
                "xmax": int(x_max),
                "ymax": int(y_max),
                "frame_width": width,
                "frame_height": height,
            })

            # Draw on frame
            if draw:
                draw.rectangle([(x_min, y_min), (x_max, y_max)], outline="red", width=2)
                draw.text((x_min, max(0, y_min - 14)),
                          f"{bioclip_label} ({bioclip_score:.2f})", fill="red")

        # Save annotated frame
        if args.save_frames and det_count > 0:
            frame_out = os.path.join(
                frames_dir, f"{os.path.splitext(video_name)[0]}_f{current_frame:06d}.jpg"
            )
            pil_img.save(frame_out, format="JPEG")

        # Frame summary
        frame_summaries.append({
            "video": video_name,
            "frame_number": current_frame,
            "frame_time_sec": f"{frame_time_sec:.2f}",
            "detections": det_count,
            "is_blank": 1 if det_count == 0 else 0,
            "species": "; ".join(sorted(set(frame_labels))) if frame_labels else "",
        })

        if frame_count % 50 == 0:
            print(f"  Frame {frame_count}/{frames_to_process} "
                  f"(video frame {current_frame}/{total_frames}) - "
                  f"{det_count} detections")

        current_frame += 1

    cap.release()

    # Write detection CSV
    if csv_rows:
        fieldnames = list(csv_rows[0].keys())
        csv_dir = os.path.dirname(args.csv_out)
        if csv_dir:
            os.makedirs(csv_dir, exist_ok=True)
        with open(args.csv_out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"\n{len(csv_rows)} detections saved to {args.csv_out}")
    else:
        print(f"\nNo detections found in {video_name}")

    # Write frame summary
    summary_path = args.csv_out.replace("_detections.csv", "_frame_summary.csv")
    if summary_path == args.csv_out:
        summary_path = args.csv_out.replace(".csv", "_frame_summary.csv")
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(frame_summaries[0].keys()))
        writer.writeheader()
        writer.writerows(frame_summaries)

    # Stats
    blank_frames = sum(1 for s in frame_summaries if s["is_blank"])
    print(f"\nSummary for {video_name}:")
    print(f"  Frames processed: {frame_count}")
    print(f"  Frames with detections: {frame_count - blank_frames}")
    print(f"  Blank frames: {blank_frames} ({blank_frames/frame_count*100:.1f}%)")
    print(f"  Total detections: {len(csv_rows)}")
    print(f"  Frame summary: {summary_path}")


if __name__ == "__main__":
    main()
