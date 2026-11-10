# Predicted Feasibility Grid Summary

This report explains why each Exp 3.2 grid cell received its feasibility verdict. It is generated from `predicted_feasibility_grid.csv`.

## Verdict Rules

- `feasible`: aggregate utilization is below 70% and predicted p95 latency is within the case-study SLO.
- `degraded`: aggregate utilization is below 100% and predicted p95 latency is within 1.25x the SLO, but the cell is not comfortably feasible.
- `infeasible`: utilization saturates, latency exceeds the degraded tolerance band, or the tier has an unsupported required model.

## Overall Counts

- `feasible`: 40
- `degraded`: 1
- `infeasible`: 39

## Compact Verdict Matrix

|                             | process_all   | event_triggered   | adaptive   | control_theoretic   |
|:----------------------------|:--------------|:------------------|:-----------|:--------------------|
| ('CS1', 'field_laptop')     | feasible      | feasible          | feasible   | feasible            |
| ('CS1', 'jetson_orin_nano') | feasible      | feasible          | feasible   | feasible            |
| ('CS1', 'pi4_cpu')          | infeasible    | infeasible        | infeasible | infeasible          |
| ('CS1', 'pi5_coral')        | infeasible    | infeasible        | infeasible | infeasible          |
| ('CS1', 'workstation_rtx')  | feasible      | feasible          | feasible   | feasible            |
| ('CS2', 'field_laptop')     | feasible      | feasible          | feasible   | feasible            |
| ('CS2', 'jetson_orin_nano') | infeasible    | feasible          | infeasible | infeasible          |
| ('CS2', 'pi4_cpu')          | infeasible    | infeasible        | infeasible | infeasible          |
| ('CS2', 'pi5_coral')        | infeasible    | infeasible        | infeasible | infeasible          |
| ('CS2', 'workstation_rtx')  | feasible      | feasible          | feasible   | feasible            |
| ('CS3', 'field_laptop')     | feasible      | feasible          | feasible   | feasible            |
| ('CS3', 'jetson_orin_nano') | feasible      | feasible          | feasible   | feasible            |
| ('CS3', 'pi4_cpu')          | infeasible    | infeasible        | infeasible | infeasible          |
| ('CS3', 'pi5_coral')        | infeasible    | infeasible        | infeasible | infeasible          |
| ('CS3', 'workstation_rtx')  | feasible      | feasible          | feasible   | feasible            |
| ('CS4', 'field_laptop')     | feasible      | feasible          | feasible   | infeasible          |
| ('CS4', 'jetson_orin_nano') | infeasible    | infeasible        | infeasible | infeasible          |
| ('CS4', 'pi4_cpu')          | infeasible    | feasible          | degraded   | infeasible          |
| ('CS4', 'pi5_coral')        | infeasible    | infeasible        | infeasible | infeasible          |
| ('CS4', 'workstation_rtx')  | feasible      | feasible          | feasible   | infeasible          |

## Cell-by-cell Explanation

### CS1: `CS1_ct_to_drone`

SLO target: 5,000.0 ms.

#### workstation_rtx

- **process_all** -> `feasible`
  - Utilization: 3.83%
  - P95 latency: 369.2 ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **feasible** because aggregate utilization is 3.83% (<70%) and predicted p95 latency is 369.2 ms, below the 5,000.0 ms SLO. The bottleneck is `drone:sam3`, but it still has enough headroom. Policy/model notes: policy_actions=process:477197,drop:0,defer:0; camera_trap:megadetector:rate=766.75/h,util=1.21%; drone:sam3:rate=787.25/h,util=2.62%.

- **event_triggered** -> `feasible`
  - Utilization: 2.56%
  - P95 latency: 368.9 ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **feasible** because aggregate utilization is 2.56% (<70%) and predicted p95 latency is 368.9 ms, below the 5,000.0 ms SLO. The bottleneck is `drone:sam3`, but it still has enough headroom. Policy/model notes: policy_actions=process:189556,drop:287641,defer:0; drone:sam3:rate=766.75/h,util=2.56%.

