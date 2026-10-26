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
  corrected timestamps, per-deployment sensor settings, and 72,769 Darwin Core
  Occurrences: SAM3 animal boxes labelled by embedding-based triage with human
  review, plus a separate 2,067-box human-reviewed reference set.

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
    sampling_protocol: "Passive-infrared-triggered trail cameras; SAM3 animal proposals labelled by embedding-based triage (Resolve-Clear-Defer) with targeted human review"

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
- config_name: validation
  data_files: validation/camera_census_validation_annotations.csv
---

# Dataset Card for SmartWilds Camera Traps

![Camera-trap detections of three managed focal species](images/preview.png)
*SAM3 detections on camera-trap images of Przewalski's horse, Sichuan takin, and Milu (Père David's) deer. The burned-in overlay shows each camera's **raw device clock**, which was often wrong; use `corrected_timestamp` in `data/images.csv` (the takin frame's overlay reads 2025/09/13 for an image captured in August).*
<!-- TODO(confirm-stats): preview.png was drawn from the pre-triage (BioCLIP) boxes; confirm the boxes shown still exist in the post-triage Occurrences or regenerate. -->

<img src="images/deployment.jpg" alt="GardePro camera trap strapped to a tree" width="320">

*A GardePro trail camera deployed at The Wilds.*

**Every image from 13 camera-trap deployments at The Wilds in summer 2025, with the
corrected time it was taken, how the camera was configured, and the animals
found in it by a detector, embedding-based triage, and human review.**

