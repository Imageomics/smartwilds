# SmartWilds — open data quality questions

**For team review.** Raised while drafting the SenSys systems-dataset paper,
2026-10-01. Everything below was verified directly against files in
`/fs/ess/PAS2136/TheWilds2025`, not taken from summary docs.

Snapshot in use: **`processing_output/darwin_core_latest_20260724`, post-curated-bird
(updated 2026-09-20)** — confirmed by Jenna. 552,964 Occurrences / 2,404 Events.

Priority key: **P1** = blocks the paper and affects the released data ·
**P2** = needs a definition or a decision · **P3** = fix in the source docs.

---

## P1 — Found a real defect: `nan` written into `eventDate`

**The 2025-08-11 drone session has no usable timestamp, and our QC check says it does.**

`QC_SUMMARY.md` reports `missing_eventDate=0` for drones. That check tests for
null/empty. These rows contain the literal three-character string `nan` — what a
dataframe export writes for a missing value — so they pass.

Scope: **41,524 Occurrences = 13.1% of all drone Occurrences**, across 5
`MediaEvent` rows and their parent `SensorDeployment`:

| eventID | Occurrences |
|:--|--:|
| `TheWilds_2025_drone_20250811_DJI_01_DJI_0002` | 12,522 |
| `TheWilds_2025_drone_20250811_parrot_01_P5190525` | 12,430 |
| `TheWilds_2025_drone_20250811_parrot_01_P5190526` | 11,996 |
| `TheWilds_2025_drone_20250811_DJI_01_DJI_0001` | 4,535 |
| `TheWilds_2025_drone_20250811_parrot_01_P5180524` | 41 |
| `TheWilds_2025_drone_20250811_DJI_01` (deployment) | — |

The same rows have an **empty `eventTime`**.

Consequences already visible in our own numbers:
- Drones appear to have operated on **6 dates when they operated on 7**.
- Drone hourly bins read 9; Aug 11 contributes none.
- Campaign-2 drone arrival statistics are computed over **2 flight dates, not 3**.

**Recoverable?** The *date* yes — it's in the `eventID` (`20250811`). The
**intra-day time is not recoverable** from anything we have, so these records can
be placed on a day but never within it, and they can't contribute to
inter-arrival/diurnal analysis.

**Asks:**
1. Should we repair `eventDate` from the identifier and re-release, or leave it
   and document? (Paper currently documents rather than silently repairing.)
2. Can the Aug 11 intra-day times be recovered from the raw telemetry or video
   file mtimes? If yes it's worth doing — it restores a third of Campaign-2
   drone coverage.
3. **The validator needs to parse, not test for emptiness.** Any string that
   fails `date.fromisoformat` should fail the build. Same for sentinel values
   generally (`nan`, `None`, `NULL`, `-1`, `1970-01-01`).
4. Worth auditing every other column the same way — we only found this because
   the arrival analysis choked on it.

---

## P1 — Root Event row missing from the Event table

`events_all_modalities.csv` has 2,404 rows. All five `Project` rows declare
`parentEventID = TheWilds_2025`, but **there is no row with
`eventID = TheWilds_2025`**. It's a dangling parent reference, and none of the
four structural checks cover it.

One-line fix, and it makes hierarchy traversal clean. **Add it?**

---

## P2 — What counts as an "event" in the arrival primitives?

`processing_output/experimental_resultsv2/exp1_characterization/primitives/*.json`
(Campaign 2) vs the DwC Occurrence table:

| Modality | `total_events` in primitives | DwC Occurrences |
|:--|--:|--:|
| camera_trap | 189,289 | 224,149 |
| drone | 98,335 | 318,203 |
| bioacoustic | 1,570 | 9,960 |
| citizen_science | 139 | 622 |

