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
- humboldt-eco
- fair2
- smartwilds
- the-wilds
- ohio
size_categories:
- 100K<n<1M
description: >-
  235,778 camera-trap images and 5,113 video clips from 13 deployments at The
  Wilds conservation center (Ohio, USA), June-August 2025, with per-image
  corrected timestamps, per-deployment sensor settings, and 224,149 Darwin Core
  Occurrences from SAM3 detection and BioCLIP Tree-of-Life classification.

fair2_compliance:
  findable:
    doi: ""  # TODO: assign on publication
    metadata_registry: ["DataCite", "GBIF"]
  accessible:
    open_access: true
    authentication_required: false
  interoperable:
    standards: ["Darwin Core", "Humboldt Eco", "FAIR2"]
  reusable:
    license_clear: true
    provenance_documented: true
  ai_ready:
    machine_readable: true
    structured_annotations: true

darwin_core:
  event_coverage:
    start_date: "2025-06-30"
    end_date: "2025-08-28"
    decimal_latitude: 39.83
    decimal_longitude: -81.74
    coordinate_uncertainty_meters: 5000
    locality: "The Wilds, Cumberland, Muskingum County, Ohio, USA"
    habitat: "Reclaimed surface-mine grassland, pasture, wetland and lake edge"
  occurrence_info:
    basis_of_record: "MachineObservation"
    sampling_protocol: "Passive-infrared-triggered trail cameras; SAM3 detection, BioCLIP Tree-of-Life classification, pinhole-model ground projection"

sensors:
  - type: "RGB trail camera"
    manufacturer: "GardePro"
    model: "T5NG"
  - type: "RGB trail camera"
    manufacturer: "GardePro"
    model: "A3"
  - type: "RGB trail camera"
    manufacturer: "Trail Camera"
    model: "G600"
  - type: "RGB cellular trail camera"
    manufacturer: "Tactacam"
    model: "Reveal Pro 3.0"

configs:
- config_name: occurrences
  data_files: data/occurrences.csv
- config_name: events
  data_files: data/events.csv
- config_name: images
  data_files: data/images.csv
---

# Dataset Card for SmartWilds Camera Traps

![Camera-trap detections of three managed focal species](images/preview.png)
*SAM3 detections on camera-trap images of Przewalski's horse, Sichuan takin, and Milu (Père David's) deer. The burned-in overlay shows each camera's **raw device clock**, which was often wrong; use `corrected_timestamp` in `data/images.csv` (the takin frame's overlay reads 2025/09/13 for an image captured in August).*

<img src="images/deployment.jpg" alt="GardePro camera trap strapped to a tree" width="320">

*A GardePro trail camera deployed at The Wilds.*

**Every image from 13 camera-trap deployments at The Wilds in summer 2025, with the
corrected time it was taken, how the camera was configured, and what a
state-of-the-art detector and classifier found in it.**

