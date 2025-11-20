# Wildlife Detection and Species Identification

A pipeline for processing citizen science photos from The Wilds using MegaDetector v5 for wildlife detection and BioCLIP v2 for species identification.

## Overview

This project processes photos from Google Photos Takeout, extracting metadata and identifying wildlife species while filtering out photos containing people.

### Pipeline Components

1. **Metadata Extraction** ([process_photos.py](process_photos.py))
   - Extracts EXIF data (datetime, GPS coordinates)
   - Parses Google Takeout JSON metadata
   - Creates structured CSV with photo information

2. **Wildlife Detection** ([detect_species.py](detect_species.py))
   - **MegaDetector v5**: Detects animals, people, and vehicles
   - **BioCLIP v2**: Identifies species from detected animals
   - Filters out photos with people
   - Provides bounding boxes and confidence scores

## Features

- **Two-stage processing**: Detection → Species ID
- **People filtering**: Automatically exclude photos containing people
- **GPU acceleration**: Utilizes CUDA if available
- **Batch processing**: Process entire photo collections efficiently
- **Detailed outputs**: CSV summaries + JSON with full detection data
- **Custom species lists**: Optionally constrain predictions to known local species

## Installation

### Requirements

- Python 3.12+
- PyTorch with CUDA support (recommended)
- ~2GB disk space for model weights

### Setup with uv (recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

### Setup with pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Required Dependencies

```
pandas>=2.0.0
pillow>=10.0.0
numpy>=1.24.0
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.35.0
megadetector>=5.0.0
tqdm>=4.65.0
```

## Usage

### Step 1: Extract Photo Metadata

First, extract metadata from your photos:

```python
from process_photos import process_photo_folder

# Configure paths
input_folder = "/path/to/google/takeout/photos"
output_csv = "photo_metadata.csv"

# Process all photos
df = process_photo_folder(input_folder, output_csv)

# View summary
print(f"Processed {len(df)} photos")
print(f"Photos with GPS: {df['has_gps'].sum()}")
```

Run the script:
```bash
python process_photos.py
```

### Step 2: Detect Wildlife and Identify Species

Process photos with MegaDetector and BioCLIP:

```python
from detect_species import process_images

# Configure paths
image_folder = "/path/to/google/takeout/photos"
metadata_csv = "photo_metadata.csv"  # From step 1
output_csv = "wildlife_detections.csv"
output_json = "wildlife_detections.json"

# Optional: Define expected species
species_list = [
    "white-tailed deer",
    "bison",
    "giraffe",
    "rhinoceros",
    "zebra",
    "elk",
    "sandhill crane",
    "wild turkey"
]

# Process images
df = process_images(
    image_folder=image_folder,
    metadata_csv=metadata_csv,
    output_csv=output_csv,
    output_json=output_json,
    filter_people=True,      # Skip photos with people
    species_list=species_list,  # Optional species constraint
    max_images=None          # Process all images
)
```

Run the script:
```bash
python detect_species.py
```

### Example Workflow

```bash
# 1. Extract metadata from all photos
python process_photos.py

# 2. Detect wildlife and identify species
python detect_species.py

# 3. Analyze results
python -c "
import pandas as pd
df = pd.read_csv('wildlife_detections.csv')
print(df[df['contains_animals']].head())
"
```

## Output Data

### Metadata CSV (photo_metadata.csv)

| Column | Description |
|--------|-------------|
| filename | Image filename |
| file_path | Full path to image |
| datetime_taken | Photo timestamp from EXIF/JSON |
| latitude | GPS latitude |
| longitude | GPS longitude |
| has_gps | Boolean - GPS data available |
| width | Image width in pixels |
| height | Image height in pixels |

### Wildlife Detection CSV (wildlife_detections.csv)

| Column | Description |
|--------|-------------|
| filename | Image filename |
| file_path | Full path to image |
| num_animals | Count of detected animals |
| num_people | Count of detected people |
| num_vehicles | Count of detected vehicles |
| contains_animals | Boolean - animals present |
| species_detected | Comma-separated species names |
| num_species | Number of unique species |
| avg_species_confidence | Average confidence score |

### Detailed JSON (wildlife_detections.json)

Contains full detection data including:
- Bounding boxes for each detection
- Confidence scores
- Species predictions with probabilities
- MegaDetector raw outputs

## Configuration

### Model Settings

Edit [detect_species.py](detect_species.py) to adjust:

