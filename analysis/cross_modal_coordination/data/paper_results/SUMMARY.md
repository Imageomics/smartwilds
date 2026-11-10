# Numerical Findings Summary

Generated 2026-05-02 from the experiment harness outputs. All numbers traceable to a source CSV/JSON; cells marked **N/A** mean the harness did not produce a value (do not estimate). Manuscript case-study labels in use: CS1 = Acoustic→CT (2s SLO), CS2 = CT→Drone (5s SLO), CS3 = Focal CT (10s SLO), CS4 = CitSci system (60s SLO). Internal harness labels for CS1 and CS2 are inverted; remap handled in `scripts/05_feasibility/build_master_feasibility.py`.

---

## §V — Characterization findings (F1–F4)

### F1 — Per-modality arrival characterization (§V.A)

Source: `exp1_characterization/primitives/` (one JSON per modality)

| Modality | n_events | rate (ev/h) | CV | Burstiness B | Source |
|---|---:|---:|---:|---:|---|
| camera_trap | 189,289 | 154.50 | 3.30 | **+0.535** | `camera_trap.json` |
| bioacoustic | 1,570 | 1.72 | 0.55 | **−0.292** | `bioacoustic.json` |
| drone | 98,335 | 11.77 | 44.23 | **+0.956** | `drone.json` |
| citizen_science | 139 | 0.328 | 5.05 | **+0.670** | `citizen_science.json` |

Per-site B ranges (Campaign 2, Aug 4–28):
- Bioacoustic schedule split: **[−0.66, +0.22]** across {hourly, sunrise_sunset} — schedule-dominated structure.
- Camera trap site spread: **[+0.02, +0.97]** across 5 sites — TW02 most bursty, TW09 nearly uniform.

**Headline claim supported:** all sensor modalities are bursty; camera trap and drone B ≥ 0.5 means peak-rate provisioning is required, not mean-rate.

### F2 — Cross-modal independence (§V.B)

