# MOSAIC — Experimental Execution Plan v2

**SEC 2026 — April 20 to May 1**
*Framing locked in `mosaic_framing_v4.tex`. This doc is execution.*

**v2 updates from v1:**
- Within-modality variance envelope is now the primary defensibility argument for Exp 6.2 (stronger than leave-one-site-out)
- Replay-level fidelity added as Exp 6.2.B (queue buildup, latency distributions, policy ranking invariance)
- New Section III.B methodology subsection distinguishing measured / modeled / simulated / predicted
- Optional real-hardware calibration run flagged as highest-leverage stretch goal
- Solo-first sequencing updated: Jenna runs Exp 1, 2.A, 5, 6.1 in Days 1–3 for clean handoff

**v2.1 scope pivot (2026-04-23):**
- No Jetson or Pi hardware accessible this cycle. Exp 3 pivots from measured grid to **predicted grid** across all edge tiers, populated from published inference benchmarks.
- Exp 3.5 **promoted from stretch to required**, repurposed as a field-laptop measurement anchor — the sole physical hardware measurement that calibrates the predicted grid.
- Paper framing tightened: synthesis methodology is the primary contribution; hardware is illustrative. §VII blueprint becomes a concrete **SmartWilds v2 Bill of Materials** with per-tier node counts, predicted cost, and flagged unmeasured assumptions.
- Drone leave-one-site-out (0/9 folds pass) reframed: 37 flights are few and varied, per-mission heterogeneity dominates, LOSO not applicable for this modality. Dropped from LOSO table; variance envelope remains primary defense.

---

## Contents

1. Experiment roster with ownership and dependencies
2. Per-experiment specifications
3. Case study recipes (operationalizing mosaic synthesis)
4. Synthesis fidelity protocol (the methodology-defense spec)
5. Methodology subsection: what is measured vs. modeled
6. Results-to-blueprint derivation table
7. Triage order
8. Solo-first sequencing and handoff spec
9. Ten-day timeline with checkpoints

---

## 1. Experiment Roster with Ownership

| Experiment | Role in paper | Owner | Status | Dependencies |
|---|---|---|---|---|
| Exp 1: Per-modality characterization | Produces synthesis primitives (arrival rates, burstiness, diurnal structure) consumed by Exp 6 | **Jenna** | Complete; minor reframing | None |
| Exp 2.A: Cross-modal independence | Statistical license for synthesis (Jaccard matrices) | **Jenna** | Done; write up | Exp 1 |
| Exp 2.B: Marginal value coverage | Non-redundancy hypothesis test (temporal, spatial, event-context) | **Jenna** | New work | Exp 1 |
| Exp 3: Predicted hardware tier feasibility | Predicted feasibility map (hardware × workload × policy) from published benchmarks; feeds BoM | **Anirudh** | Prediction-only (no device access); pivoted from measured | Exp 6.3 case studies; Exp 1 benchmarks; published inference numbers |
| Exp 3.5 (required): Field-laptop measurement anchor | Sole measured hardware cell; calibrates predicted grid error on the one accessible tier | **Anirudh + Jenna** | Promoted from stretch; now load-bearing | Exp 6.3; field laptop access |
| Exp 4: Policy comparison across synthesized workloads | Latency/energy/coverage Pareto fronts; includes control-theoretic extension | **Yuanyang** | Existing + extend with energy + synthesized workloads | Exp 6.3 case studies |
| Exp 5: Edge filtering storage savings | Strongest standalone result; unchanged | **Jenna** | Complete | None |
| Exp 6.1: Synthesis procedure | Core methodology; turns recorded traces into recombined workloads | **Jenna** | To build | Exp 1 primitives; Exp 2.A independence bounds |
| Exp 6.2.A: Trace-level fidelity (variance envelope + leave-one-out) | Defends synthesis at the input level | **Jenna** | To build | Exp 6.1 |
| Exp 6.2.B: Replay-level fidelity | Defends the evaluation machinery (queue, latency dist, policy ranking) | **Jenna** | To build | Exp 6.1; Exp 4 basic replay harness |
| Exp 6.3: Case study library | Four reusable coordination patterns (UC1–UC4) as synthesis recipes | **Jenna** | To build | Exp 6.1; Table II SLOs |
| Exp 6.4: Scaling and breaking points | 2×–10× intensity; identifies policy/hardware breaking points | **Anirudh + Yuanyang** | To build | Exp 6.3; Exp 3; Exp 4 |

