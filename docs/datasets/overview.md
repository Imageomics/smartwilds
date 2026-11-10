# Data overview

SmartWilds has four event-bearing modalities, co-located across overlapping
sites and weeks, plus field-note and text context streams. Every modality is
expressed in the same Darwin Core schema and joined into one Event hierarchy
rooted at `TheWilds_2025`.

```
TheWilds_2025 (study, 2025-06-30/2025-09-08)
├── SmartWilds_camera_traps_curated (Project)
│   └── SensorDeployment
│       └── Image
└── Other modality Projects
    └── SensorDeployment / flight session / observation session
        └── AudioRecording | MediaEvent
```

| Dataset | Content |
|---|---|
| smartwilds-camera-traps | 235,778 processed images, 19,785 Events, 72,775 operational Occurrences with original SAM3 geometry |
| smartwilds-bioacoustics | 2,371 WAV recordings, 9,960 BirdNET Occurrences |
| smartwilds-drones | 39 videos, 15 flight sessions, 318,215 Occurrences |
| smartwilds-citizen-science | 1,103 media files, 622 Occurrences |
| smartwilds (study level) | merged Event table, text records, sensor configurations, arrival traces |

The current camera-trap tables are described in the
[camera-trap release note](../CAMERA_TRAP_RELEASE.md). Counts, inventories,
and every repair are in the [supplemental material](../SUPPLEMENTAL.md); the
defects themselves are in the [defect inventory](../DEFECT_INVENTORY.md).

## Using the data correctly

!!! warning "Pick a verification floor before analysis"
    Almost every Occurrence is a machine label, and the status vocabulary
    differs by table. Camera-trap labels carry a `labelProvenance`
    (`triage_resolved`, `triage_reviewed`, `triage_forced_1nn`, `human-edit`,
    `human-reviewed`); drone and acoustic labels are `unverified` or
    `validated`; the 12 human-added drone starling boxes are
    `human-supported; limited-resolution`. For the BioCLIP Tree-of-Life drone
    labels, species-rank accuracy on human-annotated subsets is 0.271 and
    class-rank accuracy is 0.845 (supplement, S9).

- **Occurrences are detection crops, not individuals.** Bursts and adjacent
  drone frames repeat the same animal.
- **Use the corrected timestamps.** Camera clocks were wrong on most
  deployments, and burned-in overlays show the raw clock. Every image carries
  its correction method and confidence (`images.csv`).
- **A zero `occurrence_count` is not evidence of absence.**
- **Report your choices.** State the unit of observation, the verification
  floor, and the timestamp policy alongside any derived metric.

## Where the files are

- The tables under 100 MB are in [`darwin_core/`](darwin-core-tables.md) in
  this repository. The three larger tables (merged Occurrences, camera image
  inventory, drone Occurrences) are listed there with their sizes and will be
  published with the datasets.
- The dataset cards, written to the FAIR² Drones and Imageomics templates, are
  in [`metadata/`](dataset-cards.md).
- The 2025 pilot media are already public in the
  [SmartWilds collection](https://huggingface.co/collections/imageomics/smartwilds)
  on Hugging Face.
