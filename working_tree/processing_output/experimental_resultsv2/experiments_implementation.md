# MOSAIC v2 — Experiments Implementation Plan

**Purpose.** Bridge from v1 code (`processing_output/experimental_results/`) to v2 experiments defined in [mosaic_execution_plan_v2.md](mosaic_execution_plan_v2.md). Inventories what is reused, what is new, and where new files live. Companion to the execution plan (which owns specs, owners, and dates) and the paper outline [experiment_planv2.md](experiment_planv2.md).

**Branch.** `experiments-v2` (new). All new scripts land on this branch.

**v2.1 scope pivot (2026-04-23).** No Jetson/Pi hardware accessible. Exp 3 pivots to **prediction-only** across all edge tiers using published benchmarks; Exp 3.5 promoted from stretch to required as the field-laptop measurement anchor. Paper framing shifts: synthesis methodology is the primary contribution, hardware is illustrative (SmartWilds v2 BoM). See execution plan §"Key changes in v2.1" for details.

**Target layout.** Each v2 experiment gets a subdirectory under `processing_output/experimental_resultsv2/`:

```
experimental_resultsv2/
├── experiment_planv2.md           # paper outline (existing)
├── mosaic_execution_plan_v2.md    # execution plan (existing)
├── experiments_implementation.md  # this file
├── exp1_characterization/         # reuses v1 exp1 + new site-variance output
├── exp2a_independence/            # reuses v1 exp2 (write-up only)
├── exp2b_marginal_value/          # NEW
├── exp3_hardware_feasibility/     # restructures v1 ex3
├── exp3_5_calibration/            # NEW (stretch)
├── exp4_policy_comparison/        # extends v1 ex4 (+energy, +synthesized)
├── exp5_edge_filtering/           # reuses v1 exp5 (write-up only)
├── exp6_1_synthesis/              # NEW (core methodology)
├── exp6_2a_trace_fidelity/        # NEW
├── exp6_2b_replay_fidelity/       # NEW
├── exp6_3_case_studies/           # NEW
└── exp6_4_scaling/                # NEW
```

---

## 1. v1 Script Reuse Matrix

| v2 experiment | v1 source | Action |
|---|---|---|
| Exp 1 characterization | `experimental_results/exp1_cross_modal_arrival_rates/` — `submit_arrival_rates.sh`, plus `documentation/adae_model/extract_wilds_multimodal.py` and `change_points.py` | **Reuse**; add per-site-variance export (new script) |
| Exp 2.A independence | `experimental_results/exp2_cross_modal_event_correlation/` (1h, 6h, 24h Jaccard outputs) | **Reuse as-is**; write-up only |
| Exp 3 predicted hardware feasibility | `experimental_results/ex3_exp4/exp3_code/` — `build_drone_arrival_summary.py`, `build_exp3_strict_tables.py`, `plot_exp3_strict_aggregate.py`, `path_config.py` | **Restructure** into *predicted* hardware × workload × policy grid from published benchmarks (v2.1 pivot — no device access) |
| Exp 3.5 field-laptop anchor | — | **New**; single measured tier calibrating predicted grid |
| Exp 4 policy comparison | `experimental_results/ex3_exp4/exp4_code/` — `replay_engine.py`, `policies.py`, `evaluate_replay.py`, `plot_replay_timeline.py`, `build_exp4_camera_strict_trace.py`, `build_exp4_strict_summary.py` | **Extend**: add energy metric, control-theoretic policy, synthesized-workload inputs |
| Exp 5 edge filtering | `experimental_results/exp5_storage_analysis/` — `analyze_blank_image_filtering.py`, `run_storage_analysis.sh`, `src/storage_analysis/` | **Reuse as-is**; write-up only |
| Exp 6.1 synthesis | — | **New**; consumes Exp 1 JSON primitives + Exp 2.A bounds |
| Exp 6.2.A trace fidelity | — | **New** |
| Exp 6.2.B replay fidelity | — | **New**; wraps extended `replay_engine.py` from Exp 4 |
| Exp 6.3 case studies | — | **New**; recipes as Python modules |
| Exp 6.4 scaling | — | **New**; wraps Exp 3 + Exp 4 at 2×/5×/10× intensity |

