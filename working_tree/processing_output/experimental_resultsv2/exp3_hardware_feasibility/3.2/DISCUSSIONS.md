# Exp 3.2 Discussions

## Relationship To Exp 3.1

Exp 3.1 produces the benchmark table:

```text
../3.1/benchmark_table.py -> ../3.1/benchmark_table.csv
```

Exp 3.2 consumes that table. If a latency value changes in 3.1, rerun 3.2 so
the grid and heatmap reflect the new hardware-performance assumptions.

## Policy Integration

The current model uses Yuanyang's policy interface:

```python
get_policy(name).decide(event, state)
```

This replaced the earlier fixed process-fraction approximation. The grid now
depends on actual event-level policy decisions. The `modeling_notes` column
records action counts in this format:

```text
policy_actions=process:<n>,drop:<n>,defer:<n>
```

For Exp 3 prediction, only `process` events contribute immediate compute load.
`drop` events are removed. `defer` events are recorded as policy behavior but
are not modeled as delayed future compute in this first-order grid.

## Queueing Model

The model uses an M/M/1 response-time approximation:

```text
rho = arrival_rate_per_ms * service_ms
p95 = -ln(0.05) * service_ms / (1 - rho)
```

Arrival rate is the p95 hourly processed-event rate per modality after policy
filtering. The grid reports the worst p95 latency across modalities and the sum
of modality utilizations.

This is intentionally a prediction model, not a hardware measurement. Exp 3.5
is the measured field-laptop anchor.

## Unsupported Model-Tier Cells

`NaN` latency in `../3.1/benchmark_table.csv` means the model-tier combination
is unsupported or has no defensible benchmark. If a case study requires that
model on that tier, Exp 3.2 marks the cell:

```text
verdict = infeasible
bottleneck = unsupported:<modality>:<model>
```

This is why Coral and some Pi rows can be infeasible even when their numeric
utilization looks low: the required model is not assumed deployable there.

## Interpreting Degraded

`degraded` means the cell is not comfortably feasible but is not a hard failure:

```text
utilization < 100%
and p95_latency <= 1.25 * SLO
and not already feasible
```

Typical causes are utilization at or above 70%, or p95 latency slightly outside
the SLO but still within the degraded tolerance band.

## Current Caveats

- `defer` is not yet replayed as future work. It is counted but not placed back
  into a later queue.
- Policy state uses the fields provided by Yuanyang's Exp 4 policy scripts, but
  this is still an aggregate feasibility model rather than the full Exp 4 replay
  harness.
- Benchmark values are predicted/source-backed inputs. Some are direct
  benchmarks, while others are proxy or conservative planning values documented
  in `../3.1/model_benchmark_notes.md`.
- The heatmap intentionally keeps the README 3.3 layout: `case_study / policy`
  on the y-axis and hardware tier on the x-axis.

## Suggested Table V Language

Use language like:

```text
All Exp 3 hardware-tier values are predicted from source-backed benchmark
inputs. Unsupported model-tier combinations are treated conservatively as
infeasible. Field-laptop calibration is reported separately in Exp 3.5.
```