This is the camera-trap dataset of the **SmartWilds** collection. Each sensing
modality has its own dataset and DOI. They share one Darwin Core Event hierarchy
rooted at `TheWilds_2025` and are joined by the
[SmartWilds collection](https://huggingface.co/collections/imageomics/smartwilds)
<!-- TODO: confirm collection URL -->.
<!-- TODO(confirm-stats): the post-triage Event table is rooted at its own Project `SmartWilds_camera_traps_curated` (no parent), not `TheWilds_2025_camera_traps` under `TheWilds_2025`. Re-parent in the build (or the generator) before claiming a shared hierarchy. Deployment ID `TW09_CT02` also uses an underscore where the others use a hyphen. -->

## Dataset Details

### Dataset Description

- **Curated by:** Jenna M. Kline, Anirudh Potlapally, Elizabeth G. Campolongo
- **Language(s):** English (metadata)
- **Homepage:** <https://github.com/Imageomics/wilds_multimodal_data>
- **Paper:** SmartWilds: A Systems Dataset and Metadata Foundation for Cross-Modal Ecological Sensing (in preparation)
- **Snapshot:** `darwin_core_latest_20261008/camera_traps_post_triage` (2026-10-25)
  <!-- TODO(confirm-stats): set the release build date once rebuilt from the post-triage tables. -->

Camera traps were deployed in two campaigns at The Wilds, a 4,050-hectare (10,000-acre)
conservation center on reclaimed mine land in southeastern Ohio that holds
managed herds of non-native ungulates alongside native wildlife:

| Campaign | Dates | Deployments | Images | Images with Occurrences | Occurrences |
|---|---|---:|---:|---:|---:|
| 1 | 2025-06-30 to 2025-07-03 | 4 | 15,081 | 1,556 | 2,324 |
| 2 | 2025-08-04 to 2025-08-28 | 9 (8 released) | 220,697 | 18,187 | 70,445 |

The release has four layers:

1. **Raw media** (`media/`): 235,778 JPG images and 5,113 MP4/AVI clips, laid out
   as `media/<campaign>/<deployment>/<sd-card>/...` in the same structure as on
   the SD cards.
2. **Per-image table** (`data/images.csv`): one row per image, including images
   with no detection. It gives the raw and corrected timestamp, the correction
   method and confidence, and the number of Occurrences. Use this table for
   acquisition-rate (image-capture) analyses.
   <!-- TODO(confirm-stats): `occurrence_count` and `has_human_detection` in images.csv are still computed from the pre-triage Occurrences; recompute from the post-triage table in the build. -->
3. **Darwin Core tables** (`data/events.csv`, `data/occurrences.csv`): 19,762
   Events (1 modality `Project`, 12 `SensorDeployment`, and 19,749 `Image`) and
   72,769 Occurrences, each one a retained animal box. 19,743 images carry at
   least one Occurrence; the other six Image Events exist only to anchor
   reference annotations.
4. **Human-reviewed reference set** (`validation/`): 2,067 boxes on 198 images,
   kept separate from the operational Occurrences.

### Supported Tasks

- **Object detection and classification:** boxes are in `bboxX`, `bboxY`, `bboxWidth`, `bboxHeight` (pixels, COCO `xywh`), and the images are under `media/`.
- **Label re-derivation:** every Occurrence records its label provenance (`labelProvenance`, `triageRound`), its SAM3 score, and its source proposal (`sourcePoolIndex`), so you can re-label the data with a newer model and compare the results.
- **Workload and trace-driven systems research:** you can rebuild per-image acquisition arrivals and per-detection inference arrivals with corrected timestamps and per-device trigger settings.
- **Activity analysis of the managed focal species** (milu deer, Przewalski's horse, Sichuan takin) and waterfowl, with caveats (see *Limitations*).

## Dataset Structure

```
smartwilds-camera-traps/
├── data/
│   ├── events.csv            # Darwin Core Event (Project + 12 SensorDeployment + 19,749 Image)
│   ├── occurrences.csv       # Darwin Core Occurrence (72,769 retained animal boxes)
│   └── images.csv            # one row per image (235,778), corrected timestamps
├── validation/
│   ├── camera_census_validation_annotations.csv   # 2,067 human-reviewed reference boxes
│   ├── camera_verified_counts_by_image.csv        # 216 image-by-taxon count rows
│   └── README.md
├── media/                    # raw JPG / MP4 / AVI, release-relative paths
├── media_manifest.csv        # one row per raw file: path, bytes, include, reason
├── metadata/
│   ├── taxonomy_mapping.csv  # source label -> taxon
│   ├── DATA_DICTIONARY.md
│   ├── deployments.csv       # per-deployment sensor settings + geolocation inputs
│   ├── camera_models.csv     # model, manufacturer, horizontal field of view
│   ├── timestamp_summary_by_camera.csv / _by_date.csv
│   └── provenance/           # JSON audits for each mutation of the tables
├── scripts/                  # Darwin Core generator, release build
└── CHECKSUMS.sha256
```
<!-- TODO(confirm-stats): dropped analysis/bird_water_association_per_box.csv and camera_geolocation_config.csv from the tree — both depend on the pre-triage boxes / pinhole projection. Confirm they are removed from the build. -->

Every `associatedMedia` value in `occurrences.csv` and every `release_path` in
`images.csv` resolves to a file under `media/`. This is checked at build time.
<!-- TODO(confirm-stats): the post-triage tables (Occurrences, Image Events, validation CSVs) carry internal /fs/ess/... paths; the build must rewrite them (all 19,749 Image Event paths map to an images.csv release_path, checked 2026-10-26). -->

### Sensor settings

`metadata/deployments.csv` gives one row per deployment with its model, HFOV,
facing, capture mode, photo and video configuration, PIR sensitivity, trigger
delay, GPS, bearing, the source of each geolocation input, and the image count. The settings determine both
detectability and data volume:

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
`correction_method`, and `correction_confidence` for every image. Image Event
and Occurrence `eventDate` and `eventTime` always equal the corrected timestamp
of their image.

### Annotation method

- **Method:** automated detection, embedding-based label triage, and targeted
  human review, plus a separate human-reviewed reference set.
- **Detection:** SAM3 animal proposal boxes. Box geometry is never edited in the
  Occurrence table (`geometryProvenance = SAM3`), even when the label was
  human reviewed.
- **Labelling:** embedding-based triage (Resolve–Clear–Defer) chose which
  proposals went to human review and resolved the rest by similarity to
  reviewed examples. `labelProvenance` records the outcome:

  | `labelProvenance` | `identificationVerificationStatus` | Occurrences |
  |---|---|---:|
  | `triage_reviewed` | `human-reviewed` | 1,760 |
  | `triage_resolved` | `machine-resolved` | 70,808 |
  | `triage_forced_1nn` | `machine-resolved` | 201 |

  Forced nearest-neighbour labels did not meet the triage confidence rules and
  may be wrong. 30 reviewed records have no recovered `triageRound`.
- **Filtering:** the Occurrence table keeps only reviewed or resolved animal
  proposals. It excludes background/cleared proposals, user-excluded frames,
  frames on the privacy exclusion manifest, boxes overlapping the
  resolution-specific ROI mask, boxes on images of unknown resolution, and boxes
  with a shorter side below 32 px. **An image without an Occurrence is not
  evidence that no animal was present.**
- **No animal geolocation.** Occurrences carry no estimated animal coordinates;
  the camera position is on the parent `SensorDeployment` Event.

**Taxa.** The taxonomy mapping (`metadata/taxonomy_mapping.csv`) has 13 source
labels; 12 occur in the Occurrence table (banteng has none). Milu deer is also
known as Père David's deer. Bird, butterfly, dragonfly, and insect are broad
labels, not species identifications.

| Taxon | Scientific name | Rank | Occurrences | Images | Human-reviewed |
|---|---|---|---:|---:|---:|
| Milu deer | *Elaphurus davidianus* | species | 47,644 | 12,059 | 568 |
| Przewalski's horse | *Equus przewalskii* | species | 14,070 | 6,402 | 363 |
| Canada goose | *Branta canadensis* | species | 8,288 | 1,222 | 333 |
| Sichuan takin | *Budorcas taxicolor* | species | 2,207 | 1,179 | 345 |
| Trumpeter swan | *Cygnus buccinator* | species | 304 | 240 | 56 |
| Killdeer | *Charadrius vociferus* | species | 161 | 155 | 35 |
| European starling | *Sturnus vulgaris* | species | 60 | 35 | 33 |
| Barn swallow | *Hirundo rustica* | species | 13 | 13 | 7 |
| Bird | Aves | class | 11 | 11 | 9 |
| Butterfly | Lepidoptera | order | 7 | 7 | 7 |
| Dragonfly | Anisoptera | infraorder | 3 | 3 | 3 |
| Insect | Insecta | class | 1 | 1 | 1 |

**Human-reviewed reference set.** `validation/` holds 2,067 boxes on 198
selected ungulate and waterfowl images: 881 Canada goose, 627 milu deer, 349
Przewalski's horse, 149 Sichuan takin, and 61 trumpeter swan. Taxonomy and
geometry were human reviewed, including edits and added boxes, and the set is
not filtered by the 32 px or ROI rules. 1,552 boxes match a SAM3 proposal's
geometry and 515 are `human_edit_or_addition`; 1,482 link to an operational
Occurrence. The reference boxes are **not** merged into `occurrences.csv`. The
images were selected for review, so the set is not a random or exhaustive test
split. See `validation/README.md`.
<!-- TODO(confirm-stats): no accuracy figures for the triage labels are reported here. If the WACV Resolve–Clear–Defer paper or a check against the reference set gives label/box accuracy, add it (the old BioCLIP rank-accuracy table and the IoU≥0.5 P/R/F1 = 0.866/0.845/0.856 on n=1,125 no longer describe these labels). -->

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
  recorded in `metadata/deployments.csv`.
- **Battery exhaustion** at TW02-CT01 (Aug 18-25) and TW02-CT03 in Campaign 1.
<!-- TODO(confirm-stats): removed the "439 curated bird Occurrences re-timed" repair (defect #17). It applied to the pre-triage curated-bird records; the post-triage Image Event times match corrected_timestamp for 19,749/19,749 images (checked 2026-10-26). Update DEFECT_INVENTORY.md / defect_inventory.csv row 17 and drop the re-timing step from build_hf_release.py. -->

### Personal and sensitive information

- **TW07-CT05** (Zipline Tower) captured only visitors on tour buses. Its
  photos were never uploaded, and the deployment is excluded from the release.
- **Other deployments also capture people.** Frames on the privacy exclusion
  manifest are excluded from the Occurrence table, but model-based screening
  cannot guarantee that every person was found.
  <!-- TODO(confirm-stats): the old "10,797 images with a Homo sapiens detection" came from the BioCLIP labels, which no longer exist. Recount people from the MegaDetector screening (release/screening/) and recompute `has_human_detection`. Note 2,148 of the 19,749 post-triage Image Events are flagged by the old `has_human_detection`. -->
  <!-- TODO(release): decide whether these images are withheld, blurred, or released; and whether undetected people in blank images need screening. -->
- **No locality is withheld.** The species at the site are managed captive
  herds or common native wildlife.

## Considerations for Using the Data

### Limitations

- **Occurrences count boxes, not individuals.** Bursts and repeated
  triggers record the same animal many times.
- **Occurrences cover only 19,743 of 235,778 images.** Size, ROI, and privacy
  filters remove boxes, so a missing Occurrence is not an absence.
- **Most labels are machine-resolved.** Only 1,760 of 72,769 labels (2.4%) were
  human reviewed, and the 201 forced nearest-neighbour labels are the least
  reliable.
- **Detection effort was very uneven.** TW09-CT02 (dock) alone produced 90,834
  images (38.5%); TW02-CT01, TW06-CT04, and TW09-CT02 together hold 87% of
  Occurrences.
- **There are no true deploy and retrieve times.** Deployment metadata is known
  to contain errors, so effort is reported as corrected observation dates.
- **Within-card clock drift was not modeled.** Each card has only one external
  time anchor.

### Recommendations

- **Filter on `labelProvenance`** before any analysis. Exclude
  `triage_forced_1nn` unless you can tolerate label noise.
- **Evaluate on the reference set, not on the Occurrences.** Avoid random splits
  that put near-duplicate frames from the same trigger on both sides.
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

Please also cite the Resolve–Clear–Defer triage method (WACV submission; details to follow).
<!-- TODO: add the WACV bibliographic entry when available. -->

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