```python
# Detection confidence threshold
detector = WildlifeDetector(confidence_threshold=0.2)  # Default: 0.2

# Bounding box padding
cropped = detector.crop_detection(image, bbox, padding=0.1)  # Default: 10%

# Top-K species predictions
predictions = detector.identify_species(image_path, bboxes, top_k=5)
```

### Species Lists

For better accuracy with known wildlife in your area, define a species list:

```python
# The Wilds (Ohio) common species
species_list = [
    "white-tailed deer",
    "american bison",
    "giraffe",
    "greater one-horned rhinoceros",
    "plains zebra",
    "roosevelt elk",
    "przewalski's horse",
    "trumpeter swan",
    "canada goose",
    "sandhill crane",
    "turkey vulture",
    "red-tailed hawk",
    "wild turkey"
]
```

## Model Details

### MegaDetector v5

- **Purpose**: Object detection (animals, people, vehicles)
- **Architecture**: YOLOv5-based
- **Categories**:
  - Category 1: Animals
  - Category 2: People
  - Category 3: Vehicles
- **Model size**: ~300MB
- **Source**: [Microsoft CameraTraps](https://github.com/microsoft/CameraTraps)

### BioCLIP v2

- **Purpose**: Species identification
- **Architecture**: CLIP-based vision-language model
- **Training**: Trained on biological imagery
- **Model**: `imageomics/bioclip-2` on HuggingFace
- **Features**:
  - Zero-shot classification
  - Natural language species queries
  - Fine-tuned for biodiversity
- **Source**: [Imageomics BioCLIP](https://huggingface.co/imageomics/bioclip-2)

## Performance

### Processing Speed

- **MegaDetector**: ~0.1-0.5s per image (GPU)
- **BioCLIP**: ~0.2-0.8s per detection (GPU)
- **Total**: ~0.5-2s per image with animals

For 1000 photos:
- ~10-30 minutes on GPU
- ~1-3 hours on CPU

### Accuracy

- **MegaDetector**: >95% recall for animals in camera trap images
- **BioCLIP**: State-of-the-art for biological species recognition
- **People filtering**: High precision (low false negatives)

## Filtering Strategy

The pipeline automatically filters photos:

1. **People detection**: Photos with people are excluded
2. **Animal detection**: Only photos with animals proceed to species ID
3. **Confidence thresholding**: Low-confidence detections can be filtered

This approach:
- Reduces privacy concerns
- Saves computation time
- Focuses analysis on wildlife

## Troubleshooting

### CUDA/GPU Issues

```bash
# Check PyTorch CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install PyTorch with CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### MegaDetector Download Issues

If automatic download fails:

```bash
# Manually download model
wget https://github.com/microsoft/CameraTraps/releases/download/v5.0/md_v5a.0.0.pt

# Place in project directory or specify path in code
```

### Memory Issues

For large batches:

```python
# Process in smaller batches
process_images(image_folder, max_images=100)

# Reduce image size before processing
# Add to detect_species.py
image = image.resize((1280, 720))
```

## Project Structure

```
wilds_multimodal_data/
├── README_SETUP.md          # This file
├── process_photos.py        # Metadata extraction
├── detect_species.py        # Wildlife detection & species ID
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
├── photo_metadata.csv      # Output: metadata
├── wildlife_detections.csv # Output: detections
└── wildlife_detections.json # Output: detailed results
```

## Cost Analysis

- **MegaDetector**: Free (runs locally)
- **BioCLIP**: Free (runs locally)
- **Storage**: ~2GB for models
- **Compute**: GPU recommended but not required

No API costs or cloud services needed.

## Citation

If you use this pipeline, please cite:

**MegaDetector**:
```
@software{megadetector,
  author = {Microsoft AI for Earth},
  title = {MegaDetector v5},
  url = {https://github.com/microsoft/CameraTraps}
}
```

**BioCLIP**:
```
@article{bioclip2024,
  title = {BioCLIP: A Vision Foundation Model for the Tree of Life},
  author = {Imageomics Institute},
  year = {2024},
  url = {https://huggingface.co/imageomics/bioclip-2}
}
```

## License

See individual model licenses:
- MegaDetector: MIT License
- BioCLIP: Check model card on HuggingFace

## Support

For issues or questions:
- MegaDetector: [CameraTraps GitHub](https://github.com/microsoft/CameraTraps/issues)
- BioCLIP: [HuggingFace model page](https://huggingface.co/imageomics/bioclip-2)