Campaign-2 filtering doesn't explain the drone gap. I also couldn't
reverse-engineer `mean_rate_per_hour`: camera 189,289 / 154.4984 implies a
1,225-hour window, but Campaign 2 is 600 hours. (`B` *is* reproducible —
it's exactly `(CV−1)/(CV+1)` over inter-arrival times.)

**Because I couldn't define these, the paper does not use them.** I recomputed
arrival statistics from the post-curated-bird Occurrence table with an explicit
definition, and got a two-layer characterization that I think is actually a
better result:

| Stream | Arrivals | Rate/hr | CV | B |
|:--|--:|--:|--:|--:|
| *Acquisition layer* | | | | |
| Camera image captures | 220,697 | 367.83 | 2.07 | +0.347 |
| Acoustic WAV recordings | 2,007 | 3.35 | 1.23 | +0.104 |
| *Detection layer* | | | | |
| Camera traps | 208,054 | 346.76 | 7.26 | +0.758 |
| Bioacoustics | 8,865 | 14.78 | 3.21 | +0.525 |
| Drones | 53,238 | 88.73 | 229.61 | +0.991 |
| Citizen science | 242 | 0.40 | 5.30 | +0.682 |

Definitions: window = 2025-08-04 to 2025-08-28 (600 h). *Acquisition arrival* =
one image capture (from the corrected camera timestamp map) or one WAV recording
(from `AudioRecording` Event times). *Detection arrival* = one Occurrence with a
resolvable date+time. `B = (CV−1)/(CV+1)` over inter-arrivals. Drone detections
exclude the Aug 11 session (see P1).

The finding: **inference amplifies burstiness** in every modality where both
layers are measurable (camera +0.35 → +0.76; acoustic +0.10 → +0.53), because
most captures contain no animal and the ones that do contain several.

**Asks:**
1. Confirm the primitives' event definition so we can state how the two relate.
2. **Does the SEC paper need to match?** If the SEC traces use the primitives,
   the two papers will report different burstiness numbers for the same
   deployment. We should either reconcile or state the definitions explicitly in
   both.

---

## P2 — 146 WAV files on disk have no `AudioRecording` Event

- Raw WAV on disk: **2,453** (311 in C1, 2,142 in C2) — matches the per-recorder
  counts in `sensor_configurations.md` exactly.
- `AudioRecording` Events: **2,307**.

Per-deployment deltas:

| Deployment | Raw WAV | Events | Dropped |
|:--|--:|--:|--:|
| TW02-SM04 (C2) | 659 | 561 | 98 |
| TW06-SM05 (C2) | 508 | 475 | 33 |
| TW08-SM04 (C1) | 78 | 69 | 9 |
| TW05-SM06 (C2) | 100 | 96 | 4 |
| TW06-SM03 (C1) | 77 | 75 | 2 |
| all others | — | — | 0 |

**What's the rule?** Truncated/zero-length files, a minimum-duration threshold,
BirdNET failures? The paper lists these as a missingness class and needs the
rule stated. Note the drops are concentrated in the two highest-file-count
deployments, which hints at a size/duration filter rather than random loss.

---

## P2 — One drone video not processed

39 raw drone videos on disk (`*.mp4`/`*.mov`, all three campaigns); 38
`MediaEvent` rows. **Which one, and why?**

---

## P2 — Drone session count: 15 or 16?

- `sensor_configurations.md`: Parrot Anafi 11 sessions + DJI unspecified 1 +
  DJI Air 2 four flights (Sep 8) = **16**
- DwC `SensorDeployment` under `TheWilds_2025_drones`: **15**
- `matrix_empirical_20260907.md`: "15 flight/session directories"

Is one Sep-8 flight merged, or is one session excluded? The paper says 16 flight
sessions in the campaign description and 15 deployment Events in the schema,
which reads as an error unless we explain it.

---

## P2 — Citizen-science media count: four different numbers

| Source | Count |
|:--|--:|
| Files on disk in `citizen_science/photos_videos` | **1,103** |
| `matrix_empirical_20260907.md` | 1,128 photographs |
| DwC `citizen_science` Project `sampleSizeValue` | 564 photographs |
| `MULTI_MODAL_ARCHITECTURE.md` | "~991 submissions" |

Paper currently uses 1,103 (verified on disk). **Which is the release number?**
564 vs 1,103 suggests a curation filter we should describe.

---

## P2 — TW07-CT05 disposition (ethics statement)

`thewilds_20250804_20250828/camera_traps/TW07-CT05/` holds **one `.txt` file and
no images**. `sensor_configurations.md`: "ALL PEOPLE (tour buses); no wildlife
images".

**Were the images never transferred off the card, or deleted after review?** This
goes in the ethics/sensitive-data statement, so I'd rather not characterize it
without confirmation.

---

## P2 — Post-deployment analyst time (field time is now measured)

**Resolved half of this.** The Campaign-2 Jotform logs timestamp every service
visit, so field servicing effort is measurable and is now in the paper:
**23 sensor actions across 3 trips, 245 min (4.1 h) of elapsed field time**,
per-trip 103 / 66 / 76 min, median 16 min between actions on the first trip and
3 min on the later two, plus access-difficulty ratings, battery, and SD status
per action. Caveat stated in the paper: the exports cover the three mid-campaign
trips only — Campaign-1 notes have no clock times and the Aug 28 retrievals are
not in the forms.

**Still open:** nothing records analyst time per processing stage. The paper can
say what the deployment cost in the field but not what the repair cost at the
desk. **Rough wall-clock estimates for (a) timestamp reconstruction and
(b) taxonomy review would let us state that side as a figure instead of a list.**

Also worth asking: are the **Aug 28 retrieval** form submissions recoverable from
Jotform? That would close out Campaign-2 field effort completely.

---

## P3 — Stale values in `MULTI_MODAL_ARCHITECTURE.md`

Worth correcting in the doc regardless of the paper:

| Item | Architecture doc | Actual (DwC rows / `sensor_configurations.md`) |
|:--|:--|:--|
| Site coordinates | 39.498, −81.442 / 39.50, −81.44 | **≈39.83, −81.73** (~30 km off) |
| ARU model | "Song Meter 4" | **Song Meter Micro 2** |
| GardePro T5NG HFOV | 52° | **56.5°** |
| DJI airframe (C2 Aug 11) | "DJI_Mavic" | unspecified DJI |
| Camera image count | "(243k)" | **235,778** JPG |
| Bioacoustic occurrences | "~40,000" | **9,960** |
| Citizen science | "~991 submissions" | 13 observation sessions |

Most of these look like placeholder example values that were never updated.

---

## P3 — `references.bib` has duplicate entries

Three pairs differ only in case and make BibTeX hard-error if both are cited:
`buxton2018pairing`/`Buxton2018Pairing`, `lombardo2026paradigms`/`Lombardo2026Paradigms`,
`wieczorek2012darwincore`/`Wieczorek2012DarwinCore`. Also
`lahozmonfort2021monitoring` and `Lahoz-Monfort2021Comprehensive` are the same
paper under non-case-variant keys (BibTeX won't catch that one). The draft cites
one of each; the bib is unmodified.

---

## P2 — Companion paper citations

The draft now cites two companions and keeps its own scope narrow accordingly:

- `smartwilds_workload` — the full workload-characterization paper. §7 of this
  draft was cut back to a summary that defers to it.
- `smartwilds_ecology` — the ecological research-questions paper. This draft
  reports no ecological results.

Both are **placeholder entries** appended to `references.bib`. **Need titles,
venues, years, and author lists.** Also worth confirming the scope split reads
correctly from the other two papers' side, so the three don't overlap.

---

## Resolved

- **Which snapshot?** → post-curated-bird (`darwin_core_latest_20260724` as of
  2026-09-20). The 946 camera-trap + 644 drone `validated` records are the bird
  annotations added from the goose/swan review. Paper uses this throughout.
- **Drone geolocation framing.** → Flights were for population estimation and
  behavior, not geolocation. Drone GPS localizes animals to a pasture, which is
  adequate for biodiversity estimates; per-animal monocular projection from a
  moving platform is unreliable and not standard practice. The paper now treats
  platform position as a first-class adequate spatial reference and the 77.9%
  projection rate as the size of the attemptable subsample, **not** a failure
  rate. No result depends on a projected drone position.
- **Semi-automated analysis framing.** → The paper now argues that manual
  annotation does not scale to sensor-network volumes (our human-reviewed
  records are 0.4% of the release), that SOTA models (SAM3, BioCLIP
  Tree-of-Life, BirdNET) are used so reported quality reflects what a
  practitioner adopting today's best tooling would obtain, and that publishing
  model identity, version, parameters, per-rank accuracy, and per-record
  verification status is what makes the labels re-derivable when better models
  arrive.
- **October drone flights.** → None flown yet; out of scope. Campaign 3 =
  2025-09-08 is the last campaign in the release, and the paper says so.
- **"Event" is overloaded.** → The paper now reserves *Event*/*Occurrence*
  (capitalized) for Darwin Core record types, uses *arrival* for the systems
  sense, and includes a glossary table covering Event, Occurrence, arrival,
  deployment, sampling effort, duty cycle, detection, identification,
  `locationID`, and coverage.

---

## Also worth knowing (not questions — just verified facts)

Numbers in the draft, all checked against files:

- Raw: **561 GB** — C1 101 GB, C2 449 GB, C3 11 GB
- Camera: **235,778** JPG + **5,113** video clips, 13 deployments (12 retained)
- Acoustic: **2,453** WAV, 10 deployments, 6 sites
- Drone: **39** videos, 3 platforms
- Citizen science: **1,103** media files
- DwC Events: 2,404 = 5 `Project` + 37 `SensorDeployment` (12 camera + 10 ARU +
  15 drone session) + 2,307 `AudioRecording` + 38 `MediaEvent` +
  17 `ObservationSession`
- Verification: 550,722 `unverified` (99.6%), 1,590 `validated`,
  652 `verified by expert`
- Camera timestamps: **18** correction methods; 14,472 images (6.1%) accepted as
  recorded, 221,306 (93.9%) reconstructed; 105,488 high confidence (44.7%),
  130,290 medium (55.3%); 0 unmapped, 0 flagged for review
- Raw timestamp sources: 193,096 filename, 42,500 EXIF, 179 OCR of burned-in
  overlay, 3 read by hand

---

## Building the PDF

`acmart.cls` is **not** in the system TeX Live 2020 on OSC, but it **is** in the
`texlive/2025` module. `build.sh` loads it:

```bash
./build.sh            # review build, \TODO notes visible
./build.sh --submit   # submission build, \TODO notes suppressed
```

Both write `smartwilds_sys_dataset_{review,submit}.pdf` here and print fatal
errors, undefined citations/references, overfull-hbox count, and the page count.
Current state: **12 body pages**, references on 13–14, no errors, no undefined
references, no overfull boxes over 15 pt. SenSys full papers allow 12 pages
excluding references, so it fits — but only just, with the review notes off.
