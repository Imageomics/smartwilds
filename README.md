# SmartWilds: integration, alignment, and release code

This repository holds the code and documentation that turn the SmartWilds field
campaigns into the released datasets. SmartWilds is a multi-modal sensing
dataset recorded with camera traps, acoustic recorders, drones, and visitor
photographs at [The Wilds](https://thewilds.columbuszoo.org/) (Cumberland,
Ohio) in summer 2025.

![Sensor deployment across The Wilds](metadata/images/smartwilds/deployment_map.png)
*Sensor deployment across The Wilds: camera traps with viewing angles, Song Meter recorders, citizen-science photo locations, and drone flight tracks. Satellite imagery © Google.*

![The same three species seen by camera trap, drone, and citizen science](metadata/images/smartwilds/cross_modal_preview.png)
*The same three managed focal species (Sichuan takin, Milu deer, Przewalski's horse) observed by camera trap, drone, and citizen-science photography.*

## Camera-trap release (2026-11-08)

The current camera-trap release (`smartwilds-camera-traps`) contains 72,775
retained Occurrences with original SAM3 geometry on 19,785 camera Events, and
the full 235,778-image inventory. The merged multimodal tables contain 22,242
Events and 401,602 unique Occurrences. See
[`docs/CAMERA_TRAP_RELEASE.md`](docs/CAMERA_TRAP_RELEASE.md) for the
annotation method and provenance.

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
| `docs/DEFECT_INVENTORY.md` | All 22 defect classes found during integration: scope, what detected each, the repair, and the residual risk |
| `docs/CAMERA_TRAP_RELEASE.md` | Scope and label provenance of the 2026-11-08 camera-trap release |
| `docs/AGENT_ASSISTED_DOCUMENTATION.md` | How LLM coding agents were used to inventory, document, and quality-check the data, and the guidelines they were given |
| `metadata/` | The dataset cards of the five SmartWilds datasets, the defect inventory, and the card images |
| `field_campaigns/` | Field notes, data summaries, and per-campaign data reports |
| `darwin_core/` | Interim copy of the current Darwin Core tables (those under 100 MB) until the datasets are published |
| `scripts/README.md` | What each script does, its inputs and outputs, and the environment variables it reads |
| `scripts/darwin_core/` | Darwin Core Event and Occurrence generator, and raw-WAV reconciliation |
| `scripts/georeferencing/` | Camera-trap (pinhole model) and drone (ground-ray) projection, with their configs |
| `scripts/validation/` | Release audit: parent links, parsed dates/times/coordinates, sentinel rejection, media resolution |
| `scripts/arrival_traces/` | Versioned acquisition- and detection-layer arrival traces |
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

- **Pick a verification floor before analysis.** Almost every Occurrence is a
  machine label, and the status vocabulary differs by table. The current
  camera release has 70,728 `triage_resolved`, 1,807 `triage_reviewed`, 199
  `triage_forced_1nn`, 39 `human-edit`, and two `human-reviewed` labels; every
  retained camera box has original SAM3 geometry. Drone and acoustic labels are `unverified`
  or `validated`; the 12 human-added drone starling boxes are
  `human-supported; limited-resolution`. For the BioCLIP Tree-of-Life drone
  labels, species-rank accuracy on human-annotated subsets is 0.271 and
  class-rank accuracy is 0.845. A seven-video human-annotated drone reference
  set (27,159 boxes) is described in `docs/SUPPLEMENTAL.md` S9.
- **Occurrences are detection crops, not individuals.** Bursts and adjacent
  drone frames repeat the same animal.
- **Use the corrected timestamps.** Camera clocks were wrong on most
  deployments, and burned-in overlays show the raw clock. Every image carries
  its correction method and confidence.
- **Report your choices.** State the unit of observation, the verification
  floor, and the timestamp policy alongside any derived metric. See the paper's
  discussion of statistical validity.

## Reproducing the release

The scripts record the pipeline as it was run against the field archive.
Input locations come from environment variables (`SMARTWILDS_ARCHIVE` for the
archive root, `SMARTWILDS_DWC_OUT` for the generated tables, and a few
script-specific ones); `scripts/README.md` lists them. Given the same inputs the
tables are regenerated deterministically:

```bash
export SMARTWILDS_ARCHIVE=/path/to/TheWilds2025
python scripts/darwin_core/generate_darwin_core.py --force
python scripts/validation/audit_darwin_core_snapshot.py --root "$SMARTWILDS_DWC_OUT"
python scripts/arrival_traces/generate_arrival_traces_v2.py
```

Packaging the tables into the per-modality Hugging Face datasets is done in the
project's internal release staging and is not part of this repository.

Person screening needs a GPU and MegaDetector v5a (`pip install megadetector`).
`scripts/privacy_screening/run_screening.sh` is the SLURM job we used.

## Citation

See `CITATION.cff`. Please cite the paper and each modality dataset you use.

## Papers using SmartWilds

```bibtex
@inproceedings{kline2026blueprint,
  author    = {Kline, Jenna and Potlapally, Anirudh and Subramoni, Hari and Berger-Wolf, Tanya and Stewart, Christopher},
  title     = {A Blueprint for Cross-Modal Coordination at the Far Edge},
  booktitle = {ACM/IEEE Symposium on Edge Computing (SEC)},
  year      = {2026},
  note      = {To appear}
}

@inproceedings{pillai2026cross,
  author    = {Pillai, Bharath and Viswapriyan, Varun and Stewart, Christopher and Berger-Wolf, Tanya and Kline, Jenna},
  title     = {Cross-Modal Corroboration for Annotation-Free Wildlife Monitoring},
  booktitle = {CV4Animals Workshop at the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  year      = {2026}
}
```

If you publish work that uses SmartWilds, open an issue or pull request and we
will add it here.

## License

Code: MIT (see `LICENSE`). Data: see each dataset card.
<!-- TODO(license): confirm data license across the collection -->

## Acknowledgements

Supported by the Imageomics Institute (NSF Award #2118240), ICICLE (NSF Award
#2112606), and the ABC Global Center (NSF Award #2330423; NSERC Award #585136).
We thank Dan Beetem, The Wilds, and the Columbus Zoo & Aquarium.

## Contact

Jenna M. Kline (kline.377@osu.edu)
