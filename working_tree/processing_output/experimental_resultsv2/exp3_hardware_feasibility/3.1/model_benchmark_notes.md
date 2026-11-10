# Model Benchmark Notes

This note collects model-specific benchmark rows and interpretation notes for
Exp 3 predicted hardware feasibility.

## Shared notes

- These rows are intended as predicted inputs for Exp 3.
- `power_W` values are device-level estimates or spec values unless otherwise noted.
- `memory_MB` values are working estimates for deployment planning, not measured
  peak allocator traces unless explicitly stated.
- `source_url` is intended to point to the source that anchors the row value.
  For extrapolated rows, the cell may include both the benchmark basis and the
  hardware/deployment reference, separated by `<br>`.
- When a row is not a literal copy of the benchmark figure in the source, the
  `notes` field explicitly states whether the number is a proxy, a
  conservative planning value, or an extrapolation.
- The `yolo_world` rows below are **not with SAHI**. If SAHI is used, multiply
  the base detector latency by the number of slices processed.

## BirdNET

### Status

- `workstation_rtx`: keep
- `jetson_orin_nano`: keep only as unsupported/unmeasured for latency
- `pi5_coral`: keep, but this is Raspberry Pi 5 CPU inference; Coral is not used
- `pi4_cpu`: keep
- `field_laptop`: keep

### Rows

| model | tier | latency_ms | power_W | memory_MB | source_url | notes |
| --- | --- | ---: | ---: | ---: | --- | --- |
| birdnet | workstation_rtx | 14 | N/A | ~250 | https://github.com/tphakala/birdnet-go/discussions/359 | CPU inference on Intel i7-13700K (8 threads), TFLite + XNNPACK; latency taken from the GitHub community benchmark in discussion 359; ~3 s audio window; GPU not used |
| birdnet | jetson_orin_nano | N/A | 7-25 | ~250 | https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/ | No direct BirdNET latency benchmark found for Jetson Orin Nano; source URL is the NVIDIA device spec used for the power range; row retained as unsupported/unmeasured prediction input |
| birdnet | pi5_coral | 90 | ~27 | ~250 | https://github.com/tphakala/birdnet-go/discussions/359<br>https://github.com/tphakala/birdnet-go/wiki/BirdNET%E2%80%90Go-Guide | BirdNET run on Raspberry Pi 5 CPU; latency taken from discussion 359; BirdNET-Go guide is the support source for Raspberry Pi use and Coral non-support; Coral is not used |
| birdnet | pi4_cpu | 166 | 12.5 | ~250 | https://github.com/tphakala/birdnet-go/discussions/359 | Raspberry Pi 4B CPU inference (4 threads), TFLite + XNNPACK; latency taken from the GitHub community benchmark; ~3 s audio window; power from PSU/device estimate |
| birdnet | field_laptop | 37 | N/A | ~250 | https://github.com/tphakala/birdnet-go/discussions/359 | CPU inference on Intel i5-7260U laptop; latency taken from the GitHub community benchmark; ~3 s audio window; GPU not used |

## YOLO-World

### Status

- `workstation_rtx`: keep
- `jetson_orin_nano`: keep as estimated
- `pi5_coral`: unsupported / no reliable latency
- `pi4_cpu`: keep as extrapolated CPU estimate
- `field_laptop`: keep as scaled laptop GPU estimate

### Rows

