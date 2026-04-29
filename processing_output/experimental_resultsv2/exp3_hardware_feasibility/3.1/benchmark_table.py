#!/usr/bin/env python3
"""Generate the Exp 3 hardware/model benchmark table.

The table is intentionally explicit about assumptions. Rows marked
``provisional`` are good enough to run the prediction pipeline, but should be
replaced with final cited benchmark values before paper submission.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


OUT = Path(__file__).resolve().parent / "benchmark_table.csv"


ROWS = [
    # Workstation RTX-class tier.
    ("birdnet", "workstation_rtx", 14.0, math.nan, 250.0, "https://github.com/tphakala/birdnet-go/discussions/359", "CPU inference on Intel i7-13700K; latency from BirdNET-Go community benchmark; GPU not used"),
    ("yolo_world", "workstation_rtx", 12.0, 315.0, 1500.0, "https://huggingface.co/D-Robotics/DOSOD/blob/main/README.md", "conservative YOLO-World planning value from RTX 4090 FP16 benchmark family; SAHI tiling overhead not included"),
    ("sam3", "workstation_rtx", 120.0, 315.0, 8000.0, "https://github.com/ChaoningZhang/MobileSAM", "conservative SAM-family planning estimate between original SAM and MobileSAM GPU anchors; not a direct SAM3 benchmark"),
    ("bioclip", "workstation_rtx", 18.0, 315.0, 2200.0, "https://docs.nvidia.com/nim/nvclip/latest/performance.html", "conservative CLIP-family planning estimate anchored to NVIDIA NV-CLIP RTX 4090 performance"),
    ("megadetector", "workstation_rtx", 56.8, 315.0, 1200.0, "https://megadetector.readthedocs.io/en/latest/userguide.html", "MegaDetector docs list RTX 4090 at 17.6 images/s; converted to 56.8 ms/image"),
    # Jetson Orin Nano Super tier.
    ("birdnet", "jetson_orin_nano", math.nan, 16.0, 250.0, "https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/", "unsupported/unmeasured for latency; source anchors Jetson power range only"),
    ("yolo_world", "jetson_orin_nano", 45.0, 16.0, 1500.0, "https://blog.roboflow.com/run-inference/", "proxy edge estimate from YOLOv8-n on Jetson Orin Nano, rounded upward for YOLO-World planning"),
    ("sam3", "jetson_orin_nano", 900.0, 16.0, 8000.0, "https://github.com/NVIDIA-AI-IOT/nanosam", "extrapolated SAM-family Jetson estimate; memory constrained"),
    ("bioclip", "jetson_orin_nano", 120.0, 16.0, 2200.0, "https://blog.roboflow.com/clip-jetson-orin/", "extrapolated CLIP-family edge estimate; no direct BioCLIP benchmark found"),
    ("megadetector", "jetson_orin_nano", 80.0, 16.0, 1200.0, "https://github.com/Qengineering/YoloV8-ncnn-Raspberry-Pi-4", "YOLOv5-family detector proxy for MegaDetector v5 on Orin-class edge hardware"),
    # Raspberry Pi 5 + Coral TPU.
    ("birdnet", "pi5_coral", 90.0, 27.0, 250.0, "https://github.com/tphakala/birdnet-go/discussions/359", "Raspberry Pi 5 CPU inference; Coral not used"),
    ("yolo_world", "pi5_coral", math.nan, 27.0, 1500.0, "https://github.com/AILab-CVC/YOLO-World", "unsupported; no reliable Edge TPU deployment path for YOLO-World"),
    ("sam3", "pi5_coral", math.nan, 27.0, 8000.0, "https://github.com/ChaoningZhang/MobileSAM", "unsupported; no feasible Edge TPU deployment for full SAM3"),
    ("bioclip", "pi5_coral", math.nan, 27.0, 2200.0, "https://github.com/mlfoundations/open_clip", "unsupported; OpenCLIP-style transformer encoder is not treated as Edge TPU deployable"),
    ("megadetector", "pi5_coral", math.nan, 27.0, 1200.0, "https://github.com/microsoft/CameraTraps/releases", "unsupported; MegaDetector v5 is YOLOv5/PyTorch-based and not assumed Coral-compatible"),
    # Raspberry Pi 4 CPU-only.
    ("birdnet", "pi4_cpu", 166.0, 12.5, 250.0, "https://github.com/tphakala/birdnet-go/discussions/359", "Raspberry Pi 4B CPU inference from BirdNET-Go community benchmark"),
    ("yolo_world", "pi4_cpu", 2500.0, 12.5, 1500.0, "https://github.com/Qengineering/YoloV8-ncnn-Raspberry-Pi-4", "extrapolated CPU planning estimate from Raspberry Pi detector benchmarks"),
    ("sam3", "pi4_cpu", math.nan, 12.5, 8000.0, "https://github.com/ChaoningZhang/MobileSAM", "unsupported/infeasible in practice due to memory pressure and latency"),
    ("bioclip", "pi4_cpu", 1800.0, 12.5, 2200.0, "https://github.com/mlfoundations/open_clip", "very slow CPU planning estimate for OpenCLIP-style ViT encoder"),
    ("megadetector", "pi4_cpu", 3000.0, 12.5, 1200.0, "https://github.com/Qengineering/Yolact-ncnn-Raspberry-Pi-4", "very slow CPU estimate from Raspberry Pi detector benchmark proxies"),
    # Field laptop prediction placeholder. Exp 3.5 can replace this once the
    # actual spec is known; keeping it here lets Table V shape stabilize.
    ("birdnet", "field_laptop", 37.0, math.nan, 250.0, "https://github.com/tphakala/birdnet-go/discussions/359", "Intel i5-7260U laptop CPU inference from BirdNET-Go community benchmark"),
    ("yolo_world", "field_laptop", 45.0, math.nan, 1500.0, "https://huggingface.co/D-Robotics/DOSOD/blob/main/README.md", "scaled laptop GPU estimate from YOLO-World RTX 4090 FP16 benchmark family"),
    ("sam3", "field_laptop", 350.0, math.nan, 8000.0, "https://github.com/ChaoningZhang/MobileSAM", "extrapolated laptop GPU planning estimate from SAM-family speed anchors"),
    ("bioclip", "field_laptop", 55.0, math.nan, 2200.0, "https://docs.nvidia.com/nim/nvclip/latest/performance.html", "scaled laptop GPU estimate from NVIDIA NV-CLIP FP16 GPU performance"),
    ("megadetector", "field_laptop", 333.0, math.nan, 1200.0, "https://megadetector.readthedocs.io/en/latest/userguide.html", "MegaDetector docs list laptop RTX 3050 at 3.0 images/s; converted to 333 ms/image"),
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
