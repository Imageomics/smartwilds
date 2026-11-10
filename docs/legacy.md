# Legacy branches

This repository subsumes the project's earlier working repository,
`Imageomics/wilds_multimodal_data`. Every branch of that repository was
brought over with its full history under the `legacy/wilds_multimodal_data/`
prefix, so nothing was lost, and `main` stays the curated metadata release.

| Branch | What it holds |
|---|---|
| `mosaic-wip` (latest, 424 files) | The internal working tree: documentation (manuscripts, meeting notes, the ADAE arrival-rate model, the annotation pipeline), the experimental results of the systems analysis, and the Hugging Face release staging (cards, build scripts, people screening) |
| `sys-dataset-icde`, `add-documentation` | Earlier states of the same tree |
| `sam3_detection_pipeline` | The SAM3 text-prompted detection pipeline for drone imagery with optional BioCLIP enrichment, its performance benchmarks, and the camera-trap storage analysis |
| `smartwilds-analysis` | Early per-modality data-analysis notebooks and heat maps |
| `copilot/create-heat-maps-for-sensors` | Heat-map generators per sensor modality |
| `citizen_science` | Visitor-photo processing: MegaDetector v5 and BioCLIP detection, review tools, detection CSV format |
| `deer_vocalizations` | A small YAMNet + XGBoost classifier for deer vocalizations in field recordings |
| `yuanyang-profile-scripts` | Benchmark scripts (YOLO, BioCLIP, BirdNET runtime on the benchmark subsets) and result tables |
| `main` | The original two-line README |

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
