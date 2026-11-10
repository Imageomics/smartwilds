# Data

## What is shipped

### `primitives/` — the workload model (4.8 MB)

One JSON per modality, the output of the characterize phase. Each contains the
change-point rate model, aggregate and per-site burstiness statistics, the
diurnal profile, and the campaign-2 date range. **These are what synthesis
actually reads** — the repository generates traces for all four modalities from
these alone, with no access to the field archive.

Scoped to `campaign2_aug4_aug28` (`2025-08-04T00:00:00 .. 2025-08-28T23:59:59`).

Verified free of location and raw-media identifiers: no coordinates, no file
paths into the archive, no per-detection records. Sites appear only as opaque
labels (`TW01`, `TW06|hourly`).

### `timestamps/` — derived event tables for two modalities

`synthesize.py` routes bioacoustic and citizen science through a timestamp
bootstrap rather than the change-point model, because their rate models are too
coarse to reproduce arrival burstiness (~90 segments for 1,714 bioacoustic
events; a single segment for 991 citizen-science events).

These two tables are therefore required for synthesis and are committed here.
They carry only `timestamp, modality, site, label`.

## What is not shipped, and why

| Artifact | Why not |
|---|---|
| `timestamps_combined.csv` (101 MB) | Contains `source_file` paths into the raw field archive; too large for git |
| `timestamps_camera_trap.csv`, `timestamps_drone.csv` | Large, and not needed — those modalities synthesize from the change-point model |
| Raw imagery, audio, video | Not redistributable |
| Precise GPS | Withheld; conservation-sensitive |
| Independence bounds (Exp 2) | Not present in the source tree either — see below |

## Regenerating the derived tables

If you have the field archive:

```bash
python3 scripts/00_prepare/make_event_tables.py \
    --combined /path/to/timestamps_combined.csv
```

This drops `source_file` and every other archive-linked column, keeping only the
four redistributable ones.

## Independence bounds are absent

`synthesize.py` looks for cross-modal correlation matrices to bound the
interleave combinator. They are not in this repository, and were not in the
source tree either. When absent it logs a warning and **assumes full
independence**:

```
WARNING synthesize: Independence bounds not found at ...; synthesis will assume
full independence
```

This is consistent with the paper's own finding F2 — all pairwise
`C_{m,m'} < 0.05` at 1 h — so the assumption matches the measured data. But it
is an assumption the code makes silently at INFO/WARNING level, not a value it
reads. Note it if you rescope the synthesis to finer temporal granularity, where
independence is applied as an assumption rather than a measurement (§V-B).
