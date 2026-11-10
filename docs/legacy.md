# Legacy repositories and branches

Two earlier repositories preceded this one. [`Imageomics/naturelab`](https://github.com/Imageomics/naturelab)
remains the public home of the field logs, the field collection protocols,
the Google Earth site files, and the data-storage protocol; this repository
links to it rather than duplicating them. `Imageomics/wilds_multimodal_data`
was the internal working repository and is subsumed here as described below.

This repository subsumes the project's earlier working repository,
`Imageomics/wilds_multimodal_data`. Every branch of that repository was
brought over with its full history under the `legacy/wilds_multimodal_data/`
prefix, so nothing was lost, and `main` stays the curated metadata release.

| Branch | What it holds |
|---|---|
| `wip` (latest, 424 files) | The internal working tree: documentation (manuscripts, meeting notes, the ADAE arrival-rate model, the annotation pipeline), the experimental results of the systems analysis, and the Hugging Face release staging (cards, build scripts, people screening) |
| `sys-dataset-icde`, `add-documentation` | Earlier states of the same tree |
| `sam3_detection_pipeline` | The SAM3 text-prompted detection pipeline for drone imagery with optional BioCLIP enrichment, its performance benchmarks, and the camera-trap storage analysis |
| `smartwilds-analysis` | Early per-modality analysis: camera-trap detections with GPS for three deployments, BirdNET hourly and sunrise/sunset sheets, species heat-map notebooks. Part of the Milu-deer activity work (see below) |
| `copilot/create-heat-maps-for-sensors` | Heat-map generators per sensor modality |
| `citizen_science` | Early visitor-photo processing: MegaDetector v5 and BioCLIP detection, review tools, detection CSV format. Superseded by the labeling protocol of the holistic dataset |
| `deer_vocalizations` | YAMNet + XGBoost classifier for Père David's deer vocalizations in field recordings, trained on the `imageomics/pere-david-deer-vocalizations` dataset. Part of the Milu-deer activity work (see below) |
| `yuanyang-profile-scripts` | Benchmark scripts (YOLO, BioCLIP, BirdNET runtime on the benchmark subsets) and result tables |
| `main` | The original two-line README |

## The Milu-deer activity project

The camera-trap and acoustic analysis on `smartwilds-analysis` and the
`deer_vocalizations` classifier belong to a separate project by Bharath Pillai
and Varun Viswapriyan on annotation-free verification of Milu (Père David's)
deer activity, using deer calls and distance estimation. It has a workshop
paper, [Cross-Modal Corroboration for Annotation-Free Wildlife Monitoring](https://arxiv.org/abs/2606.21613),
and a journal paper under review.
That work uses its own labels and its own acoustic model; the holistic dataset
documented here uses a substantially updated labeling protocol (see the
[camera-trap release note](CAMERA_TRAP_RELEASE.md)). The two are kept
separate on purpose: nothing from those branches is merged into `main`, and
the numbers in this release should not be read as inputs to or outputs of that
paper.

## What was migrated

What belongs to the metadata release has been migrated into `main`: the
sensor configurations (`metadata/sensor_configurations.md`), the
documentation guidelines (`guidelines/`), the dataset cards, the defect
inventory, and the supplemental material. The labeling pipelines, model
experiments, and systems-paper results stay on their branches; they are a
different kind of artifact from the one this release documents.

To look at a legacy branch:

```bash
git fetch origin 'refs/heads/legacy/*:refs/remotes/origin/legacy/*'
git switch --detach origin/legacy/wilds_multimodal_data/sam3_detection_pipeline
```
