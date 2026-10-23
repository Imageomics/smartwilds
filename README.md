# SmartWilds: integration, alignment, and release code

This repository holds the code and documentation that turn the SmartWilds field
campaigns into the released datasets. SmartWilds is a multi-modal sensing
dataset recorded with camera traps, acoustic recorders, drones, and visitor
photographs at [The Wilds](https://thewilds.columbuszoo.org/) (Cumberland,
Ohio) in summer 2025.

- **Data:** one Hugging Face dataset per modality, joined by the
  SmartWilds collection <!-- TODO: collection URL + per-modality repo links/DOIs -->
- **Field protocols, forms, and logs:**
  [Imageomics/naturelab](https://github.com/Imageomics/naturelab)
- **Paper:** *SmartWilds: Integrating, Aligning, and Documenting Multi-Modal
  Field Sensing Data* (under review)
- **Earlier release:** the 2025 four-day pilot release,
  [arXiv:2509.18894](https://arxiv.org/abs/2509.18894)

## What is here

| Path | Contents |
|---|---|
| `docs/SUPPLEMENTAL.md` | The paper's supplemental material: glossary, per-deployment inventories, the 18 timestamp-repair methods, drone ground projection, standards crosswalk, typed missingness, model accuracy, validation checks, field dictionary, and arrival statistics |
| `docs/DEFECT_INVENTORY.md` | All 20 defect classes found during integration: scope, what detected each, the repair, and the residual risk |
| `scripts/darwin_core/` | Darwin Core Event and Occurrence generator, and raw-WAV reconciliation |
| `scripts/georeferencing/` | Camera-trap (pinhole model) and drone (ground-ray) projection, with their configs |
| `scripts/validation/` | Release audit: parent links, parsed dates/times/coordinates, sentinel rejection, media resolution |
| `scripts/arrival_traces/` | Versioned acquisition- and detection-layer arrival traces |
| `scripts/release/` | Builds the per-modality Hugging Face packages and renders dataset cards to PDF |
| `scripts/privacy_screening/` | MegaDetector person screening, triage by identifiability, and a review-first drone launch/landing trim plan |
| `examples/quickstart.py` | Load the tables, apply a verification floor, walk the Event hierarchy, and extract a drone frame |

## Quickstart

```bash
pip install -r requirements.txt
huggingface-cli download --repo-type dataset <camera-trap repo> --local-dir smartwilds-camera-traps
python examples/quickstart.py smartwilds-camera-traps
```

Pass several dataset folders to combine modalities. They share one Event
hierarchy, rooted at `TheWilds_2025`.

## Using the data correctly

- **Pick a verification floor before analysis.** 99.6% of Occurrences are
  `unverified` machine predictions. Species-rank accuracy on human-annotated
  subsets is 0.271, while class-rank accuracy is 0.845.
- **Occurrences are detection crops, not individuals.** Bursts and adjacent
  drone frames repeat the same animal.
- **Use the corrected timestamps.** Camera clocks were wrong on most
  deployments, and burned-in overlays show the raw clock. Every image carries
  its correction method and confidence.
- **Report your choices.** State the unit of observation, the verification
  floor, and the timestamp policy alongside any derived metric. See the paper's
  discussion of statistical validity.

## Reproducing the release

The scripts record the pipeline exactly as it was run on the Ohio
Supercomputer Center. Input locations are set as constants at the top of each
script (for example `ROOT`, `SNAP`), so edit those to point at your copy of
the data. The release build is deterministic given the frozen snapshot:

```bash
python scripts/darwin_core/generate_darwin_core.py --force
python scripts/validation/audit_darwin_core_snapshot.py
python scripts/arrival_traces/generate_arrival_traces_v2.py
python scripts/release/build_hf_release.py
```

Person screening needs a GPU and MegaDetector v5a (`pip install megadetector`).
`scripts/privacy_screening/run_screening.sh` is the SLURM job we used.

## Citation

See `CITATION.cff`. Please cite the paper and each modality dataset you use.

## License

Code: MIT (see `LICENSE`). Data: see each dataset card.
<!-- TODO(license): confirm data license across the collection -->

## Acknowledgements

Supported by the Imageomics Institute (NSF Award #2118240), ICICLE (NSF Award
#2112606), and the ABC Global Center (NSF Award #2330423; NSERC Award #585136).
We thank Dan Beetem, The Wilds, and the Columbus Zoo & Aquarium.

## Contact

Jenna M. Kline (kline.377@osu.edu)
