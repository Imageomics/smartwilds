# SmartWilds camera traps: release note

The canonical camera-trap release is the `smartwilds-camera-traps` dataset
(release build 2026-11-08). It contains 72,775
retained animal bounding boxes with original SAM3 proposal geometry, 19,785
camera Events, and the complete 235,778-image inventory. The canonical merged
multimodal tables have 22,242 Events and 401,602 unique Occurrences.

SAM3 generated the original proposals. Resolve–Clear–Defer prototype triage
used reviewed examples to classify or defer proposals, and label provenance is
preserved per box. Every retained occurrence preserves original SAM3 proposal
geometry; targeted taxonomic corrections to existing proposals are retained.

The full inventory remains available and its image-level occurrence counts are
recomputed for this release. A zero count does not establish animal absence.
Privacy fields retain screening evidence and record the human-review outcome.
The 31 curated images flagged by screening were human-reviewed and approved
for upload.

## Method citation

The semi-automated labeling workflow follows [Potlapally et al. (2026),
*Resolve, Clear, or Defer: Training-Free Active Prototype Triage for Ecological
Detection Pipelines*](https://arxiv.org/abs/2611.01466).
