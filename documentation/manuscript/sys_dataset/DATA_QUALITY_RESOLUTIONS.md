# SmartWilds Data Quality and Representation Resolutions

**Status:** evidence review and release repairs completed 2026-10-10. This document answers the
questions in `DATA_QUALITY_QUESTIONS.md` from the repository artifacts that are
currently available. It separates confirmed defects, resolved representation
questions, and items that require a data owner rather than speculation.

## Release Rules

- A release count must state its unit: raw file, retained media item, event,
  detection crop, or curated wildlife photo. These are not interchangeable.
- A value recovered from an identifier must be marked as derived, including the
  rule used. Do not synthesize an intra-day timestamp from a file modification
  time.
- A source file, transformation, and exclusion reason must be retained for
  every release row or aggregate. Counts without a named denominator are not
  release metadata.

## P1: Invalid Drone Dates

**Finding: confirmed release defect.** The five 2025-08-11 per-video
geolocation inputs contain the literal string `nan` in `date_time`.
`generate_darwin_core_latest_20260724.py` passes that string through
`split_datetime`, which writes `nan` into `eventDate`. Its validator only
checks `not r.get("eventDate")`, so `nan` is reported as present.

**Resolution:** issue a new snapshot. For the five video events, their parent
deployment, and their occurrences, set `eventDate` to `2025-08-11`, derived
from the unambiguous flight identifier `20250811_*`. Keep `eventTime` empty.
Record in `fieldNotes`/`occurrenceRemarks` that the date was identifier-derived
and that source intra-day telemetry was unavailable. Do not use these rows in
diurnal or inter-arrival analyses unless source capture times are recovered.

**Implemented 2026-10-08:** the current snapshot now has `eventDate=2025-08-11`
and blank `eventTime` for 7 affected event rows and 41,524 related occurrences
in both modality-specific and merged CSVs. Per-file backups and
`invalid_drone_date_repair_20261008.json` preserve the repair audit.

**Implemented generator and QC controls (2026-10-10):**

1. The generator strictly parses dates and times and rejects sentinel values such
   as `nan`, `none`, `null`, `-1`, and `1970-01-01` before export.
2. The integrity audit validates every Event and Occurrence date/time, coordinate
   pair, parent link, source-to-merged value, and local media reference.
3. The final audit reports zero errors and zero warnings:
   `processing_output/darwin_core_latest_20261008/DARWIN_CORE_AUDIT_20261010_FINAL.json`.

The existing drone README identifies 15 flight-level exports, and the Aug. 11
flight entries show the expected two DJI and three Parrot video sources. No
artifact reviewed contains trustworthy intra-day timestamps for those five
videos.

## P1: Invalid Drone Coordinates

**Finding: confirmed release and generator defect.** The affected drone inputs
contained literal `nan` values and impossible coordinate pairs, including
longitude near `500`. The released snapshot was repaired, but the generator
previously retained the old fallback logic and could reintroduce those values
on regeneration.

**Implemented 2026-10-10:**
`generate_darwin_core_latest_20261008.py` now accepts a coordinate only when
both values are finite and within WGS84 bounds. Occurrences prefer a valid
projected animal position, then valid frame/drone telemetry. If neither is
valid, the generator uses a static, video-level QuickTime ISO-6709 location
read from a whitelisted original MP4 only when that location is within a
conservative The Wilds study-area envelope. It otherwise leaves latitude,
longitude, and coordinate uncertainty blank and records the unavailable source.
Media Events use telemetry or that static video-level fallback; flight parent
Events remain blank when a single session-level coordinate cannot be defended.

The full dry-run audit over all 317,559 generator input occurrences found zero
invalid occurrence or MediaEvent outputs: `processing_output/darwin_core_latest_20261008/generator_drone_coordinate_parity_audit_20261010.json`.
The corresponding released-table repair remains documented in
`processing_output/darwin_core_latest_20261008/invalid_drone_coordinate_repair_20261009.json`.

## P1: Drone Media Reference Portability

**Finding: confirmed release portability defect.** Drone Occurrences referenced
extracted frames under the temporary `/fs/scratch/PAS2136/smartwilds_detection`
workspace. The files were no longer present, leaving 16,069 unique frame paths
unresolvable; they were referenced by 307,260 occurrence rows.

