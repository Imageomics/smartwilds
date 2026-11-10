#!/usr/bin/env python3
"""Generate the Exp 3 hardware/model benchmark table.

The table is intentionally explicit about assumptions. Rows marked
``provisional`` are good enough to run the prediction pipeline, but should be
replaced with final cited benchmark values before paper submission.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


OUT = Path(__file__).resolve().parent / "benchmark_table.csv"


ROWS = [
    # Workstation tier. SAM3 row uses the local A100 benchmark in this workspace;
    # RTX-class rows should be replaced if a specific workstation GPU is named.
    ("birdnet", "workstation_rtx", 50.0, 250.0, 600.0, "https://pypi.org/project/birdnet/", "provisional GPU/CPU planning estimate; BirdNET package documents CPU/GPU backends"),
    ("yolo_sahi", "workstation_rtx", 12.0, 250.0, 1200.0, "https://github.com/ultralytics/ultralytics/issues/8280", "provisional YOLO TensorRT batch-1 edge/desktop estimate; SAHI tiling overhead not included"),
    ("sam3", "workstation_rtx", 2295.5, 250.0, 4751.0, "local A100 benchmark run (sam3_hf_benchmarks/vid005_bs1_100img/summary.json; not shipped)", "local A100 SAM3 HF benchmark p95 total latency, batch=1, 100 images, prompts animal/person/vehicle"),
    ("bioclip", "workstation_rtx", 35.0, 250.0, 1200.0, "https://github.com/Imageomics/bioclip", "provisional CLIP-style image embedding estimate; replace with measured BioCLIP benchmark"),
    ("megadetector", "workstation_rtx", 56.8, 250.0, 1800.0, "https://megadetector.readthedocs.io/en/latest/_modules/megadetector/detection/run_detector.html", "MegaDetector docs list MDv5 speed for RTX 4090 as 17.6 images/s; converted to 56.8 ms/image"),
    # Jetson Orin Nano Super tier.
    ("birdnet", "jetson_orin_nano", 220.0, 15.0, 600.0, "https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/", "provisional; scaled from workstation estimate and Jetson 7W-25W power envelope"),
    ("yolo_sahi", "jetson_orin_nano", 25.0, 15.0, 1200.0, "https://pmc.ncbi.nlm.nih.gov/articles/PMC13030541/", "YOLOv8/YOLO11 pose on Orin Nano reports roughly 24-61 ms at 640x512 depending model size/precision; using 25 ms optimistic detector row"),
    ("sam3", "jetson_orin_nano", 12000.0, 15.0, 6000.0, "https://huggingface.co/docs/transformers/en/model_doc/sam3", "extrapolated planning value; SAM3 docs note 1008px default and lower resolution for memory/speed tradeoff"),
    ("bioclip", "jetson_orin_nano", 250.0, 15.0, 1200.0, "https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/", "provisional CLIP-style image embedding estimate on Jetson"),
    ("megadetector", "jetson_orin_nano", 120.0, 15.0, 1800.0, "https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/", "provisional MDv5 detector estimate; replace with direct Jetson benchmark if available"),
    # Raspberry Pi 5 + Coral TPU.
    ("birdnet", "pi5_coral", 900.0, 8.3, 600.0, "https://www.coral.ai/products/accelerator", "provisional; BirdNET generally CPU-bound unless converted to Edge TPU-compatible TFLite"),
    ("yolo_sahi", "pi5_coral", 85.0, 8.3, 800.0, "https://www.alibaba.com/product-insights/raspberry-pi-5-vs-nvidia-jetson-orin-nano-which-is-actually-better-for-beginner-ai-projects.html", "reported Pi5+Coral YOLOv5s INT8/TFLite latency; use as detector proxy"),
    ("sam3", "pi5_coral", 60000.0, 8.3, 6000.0, "https://huggingface.co/docs/transformers/en/model_doc/sam3", "extrapolated; SAM3 is not Edge TPU-native and likely infeasible on this tier"),
    ("bioclip", "pi5_coral", 1500.0, 8.3, 1200.0, "https://www.coral.ai/products/accelerator", "provisional; CLIP-style model not assumed Edge TPU-native"),
    ("megadetector", "pi5_coral", 85.0, 8.3, 1000.0, "https://www.alibaba.com/product-insights/raspberry-pi-5-vs-nvidia-jetson-orin-nano-which-is-actually-better-for-beginner-ai-projects.html", "detector proxy from Pi5+Coral YOLOv5s latency"),
    # Raspberry Pi 4 CPU-only.
    ("birdnet", "pi4_cpu", 1800.0, 6.0, 600.0, "https://pypi.org/project/acoupi-birdnet/", "provisional; acoupi-birdnet documents BirdNET use on Raspberry Pi-class edge devices"),
    ("yolo_sahi", "pi4_cpu", 1200.0, 6.0, 800.0, "https://www.raspberrypi.com/products/raspberry-pi-4-model-b/specifications/", "provisional CPU-only detector estimate; replace with measured Pi4 YOLO/SAHI benchmark"),
    ("sam3", "pi4_cpu", 120000.0, 6.0, 6000.0, "https://huggingface.co/docs/transformers/en/model_doc/sam3", "extrapolated; SAM3 expected infeasible on Pi4 CPU"),
    ("bioclip", "pi4_cpu", 3000.0, 6.0, 1200.0, "https://www.raspberrypi.com/products/raspberry-pi-4-model-b/specifications/", "provisional CPU-only CLIP-style estimate"),
    ("megadetector", "pi4_cpu", 1200.0, 6.0, 1000.0, "https://www.raspberrypi.com/products/raspberry-pi-4-model-b/specifications/", "provisional CPU-only detector estimate"),
    # Field laptop prediction placeholder. Exp 3.5 can replace this once the
    # actual spec is known; keeping it here lets Table V shape stabilize.
    ("birdnet", "field_laptop", 180.0, 45.0, 600.0, "https://pypi.org/project/birdnet/", "placeholder until exp3_5_calibration/laptop_spec.md is filled"),
    ("yolo_sahi", "field_laptop", 400.0, 45.0, 1200.0, "https://megadetector.readthedocs.io/en/latest/userguide.html", "placeholder laptop CPU/GPU detector estimate"),
    ("sam3", "field_laptop", 20000.0, 45.0, 6000.0, "https://huggingface.co/docs/transformers/en/model_doc/sam3", "placeholder; likely infeasible without discrete GPU"),
    ("bioclip", "field_laptop", 700.0, 45.0, 1200.0, "https://github.com/Imageomics/bioclip", "placeholder until laptop spec and runtime are known"),
    ("megadetector", "field_laptop", 2500.0, 45.0, 1800.0, "https://megadetector.readthedocs.io/en/latest/userguide.html", "MegaDetector docs give laptop CPU guidance of 30k-50k images/day; converted to ~1.7-2.9 s/image"),
]


def main() -> None:
    df = pd.DataFrame(
        ROWS,
        columns=["model", "tier", "latency_ms", "power_W", "memory_MB", "source_url", "notes"],
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
