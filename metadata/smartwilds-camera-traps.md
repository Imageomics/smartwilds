---
license: cc0-1.0
language:
- en
pretty_name: SmartWilds Camera Traps (The Wilds 2025)
task_categories:
- object-detection
- image-classification
tags:
- biology
- ecology
- biodiversity
- camera-trap
- darwin-core
- smartwilds
- the-wilds
- ohio
size_categories:
- 100K<n<1M
description: >-
  235,778 processed camera-trap images from The Wilds conservation center
  (Ohio, USA), June-August 2025. The release contains 72,775 retained animal
  bounding boxes with original SAM3 geometry, labels from Resolve–Clear–Defer
  prototype triage and targeted human taxonomic corrections, and 19,785 Darwin
  Core Events.

configs:
- config_name: occurrences
  data_files: data/occurrences.csv
- config_name: events
  data_files: data/events.csv
- config_name: images
  data_files: data/images.csv
---

# Dataset Card for SmartWilds Camera Traps

This camera-trap component of **SmartWilds** contains the complete processed
image inventory collected at The Wilds in summer 2025, corrected image
timestamps, deployment metadata, and a curated operational animal-detection
table.

## Dataset Details

| Resource | Count | Description |
|---|---:|---|
| Processed image inventory | 235,778 | All valid processed camera images, including images without retained animal boxes. |
| Camera Events | 19,785 | One Project, 12 SensorDeployments, and 19,772 per-image Events. |
| Retained operational Occurrences | 72,775 | Animal bounding boxes, each with original SAM3 proposal geometry. |
| Images with retained Occurrences | 19,726 | Images referenced by one or more retained operational boxes. |
| Zero-occurrence Image Events | 46 | Legitimate Image Events with no retained operational box. |
| Curated images approved for upload after human privacy review | 31 | Screened candidates human-reviewed and approved for upload. |

The Event hierarchy is rooted at `TheWilds_2025`. The camera Project is
`SmartWilds_camera_traps_curated`; its 12 SensorDeployments and 19,772 Image
Events preserve the final curated hierarchy. The image inventory is broader
than the curated Image Event subtree, so an image with `occurrence_count = 0`
does not establish animal absence.

### Files

```text
smartwilds-camera-traps/
├── data/
│   ├── events.csv                 # Darwin Core Event hierarchy
│   ├── occurrences.csv            # 72,775 retained animal boxes
│   └── images.csv                 # 235,778 processed images and corrected times
├── analysis/                      # acquisition and operational-inference traces
├── metadata/
│   ├── DATA_DICTIONARY.md
│   ├── taxonomy_mapping.csv
│   ├── deployments.csv            # per-deployment sensor settings and geolocation config
│   ├── camera_models.csv
│   ├── timestamp_summary_by_camera.csv, timestamp_summary_by_date.csv
│   └── provenance/                # annotation and release-integration records
├── scripts/                       # Darwin Core generator, georeferencing, release build
├── media_manifest.csv             # relative raw-media packaging references
└── CHECKSUMS.sha256
```

All `associatedMedia` and manifest `release_path` values are release-relative
`media/...` paths. The media manifest references raw media; it does not copy
media into this release tree.

## Annotation Method and Provenance

SAM3 generated the original animal proposals. Labels were assigned with the
Resolve–Clear–Defer prototype-triage protocol described by Potlapally et al.
(2026), using reviewed support examples to resolve, clear, or defer proposals.
The retained per-box provenance records the resulting label pathway.

| `labelProvenance` | Retained boxes | Interpretation |
|---|---:|---|
| `triage_resolved` | 70,728 | Prototype-triage machine assignment. |
| `triage_reviewed` | 1,807 | Human-reviewed triage label; 81 were targeted reviews outside numbered rounds, including banteng. |
| `triage_forced_1nn` | 199 | Small proposal unresolved after guarded triage; machine-assigned from its nearest reviewed prototype without the usual decision safeguards. |
| `human-edit` | 39 | Targeted human taxonomic correction on an existing SAM3 proposal. |
| `human-reviewed` | 2 | Targeted human review label on an existing SAM3 proposal. |
| **Total** | **72,775** | **Retained operational occurrences.** |

The 199 forced 1-NN labels correspond to small proposals remaining unresolved
after guarded Resolve–Clear–Defer triage. They were assigned the label of their
nearest reviewed prototype without the usual decision safeguards and were not
individually expert-verified. Every retained row uses original SAM3 proposal
geometry.

The taxonomy mapping in `metadata/taxonomy_mapping.csv` records the final
scientific names and ranks for the 13 project source-label classes. Broad
labels such as `bird` and `insect` remain broad rather than being generalized
beyond the evidence available for the proposal.

## Timestamps, Media, and Privacy

`data/images.csv` retains the raw timestamp, corrected timestamp, correction
method, and correction confidence for the full processed inventory. Camera
Event and Occurrence dates and times use the corrected image timestamps.

`media_manifest.csv` supplies release-relative paths and packaging status for
raw media. Privacy fields retain screening evidence and record the
human-review outcome. The 31 curated images flagged by screening were reviewed
and cleared for retention.

## Limitations

- Occurrences are detection boxes, not unique animals; repeated triggers and
  adjacent images can represent the same individual.
- The operational labels are semi-automated rather than a fully verified
  object-detection ground-truth set. The 1,807 rows with
  `labelProvenance = triage_reviewed` are the human-verified triage subset;
  machine-derived labels elsewhere in the table should not be used as a fully
  verified object-detection benchmark.
- A zero `occurrence_count` is not evidence of animal absence.

## Reproducibility

The camera tables are produced by the post-triage annotation pipeline described
above and packaged by `scripts/build_hf_release.py`, which validates original
SAM3 geometry and release-relative media paths before staging. The Darwin Core
generator and the georeferencing script are in `scripts/`.

## Annotation-protocol reference

The semi-automated labeling workflow follows [Potlapally et al. (2026),
*Resolve, Clear, or Defer: Training-Free Active Prototype Triage for Ecological
Detection Pipelines*](https://arxiv.org/abs/2611.01466).

## Citation

```bibtex
@misc{smartwilds2025_camera_traps,
  author    = {Kline, Jenna M. and Potlapally, Anirudh and Campolongo, Elizabeth G.},
  title     = {SmartWilds Camera Traps (The Wilds 2025)},
  year      = {2026},
  publisher = {Hugging Face},
  doi       = {TODO},
  url       = {https://huggingface.co/datasets/imageomics/smartwilds-camera-traps}
}
```

## Acknowledgements

We thank Dan Beetem, The Wilds, and the Columbus Zoo & Aquarium. Supported by
the Imageomics Institute (NSF #2118240), ICICLE (NSF #2112606), and the ABC
Global Center (NSF #2330423; NSERC #585136).

## Dataset Card Contact

Jenna M. Kline ([kline.377@osu.edu](mailto:kline.377@osu.edu))
