import os
import cv2
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# ─── Configuration ─────────────────────────────────────────────────────────────
video_path      = "/fs/ess/PAS2136/TheWilds2025/thewilds_20250804_20250828/drones/20250811_DJI_01/videos/DJI_0002.MOV"
output_dir      = "/fs/ess/PAS2699/object_detection_datasets/smartwilds_drones/thewilds_20250804_20250828/drones/20250811_DJI_01/videos/DJI_0002_frames/"
image_ext       = "png"                   # "jpg", "png", etc.
frame_interval  = 15                      # only save every 15th frame
num_workers     = os.cpu_count() or 4     # threads for parallel writes
# ────────────────────────────────────────────────────────────────────────────────

os.makedirs(output_dir, exist_ok=True)

# derive base name for file naming
base_name = os.path.splitext(os.path.basename(video_path))[0]

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    raise IOError(f"Cannot open video file: {video_path}")

total_frames  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
# estimate how many frames will actually be saved → for zero‐padded filenames
max_saved     = (total_frames + frame_interval - 1) // frame_interval
digits        = len(str(max_saved))

frame_width   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

images = []
saved_count = 0

def save_frame(frame, path):
    """Helper to write a frame to disk."""
    cv2.imwrite(path, frame)

with ThreadPoolExecutor(max_workers=num_workers) as executor:
    for frame_idx in tqdm(range(total_frames), desc="Extracting every 15th frame"):
        ret, frame = cap.read()
        if not ret:
            break

        # skip until we hit the next interval
        if frame_idx % frame_interval != 0:
            continue

        # schedule save
        filename = f"{base_name}_{frame_idx:06d}.{image_ext}"
        filepath = os.path.join(output_dir, filename)
        executor.submit(save_frame, frame.copy(), filepath)

        # record for COCO
        images.append({
            "id": saved_count,
            "file_name": filename,
            "width": frame_width,
            "height": frame_height
        })
        saved_count += 1

cap.release()

# build minimal COCO annotation file
coco_output = {
    "images": images,
    "annotations": [],
    "categories": []
}

coco_path = os.path.join(output_dir, f"{base_name}_annotations.json")
with open(coco_path, "w") as f:
    json.dump(coco_output, f, indent=4)

print(f"Done! Saved {saved_count} frames (every {frame_interval}th) to '{output_dir}'.")
print(f"COCO annotation file saved to '{coco_path}'.")
