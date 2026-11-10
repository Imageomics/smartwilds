# What the dataset enables

Clean, aligned metadata is not an end in itself. These are the kinds of work
that the SmartWilds tables support, each using a different property of them.
The first three have published or submitted papers behind them.

## Comparing modalities for ecological findings

Camera traps and acoustic recorders share site codes and a corrected time
base, so activity patterns recovered independently by vision and by sound can
be compared without manual labels. *Cross-Modal Corroboration for
Annotation-Free Wildlife Monitoring* ([Pillai et al., 2026](https://arxiv.org/abs/2606.21613))
shows that vision-based detection and acoustic vocalization analysis
independently recover Milu deer activity patterns consistent with the
species' known ecology, using expert knowledge of those patterns as the
validation signal. The [joining guide](../datasets/joining.md) gives the keys
and a worked site-hour example.

## Benchmarking computer-vision and labeling pipelines

The camera-trap tables keep every label's provenance (`triage_resolved`,
`triage_reviewed`, `triage_forced_1nn`, `human-edit`, `human-reviewed`) and
the original proposal geometry, and the release documents human-annotated
reference sets for camera traps (2,067 boxes) and drones (27,159 boxes). That
is what lets a labeling method be evaluated rather than just applied.
*Resolve, Clear, or Defer: Training-Free Active Prototype Triage for Ecological
Detection Pipelines* ([Potlapally et al., 2026](https://arxiv.org/abs/2611.01466))
developed and evaluated the semi-automated triage that produced the current
camera-trap labels; the per-rank accuracy of the drone labels is measured
against the drone reference set (supplement, S9). When the media are released,
the same tables become detection, classification, and tracking benchmarks with
known label quality.

## Planning cross-modal sensing systems

Second-level timestamps, sensor configurations, and confidence-scored
detections across four co-located modalities make it possible to characterize
each modality's workload, synthesize the workload a coordinated system would
produce, and predict which hardware tier can carry it. *A Blueprint for
Cross-Modal Coordination at the Far Edge* does this; its code and derived data
are in `analysis/cross_modal_coordination/`. See
[Cross-modal coordination](cross-modal-coordination.md).

## Biodiversity monitoring and detectability

The Occurrence tables give species occurrence and relative activity per site,
hour, and date for every modality, with the sensor configuration that
produced each record. That supports diel activity analysis, species richness
and detection-frequency comparison across sensors, and the question of how
detectability depends on camera trigger mode, recorder schedule, flight
altitude, or visitor attention. Multi-sensor fusion for biodiversity
assessment on these tables is in preparation.

## Designing sensor deployments

Which modality uniquely covers which places and hours (sensor marginal value),
how co-located sensors overlap, and how burstiness changes with the number and
spacing of sites are all answerable from the Event hierarchy and the arrival
traces. Those answers feed the next deployment: where to place sensors, which
to co-locate, and what each adds.

## Methods for integrating heterogeneous field data

The 22-item [defect inventory](../DEFECT_INVENTORY.md), the 18 timestamp
reconstruction methods, the telemetry mapping across three drone platforms,
and the raw-inventory reconciliation are a documented worked case of turning
four uncoordinated sensor streams into one standards-compliant release. The
paper under review, *SmartWilds: Integrating, Aligning, and Documenting
Multi-Modal Field Sensing Data*, is about this, and the
[agent documentation](../agents/index.md) shows how to repeat it with LLM
coding agents.

Each dataset card lists the tasks its tables support under *Supported Tasks
and Applications*.