**Implemented 2026-10-10:** each unavailable scratch-frame reference was
replaced with its unique retained original-video path. Existing frame links were
kept. Occurrence remarks mark the substitution as
`associated_media_source=original_video_fallback_missing_scratch_frame`, so the
video-level fallback is not confused with a specific frame. All 38 source-video
groups resolved uniquely, with no missing replacement video. The generator uses
the same policy on regeneration. The repair audit is
`processing_output/darwin_core_latest_20261008/drone_missing_media_repair_20261010.json`.

## P1: Missing Study Root Event

**Finding: confirmed structural defect.** Every modality `Project` row names
`TheWilds_2025` as its parent, but the merged event table has no matching root
row. The generator creates modality project rows directly and never creates the
study event.

**Resolution:** prepend one `Project` event with `eventID=TheWilds_2025`, no
parent, an event span of `2025-06-30/2025-09-08`, the study-area coordinates
already used by modality rows, and a description of the multi-modal survey.
Run parent-link validation after merging all modality tables. The date span must
include the September drone campaign; the older architecture document's August
end date is stale.

**Implemented 2026-10-08; reconciled 2026-10-10:**
`darwin_core_latest_20261008/events_all_modalities.csv` contains the study root
as its first Event row. It uses the same study-area reference as the generator
(`39.83, -81.74`, 5 km uncertainty) and an event span of
`2025-06-30/2025-09-08`. The generator/release alignment check passes in the
final audit.

## P2: Arrival Primitives

**Finding: the primitive JSON files are stale and not presently reproducible.**
`export_primitives.py` defines `total_events` as the number of rows in
`timestamps_<modality>.csv` after the Campaign-2 filter. A row is therefore a
source-stream arrival, not a Darwin Core occurrence. For drones, the retained
source has one row per detection crop, as shown by repeated crop timestamps in
`timestamps_drone.csv`. `mean_rate_per_hour` is `3600 / mean(inter-arrival)`;
it is not `total_events / 600 h`, which explains the apparent 1,225-hour camera
denominator.

More seriously, only `timestamps_drone.csv` remains at the paths declared by
the primitive exporter. The camera, bioacoustic, and citizen-science timestamp
files named in the JSON provenance are absent. The four JSON files must not be
used as reproducible paper or SEC results.

**Resolution:** retire the current primitives from reported results. Regenerate
them from versioned, retained timestamp inputs and state the unit in each file:

| Stream | Recommended arrival unit |
| --- | --- |
| Camera acquisition | One corrected image capture |
| Camera inference | One retained detection crop, if compute workload is the target |
| Acoustic acquisition | One WAV recording |
| Acoustic inference | One BirdNET detection, if inference workload is the target |
| Drone acquisition | One video/frame sample, stated explicitly |
| Drone inference | One detection crop |
| Citizen science | One curated wildlife photo or observation session, stated explicitly |

Report observation-window rates separately from inter-arrival rates, and retain
the date filter, missing-time policy, and source-file manifest alongside every
primitive. The paper's two-layer characterization is defensible only after its
inputs and filtering are versioned in the same way.


**Implemented 2026-10-08 (drone inference stream):** the corrected snapshot
now includes `analysis/arrival_primitives/drone_detection_crop_arrivals.csv`.
This is deliberately a derived analysis table, not a new Darwin Core table: it
has one row for each retained machine-derived drone Occurrence and retains the
source `occurrenceID`. The 644 curated bird records from the review subset are
explicitly excluded rather than mixed into the automated stream. The file
contains 317,559 machine-derived rows; 276,035 have second-level timestamps.
For Campaign 2, 53,238 rows are time-eligible (Aug. 18 and Aug. 25); the
41,524 Aug. 11 rows are retained as date-only coverage and excluded from timed
rate/inter-arrival calculations. Its manifest records the source checksum,
inclusion/exclusion rule, and missing-time policy.

**Implemented 2026-10-09 (reproducible v2 package):**
`processing_output/darwin_core_latest_20261008/analysis/arrival_traces_v2/`
now contains five regenerated, source-linked arrival streams, their CSV inputs,
an input-checksum manifest, a machine-readable contract, and a README. The
Campaign-2 timed counts are 208,054 camera machine Occurrences, 2,060 acoustic
WAV `AudioRecording` Events, 8,865 bioacoustic machine Occurrences, 53,238
drone machine detection crops, and 242 curated citizen-science Occurrences.
Rates use the fixed 600-hour observation window, rather than an implicit
inter-arrival denominator. The package explicitly deprecates the legacy JSONs.