| model | tier | latency_ms | power_W | memory_MB | source_url | notes |
| --- | --- | ---: | ---: | ---: | --- | --- |
| yolo_world | workstation_rtx | 12 | ~315 | ~1500 | https://huggingface.co/D-Robotics/DOSOD/blob/main/README.md<br>https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090 | Conservative end-to-end planning estimate. The direct DOSOD/YOLO-World RTX 4090 TensorRT FP16 table reports 1007-1221 FPS for YOLO-World variants at 640 resolution (roughly sub-2 ms compute time); this row intentionally inflates that benchmark to 12 ms for a safer single-image planning budget. RTX 4090 spec page anchors the workstation power band |
| yolo_world | jetson_orin_nano | ~45 | 7-25 | ~1500 | https://blog.roboflow.com/run-inference/<br>https://developer.nvidia.com/embedded/jetson-orin-nano | Proxy edge estimate. Roboflow reports ~25 FPS for YOLOv8-n on Jetson Orin Nano (~40 ms/image); this row rounds slightly upward to 45 ms as a safer open-vocabulary detector planning value. NVIDIA Jetson docs anchor the power range |
| yolo_world | pi5_coral | N/A | ~27 | ~1500 | https://github.com/AILab-CVC/YOLO-World<br>https://coral.ai/products/accelerator/ | Coral TPU unsupported for YOLO-World because there is no supported Edge TPU deployment path for the model; YOLO-World repo used for model/deployment context and Coral docs for the accelerator spec |
| yolo_world | pi4_cpu | ~2500 | 12.5 | ~1500 | https://github.com/Qengineering/YoloV8-ncnn-Raspberry-Pi-4 | CPU latency is an extrapolated planning estimate using Raspberry Pi detector benchmarks from Qengineering as the reference basis; 640x640; very slow |
| yolo_world | field_laptop | ~45 | N/A | ~1500 | https://huggingface.co/D-Robotics/DOSOD/blob/main/README.md<br>https://www.waredb.com/processor/nvidia-geforce-rtx-3050-laptop | Laptop GPU estimate scaled from the YOLO-World family RTX 4090 FP16 benchmark table, with RTX 3050 laptop-class hardware used as the downscale target |

## SAM3

### Status

- `workstation_rtx`: keep as extrapolated GPU estimate
- `jetson_orin_nano`: keep as extrapolated and memory-constrained
- `pi5_coral`: unsupported / no feasible deployment
- `pi4_cpu`: unsupported / infeasible
- `field_laptop`: keep as extrapolated laptop GPU estimate

### Rows

| model | tier | latency_ms | power_W | memory_MB | source_url | notes |
| --- | --- | ---: | ---: | ---: | --- | --- |
| sam3 | workstation_rtx | ~120 | ~315 | ~8000 | https://github.com/ChaoningZhang/MobileSAM<br>https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090 | Conservative SAM-family planning estimate. MobileSAM reports 456 ms for original SAM and 12 ms for MobileSAM on a single GPU; this row places SAM3 between those anchors as a large-model workstation proxy rather than claiming a direct public SAM3 RTX 4090 benchmark. RTX 4090 spec page anchors the workstation power band |
| sam3 | jetson_orin_nano | ~900 | 7-25 | ~8000 | https://github.com/NVIDIA-AI-IOT/nanosam<br>https://github.com/facebookresearch/segment-anything-2/issues/161 | Extrapolated from SAM-family Jetson evidence: NanoSAM and MobileSAM performance on Orin-class hardware plus SAM2 Orin Nano installation/memory constraints; TensorRT support for full SAM-family models remains limited |
| sam3 | pi5_coral | N/A | ~27 | ~8000 | https://github.com/ChaoningZhang/MobileSAM<br>https://coral.ai/products/accelerator/ | Unsupported row; MobileSAM official speed table is the SAM-family benchmark basis and Coral docs are the accelerator spec basis; no feasible Edge TPU deployment for full SAM3 |
| sam3 | pi4_cpu | N/A | 12.5 | ~8000 | https://github.com/ChaoningZhang/MobileSAM | Unsupported row; even lightweight SAM-family CPU results are slow, so full SAM3 on Pi 4 CPU is treated as infeasible in practice due to memory pressure and latency |
| sam3 | field_laptop | ~350 | N/A | ~8000 | https://github.com/ChaoningZhang/MobileSAM | Laptop GPU latency is an extrapolated planning estimate using the official SAM-family speed table from MobileSAM as the benchmark anchor and assuming an RTX 3050 or 3060-class mobile GPU |

## MegaDetector

### Status

- `workstation_rtx`: keep
- `jetson_orin_nano`: keep as edge benchmark proxy
- `pi5_coral`: unsupported / CPU fallback only
- `pi4_cpu`: keep as very slow CPU estimate
- `field_laptop`: keep as scaled laptop GPU estimate

### Rows

