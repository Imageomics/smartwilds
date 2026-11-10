# SmartWilds — supplemental material

> **Camera-trap update (2026-11-08).** The legacy camera counts,
> Event hierarchy, first-generation Tree-of-Life method statements, and
> camera detection-arrival rows in this historical supplement do not describe
> the current camera release. The canonical camera release has 72,775
> original-SAM3-geometry Occurrences, 19,785 camera Events, a 235,778-image
> inventory, and 70,466 Campaign-2 operational-inference arrivals. Its
> combined multimodal table has 401,602 Occurrences and 22,242 Events. See
> [`CAMERA_TRAP_RELEASE.md`](CAMERA_TRAP_RELEASE.md) for the
> release-facing scope and provenance. The historical sections remain for
> auditability and must not be used as current camera-release statistics.

Supplemental material for the SmartWilds
datasets.
This contains the full data inventories details, the timestamp-repair methods,
the standards crosswalk, the field dictionary, the arrival statistics, and the
complete defect inventory.

Last updated: 2026-11-10.
Release: SmartWilds release build 2026-10-22, camera tables updated 2026-11-08.
It supersedes the 2026-07-24 integration pass. Paths such as
`processing_output/...` are relative to the project archive; the released files
are in the per-modality datasets of the [SmartWilds collection](https://huggingface.co/collections/imageomics/smartwilds).

---

## S1. Extended glossary


| Term | Source | Meaning in this release | What it is *not* |
|:--|:--|:--|:--|
| Event | Darwin Core | A sampling act with a date, location, protocol, and `parentEventID`. Five levels in use: `Project`, `SensorDeployment`, `AudioRecording`, `MediaEvent`, `ObservationSession`. | Not an arrival in a stream. One Event can contain 10⁵ arrivals. |
| Occurrence | Darwin Core | One organism record at a place and time, linked by `eventID`. Usually one detection crop. | Not an individual animal. Adjacent drone frames yield many Occurrences of the same animal. |
| `eventType` | Darwin Core | The level of the hierarchy a row occupies. | Not the modality; modality is carried by `parentEventID` and `modality_type`. |
| `basisOfRecord` | Darwin Core | `MachineObservation` for every detector-derived row; `HumanObservation` for citizen-science and text records and for the 12 human-added drone starling boxes. | Not a quality statement. See `identificationVerificationStatus`. |
| `identificationVerificationStatus` | Darwin Core | Vocabulary differs by table. Post-triage camera traps: `human-reviewed`, `machine-resolved`. Drones and bioacoustics: `unverified`, `validated`, plus `human-supported; limited-resolution` for the drone starling supplement. Citizen science and text: `verified by expert`. Counts in S9.3. | Not a confidence score. `machine-resolved` and `unverified` are both machine labels; a `validated` or `human-reviewed` record was reviewed by a person. |
| `dataGeneralizations` | Darwin Core | States whether a coordinate is an observed position, a sensor position, a projected estimate, or a platform-telemetry fallback. | Not a precision estimate; see `coordinateUncertaintyInMeters`. |
| `informationWithheld` | Darwin Core | Records where locality precision was reduced for sensitive taxa. | — |
| Sampling effort | Humboldt ext. | Acquisition quantity actually expended, per modality: camera observation-days, recorder-hours, flight-minutes, visitor sessions. | Not comparable across modalities. Not a detection count. |
| Arrival | systems | One item entering a processing stream. Two layers measured: *acquisition* (image capture, WAV file) and *detection* (an Occurrence). | Not a Darwin Core Event. |
| Deployment | systems | One physical installation of one device at one site over one interval. | Not a device. One device yields several deployments across campaigns. |
| Duty cycle | systems | Fraction of wall-clock time a device was *scheduled* to acquire. | Not uptime. A device can be on-schedule and dead. |
| Detection | systems | A model output: a SAM3 box, a BirdNET hit. | Not an identification. |
| Identification | Darwin Core | A taxonomic assignment with a stated verification status. | Not implied by a detection. |
| `locationID` | Darwin Core | Stable identifier for a **fixed** sensor position or a drone session origin. Null for locality-only records. | Not a comparable spatial sampling unit across modalities. |
| Coverage | systems | Distinct (date, hour) pairs containing ≥1 Occurrence, per modality. | Not area surveyed. Not detection probability. |
| Campaign | this release | One field deployment interval. Three: C1 Jun 30–Jul 3, C2 Aug 4–28, C3 Sep 8. | Not a Darwin Core term. |

---

## S2. Camera-trap deployment inventory

Four camera models, HFOV 55–120°. Configuration varied in capture mode,
resolution, burst length, PIR sensitivity, and inter-trigger delay. Every one of
these is a workload multiplier (S2.3).

### S2.1 Campaign 1 — Jun 30 to Jul 3, 2025

| Deployment | Site | Model | HFOV | Facing | Mode | Photo | Video | PIR | Images | Notes |
|:--|:--|:--|--:|:--|:--|:--|:--|:--|--:|:--|
| TW01-CT02 | Nomad Ridge E | GardePro T5NG | 56.5° | SE (135°) | Hybrid | 4 MP, 3-burst | 1080p 10 s MP4+audio | High | 7,811 | Hourly timelapse, info strip on |
| TW02-CT03 | Nomad Ridge W | GardePro A3 | 63° | SW (225°) | Photo+Video | 8 MP, 3-series | 1080p 10 s AVI+audio | High | 39 | Early battery death; 55 files total on card |
| TW03-CT01 | Pasture D Feeder | GardePro T5NG | 56.5° | S (180°) | — | — | — | — | 6,661 | Near salt lick; config not documented |
| TW04-CT04 | Lake Trail | Trail Camera G600 | 120° | NW (315°) | Photo+Video | 8 MP, 5-burst | 1080p 10 s MP4+audio | High | 570 | Images inverted (mount orientation) |

### S2.2 Campaign 2 — Aug 4 to Aug 28, 2025

| Deployment | Site | Model | HFOV | Facing | Mode | Photo | Video | Images | Notes |
|:--|:--|:--|--:|:--|:--|:--|:--|--:|:--|
| TW01-CT02 | Nomad Ridge E | GardePro T5NG | 56.5° | SE (135°) | Photo only | 4 MP, 3-burst | — | 26,573 | Removed Aug 11, relocated to dock |
| TW02-CT01 | Nomad Ridge W | GardePro T5NG | 56.5° | SW (225°) | Photo only | 4 MP, 3-burst | — | 61,217 | Clock error; battery died Aug 18–25; 4 card clock states |
| TW04-CT03 | Lake Trail | GardePro A3 | 63° | NW (315°) | Photo+Video | 8 MP, 3-burst | 1080p 10 s | 984 | Reset Aug 7; no data after Aug 25 |
| TW06-CT04 | Zebra Shelter | Trail Camera G600 | 120° | NW (315°) | Photo+Video | 8 MP, 5-burst | 1080p 10 s | 40,907 | Battery reported 100% at retrieval (unusual) |
| TW06-CT05 | Zebra Shelter (in) | Reveal Pro 3.0 | 55° | N (0°) | Photo+Video | 4K | 720p 10 s | 84 | Late deploy Aug 25–28 |
| TW07-CT05 | Zipline Tower | Reveal Pro 3.0 | 55° | N (0°) | Photo+Video | 4K | 720p 10 s | **withdrawn** | People-only media were not uploaded; metadata only retained; deletion status unknown |
| TW09-CT02 | Dock (left) | GardePro T5NG | 56.5° | S (180°) | Photo only | 4 MP, 3-burst | — | 90,834 | Largest deployment (38.5% of all images); relocated Aug 18; battery gap Aug 18–25 |
| TW09-CT05 | Dock (right) | Reveal Pro 3.0 | 55° | SE (135°) | Photo+Video | 4K | 720p 10 s | 9 | Detection issues |
| TW11-CT06 | Fence / lake | Reveal Pro 3.0 | 55° | NE (45°) | Photo+Video | 4K | 1080p 15 s | 89 | PIR level 9, 20 s delay, 1 bar cell service |

**Totals:** 235,778 JPG + 5,113 video clips, 260 GB. 13 deployments, 12 retained.

### S2.3 Configuration as workload multiplier

| Parameter | Range in deployment | Workload effect |
|:--|:--|:--|
| Burst length | 3 or 5 frames/trigger | Direct 3× or 5× multiplier on raw images per ecological event |
| Capture mode | photo-only / photo+video / hybrid | Video adds a 10–15 s clip per trigger: large storage, frame-extraction compute |
| Resolution | 4 MP / 8 MP / 4K | Bytes and per-image inference time |
| PIR sensitivity | High, Level 9, motion-detect | Higher sensitivity → more triggers and more blanks |
| Inter-trigger delay | 0 / 10 / 20 s | Longer delay suppresses repeat triggers, lowering effective arrival rate |
| HFOV | 55°–120° | Wide-angle covers more area at lower pixel density per animal |
| Cellular uplink | Reveal Pro 3.0 only | The only device in the deployment that could participate in near-real-time coordination |
| Timelapse | TW01-CT02 C1 only | Adds a scheduled arrival stream independent of PIR |

---

## S3. Acoustic recorder inventory

All units: Wildlife Acoustics Song Meter Micro 2, 48 kHz.
10 deployments across 6 sites. Duty cycle, not deployment duration, determines
volume: uncompressed 48 kHz stereo WAV ≈ 33 MB/minute.

| Deployment | Site | GPS | Schedule | Duty cycle | Raw WAV | Events | GB |
|:--|:--|:--|:--|--:|--:|--:|--:|
| **C1** | | | | | | | |
| TW05-SM01 | Lake Trail Gate O | 39.83537, −81.73842 | 5-min clips hourly (**config error** — intended 1 hr sunrise + sunset) | 8.3% | 144 | 144 | — |
| TW06-SM03 | Zebra Shelter | 39.83518, −81.73087 | 5 min/hr, 24/7 | 8.3% | 77 | 77 | — |
| TW07-SM02 | Zipline Tower | 39.83288, −81.73455 | 1 hr sunrise + 1 hr sunset | ~8% | 12 | 12 | — |
| TW08-SM04 | Fence w/ vegetation | 39.82900, −81.74378 | 5 min/hr, 24/7 | 8.3% | 78 | 78 | — |
| | | | | | **311** | **311** | **6.0** |
| **C2** | | | | | | | |
| TW02-SM04 | Nomad Ridge Shelter | 39.82957, −81.73295 | 5 min/hr | 8.3% | 659 | 581 | 26.1 |
| TW05-SM06 | Lake Trail Gate O | 39.82866, −81.73758 | sunrise–sunset | ~50–60% | 100 | 96 | 16.6 |
| TW06-SM05 | Zebra Shelter | 39.82870, −81.73756 | 15 min/hr | 25% | 508 | 508 | 21.8 |
| TW07-SM02 | Zipline Tower | 39.82891, −81.74392 | sunrise–sunset | ~50–60% | 339 | 339 | 56.4 |
| TW08-SM03 | Fence w/ vegetation | 39.82892, −81.74392 | sunrise–sunset | ~50–60% | 341 | 341 | 56.7 |
| TW09-SM01 | Dock | 39.83418, −81.73783 | sunrise–sunset (deployed Aug 14) | ~50–60% | 195 | 195 | 32.4 |
| | | | | | **2,142** | **2,060** | **210** |
| **Total** | | | | | **2,453** | **2,371** | **216** |

**Raw-WAV reconciliation.** Of the 2,453 WAV paths on disk, 2,371 are
`AudioRecording` Events: 2,307 with BirdNET detections and 64 on which BirdNET
ran but detected nothing (Events with no Occurrences). The other 82 are not
recordings of their own: 78 are Campaign-1 files copied into the Campaign-2
TW02-SM04 directory during transfer, and 4 TW05-SM06 files produced no BirdNET
result (three 3.9–22.0 s fragments and one unreadable file). Every path is
classified in `data/recordings.csv` of the bioacoustics dataset.

Note that TW02-SM04 produced **more than twice the files** of TW07-SM02 but
**less than half the bytes** — the clearest illustration that duty cycle and
file count are independent axes.

---

## S4. Drone platform and session inventory

| Platform | Campaigns | Video | Telemetry format | Sessions |
|:--|:--|:--|:--|--:|
| Parrot Anafi 4K | C1 (Jul 1, 3), C2 (Aug 11, 18, 25) | 4K MP4 | Parrot JSON / GUTMA DX | 10 (+3 telemetry-only) |
| DJI (unspecified) | C2 (Aug 11) | 1080p MOV | CSV, GPS + battery, 10 Hz | 1 |
| DJI Air 2 | C3 (Sep 8) | 4K MP4 | Airdata CSV | 4 |

**39** raw videos and **39** `MediaEvent` rows; one MediaEvent (`VID_001`)
has zero Occurrences because it was intentionally excluded after review.
**15** video-bearing `SensorDeployment` flight-session Events. Three more
Aug 25 Parrot directories hold telemetry but no video and are not sampling
Events. 90 GB total.

Three platforms produced three telemetry schemas with different field names,
units (feet vs. metres for altitude), and gimbal-angle conventions. Fields
consumed by the projection script, with their per-platform sources:

- platform GPS — `latitude_y` / `longitude_y`
- AGL height — `height_sonar(feet)` when available, else `altitude (m)` / `altitude_m`
- heading — `gimbal_heading(degrees)` or `compass_heading(degrees)`
- pitch — `gimbal_pitch(degrees)`, with a configurable fallback when near-level
- FOV — approximate per-platform constant

---

## S5. Camera-trap timestamp repair, in full

235,778 images; 0 unmapped; 0 flagged for review. 18 correction methods.

### S5.1 Raw timestamp source

| Source | Images | Share |
|:--|--:|--:|
| Filename | 193,096 | 81.9% |
| EXIF | 42,500 | 18.0% |
| OCR of burned-in bottom overlay | 179 | 0.08% |
| Manual read of bottom overlay | 3 | 0.001% |

### S5.2 Final confidence

| Confidence | Images | Share | Meaning |
|:--|--:|--:|:--|
| high | 105,488 | 44.7% | Verified correct, or anchored to a logged service event |
| medium | 130,290 | 55.3% | Anchored interpolation assuming a constant clock rate — **untestable without a second anchor** |

### S5.3 All 18 correction methods

| Method | Images | Pattern |
|:--|--:|:--|
| `aug_tw09_ct02_sd23_correct_after_move` | 59,568 | verified correct |
| `aug_tw09_ct02_sd22_start_anchor` | 31,266 | per-card anchor |
| `aug_tw06_ct04_sd02_start_anchor` | 27,734 | per-card anchor |
| `aug_tw01_2025_clock_offset` | 26,558 | constant offset |
| `aug_tw02_actual_august_clock` | 17,301 | verified correct |
| `aug_tw02_sd01_sep_clock_anchor` | 17,262 | per-card anchor |
| `aug_tw02_sd01_2023_clock_anchor` | 13,689 | constant offset (**clock reporting 2023**) |
| `aug_tw06_ct04_initial_start_anchor` | 13,173 | per-card anchor |
| `aug_tw02_sd11_sep_clock_anchor` | 12,965 | per-card anchor |
| `june_tw01_correct` | 7,811 | verified correct |
| `june_tw03_correct` | 6,661 | verified correct |
| `aug_tw04_sd02_start_anchor` | 696 | per-card anchor |
| `june_tw04_start_anchor_inverted_images` | 570 | per-card anchor + inverted mount |
| `aug_tw04_sd03_start_anchor` | 288 | per-card anchor |
| `bottom_overlay_ocr` | 179 | OCR of in-frame timestamp |
| `june_tw02_start_anchor` | 39 | per-card anchor |
| `aug_tw01_2023_tail_clock_offset` | 15 | constant offset (**2023 tail**) |
| `manual_bottom_overlay_read` | 3 | human read |

Only **14,472 images (6.1%)** were accepted as recorded
(`june_tw01_correct` + `june_tw03_correct`). The remaining
**221,306 (93.9%)** required reconstruction.

### S5.4 Per-deployment repair summary

| Dataset | Deployment | Location | Images | First corrected | Last corrected | Methods |
|:--|:--|:--|--:|:--|:--|--:|
| C1 | TW01-CT02 | Nomad Ridge E | 7,811 | 2025-06-30 12:18 | 2025-07-02 06:50 | 1 |
| C1 | TW02-CT03 | Nomad Ridge W | 39 | 2025-06-30 12:34 | 2025-07-01 00:34 | 1 |
| C1 | TW03-CT01 | Pasture D Feeder | 6,661 | 2025-06-30 13:06 | 2025-07-02 01:04 | 1 |
| C1 | TW04-CT04 | Lake Trail | 570 | 2025-06-30 13:25 | 2025-07-03 16:56 | 1 |
| C2 | TW01-CT02 | Nomad Ridge E | 26,573 | 2025-08-04 09:01 | 2025-08-10 10:15 | 2 |
| C2 | TW02-CT01 | Nomad Ridge W | 61,217 | 2025-08-04 09:05 | 2025-08-18 09:07 | **4** |
| C2 | TW04-CT03 | Lake Trail | 984 | 2025-08-07 10:38 | 2025-08-25 10:49 | 2 |
| C2 | TW06-CT04 | Zebra Shelter | 40,907 | 2025-08-04 09:52 | 2025-08-26 15:35 | 2 |
| C2 | TW06-CT05 | Zebra Shelter | 84 | 2025-08-25 15:09 | 2025-08-28 08:17 | 2 |
| C2 | TW09-CT05 | Dock / Waterfront | 9 | 2025-08-11 10:18 | 2025-08-13 18:20 | 1 |
| C2 | TW09-CT02 | Dock, then Nomad Ridge W after Aug 18 | 90,834 | 2025-08-11 10:27 | 2025-08-28 09:44 | 2 |
| C2 | TW11-CT06 | Nomad Ridge W | 89 | 2025-08-18 09:00 | 2025-08-28 02:47 | 2 |

Files: `processing_output/detections/drone_camera_analysis/camera_time_mapping/`
— `camera_image_timestamp_map.csv` (per-image, 17 columns),
`camera_timestamp_summary_by_camera.csv`,
`camera_timestamp_summary_by_date.csv`,
`camera_trap_timestamp_corrections.csv`,
plus `.before_bottom_ocr` and `.before_ocr_interpolation` stages.

---

## S6. Drone ground projection

**The campaigns were flown for population estimation and behavior, not
geolocation.** Platform GPS localizes a detection to a known pasture, which is
the operative spatial reference. Per-animal projection is an optional refinement
provided for completeness; **no result in any of the three papers depends on
it.** Monocular distance estimation from a moving platform to moving subjects is
unreliable and is not established practice in aerial wildlife survey.

| Status | Detections | Share |
|:--|--:|--:|
| `ok` (projected position available) | 247,340 | 77.9% |
| `invalid_altitude` | 27,306 | 8.6% |
| `missing_drone_gps` | 24,467 | 7.7% |
| `horizon_ray` (camera near level) | 18,324 | 5.8% |
| `out_of_range` | 122 | 0.04% |

Method: convert the bbox bottom-center pixel to a camera ray, rotate by
heading/pitch, intersect with a flat ground plane, project the offset from
platform GPS. Dominant error sources: gimbal-pitch convention, terrain relief,
altitude source, video stabilisation, FOV assumption, and whether bbox
bottom-center is the animal's ground-contact point.

Camera-trap coordinates use the pinhole method from
<https://github.com/Imageomics/camera-trap-geolocation>: bbox height → range,
bbox horizontal offset → bearing, projected from the camera GPS. Assumes flat
ground and a uniform **0.9 m** target height — the dominant error term at a site
holding animals from geese to Père David's deer.

**Known analysis hazard.** An internal audit found a spatial figure that plotted
projected animal positions and platform-telemetry positions together without
distinguishing them: 15.66% of 292,106 plotted drone points were platform
coordinates. The status field was present and correct; the script did not read
it. The release carries that status on every drone Occurrence
(`drone_georef_status` in `occurrenceRemarks`, `georef_status` in
`detections.csv`); any analysis of drone coordinates must filter on it, and
`examples/quickstart.py` shows the pattern. No automated check of downstream
analyses ships with the release.

---

## S7. Standards crosswalk, in full

| Required information | Standard | Status |
|:--|:--|:--|
| Taxon, rank hierarchy, vernacular name | Darwin Core | reused directly |
| `eventDate`, `eventTime`, event hierarchy | Darwin Core | reused directly |
| `decimalLatitude`/`Longitude`, `coordinateUncertaintyInMeters`, `geodeticDatum` | Darwin Core | reused directly |
| `basisOfRecord`, `identificationVerificationStatus` | Darwin Core | reused as the automation boundary |
| `dataGeneralizations`, `informationWithheld` | Darwin Core | reused for coordinate semantics and sensitive taxa |
| `samplingProtocol`, `samplingEffort`, `sampleSizeValue`/`Unit` | Darwin Core + Humboldt | reused; effort reported per modality, never summed |
| Inventory completeness, sampling scope | Humboldt | partially used |
| Device model, sensor specification | SensorML concepts | re-expressed in platform tables (not SensorML-encoded) |
| Derivation chain (raw → detection → identification) | PROV-DM concepts | re-expressed in remarks fields (not PROV-encoded) |
| Platform, mission, annotation documentation | FAIR² Drones | dataset card template adopted |
| Release principles | FAIR, CARE, TRUST | followed |
| **Duty cycle and acquisition schedule** | — | **systems extension** (deployment `samplingProtocol` + config tables) |
| **Trigger semantics** (PIR sensitivity, burst length, delay) | — | **systems extension** (config tables, S2.3) |
| **Timestamp confidence and repair method** | — | **systems extension** (timestamp map, S5) |
| **Per-detection coordinate provenance status** | — | **systems extension** (`drone_georef_status`, S6) |
| **Typed missingness** | — | **systems extension** (S8) |
| **Model identity, version, parameters, per-rank accuracy** | — | **systems extension** (S9) |
| **Validator coverage and known gaps** | — | **systems extension** (S11) |

The last six rows are the ones no standard we found expresses in a
machine-readable way. We name them and use them consistently; we do not claim to
have standardized them.

---

## S8. Missing data, broken down by type.



| # | State | How it is computable | Example |
|--:|:--|:--|:--|
| 1 | Sensor active, nothing observed | Hourly bin inside a deployment window with no Occurrence | Most nocturnal camera bins |
| 2 | Sensor inactive by schedule | Deployment-level schedule field | 5 min/hr recorders are off 91.7% of the time by design |
| 3 | Sensor inactive by failure | Capture gap vs. logged deployment window, with cause | TW02-CT01 battery, Aug 18–25 |
| 4 | Captured but not represented | Raw file inventory vs. Event table | 78 transfer-duplicate WAVs and 4 failed WAVs, each classified per path (S3) |
| 5 | Metadata unusable for a purpose | Status/provenance column | 41,524 drone Occurrences with a date but no time of day (S10); 70,219 detections unprojectable (S6) |
| 6 | Excluded in QC | Documented exclusion | People-only TW07-CT05 deployment excluded; one drone video reviewed and kept as a zero-Occurrence `MediaEvent` |

States 1 and 2 have opposite implications for a coordination policy, which is
why the schedule field is load-bearing and not documentation.

---

## S9. Models, parameters, and measured accuracy

Manual annotation does not scale to sensor-network volume: human-reviewed
labels are under 1% of the release and consumed the review capacity available.
Semi-automated analysis is therefore the realistic condition, and we use
current state-of-the-art models so that reported quality reflects what a
practitioner adopting today's best tooling would obtain.

Labels were produced in two generations, and the released tables carry both.
The **first generation** labeled every SAM3 box with a BioCLIP Tree-of-Life
taxon; it still describes the operational drone table and the merged
cross-modal snapshot. The **second generation** (October–November 2026)
replaced the camera-trap labels with embedding-based triage plus targeted
human review (S9.1), and added a seven-video human-annotated drone reference
set with a manual starling supplement (S9.2).

| Stage | Model | Role |
|:--|:--|:--|
| Visual segmentation | SAM 3 | bounding boxes on camera-trap images and drone frames |
| Visual classification, first generation | BioCLIP Tree-of-Life (TreeOfLife-200M) | top-1 taxon with full rank hierarchy, top-5 retained; operational drone labels |
| Label triage, second generation | Resolve–Clear–Defer prototype triage over proposal embeddings | routes proposals to human review and resolves the rest by similarity to reviewed examples; operational camera-trap labels |
| Acoustic detection | BirdNET | detections with frequency bounds and offset into the WAV |
| Water/lake masking | SAM 3 | lake/water masks for habitat-association analysis |

### S9.1 Camera-trap labels (post-triage)

Operational camera-trap Occurrences are SAM3 animal proposals labeled by
Resolve–Clear–Defer triage. The triage selects proposals for human review and
resolves the remainder by similarity to reviewed examples; `labelProvenance`
records the outcome on every row, with the triage round where recovered.

| `labelProvenance` | `identificationVerificationStatus` | Occurrences |
|:--|:--|--:|
| `triage_reviewed` | `human-reviewed` | 1,760 |
| `triage_resolved` | `machine-resolved` | 70,808 |
| `triage_forced_1nn` | `machine-resolved` | 201 |
| **Total** | | **72,769** |

Forced nearest-neighbour labels did not meet the triage confidence rules and
may be wrong; exclude them unless label noise is tolerable. Box geometry is
never edited (`geometryProvenance = SAM3`), even when the label was human
reviewed. The table keeps only reviewed or resolved animal proposals: cleared
and background proposals, boxes with a shorter side below 32 px, boxes
overlapping the per-resolution ROI mask, and frames on the privacy exclusion
manifest are excluded, so **an image without an Occurrence is not evidence
that no animal was present.** Twelve taxa occur: milu (Père David's) deer,
Przewalski's horse, Canada goose, Sichuan takin, trumpeter swan, killdeer,
European starling, barn swallow, and the broad labels bird, butterfly,
dragonfly, and insect.

A separate **human-reviewed reference set** of 2,067 boxes on 198 selected
ungulate and waterfowl images (881 Canada goose, 627 milu deer, 349
Przewalski's horse, 149 Sichuan takin, 61 trumpeter swan) is released beside,
not inside, the Occurrence table. Taxonomy and geometry were both reviewed;
1,552 boxes share a SAM3 proposal's geometry and 515 are human edits or
additions, and the set is not filtered by the 32 px or ROI rules. The images
were selected for review, so the set is not a random or exhaustive test split.
Triage label accuracy against this reference set has not yet been reported.
<!-- TODO(confirm-stats): add triage label accuracy vs. the 2,067-box reference set, or cite the Resolve–Clear–Defer paper's figures. -->

### S9.2 Drone labels: operational table and seven-video reference set

**Operational table.** The 318,203 machine drone Occurrences remain
first-generation labels: a SAM3 box on every 15th frame with a top-1 BioCLIP
Tree-of-Life taxon. The only measured accuracy for that labeler comes from
human-annotated camera-trap subsets:

| Analysis | Level | n | Precision | Recall | F1 / accuracy |
|:--|:--|--:|--:|--:|--:|
| SAM3 animal localization, camera traps | IoU ≥ 0.50 | 1,125 | 0.866 | 0.845 | 0.856 |
| Tree-of-Life taxonomic assignment | class | 951 | | | 0.845 |
| | order | 951 | | | 0.660 |
| | family | 951 | | | 0.463 |
| | genus | 951 | | | 0.322 |
| | species | 951 | | | 0.271 |

Usable statement: **class-rank labels support screening and triage; species-rank
labels require curation; anything aggregating across ranks is uninterpretable.**
A single headline accuracy anywhere in the 0.27–0.85 range would mislead.
Corroborating evidence: the taxonomy crosswalk holds **12,577 label keys**, of
which only **4** consist entirely of expert-verified records and 16 contain
accepted names with mixed verification evidence.

**Seven-video reference set.** Seven drone videos were human-annotated on
1,089 sampled frames for four focal classes, with onager observations
excluded: `20250703_parrotanafi_1`, `_2`, `_5` (C1), `20250811_DJI_01`,
`20250818_parrot_01`, `_02`, and `20250825_parrot_01` (C2). The corrected
reference holds **27,159** four-class boxes (the localization audit below was
run against 27,180 before the final manual review): Père David's deer 21,177,
Sichuan takin 3,293, Przewalski's horse 2,066, Canada goose 644. It is
delivered as COCO JSON with provenance, a frame-to-proposal mapping, and the
audit files. <!-- TODO(release): confirm the path of the seven-video reference set in the drone dataset. -->

SAM3 localization against the reference (35,312 proposals, one-to-one
matching):

| IoU | Precision | Recall | F1 |
|:--|--:|--:|--:|
| 0.25 | 0.758 | 0.985 | 0.856 |
| 0.50 | 0.749 | 0.973 | 0.847 |
| 0.75 | 0.740 | 0.961 | 0.836 |

Per-class recall at IoU 0.25: Przewalski's horse 0.961, Père David's deer
0.985, Sichuan takin 0.993, Canada goose 1.000. Per-video recall at IoU 0.25
ranges from 0.958 (`20250818_parrot_02`) to 0.999 (`20250825_parrot_01`).

Resolve–Clear–Defer prototype triage was then run over the full proposal pool
(seed 3, density-moderated k-center acquisition, calibrated rule k = 5,
τ_fg = 4, τ_bg = 4). It spent 100 proposals on calibration and 1,610 on
expert review (4.6% of the 35,212-proposal evaluation pool), handled the
remaining 33,602 automatically, and got 28,040 of those right: 79.6% of the
evaluation pool, or 83.5% of the automatic decisions. Zero proposals were left
deferred.

Four-species classification on the 25,897 matched, unreviewed foreground
instances (78.4% Père David's deer, so always-deer scores 0.784 accuracy):

| Method | Precision | Recall | F1 | Accuracy | Macro-F1 |
|:--|--:|--:|--:|--:|--:|
| Prototype triage, automatic decisions only | 0.913 | 0.850 | 0.880 | 0.850 | 0.789 |
| BioCLIP 2 zero-shot, four prompts | 0.167 | 0.167 | 0.167 | 0.167 | 0.230 |
| Tree-of-Life, open-world, exact focal-taxon match | 0.947 | 0.037 | 0.071 | 0.037 | 0.188 |

Species-wise recall for triage: Père David's deer 0.918, Przewalski's horse
0.687, Canada goose 0.590, Sichuan takin 0.551. The dominant automatic errors
are wrong-species resolves into Père David's deer (takin 1,287, horse 595,
goose 100) and 1,584 deer cleared as background. Read the table carefully:
Tree-of-Life is evaluated open-world, so its 0.037 recall is exact top-1
recognition of a focal taxon under an unconstrained vocabulary, not animal
recognition accuracy; BioCLIP 2 zero-shot always answers one of four prompts
and has no background option; triage abstentions count as no prediction. All
figures are proposal-level repeated observations from seven videos, not
independent animals.

**Manual European starling supplement.** Twelve human-added *Sturnus vulgaris*
boxes on one frame (`20250703_parrotanafi_2` / `VID_002`, frame 1320) were
appended to the drone Occurrence table on 2026-11-01 with
`basisOfRecord = HumanObservation`,
`identificationVerificationStatus = human-supported; limited-resolution`, and
remarks stating that no SAM3 proposal, embedding, or triage decision was
involved.
The identification rests on limited pixels in a single frame and should be
interpreted cautiously. These records are excluded from the 27,159-box
reference, the localization audit, the triage calibration and evaluation, and
the species-classification comparison; none of the numbers above change if
they are dropped. The 12 rows were appended twice (24 rows, 12 distinct
`occurrenceID`s) in both the drone and merged tables (defect 21, repaired in the release build).

### S9.3 Verification status distribution

Counts are per table, because the vocabularies differ. The merged table below
is the pre-update state (2026-11-01), before the camera rows were regenerated
from the post-triage tables (defect 22, resolved 2026-11-08).

Merged `occurrences_all_modalities.csv` as of 2026-11-01:

| Modality | Status | Records |
|:--|:--|--:|
| Camera traps (first generation) | `unverified` | 223,203 |
| | `validated` | 946 |
| Bioacoustics | `unverified` | 9,960 |
| Drones | `unverified` | 317,559 |
| | `validated` | 644 |
| | `human-supported; limited-resolution` | 24 (12 distinct records; defect 21) |
| Citizen science | `verified by expert` | 622 |
| Text data | `verified by expert` | 30 |
| **Total** | | **552,988** |

Post-triage camera-trap Occurrence table (the released camera dataset):

| Status | Records | Share |
|:--|--:|--:|
| `machine-resolved` | 71,009 | 97.6% |
| `human-reviewed` | 1,760 | 2.4% |

`validated` = 946 camera-trap + 644 drone bird records from the curated
goose/swan review set (added 2026-09-20). The 946 camera records belong to the
first-generation camera table and are not carried into the post-triage
Occurrence table; the 2,067-box reference set takes their role.
`verified by expert` = all 622 citizen-science + 30 text-data records.

A verification floor is one predicate: treat `unverified` and
`machine-resolved` as machine labels; `human-reviewed`, `validated`, and
`verified by expert` as person-reviewed; and `human-supported;
limited-resolution` as person-reviewed but low confidence.

### S9.4 Why this must be published

1. A taxon string is not reproducible without the model that produced it. Two
   versions of the same classifier yield different taxa from the same image.
2. Published uncertainty is what makes labels **re-derivable**. Machine labels
   are a snapshot of a model, not ground truth. A release that keeps source
   media, detection geometry, model identity, and per-rank accuracy can be
   re-labeled when better models arrive and the label sets compared
   meaningfully. One shipping only final taxon strings cannot.
3. Aggregate accuracy hides the rank-dependent failure mode above.
4. Verification status must be per record, not per dataset — a README caveat
   cannot be filtered on.

---

## S10. Sentinel values: `nan` as a date string (repaired)

In snapshot `darwin_core_latest_20260724`, the 2025-08-11 drone session carried
`eventDate` = the literal string `nan` (a dataframe export of a missing value)
and an empty `eventTime`. The QC summary reported `missing_eventDate=0` because
the check tested for null/empty and `"nan"` is neither.

| eventID | Occurrences |
|:--|--:|
| `TheWilds_2025_drone_20250811_DJI_01_DJI_0002` | 12,522 |
| `TheWilds_2025_drone_20250811_parrot_01_P5190525` | 12,430 |
| `TheWilds_2025_drone_20250811_parrot_01_P5190526` | 11,996 |
| `TheWilds_2025_drone_20250811_DJI_01_DJI_0001` | 4,535 |
| `TheWilds_2025_drone_20250811_parrot_01_P5180524` | 41 |
| `TheWilds_2025_drone_20250811_DJI_01`, `..._parrot_01` (`SensorDeployment`) | — |
| **Total** | **41,524** (13.1% of drone Occurrences) |

**Repair (release build 2026-10-22).** `eventDate` was restored to
`2025-08-11` from the flight identifier and marked as identifier-derived.
`eventTime` is left blank: neither the DJI telemetry nor the video containers
retain a trustworthy capture time, and no time was synthesized from file
modification times. These records can be placed on a day but not within it,
and they are excluded from inter-arrival and diurnal analyses. Drones flew on
6 dates; the old count of 7 included the string `nan`.

The same audit found impossible coordinates (`nan`, longitude ≈ 500) on seven
drone Events, now replaced with a validated static video location or left
blank, and a missing study-root Event `TheWilds_2025`, now added.

---

## S11. Validation: checks run, and gaps

### S11.1 Original checks (snapshot `20260724`)

- no missing event links (`eventID` resolves)
- no missing taxon
- no missing `eventDate` (presence only; this is how the `nan` dates passed)
- no duplicate `occurrenceID`

### S11.2 Current release checks

The generator now parses every date, time, and coordinate pair and rejects
sentinel values (`nan`, `None`, `NULL`, `-1`, `1970-01-01`) before export. The
release audit checks, over every modality and merged table:

- source-to-merged parity for Events and Occurrences;
- a single-rooted Event hierarchy with no dangling `parentEventID`;
- Occurrence-to-Event links and ancestry;
- parsed dates and times, and WGS84-bounded coordinates;
- every Occurrence date inside its parent Event's span and the study window;
- no absolute cluster paths, and every `associatedMedia` resolving to a
  released file in the dataset's media manifest;
- agreement between the generator and the released tables.

### S11.3 Gaps that remain

| Gap | Consequence |
|:--|:--|
| No check that analyses constrain `drone_georef_status` | Mixed-semantics spatial figures are possible (S6) |
| No semantic content check | People in imagery are found by a person detector plus human review, not by the validators |

**A passing validator is evidence about the validator.** The original checks
certified 552,964 records clean while 13.1% of one modality had no usable
timestamp. Validator coverage should be reported, not assumed.

---

## S12. Darwin Core field dictionary

`occurrences_all_modalities.csv` — 44 columns:

`modality_type`, `occurrenceID`, `eventID`, `catalogNumber`, `scientificName`,
`kingdom`, `phylum`, `class`, `order`, `family`, `genus`, `specificEpithet`,
`taxonRank`, `vernacularName`, `occurrenceStatus`, `individualCount`,
`lifeStage`, `sex`, `behavior`, `basisOfRecord`, `recordedBy`, `identifiedBy`,
`identificationVerificationStatus`, `identificationRemarks`, `eventDate`,
`eventTime`, `decimalLatitude`, `decimalLongitude`,
`coordinateUncertaintyInMeters`, `geodeticDatum`, `locality`, `locationID`,
`country`, `stateProvince`, `county`, `establishmentMeans`,
`degreeOfEstablishment`, `occurrenceRemarks`, `associatedMedia`,
`associatedReferences`, `datasetID`, `datasetName`, `informationWithheld`,
`dataGeneralizations`

`events_all_modalities.csv` — 21 columns:

`eventID`, `parentEventID`, `eventType`, `eventDate`, `samplingProtocol`,
`sampleSizeValue`, `sampleSizeUnit`, `locality`, `locationID`,
`decimalLatitude`, `decimalLongitude`, `coordinateUncertaintyInMeters`,
`geodeticDatum`, `country`, `stateProvince`, `county`, `datasetID`,
`datasetName`, `recordedBy`, `fieldNotes`, `eventTime`

### S12.1 Event hierarchy composition

| `eventType` | Rows | Granularity |
|:--|--:|:--|
| `Project` | 6 | study root `TheWilds_2025` + one per modality |
| `SensorDeployment` | 37 | 12 camera + 10 ARU + 15 drone flight session |
| `AudioRecording` | 2,371 | one per processed WAV file (64 with no detections) |
| `MediaEvent` | 39 | one per raw drone video (1 reviewed, no Occurrences) |
| `ObservationSession` | 17 | 13 citizen science + 4 text data |
| **Total** | **2,470** | |

### S12.2 Occurrence composition

| Modality | Events | Occurrences | Dates | Hourly bins | `locationID`s |
|:--|--:|--:|--:|--:|--:|
| Study root | 1 | — | | | |
| Camera traps | 13 | 224,149 | 29 | 624 | 7 |
| Bioacoustics | 2,382 | 9,960 | 29 | 650 | 6 |
| Drones | 55 | 318,203 | 6 | 8* | 15 |
| Citizen science | 14 | 622 | 13 | 28 | 0 |
| Text data | 5 | 30 | 4 | 4 | 6 |
| **Total** | **2,470** | **552,964** | | | |

\* the 2025-08-11 session has a date but no time of day, so it contributes no
hourly bin (S10). Camera dates and bins use the corrected timestamps of the
release build (439 curated records re-timed).

Camera-trap figures here are the first-generation table in the merged
snapshot. The released post-triage camera dataset has 19,762 Events (1
`Project`, 12 `SensorDeployment`, 19,749 `Image`) and 72,769 Occurrences, and
the drone table gained 12 manual starling records on 2026-11-01 (S9, defects
21–22).

---

## S13. Arrival characterization, both layers

Window: Campaign 2, 2025-08-04 to 2025-08-28, 600 hours — the only interval in
which all four modalities were simultaneously active.

Definitions. *Acquisition arrival* = one image capture (from
`camera_image_timestamp_map.csv`, corrected timestamps) or one WAV recording
(from `AudioRecording` Event times). *Detection arrival* = one Occurrence with
a resolvable date and time. `B = (σ−μ)/(σ+μ) = (CV−1)/(CV+1)` over
inter-arrival times: −1 periodic, 0 Poisson, →1 maximally bursty.

| Stream | Arrivals | Rate/hr | CV | B | Dates |
|:--|--:|--:|--:|--:|--:|
| **Acquisition** | | | | | |
| Camera image captures | 220,697 | 367.83 | 2.06 | +0.347 | 25 |
| Acoustic WAV recordings | 2,060 | 3.43 | 1.23 | +0.103 | 25 |
| **Detection** | | | | | |
| Camera traps | 208,054 | 346.76 | 7.26 | +0.758 | 25 |
| Bioacoustics | 8,865 | 14.78 | 3.21 | +0.525 | 25 |
| Drones | 53,238 | 88.73 | 229.61 | +0.991 | 2 |
| Citizen science | 242 | 0.40 | 5.30 | +0.682 | 10 |

Detection streams count machine-derived Occurrences only; curated review
records are excluded. Acoustic recordings include the 64 zero-detection WAVs.
Excluded from timed statistics: 41,524 drone Occurrences (date but no time,
S10). Every stream is released as a versioned trace (`analysis/arrival_traces_v2/`
in the study-level dataset) with a source-record ID per arrival, inclusion rules,
and input checksums; earlier unversioned arrival summaries are deprecated.
Acquisition arrivals are not reconstructible for drones (per-frame times are not
retained) or citizen science (one submission per session).

### S13.1 Diurnal profiles (mean arrivals per hour-of-day over 25 days)

| Hour | Cam capture | Cam detect | Acoustic WAV | Acoustic detect | CS detect |
|--:|--:|--:|--:|--:|--:|
| 00 | 290.1 | 76.5 | 1.8 | 3.4 | 0.0 |
| 01 | 296.3 | 86.9 | 1.8 | 3.2 | 0.0 |
| 02 | 317.4 | 184.1 | 1.8 | 3.3 | 0.0 |
| 03 | 300.3 | 128.6 | 1.8 | 4.3 | 0.0 |
| 04 | 304.0 | 211.9 | 1.8 | 3.3 | 0.0 |
| 05 | 300.6 | 133.3 | 2.8 | 21.1 | 0.7 |
| 06 | 317.9 | 519.2 | **5.2** | **41.6** | 0.0 |
| 07 | 321.8 | **674.4** | 4.3 | 20.1 | 0.0 |
| 08 | 341.3 | 503.2 | 4.3 | 18.3 | 0.0 |
| 09 | 407.2 | 597.6 | 4.6 | 18.4 | 1.7 |
| 10 | 454.4 | 416.5 | 4.3 | 18.6 | **2.7** |
| 11 | 534.4 | 495.1 | 4.3 | 16.8 | 1.4 |
| 12 | 589.0 | 507.6 | 4.3 | 16.2 | 0.2 |
| 13 | **611.8** | 496.8 | 4.3 | 16.2 | 0.4 |
| 14 | 527.6 | 301.1 | 4.3 | 15.8 | 0.0 |
| 15 | 446.0 | 285.0 | 4.3 | 14.6 | 0.0 |
| 16 | 385.3 | 193.5 | 4.3 | 16.5 | 0.0 |
| 17 | 326.1 | 536.7 | 4.3 | 16.4 | 0.0 |
| 18 | 297.8 | 499.9 | 4.3 | 17.6 | 0.0 |
| 19 | 286.4 | 393.7 | **5.2** | 36.2 | 0.0 |
| 20 | 292.8 | 494.8 | 3.0 | 18.7 | 0.0 |
| 21 | 304.8 | 392.9 | 1.8 | 7.2 | 0.0 |
| 22 | 288.4 | 138.9 | 1.8 | 3.0 | 1.6 |
| 23 | 286.1 | 53.9 | 1.8 | 3.8 | 1.0 |

Drone detections are zero in every hour but 09 (26,619 arrivals summed across
the two flight dates).

Diurnal swing, max/min: camera captures **2.1×**, camera detections **12.5×**,
acoustic acquisition **2.9×**, acoustic detections **13.9×**. Detection profiles
are sharper than the acquisition profiles feeding them in every modality where
both are measurable.

These values come from the versioned v2 arrival traces. They supersede the
earlier unversioned arrival summaries, whose event definitions were not
recorded.

---

## S13.2 Field servicing effort

Derived from the Campaign-2 Jotform logs in
`thewilds_20250804_20250828/jotforms/` (two camera-trap exports, two
bioacoustic exports). Every row is one sensor servicing action with a `DateTime`
stamp, site ID, device ID, SD-card ID, team member, and free-text note.

| Trip | Actions | Window | Elapsed | Median gap between actions | People |
|:--|--:|:--|--:|--:|--:|
| 2025-08-04 | 8 | 08:58–10:41 | 103 min | 16.0 min | 3 |
| 2025-08-07 | 6 | 08:59–10:05 | 66 min | 3.0 min | 1 |
| 2025-08-11 | 9 | 09:32–10:48 | 76 min | 3.0 min | 2 |
| **Total** | **23** | | **245 min (4.1 h)** | | |

Breakdown of the 23 actions: 11 dropoff (deployment), 6 pickup (retrieval),
5 check-in (status only, no SD or battery swap), 1 combined. By modality:
12 acoustic, 11 camera.

Additional operational fields captured per action:

- **Access difficulty**, 1–3 scale — recorded on 15 of 23 actions
  (rating 3: 9 actions; rating 1: 5; rating 2: 1)
- **Battery status** — e.g. 98%, 95%, 60%, "Low", "100%"
- **SD-card storage** — e.g. "7% full", "26% full", "5GB"
- **Camera heading** — compass octant, used by the camera-trap georeferencing
- **Relocation notes** — free text landmarks ("Zebra shelter", "Zip tower",
  "Lake trail"), which is how the TW09-CT02 mid-deployment move was recovered
- **Team member name and email**


**Scope boundary:** this is measured elapsed field time for the three retained
mid-campaign Jotform exports only. Campaign-1 field notes have no clock times,
Aug. 28 retrieval submissions are absent from the retained exports, and no
per-stage analyst-time log exists. The release therefore reports no total
campaign field effort and no measured desk-processing hours.

**Coverage limits.** These exports cover the three mid-campaign trips only.
Campaign-1 field notes
(`thewilds_20250630_20250703/field_notes/*.md`) are narrative and contain no
clock times, and the 2025-08-28 retrieval visits do not appear in the exported
forms. So 4.1 h is logged servicing time, not total field effort.

**Not recorded anywhere:** analyst time per processing stage. Field visits were
logged with timestamps; the timestamp-repair and taxonomy-review work was not.
This asymmetry is requirement R7 in the paper.

---

## S14. Reproduction

Darwin Core generation:

The scripts live in the SmartWilds code repository (`scripts/`). Set
`SMARTWILDS_ARCHIVE` to the root of the field archive before running them; see
`scripts/README.md`.

```bash
python scripts/darwin_core/generate_darwin_core.py --force
python scripts/arrival_traces/generate_arrival_traces_v2.py
```

Camera-trap georeferencing:

```bash
python scripts/georeferencing/geolocate_camera_trap_treeoflife_predictions.py \
  --input-dir  <archive>/processing_output/detections/camera_traps/methods_paper/annotations/sam3/treeoflife_sam3/predictions \
  --config-csv scripts/georeferencing/camera_geolocation_config.csv \
  --output-dir <archive>/processing_output/detections/camera_traps/methods_paper/annotations/sam3/treeoflife_sam3/geolocation/geolocated_predictions \
  --overwrite
```

Drone georeferencing:

```bash
python scripts/georeferencing/geolocate_drone_treeoflife_predictions.py \
  --prediction-dir <SAM3 per-video prediction CSVs> \
  --detection-dir  <archive>/processing_output/detections/drones \
  --config-csv     scripts/georeferencing/drone_projection_config.csv \
  --output-dir     <archive>/processing_output/detections/drones/geolocation/geolocated_predictions \
  --overwrite
```

### S14.1 Release discipline

Integration passes are dated and immutable. Every mutation retains a
before-copy and emits a JSON audit record. Passes differ **semantically**,
not just additively — different visual-label semantics, corrected timestamps —
so comparing numbers across passes is invalid in a way that is not visible in
the numbers. **Any figure or table must name the release build it was computed
from.**

The 2026-10-22 release build supersedes the 2026-07-24 pass; each of its
repairs (S10, S3, S4, S16) has its own JSON audit record, shipped under
`metadata/provenance/`. The 2026-09-20 curated-bird update is reconstructible
from:

- `curated_bird_dwc_update_audit_20260920_015706.json`
- `curated_bird_event_sync_audit_20260920_020046.json`
- `curated_bird_project_sample_size_fix_20260920_020401.json`

---

## S15. Release logistics

Each modality is published as its own Hugging Face dataset with its own DOI,
and a study-level dataset holds the merged Event table, the text records, the
arrival traces, and this supplement. The [SmartWilds collection](https://huggingface.co/collections/imageomics/smartwilds) joins all five.
DOIs, the license, and the maintenance commitment will be listed here at
publication. Contact: Jenna M. Kline (kline.377@osu.edu).

## S16. Defect inventory, in full

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
| 15 | Null written as the string `nan` | Drone | 41,524 / 318,203 Occ. (13.1%); 5 Events + 2 deployments | Date redundantly encoded in the `eventID` (Redundant encoding in data) | Date restored from the identifier and flagged as derived; time left blank | 2025-08-11 session absent from intra-day analysis (paper §sentinel values; S10) |
| 16 | Impossible drone coordinates (`nan`, longitude ≈500) | Drone | 7 Events | Domain check on coordinate pairs (Cross-check) | Valid static video location if inside study area, else blank | Those Events lack a flight-level position |
| 17 | Curated records bypassed timestamp correction | Cam | 439 / 946 curated Occ. | Occurrence date outside parent deployment interval (Cross-check) | Re-timed from the corrected camera timestamp map (release build 2026-10-22) | --- |
| 18 | Root Event row absent from Event table | All | 1 dangling `parentEventID` | Referential check over the Event table (Cross-check) | Study root Event added; parent links validated | --- |
| 19 | Within-card clock drift | Cam | Up to 130,290 images | *none* (None (recorded once)) | Constant clock rate assumed | Unquantifiable timestamp error |
| 20 | True deployment / retrieval times | Cam | Deployment metadata known to contain errors | *none beyond the erroneous records* (None (recorded once)) | Corrected occurrence dates used instead | True camera-days not reportable |
| 21 | Manual starling supplement appended twice | Drone | 24 rows / 12 distinct `occurrenceID`s in the drone and merged Occurrence tables (2026-11-01) | Duplicate `occurrenceID` check (Cross-check) | Repaired in the release build: the 12 exact duplicate rows are dropped, leaving every `occurrenceID` unique (318,215 drone Occurrences) | --- |
| 22 | Merged snapshot and camera release disagree on camera labels | Cam | 224,149 first-generation vs 72,769 post-triage Occ.; 13 vs 19,762 camera Events | Row-count parity between the camera release tables and the merged table (Cross-check) | Not yet repaired; regenerate the merged snapshot and the camera detection-layer arrival traces from the post-triage tables | Cross-modal totals (552,964) and camera detection-layer traces describe the first-generation labels |