**Coordination risk.** Exp 3, 4, 6.4 all consume Exp 6.3 outputs. If Exp 6.3 slips, downstream stalls. Highest-priority dependency: **Jenna delivering Exp 6.1 + 6.3 by Day 3**, tightly scoped handoff to Anirudh and Yuanyang on Day 4.

---

## 2. Per-Experiment Specifications

### Exp 1: Per-Modality Characterization (Jenna)

**Role reframe.** Outputs are *synthesis primitives* (parameters the synthesis engine consumes), not standalone findings.

**Inputs.** Recorded traces: camera traps (~236K images), bioacoustic monitors (1,180 records), drones (37 flights), citizen science (991 records).

**Outputs, per modality:**
- Time-varying Poisson rate model with change points at thresholds [0.8, 0.95, 0.99, 0.995]
- Burstiness parameter B, coefficient of variation CV
- Diurnal structure (24-hour profile)
- Site-level heterogeneity: **per-site distributions of B, CV, and diurnal KS distance — this is the input to the variance envelope in 6.2.A**

**Definition of done.** Per-modality JSON file with all parameters, loadable by the Exp 6.1 synthesis engine. Table IV populated.

**Done date.** Day 1.

---

### Exp 2.A: Cross-Modal Independence (Jenna)

**Existing work, write-up only.** Jaccard co-occurrence matrix at 1h, 6h, 24h windows across co-located site pairs TW02, TW06, TW07, TW09.

**Claim language.** "Negligible at deployment-relevant scales" — name the scales explicitly. This is the defense against the "artifact of sensor spacing" objection.

**Done date.** Day 1.

---

### Exp 2.B: Marginal Value Coverage (Jenna)

**New work.** Three-dimensional coverage analysis.

- **Temporal:** For each modality m, fraction of hour-of-day bins where m is the sole source of detections. Report per-modality unique-coverage percentage.
- **Spatial:** For each modality, fraction of sites where it is the sole detector in a given 24h window (averaged across deployment). Report heatmap.
- **Event-context:** Bin detections by confidence tier (low/med/high). For each modality, fraction of confidence-tier bins uniquely covered. **Drop first if time-tight.**

**Outputs.**
- 4×4 Jaccard matrices at each time window (heatmaps)
- Per-modality unique-coverage percentages: temporal, spatial, (event-context optional)
- One combined figure: "non-redundant coverage across dimensions" (small multiples)

**Done date.** Day 2.

---

### Exp 3: Predicted Hardware Tier Feasibility (Anirudh)

**Scope pivot (v2.1).** No Jetson or Pi hardware accessible this cycle. Exp 3 is **prediction-only** across all edge tiers, populated from published inference benchmarks. The field laptop (Exp 3.5) is the sole measured tier, anchoring prediction error. Every hardware claim in the paper carries an explicit "(predicted)" qualifier except the laptop-tier anchor. This matches the paper's intended use case: predicting hardware feasibility before procurement, which is the point of the methodology.

**Role reframe.** "Across hardware × workload × policy, where are the predicted-feasible cells, and what is our calibrated confidence in those predictions?"

**Hardware tiers (all predicted, one measured):**
- Tier 1: Workstation GPU (RTX-class) — baseline; *predicted* from published benchmarks
- Tier 2: Jetson Orin Nano — mid-tier edge; *predicted*
- Tier 3: Raspberry Pi 5 + Coral TPU / Pi 4 CPU — low-tier edge; *predicted*
- Tier 0 (anchor): Jenna's field laptop — **measured** in Exp 3.5

**Prediction inputs.** Per tier × per model (BirdNET, YOLO+SAHI, SAM3, BioCLIP, MegaDetector): published inference latency, device TDP, memory. Source cited per cell (model card, paper, manufacturer spec).

**Workloads.** Consume Exp 6.3 case studies.
- Baseline: replay of recorded traces
- CS1 (CT→Drone) at 1×, 2×, 10× intensity
- CS2 (Acoustic→CT) at 1×, 2×, 10×
- CS3, CS4 at 1× only (time permitting)

**Per cell, report:**
- Predicted aggregate utilization % (>100% = load shedding required)
- Predicted P95 latency vs. SLO target
- Predicted bottleneck modality
- Predicted feasibility: `feasible / degraded / infeasible`

**Definition of done.** Predicted feasibility grid (CSV + heatmap). §VII blueprint pulls *predicted* hardware recommendations from this; the SmartWilds v2 BoM is expressed as "predicted to meet SLOs, pending physical validation for non-laptop tiers."