This is the camera-trap dataset of the **SmartWilds** collection. Each sensing
modality has its own dataset and DOI. They share one Darwin Core Event hierarchy
rooted at `TheWilds_2025` and are joined by the
[SmartWilds collection](https://huggingface.co/collections/imageomics/smartwilds)
<!-- TODO: confirm collection URL -->.

## Dataset Details

### Dataset Description

- **Curated by:** Jenna M. Kline, Anirudh Potlapally, Elizabeth G. Campolongo
- **Language(s):** English (metadata)
- **Homepage:** <https://github.com/Imageomics/wilds_multimodal_data>
- **Paper:** SmartWilds: A Systems Dataset and Metadata Foundation for Cross-Modal Ecological Sensing (in preparation)
- **Snapshot:** `darwin_core_latest_20261008`, release build 2026-10-22

Camera traps were deployed in two campaigns at The Wilds, a 4,050-hectare (10,000-acre)
conservation center on reclaimed mine land in southeastern Ohio that holds
managed herds of non-native ungulates alongside native wildlife:

| Campaign | Dates | Deployments | Images |
|---|---|---:|---:|
| 1 | 2025-06-30 to 2025-07-03 | 4 | 15,081 |
| 2 | 2025-08-04 to 2025-08-28 | 9 (8 released) | 220,697 |

The release has three layers:

1. **Raw media** (`media/`): 235,778 JPG images and 5,113 MP4/AVI clips, laid out
   as `media/<campaign>/<deployment>/<sd-card>/...` in the same structure as on
   the SD cards.
2. **Per-image table** (`data/images.csv`): one row per image, including images
   with no detection. It gives the raw and corrected timestamp, the correction
   method and confidence, and the number of Occurrences. Use this table for
   acquisition-rate (image-capture) analyses.
3. **Darwin Core tables** (`data/events.csv`, `data/occurrences.csv`): 13 Events
   (1 modality `Project` and 12 `SensorDeployment`) and 224,149 Occurrences,
   each one a detection crop.

### Supported Tasks

- **Object detection and classification:** boxes are given in `identificationRemarks`, and the images are under `media/`.
- **Label re-derivation:** every label records its model, its score, and its box geometry, so you can re-label the data with a newer model and compare the results.
- **Workload and trace-driven systems research:** you can rebuild per-image acquisition arrivals and per-detection inference arrivals with corrected timestamps and per-device trigger settings.
- **Occupancy and activity analysis:** you can analyze occupancy and activity at class rank, with caveats (see *Limitations*).

## Dataset Structure

```
smartwilds-camera-traps/
├── data/
│   ├── events.csv            # Darwin Core Event (Project + 12 SensorDeployment)
│   ├── occurrences.csv       # Darwin Core Occurrence (224,149 detection crops)
│   └── images.csv            # one row per image (235,778), corrected timestamps
├── media/                    # raw JPG / MP4 / AVI, release-relative paths
├── media_manifest.csv        # one row per raw file: path, bytes, include, reason
├── metadata/
│   ├── deployments.csv       # per-deployment sensor settings + geolocation inputs
│   ├── camera_models.csv     # model, manufacturer, horizontal field of view
│   ├── camera_geolocation_config.csv
│   ├── timestamp_summary_by_camera.csv / _by_date.csv
│   └── provenance/           # JSON audits for each mutation of the tables
├── analysis/bird_water_association_per_box.csv
├── scripts/                  # Darwin Core generator, geolocation, release build
└── CHECKSUMS.sha256
```

Every `associatedMedia` value in `occurrences.csv` and every `release_path` in
`images.csv` resolves to a file under `media/`. This is checked at build time.

### Sensor settings

`metadata/deployments.csv` gives one row per deployment with its model, HFOV,
facing, capture mode, photo and video configuration, PIR sensitivity, trigger
delay, GPS, bearing, the source of each geolocation input, and the image count.
The settings determine both detectability and data volume:

| Parameter | Range in this release | Effect |
|---|---|---|
| Burst | 3- or 5-shot | 3-5x raw images per trigger |
| Mode | photo only / photo+video / hybrid | video adds 10-15 s clips per trigger |
| HFOV | 55°-120° | wide lens means a larger zone and fewer pixels per animal |
| Resolution | 4 MP, 8 MP, 4K | file size and inference cost |
| Delay | 0-20 s | lower arrival rate and fewer duplicates |

### Timestamps

Camera clocks were wrong or unset on most deployments. Timestamps were
reconstructed against field service logs using 18 per-deployment methods:

- 14,472 images (6.1%) were accepted as recorded.
- 221,306 (93.9%) were reconstructed.
- 105,488 (44.7%) have high confidence and 130,290 (55.3%) have medium confidence.

`images.csv` keeps `raw_timestamp`, `raw_timestamp_source` (filename, EXIF,
OCR of the burned-in overlay, or manual), `corrected_timestamp`,
`correction_method`, and `correction_confidence` for every image. Occurrence
`eventDate` and `eventTime` always equal the corrected timestamp of their image.

### Annotation method

- **Method:** automated, with a human-validated subset.
- **Detection:** SAM3 boxes.
- **Classification:** top-1 label from BioCLIP Tree-of-Life, with the full rank
  hierarchy written to the Darwin Core taxon fields. `identificationRemarks`
  records the rank, the top-1 score, and the box (`xywh`, in pixels).
- **Geolocation:** a pinhole model projects each box from the camera's GPS, its
  bearing, its HFOV, the box height, and an assumed 0.9 m target height. See
  [camera-trap-geolocation](https://github.com/Imageomics/camera-trap-geolocation).
  The coordinates are estimated animal positions, not GPS fixes, and
  `dataGeneralizations` says so on every row.
- **Verification:** 223,203 rows are `unverified` machine predictions. 946 are
  `validated`: Canada goose and trumpeter swan records from a targeted human
  review.

**Accuracy on human-annotated subsets.** Localization is strong: precision 0.866,
recall 0.845, and F1 0.856 at IoU ≥ 0.5 (n = 1,125). Taxonomic accuracy drops
with rank (n = 951):

| Rank | Accuracy |
|---|---:|
| Class | 0.845 |
| Order | 0.660 |
| Family | 0.463 |
| Genus | 0.322 |
| Species | 0.271 |

**Use class-rank labels for screening. Species-rank labels require curation.**
The species-rank labels include taxa that are impossible at this site, such as
brown hyena and bushpig.

## Dataset Creation

### Source data

Cameras were mounted on posts and trees at shelters, feeders, fences, the lake
dock, and trails. SD cards were swapped during service visits. Service visits in
Campaign 2 were logged in structured Jotform field logs, and those logs are the
reference that made the clock repairs possible.

### Known defects and repairs

The full inventory is in the paper (Table "Defect inventory"). The defects
specific to camera traps are:

- **Clocks wrong, unset, or reset to the factory epoch.** These were repaired per
  deployment (see *Timestamps*).
- **TW02-CT01 media split across 4 SD cards with different clock states.** Each
  card was anchored separately.
- **TW04-CT04 mounted upside down (570 images).** The images are released as
  captured.
- **TW09-CT02 moved from the dock to Nomad Ridge on Aug 18.** The move is
  expressed as a path-specific geolocation override for SD23
  (`metadata/deployments.csv`).
- **Battery exhaustion** at TW02-CT01 (Aug 18-25) and TW02-CT03 in Campaign 1.
- **Release build 2026-10-22:** 439 curated bird Occurrences had bypassed the
  timestamp correction. 124 carried the drifted raw clock (2025-09-14), and 315
  carried only the deployment interval. All 439 were re-timed from the
  corrected map and are marked in `occurrenceRemarks`.

### Personal and sensitive information

- **TW07-CT05** (Zipline Tower) captured only visitors on tour buses. Its
  photos were never uploaded, and the deployment is excluded from the release.
- **Other deployments also capture people.** 10,797 images contain at least one
  detection labelled *Homo sapiens*, and `has_human_detection` flags them in
  `images.csv` and `media_manifest.csv`.
  <!-- TODO(release): decide whether these images are withheld, blurred, or released; and whether undetected people in blank images need screening. -->
- **No locality is withheld.** The species at the site are managed captive
  herds or common native wildlife.

## Considerations for Using the Data

### Limitations

- **Occurrences count detection crops, not individuals.** Bursts and repeated
  triggers record the same animal many times.
- **Detection effort was very uneven.** TW09-CT02 (dock) alone produced 90,834
  images (38.5%).
- **There are no true deploy and retrieve times.** Deployment metadata is known
  to contain errors, so effort is reported as corrected observation dates.
- **Within-card clock drift was not modeled.** Each card has only one external
  time anchor.

### Recommendations

- **Filter on `identificationVerificationStatus`** before any analysis, and pick
  a verification floor in advance.
- **For acquisition workloads, use `images.csv`.** For inference workloads, use
  `occurrences.csv`.
- **Treat `correction_confidence = medium` timestamps as accurate to the day,**
  not to the minute.

## Supplemental Material

Extended inventories, the timestamp-repair methods, the standards crosswalk,
validation checks, and the full defect inventory are in
[`SUPPLEMENTAL.md`](https://huggingface.co/datasets/imageomics/smartwilds/blob/main/SUPPLEMENTAL.md)
in the study-level SmartWilds dataset. <!-- TODO: confirm repo URL -->

## Licensing

Data: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
<!-- TODO(license): confirm CC0 vs CC BY 4.0 across the collection -->.
Scripts: MIT.

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

We thank Dan Beetem, The Wilds, and the Columbus Zoo & Aquarium. Data
collection was supervised by the Director of Animal Management under The
Wilds Animal Care and Use Committee permissions. Supported by the
[Imageomics Institute](https://imageomics.org) (NSF Award #2118240),
[ICICLE](https://icicle.osu.edu) (NSF Award #2112606), and the
[ABC Global Center](http://abcresearchcenter.org) (NSF Award #2330423; NSERC
Award #585136).

## Dataset Card Contact

Jenna M. Kline (kline.377@osu.edu)
