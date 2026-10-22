# SmartWilds Hugging Face Release Staging

Last updated: 2026-10-22

This directory stages the SmartWilds datasets for Hugging Face. There is one
dataset (and one DOI) per modality, plus a study-level dataset. All five are
joined by the SmartWilds collection.

| Directory | Planned HF repo | Status |
|---|---|---|
| `hf_smartwilds_20261022/smartwilds-camera-traps` | `imageomics/smartwilds-camera-traps` | tables staged, checks pass |
| `hf_smartwilds_20261022/smartwilds-bioacoustics` | `imageomics/smartwilds-bioacoustics` | tables staged, checks pass |
| `hf_smartwilds_20261022/smartwilds-drones` | `imageomics/smartwilds-drones` | tables staged, checks pass |
| `hf_smartwilds_20261022/smartwilds-citizen-science` | `imageomics/smartwilds-citizen-science` | **blocked**: source tables are owner-only |
| `hf_smartwilds_20261022/smartwilds` | `imageomics/smartwilds` | **blocked**: `events_all_modalities.csv` is owner-only |

## Layout

Each dataset follows the layout of `imageomics/kabr-behavior-telemetry`:

- `README.md`: the dataset card (FAIR² and Darwin Core YAML front matter).
  The source for each card is in `cards/`.
- `data/`: the Darwin Core `events.csv` and `occurrences.csv`, plus per-file
  tables (`images.csv` for camera traps, `recordings.csv` for bioacoustics).
- `metadata/`: per-deployment sensor settings, `DATA_DICTIONARY.md`
  (generated), the geolocation and projection configs, and `provenance/`
  audit JSONs.
- `scripts/`: the generator, the georeferencing scripts, and the release
  build script.
- `media_manifest.csv`: one row per raw file, with its release path, size,
  include flag, exclusion reason, and (for camera traps) whether it has a human
  detection.
- `CHECKSUMS.sha256`: checksums for every staged file except the media.

## Rebuild

```bash
python3 -I release/scripts/build_hf_release.py          # all repos
python3 -I release/scripts/build_hf_release.py --only drones
```

The build reads the frozen snapshot `processing_output/darwin_core_latest_20261008`
and never modifies it. It applies two repairs to the staged copies only, and
records them in `hf_smartwilds_20261022/RELEASE_BUILD_AUDIT.json`:

1. **Re-timing curated camera records.** 439 curated camera-trap Occurrences are
   re-timed from the corrected camera timestamp map. Before the fix, 124 were
   dated 2025-09-14 and 315 carried only the deployment interval.
2. **Release-relative media paths.** All `associatedMedia` values are rewritten
   to paths relative to the release. The 10,943 drone rows that pointed at
   purged scratch frames now point at their original videos.

The build also runs the checks that the snapshot audit lacked:

- each Occurrence date lies inside its parent Event's span and inside the study
  window;
- no cluster paths remain in any cell;
- every `associatedMedia` value resolves to an included file in the media
  manifest.

## Before upload (decisions and blockers)

1. **Permissions.** potlapally2 needs to run `chmod g+r` on
   `processing_output/darwin_core_latest_20261008/events_all_modalities.csv`,
   `.../events_all_modalities.before_root_parity_repair_20261010.csv`, and
   `.../citizen_science/*.csv`. Then rebuild.
2. **People in imagery.** 10,797 camera images have at least one *Homo sapiens*
   detection (`has_human_detection`), and 3,114 drone Occurrences are labelled
   human. Decide whether to withhold, blur, or release these images, and
   whether blank images need screening.
3. **Citizen-science consent.** Confirm that visitor submissions may be
   redistributed, and under which license.
4. **License.** The cards say CC0-1.0, following the Imageomics default and
   KABR. The manuscript said "CC BY 4.0 assumed". Pick one license for all
   five datasets.
5. **Media packaging.** The camera dataset has about 241k files. Hugging Face
   recommends fewer than 100k files per repo, so pack the camera media as tar
   shards per deployment/SD card and add a `shard` column to
   `media_manifest.csv`. The logical `release_path` stays the same. The WAV
   files (2,393) and drone files (77) can be uploaded as individual files.
6. **DOIs.** Mint one DOI per dataset after upload, then fill in the `doi`
   fields in the cards and the manuscript.

## Upload (not yet run)

```bash
hf upload-large-folder imageomics/smartwilds-bioacoustics \
    release/hf_smartwilds_20261022/smartwilds-bioacoustics --repo-type dataset --private
```

Create each repo as private first, and review it before making it public. Add
the five repos to an `imageomics` collection named "SmartWilds".
