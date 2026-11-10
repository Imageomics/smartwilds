# Experiment 5: Storage Savings from Edge Blank Image Filtering

## Key Results

- Total raw images analyzed: 235,778
- Images with no retained detections under the current camera-trap pipeline: 229,956 (97.53%)
- Raw storage volume: 236.89 GB
- Post-filter storage volume: 7.39 GB
- Storage saved by filtering: 229.51 GB (96.88%)
- Average raw arrival rate: 78.59 images/hour
- Average true-positive arrival rate: 1.94 images/hour
- Downstream throughput reduction: 40.50x

## Campaign Rollup

- 20250630_20250703: 15,081 images, 84.44% blank, 79.80% storage saved, 6.43x throughput reduction
- 20250804_20250828: 220,697 images, 98.42% blank, 97.97% storage saved, 63.49x throughput reduction

## Largest Absolute Storage Savings

- TW06-CT04_20250804_20250828: 93.52 GB saved (98.86%)
- TW09_CT02_20250804_20250828: 53.22 GB saved (99.20%)
- TW02-CT01_20250804_20250828: 46.01 GB saved (99.74%)

## Notes

- Raw-image counts and storage volumes come from rescanning the camera trap directories on disk.
- In this experiment, a filtered-out image is operationally treated as blank: it has no retained detections in the current YOLO/SAHI/BioCLIP pipeline outputs.
- True-positive arrival rate refers to images retained by the detector pipeline, not human-verified ground truth events.
- The combined `all_images_summary.csv` file was not used because it duplicates rows and would bias blank-rate estimates.