**No scope reduction lever needed.** All tiers are cheap to populate from published numbers. Keep all four.

**Done date.** Day 7.

---

### Exp 3.5: Field-Laptop Measurement Anchor (Anirudh + Jenna)

**Promoted from stretch to required (v2.1).** With no edge hardware accessible, the field laptop is the sole physical measurement point anchoring the predicted grid. Without this calibration, every hardware claim in the paper is pure simulation. This is what keeps the methodology honest.

**Purpose.** Calibrate prediction error on the one tier we can physically measure, so reviewers can see the predicted grid is anchored, not pure extrapolation. Paper framing: "we measured on the tier accessible to us; edge-tier predictions are explicit hypotheses for future deployment to test."

**Protocol.**
- Case study: CS1 (CT→Drone — most concurrency-stressful; feeds §VII BoM directly).
- Hardware: Jenna's field laptop. Document CPU, GPU (if any), RAM, OS in a `laptop_spec.md` and in Table V.
- Policy: adaptive (the one most likely to be deployed).
- Run YOLO (or MegaDetector) + BirdNET concurrently on the device against the CS1 1× replay trace.
- Measure: wall-clock end-to-end latency distribution (P50, P95, P99), memory pressure peaks, thermal behavior if observed.
- Compare measured P95 to the laptop-tier *predicted* P95 for the same cell. Report the gap as calibration error.

**Paper wording.** "Predicted P95 on laptop-class hardware: X ms. Measured P95 on the field laptop under the same workload: Y ms. Calibration error: |X−Y|/X = Z%. We treat this as a lower bound on prediction error; edge-tier predictions (Jetson, Pi) are flagged as hypotheses for next-cycle measurement in §VII.F."

**Definition of done.** One paired measurement in hand; one paragraph in §VI.B reporting the gap; §VII.F names edge-tier validation as the priority item for SmartWilds v2.

**Fallback.** If models don't run on the laptop as configured (library/driver issues), pare back to BirdNET-only or YOLO-only measurement rather than fake the data. Document constraints honestly.

**Done date.** Day 8.

---

### Exp 4: Policy Comparison Across Synthesized Workloads (Yuanyang)

**Role reframe.** Adds energy axis and synthesized workloads. Control-theoretic extension becomes a fourth policy.