It deliberately does not generate a camera image-capture acquisition trace:
the frozen snapshot lacks a corrected one-row-per-image timestamp manifest for
images without detections. The package's
`UNAVAILABLE_CAMERA_IMAGE_CAPTURE_ACQUISITION.md` documents the recovery
requirement, so a machine-occurrence trace cannot be mistaken for acquisition.

## P2: Raw WAV Files Without `AudioRecording` Events

**Finding: resolved.** The earlier 146-file difference mixed three different
populations. Of the 2,453 physical WAV paths, 78 are Campaign-1 WAVs copied
into the Campaign-2 `TW02-SM04/Data` directory and are transfer duplicates,
not additional Campaign-2 recordings. Sixty-four in-window recordings have
header-only BirdNET result CSVs: processing completed, but zero detections were
emitted. The remaining four `TW05-SM06` files have no BirdNET result; three are
3.9–22.0-second fragments and one is unreadable.

**Implemented 2026-10-08:** `darwin_core_latest_20261008` now contains 2,371
unique `AudioRecording` Events. It adds the 64 processed zero-detection
recordings as Events with no Occurrences, leaves all 9,960 BirdNET Occurrences
unchanged, and does not create Events for the 78 transfer duplicates or four
failed files. The one-row-per-path reconciliation is
`bioacoustics_complete/RAW_WAV_RECONCILIATION_20261008.csv`; the detailed
policy and integrity checks are in
`bioacoustics_complete/RAW_WAV_RECONCILIATION_20261008.md`.

## P2: Raw Drone Video Not Represented by a `MediaEvent`

**Finding: resolved.** The omitted raw video was
`thewilds_20250630_20250703/drones/20250703_parrotanafi_4/video_files/VID_001.MP4`.
It has no Tree-of-Life or geolocated-prediction output because it was reviewed
and intentionally excluded: the tiny video contained no significant content.

**Implemented 2026-10-08:** the corrected Darwin Core snapshot represents it as
`TheWilds_2025_drone_20250703_parrotanafi_4_VID_001`, a `MediaEvent` under its
flight deployment. It has `sampleSizeValue=0`, no Occurrences, and field-note
provenance for the raw path, review decision, and exclusion reason. Thus the
release inventories all 39 raw drone videos while retaining occurrence evidence
for only the 38 processed videos. The audit is
`processing_output/darwin_core_latest_20261008/excluded_drone_media_event_repair_20261008.json`.

## P2: Drone Session Count

**Finding: resolved for the released data; the configuration summary is stale.**
The drone README inventories 15 flight-level exports containing 39 raw videos:
10 Parrot flight directories with media, one Aug. 11 DJI directory, and four
Sep. 8 DJI Air 2 directories. This matches the 15 `SensorDeployment` flight
units used by the release. The additional C2 Parrot directories dated Aug. 25
contain metadata only, not raw video.

**Implemented 2026-10-08:** the paper, methods matrix, and sensor
configuration now use **15 video-bearing flight/session directories**. The
configuration explicitly distinguishes the 10 Parrot Anafi, one DJI, and four
DJI Air 2 video-bearing directories from the three Aug. 25 Parrot directories
that contain metadata but no video. Any future count of all field attempts must
be labelled separately from the video-bearing release inventory.

## P2: Citizen-Science Media Counts

**Finding: resolved.** These counts describe distinct, reproducible populations:
1,103 raw files in `citizen_science/photos_videos` (965 still images and 138
videos); 791 manually annotated photo rows; 564 curated wildlife photos; and
622 taxon Occurrences from those photos. The occurrence total exceeds the photo
total because 58 additional taxon records arise from multi-taxon photos.

**Implemented 2026-10-08:** the Darwin Core citizen-science project Event now
identifies 564 as its sample size and records the raw, annotated, curated, and
Occurrence counts in `fieldNotes`. The 50 curated September 8 Google Photos
album-export assets absent from `photos_videos` are explicitly identified in
`associatedMedia` and `occurrenceRemarks`; they are not falsely represented as
local raw-folder files. Authored documentation now retires the unsupported
`~991 submissions` and `1,128 photographs` values. The audit is
`processing_output/darwin_core_latest_20261008/citizen_science_media_reconciliation_20261008.json`.

## P2: TW07-CT05 Sensitive Media

**Finding: resolved to the available evidence.** The sole retained source file,
`thewilds_20250804_20250828/camera_traps/TW07-CT05/metadata.txt`, states that
the camera was monitored by mobile app, captured people rather than animals,
and that all photos were not uploaded. The release contains no retained image
media, Darwin Core Event, or Occurrence from this deployment.

