# Sensor Configuration Reference

Consolidated sensor configurations across all deployments at The Wilds 2025.
These configs directly impact workload analysis (data arrival rates, storage, compute requirements)
and species detectability (detection probability, spatial coverage).

Last updated: 2026-03-20

---

## Camera Trap Configurations

### Camera Models

| Model | Manufacturer | HFOV (°) | Notes |
|-------|-------------|----------|-------|
| GardePro T5NG | GardePro | 56.5 | Standard trail cam, photo-only or hybrid |
| GardePro A3 | GardePro | 63 | Video-capable model |
| Trail Camera G600 | Trail Camera | 120 | Wide-angle lens |
| Reveal Pro 3.0 | Tactacam | 55 | Cellular-capable, 4K photo, HD video |

### Campaign 1: June 30 – July 3, 2025

| Camera | Site | Model | HFOV | Facing | Mode | Photo Config | Video Config | PIR | Delay | Notes |
|--------|------|-------|------|--------|------|-------------|-------------|-----|-------|-------|
| CT02 | TW01 - Nomad Ridge E | GardePro T5NG | 56.5° | SE (135°) | Hybrid | 4MP, 3-burst | 1080p, 10s, MP4+audio | High | — | Timelapse hourly, info strip ON |
| CT03 | TW02 - Nomad Ridge W | GardePro A3 | 63° | SW (225°) | Photo+Video | 8MP, 3-series | 1080p, 10s, AVI+audio | High | 10s shot lag | Only 55 files captured (early battery death) |
| CT01 | TW03 - Pasture D Feeder | GardePro T5NG | 56.5° | S (180°) | — | — | — | — | — | Near salt lick, config not documented |
| CT04 | TW04 - Lake Trail | Trail Camera G600 | 120° | NW (315°) | Photo+Video | 8MP, 5-burst | 1080p, 10s, MP4+audio | High | — | Images upside-down (mount orientation) |

### Campaign 2: August 4 – August 28, 2025

| Camera | Site | Model | HFOV | Facing | Mode | Photo Config | Video Config | PIR/Sensitivity | Delay | Notes |
|--------|------|-------|------|--------|------|-------------|-------------|----------------|-------|-------|
| CT02 | TW01 - Nomad Ridge E | GardePro T5NG | 56.5° | SE (135°) | Photo only | 4MP, 3-burst | — | High | — | 26,573 JPG; removed Aug 11, relocated to dock |
| CT01 | TW02 - Nomad Ridge W | GardePro T5NG | 56.5° | SW (225°) | Photo only | 4MP, 3-burst | — | High | — | 61,217 JPG; DATE ERROR (clock incorrect); battery died Aug 18-25 |
| CT03 | TW04 - Lake Trail | GardePro A3 | 63° | NW (315°) | Photo+Video | 8MP, 3-burst | 1080p, 10s | — | — | 984 JPG + 67 AVI; reset Aug 7, no data after Aug 25 |
| CT04 | TW06 - Zebra Shelter | Trail Camera G600 | 120° | NW (315°) | Photo+Video | 8MP, 5-burst | 1080p, 10s | Motion detection | — | 40,907 JPG; battery 100% (unusual) |
| CT05 | TW06 - Zebra Shelter (inside) | Reveal Pro 3.0 | 55° | N (0°) | Photo+Video | 4K | 720p, 10s | — | — | 84 jpg + 84 mp4; late deploy Aug 25-28 |
| CT05 | TW07 - Zipline Tower | Reveal Pro 3.0 | 55° | N (0°) | Photo+Video | 4K | 720p, 10s | — | — | ALL PEOPLE (tour buses); no wildlife images |
| CT02 | TW09 - Dock (left) | GardePro T5NG | 56.5° | S (180°) | Photo only | 4MP, 3-burst | — | — | — | 90,834 JPG (largest dataset); battery gap Aug 18-25 |
| CT05 | TW09 - Dock (right) | Reveal Pro 3.0 | 55° | SE (135°) | Photo+Video | 4K | 720p, 10s | — | — | Only 9 jpg + 6 mp4; detection issues |
| CT06 | TW11 - Fence/lake | Reveal Pro 3.0 | 55° | NE (45°) | Photo+Video | 4K | FHD 1080p, 15s | Level 9 | 20s | 89 jpg + 23 mp4; Pic+Video mode, multi-shot 1s interval, flash high, 1 bar cell service |

### Workload Impact Summary — Camera Traps

| Config Parameter | Impact on Workload |
|------------------|--------------------|
| **Burst mode (3-burst vs 5-burst)** | 3x or 5x multiplier on raw image count per trigger event |
| **Photo+Video vs Photo only** | Video adds ~10-15s clips per trigger; significant storage (AVI/MP4) and compute for frame extraction |
| **PIR sensitivity (High/Level 9)** | Higher sensitivity → more triggers → higher arrival rate; also more blanks/false positives |
| **HFOV (55°–120°)** | Wide-angle (G600, 120°) captures more area but lower pixel density per animal; narrow FOV (Reveal, 55°) better for ID but smaller detection zone |
| **Resolution (4MP vs 8MP vs 4K)** | Higher resolution → larger files → more storage and inference time per image |
| **Delay (0s vs 10s vs 20s)** | Longer delay between triggers → lower effective arrival rate; reduces duplicate captures |
| **Cellular capability** | Reveal Pro 3.0 can transmit photos in near-real-time (when cell service exists) — relevant for edge processing SLOs |

