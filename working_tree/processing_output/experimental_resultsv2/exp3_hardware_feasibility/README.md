# Exp 3 — Predicted Hardware Tier Feasibility (Anirudh)

**Owner:** Anirudh
**Deadline:** Day 7 (2026-04-28) predicted grid; Day 8 (2026-04-29) field-laptop anchor (Exp 3.5)
**Companion docs:** [mosaic_execution_plan_v2.md](../mosaic_execution_plan_v2.md) §2 Exp 3 and §2 Exp 3.5; [experiments_implementation.md](../experiments_implementation.md) §3.

---

## 1. Scope (v2.1 — read this first)

We do not have Jetson or Pi hardware this cycle. Exp 3 is **prediction-only** across all edge tiers; the field laptop (Exp 3.5) is the sole measured tier, anchoring prediction error. Every hardware claim in the paper will carry an explicit "(predicted)" qualifier except the laptop-tier anchor. This matches the paper's intended use case: predicting feasibility *before* procurement, then calibrating.

Your job has two parts:
1. **Exp 3 (pred grid):** build the benchmark table + prediction model, run across (tier × workload × policy), emit the feasibility grid.
2. **Exp 3.5 (anchor):** one physical measurement on Jenna's field laptop (CS1 1× + adaptive policy), compared against your laptop-tier prediction to report calibration error.

No device access required for Exp 3. Exp 3.5 runs on Jenna's laptop — coordinate timing with her.

---

## 2. Inputs (what's already available)

| Input | Path | Notes |
|---|---|---|
| CS1 trace (1×) | `../exp6_3_case_studies/traces/CS1_ct_to_drone_1x.events.csv` | 799,314 events; CT→Drone; 5s SLO |
| CS2 trace (1×) | `../exp6_3_case_studies/traces/CS2_acoustic_to_ct_1x.events.csv` | 491,964 events; Acoustic→CT; 2s SLO |
| CS3 trace (1×) | `../exp6_3_case_studies/traces/CS3_focal_ct_network_1x.events.csv` | time-permitting |
| CS4 trace (1×) | `../exp6_3_case_studies/traces/CS4_citsci_system_1x.events.csv` | time-permitting |
| Case study metadata | `../exp6_3_case_studies/traces/manifest.json` | SLOs, event counts, seeds |
| Event log schema | `../exp6_1_synthesis/schemas.py` (`EVENT_LOG_COLUMNS`) | `(timestamp, modality, site, source_file, confidence, recipe_step)` |
| v1 Exp 3 code | `../../experimental_results/ex3_exp4/exp3_code/` | reuse `build_drone_arrival_summary.py`, `build_exp3_strict_tables.py`, `path_config.py` (adapt paths) |
| Exp 1 primitives | `../exp1_characterization/primitives/*.json` | per-modality burstiness, CV, diurnal for sanity checks |

---

## 3. Deliverables

### 3.1 Benchmark table (Day 4–5)

Directory: `3.1/`

File: `3.1/benchmark_table.py` (generator) → `3.1/benchmark_table.csv` (data).

One row per (model, tier). Columns:
- `model` — one of `birdnet`, `yolo_sahi`, `sam3`, `bioclip`, `megadetector`
- `tier` — one of `workstation_rtx`, `jetson_orin_nano`, `pi5_coral`, `pi4_cpu`, `field_laptop`
- `latency_ms` — published inference latency per event, single-stream
- `power_W` — device TDP or published inference power
- `memory_MB` — working-set memory footprint
- `source_url` — model card, paper, or manufacturer spec (one source per cell)
- `notes` — assumptions (batch size, image size, precision, etc.)

**Field laptop row:** use Jenna's laptop spec (to be filled in `../exp3_5_calibration/laptop_spec.md`). Predict from published CPU/GPU benchmarks for the exact chip.

**Quality bar:** every cell cited. If a number is extrapolated (e.g., SAM3 on Pi), flag in `notes` with "extrapolated from X by factor Y" — do not invent numbers.

### 3.2 Prediction model (Day 6–7)

Directory: `3.2/`

File: `3.2/prediction_model.py`.

Function signature:
```python
def predict_cell(
    trace_path: Path,        # event log CSV
    tier: str,               # tier name from benchmark_table
    policy: str,             # one of: process_all, event_triggered, adaptive, control_theoretic
    benchmark_table: pd.DataFrame,
    slo_chain: list[dict],   # from manifest.json
) -> dict:
    """Returns {utilization_pct, p95_latency_ms, bottleneck_modality, verdict}."""
```

