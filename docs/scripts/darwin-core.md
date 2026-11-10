# Darwin Core generation

`scripts/darwin_core/` builds the Event and Occurrence tables that the whole
release rests on.

## `generate_darwin_core.py`

Builds the Darwin Core tables for every modality and merges them into
`events_all_modalities.csv` and `occurrences_all_modalities.csv`.

| Modality | Inputs | What the script does |
|---|---|---|
| Camera traps | SAM3 + BioCLIP Tree-of-Life prediction CSVs, geolocated animal positions, the corrected camera timestamp map | One `SensorDeployment` Event per camera deployment, one Occurrence per retained detection box; dates and times from the corrected timestamps |
| Bioacoustics | BirdNET result files (hourly and sunrise/sunset schedules) | One `AudioRecording` Event per WAV, one Occurrence per recording × species with `individualCount` = detections; taxonomy filled from the raw results |
| Drones | Labelled detection CSVs with telemetry | One `SensorDeployment` per flight, one `MediaEvent` per video, one Occurrence per detection crop |
| Citizen science, text | Their Darwin Core exports | Copied into the table set |

The "Tree-of-Life prediction CSVs" are the per-box outputs of BioCLIP 2
(`imageomics/bioclip-2`, trained on TreeOfLife-200M) in open-world Tree of
Life mode: for each SAM3 box, the top-1 taxon with its rank hierarchy (kingdom
to species) and the top-5 candidates, as recorded in `identificationRemarks`
(`Tree-of-Life rank`, `top1 score`). They were produced in the external
detection workspace; the code that wrote them is not in this repository.

```bash
export SMARTWILDS_ARCHIVE=/path/to/TheWilds2025
export SMARTWILDS_DWC_OUT=$SMARTWILDS_ARCHIVE/processing_output/darwin_core_release
python scripts/darwin_core/generate_darwin_core.py --force
```

`--force` overwrites an existing output directory. The script also writes
`QC_SUMMARY.md` (row counts, distinct values, date ranges per table) and a
`citizen_science_media_reconciliation_*.json` audit of which visitor files are
referenced by Occurrences.

!!! note "Hardened generation"
    The generator writes a fresh, non-destructive table set and never edits an
    existing one. Repairs to released tables (the drone `nan` dates, the study
    root Event, the WAV reconciliation) each left a `*.before_*` copy and a JSON
    audit record; the supplemental material (S10, S14) describes each.

## `reconcile_bioacoustic_raw_wavs.py`

Walks the raw WAV directories of both campaigns, matches every file to its
BirdNET result and to its `AudioRecording` Event, and classifies each path:

- released, with a non-empty BirdNET result;
- processed but zero detections (header-only result): added as an Event with
  no Occurrences;
- transfer duplicate (a campaign-1 file copied under a campaign-2 directory);
- truncated or unreadable.

```bash
python scripts/darwin_core/reconcile_bioacoustic_raw_wavs.py
```

Writes `RAW_WAV_RECONCILIATION_*.csv` (one row per raw path) and `.md` next
to the bioacoustic tables, plus the Event-repair audit JSON. This is how defect
10 in the [defect inventory](../DEFECT_INVENTORY.md) was found and repaired.
