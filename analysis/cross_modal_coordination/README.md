# Cross-Modal Coordination at the Far Edge

Scripts to generate synthetic multi-modal sensor traces and reproduce the
results in:

> **A Blueprint for Cross-Modal Coordination at the Far Edge**
> Jenna Kline, Anirudh Potlapally, Yuanyang Cheng, Tanya Berger-Wolf,
> Hari Subramoni, Christopher Stewart. To appear.

Part of [SmartWilds](https://github.com/Imageomics/smartwilds). The dataset is a
24-day multi-modal deployment at The Wilds conservation center, with four
event-bearing modalities: camera traps, bioacoustic monitors, drones, and
citizen science.

## What this does

The paper's method is *record → characterize → synthesize*. This repository
implements the second and third phases:

| Phase | What it produces | Where |
|---|---|---|
| **Characterize** | workload model `W = {ρ, B, C, φ}` per modality | `scripts/01_characterize/` |
| **Synthesize** | `synth(W, c, s) → T*`, a synthetic multi-modal trace | `scripts/02_synthesize/` |
| **Case studies** | the four coordination scenarios CS1–CS4 | `scripts/03_case_studies/` |
| **Fidelity** | variance-bound and topology-scaling checks | `scripts/04_fidelity/` |
| **Feasibility** | predicted hardware × policy grid | `scripts/05_feasibility/` |
| **Figures** | paper figures 3, 5, 7 and appendix 3, 4 | `scripts/figures/` |
| **Supplement** | tables and figures cut from the camera-ready, in markdown | `supplement/` |

Synthesis is deterministic: the same recipe and seed always produce the same
trace.

## Quickstart

```bash
pip install -r requirements.txt

# Generate one case-study trace
python3 scripts/03_case_studies/generate_traces.py --case CS2 --intensity 1

# Or reproduce everything the repo can standalone
./run_all.sh
```

No configuration is needed — the shipped workload primitives in `data/` are
enough to synthesize all four modalities. Paths are resolved by
`scripts/paths.py` and can be overridden with environment variables
(`SMARTWILDS_DATA`, `SMARTWILDS_RESULTS`, …) if your data lives elsewhere.

## Verified reproductions

Identity synthesis (`c = c_identity`) re-emits the recorded event counts:

| Modality | Synthesized | Recorded (Table II) | Ratio |
|---|---:|---:|---:|
| Camera traps | 189,118 | 189,289 | 0.999 |
| Bioacoustic | 1,537 | 1,570 | 0.979 |
| Drones | 98,448 | 98,335 | 1.001 |
| Citizen science | 145 | 139 | 1.043 |

Regenerating `CS2_acoustic_to_ct_1x` reproduces the original trace exactly:
395,894 events (394,412 camera trap, 1,482 bioacoustic).

## Layout

```
cross_modal_coordination/
├── data/
│   ├── primitives/       # workload model per modality (shipped)
│   └── timestamps/       # derived event tables for bootstrap modalities
├── scripts/
│   ├── paths.py          # portable path resolution
│   ├── 00_prepare/       # derive event tables from the field archive
│   ├── 01_characterize/  # → primitives
│   ├── 02_synthesize/    # synthesis engine + identity test
│   ├── 03_case_studies/  # CS1–CS4 recipes and driver
│   ├── 04_fidelity/      # variance envelope, topology scaling
│   ├── 05_feasibility/   # hardware prediction grid
│   └── figures/          # paper figures
├── supplement/           # cut tables + figures, rendered as markdown
├── run_all.sh
└── REPRODUCIBILITY.md    # what reproduces, and what is missing
```

**Read [REPRODUCIBILITY.md](REPRODUCIBILITY.md) before relying on any number.**
Several results in §V-C depend on artifacts that are not in this repository.

## Citation

```bibtex
@inproceedings{kline2026blueprint,
  title     = {A Blueprint for Cross-Modal Coordination at the Far Edge},
  author    = {Kline, Jenna and Potlapally, Anirudh and Cheng, Yuanyang and
               Berger-Wolf, Tanya and Subramoni, Hari and Stewart, Christopher},
  booktitle = {ACM/IEEE Symposium on Edge Computing (SEC)},
  year      = {2026}
}
```
