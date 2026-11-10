# Scripts

The code that turns the SmartWilds field archive into the released Darwin Core
tables, and the checks that were run on them. Every script reads its input
locations from environment variables, so nothing here depends on the layout of
the machine the pipeline originally ran on.

| Variable | Used by | Meaning |
|---|---|---|
| `SMARTWILDS_ARCHIVE` | all | Root of the field archive (the `thewilds_<campaign>/` directories and `processing_output/`). Default: current directory |
| `SMARTWILDS_DWC_OUT` | `darwin_core/` | Where the generated Darwin Core tables are written. Default: `<archive>/processing_output/darwin_core_release` |
| `SMARTWILDS_DETECTIONS` | `darwin_core/generate_darwin_core.py` | External SAM3 + BioCLIP detection workspace (per-video prediction CSVs) |
| `SMARTWILDS_RELEASE` | `privacy_screening/trim_drones.py` | Root of the staged per-modality datasets |
| `SMARTWILDS_SCRUBBED_MEDIA` | `privacy_screening/trim_drones.py` | Output directory for trimmed drone videos |
| `MEGADETECTOR_WEIGHTS` | `privacy_screening/screen_videos.py` | Path to `md_v5a.0.0.pt` |
| `CAMERA_TRAP_GEOLOCATION_SRC` | `georeferencing/geolocate_camera_trap_treeoflife_predictions.py` | `src/` directory of a checkout of Imageomics/camera-trap-geolocation |

## `darwin_core/` — build the tables

| Script | What it does |
|---|---|
| `generate_darwin_core.py` | Builds the Darwin Core Event and Occurrence tables for every modality and merges them. Camera traps: SAM3 + BioCLIP Tree-of-Life prediction CSVs, geolocated animal positions, and the corrected camera timestamp map. Bioacoustics: BirdNET result files, with taxonomy filled from the raw results. Drones: labeled detection CSVs with telemetry. Citizen science and text records are copied from their Darwin Core exports. The "Tree-of-Life prediction CSVs" are the per-box outputs of BioCLIP 2 (`imageomics/bioclip-2`, trained on TreeOfLife-200M) in open-world Tree of Life mode: for each SAM3 box, the top-1 taxon with its rank hierarchy (kingdom to species) and the top-5 candidates. They were produced in the external detection workspace; the code that wrote them is not in this repository. Writes `events_all_modalities.csv`, `occurrences_all_modalities.csv`, per-modality tables, and `QC_SUMMARY.md` under `SMARTWILDS_DWC_OUT`. `--force` overwrites an existing output |
| `reconcile_bioacoustic_raw_wavs.py` | Walks the raw WAV directories of both campaigns, matches every file to its BirdNET result and its `AudioRecording` Event, and classifies each path (released, zero-detection recording added as an Event, transfer duplicate, truncated or unreadable). Writes `RAW_WAV_RECONCILIATION_*.csv/.md` and the Event-repair audit JSON next to the bioacoustic tables |

## `validation/` — audit the tables

| Script | What it does |
|---|---|
| `audit_darwin_core_snapshot.py` | Read-only integrity audit of a generated table set (`--snapshot-dir`). Checks that every modality row appears unchanged in the merged tables, that the Event hierarchy has one root and no orphans or cycles, that every Occurrence links to an Event of the right modality, that dates, times, and coordinates parse and sentinel strings (`nan`, `-1`, epoch dates) are absent, and that local `associatedMedia` paths resolve. Writes a JSON and Markdown report named by `--stem` |

## `arrival_traces/` — workload traces for the systems analysis

| Script | What it does |
|---|---|
| `generate_arrival_traces_v2.py` | Derives the Campaign-2 arrival streams from the Darwin Core tables (run it from the `scripts/` directory of a table set). One stream per modality and layer: acquisition (one WAV recording per arrival) and inference (one retained Occurrence per arrival). Each output row links back to its source Event or Occurrence; the companion `arrival_trace_contract_v2.json` and `input_manifest_v2.json` record units, inclusion rules, date window, and checksums |

## `georeferencing/` — animal positions from detections

| Script | What it does |
|---|---|
| `geolocate_camera_trap_treeoflife_predictions.py` | Pinhole-model projection of camera-trap detection boxes to ground coordinates, using each camera's GPS position, bearing, horizontal field of view, and an assumed target height (`camera_geolocation_config.csv`). Wraps the geometry of Imageomics/camera-trap-geolocation |
| `geolocate_drone_treeoflife_predictions.py` | Ground-ray projection of drone detection boxes using the aircraft's telemetry (position, altitude, gimbal pitch) and per-platform field of view (`drone_projection_config.csv`). Every row carries a projection status (`ok`, `invalid_altitude`, `missing_drone_gps`, `horizon_ray`, `out_of_range`) |
| `camera_geolocation_config.csv`, `drone_projection_config.csv` | The configurations used for the release |

## `privacy_screening/` — people in the media

Person screening with MegaDetector v5a, then triage by identifiability. A
person whose box is shorter than 80 px in the native image cannot be identified
and the file is released as is; anything larger goes to human review.

| Script | What it does |
|---|---|
| `make_lists.py` | Lists every camera-trap and citizen-science still (sharded) and every video under the campaign directories, excluding the withdrawn TW07-CT05 deployment |
| `run_screening.sh` | SLURM array job: MegaDetector batch runs on the image shards and `screen_videos.py` on the video halves. Needs a GPU and a virtual environment with `megadetector`, `av`, and `imageio-ffmpeg` |
| `screen_videos.py` | Samples frames (1 s for camera and visitor clips, 2 s for drone videos) and records every frame with a person detection as a JSON line |
| `triage.py` | Turns the detector output into `person_screening_images.csv` and `person_screening_videos.csv` with a `release` / `review` decision per file, and renders crop sheets for the review queue |
| `trim_drones.py` | For drone videos with people near launch or landing, plans lossless start/end trims (`plan`) and applies only the rows a reviewer has marked `approved=yes` (`apply`). People in mid-flight frames are listed for review, never auto-trimmed |

Packaging the tables into the per-modality Hugging Face datasets and rendering
the dataset cards happens in the project's internal release staging and is not
part of this repository.