**Implemented 2026-10-08:** the ethics and supplemental text now state that
people-only imagery was excluded from the release because it was not uploaded.
They explicitly do not claim that the camera-card contents were deleted, because
the retained evidence cannot establish that. See
`TW07_CT05_SENSITIVE_MEDIA_DISPOSITION_20261008.md`.

## P2: Field and Analyst Time

**Finding: resolved for the measurable scope; analyst time remains unavailable.**
The retained Jotform exports record 23 Campaign-2 service actions on Aug. 4, 7,
and 11: 103, 66, and 76 minutes respectively, or 245 minutes (4.1 hours) of
elapsed time. They do not contain Aug. 28 retrieval entries. Campaign-1 notes
lack clock times, and no retained log records time spent on timestamp repair,
telemetry reconciliation, or taxonomy review.

**Implemented 2026-10-08:** the manuscript and supplement label 4.1 hours as
measured mid-campaign field-servicing time only. They report no total campaign
field effort and no measured analyst hours, rather than presenting retrospective
estimates as observations. See `FIELD_AND_ANALYST_TIME_AUDIT_20261008.md`.

## P3: Stale Architecture Documentation

**Finding: resolved 2026-10-09.** The previous
`MULTI_MODAL_ARCHITECTURE.md` was an aspirational/example schema rather than
a faithful description of the released snapshot. It contained obsolete event
identifiers, schema fields, coordinate examples, platform examples, counts, and
fictional citizen-science contributor names.

**Implemented:** the architecture guide now describes the validated snapshot
at `processing_output/darwin_core_latest_20261008`: its 2,470 Event records,
552,964 Occurrence records, actual event types and parent-child chains, current
modality totals, and Darwin Core field semantics. The study root and modality
projects use the coarse `39.83, -81.74` study-area reference with 5 km
uncertainty; deployment and occurrence coordinates have their own provenance
and uncertainty.

The guide also documents the source notation conversion that explains the
apparent latitude/longitude discrepancy (for example, raw
`39.49.8459, 081.44.2737` becomes WGS84 `39.83076500, -81.73789500`). Of the
2,404 Event IDs shared by the July and October snapshots, seven deliberate
drone-coordinate repairs replaced invalid `nan`/`500` values with either a
validated static original-video location or blank fields when no defensible
coordinate existed. The remaining 2,397 shared Event coordinates are unchanged.

**Proxy documentation:** the guide identifies
`zebra_shelter_drone_frame_anchor`, `sensor_config_aru_site_proxy`, and
`relocated_to_nomad_ridge_proxy_needs_review` as spatial proxies rather than
measured device GPS. The authoritative frozen release configuration is
`processing_output/darwin_core_latest_20261008/scripts/georeferencing/camera_geolocation_config.csv`;
the identical active source configuration is under
`processing_output/detections/camera_traps/methods_paper/annotations/sam3/treeoflife_sam3/geolocation/`.
For camera bearing and field-of-view inputs, see
`documentation/sensor_configurations.md`.

The corrected guide is
`documentation/annotation_pipeline/MULTI_MODAL_ARCHITECTURE.md`. The older
generic generator is explicitly labelled historical planning material and must
not be used to infer release values.

## P3: Duplicate Bibliography Entries

**Finding: confirmed in the canonical manuscript bibliography.** The duplicate
pairs named in the questions document are present, including the case-only
keys and the two Lahoz-Monfort entries for the same paper.

**Resolution:** keep one canonical key per work in
`documentation/manuscript/sys_dataset/references.bib`, update manuscript cites
to that key, and regenerate `build_review` and `build_submit` from the
canonical source. Add a bibliography check that normalizes keys case-insensitively
and flags duplicate DOI/title pairs before compilation.

## P2: Companion Paper Citations

**Finding: awaiting bibliographic authority.** The bibliography's own comments
still mark the SEC and MEE companion citations as TODOs. Repository artifacts
cannot establish their titles, author lists, venue, or publication year.

**Resolution:** retain placeholders only in private drafting material. Before
submission, replace them with owner-verified metadata, cite each companion in
third person, and add one sentence in every paper defining the non-overlapping
scope: normalized workload traces (SEC), ecological research questions (MEE),
and systems-dataset provenance/representation (this paper).

## Release Gate

