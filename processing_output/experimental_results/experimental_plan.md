# Experimental Plan: SEC 2026 — Cross-Modal Ecological Sensing

**Paper**: "Replay in the Wild: Trace-Driven Evaluation of Multi-Modal Autonomous Sensing Systems"
**Venue**: ACM/IEEE SEC 2026 (Oct 13–16, Santa Clara)
**Abstract registration**: April 24, 2026
**Paper submission**: May 1, 2026
**Lead**: Jenna Kline
**Support**: Yuanyang, Anirudh, Chris, Tanya
**Coauthors**: Bharath, Chris, Anirudh, Tanya, others? 

---

## Modalities

| Modality | Data Volume | Timestamps | Sites | Status |
|----------|------------|------------|-------|--------|
| Camera traps | ~236K images (Campaigns 1+2) | Filename `_YYMMDDHHMMSS_` or EXIF | 13 site-camera combos | Timestamps extractable; detections not yet run |
| Bioacoustics | 1,180 hourly rows, 105 species | ISO 8601 in CSV | 6 AudioMoth sites | Complete (BirdNET) |
| Drones | 37 MP4 videos + flight logs | Airdata CSV `datetime(utc)` | Flight paths | Metadata available |
| Citizen science | 991 files | EXIF or filesystem mtime | Opportunistic | Raw only |

---

## Experiments

### Experiment 1: Cross-Modal Arrival Rate Characterization

**Research question**: How do workload arrival patterns differ across modalities, and how do they compare to single-modality characterizations from the 2024 SEC paper?

**SEC CFP fit**: Monitoring, measurements, management, and diagnosis in edge computing

**Method**:
1. Extract timestamps from all 4 modalities using `extract_wilds_multimodal.py`
2. Apply ADAE methodology (`change_points.py`): detect change points in cumulative arrival distributions at thresholds [0.8, 0.95, 0.99, 0.995]
3. Fit time-varying Poisson processes per modality
4. Compute per-modality statistics: total events, mean arrival rate, coefficient of variation (CV), burstiness parameter B = (CV−1)/(CV+1)
5. Compare across modalities

**Data inputs**:
- Camera traps: ~236K timestamps from filenames/EXIF (no detection needed)
- Bioacoustics: `WildsBird_Every_Hour.csv` — 1,180 rows with `total_birds` counts
- Drones: Airdata CSVs — flight start/end times
- Citizen science: filesystem timestamps or EXIF from JPEG files

**Outputs**:
- Summary table: modality, total_events, date_range, mean_rate, CV, burstiness, num_sites
- Overlaid cumulative arrival rate figure (like 2024 paper Fig 3, with 4 modality curves)
- Per-modality change point CSVs and Poisson model parameters

**Owner**: Jenna
**Timeline**: Weeks 1–2

---

### Experiment 2: Cross-Modal Event Correlation

**Research question**: When one modality detects an event at a site, how often does another modality detect a concurrent event at the same site?

**SEC CFP fit**: Geo-distributed analytics and indexing on edge nodes