**Copy strategy.** Do not duplicate v1 code into v2. Import or symlink from `experimental_resultsv2/exp*/` using relative paths. Keep v1 tree intact as ground truth for Campaign 2 results.

---

## 2. Experiments Reusing v1 (minor new work)

### Exp 1 — Per-modality characterization (Jenna, Day 1)

**Reuse.** `extract_wilds_multimodal.py`, `change_points.py`, existing `submit_arrival_rates.sh`.

**New.** One script:

- `exp1_characterization/export_primitives.py`
  - Input: existing v1 outputs + recorded traces per modality
  - Output: one JSON per modality at `exp1_characterization/primitives/{camera,acoustic,drone,citsci}.json` with fields:
    - `rate_model` (time-varying Poisson λ(t) with change points at [0.8, 0.95, 0.99, 0.995])
    - `burstiness_B`, `cv`
    - `diurnal_profile` (24-element hour-of-day rate vector)
    - `per_site_variance`: list of `{site, B, CV, diurnal_ks_vs_modality_mean}` → **this is the input to variance envelope in 6.2.A**
  - Must be deterministic; include seed in output metadata

**Table IV** (paper §V.A) is generated from these JSONs.

### Exp 2.A — Cross-modal independence (Jenna, Day 1)

**Reuse entirely.** v1 outputs at `experimental_results/exp2_cross_modal_event_correlation/{1h,6h,24h}/` are final.

**New.** None. Paper §V.B text references existing outputs. Figure 6 heatmaps use existing CSVs.

### Exp 5 — Edge filtering (Jenna, Day 1)

**Reuse entirely.** `analyze_blank_image_filtering.py` outputs at `experimental_results/exp5_storage_analysis/results/` are final (97.5% blank rate, 40.5× throughput reduction).

**New.** None. Paper §V.D and Table VII from existing outputs.

---

## 3. Experiments Extending v1 (new work required)

### Exp 3 — Predicted hardware tier feasibility (Anirudh, Day 7)

**Scope pivot (v2.1).** No device access. Prediction-only across all edge tiers from published benchmarks. Hardware claims in the paper carry "(predicted)" qualifier except the laptop tier (measured in Exp 3.5).

**Reuse.** `exp3_code/build_drone_arrival_summary.py`, `build_exp3_strict_tables.py`, `path_config.py` (adapt paths).

**New files.**

- `exp3_hardware_feasibility/benchmark_table.py`
  - Compiles published inference latency + device TDP + memory for {BirdNET, YOLO+SAHI, SAM3, BioCLIP, MegaDetector} × {RTX workstation, Jetson Orin Nano, Pi 5 + Coral TPU, Pi 4 CPU, field laptop}
  - One source cited per cell (model card, paper, manufacturer spec)
  - Output: `benchmark_table.csv` with columns `(model, tier, latency_ms, power_W, memory_MB, source_url, notes)`
- `exp3_hardware_feasibility/prediction_model.py`
  - Input: synthesized workloads from Exp 6.3, benchmark table, policy under test
  - For each (tier × workload × policy) cell computes: predicted aggregate utilization %, predicted P95 latency vs SLO, predicted bottleneck modality, predicted feasibility verdict (`feasible/degraded/infeasible`)
  - Output: `results/predicted_feasibility_grid.csv` and `results/predicted_feasibility_heatmap.pdf` (Table V, Figure 10 input)
- `exp3_hardware_feasibility/run_predictions.sh` — orchestrates prediction runs across all cells (no device required)

### Exp 4 — Policy comparison + energy + synthesized workloads (Yuanyang, Day 8)

**Reuse.** `exp4_code/replay_engine.py`, `policies.py`, `evaluate_replay.py`, `plot_replay_timeline.py`. Adapt `path_config.py`.

**New files.**

- `exp4_policy_comparison/energy_model.py`
  - `E_event = latency_stage × device_power_stage` summed across inference stages
  - Per-device power numbers loaded from `exp3_hardware_feasibility/hardware_tiers.py`
- `exp4_policy_comparison/control_theoretic_policy.py`
  - Yuanyang's Lyapunov-based policy. Implements `Policy` interface from v1 `policies.py`
  - Standalone testable with identity recipe before plugging in
