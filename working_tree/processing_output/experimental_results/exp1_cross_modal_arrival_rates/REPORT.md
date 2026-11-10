# Cross-Modal Arrival Rates — Results Report

**Analysis date:** 2026-04-10
**Pipeline:** ADAE methodology (SEC '24), applied to TheWilds2025 multi-modal detections
**Source script:** [extract_wilds_multimodal.py](../../../documentation/adae_model/extract_wilds_multimodal.py)
**Results:** [results/](results/)

## 1. Overview

We extracted per-event timestamps from four sensing modalities at The Wilds and applied the ADAE change-point / time-varying Poisson framework to characterize the temporal structure of detection events. The goal is to quantify how bursty and how correlated each modality's event stream is — inputs to both the SEC 2026 workload characterization and the MEE fusion paper.

## 2. Per-modality summary

From [summary_table.csv](results/summary_table.csv):

| Modality | Total events | Date range | Mean rate (events/hr) | CV | Burstiness B | # Sites |
|---|---:|---|---:|---:|---:|---:|
| Camera trap | 235,596 | 2023-10-31 → 2025-09-14 | 7.00 | 301.70 | **0.9934** | 6 |
| Citizen science | 991 | 2025-06-30 → 2025-09-08 | 0.58 | 16.94 | 0.8885 | 1 |
| Bioacoustic (BirdNET) | 1,180 | 2025-06-30 → 2025-08-28 | 0.46 | 13.71 | 0.8640 | 2 |
| Drone | **302,894** | 2025-07-01 → 2025-09-08 | **TBD** | **TBD** | **TBD** | 14 missions / 6 days |

Burstiness B = (CV − 1) / (CV + 1); B → 1 is maximally bursty, B = 0 is Poisson, B < 0 is regular.

**Key observations:**

- **All three statistically-analyzed modalities are extremely bursty** (B ≥ 0.86). None are well-described by a homogeneous Poisson process. Workload models built on a constant-rate assumption will badly under-provision peak demand and over-provision mean demand.
- **Camera traps dominate volume by >200×** (235k vs ~1k for the others) and are the burstiest modality (B ≈ 0.993, CV ≈ 302). This is consistent with motion-triggered arrays that sit idle for long periods then fire rapid bursts during animal visits — the dominant driver of edge compute demand for the SEC paper.
- **Bioacoustic and citizen science sit in a similar burstiness band** (B ≈ 0.86–0.89), but for different reasons: BirdNET is diurnally/seasonally concentrated (dawn chorus, migration), while citizen science tracks visitor activity.
- **Drone is now a major modality** — 302,894 per-frame SAM3 detections across 14 missions on 6 days (Jul 1, Jul 3, Aug 11, Aug 18, Aug 25, Sep 8). Source: `processing_output/detections/drones/*_detections.csv`. One mission (`20250811_parrot_01`, 25,806 rows) is excluded because neither per-frame timestamps nor a known start time exist for reconstruction. One mission (`20250811_DJI_01`, 17,133 rows) has timestamps reconstructed from ExportCSV filename + frame/30fps; see Darwin Core `fieldNotes` for provenance. Different drone missions may require different SLOs — per-frame detection events represent the SAM3 inference workload but not necessarily the ecologically-meaningful event count. A mission-level or track-level aggregation will be discussed separately.
- **Temporal coverage is uneven.** Only camera traps span multiple seasons (earliest timestamps from 2023 are a known clock-drift artifact on TW01-CT02 — see §6). All modalities share a summer 2025 window. Cross-modal comparisons should be restricted to the **2025-07-01 → 2025-08-28** overlap window to avoid biasing CV/burstiness by coverage asymmetry.

## 3. Change-point structure

Change points were computed at cumulative-arrival thresholds [0.8, 0.95, 0.99, 0.995]. Counts per modality (see [results/change_points_*.csv](results/)):

| Modality | # change points (all thresholds) |
|---|---:|
| Camera trap | 19,581 |
| Bioacoustic | 13 |
| Citizen science | 1 |

The change-point counts are **identical across all four thresholds** for every modality. This means the ADAE detector is finding the same set of rate breakpoints regardless of how strictly we set the cumulative-arrival threshold — i.e., the modalities' cumulative distributions are either step-like (camera trap) or nearly linear with a handful of inflections (bioacoustic), so the threshold sweep does not add information here. **Recommend dropping the threshold sweep** in future runs or replacing it with a sensitivity analysis on a different parameter (minimum segment length, penalty term).

Camera-trap change points (~19.5k) reflect the fine-grained burst structure — roughly one rate regime shift per ~12 events. Bioacoustic has only 13 segments over two months, meaning BirdNET detections arrive in ~weekly "regimes" that the model flags as distinct Poisson rates (likely dawn-chorus windows and weather-driven quiet periods). Citizen science has a single change point: effectively one low-rate regime with negligible structure.

## 4. Cross-modal correlation

Pearson correlation between hourly-binned event counts, at three bin widths ([results/cross_modal_correlation_{1h,6h,24h}.csv](results/)):

| Bin | Bioacoustic ↔ Camera trap |
|---|---:|
| 1 h | 0.390 |
| 6 h | 0.615 |
| 24 h | 0.690 |

Only the bioacoustic–camera trap pair was computed in the initial run (citizen science and drone were excluded). **With the corrected drone extraction (302k events), drone should now be included in the correlation matrix.** Results below are from the initial run; re-run pending.

**Interpretation.** Correlation rises monotonically with bin width, which is the expected signature of two processes that share a coarse diurnal/seasonal envelope but desynchronize at fine timescales. At the hour level, camera-trap and bioacoustic events are only weakly coupled (r ≈ 0.39) — animals trigger cameras and birds vocalize on different minute-to-minute schedules. At the day level they largely track each other (r ≈ 0.69), reflecting shared drivers (weather, season, site activity). **For fusion (MEE paper), this supports using one modality to *prime* the other over multi-hour windows but not as a near-real-time trigger.** For the SEC paper, the low hourly correlation means camera-trap and acoustic workloads can be treated as approximately independent arrival streams at the edge-scheduling timescale.

Heatmaps of the correlation matrices are in [cross_modal_heatmap_1h.png](results/cross_modal_heatmap_1h.png), [cross_modal_heatmap_6h.png](results/cross_modal_heatmap_6h.png), [cross_modal_heatmap_24h.png](results/cross_modal_heatmap_24h.png).

## 5. Visualizations

- [overlaid_arrival_rates.png](results/overlaid_arrival_rates.png) — cumulative arrivals, all modalities on one axis
- [cross_modal_heatmap_24h.png](results/cross_modal_heatmap_24h.png) — daily-bin correlation matrix

## 6. Caveats and follow-ups

1. **Camera-trap 2023 timestamps.** 15 rows from TW01-CT02 carry 2023-10-31 timestamps due to an uncorrected camera clock drift. The correction table in `camera_deployment_metadata.py` covers TW02-CT01 (13,689 corrected rows) but not TW01-CT02. Fix: add a `timestamp_corrections` entry for TW01-CT02 mapping `(2023, 10, 31) → (2025, 8, 4)`. Also fix the duplicate `"TW01-CT02"` key in `DEPLOYMENTS` (the June campaign entry is silently clobbered by the August one).
2. **Drone event granularity.** The 302k drone rows are per-frame SAM3 bounding boxes — the inference workload unit (SEC paper). For the MEE ecology paper, this massively overweights drone vs. the ~1k bioacoustic/citizen-science events. A mission-level or track-level aggregation is needed; different missions may also require different SLOs.
3. **20250811_DJI_01 timestamps reconstructed.** Per-frame datetimes were computed as `start_time + frame/30fps`. No inter-video gap modeled; altitude unavailable. See Darwin Core `fieldNotes` for full provenance.
4. **20250811_parrot_01 excluded.** 25,806 detections with no per-frame timestamps and no known mission start time. Needs flight log recovery or manual timestamp anchoring.
5. **3 Aug-25 missions have no video data.** Detection CSVs exist only for `20250825_parrot_01`. The SD card for flights `_02`, `_03`, `_04` was lost, so no video was available for SAM3 processing. Flight telemetry metadata exists but cannot produce detections.
6. **Citizen science = 1 site, 1 change point.** Low volume (991 events) limits statistical conclusions.
7. **Change-point threshold sweep is degenerate** for this dataset (identical output at all four thresholds). Drop or replace with a penalty sensitivity analysis.
8. **Per-site decomposition not yet done.** Camera trap spans 6 sites; the aggregate B ≈ 0.993 may be inflated by cross-site heterogeneity. Per-site burstiness needed for the SEC workload model.
9. **Re-run needed.** The extractor has been updated to read drone detections from `processing_output/detections/drones/`. Summary statistics, change points, correlations, and plots need to be regenerated via `submit_arrival_rates.sh`.