**Current release status: cleared.** The invalid-date repair, root Event, strict
validation, parent-link check, media-path repair, source-to-merged parity, and
generator/release alignment all pass in
`processing_output/darwin_core_latest_20261008/DARWIN_CORE_AUDIT_20261010_FINAL.json`.

Future releases must rerun the generator and integrity audit. They must retain
the documented exclusions and unavailable metadata rather than silently merging
them into a single count. Legacy arrival JSONs remain deprecated; use only the
versioned `analysis/arrival_traces_v2/` products for reproducible workload
results.

## Addendum 2026-10-22: Cross-Check Before HF Release

An independent re-check of the snapshot against this document found the
following items. They were open, or had regressed, after the 2026-10-10 release
gate.

- **The Event table cannot be read by the group (P1, release blocker).**
  `events_all_modalities.csv`, its `before_root_parity` backup, and both
  `citizen_science/*.csv` files are mode 600 and owned by potlapally2. As a
  result, the citizen-science dataset and the study-level dataset cannot be
  staged.
- **439 curated camera Occurrences bypassed timestamp correction (P1).** 124
  TW02-CT01 SD11 records carry the drifted raw clock (`eventDate=2025-09-14`,
  which is outside both the study and the deployment). 315 TW06-CT04 records
  carry only the deployment interval as `eventDate`. All 439 map one-to-one to
  rows in the corrected camera timestamp map. The final audit did not catch
  them because it never checks that an Occurrence date lies inside its parent
  Event's span. The arrival-trace contract counts the same rows as
  `outside_defined_campaigns` / `unparseable_or_interval`.
  - **Staged fix:** `release/scripts/build_hf_release.py` re-times these
    records in the HF staging copy.
  - **Still needed:** apply the same fix in the canonical snapshot and add the
    span check to `audit_darwin_core_snapshot.py`.
- **Some drone media references are broken again (P1).** 10,943 drone
  Occurrences (479 unique frame PNGs) still point at
  `/fs/scratch/.../smartwilds_detection`, and none of those files exist now. The
  2026-10-10 repair kept frame links that existed at the time, and scratch
  storage has since been purged. The `media_paths: pass` result in the final
  audit is therefore stale.
  - **Staged fix:** the original-video fallback is applied in the staging copy.
- **Media paths are not portable (P1 for release).** Every `associatedMedia`
  value is an absolute cluster path. Bioacoustic rows carry only a bare WAV
  filename. Curated records point at copies in PAS2699. Remarks and references
  contain further `/fs/` paths.
  - **Staged fix:** all of these are rewritten to release-relative paths.
- **The camera acquisition trace can be reproduced.** Contrary to
  `UNAVAILABLE_CAMERA_IMAGE_CAPTURE_ACQUISITION.md`, the corrected
  one-row-per-image map exists at
  `processing_output/detections/drone_camera_analysis/camera_time_mapping/camera_image_timestamp_map.csv`
  (235,778 rows, all inside the campaigns). Recomputing from it gives
  220,697 Campaign-2 captures, 367.83 per hour, CV 2.06, and B = +0.347. The
  map just needs to be versioned into the release. It ships as
  `smartwilds-camera-traps/data/images.csv`.
- **The arrival-trace checksums are stale.** `arrival_trace_contract_v2.json`
  records source SHA-256 values for `occurrences_all_modalities.csv` and the
  drone occurrence file that were taken before the 2026-10-10 media repair. The
  statistics are unaffected because timestamps did not change, but the traces
  should be regenerated.
- **Drones flew on 6 dates, not 7.** The earlier "seven dates" figure counted
  the `nan` string as a date. Drone bins are 8, because the Aug 11 session has
  no time of day.
- **Raw media contains people.** 10,797 camera images contain a detection
  labelled *Homo sapiens*, and 3,114 drone Occurrences are labelled human. A
  release policy is needed for these images.
- **Sensor configuration is out of date for TW04-CT03 (Campaign 2).**
  `sensor_configurations.md` lists its facing as NW (315°). The geolocation
  config uses 225°, which was corrected after visual review.
- **The bibliography had more duplicates than reported.** Besides the pairs
  listed above, the file contained a second `Pollock2025Harnessing` entry and a
  `pollock2026putting` entry that duplicated `pollock2026roam`. All of these
  were removed on 2026-10-22, and cites now use a single key.
- **Still open:** companion-paper citations, Aug. 28 Jotform retrieval forms,
  the drone fallback-coordinate fraction (15.66% vs 22.1%, which needs
  recomputing after the coordinate repair), and release logistics (DOIs,
  license, maintenance, contact).