---

## Bioacoustic Recorder Configurations

All recorders: **Wildlife Acoustics Song Meter Micro 2**

### Campaign 1: June 30 – July 3, 2025

| Recorder | Site | GPS | Orientation | Height | Recording Schedule | WAV Count | Storage |
|----------|------|-----|-------------|--------|-------------------|-----------|---------|
| SM01 | TW05 - Lake Trail Gate O | 39.83537, -81.73842 | East | ~1.5m | 5-min clips every hour (intended 1hr sunrise/sunset — config error) | 144 | — |
| SM03 | TW06 - Zebra Shelter | 39.83518, -81.73087 | Southeast | 2m | 5 min every hour, top of hour, 24/7 | 77 | — |
| SM02 | TW07 - Zipline Tower | 39.83288, -81.73455 | Southwest | ~1.5m | 1hr at sunrise + 1hr at sunset | 12 | — |
| SM04 | TW08 - Fence w/ Vegetation | 39.82900, -81.74378 | Southwest | ~1.5m | 5 min every hour, top of hour, 24/7 | 78 | — |

### Campaign 2: August 4 – August 28, 2025

| Recorder | Site | GPS | Recording Schedule | WAV Count | Storage | Deploy | Retrieve |
|----------|------|-----|--------------------|-----------|---------|--------|----------|
| SM04 | TW02 - Nomad Ridge Shelter | 39.82957, -81.73295 | 5 min every hour | 659 | 26.06 GB | Aug 4 | Aug 28 |
| SM06 | TW05 - Lake Trail Gate O | 39.82866, -81.73758 | Sunrise to sunset (continuous) | 100 | 16.62 GB | Aug 4 | Aug 28 |
| SM05 | TW06 - Zebra Shelter | 39.82870, -81.73756 | 15 min every hour | 508 | 21.82 GB | Aug 4 | Aug 28 |
| SM02 | TW07 - Zipline Tower | 39.82891, -81.74392 | Sunrise to sunset (continuous) | 339 | 56.44 GB | Aug 4 | Aug 28 |
| SM03 | TW08 - Fence w/ Vegetation | 39.82892, -81.74392 | Sunrise to sunset (continuous) | 341 | 56.69 GB | Aug 4 | Aug 28 |
| SM01 | TW09 - Dock | 39.83418, -81.73783 | Sunrise to sunset (continuous) | 195 | 32.38 GB | Aug 14 | Aug 28 |

### Workload Impact Summary — Bioacoustics

| Config Parameter | Impact on Workload |
|------------------|--------------------|
| **5 min/hr vs 15 min/hr vs continuous** | Duty cycle directly determines data volume: 5 min/hr = 8.3% duty cycle vs continuous sunrise-sunset ≈ 50-60% |
| **Sunrise-to-sunset vs 24/7** | Continuous 24/7 recording (SM03, SM04 in C1) captures nocturnal species but 2x storage vs sunrise-sunset |
| **Deployment duration** | 3-day C1 vs 24-day C2 → ~8x more data per recorder in C2 |
| **WAV file size** | Uncompressed WAV at 48kHz stereo ≈ 33 MB/min; drives storage requirements |

---

## Co-located Sensors (Multi-Modal Overlap)

Sites where multiple sensor types were deployed simultaneously, enabling cross-modal analysis:

| Site | Camera Trap | ARU | Overlap Period | Notes |
|------|------------|-----|----------------|-------|
| TW01/TW02 - Nomad Ridge | CT01, CT02 | SM04 | Aug 4–28 | Camera + acoustic at shelter; deer corridor |
| TW05 - Lake Trail Gate O | — | SM01 (C1), SM06 (C2) | Jun 30–Jul 3, Aug 4–28 | Acoustic only; bird focus |
| TW06 - Zebra Shelter | CT04, CT05 | SM03 (C1), SM05 (C2) | Jun 30–Jul 3, Aug 4–28 | Camera + acoustic; ungulate shelter |
| TW07 - Zipline Tower | CT05 (people only) | SM02 (C1+C2) | Aug 7–11 | Camera useless (people); acoustic captures birds |
| TW08 - Fence | — | SM04 (C1), SM03 (C2) | Jun 30–Jul 3, Aug 4–28 | Acoustic only; dense vegetation |
| TW09 - Dock | CT02, CT05 | SM01 (C2) | Aug 11–28 | Camera + acoustic; waterfront activity |

---

## Drone Configurations

| Platform | Campaigns | Video Resolution | Telemetry Format | Flights |
|----------|-----------|-----------------|-----------------|---------|
| Parrot Anafi 4K | C1 (Jul 1, 3), C2 (Aug 11, 18, 25) | 4K MP4 | Parrot JSON / GUTMA DX | 11 sessions |
| DJI (unspecified) | C2 (Aug 11) | 1080p MOV | CSV (GPS + battery, 10Hz) | 1 session |
| DJI Air 2 | C3 (Sep 8) | 4K MP4 | Airdata CSV | 4 flights |
