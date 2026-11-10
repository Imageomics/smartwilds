---
license: cc0-1.0
language:
- en
pretty_name: SmartWilds Metadata (The Wilds 2025)
task_categories:
- object-detection
- image-classification
- audio-classification
tags:
- biology
- ecology
- biodiversity
- multimodal
- sensor-networks
- camera-trap
- bioacoustics
- drone
- citizen-science
- darwin-core
- humboldt-eco
- fair2
- smartwilds
- the-wilds
- ohio
size_categories:
- 100K<n<1M
description: >-
  The metadata of the SmartWilds multi-modal field sensing dataset (The Wilds,
  Ohio, USA, summer 2025): Darwin Core Event and Occurrence tables for camera
  traps, bioacoustics, drones, and citizen science on one Event hierarchy, with
  corrected timestamps and coordinates, dataset cards, data dictionaries,
  provenance records, media manifests, arrival traces, the supplemental
  material, and the defect inventory. Raw images, audio, and video are not
  included.

fair2_compliance:
  findable:
    doi: ""  # pending
    metadata_registry: ["DataCite"]
  accessible:
    open_access: true
    authentication_required: false
  interoperable:
    standards: ["Darwin Core", "TDWG", "Humboldt Eco", "FAIR2"]
  reusable:
    license_clear: true
    provenance_documented: true
  ai_ready:
    machine_readable: true
    structured_annotations: true

darwin_core:
  event_coverage:
    start_date: "2025-06-30"
    end_date: "2025-09-08"
    decimal_latitude: 39.83
    decimal_longitude: -81.74
    coordinate_uncertainty_meters: 5000
    locality: "The Wilds, Cumberland, Ohio, USA"
    habitat: "Reclaimed grassland and lakes of a conservation center on a former surface mine"
  occurrence_info:
    kingdom: "Animalia"
    sampling_protocol: "Camera traps, Song Meter acoustic recorders, drone video surveys, and structured visitor photography, integrated into Darwin Core Event and Occurrence records"

configs:
- config_name: camera_trap_occurrences
  data_files: smartwilds-camera-traps/data/occurrences.csv
- config_name: camera_trap_events
  data_files: smartwilds-camera-traps/data/events.csv
- config_name: camera_trap_images
  data_files: smartwilds-camera-traps/data/images.csv
- config_name: bioacoustic_occurrences
  data_files: smartwilds-bioacoustics/data/occurrences.csv
- config_name: bioacoustic_events
  data_files: smartwilds-bioacoustics/data/events.csv
- config_name: bioacoustic_recordings
  data_files: smartwilds-bioacoustics/data/recordings.csv
- config_name: drone_occurrences
  data_files: smartwilds-drones/data/occurrences.csv
- config_name: drone_events
  data_files: smartwilds-drones/data/events.csv
- config_name: drone_detections
  data_files: smartwilds-drones/data/detections.csv
- config_name: citizen_science_occurrences
  data_files: smartwilds-citizen-science/data/occurrences.csv
- config_name: citizen_science_events
  data_files: smartwilds-citizen-science/data/events.csv
- config_name: all_events
  data_files: smartwilds/data/events_all_modalities.csv
- config_name: all_occurrences
  data_files: smartwilds/data/occurrences_all_modalities.csv
---

# Dataset Card for SmartWilds Metadata

![Sensor deployment across The Wilds](smartwilds/images/smartwilds/deployment_map.png)
*Sensor deployment across The Wilds: camera traps with viewing angles, Song Meter recorders, citizen-science photo locations, and drone flight tracks. Satellite imagery © Google.*

