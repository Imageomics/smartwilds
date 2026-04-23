# Case study traces

The `*.events.csv` files are **not tracked in git** — they are deterministic outputs of `../generate_traces.py` from (recipe + primitives + seed), and they are 51–90MB each.

On the shared OSC node, the authoritative copies live in this directory. If you are a team member reading this README on GitHub: the trace files exist on disk at `/fs/ess/PAS2136/TheWilds2025/processing_output/experimental_resultsv2/exp6_3_case_studies/traces/` — point your scripts at them directly.

Per `manifest.json`:

| Case | Events | Modalities | SLO | Seed | Size |
|---|---|---|---|---|---|
| CS1 — CT→Drone | 799,314 | CT, drone | 5s | 1 | 90M |
| CS2 — Acoustic→CT | 491,964 | CT, bioacoustic | 2s | 2 | 51M |
| CS3 — Focal CT network | 527,673 | CT | 10s | 3 | 65M |
| CS4 — CitSci system | 709,018 | all four | 60s | 4 | 77M |

## Regenerate

```
module load python/3.12
cd /fs/ess/PAS2136/TheWilds2025/processing_output/experimental_resultsv2/exp6_3_case_studies
python generate_traces.py
```

Runs deterministically; reproduces the sizes and manifest counts above.