- `exp4_policy_comparison/pareto_analysis.py`
  - Input: per-policy × per-workload replay results (latency, energy, coverage, compute budget)
  - Output: Pareto front per workload as CSV + per-axis-pair figures (`results/pareto_{workload}.pdf`)
- `exp4_policy_comparison/run_all_policies.sh` — runs 4 policies × N synthesized workloads

---

## 4. Experiments Entirely New

### Exp 6.1 — Synthesis procedure (Jenna, Day 3 — GATE)

**New files.**

- `exp6_1_synthesis/synthesize.py`
  - Core API: `synthesize(recipe: Recipe, primitives: dict, independence_bounds: dict, seed: int) → EventLog`
  - Deterministic given seed
  - Produces unified event log with same schema as recorded traces (compatible with v1 `replay_engine.py`)
- `exp6_1_synthesis/combinators.py`
  - Four combinators: `concatenate`, `interleave`, `conditional_scale`, `prior_inject`
  - Each takes per-modality event streams + recipe params → combined stream
- `exp6_1_synthesis/schemas.py`
  - `Recipe` dataclass (modality mix, density, intensity, combinator choice, SLO chain)
  - `EventLog` schema matching v1 trace format from `build_exp4_camera_strict_trace.py`
- `exp6_1_synthesis/identity_test.py`
  - Sanity test: `synthesize(identity_recipe, full_primitives) ≈ recorded trace` within tight tolerance on B, CV, diurnal KS
  - Must pass end-of-Day-3 before handoff

### Exp 6.2.A — Trace-level fidelity (Jenna, Day 5)

**New files.**

- `exp6_2a_trace_fidelity/variance_envelope.py`
  - Natural variance: per-site distributions of B, CV, diurnal KS from Exp 1 JSON
  - Synthesis variance: N-seed synthesis on fixed recipe, same metrics
  - Output: paired-plot data + Figure 8 (paper §VI.A.1 headline)
- `exp6_2a_trace_fidelity/leave_one_site_out.py`
  - For each modality with ≥3 sites: hold one out, synthesize from rest, compare on 5 fidelity metrics (thresholds in execution plan §Exp 6.2.A table)
  - Output: pass/fail table per fold per metric
- `exp6_2a_trace_fidelity/fidelity_metrics.py`
  - Shared metric implementations: burstiness preservation, CV preservation, diurnal KS, independence preservation, post-filter rate
  - Reused by 6.2.B and 6.4

### Exp 6.2.B — Replay-level fidelity (Jenna, Day 6)

**New files.**

- `exp6_2b_replay_fidelity/replay_fidelity.py`
  - For each policy: run on recorded trace vs. synthesized-identity trace; compare queue depth distribution (KS ≤ 0.15), latency distribution (P95 ratio within 15%, KS ≤ 0.15), SLO compliance (≤ 5 pp absolute diff)
- `exp6_2b_replay_fidelity/policy_ranking_invariance.py`
  - Across all 4 policies, Kendall's tau between (ranking on recorded) and (ranking on synthesized) for each metric
  - Output: Figure 11 (optional), headline number in paper §VI.A.3
- `exp6_2b_replay_fidelity/generalization_sweep.py`
  - Runs fidelity at generalization levels 0 (identity), 1 (cross-site recombination), 2 (+intensity), 3 (+modality mix)
  - Output: fidelity-vs-generalization curve → **Figure 9, methodology headline figure**

### Exp 6.3 — Case study library (Jenna, Day 4 — GATE)

**New files.**

- `exp6_3_case_studies/recipes/cs1_ct_to_drone.py` — CT motion-trigger bursts concatenated with drone response windows; 5s SLO
- `exp6_3_case_studies/recipes/cs2_acoustic_to_ct.py` — BirdNET high-confidence interleaved with CT sensitivity-raised windows; 2s SLO
- `exp6_3_case_studies/recipes/cs3_focal_ct_network.py` — multi-site CT with corridor-movement conditional_scale; 10s SLO
- `exp6_3_case_studies/recipes/cs4_citsci_system.py` — citsci events as prior_inject across all modalities; 60s SLO
- `exp6_3_case_studies/base_recipe.py` — common Recipe dataclass + validation
- `exp6_3_case_studies/generate_traces.py` — runs each recipe through `synthesize()` at 1× baseline, emits traces to `exp6_3_case_studies/traces/cs{1,2,3,4}_1x.events.csv`

