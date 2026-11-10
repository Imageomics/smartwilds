# Related repositories

Two earlier repositories preceded this one.

- [`Imageomics/naturelab`](https://github.com/Imageomics/naturelab) is the
  public home of the field logs, the field collection protocols, the Google
  Earth site files, and the data-storage protocol. This repository links to it
  rather than duplicating them.
- `Imageomics/wilds_multimodal_data` was the internal working repository. It
  is preserved here on the [`legacy-wilds_multimodal_data`](https://github.com/Imageomics/smartwilds/tree/legacy-wilds_multimodal_data)
  branch: one folder per former branch, with the full commit history in the
  branch's ancestry. `main` is the curated metadata release.

## The Milu-deer activity project

The camera-trap and acoustic analysis on the legacy branch belongs to a
separate project by Bharath Pillai and Varun Viswapriyan on annotation-free
verification of Milu (Père David's) deer activity, using deer calls and
distance estimation. It has a workshop paper,
[Cross-Modal Corroboration for Annotation-Free Wildlife Monitoring](https://arxiv.org/abs/2606.21613),
and a journal paper under review. That work uses its own labels and its own
acoustic model; the holistic dataset documented here uses a substantially
updated labeling protocol (see the [camera-trap release note](CAMERA_TRAP_RELEASE.md)).
The two are kept separate on purpose, and the numbers in this release should
not be read as inputs to or outputs of that paper.

## What was migrated

The sensor configurations (`metadata/sensor_configurations.md`), the
documentation guidelines (`guidelines/`), the dataset cards, the defect
inventory, the supplemental material, and the cross-modal coordination
analysis (`analysis/cross_modal_coordination/`) are in `main`. Labeling
pipelines, model experiments, and raw experiment outputs stay on the legacy
branch.