**Method**:
1. Identify co-located sensors by matching site prefix (TW##):
   - TW02: CT01 + SM04
   - TW06: CT04/CT05 + SM05
   - TW07: CT05 + SM02
   - TW09: CT02/CT05 + SM01
2. Bin events into time windows (1h, 6h, 24h)
3. For each site and window: compute binary presence/absence per modality per bin
4. Compute Jaccard similarity: |bins with both modalities active| / |bins with either active|
5. Build 4×4 cross-modal correlation matrix

**Outputs**:
- Cross-modal correlation matrices for each time window
- Heatmap visualization
- Per-site breakdown showing which modality pairs have strongest co-occurrence

**Owner**: Anirudh
**Timeline**: Weeks 2–3

---

### Experiment 3: Edge Resource Model

**Research question**: Can a single mobile edge node handle concurrent multi-modal inference under SLO constraints? At what arrival rate does it need to prioritize or shed load?

**SEC CFP fit**: Resource management, scalability, and reliability for edge computing

**Method**:
1. Collect published inference benchmarks per model:
   - BirdNET: ~0.1s per 3s audio clip (CPU)
   - YOLO+SAHI: ~0.3–2s per image (GPU-dependent)
   - BioCLIP: ~0.5s per crop (GPU)
   - MegaDetector: ~0.2s per image (GPU)
2. Combine with measured arrival rates from Experiment 1 to compute required throughput per modality
3. Model aggregate workload: what happens when all modalities fire simultaneously?
4. Compare 3 scheduling policies:
   - **Process-all**: every event gets full inference
   - **Priority-based**: camera traps get detection only; acoustics batch-processed; drones real-time
   - **Adaptive**: trigger secondary modality processing only when primary modality detects an animal

**Optional enhancement (master's student)**:
- Profile BirdNET, YOLO+SAHI, BioCLIP on the actual ruggedized field laptop
- Measure wall-clock time, GPU/CPU utilization, memory per model
- Start with small subset (~100 images, ~10 audio clips), then scale

**Outputs**:
- Table: model, published_latency, arrival_rate, required_throughput, single_node_feasibility
- Gap analysis: which modality combinations exceed edge capacity
- Policy comparison table

**Owner**: Anirudh and Yuanguang (profiling)
**Timeline**: Weeks 3–4

---

### Experiment 4: Replay-Based Policy Comparison

**Research question**: How do different sensing policies perform when replayed on identical real-world traces?

**SEC CFP fit**: AI-driven self-evolving software at the edge

**Method**:
1. Use Campaign 2 traces (Aug 4–28, 24-day deployment) as replay input
2. Implement 3 policies:
   - **Baseline (process-all)**: every sensor event triggers immediate inference
   - **Event-triggered**: only motion-triggered camera trap images and high-confidence acoustic detections (confidence > 0.7) get full inference; timelapse images skipped
   - **Adaptive**: start with event-triggered; if detection rate in a 1-hour window exceeds threshold, increase processing; if idle for >2 hours, batch-process backlog
3. Replay identical traces through each policy
4. Measure per-policy: SLO compliance (latency P95, coverage %), compute budget consumed, operator effort

**Outputs**:
- Comparison table (3 policies × 4 SLO metrics)
- Timeline visualization showing policy behavior over 24 days

**Owner**: Anirudh, Yuanyang
**Timeline**: Weeks 4–5

---

### Experiment 5: Storage Savings from Edge Blank Image Filtering

**Research question**: What fraction of camera trap images are blank, and how does edge filtering change the effective workload and hardware requirements?

**SEC CFP fit**: Storage and data management technologies for edge computing

**Method**:
1. Compute total raw data volume per camera per day across all campaigns
2. Run object detection (MegaDetector/YOLO) on all camera trap images to classify blank vs. non-blank
3. Compute:
   - % blank images per camera, per campaign, overall
   - Total storage (GB) raw vs. filtered
   - Raw arrival rate vs. true-positive arrival rate (events with animals / time)
4. Profile hardware requirements:
   - Throughput needed to process ALL images at raw arrival rate
   - Throughput needed to process only true positives (post-filtering)
   - Show that true-positive-only processing is feasible on much cheaper hardware

**Key insight**: If 60–80% of camera trap images are blank (consistent with literature — Orinoquia dataset was 20%+ blank), then edge filtering reduces the downstream inference throughput requirement by 3–5×. This means richer models (BioCLIP species classification) become feasible within SLO constraints.

**Outputs**:
- Table: camera, total_images, blank_count, blank_pct, raw_rate_per_hour, tp_rate_per_hour
- Storage savings figure (raw vs filtered GB)
- Hardware requirement comparison (raw vs true-positive throughput)

**Owner**: Anirudh (running detections and analysis)
**Timeline**: Weeks 3–5 (detection runs can be parallelized on cluster)

**Dependency**: Requires running the camera trap detection pipeline on ~236K images. The pipeline exists at `documentation/annotation_pipeline/camera_traps/imageomicsthewilds_cameratraps/src/` (YOLO+SAHI+BioCLIP). Can use Campaign 1 (~15K images) as proof of concept first.


---

### Experiment 6: Stress Testing via Synthetic Trace Modification

**Research question**: How does SLO compliance degrade as workload burstiness increases?

**SEC CFP fit**: Edge computing infrastructure and its sustainability

**Method**:
1. Use Poisson models from Experiment 1 as baseline
2. Scale arrival rates by 2×, 5×, 10× to simulate denser deployments or more active wildlife periods
3. Replay synthetic traces through the edge resource model from Experiment 3
4. Measure SLO compliance at each scale factor
5. Identify the breaking point for each policy

**Outputs**:
- SLO compliance curves vs. burstiness scaling factor (one per policy)
- Breaking point analysis: at what scale does each policy fail to meet SLOs?

**Owner**: Jenna
**Timeline**: Weeks 5–6

---

## Timeline

| Week | Dates | Milestones |
|------|-------|------------|
| 1 | Mar 17–23 | `extract_wilds_multimodal.py` complete. Camera trap + bioacoustic timestamps extracted. |
| 2 | Mar 24–30 | All 4 modalities extracted. **Experiment 1** (arrival rates) complete. |
| 3 | Mar 31–Apr 6 | **Experiment 2** (correlation) complete. **Experiment 3** (resource model) started. Camera trap detection runs started for Exp 5. |
| 4 | Apr 7–13 | **Experiments 3, 4** (resource model, replay policies) complete. |
| 5 | Apr 14–20 | **Experiments 5, 6** complete. All figures generated. Paper draft updated with results. |
| 5 | **Apr 24** | **Abstract registration deadline** |
| 6 | Apr 21–May 1 | Paper writing, revision, internal review, submission. |
| | **May 1** | **Paper submission deadline** |

## Dependencies

```
Experiment 1 ──→ Experiment 2 (needs timestamps)
Experiment 1 ──→ Experiment 4 (needs traces)
Experiment 1 ──→ Experiment 6 (needs Poisson models)
Experiment 3 can run in parallel (uses published benchmarks)
Experiment 5 requires camera trap detection runs (can start early, parallelizable)
```

## Yuanyang Onboarding Path

1. **Week 1**: Run BirdNET, YOLO+SAHI, BioCLIP on small subset (~100 images, ~10 audio clips). Measure wall-clock time, GPU/CPU utilization, memory.
2. **Week 2**: Profile systematically on ruggedized laptop — vary batch size, measure throughput and latency per model.
3. **Week 3**: Run camera trap detection pipeline on Campaign 1 (~15K images) — produces both profiling data and annotation outputs.
4. **Week 4+**: Help run detections on Campaign 2 (~220K images); assist with replay framework.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Camera trap EXIF extraction slow at 236K images | Delays Exp 1 | Extract from filenames first (faster); EXIF as fallback only. Cache results. |
| TW02-CT01 timestamp corrections incomplete | Bad arrival rate data | Corrections in `camera_deployment_metadata.py` cover known bad dates; flag any remaining outliers |
| Citizen science timestamps unreliable (mtime vs capture time) | Weak Exp 2 correlation | Try EXIF from JPEG/HEIC first; note limitation in paper |
| Camera trap detections not run in time for Exp 5 | Missing storage analysis | Run on Campaign 1 first (15K images, fast); use as proof of concept; extrapolate to full dataset |
| Yuanyang not onboarded in time for profiling | No measured benchmarks | Use published benchmarks; clearly state in paper |
