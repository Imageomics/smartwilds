# Joining the modalities in space and time

The point of the release is that four independently collected modalities can
be put on the same spatial and temporal footing. This page says which columns
do that, what their precision is, and where the traps are. A runnable example
is at `examples/join_camera_acoustic_by_site_hour.py`.

## Temporal keys

| Column | Tables | Meaning |
|---|---|---|
| `eventDate`, `eventTime` | all Occurrence tables | Local date and time of the record. Camera-trap values are the **corrected** timestamps, not the camera clock. An `eventDate` interval (`start/end`) means the record is only known to lie in that span |
| `corrected_timestamp`, `correction_method`, `correction_confidence` | `images.csv` (camera traps) | Per-image corrected capture time, the method that produced it (18 methods, supplement S5), and its confidence |
| `timestampPrecision`, `timeEligible` | arrival traces | `second` or `day`; whether the record can enter inter-arrival statistics |

!!! warning "Three temporal traps"
    - **Camera clocks were wrong on 93.9% of images** (defect 1). Use the
      corrected values; the burned-in overlay in the image shows the raw clock.
    - **The 2025-08-11 drone flights have a date but no time** (defect 15):
      their `eventTime` is blank and they cannot be placed within the day.
    - **Acoustic Events are recording windows**, not instants: a 5- or
      15-minute WAV. An acoustic Occurrence's time is the recording start.

Campaign windows: June 30 – July 3 (campaign 1), August 4 – 28 (campaign 2),
September 8 (campaign 3). The deployment Events carry each sensor's actual
`eventDate` interval, which is the right denominator for effort.

## Spatial keys

| Modality | `locationID` | Coordinates | Uncertainty |
|---|---|---|---|
| Camera traps | Site code `TW01` … `TW11` | Deployment Event: camera position. Occurrences inherit the site; animal positions are not inferred in the released table | 5 m |
| Bioacoustics | Site code | Deployment Event: recorder position | 50 m |
| Drones | Flight identifier (`20250818_parrot_01`) | Deployment Event: flight centroid; `MediaEvent`: video position; Occurrences: ground-projected box position where `georef_status = ok` | 100 m (flight), per-row for projections |
| Citizen science | none | Park-level point on the observation session | 5,000 m |

Fixed sensors are joined by **site code and campaign**, because several
sensors moved between campaigns (the TW07 recorder, the TW09 camera after
August 18; defect 6). Drones and citizen science have no site code and are
joined by coordinates or by date.

Site codes are shared across modalities. In campaign 2, camera traps and
recorders were co-located at TW02, TW06, and TW09; the supplemental material
(S2, S3) lists every deployment with its coordinates and dates.

## The Event hierarchy

All tables share one hierarchy rooted at `TheWilds_2025`. Walking
`parentEventID` from an Occurrence's `eventID` reaches the deployment (or
flight, or session), then the modality's Project, then the study root. That is
how an Occurrence finds its campaign, its sensor configuration, and its
deployment coordinates.

## Example: camera and acoustic co-occurrence by site-hour

```python
--8<-- "examples/join_camera_acoustic_by_site_hour.py"
```

On the current tables this reports 403 site-hours (of 2,299 with any
detection) in which both a camera and a recorder at the same site produced
Occurrences, at TW02, TW06, and TW09.

## Arrival traces

For workload or systems questions, `analysis/arrival_traces_v2/` in the
study-level dataset already has the campaign-2 streams at two layers with
checksums and a contract describing units and inclusion rules; see
[Arrival traces](../scripts/arrival-traces.md).