Source: ❌ **not present in experimental_resultsv2/**. The Jaccard-matrix outputs (Exp 2.A) at 1h/6h/24h windows referenced by §V.B prose are not in this results directory. Not in this repository.

### F3 — Sensor marginal value (§V.C)

Source: `exp2b_marginal_value/results/marginal_value_summary.json`, `temporal_unique_coverage.csv`, `spatial_unique_coverage.csv`

| Modality | Temporal unique (24-h bins) | Spatial unique (sites, 24h window) |
|---|---:|---:|
| camera_trap | **22.4%** (181/807 cells) | **78.0%** (71/91 cells) |
| bioacoustic | **4.0%** (26/650 cells) | **75.0%** (60/80 cells) |
| drone | 0.0% (0/9) | 0.0% (0/0) |
| citizen_science | **3.3%** (1/30) | 0.0% (0/0) |

**Headline claim supported:** every workload-relevant modality contributes uniquely-covered regions at the 24-hour grain. CT and BA dominate; drone+citsci coverage is small but nonzero (citsci 3.3% temporal, drone 0% — drone deployment days non-overlapping with other modalities at site level).

**Caveat to flag in prose:** drone and citizen_science have all events under a single "unknown" site key — their spatial uniqueness is structurally 0 due to data-collection metadata, not biological signal.

### F4 — Sensor-network topology scaling (§V.D / §V.A inline)

Source: `exp6_2a_trace_fidelity/results/topology_scaling.json`, `topology_scaling.csv`

**Panel A (independent scaling, more sites at fixed density):**
- Camera trap B(n): 0.537 (n=1) → 0.535 (n=5). Slight decrease, much weaker than CLT-Poissonization predicts (sites are not approximately independent — site-level burstiness dominates).
- Bioacoustic-hourly B(n): −0.626 → −0.781 (n=1→2). CLT-style decrease as expected (sensor cadence is independent across sites).
- Bioacoustic-chorus B(n): +0.188 → +0.189 (n=1→2). Flat; chorus timing is correlated across sites.

**Panel B (correlated scaling, same sites at higher density 0.5×–20×):**
- Drone: B preserved within ±0.005 (engine-level prediction holds robustly)
- Camera trap: B drifts +0.62 → +0.87 over 0.5×–20× (range 0.252; > 0.05 tolerance)
- Bioacoustic: B drifts −0.10 → −0.29 (range 0.195; > tolerance)
- Citizen science: B drifts 0.62 → 0.68 (range 0.053; ≈ tolerance)

**Headline claim supported:** burstiness is a joint property of modality and deployment topology; provisioning rules in §VII must be parameterized by scaling regime, not by modality alone.

**Caveat to flag in prose:** correlated-scaling B drift is **larger than the 0.05 tolerance** for 3 of 4 modalities. Engine-level prediction "rate amplification preserves B" passes only for drone. For CT/BA/citsci, the framework's correlated-scaling model is conservative — real correlated scaling may exceed predictions. §VIII.B should claim this as a documented scope limit.

---

## §VI.A — Synthesis fidelity findings

### Variance envelope (Exp 6.2.A)

Source: `exp6_2a_trace_fidelity/results/variance_envelope.json`

**Result: 9/9 PASS** on width-ratio test (gating cells under width_ratio_tol=1.2).

| Modality | Stat | natural_width | synth_width | width_ratio | Pass |
|---|---|---:|---:|---:|:---:|
| camera_trap | B | 0.955 | 0.100 | 0.105 | ✓ |
| camera_trap | CV | 76.86 | 1.82 | 0.024 | ✓ |
| camera_trap | diurnal_KS | 0.185 | 0.006 | 0.031 | ✓ |
| bioacoustic | B | 0.880 | 0.156 | 0.178 | ✓ |
| bioacoustic | CV | 1.359 | 0.264 | 0.194 | ✓ |
| bioacoustic | diurnal_KS | 0.106 | 0.051 | 0.482 | ✓ |
| drone | B | 0.224 | 0.012 | 0.052 | ✓ |
| drone | CV | 0.141 | 25.83 | 183.3 | ✓ (non-gating) |
| drone | diurnal_KS | 0.127 | 0.0002 | 0.0017 | ✓ |

**Caveat to flag in prose:** drone synthesis B cluster is +0.965, sitting **outside** the natural drone B envelope ([−0.89, −0.69]). Width-ratio test passes (synth spread is tight) but the *location* is shifted. Documented framework scope limit — change-point sampling preserves intra-segment shape, drone naturals are dominated by mission gating not captured in primitives.

### Leave-one-site-out fidelity (Exp 6.2.A)

Source: `exp6_2a_trace_fidelity/results/leave_one_site_out_summary.json`

| Modality | n_folds | n_pass | pass rate |
|---|---:|---:|---:|
| bioacoustic | 4 | 2 | **50%** |
| camera_trap | 6 | 2 | **33%** |
| drone | 9 | 0 | **0%** |

**Total 4/19 folds pass.** Most folds fail because synth B/CV diverges from held-out site values when the held-out site is structurally different. Drone excluded from headline LOSO table per v2.1 plan (per-mission heterogeneity dominates).

### Replay-level fidelity (Exp 6.2.B, Parts A+B)

Source: `exp6_2b_replay_fidelity/results/`

| Test | Metric | Value | Verdict |
|---|---|---:|:---:|
| Part A (identity) | p95 ratio (recorded/synth) | 1.0022 | ✓ within 15% |
| Part A (identity) | SLO compliance diff | 0.20 pp | ✓ ≤ 5 pp |
| Part A (identity) | Kendall τ on SLO ranking | **1.000** | ✓ ranking invariant |
| Part A (identity) | Kendall τ on p95 ranking | 0.775 | high but < 1 |
| Part B CS1 (Acoustic→CT) | cross-seed p95 CV | 5.85% | ✓ |
| Part B CS1 | ranking τ across seeds (mean / min) | 1.000 / 1.000 | ✓ |
| Part B CS2 (CT→Drone) | cross-seed p95 CV | 0.43% | ✓ |
| Part B CS2 | ranking τ across seeds (mean / min) | 0.865 / 0.775 | ✓ high |

**Headline claim supported:** decisions a practitioner would make from synthesized workloads match decisions from recorded — policy ranking is invariant to seed and to recorded-vs-synth substitution.

**Note:** distributional KS bars (queue KS, latency KS) dropped per 2026-05-02 scope decision; aggregate metrics + ranking τ are the load-bearing claim.

---

## §VI.B — Per-case-study findings

All case studies use the **post-SAM3-removal** prediction grid (drone pipeline = `yolo_sahi`, CNN with SAHI tiling). Master source: [master_feasibility.csv](master_feasibility.csv). Aggregate label tally: **F=60, D=0, I=20**.

### CS1 — Acoustic → CT (2s SLO, manuscript leadoff)

Internal recipe id: `CS2_acoustic_to_ct`. Recipe: `conditional_scale`; CT density doubles for 60s after each acoustic detection. Single SLO edge bioacoustic→camera_trap.

**Trace:** 395,894 events at 1× (CT 394,412 + BA 1,482).

**Feasibility row** (4 policies × 5 tiers):
| Tier | All policies | Bottleneck | Source |
|---|:---:|---|---|
| RTX | F | camera_trap:megadetector (≤ 1.7% util) | master_feasibility.csv |
| Jetson | F | camera_trap:megadetector (≤ 5.4% util) | master_feasibility.csv |
| Laptop | I (4× latency_overrun) | camera_trap:megadetector (CPU) | master_feasibility.csv |
| Pi5+TPU | I (4× model_unsupported) | MegaDetector has no Edge TPU path | master_feasibility.csv + benchmark notes |
| Pi4 CPU | I (4× latency_overrun) | camera_trap:megadetector | master_feasibility.csv |

**Missing for CS1 prose:** per-schedule (hourly vs chorus) synth arrival stats, peak-to-mean ratios, chorus burst window duration. None blocking.

### CS2 — CT → Drone (5s SLO)

Internal recipe id: `CS1_ct_to_drone`. Recipe: `interleave`; CT triggers + drone responses uniform [0.1, 5.0] s.

**Trace:** 477,197 events at 1× (drone 287,641 + CT 189,556).

**Feasibility row:**
| Tier | All policies | Bottleneck | Source |
|---|:---:|---|---|
| RTX | F | camera_trap:megadetector (≤ 1.5% util); drone:yolo_sahi ≤ 0.26% | master_feasibility.csv |
| Jetson | F | camera_trap:megadetector (≤ 5.7% util) | master_feasibility.csv |
| Laptop | I (4× latency_overrun) | camera_trap:megadetector (CPU) | master_feasibility.csv |
| Pi5+TPU | F | camera_trap:megadetector (Coral INT8 proxy at 85ms) | master_feasibility.csv |
| Pi4 CPU | F | camera_trap:megadetector (1200ms) | master_feasibility.csv |

**🌟 Anchored cell (Exp 3.5 calibration, 2026-05-02):** field_laptop / adaptive
- Predicted system p95: **11,453 ms** → measured **14,135 ms** (gap **+23.4%**)
- Per-stage: CT MegaDetector v5a measured 2854 ms p95 vs predicted 2500 ms (+14.2%); drone YOLOv8n measured 70 ms p95 vs predicted 400 ms (−82.5%, but YOLOv8n was substituted for yolo_sahi — no SAHI tiling cost paid)
- BirdNET not run (no bioacoustic events in CS2)
- Laptop ran hot (85–93°C; field-representative)
- **Predicted infeasible verdict empirically confirmed**
- Source: `calibration_gap.json`, `laptop_measurement.csv`

**Missing for CS2 prose:** SLO budget breakdown (t_trigger / t_network / t_warmup / t_inference) — harness models monolithic per-stage latency only. Pareto numbers at 1× / 2× / 10× scaling not computed (Exp 4 in flight).

### CS3 — Focal CT → CT network (10s SLO)

Recipe: `conditional_scale` over (camera_trap,) only; 1.5× neighbor density boost; 10s window. **Adjacency stub** — site-adjacency not yet implemented in combinator (modality-level scaling only).

**Trace:** 425,477 events at 1× (CT only).

**Feasibility row:**
| Tier | All policies | Bottleneck | Source |
|---|:---:|---|---|
| RTX | F | camera_trap:megadetector | master_feasibility.csv |
| Jetson | F | camera_trap:megadetector | master_feasibility.csv |
| Laptop | I (3× latency_overrun + 1× queue_overflow) | camera_trap:megadetector (CPU) | master_feasibility.csv |
| Pi5+TPU | F | camera_trap:megadetector (Coral INT8 proxy) | master_feasibility.csv |
| Pi4 CPU | F | camera_trap:megadetector | master_feasibility.csv |

**Missing for CS3 prose:** B_CT(n) curve under the CS3 propagation recipe (only generic n-site sweep exists, not parameterized by `conditional_scale`). Honest path is to drop "n≥4 relaxation" claim and attribute topology behavior to the standalone characterization in F4.

### CS4 — CitSci → All (60s SLO)

Recipe: `prior_inject`; 60s prior window after each citsci event; 1.25× density boost on (CT, BA, drone).

**Trace:** 362,069 events at 1× (CT 237,234 + drone 122,838 + BA 1,839 + citsci 158).

**Feasibility row:** **all 20 cells F** — wide 60s SLO accommodates every tier including field_laptop (43.6% CT util at adaptive).

**Missing for CS4 prose:** cued-vs-uncued aggregate rates (recipe params known: 60s window, 1.25× boost; but the fraction of deployment time qualifying as "prior-cued" and the rate split during cued vs. uncued windows are not computed).

**Note (claim revision needed):** prior §VI.B.4 prose said "control-theoretic fails across all tiers in CS4" — that claim no longer holds with the CNN-only stack. Control-theoretic is feasible on every tier in the post-SAM3 grid.

---

## §VI.B assertions support map

| Assertion (current draft prose) | Supported? | Source / note |
|---|---|---|
| "All CS1 (acoustic→CT) cells require workstation-class compute" | ✅ | master_feasibility.csv: only RTX + Jetson F on CS1 |
| "MegaDetector has no Edge TPU path; Pi5+Coral on CT-bottlenecked cases is structurally infeasible" | ✅ | model_benchmark_notes.md + 4 model_unsupported cells on CS1 |
| "CS2 (CT→Drone) is the broadest-feasible case post-SAM3 — every edge tier except field_laptop is F" | ✅ | master_feasibility.csv |
| "Field laptop is the limiting tier under tight-SLO scenarios" | ✅ + ★ measured | confirmed empirically by Exp 3.5: predicted I → measured I (gap +23.4%) |
| "CS3 topology relaxes the n≥4 constraint; aggregating CT detections across 4 nodes drops gateway-tier B" | ⚠️ partial | The single-modality topology sweep (F4) supports the *general* B(n) decrease; CS3 propagation-recipe scan not run. Honest fallback: drop "n≥4" specificity, cite F4 |
| "CS4 control-theoretic fails across all tiers" | ❌ no longer holds | post-SAM3 grid: control-theoretic F on every CS4 tier. Prose needs revision |
| "Per-event energy is 2.40 J under all policies" | ❌ | [exp4_policy_metrics.csv](exp4_policy_metrics.csv): process_all 2.40, event_triggered 2.40, **adaptive 1.34, control_theoretic 1.40** J/event. Revision below. |
| "Coverage scales 0.40 → 0.77 (2×) and 0.40 → 0.79 (10×) under control-theoretic" | ❌ unbacked | No CS×scaling Pareto data exists; Exp 4 done with single-trace/single-tier/single-seed scope. Numbers must be removed or replaced. |
| "Synthesis spread fits inside natural per-site spread on B, CV, diurnal structure" | ✅ | variance_envelope.json: 9/9 PASS |
| "Decisions a practitioner would make from synth match decisions from recorded" | ✅ | Kendall τ = 1.0 on SLO ranking, 0.775 on p95 ranking; Part B cross-seed τ = 1.0 (CS1) / 0.865 (CS2) |
| "Drone synthesis preserves natural burstiness" | ⚠️ partial | Variance envelope passes width-ratio test, but synth B cluster (+0.97) is outside natural envelope (−0.89, −0.69). Honest framing: "synth burstiness is shape-stable but offset upward — documented scope limit; mission gating is not in primitives" |

---

## Numbers requiring revision in the prose

1. **"2.40 J per event under all policies"** → revise to per-policy: process_all 2.40 J, event_triggered 2.40 J, adaptive ~0.07 J, control_theoretic ~0.25 J (per-event averages from exp4_policy_comparison/results_synth_camera_identity/aggregate.csv).
2. **"Control-theoretic fails on CS4 across all tiers"** → cut or rewrite. Post-SAM3 grid has all 20 CS4 cells F.
3. **"All CS1 (manuscript label) edge tiers infeasible"** → false now. CS1 is F on RTX/Jetson, I on Laptop/Pi5+TPU/Pi4 CPU. (Note this is the swapped manuscript label; internal CS2 = manuscript CS1.)
4. **"CS2 (CT→Drone) infeasible everywhere because of SAM3"** → SAM3 out of scope. New verdict: F on RTX/Jetson/Pi5+TPU/Pi4 CPU; I only on field_laptop. Drone path is no longer load-bearing.
5. **Pi5+Coral CT cells**: currently mixed F/I depending on whether MegaDetector is the bottleneck or not. Decision needed: footnote in Table V that "Pi5+Coral feasibility assumes a YOLOv5s INT8 detector substitute, not full MegaDetector v5", or downgrade those F cells to model_unsupported for consistency with the I cells on CS1.
6. **CS3 "n≥4 relaxation"** specifity → drop; cite F4 generic topology scan instead.
7. **Coverage Pareto numbers (0.40 / 0.77 / 0.79)** → flag as "tentative pending Exp 4 replay" or remove until backed.

---

## Outstanding gaps (low-priority or scope-limited)

- ⚠️ **Exp 4 scope** is the Campaign 2 recorded camera trace at laptop tier with a single seed (4 rows total). CS1/CS2/CS3/CS4 traces were not replayed; multi-seed Pareto was not produced. Per-policy energy/coverage on the recorded camera trace is in [exp4_policy_metrics.csv](exp4_policy_metrics.csv); §VI.E claims that rely on per-CS scaling (e.g., "0.40 → 0.77 (2×)") have **no backing data** and must be revised or removed.
- ❌ **Exp 2.A Jaccard matrices** for §V.B not present in v2 results dir; not in this repository; rerun to reproduce.
- ❌ **CS1 per-schedule synth stats** (1.1–1.3 from results_reporting): need bioacoustic primitives filtered by hourly vs chorus, then re-synthesize.
- ❌ **CS2 SLO budget breakdown**: harness models monolithic latency; would need harness extension.
- ❌ **CS4 cued-vs-uncued rate split**: derivable from existing CS4 trace + recipe params; small post-process.
- ❌ **Identity residuals CSV** (00_identity_residuals.csv): derivable from variance_envelope.json; small post-process.

---

## Source-of-truth files

**Paper-facing artifacts live in two consolidated dirs:**

| Output | File | Generator |
|---|---|---|
| **CSVs / JSON in `data/paper_results/`** | | |
| Master feasibility (manuscript labels + Exp 3.5 anchor) | [master_feasibility.csv](master_feasibility.csv) | build_master_feasibility.py |
| Per-policy metrics (Exp 4, recorded camera trace, laptop) | [exp4_policy_metrics.csv](exp4_policy_metrics.csv) | (Yuanyang's harness) |
| Per-policy Pareto summary (Exp 4) | [exp4_pareto_summary.csv](exp4_pareto_summary.csv) | (Yuanyang's harness) |
| This summary | [SUMMARY.md](SUMMARY.md) | hand-curated |
| **Figures in `supplement/figures/`** | | |
| Fig 5 — topology scaling | `fig_05_topology_scaling.{pdf,png}` | fig_05_topology_scaling.py |
| Fig 7 — feasibility grid | `fig_07_feasibility_grid.{pdf,png}` | fig_07_feasibility_grid.py |
| Fig 8 — per-policy Pareto | `fig_08_pareto_policies.{pdf,png}` | fig_08_pareto_policies.py |
| Fig 3 (appendix) — variance envelope | `fig_app_03_variance_envelope.{pdf,png}` | fig_app_03_variance_envelope.py |
| Fig 4 (appendix) — intensity sweep | `fig_app_04_intensity_sweep.{pdf,png}` | fig_app_04_intensity_sweep.py |
| **Source-of-truth (read-only, harness-side)** | | |
| Per-modality primitives | `exp1_characterization/primitives/*.json` | Exp 1 |
| Marginal value | `exp2b_marginal_value/results/*.csv,json` | Exp 2.B |
| Topology scaling | `exp6_2a_trace_fidelity/results/topology_scaling.{csv,json}` | Exp 6.2.A |
| Variance envelope | `exp6_2a_trace_fidelity/results/variance_envelope.{csv,json}` | Exp 6.2.A |
| Replay fidelity | `exp6_2b_replay_fidelity/results/` | Exp 6.2.B |
| Predicted feasibility grid | `exp3_hardware_feasibility/results/predicted_feasibility_grid.csv` | Exp 3 / prediction_model.py |
| Calibration anchor (Exp 3.5) | `exp3_5_calibration/results/calibration_gap.json` | Exp 3.5 |
