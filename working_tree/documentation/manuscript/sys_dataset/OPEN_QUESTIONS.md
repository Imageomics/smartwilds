> **SUPERSEDED** by [DATA_QUALITY_QUESTIONS.md](DATA_QUALITY_QUESTIONS.md),
> which is the current team-facing list. Kept only for history.

# Open questions / version discrepancies — smartwilds_sys_dataset

Raised while drafting `smartwilds_sys_dataset.tex` (2026-10-01). Each item is
marked `\TODO{}` in the manuscript at the point it matters. **Not guessed at** —
needs a decision from Jenna / the group.

---

## 1. Which snapshot does this paper report? (blocking for all tables)

Two snapshots are in play and they differ *semantically*, not just additively.

| Quantity | Pre-curated-bird (used by `matrix_empirical_20260907.md`) | Post-curated-bird (`darwin_core_latest_20260724` as of 2026-09-20) |
|:--|--:|--:|
| Camera-trap occurrences | 223,203 | 224,149 |
| Drone occurrences | 317,559 | 318,203 |
| Merged occurrences | 551,374 (biodiversity-filtered) / ~551,762 | 552,964 |
| Camera-trap unique dates | 29 | 30 |
| Drone hourly bins | 8 | 9 |
| Drone `locationID`s | 15 | 15 |

The curated-bird update appended 946 validated camera-trap + 644 validated drone
records (= the 1,590 `validated` rows).

The draft currently uses **post-curated-bird** for schema/occurrence tables
(Table 3) and **pre-curated-bird** for the Campaign-2 arrival primitives
(Table 5), because that is how the source files stand. These need to agree, or
the paper needs to say explicitly which number came from where.

**Also:** `scope_and_quality_audit.md` reports 551,374 "latest-snapshot
occurrence rows retained" and a split of 2,080 direct event rows vs 2,110
parent-closure rows, against 2,404 events in the released table. Is the
2,080/2,110 figure a biodiversity-filtered subset, or a different snapshot?

---

## 2. Arrival-primitive event counts don't match occurrence counts (Table 5)

`processing_output/experimental_resultsv2/exp1_characterization/primitives/*.json`
(Campaign 2, Aug 4–28):

| Modality | `total_events` in primitives | DwC occurrences (all campaigns) |
|:--|--:|--:|
| camera_trap | 189,289 | 224,149 |
| drone | 98,335 | 318,203 |
| bioacoustic | 1,570 | 9,960 |
| citizen_science | 139 | 622 |

Campaign-2-only filtering explains part of this but not the drone gap
(98,335 vs 318,203, when drones only flew 6 dates total). **What is an "event"
in the primitives — per-image / per-frame arrivals, deduplicated detections,
or something else?** The caption needs a precise definition.

---

## 3. 146 WAV files on disk have no `AudioRecording` event

- Raw WAV on disk: **2,453** (311 in C1, 2,142 in C2) — matches
  `sensor_configurations.md` per-recorder counts exactly.
- `AudioRecording` events in DwC: **2,307**.
- Per-deployment deltas: TW02 659→561, TW06-C2 508→475, TW05-C2 100→96,
  TW06-C1 77→75, TW08-C1 78→69, TW05-C1 144→144, TW07-C1 12→12,
  TW07-C2 339→339, TW08-C2 341→341, TW09 195→195.

**What is the QC rule that drops these 146?** Truncated/zero-length files, a
minimum-duration threshold, BirdNET failures? The draft describes them as
missingness category 4 ("captured but lost or unusable") and needs the rule.

---

## 4. One drone video not processed

