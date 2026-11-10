#!/usr/bin/env python3
"""
Visualize drone detections by drawing bounding boxes + labels on extracted frames.

For each video, samples frames with detections and saves annotated images
for manual review. Prioritizes frames with:
  - Flagged/impossible labels
  - High detection counts (busy frames)
  - Evenly spaced temporal sampling

Usage:
    # Default: sample up to 10 frames per video
    python visualize_drone_detections.py

    # More frames per video
    python visualize_drone_detections.py --max-frames 20

    # Only specific missions
    python visualize_drone_detections.py --mission 20250908_djiair_4

    # Only frames with flagged labels
    python visualize_drone_detections.py --flagged-only

Output:
    processing_output/detections/drones/annotation_review/frames/
        {mission}/{video}/frame_{N}_annotated.jpg
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
DETECTIONS_DIR = BASE_DIR / "processing_output" / "detections" / "drones"
OUTPUT_DIR = DETECTIONS_DIR / "annotation_review" / "frames"

CAMPAIGN_DIRS = [
    BASE_DIR / "thewilds_20250630_20250703" / "drones",
    BASE_DIR / "thewilds_20250804_20250828" / "drones",
    BASE_DIR / "thewilds_20250908_20250908" / "drones",
]

# Color coding by label classification
IMPOSSIBLE_LABELS = {"Lycaon", "wild dog", "human", "fish"}
NON_ANIMAL_LABELS = {"sky", "grass", "rock", "tree", "vegetation", "water", "c"}

# Colors (BGR for cv2, but we use PIL so RGB)
COLOR_VALID = (0, 200, 0)        # green
COLOR_PLAUSIBLE = (255, 165, 0)  # orange
COLOR_IMPOSSIBLE = (255, 0, 0)   # red
COLOR_NON_ANIMAL = (128, 128, 128)  # gray

VALID_LABELS = {
    "Pere David's deer", "Elaphurus", "Milu deer",
    "Grevy's zebra", "zebra",
    "Sichuan takin", "Budorcas",
    "Przewalski's horse", "Equus", "horse",
    "rhinoceros", "Ceratotherium",
    "oryx",
    "banteng", "Bos",
    "bison",
    "Giraffa",
    "white-tailed deer", "Odocoileus", "deer",
    "coyote", "Canis",
    "bird", "songbird", "hawk", "raptor", "heron", "waterfowl",
    "Struthio", "ostrich",
    "Camelus", "camel",
}


def classify_label(label):
    if label in NON_ANIMAL_LABELS:
        return "non_animal"
    if label in IMPOSSIBLE_LABELS:
        return "impossible"
    if label in VALID_LABELS:
        return "valid"
    return "plausible"


def get_color(label):
    cls = classify_label(label)
    if cls == "valid":
        return COLOR_VALID
    elif cls == "impossible":
        return COLOR_IMPOSSIBLE
    elif cls == "non_animal":
        return COLOR_NON_ANIMAL
    return COLOR_PLAUSIBLE


# ─── Video file mapping ──────────────────────────────────────────────────────

def build_video_map():
    """Build mapping: (mission, video_filename) -> full path to MP4."""
    video_map = {}

    for campaign_dir in CAMPAIGN_DIRS:
        if not campaign_dir.exists():
            continue
        for mission_dir in sorted(campaign_dir.iterdir()):
            if not mission_dir.is_dir() or mission_dir.name == "video_files":
                continue
            mission = mission_dir.name
            # Check both "videos/" and "video_files/" subdirectories
            for subdir_name in ("videos", "video_files"):
                video_subdir = mission_dir / subdir_name
                if video_subdir.exists():
                    for vf in video_subdir.iterdir():
                        if vf.suffix.upper() == ".MP4":
                            video_map[(mission, vf.name)] = vf

    return video_map


# ─── Load detections ─────────────────────────────────────────────────────────

def load_detections_by_video():
    """Load detections grouped by (mission, video_filename, frame_number)."""
    # Structure: {source_file: {frame_number: [detections]}}
    by_file = defaultdict(lambda: defaultdict(list))
    file_to_mission_video = {}

    for f in sorted(DETECTIONS_DIR.glob("*_detections.csv")):
        stem = f.stem.replace("_detections", "")
        parts = stem.split("_")

        # Parse mission and video name from filename
        mission_parts = []
        video_parts = []
        in_video = False
        for p in parts:
            if not in_video and (p in ("VID", "DJI") or (p.startswith("P") and p[1:].isdigit())):
                in_video = True
            if in_video:
                video_parts.append(p)
            else:
                mission_parts.append(p)

        mission = "_".join(mission_parts)
        video_name = "_".join(video_parts) + ".MP4"

        file_to_mission_video[f.name] = (mission, video_name)

        with open(f, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                frame = int(row["frame_number"])
                by_file[f.name][frame].append(row)

    return by_file, file_to_mission_video


# ─── Frame selection ─────────────────────────────────────────────────────────

def select_frames(frame_detections, max_frames, flagged_only):
    """Select which frames to render for a given video.

    Prioritizes:
    1. Frames with impossible/flagged labels
    2. Frames with most detections
    3. Evenly spaced temporal sampling
    """
    frames_with_scores = []

    for frame_num, dets in frame_detections.items():
        score = 0
        has_flagged = False

        for d in dets:
            label = d["bioclip_label"]
            cls = classify_label(label)
            if cls == "impossible":
                score += 100
                has_flagged = True
            elif cls == "non_animal":
                score += 50
                has_flagged = True
            elif cls == "plausible":
                score += 10
                has_flagged = True

            conf = float(d.get("bioclip_score", 0))
            if conf < 0.4:
                score += 20
                has_flagged = True

        score += len(dets)  # more detections = more interesting

        if flagged_only and not has_flagged:
            continue

        frames_with_scores.append((frame_num, score, has_flagged))

    if not frames_with_scores:
        return []

    # Sort by score descending, take top candidates
    frames_with_scores.sort(key=lambda x: (-x[1], x[0]))

    # Take top-scoring frames, but ensure some temporal spread
    selected = []
    selected_nums = set()

    # First pass: take highest-priority frames
    priority_budget = max(max_frames // 2, 1)
    for frame_num, score, flagged in frames_with_scores[:priority_budget]:
        selected.append(frame_num)
        selected_nums.add(frame_num)

    # Second pass: fill remaining slots with evenly spaced frames
    remaining = max_frames - len(selected)
    if remaining > 0:
        all_frames = sorted(frame_detections.keys())
        step = max(1, len(all_frames) // (remaining + 1))
        for i in range(0, len(all_frames), step):
            if len(selected) >= max_frames:
                break
            f = all_frames[i]
            if f not in selected_nums:
                selected.append(f)
                selected_nums.add(f)

    return sorted(selected)


# ─── Rendering ───────────────────────────────────────────────────────────────

def draw_detections_on_frame(frame_bgr, detections):
    """Draw bounding boxes and labels on a frame. Returns PIL Image."""
    # Convert BGR -> RGB
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    draw = ImageDraw.Draw(img)

    # Try to get a reasonable font
    font_size = max(16, img.width // 120)
    try:
        font = ImageFont.truetype("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    small_font_size = max(12, font_size - 4)
    try:
        small_font = ImageFont.truetype("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf", small_font_size)
    except (OSError, IOError):
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", small_font_size)
        except (OSError, IOError):
            small_font = font

    box_width = max(2, img.width // 600)

    for det in detections:
        label = det["bioclip_label"]
        bioclip_conf = float(det.get("bioclip_score", 0))
        yolo_conf = float(det.get("yolo_conf", 0))
        x1 = int(float(det["xmin"]))
        y1 = int(float(det["ymin"]))
        x2 = int(float(det["xmax"]))
        y2 = int(float(det["ymax"]))

        color = get_color(label)
        cls = classify_label(label)

        # Draw bounding box
        for i in range(box_width):
            draw.rectangle([x1 - i, y1 - i, x2 + i, y2 + i], outline=color)

        # Build label text
        flag = ""
        if cls == "impossible":
            flag = " [IMPOSSIBLE]"
        elif cls == "non_animal":
            flag = " [NON-ANIMAL]"
        elif cls == "plausible":
            flag = " [?]"

        main_text = f"{label}{flag}"
        conf_text = f"bio:{bioclip_conf:.2f} yolo:{yolo_conf:.2f}"

        # Draw label background
        main_bbox = draw.textbbox((0, 0), main_text, font=font)
        conf_bbox = draw.textbbox((0, 0), conf_text, font=small_font)
        text_w = max(main_bbox[2] - main_bbox[0], conf_bbox[2] - conf_bbox[0])
        text_h = (main_bbox[3] - main_bbox[1]) + (conf_bbox[3] - conf_bbox[1]) + 4

        # Position label above box, or below if near top edge
        label_y = y1 - text_h - 4
        if label_y < 0:
            label_y = y2 + 2

        draw.rectangle(
            [x1, label_y, x1 + text_w + 8, label_y + text_h + 4],
            fill=(0, 0, 0, 180),
        )
        draw.text((x1 + 4, label_y + 2), main_text, fill=color, font=font)
        draw.text(
            (x1 + 4, label_y + 2 + (main_bbox[3] - main_bbox[1]) + 2),
            conf_text, fill=(200, 200, 200), font=small_font,
        )

    # Draw frame info in top-left corner
    frame_num = detections[0]["frame_number"] if detections else "?"
    frame_time = detections[0].get("frame_time_sec", "?") if detections else "?"
    info_text = f"Frame {frame_num} | {frame_time}s | {len(detections)} detections"
    info_bbox = draw.textbbox((0, 0), info_text, font=font)
    draw.rectangle([0, 0, info_bbox[2] - info_bbox[0] + 16, info_bbox[3] - info_bbox[1] + 8], fill=(0, 0, 0, 200))
    draw.text((8, 4), info_text, fill=(255, 255, 255), font=font)

    return img


# ─── Main ─────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Visualize drone detections on video frames")
    p.add_argument("--max-frames", type=int, default=10,
                   help="Max frames to render per video (default: 10)")
    p.add_argument("--mission", type=str, default=None,
                   help="Only process this mission (e.g., 20250908_djiair_4)")
    p.add_argument("--flagged-only", action="store_true",
                   help="Only render frames with flagged/suspicious labels")
    p.add_argument("--quality", type=int, default=85,
                   help="JPEG quality (default: 85)")
    return p.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("Drone Detection Visualization")
    print("=" * 60)

    print("\nBuilding video file map...")
    video_map = build_video_map()
    print(f"  Found {len(video_map)} video files across campaigns")

    print("Loading detections...")
    by_file, file_to_mission_video = load_detections_by_video()
    print(f"  Loaded detections for {len(by_file)} videos")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_frames_rendered = 0
    total_videos_processed = 0
    skipped_no_video = []

    for det_file in sorted(by_file.keys()):
        mission, video_name = file_to_mission_video[det_file]

        if args.mission and mission != args.mission:
            continue

        # Find the video file
        video_path = video_map.get((mission, video_name))
        if video_path is None:
            skipped_no_video.append((mission, video_name))
            continue

        frame_detections = by_file[det_file]

        # Select frames to render
        selected_frames = select_frames(frame_detections, args.max_frames, args.flagged_only)
        if not selected_frames:
            continue

        # Create output directory
        video_stem = video_name.replace(".MP4", "").replace(".mp4", "")
        out_dir = OUTPUT_DIR / mission / video_stem
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  {mission}/{video_name} — rendering {len(selected_frames)} frames")

        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"    ERROR: Could not open {video_path}")
            continue

        total_videos_processed += 1

        for target_frame in selected_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            if not ret:
                print(f"    WARNING: Could not read frame {target_frame}")
                continue

            dets = frame_detections[target_frame]
            annotated = draw_detections_on_frame(frame, dets)

            out_path = out_dir / f"frame_{target_frame:06d}_annotated.jpg"
            annotated.save(str(out_path), quality=args.quality)
            total_frames_rendered += 1

        cap.release()

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"  Videos processed: {total_videos_processed}")
    print(f"  Frames rendered:  {total_frames_rendered}")
    print(f"  Output: {OUTPUT_DIR}/")

    if skipped_no_video:
        print(f"\n  WARNING: {len(skipped_no_video)} videos skipped (MP4 not found):")
        for mission, vname in skipped_no_video:
            print(f"    {mission}/{vname}")

    # Write an index HTML for easy browsing
    write_index_html(OUTPUT_DIR)
    print(f"\n  Open annotation_review/frames/index.html to browse")


def write_index_html(output_dir):
    """Write a simple HTML gallery for browsing annotated frames."""
    html_path = output_dir / "index.html"

    # Collect all annotated images
    images = sorted(output_dir.rglob("*_annotated.jpg"))
    if not images:
        return

    # Group by mission/video
    grouped = defaultdict(list)
    for img in images:
        # path relative to output_dir
        rel = img.relative_to(output_dir)
        parts = rel.parts
        if len(parts) >= 3:
            key = f"{parts[0]}/{parts[1]}"
        else:
            key = str(rel.parent)
        grouped[key].append(rel)

    with open(html_path, "w") as f:
        f.write("""<!DOCTYPE html>