**CS1 and CS2 are Day-3 hard deadline (handoff).** CS3, CS4 by Day 4. Per execution plan triage, CS3/CS4 drop first if schedule slips.

### Exp 6.4 — Scaling and breaking points (Anirudh + Yuanyang, Day 9)

**New files.**

- `exp6_4_scaling/scaling_runner.py`
  - For each case study × each intensity (2×, 5×, 10×): generate scaled trace via `synthesize()`, run through Exp 3 feasibility grid + Exp 4 Pareto
  - Output: per-case breaking-point table (intensity at which each tier × policy loses feasibility)
- `exp6_4_scaling/breaking_point_plot.py` — Figure 10 in paper §VI.B

### Exp 3.5 — Field-laptop measurement anchor (Anirudh + Jenna, Day 8)

**Promoted from stretch to required (v2.1).** Field laptop is the sole physical measurement tier; anchors the predicted grid's calibration error. Without this, every hardware claim in the paper is pure simulation.

**New files.**

- `exp3_5_calibration/laptop_spec.md` — documents Jenna's field laptop: CPU, GPU (if any), RAM, OS, installed runtimes. Reproduced in Table V.
- `exp3_5_calibration/run_on_laptop.sh` — concurrent YOLO (or MegaDetector) + BirdNET against CS1 1× replay on Jenna's field laptop under the adaptive policy
- `exp3_5_calibration/compare_to_prediction.py` — loads predicted P95 for the laptop cell from `exp3_hardware_feasibility/results/predicted_feasibility_grid.csv`; compares against measured P95; emits calibration gap
- `exp3_5_calibration/results/laptop_measurement.csv` — measured latency distribution (P50/P95/P99), memory pressure peaks, thermal observations
- `exp3_5_calibration/results/calibration_gap.json` — `{predicted_p95_ms, measured_p95_ms, gap_pct, notes}` for the one measured cell

Paper §VI.B.3 references this measurement; §VII.F names edge-tier validation as priority item for SmartWilds v2. If models don't run on the laptop as configured, pare back to single-model measurement (BirdNET-only or YOLO-only) and document constraints honestly rather than fake data.

---

## 5. Shared Utilities

New top-level helper module to avoid duplication across experiments:

- `experimental_resultsv2/common/`
  - `paths.py` — single source of truth for paths to recorded traces, Exp 1 primitives, Exp 6.3 case study traces
  - `event_schema.py` — unified event log schema, shared by synthesis + replay
  - `fidelity_metrics.py` — reused by 6.2.A, 6.2.B, 6.4 (lifted from 6.2.A once stable)

---

## 6. Dependencies and Critical Path

```
Exp 1 primitives ──→ Exp 6.1 synthesis ──→ Exp 6.3 case studies ──→ Exp 3 grid
                                                                 └──→ Exp 4 Pareto
                                                                 └──→ Exp 6.4 scaling
                          │
                          └──→ Exp 6.2.A variance envelope
                          └──→ Exp 6.2.B replay fidelity (requires Exp 4 replay harness too)

Exp 2.A independence ─────→ Exp 6.1 synthesis
Exp 5 edge filtering ─────→ (standalone; §V.D write-up)
```

**Critical path:** Exp 1 → Exp 6.1 → Exp 6.3 → handoff on Day 3–4. Everything downstream stalls if this slips.

---

## 7. Handoff Packaging (end of Day 3)

Single pull request from `experiments-v2` branch merging Exp 1, 6.1, 6.3 (CS1+CS2) to shared trunk, with:

1. `exp6_1_synthesis/synthesize.py` passing identity test
2. `exp6_3_case_studies/traces/cs1_1x.events.csv` and `cs2_1x.events.csv` generated
3. README in each of `exp3_hardware_feasibility/`, `exp4_policy_comparison/` documenting the expected input trace schema
4. `common/event_schema.py` finalized

Anirudh and Yuanyang branch off `experiments-v2` for their downstream work.