Implementation sketch:
1. Load event log, group by modality, get arrival rate per modality per hour-of-day.
2. From benchmark_table, look up per-stage latency and power on this tier.
3. Apply policy (uses Yuanyang's `policies.py` — coord with him for a stable interface; see §5 below).
4. Compute queueing-model utilization (M/M/1 or deterministic queue; pick one and document).
5. Compute predicted P95 latency: service time + queueing delay at the arrival-rate tail (e.g., 95th percentile of hourly rate).
6. Bottleneck = modality × stage with highest utilization.
7. Verdict: `feasible` if util < 70% and p95 ≤ SLO; `degraded` if 70–100% or p95 near SLO; `infeasible` if util > 100% or p95 > SLO.

Output: `3.2/results/predicted_feasibility_grid.csv` with one row per (case_study × tier × policy).

### 3.3 Heatmap (Day 7)

File: `3.2/plot_predicted_grid.py` → `3.2/results/predicted_feasibility_heatmap.pdf`.

Axis: case study × policy on y; tier on x. Cell color by verdict. This is Figure 10 input.

### 3.4 Orchestration script

File: `3.2/run_predictions.sh` — regenerates `3.1/benchmark_table.csv`, then runs `3.2/prediction_model.py` and `3.2/plot_predicted_grid.py` over all (case × tier × policy) cells. No device required.

### 3.5 Field-laptop anchor (Exp 3.5, Day 8 — joint with Jenna)

Files in `../exp3_5_calibration/`:
- `laptop_spec.md` — documents Jenna's laptop (CPU, GPU if any, RAM, OS, installed runtimes). Reproduced in paper Table V.
- `run_on_laptop.sh` — run YOLO (or MegaDetector) + BirdNET concurrently against CS1 1× replay on Jenna's laptop, adaptive policy.
- `compare_to_prediction.py` — load predicted laptop-tier P95 from `prediction_model.py` output; compare against measured.
- `results/laptop_measurement.csv` — measured P50/P95/P99 latency, memory peaks, thermal notes.
- `results/calibration_gap.json` — `{predicted_p95_ms, measured_p95_ms, gap_pct, notes}`.

**If models don't run as configured on laptop:** pare back to single-model measurement (BirdNET-only or YOLO-only). Document the constraint honestly — do not fake data.

---

## 4. Environment

**Python 3.12 required** (`module load python/3.12` on the cluster). The user-local Python 3.9 has a numpy/pandas ABI mismatch — you'll hit `ImportError: this version of pandas is incompatible with numpy < 1.22.4` if you use it. Verified against the identity test (2026-04-23).

For the field-laptop anchor (Exp 3.5), you'll need the actual YOLO/MegaDetector + BirdNET runtimes installed on Jenna's laptop. Coordinate install steps with her on Day 7.

---

## 5. Interfaces to lock in with Yuanyang

Your prediction model consumes policy decisions (event_triggered, adaptive, control_theoretic filter/dispatch events differently). Yuanyang is building the replay harness with the authoritative policy implementations. Agree on this interface with him by **Day 4 (2026-04-25)**:

```python
# In Yuanyang's exp4_policy_comparison/policies.py
class Policy(Protocol):
    name: str
    def decide(self, event: dict, state: dict) -> Literal["process", "drop", "defer"]:
        ...
```

Your prediction model should `from exp4_policy_comparison.policies import get_policy` and apply the same decision function. This avoids prediction and Pareto analysis disagreeing on what each policy does.

---

## 6. Deliverables and due dates

| Date | Deliverable |
|---|---|
| **2026-04-25** | Agree policy interface with Yuanyang; start `benchmark_table.py` |
| **2026-04-26** | `benchmark_table.csv` populated (all cells cited); `prediction_model.py` scaffolded |
| **2026-04-27** | `predicted_feasibility_grid.csv` + heatmap PDF emitted; send CS1/CS2 cells to Jenna for Table V draft |
| **2026-04-28** | Field-laptop anchor (Exp 3.5) with Jenna; `calibration_gap.json` in hand |
| **2026-04-29** | Exp 6.4 scaling (joint with Yuanyang) — predicted breaking points at 2×, 10× |

---

## 7. Output schema for Table V (paper §VI.B)

One row per (case study × tier × policy). Columns Jenna will use to populate Table V:
- `case_study`, `tier`, `policy`
- `utilization_pct_predicted`
- `p95_latency_ms_predicted`
- `slo_target_ms` (from manifest.json)
- `slo_met_predicted` (boolean)
- `bottleneck`
- `verdict`
- `measured` (boolean; True only for `tier == field_laptop, case_study == CS1`)
- `calibration_gap_pct` (only for the measured row)

Consistency rule: every *non-measured* row in Table V displays numbers with "(predicted)" in the caption or a superscript marker.

---

## 8. Questions

Raise early (DM Jenna); don't block on these:
- Whether to use M/M/1 or deterministic queue for utilization modeling (pick one and document).
- Whether to report per-modality or aggregated utilization (aggregated is paper-ready; per-modality helps with bottleneck naming).
- Whether the laptop anchor should test multiple SLO targets (CS1 @ 5s is minimum; CS2 @ 2s stretch).
