# Exp 6.2.B — Replay-Level Fidelity (Jenna)

**Owner:** Jenna
**Deadline:** Day 6 (2026-04-27)
**Companion docs:** [mosaic_execution_plan_v2.md](../mosaic_execution_plan_v2.md) §2 Exp 6.2.B (refined protocol).

---

## 1. Why this exists

Trace-level fidelity (6.2.A variance envelope) shows the *input* is faithful. Replay-level fidelity shows the *evaluation machinery* is faithful — that running policies on synthesized traces produces the same system behavior (queue buildup, latency distribution, policy rankings) as running on recorded traces.

**Load-bearing claim for §VII.D:** "Decisions a practitioner would make from MOSAIC-synthesized workloads are the same as from recorded workloads." Policy ranking invariance is the number that backs this.

---

## 2. Three-part protocol (refined v2.1)

### Part A — Identity trace (zero-generalization baseline)

For each of 4 policies (process_all, event_triggered, adaptive, control_theoretic):
1. Run on recorded trace (Campaign 2 Aug 4–28); record queue depth timeseries, P50/P95/P99 latency, SLO compliance.
2. Run on synthesized identity trace (identity recipe, full primitives); record same metrics.
3. Compare: queue KS ≤ 0.15, P95 ratio within 15%, latency KS ≤ 0.15, SLO compliance diff ≤ 5 pp.

### Part B — Case studies (generalization levels 1–3)

Run all 4 policies on CS1 and CS2 at 1×, with 5 seeds each. No recorded comparand exists (these are the synthesis counterfactual) — the fidelity check is cross-seed stability:
- Same case × same policy across seeds: queue / latency KS ≤ 0.10
- Per-policy per-case-study metrics table reported in §VI.A.3 or §VI.B

### Part C — Policy ranking invariance

The binding result:
- Part A: Kendall's tau between policy ranking on recorded vs synthesized per metric
- Part B: Kendall's tau across seeds on CS1 and CS2
- Cross-case-study: do the same policies win on CS1 as on CS2? (This is a *finding* for §VII.D, not a fidelity test.)

---

## 3. Uses Yuanyang's replay harness

**This is not a separate harness.** It's his `replay()` function called on different inputs:
- Part A: `replay(recorded_trace, ...)` vs `replay(identity_synthesized_trace, ...)`
- Part B: `replay(cs1_trace, seed=k, ...)` for k in 0..4
- Same `policies.py`, same `replay_engine.py`, same metrics definitions

**Sanity check before the real run:** pick one Exp 4 cell (e.g., adaptive policy on CS1 1× seed 0). Run via his `replay()` call path here. Compare the `ReplayResult` to Yuanyang's stored Exp 4 output for that cell. They should match bit-for-bit. If they don't, there's a harness bug — fix before proceeding.

---

## 4. Deliverables

- `replay_fidelity.py` — Part A: recorded vs identity-synthesized comparisons per policy
- `policy_ranking_invariance.py` — Part C: Kendall's tau across policies
- `generalization_sweep.py` — Parts A+B+C wrapped; emits the fidelity-vs-generalization curve (paper Figure 9)
- `results/part_a_identity_fidelity.csv` — per-policy: queue_ks, p95_ratio, latency_ks, slo_diff, verdict
- `results/part_b_cross_seed.csv` — per-(policy × case_study × seed_pair): cross-seed KS stability
- `results/part_c_ranking_invariance.json` — Kendall's tau numbers; one per (metric × {identity, CS1, CS2})

---

## 5. Dependencies

- **Blocks on:** Yuanyang's `replay_engine.py` + `policies.py` interface (locked by Day 4 per his README). Control-theoretic policy by Day 5 or he drops it to 3 policies — either is fine, adjust the ranking analysis accordingly.
- **Consumes:** Anirudh's `benchmark_table.csv` (for tier-specific service rates; the recorded-vs-synthesized comparison should use one consistent tier — pick `workstation_rtx` since that's the Campaign 2 processing environment).

---

## 6. Environment

`module load python/3.12`.
