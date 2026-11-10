# Legacy: Imageomics/wilds_multimodal_data

The earlier working repository of the SmartWilds project, condensed into one
branch. Each folder is the final tree of one of its branches; the full commit
history of every branch is in this branch's ancestry (`git log --all` from
here reaches all of it).

| Folder | Former branch | What it holds |
|---|---|---|
| `working_tree/` | the main working branch | Documentation (manuscripts, notes, the ADAE arrival-rate model, the annotation pipeline), the experiment harness outputs of the systems analysis, and the Hugging Face release staging |
| `sam3_detection_pipeline/` | `sam3_detection_pipeline` | SAM3 text-prompted detection pipeline for drone imagery with optional BioCLIP enrichment, performance benchmarks, camera-trap storage analysis |
| `data_analysis/` | `smartwilds-analysis` | Early per-modality analysis and heat-map notebooks (Milu-deer activity project) |
| `deer_vocalizations/` | `deer_vocalizations` | Classifier for Père David's deer vocalizations (Milu-deer activity project) |
| `benchmarks/` | `yuanyang-profile-scripts` | YOLO, BioCLIP, and BirdNET runtime benchmarks and result tables |
| `citizen_science_processing/` | `citizen_science` | Early visitor-photo detection and review tools |
| `heatmaps/` | `copilot/create-heat-maps-for-sensors` | Heat-map generators per sensor modality |

Nothing here is part of the SmartWilds release. The curated metadata release,
its documentation, and the cross-modal coordination analysis are on `main`.
Files in these folders may contain cluster-specific paths and internal notes.