- **adaptive** -> `feasible`
  - Utilization: 2.98%
  - P95 latency: 365.9 ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **feasible** because aggregate utilization is 2.98% (<70%) and predicted p95 latency is 365.9 ms, below the 5,000.0 ms SLO. The bottleneck is `drone:sam3`, but it still has enough headroom. Policy/model notes: policy_actions=process:192055,drop:0,defer:285142; camera_trap:megadetector:rate=766.75/h,util=1.21%; drone:sam3:rate=529.70/h,util=1.77%.

- **control_theoretic** -> `feasible`
  - Utilization: 2.34%
  - P95 latency: 363.6 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 2.34% (<70%) and predicted p95 latency is 363.6 ms, below the 5,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:360150,drop:1,defer:117046; camera_trap:megadetector:rate=766.75/h,util=1.21%; drone:sam3:rate=339.00/h,util=1.13%.

#### jetson_orin_nano

- **process_all** -> `feasible`
  - Utilization: 21.39%
  - P95 latency: 3,356.8 ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **feasible** because aggregate utilization is 21.39% (<70%) and predicted p95 latency is 3,356.8 ms, below the 5,000.0 ms SLO. The bottleneck is `drone:sam3`, but it still has enough headroom. Policy/model notes: policy_actions=process:477197,drop:0,defer:0; camera_trap:megadetector:rate=766.75/h,util=1.70%; drone:sam3:rate=787.25/h,util=19.68%.

- **event_triggered** -> `feasible`
  - Utilization: 19.17%
  - P95 latency: 3,335.5 ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **feasible** because aggregate utilization is 19.17% (<70%) and predicted p95 latency is 3,335.5 ms, below the 5,000.0 ms SLO. The bottleneck is `drone:sam3`, but it still has enough headroom. Policy/model notes: policy_actions=process:189556,drop:287641,defer:0; drone:sam3:rate=766.75/h,util=19.17%.

- **adaptive** -> `feasible`
  - Utilization: 14.95%
  - P95 latency: 3,107.7 ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **feasible** because aggregate utilization is 14.95% (<70%) and predicted p95 latency is 3,107.7 ms, below the 5,000.0 ms SLO. The bottleneck is `drone:sam3`, but it still has enough headroom. Policy/model notes: policy_actions=process:192055,drop:0,defer:285142; camera_trap:megadetector:rate=766.75/h,util=1.70%; drone:sam3:rate=529.70/h,util=13.24%.

- **control_theoretic** -> `feasible`
  - Utilization: 10.18%
  - P95 latency: 2,945.8 ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **feasible** because aggregate utilization is 10.18% (<70%) and predicted p95 latency is 2,945.8 ms, below the 5,000.0 ms SLO. The bottleneck is `drone:sam3`, but it still has enough headroom. Policy/model notes: policy_actions=process:360150,drop:1,defer:117046; camera_trap:megadetector:rate=766.75/h,util=1.70%; drone:sam3:rate=339.00/h,util=8.47%.

#### pi5_coral

- **process_all** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector+drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector+drone:sam3`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:477197,drop:0,defer:0; unsupported=camera_trap:megadetector,drone:sam3.

- **event_triggered** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `drone:sam3`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:189556,drop:287641,defer:0; unsupported=drone:sam3.

- **adaptive** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector+drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector+drone:sam3`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:192055,drop:0,defer:285142; unsupported=camera_trap:megadetector,drone:sam3.

