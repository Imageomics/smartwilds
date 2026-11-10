# Wilds Multimodal Data Processing
Analysis of multi-modal dataset collected at The Wilds Summer 2025.

This repository contains exploratory and processing scripts, separated by modality, with some cross-modality helper scripts maintained at the root level. Please see each modality's respective `README` for details on processing and setup.

## Project Structure

```
wilds_multimodal_data/
├── citizen_science/
|   ├──  data/
|   |   ├── photo_metadata.csv      # Output: metadata
|   |   ├── wildlife_detections.csv # Output: detections
|   |   ├── wildlife_detections.json
|   |   ├── wildlife_detections_review.csv
|   |   └── annotated_images/
|   |
|   ├── notebooks/
|   |   └── citizen_science.ipynb
|   └── process_photos.py        # Metadata extraction for citizen science images
|
├── detection/
|   ├── batch_review.py
|   ├── detect_species.py        # Wildlife detection & species ID
|   └── review_detections.py
|
├── main.py                  # Entry point
├── pyproject.toml          # Project configuration
└── requirements.txt         # Python dependencies
```
