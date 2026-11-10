# MOSAIC — Paper Outline v1

**SEC 2026 — 12 pages + references**
*Companion to `mosaic_framing_v4.tex` and `mosaic_execution_plan_v2.md`.*

**v2.1 scope pivot (2026-04-23).** Synthesis methodology is the primary contribution; hardware is illustrative (predicted grid from published benchmarks, one tier measured on a field laptop as calibration anchor). §VII becomes a concrete SmartWilds v2 Bill of Materials with "(predicted)" qualifiers. Drone LOSO is dropped from the fidelity table with per-mission heterogeneity as the reason. See `mosaic_execution_plan_v2.md` "Key changes in v2.1" for the full diff.

---

## Structure at a glance

| § | Title | Pages | Role |
|---|---|---|---|
| I | Introduction | 1.25 | 12Q-shaped; case studies appear as motivating instances |
| II | Related Work | 1.0 | Inverted ordering: Systems → Edge AI → Multi-Modal → Ecology |
| III | The MOSAIC Framework | 2.5 | Methodology; fidelity protocol lives here, not in results |
| IV | Deployment Instantiation | 1.5 | Dedicated section; "why ecology" justification first |
| V | Characterization Results | 1.5 | What the deployment reveals about the workload class |
| VI | Synthesis Fidelity and Case Study Evaluation | 2.0 | What the framework enables; internal organization TBD |
| VII | Deployment Blueprint | 1.0 | Derived from V + VI; every claim backward-referenced |
| VIII | Discussion | 0.5 | Transfer to other domains, limitations, iterative loop |
| IX | Conclusion | 0.25 | Recap + path forward |
| | **Total** | **11.5** | **0.5 page float** |

**Case studies appear three times:**
- §I ¶3 — motivating concrete instances
- §IV.D + Table II — SLO specifications
- §VI.B — evaluation structure

**Contributions appear three times:**
- §I ¶8 — stated as bullets
- §III, IV, V-VI, VII — each contribution gets its primary section
- §IX — recapped

---

## §I. Introduction (1.25 pages, ~9 paragraphs)

Paragraphs follow the 12Q structure from v4 framing. One paragraph per question, some compressed.

### ¶1 — Q1. The technology moment
**Opening sentence:** *Advances in model compression and energy-efficient edge hardware now make concurrent AI inference across heterogeneous sensing modalities feasible in remote, resource-constrained deployments.*
**Closing:** names cross-modal coordination at the edge as what is newly possible but unrealized.

### ¶2 — Q1-Q2 bridge. The problem class
**Opening:** *This enables a new class of systems: mission-driven multi-modal edge sensing in challenging environments.*
**Work done:** names agriculture, SAR, wildfire, ecology with structural specifics. Lead comparator: agriculture.
**Closing:** "What this class has in common is a chicken-and-egg barrier to deployment..."

### ¶3 — Case studies as motivating instances
**Opening:** *Consider four concrete coordination patterns a deployed system would have to support.*
**Work done:** CS1 through CS4 each get one sentence describing the coordination pattern and SLO budget. These are the things the paper's framework has to enable.
**Closing:** "None of these patterns has been empirically evaluated at deployment; none has a documented workload; none has a provisioning basis."

### ¶4 — Q3-Q4. The chicken-and-egg
**Opening:** *The obstacle is a workload-measurement loop...*
**Work done:** names the chicken-and-egg explicitly. Consequences: guess-and-check provisioning, unanswered scheduling tradeoffs, no way to evaluate causally chained SLOs.
**Closing:** the deepest barrier — the field has no methodology for learning from one deployment to design the next.

### ¶5 — Q5. Naive replay fails
**Opening:** *The direct path — record one deployment and replay its traces — fails for two reasons.*
**Work done:** single-realization limit; metadata-poor existing datasets.

### ¶6 — Q6. The hard parts
**Opening:** *Three obstacles stand between a single recorded deployment and a workload framework usable by other systems researchers.*
**Work done:** synchronization, recomposition fidelity, causal SLO chains. One sentence each.

### ¶7 — Q7-Q8. MOSAIC solution statement
**Opening:** *We present MOSAIC, a record–characterize–synthesize framework grounded in a six-modality field deployment.*
**Work done:** three-phase structure named; the shift from replay to synthesize called out; three enabling properties (independence, metadata preservation, fidelity criteria) listed.

### ¶8 — Contributions
**Four bullets, from v4 contribution list.** Each reads as class-general with ecological instantiation.