<html><head>
<title>Drone Detection Review</title>
<style>
  body { font-family: monospace; background: #1a1a1a; color: #eee; padding: 20px; }
  h1 { color: #4fc3f7; }
  h2 { color: #81c784; margin-top: 40px; border-bottom: 1px solid #444; padding-bottom: 8px; }
  .gallery { display: flex; flex-wrap: wrap; gap: 12px; }
  .frame { background: #2a2a2a; padding: 8px; border-radius: 4px; }
  .frame img { max-width: 800px; width: 100%; cursor: pointer; }
  .frame img:hover { outline: 2px solid #4fc3f7; }
  .frame .caption { font-size: 12px; color: #aaa; margin-top: 4px; }
  .legend { display: flex; gap: 20px; margin: 16px 0; }
  .legend span { padding: 4px 8px; border-radius: 3px; font-size: 13px; }
  .leg-valid { color: #00c800; border: 1px solid #00c800; }
  .leg-plausible { color: #ffa500; border: 1px solid #ffa500; }
  .leg-impossible { color: #ff0000; border: 1px solid #ff0000; }
  .leg-nonani { color: #808080; border: 1px solid #808080; }
  /* Lightbox */
  .lightbox { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.95); z-index: 999; justify-content: center; align-items: center; }
  .lightbox.active { display: flex; }
  .lightbox img { max-width: 95vw; max-height: 95vh; }
</style>
</head><body>
<h1>Drone Detection Review</h1>
<div class="legend">
  <span class="leg-valid">Valid species</span>
  <span class="leg-plausible">Plausible (needs check)</span>
  <span class="leg-impossible">Impossible species</span>
  <span class="leg-nonani">Non-animal</span>
</div>
""")

        for key in sorted(grouped.keys()):
            imgs = grouped[key]
            f.write(f'<h2>{key} ({len(imgs)} frames)</h2>\n')
            f.write('<div class="gallery">\n')
            for img_rel in imgs:
                frame_name = img_rel.name.replace("_annotated.jpg", "")
                f.write(f'  <div class="frame">\n')
                f.write(f'    <img src="{img_rel}" onclick="openLightbox(this.src)" />\n')
                f.write(f'    <div class="caption">{frame_name}</div>\n')
                f.write(f'  </div>\n')
            f.write('</div>\n')

        f.write("""
<div class="lightbox" id="lb" onclick="this.classList.remove('active')">
  <img id="lb-img" src="" />
</div>
<script>
function openLightbox(src) {
  document.getElementById('lb-img').src = src;
  document.getElementById('lb').classList.add('active');
}
</script>
</body></html>
""")

    print(f"  Wrote HTML gallery: {html_path}")


if __name__ == "__main__":
    main()
