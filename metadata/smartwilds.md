---
license: cc0-1.0
language:
- en
pretty_name: SmartWilds (The Wilds 2025) - Study Hierarchy, Text Records, and Workload Traces
tags:
- biology
- ecology
- biodiversity
- multimodal
- sensor-networks
- darwin-core
- humboldt-eco
- fair2
- smartwilds
- the-wilds
size_categories:
- 100K<n<1M
description: >-
  The study-level component of the SmartWilds collection: the merged Darwin
  Core Event hierarchy (22,242 Events) rooted at TheWilds_2025, 401,602
  unique multimodal Occurrences, field text records and site-selection
  rationale, sensor configurations, and versioned Campaign-2 arrival traces.
---

# Dataset Card for SmartWilds

![SmartWilds sensor deployment map](images/deployment_map.png)
*Sensor deployment across The Wilds: camera traps with viewing angles, Song Meter recorders, citizen-science photo locations, and drone flight tracks. Satellite imagery © Google.*

![The same three species seen by camera trap, drone, and citizen science](images/cross_modal_preview.png)
*The same three managed focal species (Sichuan takin, Milu deer, Przewalski's horse) observed by camera trap, drone, and citizen-science photography.*


**SmartWilds** is a multi-modal sensing dataset from three 2025 field campaigns
at The Wilds (Cumberland, Ohio). Each modality has its own dataset and DOI:

| Dataset | Content |
|---|---|
| [smartwilds-camera-traps](https://huggingface.co/datasets/imageomics/smartwilds-camera-traps) | 235,778 processed images, 19,785 Events, 72,775 original-SAM3-geometry operational Occurrences; the 2,067-box reference set is separate |
| [smartwilds-bioacoustics](https://huggingface.co/datasets/imageomics/smartwilds-bioacoustics) | 2,371 WAV recordings, 9,960 Occurrences |
| [smartwilds-drones](https://huggingface.co/datasets/imageomics/smartwilds-drones) | 39 videos, 15 flight sessions, 318,215 Occurrences |
| [smartwilds-citizen-science](https://huggingface.co/datasets/imageomics/smartwilds-citizen-science) | 1,103 media files, 622 Occurrences |
| **smartwilds** (this dataset) | study root, merged Event table, text records, arrival traces |

All five datasets share one Event hierarchy. The camera branch has its own
final Project and adds a per-image Event level:

```
TheWilds_2025 (study, 2025-06-30/2025-09-08)
├── SmartWilds_camera_traps_curated (Project)
│   └── SensorDeployment
│       └── Image
└── Other modality Projects
    └── SensorDeployment / flight session / observation session
        └── AudioRecording | MediaEvent
```

## Contents

- `data/events_all_modalities.csv`: all 22,242 Events, including the final
  camera Project, 12 SensorDeployments, and 19,772 per-image Events.
- `data/occurrences_all_modalities.csv`: 401,602 unique Occurrences. Every
  retained camera row joins to the merged Event hierarchy on `eventID`.
  
- `data/text_*.csv`, `data/site_selection_rationale.csv`: 30 text-derived
  Occurrences, plus the reasoning behind where each sensor was placed.
- `metadata/sensor_configurations.md`: per-device configurations for every
  modality.
- `analysis/arrival_traces_v2/`: Campaign-2 arrival streams at two layers.
  - Acquisition: one WAV recording per arrival.
  - Detection: one retained operational Occurrence per arrival. The camera
    trace uses the final 72,775 original-SAM3-geometry camera rows rather than
    the superseded first-generation camera output.

  Each stream comes with source-record IDs, inclusion rules, and checksums. The
  camera image-capture acquisition stream can be rebuilt from
  `smartwilds-camera-traps/data/images.csv`.
- `SUPPLEMENTAL.md`: the paper's supplemental material --- extended glossary,
  per-deployment inventories, all 18 timestamp-repair methods, drone ground
  projection, the standards crosswalk, typed missingness, model accuracy,
  validation checks, the field dictionary, arrival statistics, reproduction
  commands, and the full defect inventory.
- `metadata/DEFECT_INVENTORY.md` (and `defect_inventory.csv`): all 22 defect
  classes found during integration, each with its scope, what detected it,
  the repair applied, and the residual risk.
- `metadata/provenance/`: the final release audit.

## Citation

Cite the paper, plus each modality dataset you use. <!-- TODO: DOIs -->

## Dataset Card Contact

Jenna M. Kline (kline.377@osu.edu)
