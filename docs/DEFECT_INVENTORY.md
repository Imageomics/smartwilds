# SmartWilds defect inventory

Every defect class found while integrating the SmartWilds campaigns (release
build 2026-10-22; camera tables updated 2026-11-08). **Detected by** is
what made the defect visible, grouped into five families: an external record
(service log, field note, platform documentation), a redundant encoding inside
the data, a cross-check between two artifacts, human inspection, or nothing.
Rows 19-20 had no second record and could be bounded but not repaired.
Rows 21-22 were found after the 2026-11-01 annotation update and were
repaired in the release build (row 21) and the 2026-11-08 camera update (row 22).

| # | Defect | Mod. | Scope | Detected by (family) | Repair | Residual risk |
|---:|---|---|---|---|---|---|
| 1 | Device clock wrong or unset | Cam | 221,306 / 235,778 images (93.9%) | Service log deploy/retrieve times (External record) | 18 per-deployment reconstruction methods (paper §timestamp reconstruction; S5) | 130,290 images (55.3%) only medium confidence |
| 2 | Clock reset to factory epoch | Cam | 2 deployments, 1 reporting year 2023 | Service log; implausible date on its face (External record) | Anchored offset from known deploy time | Offset assumed constant over deployment |
| 3 | Media split across SD cards with inconsistent clocks | Cam | TW02-CT01 (4 clock states), TW09-CT02 (2), TW06-CT04 (2), TW04-CT03 (2) | Card-level directory structure + service log (External record) | Per-card anchors reconciled against logs | Within-card drift unmodeled |
| 4 | Timestamp only in burned-in overlay | Cam | 182 images (TW06-CT05, TW09-CT05, TW11-CT06) | The image itself (redundant in-frame encoding) (Redundant encoding in data) | OCR of bottom overlay; 3 read manually | OCR errors on 179 automated reads |
| 5 | Camera mounted inverted | Cam | TW04-CT04, 570 images | Human review of imagery (Human inspection) | Flagged; images rotated downstream | --- |
| 6 | Camera relocated mid-deployment | Cam | TW09-CT02 (dock → Nomad Ridge W, Aug 18) | Field note recording the move (External record) | Split into two logical location intervals | Single `locationID` spans both |
| 7 | Battery exhaustion | Cam | TW02-CT01 Aug 18--25; TW02-CT03 C1 (55 files) | Capture gap vs. logged deployment window (Cross-check) | Recorded as a failure gap with cause | Lost observation window unrecoverable |
| 8 | Non-wildlife content (visitors) | Cam | TW07-CT05, whole deployment | Human review of imagery (Human inspection) | People-only imagery not uploaded; deployment excluded from release | Card disposition after field not documented |
| 9 | Recorder ran a schedule other than configured | ARU | TW05-SM01 C1 (144 files) | File inventory vs. intended config (Cross-check) | Actual schedule inferred and documented | Intended vs. actual effort differ |
| 10 | WAV files with no event record | ARU | 146 / 2,453 paths (6.0%) | File inventory vs. event table (Cross-check) | Classified per path: 64 zero-detection recordings added as Events; 78 transfer duplicates and 4 failed files excluded | 4 fragments/unreadable files unrecoverable |
| 11 | Heterogeneous telemetry schemas | Drone | 3 platforms, 3 formats, feet vs. metres | Platform documentation (External record) | Per-platform field mapping with unit conversion | Mapping assumptions per platform |
| 12 | Drone video not processed | Drone | 1 / 39 raw videos | File inventory vs. event table (Cross-check) | Reviewed (no usable content); retained as a zero-Occurrence `MediaEvent` | --- |
| 13 | Media references to purged scratch workspace | Drone | 16,069 frame paths, 307,260 Occ. | Resolving every `associatedMedia` path (Cross-check) | Replaced with the retained original video, flagged as a video-level fallback | Frame-level media link lost for those rows |
| 14 | Unreviewed fine-rank taxon labels | Cam, Drone | Merged snapshot: 550,722 Occ. `unverified` (99.6%); post-triage camera table: 71,009 Occ. `machine-resolved` (97.6%) | Human-annotated validation subsets (Human inspection) | Camera labels replaced by embedding-based triage with human review and a 2,067-box reference set (S9.1); drone labels kept `unverified`, with a seven-video human-annotated reference set (S9.2); accuracy reported per rank and per method | Drone species-rank labels include implausible taxa; triage label accuracy against the camera reference set not yet reported |
| 15 | Null written as the string `nan` | Drone | 41,524 / 318,203 Occ. (13.1%); 5 Events + 2 deployments | Date redundantly encoded in the `eventID`; time from the video containers cross-checked against the field log (Redundant encoding in data; External record) | Date restored from the identifier and flagged as derived (release build 2026-10-22); time of day recovered on 2026-11-10 from the video container creation times, with each aircraft's clock convention settled against reference flights and the field log and JotForm check-ins of the day (`provenance/drone_time_recovery_20250811.json`) | DJI clock convention is inferred from the field schedule, not verified on a reference flight; treat those times as minute-level |
| 16 | Impossible drone coordinates (`nan`, longitude ≈500) | Drone | 7 Events | Domain check on coordinate pairs (Cross-check) | Valid static video location if inside study area, else blank | Those Events lack a flight-level position |
| 17 | Curated records bypassed timestamp correction | Cam | 439 / 946 curated Occ. | Occurrence date outside parent deployment interval (Cross-check) | Re-timed from the corrected camera timestamp map (release build 2026-10-22) | --- |
| 18 | Root Event row absent from Event table | All | 1 dangling `parentEventID` | Referential check over the Event table (Cross-check) | Study root Event added; parent links validated | --- |
| 19 | Within-card clock drift | Cam | Up to 130,290 images | *none* (None (recorded once)) | Constant clock rate assumed | Unquantifiable timestamp error |
| 20 | True deployment / retrieval times | Cam | Deployment metadata known to contain errors | *none beyond the erroneous records* (None (recorded once)) | Corrected occurrence dates used instead | True camera-days not reportable |
| 21 | Manual starling supplement appended twice | Drone | 24 rows / 12 distinct `occurrenceID`s in the drone and merged Occurrence tables (2026-11-01) | Duplicate `occurrenceID` check (Cross-check) | Repaired in the release build: the 12 exact duplicate rows are dropped, leaving every `occurrenceID` unique (318,215 drone Occurrences) | --- |
| 22 | Merged snapshot and camera release disagree on camera labels | Cam | 224,149 first-generation vs 72,769 post-triage Occ.; 13 vs 19,762 camera Events | Row-count parity between the camera release tables and the merged table (Cross-check) | Resolved 2026-11-08: merged tables and camera detection-layer arrival traces regenerated from the post-triage camera tables (72,775 camera Occ., 19,785 camera Events; 401,602 merged Occ., 22,242 merged Events). See `CAMERA_TRAP_RELEASE.md` | --- |
