# Field campaigns

Field notes, data summaries, and the per-campaign data reports for the three
2025 SmartWilds campaigns at The Wilds. The raw media and the processed
detection outputs described in these reports are not in this repository; they
are distributed through the SmartWilds datasets (see the top-level README).

| Campaign | Dates | What is here |
|---|---|---|
| `thewilds_20250630_20250703/` | June 30 – July 3, 2025 (pilot) | `field_notes/` (equipment list, site descriptions, deployment and retrieval notes), `data_summary.md` (working file inventory), data report |
| `thewilds_20250804_20250828/` | August 4 – 28, 2025 | Data report. Deployment and check-in logs were collected through JotForm and are summarized in the report |
| `thewilds_20250908_20250908/` | September 8, 2025 (drone re-visit) | Observer notes, data report. The scanned notebook pages and photos are not included |

Each `*_data_report.md` is the agent-assisted inventory of one campaign
directory: file counts and sizes per modality and deployment, the metadata
files present, known issues (clock errors, missing telemetry, battery
exhaustion), and the people who collected the data. Paths written as
`<archive>/...` refer to the project's field archive, which is not public.

The site descriptions record GPS fixes for the sensor sites. Those fixes are
also the basis of the `decimalLatitude`/`decimalLongitude` values in the
released Darwin Core Event tables.
