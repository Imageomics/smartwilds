# Exp 4 — Policy Comparison + Energy + Synthesized Workloads (Yuanyang)

**Owner:** Yuanyang
**Deadline:** Day 8 (2026-04-29)
**Companion docs:** [mosaic_execution_plan_v2.md](../mosaic_execution_plan_v2.md) §2 Exp 4; [experiments_implementation.md](../experiments_implementation.md) §3.

---

## 1. Scope

Extend the v1 replay harness with:
1. **Energy model** — `E_event = Σ_stage (latency_stage × device_power_stage)`.
2. **Control-theoretic policy** — your Lyapunov-based extension as a fourth policy alongside `process_all`, `event_triggered`, `adaptive`.
3. **Synthesized-workload inputs** — run policies on CS1 and CS2 traces (not just the recorded trace).
4. **Pareto analysis** across (latency, energy, coverage, compute budget).

**Critical — your harness is also Jenna's harness.** Exp 6.2.B (replay-level fidelity; Jenna, due Day 6) reuses your replay harness and policy implementations to test whether synthesized traces reproduce the queue/latency behavior of recorded traces, *and* to confirm policy ranking invariance on CS1/CS2 across seeds. If your harness interface drifts after Day 4 handoff, her fidelity results won't compose with your Pareto results. See §4 below for the interface contract.

---

## 2. Inputs

| Input | Path | Notes |
|---|---|---|
| CS1 trace | `../exp6_3_case_studies/traces/CS1_ct_to_drone_1x.events.csv` | 799K events; 5s SLO |
| CS2 trace | `../exp6_3_case_studies/traces/CS2_acoustic_to_ct_1x.events.csv` | 492K events; 2s SLO |
| CS3, CS4 traces | `../exp6_3_case_studies/traces/` | time permitting (triage lever) |
| Identity-synthesized trace | generated via `synthesize(identity_recipe(...))` — see `../exp6_1_synthesis/` | used by Jenna's 6.2.B fidelity tests; your harness must handle this input too |
| Recorded trace | `../../experimental_results/ex3_exp4/exp4_code/` inputs | Jenna's 6.2.B compares recorded vs synthesized on this harness |
| Benchmark / energy table | `../exp3_hardware_feasibility/benchmark_table.csv` (Anirudh) | `latency_ms`, `power_W` per (model × tier) — your energy model multiplies these |
| Event log schema | `../exp6_1_synthesis/schemas.py` (`EVENT_LOG_COLUMNS`) | stable columns: `timestamp, modality, site, source_file, confidence, recipe_step` |
| v1 replay harness | `../../experimental_results/ex3_exp4/exp4_code/` — `replay_engine.py`, `policies.py`, `evaluate_replay.py`, `plot_replay_timeline.py` | reuse and extend |

---

## 3. Deliverables

### 3.1 Energy model (Day 4–5)

File: `energy_model.py`.

Given an event trace and per-stage latency+power from Anirudh's benchmark table, compute energy per event and aggregate energy per policy per workload.

```python
def event_energy(event: dict, tier: str, benchmark_table: pd.DataFrame) -> float:
    """E_event = Σ over inference stages of (latency_ms/1000 * power_W)."""
```

### 3.2 Control-theoretic policy (Day 4–5)

File: `control_theoretic_policy.py`.

Your Lyapunov-based extension, implementing the `Policy` interface (see §4). Test standalone on the identity recipe first (does it converge? does it respect SLO constraints?) before plugging into replay.

**Fallback:** if it doesn't converge by Day 6, drop to three policies and flag as "ongoing work" per plan §7 triage item #2. Tell Jenna by EOD Day 6 if you're going this route so §VI.B text can be updated.

### 3.3 Pareto analysis (Day 7)

File: `pareto_analysis.py`.

Input: per-policy × per-workload replay metrics from step 3.4. Output: Pareto front per workload as CSV + per-axis-pair figures.

Axes: (latency P95, energy per event, coverage %, compute budget % normalized to process_all).

Output files:
- `results/policy_metrics.csv` — one row per (policy × case_study × seed)
- `results/pareto_{case_study}.pdf` — Pareto front figure per workload
- `results/pareto_summary.csv` — Pareto-optimal cells

### 3.4 Orchestration

File: `run_all_policies.sh` — runs 4 policies × {CS1, CS2} × N seeds (suggest N=5 for stability). Emits metrics CSV. Extend to CS3, CS4 if time permits.

### 3.5 Exp 6.4 — intensity sweep (Day 8–9, joint with Anirudh)