39 raw drone videos on disk (`*.mp4`/`*.mov` across all three campaigns);
38 `MediaEvent` events. **Which video, and why?** (`matrix_empirical` also says
"39 raw video files" and "38 geolocated drone video Tree-of-Life prediction
CSVs", consistent.)

---

## 5. Drone session count: resolved

The release contains **15 video-bearing flight/session directories** and 15
drone `SensorDeployment` Events: 10 Parrot Anafi directories, one DJI
directory, and four DJI Air 2 directories. The three additional Aug. 25 Parrot
directories contain metadata but no video files, so they are not release
sampling units. Authored manuscript and configuration references now use 15;
any count of field attempts must be labelled separately from the video-bearing
release inventory.

## 6. Citizen-science media count: resolved

The release distinguishes: **1,103** raw `photos_videos` files (965 still
images and 138 videos), **791** manually annotated photo rows, **564** curated
wildlife photos, and **622** Darwin Core Occurrences across 13 sessions. Fifty
curated September 8 assets came from the Google Photos album export, so they
are not part of the 1,103-file raw-folder inventory and are explicitly marked
as external-album media in the Darwin Core table. The old `~991` and `1,128`
values are not reproducible from the current inventory.

## 7. Drone fallback-coordinate fraction: 15.66% or 22.1%?

- `darwin_core_latest_20260724/README.md` projection-status table: non-`ok` =
  27,306 + 24,467 + 18,324 + 122 = **70,219 / 317,559 = 22.1%**.
- `scope_and_quality_audit.md`: "Of 292,106 plotted drone points, 45,736
  (**15.66%**) are non-`ok` fallback coordinates."

Different denominators (292,106 vs 317,559). The draft uses 22.1% for the
dataset-wide statement and quotes 15.66% as the audited figure *for that
specific spatial figure*. **Confirm that reading is right.**

---

## 8. Camera-trap image totals

- `find` over raw dirs: **235,778** JPG — exactly matches the timestamp-map row
  count, and the sum of the 12 per-deployment counts in
  `camera_timestamp_summary_by_camera.csv`.
- `MULTI_MODAL_ARCHITECTURE.md` data-flow diagram: "(243k)".

The draft uses 235,778. Is 243k a stale estimate, or does it include video
frames / the withdrawn TW07 deployment?

---

## 9. TW07-CT05 disposition: resolved to the available evidence

`TW07-CT05/metadata.txt` says the camera was monitored through the mobile app,
was triggered by buses rather than animals, and that all people-only photos were
not uploaded. The retained project archive contains that metadata file and no
image media; the released Darwin Core tables contain no Event or Occurrence for
this deployment. This supports the release statement that the sensitive imagery
was deliberately excluded. It does not establish whether material remaining on
the camera was later deleted, so the manuscript makes no deletion claim.

## 10. Hardware metadata conflicts between docs

| Item | `sensor_configurations.md` | `MULTI_MODAL_ARCHITECTURE.md` |
|:--|:--|:--|
| ARU model | Song Meter **Micro 2** | Song Meter **4** |
| ARU freq. response | — | 200–12,000 Hz |
| DJI airframe (C2 Aug 11) | "DJI (unspecified)" | "DJI_Mavic" |
| Camera HFOV (GardePro T5NG) | 56.5° | 52° |

The DwC event rows say "Song Meter Micro 2", so the draft uses Micro 2 / 56.5°
and "unspecified DJI airframe". The architecture doc looks like it has stale
example values — worth correcting there too.

---

## 11. Site coordinates in `MULTI_MODAL_ARCHITECTURE.md` are wrong

Architecture doc camera-deployment examples use **39.498, −81.442** and the
study-level event example uses **39.50, −81.44**. `sensor_configurations.md` and
the actual DwC rows use **≈39.83, −81.73**. These are ~30 km apart; 39.83/−81.73
is The Wilds. The draft uses no explicit coordinates, but the architecture doc
should be fixed.

---

## 12. Root event row is missing from the event table

`events_all_modalities.csv` has 2,404 rows. The five `Project` rows all declare
`parentEventID = TheWilds_2025`, but **there is no row with
`eventID = TheWilds_2025`** — it's a dangling parent reference. The QC summary's
four structural checks don't cover this.

The draft describes a four-level hierarchy with a study root and notes the
dangling reference in the defect table. **Should the root row be added to the
release?** (It's a one-line fix and would make hierarchy traversal clean.)

---

## 13. Campaign scope: is the Sep 8 revisit in the release? Are there Oct flights?

- `todo.md` says "drone flights also conducted in Oct".
- The DwC drone project event spans 2025-07-01 → **2025-09-08**, and
  `thewilds_20250908_20250908/` exists with 4 DJI Air 2 flights (11 GB).
- No October directory exists in the project space.

The draft treats Campaign 3 = 2025-09-08 as in scope and does not mention
October. **Confirm: are the October flights a separate, not-yet-ingested
campaign, or the same data mislabeled?**

---

## 14. Missing analyst-hour estimates (§7.5, "Human Effort")

We argue post-hoc metadata repair cost more than the field deployment. The paper
would be much stronger with even rough numbers for (a) timestamp
reconstruction and (b) taxonomy review. **Does anyone have an estimate?**

---

## 15. Release logistics (§8.2)

Needs: DOI, repository (HF / Zenodo / GBIF), license (CC BY 4.0 assumed from the
FAIR² Drones template), maintenance commitment, contact, and the acknowledgments
/ funding list.

---

## Build note

`acmart.cls` is **not installed** on the OSC TeX Live 2020 installation
(`kpsewhich acmart.cls` returns nothing; no copy anywhere under
`/fs/ess/PAS2136`). The draft was syntax-verified by compiling with
`article`+`twocolumn` — no LaTeX errors, no undefined citations, 49 references
resolved. To build the real thing, drop the ACM template
(<https://github.com/borisveytsman/acmart>, or `acmart.cls` + `ACM-Reference-Format.bst`)
into this directory.

`references.bib` has three genuine duplicate entries with case-variant keys that
make BibTeX error out if both are cited: `buxton2018pairing` /
`Buxton2018Pairing`, `lombardo2026paradigms` / `Lombardo2026Paradigms`,
`wieczorek2012darwincore` / `Wieczorek2012DarwinCore`. Also
`lahozmonfort2021monitoring` and `Lahoz-Monfort2021Comprehensive` are the same
paper under non-case-variant keys (BibTeX doesn't catch that one). The draft
cites only one of each pair; the bib itself is unmodified.