- **control_theoretic** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector+drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector+drone:sam3`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:360150,drop:1,defer:117046; unsupported=camera_trap:megadetector,drone:sam3.

#### pi4_cpu

- **process_all** -> `infeasible`
  - Utilization: 63.90%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `drone:sam3`. The numeric utilization (63.90%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:477197,drop:0,defer:0; camera_trap:megadetector:rate=766.75/h,util=63.90%; unsupported=drone:sam3.

- **event_triggered** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `drone:sam3`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:189556,drop:287641,defer:0; unsupported=drone:sam3.

- **adaptive** -> `infeasible`
  - Utilization: 63.90%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `drone:sam3`. The numeric utilization (63.90%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:192055,drop:0,defer:285142; camera_trap:megadetector:rate=766.75/h,util=63.90%; unsupported=drone:sam3.

- **control_theoretic** -> `infeasible`
  - Utilization: 63.90%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `drone:sam3`. The numeric utilization (63.90%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:360150,drop:1,defer:117046; camera_trap:megadetector:rate=766.75/h,util=63.90%; unsupported=drone:sam3.

#### field_laptop

- **process_all** -> `feasible`
  - Utilization: 14.75%
  - P95 latency: 1,135.4 ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **feasible** because aggregate utilization is 14.75% (<70%) and predicted p95 latency is 1,135.4 ms, below the 5,000.0 ms SLO. The bottleneck is `drone:sam3`, but it still has enough headroom. Policy/model notes: policy_actions=process:477197,drop:0,defer:0; camera_trap:megadetector:rate=766.75/h,util=7.09%; drone:sam3:rate=787.25/h,util=7.65%.

- **event_triggered** -> `feasible`
  - Utilization: 7.46%
  - P95 latency: 1,133.0 ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **feasible** because aggregate utilization is 7.46% (<70%) and predicted p95 latency is 1,133.0 ms, below the 5,000.0 ms SLO. The bottleneck is `drone:sam3`, but it still has enough headroom. Policy/model notes: policy_actions=process:189556,drop:287641,defer:0; drone:sam3:rate=766.75/h,util=7.45%.

- **adaptive** -> `feasible`
  - Utilization: 12.24%
  - P95 latency: 1,105.4 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 12.24% (<70%) and predicted p95 latency is 1,105.4 ms, below the 5,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:192055,drop:0,defer:285142; camera_trap:megadetector:rate=766.75/h,util=7.09%; drone:sam3:rate=529.70/h,util=5.15%.

- **control_theoretic** -> `feasible`
  - Utilization: 10.39%
  - P95 latency: 1,084.2 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 10.39% (<70%) and predicted p95 latency is 1,084.2 ms, below the 5,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:360150,drop:1,defer:117046; camera_trap:megadetector:rate=766.75/h,util=7.09%; drone:sam3:rate=339.00/h,util=3.30%.

### CS2: `CS2_acoustic_to_ct`

SLO target: 2,000.0 ms.

#### workstation_rtx

- **process_all** -> `feasible`
  - Utilization: 2.52%
  - P95 latency: 174.6 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 2.52% (<70%) and predicted p95 latency is 174.6 ms, below the 2,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:383814,drop:0,defer:0; bioacoustic:birdnet:rate=8.00/h,util=0.00%; camera_trap:megadetector:rate=1596.55/h,util=2.52%.

- **event_triggered** -> `feasible`
  - Utilization: 0.11%
  - P95 latency: 170.4 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 0.11% (<70%) and predicted p95 latency is 170.4 ms, below the 2,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:2024,drop:381790,defer:0; camera_trap:megadetector:rate=72.00/h,util=0.11%.

- **adaptive** -> `feasible`
  - Utilization: 2.44%
  - P95 latency: 174.4 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 2.44% (<70%) and predicted p95 latency is 174.4 ms, below the 2,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:381911,drop:0,defer:1903; bioacoustic:birdnet:rate=8.00/h,util=0.00%; camera_trap:megadetector:rate=1546.15/h,util=2.44%.

- **control_theoretic** -> `feasible`
  - Utilization: 2.44%
  - P95 latency: 174.4 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 2.44% (<70%) and predicted p95 latency is 174.4 ms, below the 2,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:381790,drop:387,defer:1637; bioacoustic:birdnet:rate=8.00/h,util=0.00%; camera_trap:megadetector:rate=1546.15/h,util=2.44%.

#### jetson_orin_nano

- **process_all** -> `infeasible`
  - Utilization: 3.55%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:bioacoustic:birdnet`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `bioacoustic:birdnet`. The numeric utilization (3.55%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:383814,drop:0,defer:0; camera_trap:megadetector:rate=1596.55/h,util=3.55%; unsupported=bioacoustic:birdnet.

- **event_triggered** -> `feasible`
  - Utilization: 0.16%
  - P95 latency: 240.0 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 0.16% (<70%) and predicted p95 latency is 240.0 ms, below the 2,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:2024,drop:381790,defer:0; camera_trap:megadetector:rate=72.00/h,util=0.16%.

- **adaptive** -> `infeasible`
  - Utilization: 3.44%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:bioacoustic:birdnet`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `bioacoustic:birdnet`. The numeric utilization (3.44%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:381911,drop:0,defer:1903; camera_trap:megadetector:rate=1546.15/h,util=3.44%; unsupported=bioacoustic:birdnet.

- **control_theoretic** -> `infeasible`
  - Utilization: 3.44%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:bioacoustic:birdnet`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `bioacoustic:birdnet`. The numeric utilization (3.44%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:381790,drop:387,defer:1637; camera_trap:megadetector:rate=1546.15/h,util=3.44%; unsupported=bioacoustic:birdnet.

#### pi5_coral

- **process_all** -> `infeasible`
  - Utilization: 0.02%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector`. The numeric utilization (0.02%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:383814,drop:0,defer:0; bioacoustic:birdnet:rate=8.00/h,util=0.02%; unsupported=camera_trap:megadetector.

- **event_triggered** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:2024,drop:381790,defer:0; unsupported=camera_trap:megadetector.

- **adaptive** -> `infeasible`
  - Utilization: 0.02%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector`. The numeric utilization (0.02%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:381911,drop:0,defer:1903; bioacoustic:birdnet:rate=8.00/h,util=0.02%; unsupported=camera_trap:megadetector.

- **control_theoretic** -> `infeasible`
  - Utilization: 0.02%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector`. The numeric utilization (0.02%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:381790,drop:387,defer:1637; bioacoustic:birdnet:rate=8.00/h,util=0.02%; unsupported=camera_trap:megadetector.

#### pi4_cpu

- **process_all** -> `infeasible`
  - Utilization: 133.08%
  - P95 latency: inf ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because queue utilization reaches or exceeds saturation for bottleneck `camera_trap:megadetector`. Aggregate utilization is 133.08%, and predicted p95 latency is `inf` against an SLO of 2,000.0 ms. Policy/model notes: policy_actions=process:383814,drop:0,defer:0; bioacoustic:birdnet:rate=8.00/h,util=0.04%; camera_trap:megadetector:rate=1596.55/h,util=133.05%.

- **event_triggered** -> `infeasible`
  - Utilization: 6.00%
  - P95 latency: 9,560.8 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because either utilization is too high or p95 latency misses the degraded tolerance band. Aggregate utilization is 6.00%, predicted p95 latency is 9,560.8 ms, SLO is 2,000.0 ms, and bottleneck is `camera_trap:megadetector`. Policy/model notes: policy_actions=process:2024,drop:381790,defer:0; camera_trap:megadetector:rate=72.00/h,util=6.00%.

- **adaptive** -> `infeasible`
  - Utilization: 128.88%
  - P95 latency: inf ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because queue utilization reaches or exceeds saturation for bottleneck `camera_trap:megadetector`. Aggregate utilization is 128.88%, and predicted p95 latency is `inf` against an SLO of 2,000.0 ms. Policy/model notes: policy_actions=process:381911,drop:0,defer:1903; bioacoustic:birdnet:rate=8.00/h,util=0.04%; camera_trap:megadetector:rate=1546.15/h,util=128.85%.

- **control_theoretic** -> `infeasible`
  - Utilization: 128.88%
  - P95 latency: inf ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because queue utilization reaches or exceeds saturation for bottleneck `camera_trap:megadetector`. Aggregate utilization is 128.88%, and predicted p95 latency is `inf` against an SLO of 2,000.0 ms. Policy/model notes: policy_actions=process:381790,drop:387,defer:1637; bioacoustic:birdnet:rate=8.00/h,util=0.04%; camera_trap:megadetector:rate=1546.15/h,util=128.85%.

#### field_laptop

- **process_all** -> `feasible`
  - Utilization: 14.78%
  - P95 latency: 1,170.4 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 14.78% (<70%) and predicted p95 latency is 1,170.4 ms, below the 2,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:383814,drop:0,defer:0; bioacoustic:birdnet:rate=8.00/h,util=0.01%; camera_trap:megadetector:rate=1596.55/h,util=14.77%.

- **event_triggered** -> `feasible`
  - Utilization: 0.67%
  - P95 latency: 1,004.3 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 0.67% (<70%) and predicted p95 latency is 1,004.3 ms, below the 2,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:2024,drop:381790,defer:0; camera_trap:megadetector:rate=72.00/h,util=0.67%.

- **adaptive** -> `feasible`
  - Utilization: 14.31%
  - P95 latency: 1,164.1 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 14.31% (<70%) and predicted p95 latency is 1,164.1 ms, below the 2,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:381911,drop:0,defer:1903; bioacoustic:birdnet:rate=8.00/h,util=0.01%; camera_trap:megadetector:rate=1546.15/h,util=14.30%.

- **control_theoretic** -> `feasible`
  - Utilization: 14.31%
  - P95 latency: 1,164.1 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 14.31% (<70%) and predicted p95 latency is 1,164.1 ms, below the 2,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:381790,drop:387,defer:1637; bioacoustic:birdnet:rate=8.00/h,util=0.01%; camera_trap:megadetector:rate=1546.15/h,util=14.30%.

### CS3: `CS3_focal_ct_network`

SLO target: 10,000.0 ms.

#### workstation_rtx

- **process_all** -> `feasible`
  - Utilization: 2.70%
  - P95 latency: 174.9 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 2.70% (<70%) and predicted p95 latency is 174.9 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:425477,drop:0,defer:0; camera_trap:megadetector:rate=1709.65/h,util=2.70%.

- **event_triggered** -> `feasible`
  - Utilization: 0.92%
  - P95 latency: 171.7 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 0.92% (<70%) and predicted p95 latency is 171.7 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:141826,drop:283651,defer:0; camera_trap:megadetector:rate=580.20/h,util=0.92%.

- **adaptive** -> `feasible`
  - Utilization: 1.81%
  - P95 latency: 173.3 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 1.81% (<70%) and predicted p95 latency is 173.3 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:285267,drop:0,defer:140210; camera_trap:megadetector:rate=1148.85/h,util=1.81%.

- **control_theoretic** -> `feasible`
  - Utilization: 1.81%
  - P95 latency: 173.3 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 1.81% (<70%) and predicted p95 latency is 173.3 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:283651,drop:21277,defer:120549; camera_trap:megadetector:rate=1145.80/h,util=1.81%.

#### jetson_orin_nano

- **process_all** -> `feasible`
  - Utilization: 3.80%
  - P95 latency: 249.1 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 3.80% (<70%) and predicted p95 latency is 249.1 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:425477,drop:0,defer:0; camera_trap:megadetector:rate=1709.65/h,util=3.80%.

- **event_triggered** -> `feasible`
  - Utilization: 1.29%
  - P95 latency: 242.8 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 1.29% (<70%) and predicted p95 latency is 242.8 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:141826,drop:283651,defer:0; camera_trap:megadetector:rate=580.20/h,util=1.29%.

- **adaptive** -> `feasible`
  - Utilization: 2.55%
  - P95 latency: 245.9 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 2.55% (<70%) and predicted p95 latency is 245.9 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:285267,drop:0,defer:140210; camera_trap:megadetector:rate=1148.85/h,util=2.55%.

- **control_theoretic** -> `feasible`
  - Utilization: 2.55%
  - P95 latency: 245.9 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 2.55% (<70%) and predicted p95 latency is 245.9 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:283651,drop:21277,defer:120549; camera_trap:megadetector:rate=1145.80/h,util=2.55%.

#### pi5_coral

- **process_all** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:425477,drop:0,defer:0; unsupported=camera_trap:megadetector.

- **event_triggered** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:141826,drop:283651,defer:0; unsupported=camera_trap:megadetector.

- **adaptive** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:285267,drop:0,defer:140210; unsupported=camera_trap:megadetector.

- **control_theoretic** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:283651,drop:21277,defer:120549; unsupported=camera_trap:megadetector.

#### pi4_cpu

- **process_all** -> `infeasible`
  - Utilization: 142.47%
  - P95 latency: inf ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because queue utilization reaches or exceeds saturation for bottleneck `camera_trap:megadetector`. Aggregate utilization is 142.47%, and predicted p95 latency is `inf` against an SLO of 10,000.0 ms. Policy/model notes: policy_actions=process:425477,drop:0,defer:0; camera_trap:megadetector:rate=1709.65/h,util=142.47%.

- **event_triggered** -> `infeasible`
  - Utilization: 48.35%
  - P95 latency: 17,400.2 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because either utilization is too high or p95 latency misses the degraded tolerance band. Aggregate utilization is 48.35%, predicted p95 latency is 17,400.2 ms, SLO is 10,000.0 ms, and bottleneck is `camera_trap:megadetector`. Policy/model notes: policy_actions=process:141826,drop:283651,defer:0; camera_trap:megadetector:rate=580.20/h,util=48.35%.

- **adaptive** -> `infeasible`
  - Utilization: 95.74%
  - P95 latency: 210,843.3 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because either utilization is too high or p95 latency misses the degraded tolerance band. Aggregate utilization is 95.74%, predicted p95 latency is 210,843.3 ms, SLO is 10,000.0 ms, and bottleneck is `camera_trap:megadetector`. Policy/model notes: policy_actions=process:285267,drop:0,defer:140210; camera_trap:megadetector:rate=1148.85/h,util=95.74%.

- **control_theoretic** -> `infeasible`
  - Utilization: 95.48%
  - P95 latency: 198,978.5 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because either utilization is too high or p95 latency misses the degraded tolerance band. Aggregate utilization is 95.48%, predicted p95 latency is 198,978.5 ms, SLO is 10,000.0 ms, and bottleneck is `camera_trap:megadetector`. Policy/model notes: policy_actions=process:283651,drop:21277,defer:120549; camera_trap:megadetector:rate=1145.80/h,util=95.48%.

#### field_laptop

- **process_all** -> `feasible`
  - Utilization: 15.81%
  - P95 latency: 1,185.0 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 15.81% (<70%) and predicted p95 latency is 1,185.0 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:425477,drop:0,defer:0; camera_trap:megadetector:rate=1709.65/h,util=15.81%.

- **event_triggered** -> `feasible`
  - Utilization: 5.37%
  - P95 latency: 1,054.2 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 5.37% (<70%) and predicted p95 latency is 1,054.2 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:141826,drop:283651,defer:0; camera_trap:megadetector:rate=580.20/h,util=5.37%.

- **adaptive** -> `feasible`
  - Utilization: 10.63%
  - P95 latency: 1,116.2 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 10.63% (<70%) and predicted p95 latency is 1,116.2 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:285267,drop:0,defer:140210; camera_trap:megadetector:rate=1148.85/h,util=10.63%.

- **control_theoretic** -> `feasible`
  - Utilization: 10.60%
  - P95 latency: 1,115.8 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 10.60% (<70%) and predicted p95 latency is 1,115.8 ms, below the 10,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:283651,drop:21277,defer:120549; camera_trap:megadetector:rate=1145.80/h,util=10.60%.

### CS4: `CS4_citsci_system`

SLO target: 60,000.0 ms.

#### workstation_rtx

- **process_all** -> `feasible`
  - Utilization: 1.61%
  - P95 latency: 359.5 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 1.61% (<70%) and predicted p95 latency is 359.5 ms, below the 60,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:364049,drop:0,defer:0; bioacoustic:birdnet:rate=9.00/h,util=0.00%; camera_trap:megadetector:rate=972.70/h,util=1.53%; citizen_science:bioclip:rate=118.00/h,util=0.06%; drone:sam3:rate=2.80/h,util=0.01%.

- **event_triggered** -> `feasible`
  - Utilization: 0.22%
  - P95 latency: 170.5 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 0.22% (<70%) and predicted p95 latency is 170.5 ms, below the 60,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:540,drop:363509,defer:0; bioacoustic:birdnet:rate=1.75/h,util=0.00%; camera_trap:megadetector:rate=137.00/h,util=0.22%.

- **adaptive** -> `feasible`
  - Utilization: 1.54%
  - P95 latency: 172.8 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 1.54% (<70%) and predicted p95 latency is 172.8 ms, below the 60,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:239691,drop:0,defer:124358; bioacoustic:birdnet:rate=9.00/h,util=0.00%; camera_trap:megadetector:rate=961.90/h,util=1.52%; citizen_science:bioclip:rate=30.00/h,util=0.02%.

- **control_theoretic** -> `infeasible`
  - Utilization: 179.66%
  - P95 latency: inf ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **infeasible** because queue utilization reaches or exceeds saturation for bottleneck `drone:sam3`. Aggregate utilization is 179.66%, and predicted p95 latency is `inf` against an SLO of 60,000.0 ms. Policy/model notes: policy_actions=process:362062,drop:427,defer:1560; bioacoustic:birdnet:rate=9.00/h,util=0.00%; camera_trap:megadetector:rate=961.90/h,util=1.52%; drone:sam3:rate=53440.40/h,util=178.13%.

#### jetson_orin_nano

- **process_all** -> `infeasible`
  - Utilization: 2.62%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:bioacoustic:birdnet`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `bioacoustic:birdnet`. The numeric utilization (2.62%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:364049,drop:0,defer:0; camera_trap:megadetector:rate=972.70/h,util=2.16%; citizen_science:bioclip:rate=118.00/h,util=0.39%; drone:sam3:rate=2.80/h,util=0.07%; unsupported=bioacoustic:birdnet.

- **event_triggered** -> `infeasible`
  - Utilization: 0.30%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:bioacoustic:birdnet`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `bioacoustic:birdnet`. The numeric utilization (0.30%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:540,drop:363509,defer:0; camera_trap:megadetector:rate=137.00/h,util=0.30%; unsupported=bioacoustic:birdnet.

- **adaptive** -> `infeasible`
  - Utilization: 2.24%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:bioacoustic:birdnet`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `bioacoustic:birdnet`. The numeric utilization (2.24%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:239691,drop:0,defer:124358; camera_trap:megadetector:rate=961.90/h,util=2.14%; citizen_science:bioclip:rate=30.00/h,util=0.10%; unsupported=bioacoustic:birdnet.

- **control_theoretic** -> `infeasible`
  - Utilization: 1338.15%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:bioacoustic:birdnet`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `bioacoustic:birdnet`. The numeric utilization (1338.15%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:362062,drop:427,defer:1560; camera_trap:megadetector:rate=961.90/h,util=2.14%; drone:sam3:rate=53440.40/h,util=1336.01%; unsupported=bioacoustic:birdnet.

#### pi5_coral

- **process_all** -> `infeasible`
  - Utilization: 0.02%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector+citizen_science:bioclip+drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector+citizen_science:bioclip+drone:sam3`. The numeric utilization (0.02%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:364049,drop:0,defer:0; bioacoustic:birdnet:rate=9.00/h,util=0.02%; unsupported=camera_trap:megadetector,citizen_science:bioclip,drone:sam3.

- **event_triggered** -> `infeasible`
  - Utilization: 0.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector`. The numeric utilization (0.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:540,drop:363509,defer:0; bioacoustic:birdnet:rate=1.75/h,util=0.00%; unsupported=camera_trap:megadetector.

- **adaptive** -> `infeasible`
  - Utilization: 0.02%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector+citizen_science:bioclip`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector+citizen_science:bioclip`. The numeric utilization (0.02%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:239691,drop:0,defer:124358; bioacoustic:birdnet:rate=9.00/h,util=0.02%; unsupported=camera_trap:megadetector,citizen_science:bioclip.

- **control_theoretic** -> `infeasible`
  - Utilization: 0.02%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:camera_trap:megadetector+drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `camera_trap:megadetector+drone:sam3`. The numeric utilization (0.02%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:362062,drop:427,defer:1560; bioacoustic:birdnet:rate=9.00/h,util=0.02%; unsupported=camera_trap:megadetector,drone:sam3.

#### pi4_cpu

- **process_all** -> `infeasible`
  - Utilization: 87.00%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `drone:sam3`. The numeric utilization (87.00%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:364049,drop:0,defer:0; bioacoustic:birdnet:rate=9.00/h,util=0.04%; camera_trap:megadetector:rate=972.70/h,util=81.06%; citizen_science:bioclip:rate=118.00/h,util=5.90%; unsupported=drone:sam3.

- **event_triggered** -> `feasible`
  - Utilization: 11.43%
  - P95 latency: 10,145.5 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 11.43% (<70%) and predicted p95 latency is 10,145.5 ms, below the 60,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:540,drop:363509,defer:0; bioacoustic:birdnet:rate=1.75/h,util=0.01%; camera_trap:megadetector:rate=137.00/h,util=11.42%.

- **adaptive** -> `degraded`
  - Utilization: 81.70%
  - P95 latency: 45,294.6 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **degraded** because the cell is below hard saturation (81.70% <100%) and p95 latency is 45,294.6 ms, within 1.25x the 60,000.0 ms SLO, but it is not comfortably feasible. The bottleneck is `camera_trap:megadetector`. Policy/model notes: policy_actions=process:239691,drop:0,defer:124358; bioacoustic:birdnet:rate=9.00/h,util=0.04%; camera_trap:megadetector:rate=961.90/h,util=80.16%; citizen_science:bioclip:rate=30.00/h,util=1.50%.

- **control_theoretic** -> `infeasible`
  - Utilization: 80.20%
  - P95 latency: inf ms
  - Bottleneck: `unsupported:drone:sam3`
  - Explanation: Assigned **infeasible** because the workload requires unsupported model-tier pair(s): `drone:sam3`. The numeric utilization (80.20%) only reflects supported processed stages; p95 is set to `inf` because one or more required stages have no defensible latency for this tier. Policy/model notes: policy_actions=process:362062,drop:427,defer:1560; bioacoustic:birdnet:rate=9.00/h,util=0.04%; camera_trap:megadetector:rate=961.90/h,util=80.16%; unsupported=drone:sam3.

#### field_laptop

- **process_all** -> `feasible`
  - Utilization: 9.21%
  - P95 latency: 1,096.2 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 9.21% (<70%) and predicted p95 latency is 1,096.2 ms, below the 60,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:364049,drop:0,defer:0; bioacoustic:birdnet:rate=9.00/h,util=0.01%; camera_trap:megadetector:rate=972.70/h,util=9.00%; citizen_science:bioclip:rate=118.00/h,util=0.18%; drone:sam3:rate=2.80/h,util=0.03%.

- **event_triggered** -> `feasible`
  - Utilization: 1.27%
  - P95 latency: 1,010.4 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 1.27% (<70%) and predicted p95 latency is 1,010.4 ms, below the 60,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:540,drop:363509,defer:0; bioacoustic:birdnet:rate=1.75/h,util=0.00%; camera_trap:megadetector:rate=137.00/h,util=1.27%.

- **adaptive** -> `feasible`
  - Utilization: 8.95%
  - P95 latency: 1,095.0 ms
  - Bottleneck: `camera_trap:megadetector`
  - Explanation: Assigned **feasible** because aggregate utilization is 8.95% (<70%) and predicted p95 latency is 1,095.0 ms, below the 60,000.0 ms SLO. The bottleneck is `camera_trap:megadetector`, but it still has enough headroom. Policy/model notes: policy_actions=process:239691,drop:0,defer:124358; bioacoustic:birdnet:rate=9.00/h,util=0.01%; camera_trap:megadetector:rate=961.90/h,util=8.90%; citizen_science:bioclip:rate=30.00/h,util=0.05%.

- **control_theoretic** -> `infeasible`
  - Utilization: 528.47%
  - P95 latency: inf ms
  - Bottleneck: `drone:sam3`
  - Explanation: Assigned **infeasible** because queue utilization reaches or exceeds saturation for bottleneck `drone:sam3`. Aggregate utilization is 528.47%, and predicted p95 latency is `inf` against an SLO of 60,000.0 ms. Policy/model notes: policy_actions=process:362062,drop:427,defer:1560; bioacoustic:birdnet:rate=9.00/h,util=0.01%; camera_trap:megadetector:rate=961.90/h,util=8.90%; drone:sam3:rate=53440.40/h,util=519.56%.