Scale CS1, CS2 to 2× and 10× via `synthesize()` with `intensity_multiplier` parameter. Run the same 4 policies. Identify breaking points: intensity at which each policy × tier × case loses feasibility.

Output: `../exp6_4_scaling/results/breaking_points.csv` + breaking-point plot.

---

## 4. Interface contract — locked in by Day 4 (2026-04-25)

This is the interface Anirudh and Jenna both depend on. Don't change it after Day 4.

### 4.1 Policy interface

```python
# exp4_policy_comparison/policies.py
from typing import Protocol, Literal

class Policy(Protocol):
    name: str  # "process_all" | "event_triggered" | "adaptive" | "control_theoretic"

    def decide(self, event: dict, state: dict) -> Literal["process", "drop", "defer"]:
        """Called per event in arrival order. state is a mutable dict the harness
        owns for tracking queue depth, recent confidence, rate estimates, etc."""

def get_policy(name: str) -> Policy:
    """Factory. Raises ValueError on unknown name."""
```

Anirudh's `prediction_model.py` calls `get_policy(name).decide(...)` to apply the same policy logic as your harness. Jenna's 6.2.B test calls your full `replay()` with each policy.

### 4.2 Replay harness interface

```python
# exp4_policy_comparison/replay_engine.py
def replay(
    trace_path: Path,             # path to an event log CSV with EVENT_LOG_COLUMNS
    policy: Policy,
    tier: str,                    # key into benchmark_table for service rates
    benchmark_table: pd.DataFrame,
    slo_chain: list[dict],        # from the trace's manifest.json entry
    seed: int = 0,
) -> ReplayResult:
    ...

@dataclass
class ReplayResult:
    queue_depth_timeseries: pd.DataFrame  # columns: time, depth
    latency_distribution: pd.DataFrame    # columns: event_id, latency_ms
    slo_compliance_rate: float            # [0, 1]
    energy_per_event: pd.Series           # joules per event
    coverage_pct: float                   # fraction of events processed (vs dropped)
    compute_budget_pct: float             # normalized to process_all on same trace/tier
```

Jenna's 6.2.B will call this with:
- `trace_path = <recorded trace>` vs `trace_path = <identity-synthesized trace>`  →  Part A (identity fidelity).
- `trace_path = <CS1 or CS2 trace>` with seeds 0..4  →  Part B (cross-seed stability).

If your `replay()` signature changes after Day 4, her fidelity results don't align with your Pareto — coordinate explicitly.

### 4.3 Event log input

Your harness must consume any CSV with the columns defined in `../exp6_1_synthesis/schemas.py::EVENT_LOG_COLUMNS`. The recorded trace, identity-synthesized trace, and CS1–CS4 traces all share this schema. Don't hardcode a particular source.

---

## 5. Environment

**Python 3.12 required** (`module load python/3.12`). The user-local Python 3.9 has a numpy/pandas ABI mismatch (numpy 1.20.1 vs pandas requiring ≥ 1.22.4). Verified against the identity test on 2026-04-23.

---

## 6. Deliverables and due dates

| Date | Deliverable |
|---|---|
| **2026-04-25** | **Interface contract locked** — send `policies.py` + `replay_engine.py` signatures to Anirudh and Jenna. Do not change after this. |
| **2026-04-25** | `energy_model.py` working; `control_theoretic_policy.py` converging on identity recipe |
| **2026-04-26** | All 4 policies running on CS1 at 1× through replay harness with energy metric |
| **2026-04-27** | `policy_metrics.csv` complete for {4 policies} × {CS1, CS2} × {5 seeds}; Pareto figures drafted |
| **2026-04-28** | Send `pareto_summary.csv` + figures to Jenna for Table VI + Figure 11 |
| **2026-04-29** | Exp 6.4 intensity sweep (joint with Anirudh) — 2× and 10× breaking points |

---

## 7. Triage levers (plan §7)

If timeline slips:
- **Item 2 (plan §7):** drop control-theoretic policy → 3 policies. Tell Jenna by EOD Day 6.
- **Item 3:** run only CS1 + CS2 through replay; skip CS3/CS4.
- **Item 4:** Exp 6.4 at {1×, 2×, 10×} only (skip 5×).

---

## 8. Questions

Raise early (DM Jenna); don't block on these:
- M/M/1 vs deterministic queue for latency calc — Anirudh is picking one for his prediction model; use the same one for consistency.
- How many seeds for Pareto stability? Suggest 5; bump to 10 if spread is large.
- Whether SLO compliance is computed per-edge-in-chain (CS1 has CT→Drone edge) or per-event end-to-end. Suggest per-edge; document the choice.