**SmartWilds** is a multi-modal sensing dataset recorded with camera traps,
acoustic recorders, drones, and visitor photographs at [The Wilds](https://thewilds.columbuszoo.org/)
(Cumberland, Ohio) in summer 2025. This dataset is its metadata: Darwin Core
tables for all four modalities on one Event hierarchy, with corrected
timestamps and coordinates so they can be joined in space and time, the
dataset cards, data dictionaries, provenance records, and media manifests of
each modality, the arrival traces used in the systems analysis, the
supplemental material of the paper, and the record of every defect found and
repaired. Raw images, audio, and video are not included; they will be released
separately.

## Dataset Details

- **Curated by:** Jenna M. Kline, Anirudh Potlapally, Elizabeth G. Campolongo
- **Homepage and code:** <https://github.com/Imageomics/smartwilds> (documentation: <https://imageomics.github.io/smartwilds/>)
- **Paper:** SmartWilds: Integrating, Aligning, and Documenting Multi-Modal Field Sensing Data (under review)
- **Release build:** 2026-10-22; camera and merged tables updated 2026-11-08
- **Collection:** [SmartWilds](https://huggingface.co/collections/imageomics/smartwilds), which also holds the 2025 pilot media

| Component | Events | Occurrences | Notes |
|---|---:|---:|---|
| `smartwilds-camera-traps/` | 19,785 | 72,775 | 235,778-image inventory with corrected timestamps; operational boxes with original SAM3 geometry and triage label provenance |
| `smartwilds-bioacoustics/` | 2,382 | 9,960 | 2,371 WAV recordings, BirdNET Analyzer v2.4 |
| `smartwilds-drones/` | 55 | 318,215 | 39 videos, 15 flight sessions; frame-indexed detections and ground-projected positions |
| `smartwilds-citizen-science/` | 14 | 622 | 1,103 media files, expert-verified labels |
| `smartwilds/` (study level) | 22,242 | 401,602 | Merged tables, text records, sensor configurations, Campaign-2 arrival traces |

All tables share one Event hierarchy rooted at `TheWilds_2025`:

```
TheWilds_2025 (study, 2025-06-30/2025-09-08)
├── SmartWilds_camera_traps_curated (Project)
│   └── SensorDeployment
│       └── Image
└── Other modality Projects
    └── SensorDeployment / flight session / observation session
        └── AudioRecording | MediaEvent
```

### Supported Tasks and Applications

This dataset supports cross-modal ecological analysis, data-quality research, and sensing-systems research. Computer-vision and audio tasks become possible when the raw media are released; the metadata here is what makes those releases usable.

**🔗 Cross-Modal Analysis:**
- Joining camera, acoustic, drone, and citizen-science records by site, campaign, and time on one Event hierarchy
- Corroboration of focal-species activity across sensors; sensor marginal value by place and hour
- Diel activity and species occurrence per modality from corrected timestamps

**🧹 Data-Quality and Metadata Research:**
- Timestamp reconstruction (18 methods, with confidence per image), telemetry mapping across three drone platforms, raw-inventory reconciliation
- Label provenance kept distinct: triage-resolved, human-reviewed, forced nearest-prototype, human-edited, validated, unverified
- A 22-item defect inventory with detection family, repair, and residual risk

**⚙️ Sensing-Systems Research:**
- Acquisition- and inference-layer arrival traces for workload characterization (burstiness, diurnal rates)
- Synthesis of coordinated multi-modal workloads and hardware feasibility prediction
- Blank-image filtering, storage, and edge provisioning from the full image inventory

**🤖 Computer Vision and Audio Tasks (with the media releases):**
- Object detection and species classification (camera traps, drones, visitor photos) with provenance-labeled boxes and human reference sets
- Multi-object tracking on frame-indexed drone detections
- Bird call classification and sound-event detection against BirdNET outputs

## Layout

Each component folder is a complete FAIR² dataset package:

```
<component>/
├── README.md             # the component's dataset card
├── data/                 # Darwin Core events.csv, occurrences.csv, per-file tables
├── metadata/             # DATA_DICTIONARY.md, deployments, configs, provenance/
├── analysis/             # arrival traces (study level), camera arrival statistics
├── scripts/              # generator, georeferencing, release build
├── media_manifest.csv    # one row per raw file: release path, size, include flag, privacy screening
└── CHECKSUMS.sha256
SUPPLEMENTAL.md           # the paper's supplemental material
```

Column definitions are in each component's `metadata/DATA_DICTIONARY.md`.
The defect inventory is `smartwilds/metadata/DEFECT_INVENTORY.md`.

## Using the data correctly

- **Pick a verification floor before analysis.** Almost every Occurrence is a
  machine label, and the status vocabulary differs by table: camera-trap rows
  carry a `labelProvenance`; drone and acoustic rows are `unverified` or
  `validated`. The drone labels come from BioCLIP 2 (TreeOfLife-200M) in
  open-world Tree of Life mode; species-rank accuracy on human-annotated
  subsets is 0.271 and class-rank accuracy is 0.845 (SUPPLEMENTAL.md, S9).
- **Occurrences are detection crops, not individuals.**
- **Use the corrected timestamps.** Camera clocks were wrong on most
  deployments; every image carries its correction method and confidence.
- **Filter drone coordinates on their status** (`georef_status` in
  `detections.csv`).
- **Join fixed sensors by site code and campaign**, drones and citizen science
  by coordinates or date; see the [joining guide](https://imageomics.github.io/smartwilds/datasets/joining/).

## Personal and sensitive information

Media in which a person can be individually identified are removed from the
media release; people too small to identify (a person box under 80 px) are
retained. The screening evidence and human-review outcome are recorded per
file in the media manifests and the camera image inventory. Coordinates fall
within a public conservation area and are not generalized, except for
citizen-science records, which carry a park-level point.

## Licensing

Data: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Scripts: MIT.

## Citation

```bibtex
@misc{smartwilds2025_metadata,
  author    = {Kline, Jenna M. and Potlapally, Anirudh and Campolongo, Elizabeth G.},
  title     = {SmartWilds Metadata (The Wilds 2025)},
  year      = {2026},
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/imageomics/smartwilds_metadata}
}
```

Please also cite the paper:

```bibtex
@article{kline2026smartwilds,
  author  = {Kline, Jenna M. and Potlapally, Anirudh and Campolongo, Elizabeth G.},
  title   = {SmartWilds: Integrating, Aligning, and Documenting Multi-Modal Field Sensing Data},
  year    = {2026},
  note    = {Under review}
}
```

This dataset card follows the [FAIR² Drones Data Standard](https://imageomics.github.io/fair_drones/)
(Kline and Campolongo, 2026).

## Acknowledgements

This project is supported by the [Imageomics Institute](https://imageomics.org), which is funded by the US National Science Foundation's Harnessing the Data Revolution (HDR) program under [Award #2118240](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2118240) (Imageomics: A New Frontier of Biological Information Powered by Knowledge-Guided Machine Learning), and by the [AI Institute for Intelligent Cyberinfrastructure with Computational Learning in the Environment (ICICLE)](https://icicle.osu.edu/), which is funded by the US National Science Foundation under [Award #2112606](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2112606).

This work is also supported by the AI and Biodiversity Change (ABC) Global Center. The ABC Global Center is funded by the US National Science Foundation under [Award No. 2330423](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2330423&HistoricalAwards=false) and the Natural Sciences and Engineering Research Council of Canada under [Award No. 585136](https://www.nserc-crsng.gc.ca/ase-oro/Details-Detailles_eng.asp?id=782440). This dataset draws on research supported by the Social Sciences and Humanities Research Council.

Any opinions, findings and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation, Natural Sciences and Engineering Research Council of Canada, or Social Sciences and Humanities Research Council.

Special thanks to Dan Beetem and [The Wilds](https://www.thewilds.org/) in Ohio for providing access to deployment sites and supporting this wildlife monitoring research. We thank the Columbus Zoo and Aquarium for their support in facilitating this project. All data collection, including drone flights, was conducted under the supervision of the Director of Animal Management, with permission from The Wilds Animal Care and Use Committee.

This work used the [Ohio Supercomputer Center](https://www.osc.edu/) (Ohio Supercomputer Center, 1987, <http://osc.edu/ark:/19495/f5s1ph73>).

## Dataset Card Contact

Jenna M. Kline ([kline.377@osu.edu](mailto:kline.377@osu.edu))
