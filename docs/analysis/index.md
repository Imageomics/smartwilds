# What the metadata enables

Clean, aligned metadata is not an end in itself. Three kinds of work have
already been built on the SmartWilds tables, each using a different property
of them.

## Planning cross-modal sensing systems

Second-level corrected timestamps, sensor configurations, and confidence-scored
detections across four co-located modalities make it possible to characterize
each modality's workload, synthesize the workload a coordinated system would
produce, and predict which hardware tier can carry it. *A Blueprint for
Cross-Modal Coordination at the Far Edge* does this; its code and derived data
are in `analysis/cross_modal_coordination/`. See
[Cross-modal coordination](cross-modal-coordination.md).

## Comparing modalities for ecological findings

Because camera traps and acoustic recorders share site codes and a corrected
time base, activity patterns recovered independently by vision and by sound
can be compared without any manual labels. *Cross-Modal Corroboration for
Annotation-Free Wildlife Monitoring* ([Pillai et al., 2026](https://arxiv.org/abs/2606.21613))
shows that BioCLIP-based detection and acoustic vocalization analysis
independently recover Milu deer activity patterns consistent with the
species' known ecology, using expert knowledge of those patterns as the
validation signal. The [joining guide](../datasets/joining.md) gives the keys
and a worked site-hour example.

## Benchmarking computer-vision pipelines

The camera-trap tables keep every label's provenance (`triage_resolved`,
`triage_reviewed`, `triage_forced_1nn`, `human-edit`, `human-reviewed`) and
original SAM3 geometry, and the release documents human-annotated reference
sets for camera traps and drones. That is what lets a labeling method be
evaluated rather than just applied. *Resolve, Clear, or Defer: Training-Free
Active Prototype Triage for Ecological Detection Pipelines*
([Potlapally et al., 2026](https://arxiv.org/abs/2611.01466)) developed and
evaluated the semi-automated triage that produced the current camera-trap
labels on SmartWilds; see the [camera-trap release note](../CAMERA_TRAP_RELEASE.md).

Each dataset card lists the tasks its tables support under *Supported Tasks
and Applications*.
