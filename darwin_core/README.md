# Darwin Core tables (interim copy)

Temporary home for the current SmartWilds Darwin Core tables while the datasets
are being prepared for Hugging Face. These are copies of the `data/` directory
of each staged dataset (release build 2026-10-22; camera and merged tables
updated 2026-11-08). The datasets themselves, with media manifests, metadata,
provenance records, and checksums, are the release of record; this directory
will be removed once they are published.

| File | Size | Status |
|---|---:|---|
| `smartwilds/events_all_modalities.csv` | 7.7 MB | copied |
| `smartwilds/occurrences_all_modalities.csv` | 521.6 MB | too large for GitHub |
| `smartwilds/text_events.csv` | 0.0 MB | copied |
| `smartwilds/text_occurrences.csv` | 0.0 MB | copied |
| `smartwilds/site_selection_rationale.csv` | 0.0 MB | copied |
| `smartwilds-camera-traps/events.csv` | 8.3 MB | copied |
| `smartwilds-camera-traps/occurrences.csv` | 67.3 MB | copied |
| `smartwilds-camera-traps/images.csv` | 139.2 MB | too large for GitHub |
| `smartwilds-bioacoustics/events.csv` | 1.7 MB | copied |
| `smartwilds-bioacoustics/occurrences.csv` | 6.5 MB | copied |
| `smartwilds-bioacoustics/recordings.csv` | 1.1 MB | copied |
| `smartwilds-drones/events.csv` | 0.0 MB | copied |
| `smartwilds-drones/occurrences.csv` | 431.5 MB | too large for GitHub |
| `smartwilds-drones/detections.csv` | 78.3 MB | copied |
| `smartwilds-citizen-science/events.csv` | 0.0 MB | copied |
| `smartwilds-citizen-science/occurrences.csv` | 0.5 MB | copied |

GitHub rejects files over 100 MB, so the three large tables are not here. They
are in the staged datasets and will be published with them.

The tables share one Event hierarchy rooted at `TheWilds_2025`. Column
definitions are in each dataset's `metadata/DATA_DICTIONARY.md`; the
verification-status vocabulary differs by table (see `docs/SUPPLEMENTAL.md`,
S9.3).
