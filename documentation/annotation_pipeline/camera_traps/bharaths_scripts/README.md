# Camera-Trap-Depth-GPS-Pipeline

This repository implements a **camera-trap image processing pipeline** that:

1. Detects animals in high-resolution still images using **YOLO (Ultralytics) + SAHI** (sliced inference)
2. Optionally assigns a coarse species label using **BioCLIP v2** (via `open_clip`)
3. Estimates **distance** and **relative viewing angle** from image geometry
4. Projects an **approximate GPS coordinate** for each detection when camera location and facing direction are known

> **Important note about camera trap data**  
> Metadata is often inconsistent across devices and deployments. This pipeline is explicitly designed to produce usable outputs when metadata is not missing (e.g., camera bearing or timestamps embedded in filenames).
> If meta data is missing such as camera bearing or datetime then manual annotation is needed.
---

## Installation

<pre> 
pip install torch torchvision
pip install ultralytics sahi
pip install opencv-python pillow numpy
pip install open_clip_torch
 </pre>

## Dataset Characteristics

- Static camera trap images (JPEG / PNG)
- Inconsistent metadata across devices
- Some deployments may lack:
  - Camera facing direction (bearing)
  - Timestamps embedded in filenames
  - Standardized filename datetime patterns


---

## Pipeline Stages

### Step 1: Input Images

Provide a directory of camera trap images, for example:

./camera_trap_images

## Step 2: Object Detection with YOLO + SAHI

Animal detections are generated using an **Ultralytics YOLO** model wrapped with **SAHI** for tiled inference on large images.

SAHI improves detection performance by:

- Splitting images into overlapping tiles
- Running YOLO inference per tile
- Merging detections using NMS / IOU logic

### Example

<pre> 
python camera_trap_detections.py \
  --weights yolov8x.pt \
  --images ./camera_trap_images \
  --conf 0.25 \
  --slice-h 512 \
  --slice-w 512 \
  --ovh 0.2 \
  --ovw 0.2
 </pre>

## Step 3: Optional Species Labeling (BioCLIP v2)

Each detected bounding box can optionally be classified using [**BioCLIP 2**](https://huggingface.co/imageomics/bioclip-2) against a user-provided label list.

### Example

<pre> 
python camera_trap_detections.py \
  --labels "white-tailed deer,deer,bird"

 </pre>


## Step 4: Distance & Angle Estimation (Geometric Approximation)

When a horizontal field-of-view (HFOV) and an approximate target height are provided, the pipeline estimates:

- `distance_m`: distance from camera to detection (meters)
- `angle_deg`: horizontal angle from image center (degrees)

### Example

<pre> 
python camera_trap_detections.py \
  --hfov-deg 90 \
  --target-height-m 1.2

 </pre>

## Step 5: GPS Projection 

If camera latitude, longitude, and facing direction are known, the pipeline projects an **approximate GPS coordinate** for each detection.

### Example

<pre> 
python camera_trap_detections.py \
  --camera-lat 39.8150 \
  --camera-lon -81.7250 \
  --camera-bearing-deg 135

 </pre>

## Missing Metadata Handling

### Missing Camera Bearing

Some deployments do not record camera facing direction.

Recommended handling:

- If bearing is unknown:
  - Set bearing to an arbitrary value and set `animal_lat` / `animal_lon` equal to the camera coordinates **or**
  - Leave projected animal coordinates blank


---

### Missing Timestamp in Filename

The pipeline can parse timestamps from filenames that follow patterns such as:

NSCF0001_YYMMDDHHMMSS_####.JPG
If no parsable timestamp is present:

timestamp_from_name is mannually anotated





## Output: CSV Schema

### File Information

- **Filename:** defined by `--csv-out`
- **Format:** CSV (UTF-8)
- **Granularity:** one row per **detection** (not per image)

---

### Core Output Columns

| Column Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `image` | String | Image filename | `NSCF0002_250805141303_0591.JPG` |
| `image_path` | String | Full path to image | `/fs/.../NSCF0002_...JPG` |
| `timestamp_file` | String (ISO datetime) | File modification timestamp | `2025-08-11T17:59:51.841391` |
| `detection_index` | Integer | 1-indexed detection per image | `1` |
| `bioclip_label` | String | BioCLIP predicted label | `white-tailed deer` |
| `bioclip_score` | Float | BioCLIP similarity score | `0.5133` |
| `yolo_conf` | Float | YOLO confidence score | `0.2691` |
| `distance_m` | Float | Estimated distance (meters) | `26.45` |
| `animal_lat` | Float | Projected latitude | `39.498376` |
| `animal_lon` | Float | Projected longitude | `-81.442449` |

---

### Extended / Debug Columns

Depending on flags and script version, additional fields may be included:

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `timestamp_from_name` | String (ISO datetime) | Timestamp parsed from filename |
| `xmin` | Float | Bounding box left (pixels) |
| `ymin` | Float | Bounding box top (pixels) |
| `xmax` | Float | Bounding box right (pixels) |
| `ymax` | Float | Bounding box bottom (pixels) |
| `angle_deg` | Float | Relative horizontal angle |
| `camera_lat` | Float | Camera latitude |
| `camera_lon` | Float | Camera longitude |
| `camera_bearing_deg` | Float | Camera bearing (deg clockwise from North) |
| `animal_absolute_bearing_deg` | Float | Camera bearing + relative angle |

## Example: Full Pipeline Run

<pre> 
python camera_trap_detections.py \
  --weights yolov8x.pt \
  --images ./camera_trap_images \
  --conf 0.25 \
  --slice-h 512 \
  --slice-w 512 \
  --ovh 0.2 \
  --ovw 0.2 \
  --hfov-deg 90 \
  --target-height-m 1.2 \
  --camera-lat 39.8150 \
  --camera-lon -81.7250 \
  --camera-bearing-deg 135 \
  --labels "white-tailed deer,deer,bird" \
  --csv-out ./outputs/camera_trap_depth_estimates.csv
 </pre>