### ¶9 — Roadmap
**Single paragraph.** "The paper is organized as follows."

### Figures/tables in §I
- **Figure 1:** The MOSAIC framework overview. Six modalities → record → characterize → synthesize → four case studies → SLO evaluation. Exists in current draft; revise per v4 framing.

---

## §II. Related Work (1.0 page)

Inverted ordering. Each subsection ends with a "what's missing" sentence.

### §II.A Systems (~0.35 page)
Edge sensing infrastructure: BioSense, AMMODs, SPARROW, WildWing, Ambience, IoT middleware.
**What's missing:** no framework for cross-modal workload characterization or synthesis.

### §II.B Edge AI (~0.30 page)
Techniques: quantization, distillation, distributed inference, adaptive pruning, workload characterization (ADAE [anon]), adaptive models (WildFit, O'Quinn et al.).
**What's missing:** existing workload characterization is single-modality; techniques are evaluated in isolation.

### §II.C Multi-Modal (~0.25 page)
Datasets and fusion: MammAlps, BuckTales, KABR, MMLA, BaboonLand; agricultural multi-modal sensing; disaster response sensor fusion.
**What's missing:** existing datasets are designed for ML benchmarking, not workload analysis; no metadata contract.

### §II.D Ecological Sensing (~0.10 page)
Brief. Drone studies, camera trap networks, acoustic monitoring, human-on-the-loop adaptive sampling.
**What's missing:** single-modality deployments; cross-modal coordination not yet attempted.

### No figures/tables in §II.

---

## §III. The MOSAIC Framework (2.5 pages)

This is the methodology section. Fidelity protocol lives here — the framework's self-defense.

### §III.A Overview (~0.25 page)
**Opening:** *MOSAIC is structured in three phases: record, characterize, and synthesize.*
References Figure 1. Names the three phases and what each produces.

### §III.B What is measured vs. modeled (~0.25 page)
**Drop in the 200-word methodology subsection from execution plan v2.**
Measured → fitted → modeled → simulated → predicted ladder.

### §III.C Record: the metadata contract (~0.35 page)
What a deployment must preserve for workload analysis:
- Fine-grained timestamps (per-event, per-modality)
- GPS coordinates (per sensor)
- Sensor configuration parameters (motion threshold, duty cycle, etc.)
- Confidence-scored detections from in-line inference
- Battery and environmental telemetry

**This is the domain-transferable contribution.** Agricultural sensors, SAR UAVs, wildfire monitoring networks can adopt this contract. Name this explicitly.

### §III.D Characterize: synthesis primitives (~0.50 page)
Three characterization outputs fed into synthesis:
1. Per-modality arrival-rate models (Exp 1 outputs)
2. Cross-modal independence bounds (Exp 2.A outputs)
3. Marginal value per dimension (Exp 2.B outputs; load-bearing for non-redundancy)

**Include:** the independence-at-resolution qualification. At what scales is independence measured? The paper's claim is bounded by those scales.

### §III.E Synthesize: the procedure (~0.60 page)
Algorithm sketch (7 steps from Exp 6.1 spec).
Recipe structure (modality mix, density, intensity, synthesis combinator).
Four combinators: concatenate, interleave, conditional_scale, prior_inject.
**This is where your mosaic intuition is operationalized.** Make the "take chunks and rearrange" metaphor explicit — mosaic as operational principle, not just name.

### §III.F Fidelity protocol (~0.55 page)
Three-part fidelity defense:
1. **Variance envelope (primary):** synthesis variance ≤ natural site-to-site variance
2. **Leave-one-site-out (secondary):** five fidelity metrics with thresholds
3. **Replay-level fidelity:** queue buildup, latency distribution, policy ranking invariance

**Why this is in methods, not results.** Fidelity is a property of the approach, not an output of a specific evaluation. Reviewers evaluate the methodology before seeing numbers.

### Figures/tables in §III
- **Figure 2:** Three-phase framework expanded. Record inputs (metadata contract), characterize outputs (primitives), synthesize inputs (recipes) + outputs (event logs). Shows the data flow.
- **Figure 3:** Synthesis algorithm flowchart or pseudocode listing.
- **Table I:** The metadata contract (what must be preserved, why).
- No tables for fidelity yet; those live in §VI.

---

## §IV. Deployment Instantiation (1.5 pages)

Dedicated section. "Why ecology" comes first so reader doesn't assume ecology is the argument.

### §IV.A Why ecology as the instantiation (~0.25 page)
**Opening:** *We develop the MOSAIC instantiation in depth for ecological sensing because this domain provides the stress test properties the framework is designed to address.*
Four stress-test properties: remote (no connectivity), power-constrained (solar + generator), event-driven (bursty arrivals), expert-dependent (semi-weekly review cycle).
**Closing:** an instantiation that produces trustworthy synthesis in this setting transfers to other domains in the class.

### §IV.B Deployment design and metadata preservation (~0.50 page)
Where, how, what. 10,000-acre conservation reserve, continental US.
How the metadata contract from §III.C was implemented in practice.
Human-on-the-loop adaptive sampling cycle: semi-weekly field review, sensor repositioning, policy adjustment.
**Closing:** all procedures documented for replicability.

### §IV.C Traces and annotation pipeline (~0.35 page)
Table III (existing): data volumes, timestamp formats, sites, status per modality.
Cross-modal synchronization pipeline: `extract_wilds_multimodal.py` (renamed to anonymized name), EXIF + CSV + flight log parsing, unified event schema.
AI-assisted annotation: YOLO, MegaDetector, BirdNET, SAM3, BioCLIP.

### §IV.D Cross-modal SLO configurations (~0.40 page)
**This is where case studies reappear, now as SLO specifications.**
Table II (existing; refined).
Four case studies as causally chained SLO configurations.
Each case study gets a short paragraph expanding what the latency budget means operationally.
**Closing:** these configurations drive the synthesis recipes (§III.E) and the evaluation (§VI).

### Figures/tables in §IV
- **Figure 4:** Site map showing sensor placements (anonymized for location). If identifying, replace with schematic.
- **Table II:** Cross-modal SLO configurations (from existing draft).
- **Table III:** Summary of data sources (from existing draft).
- **Figure 5:** Example sensing modality images — day/night camera trap, drone (existing Fig 2).

---

## §V. Characterization Results (1.5 pages)

What the deployment reveals about the workload class. Each subsection ends with the "so-what" that feeds the blueprint.

### §V.A Per-modality arrival characterization (~0.30 page)
Exp 1 results. Table IV (existing, populated).
Burstiness parameters, CV, diurnal structure per modality.
**So-what:** workloads are extremely bursty across all modalities (B ≥ 0.86); provisioning to mean rate under-provisions by ~300× during peak bursts for camera traps. Headroom-based provisioning is the correct discipline.

### §V.B Cross-modal independence (~0.25 page)
Exp 2.A results. Jaccard matrices at 1h, 6h, 24h windows.
**So-what:** negligible co-occurrence at deployment-relevant scales; this is the statistical license for synthesis recombination.
**Defensive paragraph:** independence is measured at the spatial/temporal resolution of the deployment's sensors; finer-scale coupling is a measurement-resolution question, not a framework limitation.

### §V.C Sensor marginal value (~0.45 page)
Exp 2.B results. The non-redundancy hypothesis test.
Two dimensions reported (event-context dropped in triage):
- Temporal unique coverage per modality (hour-of-day bins): CT 22.4%, BA 4.0%, drone 0.0%, citsci 3.3% [populate final]
- Spatial unique coverage per modality (sites, 24h window): CT 78%, BA 75%, drone 0%, citsci 0% [populate final]
**So-what:** every workload-relevant modality contributes uniquely covered regions; no modality is redundant at the workload level. First systems-level evidence for the "greater than the sum" hypothesis.
**Scoping language:** "at the workload level" — per-taxon biodiversity analysis stays in the companion paper.

### §V.D Edge filtering (~0.50 page)
Exp 5 results. 97.5% blank rate, 40.5× throughput reduction, 96.88% storage saved.
Table VII (existing, populated).
**So-what:** post-filter true-positive rate (1.94/hour), not raw trigger rate (78.59/hour), is the provisioning target. Edge filtering moves the regime from workstation-class to Jetson/Pi-class hardware.

### Figures/tables in §V
- **Table IV:** Cross-modal arrival rate statistics (existing).
- **Figure 6:** Jaccard matrices (heatmaps at 1h, 6h, 24h).
- **Figure 7:** Marginal value visualization. Small multiples: temporal unique coverage (bars), spatial unique coverage (heatmap), event-context (bars if included). This is the pillar-result figure.
- **Table VII:** Blank image analysis per camera (existing, populated).

---

## §VI. Synthesis Fidelity and Case Study Evaluation (2.0 pages)

Internal organization TBD pending results. Two candidate structures below; decision rule at the end.

### §VI.A Synthesis fidelity (flat, ~0.75 page)

Comes first regardless of VI.B structure. This is the methodology-defending result block.

#### §VI.A.1 Variance envelope (primary)
Exp 6.2.A variance envelope results. Paired plot: natural site-to-site variance vs. synthesis-seed variance, per metric per modality.
**Headline:** synthesis variance ≤ natural variance on B, CV, diurnal structure for all modalities.

#### §VI.A.2 Leave-one-site-out (secondary)
Exp 6.2.A leave-one-out fold. Pass/fail table across five fidelity metrics.

**Drone excluded** from the LOSO table (v2.1). 37 flights span different dates, aircraft configs, and flight paths; per-mission heterogeneity dominates, making each held-out fold effectively a different modality. Variance envelope (§VI.A.1) is the applicable defense for drone. One-sentence footnote in the table. *Optional expansion in §VIII:* if the drone-video processing overhead (SAM3 on full video) is the root cause of high per-mission variance, this finding motivates a constructive recommendation for future drone data collection — oblique + nadir high-res stills instead of video-first, capturing species ID, counts, spatial distribution, and coarse behavior cues without the processing tax.

#### §VI.A.3 Replay-level fidelity
Exp 6.2.B results. Queue distribution, latency distribution, policy ranking invariance.
**Headline number:** Kendall's tau across policies.

#### §VI.A.4 Fidelity-vs-generalization tradeoff
Exp 6.2 generalization sweep. Fidelity (y) vs. generalization level (x) curve.
**This is the systems tradeoff figure committed to in the framing.**

### §VI.B Case study evaluation (~1.25 pages) — STRUCTURE TBD

**v2.1 framing note.** All feasibility results in §VI.B are *predicted* from published benchmarks except the laptop-tier cell (Exp 3.5), which is measured. Tables and text carry "(predicted)" qualifiers consistently; §VI.B.3 reports the prediction-to-measurement calibration gap at the laptop tier.

#### Option B1: Per case study (4 subsections)
One subsection per case study. Each reports hardware feasibility (Exp 3), policy comparison (Exp 4), scaling (Exp 6.4) for that case study.
**When this structure wins:** if case studies produce *qualitatively different* stories — CS1 needs fog-node tier, CS2 works on Jetson alone, CS3 breaks under multi-node coordination. Per-case-study organization tells the reader: "here's what each coordination pattern requires."

#### Option B2: Per experiment type (3 subsections)
§VI.B.1 Hardware feasibility across case studies.
§VI.B.2 Policy comparison across case studies.
§VI.B.3 Scaling and breaking points across case studies.
**When this structure wins:** if the case studies produce *quantitatively comparable* results that benefit from direct comparison — "adaptive wins on CS1, CS2, CS3 but loses on CS4." Per-experiment organization lets the reader see patterns across cases.

#### Option B3 (hybrid): synthesis fidelity flat, then per-case-study with cross-cutting summary
§VI.A flat (as drafted).
§VI.B.1 to VI.B.4: one per case study.
§VI.B.5 Cross-case findings: 2-3 paragraphs summarizing what generalizes.
**When this structure wins:** if you want the case-study narrative but also need to surface patterns. Costs ~0.25 page more.

#### Decision rule
**Run Exp 3 on CS1 and CS2 first (as in execution plan Day 4).** If the feasibility verdicts are qualitatively different (one feasible on Jetson, one requires workstation), go B1. If they're the same, go B2 and use the space savings. If both hold partially, go B3.

### Figures/tables in §VI
- **Figure 8:** Variance envelope paired plot (natural vs. synthesis).
- **Figure 9:** Fidelity-vs-generalization tradeoff curve. **Headline methodology figure.**
- **Table V:** Edge resource model (hardware feasibility grid; from existing Table V, populated).
- **Table VI:** Policy comparison (populated with energy column added).
- **Figure 10:** Scaling breaking points per case study.
- **Possible Figure 11:** Policy ranking invariance scatter or Kendall-tau visualization.

---

## §VII. Deployment Blueprint (1.0 page)

Exactly as drafted in v4 framing. Six paragraphs with backward pointers.

### §VII.A Hardware tier *(predicted, one tier measured)*
From Exp 3 (§VI.B) — predicted grid; Exp 3.5 — field-laptop anchor. SmartWilds v2 BoM specifies **predicted** Jetson Orin Nano + Pi combinations per modality, with calibration error from the laptop-tier anchor reported as the prediction-uncertainty band. Every hardware claim in §VII carries the "(predicted)" qualifier; the laptop tier is the only measured cell.
Backward: "predicted feasibility from §VI.B.2, Table V; calibration anchor from §VI.B.3."

### §VII.B Provisioning headroom
From Exp 1 (§V.A). Per-modality headroom factors.
Backward: "burstiness from §V.A, Table IV."

### §VII.C Coordination architecture
From Exp 6.4 scaling + Table II SLOs. Fog-node tier specification.
Backward: "causally chained SLO evaluation from §VI.B, scaling from §VI.B.3."

### §VII.D Sensing policy
From Exp 4. Adaptive default, process-all fallback.
Backward: "policy comparison from §VI.B, Pareto fronts in Figure [N]."

### §VII.E Sensor composition
From Exp 2.B marginal value. All six modalities retained; siting per coverage gaps.
Backward: "marginal value from §V.C, Figure 7."

### §VII.F Open questions for the next deployment
Four questions that exceed what one recorded deployment can answer:
1. Variance across similar deployments
2. **Edge-tier validation** — Jetson-class and Pi-class predictions are hypotheses. Priority SmartWilds v2 investment: procure one Jetson Orin Nano + one Pi 5 + Coral and run CS1/CS2 under the adaptive policy; close the prediction-to-measurement gap currently anchored only at laptop tier.
3. Coordination overhead under real radio and power conditions
4. Drone collection modality tradeoff — whether oblique + nadir high-res stills close the biodiversity-information gap against video-first collection at a fraction of the processing cost. Motivated by the per-mission heterogeneity observed in §VI.A.2.

**Closing:** the framework plus this blueprint provides the empirical foundation *and a prioritized measurement plan* for SmartWilds v2; the next deployment closes the loop and feeds a second characterization cycle.

### Figures/tables in §VII
- Optional **Figure 12:** Blueprint schematic — the specified deployment with hardware, modalities, coordination links. Stretch if space allows.

---

## §VIII. Discussion (0.5 page)

### §VIII.A Transfer to other domains (~0.2 page)
One sentence per domain (agriculture, SAR, wildfire). What transfers (metadata contract, framework, independence analysis). What requires re-specification (SLO definitions, combinators for domain-specific coordination patterns).

### §VIII.B Limitations (~0.15 page)
Within-modality variance argument bounds; independence measured at specific scales; single-deployment empirical basis; **hardware feasibility is predicted for edge tiers (Jetson, Pi) and calibrated only at the laptop tier** — prediction error on edge tiers is flagged as future validation work; drone fidelity defense rests on the variance envelope since LOSO is inapplicable to this modality's per-mission data structure.

### §VIII.C Toward the next deployment (~0.15 page)
**Opening:** *To sense a system, you need a system.*
The iterative loop as closing argument. This paper is step one; the framework's value is not one-shot synthesis but iterative design.

### No figures in §VIII.

---

## §IX. Conclusion (0.25 page)

Two paragraphs.

**¶1:** Recap — problem class, chicken-and-egg, four contributions, synthesis + marginal value + blueprint as concrete outputs.

**¶2:** Path forward — next deployment enabled by this work; framework extensibility to agriculture, SAR, wildfire; closing line connecting to the iterative methodology.

---

## Figure/Table Master List

| # | Location | Content | Source |
|---|---|---|---|
| Fig 1 | §I | MOSAIC framework overview | Existing, revise |
| Fig 2 | §III.A | Three-phase framework expanded | New |
| Fig 3 | §III.E | Synthesis algorithm | New |
| Fig 4 | §IV.B | Site map or schematic | Existing or schematic |
| Fig 5 | §IV.C | Example sensing modality images | Existing |
| Fig 6 | §V.B | Jaccard heatmaps | New from Exp 2.A |
| Fig 7 | §V.C | Marginal value small multiples | **Pillar result figure** |
| Fig 8 | §VI.A.1 | Variance envelope paired plot | New from Exp 6.2.A |
| Fig 9 | §VI.A.4 | Fidelity-vs-generalization tradeoff | **Methodology headline** |
| Fig 10 | §VI.B | Scaling breaking points | New from Exp 6.4 |
| Fig 11 | §VI.A.3 | Policy ranking invariance | New from Exp 6.2.B (optional) |
| Fig 12 | §VII | Blueprint schematic | Stretch |
| Table I | §III.C | Metadata contract | New |
| Table II | §IV.D | SLO configurations | Existing |
| Table III | §IV.C | Data sources summary | Existing |
| Table IV | §V.A | Arrival rate statistics | Existing, populate |
| Table V | §VI.B | Edge resource feasibility *(predicted; laptop tier measured)* | Existing, populate |
| Table VI | §VI.B | Policy comparison | Existing, populate + add energy |
| Table VII | §V.D | Blank image analysis | Existing, populated |
| Table VIII | §VII | **SmartWilds v2 BoM** — per-tier node counts, predicted cost, measured-vs-predicted flag per cell | New, recommended |

**Figure count:** 10–12 depending on stretch items. This is at the upper end of what fits in 12 pages — may need to drop Fig 11 or Fig 12.

**Table count:** 7–8. Standard for a systems paper of this scope.

---

## Cross-Reference Map — Case Studies Through the Paper

| Case study | §I.¶3 | §III.E | §IV.D / Table II | §V | §VI.B | §VII |
|---|---|---|---|---|---|---|
| **CS1 (CT→Drone, 5s)** | Motivating instance | Synthesis recipe | SLO specification | — | Evaluation (feasibility, policy, scaling) | Blueprint: fog-node tier required |
| **CS2 (Acoustic→CT, 2s)** | Motivating instance | Synthesis recipe | SLO specification | — | Evaluation (feasibility, policy, scaling) | Blueprint: state change propagation spec |
| **CS3 (Focal CT→CT Network, 10s)** | Motivating instance | Synthesis recipe (if included) | SLO specification | — | Evaluation (reduced if scoped) | Blueprint: multi-node coordination |
| **CS4 (CitSci→All, 60s)** | Motivating instance | Synthesis recipe (if included) | SLO specification | — | Evaluation (reduced if scoped) | Blueprint: adaptive system-wide response |

---

## Cross-Reference Map — Contributions Through the Paper

| Contribution | §I.¶8 | Primary section | §VII Blueprint | §IX |
|---|---|---|---|---|
| 1. Metadata-preserving multi-modal dataset | Bullet | §III.C + §IV | Referenced | Recapped |
| 2. MOSAIC framework | Bullet | §III | Framework enables every blueprint component | Recapped |
| 3. Sensor marginal value analysis | Bullet | §V.C | Every modality is provisioning-relevant | Recapped |
| 4. Deployment blueprint | Bullet | §VII | Is §VII | Recapped |

---

## Writing sequence recommendation

Given the framing is locked and execution is Days 1–10, I'd write in this order to minimize rework:

1. **§IV (Deployment)** first — mostly reuses existing draft text; warm-up
2. **§V (Characterization)** — write as results land (Days 1–2)
3. **§III (Framework)** — can write §III.A–§III.E before Exp 6.2 results; §III.F waits for Day 5–6
4. **§VI (Evaluation)** — write per Day 7–9 as experiments complete
5. **§VII (Blueprint)** — mechanical from derivation table once V and VI are done
6. **§I (Intro)** — write last. Reason: the intro should reflect what the paper actually says, and that's only settled after V, VI, VII are done. Drafting intro early risks writing a paper the results don't support.
7. **§II, §VIII, §IX** — fit into gaps; all short

**Exception:** write the abstract early (from the v4 candidate) and keep it updated as sections land. The abstract is a forcing function for the intro.

---

## Risk flags for the outline

**§I ¶3 risk (case study introduction).** Introducing four case studies in the intro means the reader meets eight names (CS1-4 labels + coordination patterns) in the first page. Risk of overload. Mitigation: keep each to one clean sentence; reference them by number thereafter; the full descriptions wait for §IV.D.

**§III.F risk (fidelity in methods).** Putting fidelity protocol in methods rather than results is the right structural move but unusual — reviewers expect fidelity *results* in results. Mitigation: §III.F describes the *protocol*; §VI.A reports the *numbers*. Cross-reference explicitly so reviewers see both pieces.

**§IV compression risk.** If Section IV runs to 1.75 pages instead of 1.5, that's the first place to cut. The sensor type table (Table I in existing draft) is absorbable into IV.C prose if needed.

**§VI structure risk.** The TBD internal organization means §VI writing starts later than other sections. Mitigation: write §VI.A (fidelity) immediately when Exp 6.2 lands on Day 5–6 — it doesn't depend on the B1/B2/B3 decision. §VI.B organization gets decided on Day 7 when Exp 3 results land.

**Page budget risk.** 11.5 pages used + 0.5 float is tight. If experiments produce more results than anticipated, the blueprint section (VII) compresses first — it can drop to 0.75 page while keeping the backward pointers intact. Discussion (VIII) can compress to 0.35 page. Together that's 0.4 page recoverable without cutting contributions.