# Reproducibility

What this repository can regenerate, what it cannot, and why. Verified
2026-09-06 against the camera-ready.

## Status by paper artifact

| Paper artifact | Script | Status |
|---|---|---|
| Table II — arrival statistics | `01_characterize/export_primitives.py` | ⚠️ Shipped as `data/primitives/`. Re-deriving needs the field archive. |
| Identity synthesis (§VI-A.4) | `02_synthesize/synthesize.py` | ✅ Reproduces recorded counts within 0.1–4.3% |
| CS1–CS4 traces (§VI-B) | `03_case_studies/generate_traces.py` | ✅ Bit-identical to the originals |
| Fig. 3 — topology scaling | `04_fidelity/topology_scaling.py` → `figures/fig_05` | ⚠️ Needs recorded timestamp tables |
| App. Fig. 3 — variance envelope | `04_fidelity/variance_envelope.py` → `figures/fig_app_03` | ✅ Runs from primitives + synthesis |
| App. Fig. 4 — intensity sweep | `figures/fig_app_04` | ⚠️ Needs `generalization_sweep_l2.json` (not shipped) |
| Fig. 7 — feasibility grid | `figures/fig_07` | ✅ Renders from `data/paper_results/master_feasibility.csv` |
| Fig. 5 — policy Pareto | `figures/fig_08` | ✅ Renders from `data/paper_results/exp4_policy_metrics.csv` |
| §VI-A.2 — operational fidelity | — | ❌ Not included (see below) |
| §VI-A.3 — field-tier calibration | — | ⚠️ Result shipped in `master_feasibility.csv`; raw benchmark run not included |
| §V-C — post-filter throughput | — | ⚠️ Reconstructable from dataset-side artifacts; **one printed claim is refuted** (see below) |

Verified identity synthesis:

| Modality | Synthesized | Recorded | Ratio |
|---|---:|---:|---:|
| Camera traps | 189,118 | 189,289 | 0.999 |
| Bioacoustic | 1,537 | 1,570 | 0.979 |
| Drones | 98,448 | 98,335 | 1.001 |
| Citizen science | 145 | 139 | 1.043 |

`CS2_acoustic_to_ct_1x` → 395,894 events (394,412 CT, 1,482 bio) and
`CS4_citsci_system_1x` → 362,069 events, both matching the original traces
exactly.


## Figure provenance

Where each figure in the paper comes from, end to end.

| Figure | Plot script | Input file | Produced by |
|---|---|---|---|
| Fig. 3 — topology scaling | `figures/fig_05_topology_scaling.py` | `topology_scaling.csv` | `04_fidelity/topology_scaling.py` |
| Fig. 5 — policy Pareto | `figures/fig_08_pareto_policies.py` | `exp4_policy_metrics.csv` | external Exp 4 replay engine |
| Fig. 7 — feasibility grid | `figures/fig_07_feasibility_grid.py` | `master_feasibility.csv` | `05_feasibility/build_master_feasibility.py` |
| App. Fig. 3 — variance envelope | `figures/fig_app_03_variance_envelope.py` | `variance_envelope.csv` / `.json` | `04_fidelity/variance_envelope.py` |
| App. Fig. 4 — intensity sweep | `figures/fig_app_04_intensity_sweep.py` | `generalization_sweep_l2.json` | `04_fidelity/generalization_sweep.py` |

All five input files are shipped in `data/paper_results/`, so every figure
renders from a clean checkout:

```bash
for f in scripts/figures/fig_*.py; do python3 "$f"; done
```

Rendered output matches the published PNGs to within 0.8% in file size — font
and matplotlib-version rendering noise, not content.

`build_master_feasibility.py` is the step that merges the field-laptop
calibration into the grid and applies the CS1/CS2 label remap; it consumes
`05_feasibility/prediction_model.py` output plus the calibration result.
`exp4_policy_metrics.csv` is the one input this repository cannot regenerate —
see gap 2 below.

## Known gaps

### 1. §V-C rests on the dataset side, and one claim there is wrong

The blank-frame filtering experiment ("Exp 5") has no code in this tree, but its
inputs are recoverable: the camera-trap detection summary
(`detections/camera_traps/all_images_summary.csv`, 5,834 detection-positive
images) and the raw image count (235,778 JPGs across 13 deployments, recorded in
the SmartWilds dataset card). Those two numbers
reproduce four of the five printed values:

