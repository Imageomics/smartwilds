# Arrival traces

`scripts/arrival_traces/generate_arrival_traces_v2.py` derives the Campaign-2
(August 4–28, 2025) arrival streams used in the systems analysis from the
Darwin Core tables. It has no arguments: run it from the `scripts/` directory
of a table set, and it reads `../events_all_modalities.csv`,
`../occurrences_all_modalities.csv`, and the drone Occurrence table, and writes
`../analysis/arrival_traces_v2/`.

```bash
cd "$SMARTWILDS_DWC_OUT"/scripts
python generate_arrival_traces_v2.py
```

Two layers, one stream per modality:

| Layer | Unit of arrival | Streams |
|---|---|---|
| Acquisition | One recording or image capture | `acoustic_wav_recording`, `camera_image_capture` |
| Inference | One retained Occurrence | `camera_operational_occurrence`, `bioacoustic_machine_occurrence`, `drone_machine_detection_crop`, `citizen_science_curated_occurrence` |

Every output row links back to its source Event or Occurrence (`sourceID`),
carries a second-level timestamp and a `timeEligible` flag (date-only records
are kept but excluded from inter-arrival statistics), and names the release it
came from. `arrival_trace_contract_v2.json` records, per stream, the unit,
inclusion rule, date window, counts, rate, coefficient of variation, and
burstiness; `input_manifest_v2.json` carries SHA-256 checksums of inputs and
outputs.

Rates are time-eligible arrivals divided by the fixed 600-hour window; CV is
the population standard deviation over the mean of successive inter-arrival
intervals; burstiness is `B = (CV - 1) / (CV + 1)`. The arrival statistics are
in the [supplemental material](../SUPPLEMENTAL.md#s13-arrival-characterization-both-layers).
