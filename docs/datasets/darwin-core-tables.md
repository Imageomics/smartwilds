# Darwin Core tables

The Darwin Core Event and Occurrence tables of the SmartWilds release are
published as one Hugging Face dataset,
[`ABC-Center/smartwilds_metadata`](https://huggingface.co/datasets/ABC-Center/smartwilds_metadata),
part of the [SmartWilds collection](https://huggingface.co/collections/ABC-Center/smartwilds-6af3c0aac0a67864cbf6edb4).
It holds the five components of the release, each a complete FAIR² package,
plus the supplemental material:

```
smartwilds_metadata/
├── README.md                      # dataset card
├── SUPPLEMENTAL.md
├── smartwilds-camera-traps/       # 19,785 Events, 72,775 Occurrences, 235,778-image inventory
├── smartwilds-bioacoustics/       # 2,382 Events, 9,960 Occurrences, 2,371 recordings
├── smartwilds-drones/             # 55 Events, 318,215 Occurrences, frame-indexed detections
├── smartwilds-citizen-science/    # 14 Events, 622 Occurrences
└── smartwilds/                    # study level: merged tables, text records, arrival traces
    └── <component>/
        ├── README.md              # component dataset card
        ├── data/                  # events.csv, occurrences.csv, per-file tables
        ├── metadata/              # DATA_DICTIONARY.md, deployments, configs, provenance/
        ├── media_manifest.csv
        └── CHECKSUMS.sha256
```

Release build 2026-10-22; camera and merged tables updated 2026-11-08. All
tables share one Event hierarchy rooted at `TheWilds_2025`.

## Getting the tables

```bash
pip install huggingface_hub
huggingface-cli download --repo-type dataset ABC-Center/smartwilds_metadata --local-dir smartwilds_metadata
python examples/quickstart.py smartwilds_metadata/smartwilds-camera-traps smartwilds_metadata/smartwilds-bioacoustics
```

Or load one table directly:

```python
import pandas as pd
oc = pd.read_csv("hf://datasets/ABC-Center/smartwilds_metadata/smartwilds-camera-traps/data/occurrences.csv",
                 dtype=str, keep_default_na=False)
```

## Column definitions

Each component's `metadata/DATA_DICTIONARY.md` defines its columns. The Darwin
Core terms follow <https://dwc.tdwg.org/terms/>; SmartWilds-specific columns
(`labelProvenance`, `geometryProvenance`, `triageRound`, the timestamp
correction fields of `images.csv`, the privacy screening fields of the media
manifests) are defined in the [supplemental material](../SUPPLEMENTAL.md#s12-darwin-core-field-dictionary).