**Policies:**
- Process-all (baseline)
- Event-triggered (motion + high-confidence acoustic)
- Adaptive (rate-based escalation)
- Control-theoretic (Yuanyang's Lyapunov-based extension)

**Metrics per policy:**
- P95 latency
- **Energy per event** (inference energy model: E = latency × device power, per stage)
- Coverage % against SLO
- Compute budget % (normalized to process-all)

**Workloads.** Same grid as Exp 3 columns.

**Output.** Pareto front per workload across (latency, energy, coverage). Headline to land: *policy ranking is workload-dependent — adaptive wins at baseline, event-triggered wins at high intensity* (or similar).

**Scope reduction lever.** If control-theoretic doesn't converge, drop to three policies and flag as ongoing work.

**Done date.** Day 8.

---

### Exp 5: Edge Filtering Storage Savings (Jenna)

**Unchanged.** 97.5% blank rate, 40.5× throughput reduction, 96.88% storage saved.

**Done date.** Day 1 (write-up only).

---

### Exp 6.1: Synthesis Procedure (Jenna)

**Core methodology.** Takes Exp 1 primitives + Exp 2.A independence bounds + a case study recipe (Exp 6.3), produces a synthetic trace.

**Algorithm:**
1. Load per-modality rate model, diurnal structure, site-variance from Exp 1
2. Load independence bounds from Exp 2.A (at what time-window scale can modalities be treated as independent?)
3. Parse case study recipe: modality mix, density, intensity multiplier, duration
4. For each modality: draw Poisson realizations using the fitted rate model, scaled by intensity multiplier. Preserve diurnal structure.
5. Concatenate modality traces under the independence assumption — the "mosaic" step
6. Apply the case study's SLO chain: for trigger-response recipes, insert response-modality events conditioned on trigger-modality detections within the latency window
7. Output unified event log with same schema as recorded traces (downstream tooling works without modification)

**Definition of done.** A function `synthesize(recipe, primitives, independence_bounds) → event_log` that is deterministic given a seed and reproduces recorded-trace statistics when the recipe is "identity."

**Done date.** Day 3. (Hard deadline — gates handoff.)

---

### Exp 6.2.A: Trace-Level Fidelity (Jenna)

**Two-part defense:** variance envelope (primary) + leave-one-site-out (secondary).

#### Variance envelope (primary argument)

**The idea.** If the variance within a real modality (across sites) is comparable to the variance introduced by synthesis recombinations, then synthesis isn't introducing distortion beyond what the modality itself naturally exhibits.

**Protocol.**
1. For each modality, compute per-site distributions of B, CV, and diurnal KS distance from Exp 1. This is the **natural variance envelope**.
2. Run the synthesis engine with N different seeds on the same recipe; measure B, CV, diurnal KS across the synthesized runs. This is the **synthesis variance**.
3. Compare: if synthesis variance ≤ natural variance on each metric, synthesis operates within the modality's own distribution.
4. Report as a paired plot: natural range (from real sites) vs. synthesis range (from seeds), per metric per modality.

**This is the strongest defensibility argument.** Reviewers can't easily dismiss "we're not introducing more variance than your own sites already exhibit."

#### Leave-one-site-out (secondary argument)

For each modality with ≥3 sites, hold one out, synthesize from the rest, compare against held-out. Report fidelity metric pass rate across the fold.

**Drone excluded (v2.1).** 37 flights are few and varied (different dates, aircraft configs, flight paths); per-mission heterogeneity dominates, so each "fold" is effectively comparing the synthesis against a different modality. LOSO is not a meaningful test for this data structure. Drone is dropped from the LOSO pass/fail table with a footnote explanation; variance envelope (primary) still applies and passes.

**Fidelity metrics and thresholds:**

| Metric | Definition | Pass threshold |
|---|---|---|
| Burstiness preservation | `|B_synth − B_real|` | ≤ 0.05 |
| CV preservation | `|CV_synth − CV_real| / CV_real` | ≤ 0.15 |
| Diurnal structure | KS distance between hour-of-day distributions | ≤ 0.15 |
| Independence preservation | `|J_synth − J_real|` (Jaccard at 24h) | ≤ 0.05 |
| Post-filter rate | `|r_synth − r_real| / r_real` (camera traps only) | ≤ 0.20 |

**Interpretation guardrail.** If leave-one-out results are mixed but variance envelope holds, the framing is: "synthesis operates within the natural variance of the modality; leave-one-out deviations fall within the site-to-site variance already observed." This is scientifically honest and defensible.

**Done date.** Day 5.

---

### Exp 6.2.B: Replay-Level Fidelity (Jenna)

**Purpose.** Trace-level fidelity (6.2.A) shows the input is faithful. Replay-level fidelity shows the *evaluation machinery* is faithful — that running policies on synthesized traces produces the same system behavior (queue buildup, latency distributions, policy rankings) as running on recorded traces.

**Why this matters.** A reviewer can accept that synthesized traces have the right statistics and still ask: "but do policies behave the same on your traces as they would on real deployments?" This is the experiment that answers that.

**Protocol.**

**Part A — Identity trace (zero-generalization baseline).** For each policy (process-all, event-triggered, adaptive, control-theoretic):

1. Run the policy on the full recorded trace (Campaign 2, Aug 4–28). Record:
   - Queue depth distribution (time series)
   - End-to-end latency distribution (P50, P95, P99)
   - SLO compliance rate
2. Run the same policy on a synthesized trace with recipe = "identity" (synthesis from full primitives, no cross-site recombination, no intensity scaling). Record same metrics.
3. Compare:
   - **Queue buildup:** KS distance between queue depth distributions ≤ 0.15
   - **Latency distribution:** ratio of P95 values within 15%; KS distance ≤ 0.15
   - **SLO compliance:** absolute difference in compliance rate ≤ 5 percentage points

**Part B — Case studies (generalization levels 1–3).** Same four policies, run on **CS1 and CS2 traces at 1× intensity**. No recorded comparand exists for these coordination patterns (they are the synthesis counterfactual). Report:
- Per-policy per-case-study metrics (queue, latency P50/P95/P99, SLO compliance, energy per event).
- Cross-seed stability: same case study at 3–5 seeds, confirm queue/latency distributions are consistent (KS distance across seeds ≤ 0.10).
- **Harness invariance:** confirm Part-B runs use the identical replay harness, policy implementations, and metric definitions as Exp 4 Pareto analysis. (If Part B produces different numbers from Exp 4 on the same inputs, there is a harness bug to fix before writeup.)

**Part C — Policy ranking invariance (the load-bearing result).**
- On Part A (identity): rank the four policies by each metric on recorded vs. synthesized; report Kendall's tau.
- On Part B (CS1, CS2): rank the four policies by each metric across seeds; confirm the ranking is stable (Kendall's tau ≥ 0.8 across seeds).
- Cross-case-study: do the same policies win on CS1 as on CS2, or does the ranking depend on the workload? This is a *finding*, not a fidelity test — but it's what §VII.D policy recommendations will draw from.

**The load-bearing claim.** "The *decisions a practitioner would make* from MOSAIC-synthesized workloads are stable: identical on identity traces (Part A), consistent across seeds on case-study traces (Part B), and workload-sensitive in the way the paper reports (Part C)."

**Definition of done.**
- Part A: validation table (per-policy match on queue, latency, SLO) + one rank-concordance number.
- Part B: per-case-study per-policy metrics table; cross-seed stability confirmed.
- Part C: Kendall's tau on identity; cross-seed tau on CS1/CS2; cross-case-study ranking note.
- Harness used is the same as Yuanyang's Exp 4 harness — verified by re-running one Exp 4 cell and matching numbers to Exp 4's output.

**Done date.** Day 6.

---

### Exp 6.3: Case Study Library (Jenna)

See Section 3 below — case study recipes are the deliverable.

**Done date.** Day 4. **(Hard deadline — gates handoff to Anirudh and Yuanyang.)**

---

### Exp 6.4: Scaling and Breaking Points (Anirudh + Yuanyang)

Runs on top of Exp 6.3. For each case study, scale intensity by 2×, 5×, 10×. For each scale factor, run through Exp 3 (hardware feasibility) and Exp 4 (policy comparison).

**Output.** Breaking point report: per case study, intensity at which each hardware tier loses feasibility under each policy.

**Definition of done.** Table of breaking points; one summary figure.

**Done date.** Day 9.

---

## 3. Case Study Library (Exp 6.3)

Operationalizing the mosaic intuition: a case study is a **recipe**, not a trace.

| Case | Coordination pattern | Synthesis recipe | SLO chain | Systems property exercised |
|---|---|---|---|---|
| **CS1** | Camera trap → Drone | Concatenate CT motion-trigger bursts from high-activity sites with drone flight windows keyed to detections. Drone events synthesized as response traces within 5s of CT detection. | CT detection → drone dispatch, 5s | Burst response under cross-modal trigger |
| **CS2** | Acoustic → Camera Trap | Interleave acoustic detection events (BirdNET high-confidence) with CT sensitivity-raised response windows. Recipe simulates CT trigger rate doubling for 60s after each acoustic detection. | Acoustic detection → CT sensitivity, 2s | Fine-grained trigger latency; state change propagation |
| **CS3** | Focal CT → CT Network | Synthesize multi-site CT traces under corridor-movement assumption: detection at site S_i raises trigger probability at adjacent S_{i±1} within 10s window. Recombine traces from adjacent sites. | CT detection → network activation, 10s | Multi-node coordination; propagation under network constraints |
| **CS4** | Citizen Science → All | Inject citizen-science events as sampling priors. Scale all modality rates conditional on citsci-active vs. idle periods. Recipe operates at hour-level granularity. | CitSci → all modalities, 60s | System-wide adaptive response; slowest-cadence trigger |

**Triage note.** If time forces reduction, keep CS1 and CS2 (tightest SLO chains, clearest cross-modal coordination). CS3 is valuable for the multi-node story but can be sketched as future work. CS4 has the softest latency budget and is the most forgiving to synthesize imperfectly.

**Common recipe structure.** Every case study specifies:
1. Primary trigger modality (where events originate)
2. Response modality or modalities (what the trigger activates)
3. Temporal coupling (latency budget for trigger-to-response)
4. Synthesis combinator: `concatenate`, `interleave`, `conditional_scale`, or `prior_inject`
5. Intensity scaling parameter (passed through from Exp 6.4)

This gives the synthesis engine a small, well-defined interface. New case studies in future work add new combinators; everything else is reusable.

---

## 4. Synthesis Fidelity Protocol (Exp 6.2) — Full Spec

Written out because this is the paper's most important defensive result.

### 6.2.A Trace-level fidelity

- **Primary:** within-modality variance envelope (compare synthesis variance to natural site-to-site variance)
- **Secondary:** leave-one-site-out with the five fidelity metrics and thresholds in the Exp 6.2.A table above
- **Sanity:** identity test — synthesize with full real input, zero generalization; must match recorded statistics within tight tolerance

### 6.2.B Replay-level fidelity

- Queue buildup distribution comparison (KS distance)
- Latency distribution comparison (P50, P95, P99 ratios and KS)
- SLO compliance rate comparison
- Policy ranking invariance (Kendall's tau across policies)

### Generalization sweep (produces the fidelity-vs-generalizability tradeoff curve)

Synthesis at progressively more generalized recipes:
- Level 0: identity (sanity baseline)
- Level 1: cross-site recombination within modality
- Level 2: + intensity scaling
- Level 3: + modality-mix changes

For each level, report trace-level and replay-level fidelity metrics. The plot is fidelity (y) vs. generalization level (x). **This is the headline methodology figure in the paper.**

### What to say if fidelity results are mixed

If some metrics fail some thresholds, the framing becomes: "the fidelity criterion identifies which synthesis regimes are trustworthy for which downstream questions." Different metrics defend different downstream uses — burstiness preservation defends provisioning claims, replay fidelity defends policy-ranking claims. A synthesis that fails on one but passes on others is still useful for a subset of questions.

---

## 5. Methodology Subsection (Section III.B): What Is Measured vs. Modeled

**Drop this into the paper as a standalone subsection, ~200 words.** It defuses the "measured, simulated, or executed under contention" reviewer question preemptively.

**Draft text:**

> Before detailing the MOSAIC framework, we distinguish the epistemic status of its components. **Recorded traces** (Section III) are *measured* directly from the field deployment; they are empirical observations with instrumentation-level fidelity. **Synthesis primitives** (Exp 1) are *fitted* from measured traces using standard statistical procedures (change-point detection, Poisson fitting, diurnal decomposition) and carry the uncertainty inherent to parameter estimation. **Synthesized traces** (Exp 6.1) are *modeled* from fitted primitives under explicit assumptions (modality independence at specified scales, burstiness preservation across sites); their validity is established by the fidelity protocol of Exp 6.2. **Policy evaluations** (Exp 4) are *simulated* on synthesized traces using an event-driven replay harness; their replay-level fidelity is established by Exp 6.2.B. **Hardware feasibility** (Exp 3) is *predicted* from published inference benchmarks combined with synthesized workloads; predictions are calibrated against measurement on one physically accessible tier — a field laptop — in Exp 3.5, with edge-tier predictions (Jetson, Pi) flagged as hypotheses for next-cycle validation. We are explicit about this stack because the scientific load each component bears differs: measured traces carry the workload observation, fitted primitives carry the modeling abstraction, synthesized traces carry the counterfactual claim, simulated evaluations carry the design insight, and predicted feasibility carries the deployment implication. The fidelity protocol of Exp 6.2 is what binds the synthesis stack; the laptop-tier calibration of Exp 3.5 is what anchors the prediction stack.

Revise as needed. The key move is the *explicit ladder*: measured → fitted → modeled → simulated → predicted. Reviewers who were going to ask the question now see that you've already answered it.

---

## 6. Results-to-Blueprint Derivation Table

Every claim in Section VII needs a specific result pointer. Fill in during results.

| Blueprint claim | Derived from | Specific number / finding |
|---|---|---|
| Headroom factor per modality | Exp 1 burstiness parameters | CT: ≥10×; acoustic: ≥4×; drone: ≥2× [populate] |
| Post-filter provisioning target | Exp 5 blank rate | 1.94 images/hour (vs. 78.59 raw) |
| Hardware tier recommendation *(predicted)* | Exp 3 predicted feasibility grid | Jetson-class predicted-sufficient post-filter; Pi-class predicted-sufficient for acoustics [populate] |
| Prediction-to-reality gap (laptop tier only) | Exp 3.5 field-laptop anchor | Predicted laptop P95 vs. measured laptop P95; calibration error Z% [populate] |
| **SmartWilds v2 Bill of Materials** | Exp 3 predicted grid + Exp 5 filtering + Exp 2.B marginal value + Exp 6.4 breaking points | Per-tier node counts, predicted cost, flagged unmeasured assumptions [populate] |
| Every modality is provisioning-relevant | Exp 2.B marginal value | Per-modality unique-coverage %: CT 78% spatial, BA 75% spatial [populate remaining] |
| Policy recommendation | Exp 4 Pareto fronts | Adaptive wins at baseline; event-triggered at ≥5× [populate] |
| Policy decisions transfer to synthesized workloads | Exp 6.2.B policy ranking invariance | Kendall's tau [populate] |
| Coordination latency budget *(predicted)* | Exp 6.4 predicted scaling + Table II SLOs | Fog-node tier predicted-required for CS1; workstation-local predicted-sufficient for CS4 [populate] |

**Writing rule for Section VII.** Every claim gets a backward reference: "headroom factor 10× for camera traps (Section IV.B, Table IV)." No unreferenced assertions.

---

## 7. Triage Order — What Gets Cut First

Ordered from "drop first" to "protect at all costs." Updated for v2.1 (no edge hardware; synthesis-primary framing).

1. **Event-context dimension in Exp 2.B.** Temporal and spatial required; event-context nice-to-have. *(Already dropped — temporal + spatial complete.)*
2. **Control-theoretic policy in Exp 4.** If it doesn't converge, drop to three policies.
3. **Case studies CS3 and CS4 in downstream experiments.** Traces generated; but if Exp 3/4 tight, run only CS1 and CS2 through the predicted grid and Pareto.
4. **Exp 6.4 at 5× intensity.** Report 1×, 2×, 10× only.
5. **Independence preservation metric in Exp 6.2.A.** The other four are more central.
6. **Leave-one-site-out in Exp 6.2.A.** Variance envelope is primary; LOSO is diagnostic. Drone already excluded from LOSO.
7. **(Protect) Exp 6.1 synthesis procedure.** Cannot be cut — core contribution.
8. **(Protect) Exp 6.2.A variance envelope.** Cannot be cut — primary fidelity defense.
9. **(Protect) Exp 6.2.B replay-level fidelity.** Cannot be cut — policy ranking invariance is load-bearing for simulated-policy claims.
10. **(Protect) Exp 2.B marginal value (temporal + spatial).** Cannot be cut — pillar result.
11. **(Protect) Exp 3.5 field-laptop anchor.** *(Newly protected in v2.1.)* Sole hardware measurement; without it, every hardware claim in the paper is pure simulation. Fallback = single-model measurement (BirdNET-only or YOLO-only), not drop.

**Items removed from the triage list:** "Hardware Tier 2 (Jetson)" — all tiers are now cheap predictions, no reason to drop. "Exp 3.5 as stretch" — promoted to protected tier.

---

## 8. Solo-First Sequencing and Handoff Spec

Jenna runs the initial experiments solo through Day 3, then hands off tightly scoped work to Anirudh and Yuanyang.

### Solo phase (Days 1–3)

**Day 1:**
- Exp 1 primitives exported to JSON (one file per modality)
- Exp 2.A Jaccard matrices computed and written up
- Exp 5 write-up

**Day 2:**
- Exp 2.B marginal value: temporal + spatial coverage

**Day 3:**
- Exp 6.1 synthesis engine running; passes identity test (synthesize(identity_recipe, primitives) matches recorded statistics within tight tolerance)
- Exp 6.3 CS1 and CS2 recipes implemented as code; CS3 and CS4 specified but not yet implemented

### Handoff artifacts (end of Day 3)

**To Anirudh:**
- `synthesize()` function with documented interface
- Two working case study recipes (CS1, CS2) producing synthesized event logs
- Hardware benchmark table scope: compile published inference latency + TDP for {BirdNET, YOLO+SAHI, SAM3, BioCLIP, MegaDetector} × {RTX workstation, Jetson Orin Nano, Pi 5 + Coral, Pi 4 CPU, field laptop}. Cite one source per cell.
- Clear spec (v2.1): "build a *prediction model* from the benchmark table; run it across hardware × workload × policy; produce the *predicted* feasibility grid. No device access required. Then measure the CS1 1× workload on Jenna's field laptop (Exp 3.5) for the one physical calibration cell."

**To Yuanyang:**
- Same `synthesize()` function
- Same case study recipes
- Replay harness interface (takes event log, runs policy, emits queue/latency/coverage/energy metrics)
- Clear spec: "produce Pareto fronts across four policies × three workloads; energy model E = latency × device power per stage"

### Parallel work during solo phase

**Anirudh (Days 1–3):**
- Published benchmarks table: BirdNET, YOLO+SAHI, SAM3, BioCLIP, MegaDetector across {RTX, Jetson Orin Nano, Pi 5 + Coral, Pi 4 CPU, field laptop}
- Energy model scaffolding (power numbers per device tier)
- Prep field-laptop measurement environment (install YOLO + BirdNET runtimes on Jenna's laptop) for Exp 3.5 anchor

**Yuanyang (Days 1–3):**
- Energy model instrumentation in the replay harness
- Control-theoretic policy implementation (standalone; will plug into replay harness on Day 4)

### Post-handoff phase (Days 4–10)

- Jenna: Exp 6.2.A + 6.2.B + writing + CS3/CS4 (as time permits)
- Anirudh: Exp 3 grid + Exp 6.4 hardware dimension + Exp 3.5 if hardware accessible
- Yuanyang: Exp 4 Pareto + Exp 6.4 policy dimension

---

## 9. Ten-Day Timeline with Checkpoints

| Day | Milestone | Deliverables |
|---|---|---|
| 1 | Primitives exported | Exp 1 JSON files (Jenna); Exp 2.A write-up (Jenna); Exp 5 write-up (Jenna); Anirudh hardware benchmark table started; Yuanyang energy model scaffolding |
| 2 | Marginal value done | Exp 2.B temporal + spatial (Jenna) |
| 3 | **Synthesis handoff** | Exp 6.1 synthesis engine working + identity test passed; CS1 + CS2 recipes implemented (Jenna) → **handoff to Anirudh and Yuanyang** |
| 4 | Downstream started | Anirudh begins Exp 3 grid on CS1/CS2; Yuanyang begins Exp 4 Pareto; Jenna begins Exp 6.2.A |
| 5 | Trace fidelity validated | Exp 6.2.A variance envelope + leave-one-out complete (Jenna) |
| 6 | Replay fidelity validated | Exp 6.2.B complete; policy ranking invariance result in hand (Jenna); Jenna writing day |
| 7 | Predicted grid done | Exp 3 predicted feasibility grid complete (Anirudh); Table V first draft |
| 8 | Policy Pareto + laptop anchor | Exp 4 complete with energy axis (Yuanyang); Exp 3.5 field-laptop measurement complete (Anirudh + Jenna) — calibration gap in hand |
| 9 | Scaling + breaking points | Exp 6.4 complete (Anirudh + Yuanyang) |
| 10 | Integration + submission | All figures in paper; blueprint section written from derivation table; final anonymization pass; **submit** |

### Critical path dependencies

- **Day 3 (Exp 6.1)** gates everything downstream. If it slips to Day 4, cascade is recoverable. If Day 5, triage kicks in.
- **Day 4 (Exp 6.3)** gates Exp 3, 4, 6.4. Same cascade logic.
- **Day 5 (Exp 6.2.A)** and **Day 6 (Exp 6.2.B)** are the paper's methodological defense. If these slip, the methodology lands but reviewers will find the hole.

### Checkpoints with advisors

- **End of Day 2:** share Exp 2.B marginal value results. Pillar result — get advisor eyes on it early.
- **End of Day 3:** share synthesis engine identity-test output. If it doesn't match recorded statistics, fix immediately — everything downstream depends on it.
- **End of Day 6:** share trace + replay fidelity results. If fidelity is bad, framing pivots early.
- **End of Day 8:** share integrated draft of experimental sections. Last window for substantive feedback.

---

## Key additions in v2 (summary)

1. **Variance envelope** as primary fidelity argument in 6.2.A — stronger than leave-one-out alone
2. **Replay-level fidelity (6.2.B)** — queue, latency, policy ranking invariance
3. **Methodology subsection** (Section III.B) — explicit measured/modeled/simulated/predicted ladder
4. **Real-hardware calibration (Exp 3.5)** — stretch goal with highest defensive value
5. **Solo-first sequencing** — Jenna runs Days 1–3 alone, then tight handoff to team on Day 4
6. **Updated triage** — variance envelope and replay fidelity now in the protect-at-all-costs tier

## Key changes in v2.1 (2026-04-23)

1. **Exp 3 pivots to prediction-only.** No Jetson/Pi hardware this cycle; predicted grid across all edge tiers from published benchmarks.
2. **Exp 3.5 promoted to required** and repurposed as field-laptop measurement anchor (sole physical tier; calibrates prediction error).
3. **Paper framing:** synthesis methodology is the primary contribution; hardware is illustrative. §VII blueprint becomes a concrete SmartWilds v2 Bill of Materials.
4. **Drone LOSO dropped** from the pass/fail table with footnote explanation (per-mission heterogeneity); variance envelope remains primary defense for drone.
5. **Triage updated:** Tier 2 (Jetson) no longer drop-first (all tiers are cheap predictions); Exp 3.5 moved into the protect tier.
