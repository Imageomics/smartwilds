---
license: cc0-1.0  # TODO(license): visitor-submitted media; confirm contributor consent and license terms
language:
- en
pretty_name: SmartWilds Citizen Science (The Wilds 2025)
task_categories:
- image-classification
tags:
- biology
- ecology
- biodiversity
- citizen-science
- darwin-core
- fair2
- smartwilds
- the-wilds
- ohio
size_categories:
- n<1K
description: >-
  Visitor-submitted wildlife photographs from 13 observation sessions at The
  Wilds (Ohio, USA), 2025: 1,103 raw media files, 564 curated wildlife photos,
  and 622 expert-verified Darwin Core Occurrences.

configs:
- config_name: occurrences
  data_files: data/occurrences.csv
- config_name: events
  data_files: data/events.csv
---

# Dataset Card for SmartWilds Citizen Science

![Citizen-science photos of three managed focal species](images/preview.png)
*Visitor photographs of Przewalski's horse, Sichuan takin, and Milu (Père David's) deer, with annotation boxes.*

> **Status: staging incomplete.** The source Darwin Core tables for this modality
> are owner-only on the cluster. Rebuild with `release/scripts/build_hf_release.py`
> once they are readable.

This is the citizen-science dataset of the **SmartWilds** collection. Each
modality has its own dataset and DOI. They share one Darwin Core Event hierarchy
rooted at `TheWilds_2025` and are joined by the SmartWilds collection.

## Dataset Details

- **Curated by:** Jenna M. Kline, Anirudh Potlapally, Elizabeth G. Campolongo
- **Snapshot:** `darwin_core_latest_20261008`

Park visitors submitted photographs through a structured web form. The
release distinguishes four counts, each a different unit:

| Unit | Count |
|---|---:|
| Raw media files in `photos_videos` (965 images, 138 videos) | 1,103 |
| Photos manually annotated | 791 |
| Curated wildlife photos | 564 |
| Darwin Core Occurrences (some photos contain several taxa) | 622 |

Fifty of the curated photos, all from September 8, come from a Google Photos
album export rather than the raw folder. `associatedMedia` and
`occurrenceRemarks` say so for each of them.

The Event table has 14 rows: 1 `Project` and 13 `ObservationSession`.

### Annotation method

- **Method:** manual. All 622 Occurrences are `verified by expert`
  (`HumanObservation`).
- **Locality:** coordinates are generalized to locality level.

### Personal and sensitive information

The photos were taken by members of the public, and some may show people.
<!-- TODO(release): confirm visitor consent / terms of submission permit redistribution; screen for identifiable people. -->

## Considerations for Using the Data

- **Submissions arrive only during operating hours.** The diurnal profile is
  truncated by visitor schedules, not by animal activity.
- **Visitors' attention skews the taxa.** Charismatic and easily seen taxa are
  over-represented.

## Supplemental Material

Extended inventories, the timestamp-repair methods, the standards crosswalk,
validation checks, and the full defect inventory are in
[`SUPPLEMENTAL.md`](https://huggingface.co/datasets/imageomics/smartwilds/blob/main/SUPPLEMENTAL.md)
in the study-level SmartWilds dataset. <!-- TODO: confirm repo URL -->

## Dataset Card Contact

Jenna M. Kline (kline.377@osu.edu)