| Printed | Reconstruction | Result |
|---|---|---|
| 97.5% blank rate | `1 − 5834/235778` | 97.526% |
| 40.5× reduction | `235778/5834` | 40.41× |
| φ_CT^raw 78.6 /h | `235778 / ~3000 camera-hours` | 78.59 |
| φ_CT^thr 1.94 /h | `5834 / ~3000 camera-hours` | 1.945 |

Both throughput figures imply the same denominator — 3000.1 h from φ^raw and
3007.2 h from φ^thr — i.e. roughly 3,000 **camera-hours** aggregated across
deployments, not a wall-clock horizon. (96.88% storage saving was not
recomputed.)

**The subset claim does not hold.** §V-C states that of the 154.5 events/h in
Table II, 78.6 events/h are still images entering the detection pipeline and the
remainder are video triggers. But 78.6 is 235,778 images over ~3,000
camera-hours across all 13 deployments in both campaigns, while 154.5 is 189,289
events over the pooled 5-site campaign-2 stream via reciprocal-mean-IAT. The
numerator of the "subset" (235,778) is *larger* than the numerator of the
supposed whole (189,289). The 154.5/78.6 ≈ 1.966 ratio is a coincidence of two
unrelated quantities. The §V-C sentence and the Table II caption clause both
need revising.

These inputs belong to the companion dataset paper, not to this repository —
they are documented here only because §V-C depends on them.

### 2. Operational fidelity depends on an external replay engine

The Exp 4 replay pipeline and the recorded "strict" camera trace (39,742
events) live outside this repository, in a collaborator's home directory on the
cluster. Fig. 5 still *renders*, because the policy metrics it plots are shipped
in `data/paper_results/exp4_policy_metrics.csv` — but those metrics cannot be
*recomputed* here, and neither can the rest of §VI-A.2 (Kendall τ, p95 ratios,
per-event energy).

Note also that the recorded trace covers **3 camera sites**, while Table II and
the synthesized traces cover **5**. The 4.76× event-count ratio between them is
accounted for by site coverage plus burst grouping (multiple images per event),
not by a difference in the underlying detections — site TW09 appears in both at
exactly 90,834 images.

### 3. Independence bounds are assumed, not read

See `data/README.md`. Synthesis assumes full cross-modal independence when the
Exp 2 correlation matrices are absent, which they are. This matches the paper's
finding F2 (all pairwise C < 0.05 at 1 h), but it is an assumption made by the
code rather than a measurement it loads.

### 4. Benchmark latencies are mostly planning estimates

The feasibility grid is calibrated: `data/paper_results/master_feasibility.csv`
carries `measured`, `measured_p95_ms` and `calibration_gap_pct`, with one row
set — CS2 / adaptive / field_laptop, measured 14,135.1 ms against 11,453.37
predicted, a 23.41% gap. (An upstream intermediate,
`predicted_feasibility_grid.csv`, has `measured = False` throughout; that is
expected — `build_master_feasibility.py` is what adds the calibration.)

**Case-study labels are remapped.** Internal harness labels for CS1 and CS2 are
inverted relative to the manuscript; the remap happens in
`build_master_feasibility.py` and both columns are retained in the CSV. So
`case_study = CS2, case_study_internal = CS1` is correct, not a mislabelling.
Published SLOs: CS1 2 s, CS2 5 s, CS3 10 s, CS4 60 s.

What to be careful about is the *unmeasured* cells. Of the 25 (model, tier) rows
in `05_feasibility/benchmark_table.csv`, exactly one derives from a local
measurement — and that one ran on an A100 while filed under the
`workstation_rtx` tier. Twelve rows say "provisional" in their own notes, and
two cite a product-marketing aggregator page for Pi5+Coral latencies feeding
`megadetector`, one of the grid's three bottleneck models.
`model_benchmark_notes.md` carries per-row provenance. Treat all non-measured
latencies as planning estimates with at least the ±25% band the paper states —
noting that the one drone measurement came in at −82.5%, because it anchored on
YOLOv8n against a yolo_sahi prediction and so never paid the SAHI tiling cost.

## A failure mode worth knowing

`synthesize.py` routes bioacoustic and citizen science through a timestamp
bootstrap that reads `data/timestamps/timestamps_<modality>.csv`. **If those
files are missing it returns zero events silently** — logged at INFO, not as an
error. Synthesis then "succeeds" while emitting nothing for those two
modalities, and a multi-modal trace quietly becomes camera-trap-and-drone only.

Both files are committed, so this should not arise. If you see a modality
missing from a generated trace, check for it first:

```bash
python3 scripts/00_prepare/make_event_tables.py --combined /path/to/timestamps_combined.csv
```

Camera trap and drone are unaffected — they synthesize from the change-point
rate model in the primitives.