| model | tier | latency_ms | power_W | memory_MB | source_url | notes |
| --- | --- | ---: | ---: | ---: | --- | --- |
| megadetector | workstation_rtx | ~57 | ~315 | ~1200 | https://megadetector.readthedocs.io/en/latest/userguide.html<br>https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090 | Directly anchored to the official MegaDetector user-guide timing table: RTX 4090 is reported at 17.6 images/s, which corresponds to about 56.8 ms/image. RTX 4090 spec page anchors the workstation power band |
| megadetector | jetson_orin_nano | ~80 | 7-25 | ~1200 | https://github.com/Qengineering/YoloV8-ncnn-Raspberry-Pi-4<br>https://github.com/microsoft/CameraTraps/releases | Edge estimate based on YOLOv5-family detector benchmarks on Orin-class hardware, with Microsoft CameraTraps release notes used to confirm MegaDetector v5's YOLOv5 architecture |
| megadetector | pi5_coral | N/A | ~27 | ~1200 | https://github.com/microsoft/CameraTraps/releases<br>https://coral.ai/products/accelerator/ | Unsupported row; MegaDetector v5 is YOLOv5/PyTorch-based per Microsoft release notes, and Coral's accelerator path is not compatible with the full model as deployed here |
| megadetector | pi4_cpu | ~3000 | 12.5 | ~1200 | https://github.com/Qengineering/Yolact-ncnn-Raspberry-Pi-4<br>https://github.com/microsoft/CameraTraps/releases | CPU estimate based on Raspberry Pi 4 YOLOv5 detector benchmarks from Qengineering, with Microsoft CameraTraps release notes used to confirm MegaDetector v5's YOLOv5 basis |
| megadetector | field_laptop | ~333 | N/A | ~1200 | https://megadetector.readthedocs.io/en/latest/userguide.html | Directly anchored to the official MegaDetector user-guide timing table: laptop RTX 3050 is reported at 3.0 images/s, which corresponds to about 333 ms/image |

## BioCLIP

### Status

- `workstation_rtx`: keep as CLIP-family GPU estimate
- `jetson_orin_nano`: keep as extrapolated edge estimate
- `pi5_coral`: unsupported / no feasible deployment
- `pi4_cpu`: keep as very slow CPU estimate
- `field_laptop`: keep as scaled laptop GPU estimate

### Rows

| model | tier | latency_ms | power_W | memory_MB | source_url | notes |
| --- | --- | ---: | ---: | ---: | --- | --- |
| bioclip | workstation_rtx | ~18 | ~315 | ~2200 | https://docs.nvidia.com/nim/nvclip/latest/performance.html<br>https://arxiv.org/abs/2311.18803<br>https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090 | Conservative CLIP-family planning estimate. NVIDIA's NV-CLIP page reports 0.291 s end-to-end latency for a batch of 64 images on RTX 4090, which is a much lower per-image throughput-derived figure; this row keeps a larger 18 ms single-image planning budget for BioCLIP-style deployment. The BioCLIP paper anchors model identity, and the RTX 4090 spec page anchors the workstation power band |
| bioclip | jetson_orin_nano | ~120 | 7-25 | ~2200 | https://blog.roboflow.com/clip-jetson-orin/<br>https://arxiv.org/abs/2311.18803 | No direct BioCLIP benchmark exists; this is an extrapolated CLIP-family edge estimate using Jetson Orin deployment guidance for CLIP-class models and the BioCLIP paper for model identity |
| bioclip | pi5_coral | N/A | ~27 | ~2200 | https://coral.ai/products/accelerator/<br>https://github.com/mlfoundations/open_clip | Unsupported row; Coral is not a natural deployment target for an OpenCLIP-style transformer encoder, so no feasible Edge TPU path is assumed |
| bioclip | pi4_cpu | ~1800 | 12.5 | ~2200 | https://github.com/mlfoundations/open_clip<br>https://arxiv.org/abs/2311.18803 | Very slow CPU planning estimate for an OpenCLIP-style ViT encoder; no direct public Pi 4 BioCLIP benchmark was found, so this remains a conservative extrapolation |
| bioclip | field_laptop | ~55 | N/A | ~2200 | https://docs.nvidia.com/nim/nvclip/latest/performance.html<br>https://www.waredb.com/processor/nvidia-geforce-rtx-3050-laptop | Laptop GPU estimate scaled from the NVIDIA NV-CLIP FP16 GPU performance table using RTX 3050 laptop-class hardware as the target capability band |
