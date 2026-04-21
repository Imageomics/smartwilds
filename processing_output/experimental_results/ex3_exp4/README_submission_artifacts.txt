Submission Artifacts for Experiments 3 and 4
===========================================

This folder contains the final organized outputs for Experiment 3 and Experiment 4.

==================================================
Experiment 3: Edge Resource Model (strict version)
==================================================

exp3/drone_arrival_summary.csv
- Campaign 2 drone arrival-rate summary used in the strict resource model.
- Includes total events, campaign duration, active days, and average / p95 / peak arrival rates.

exp3/trace_driven_multimodal_resource_table_strict.csv
- Full strict trace-driven resource model table.
- Combines scenario, policy, camera rate, audio rate, drone rate, CPU/GPU utilization,
  aggregate utilization, and feasibility results.

exp3/exp3_summary_table_strict.csv
- Compact summary table for Experiment 3.
- Main per-scenario/per-policy results used for reporting.

exp3/exp3_modality_table_strict.csv
- Modality-level resource model table.
- Shows the modeling assumption, reference model, latency, arrival rate, and utilization
  contribution for each modality (camera, bioacoustics, drone, camera-classification reference).

exp3/exp3_strict_aggregate_util.png
- Figure showing aggregate utilization under different scenarios and policies.
- Useful as the main Experiment 3 visualization.

=========================================================
Experiment 4: Replay-Based Policy Comparison (strict final)
=========================================================

exp4/replay_trace_exp4_strict_camera.csv
- Strict replay input trace for Experiment 4.
- Built from Campaign 2 camera events only.
- This is the final strict replay input used for the reported Experiment 4 results.

exp4/replay_results_exp4_strict.csv
- Full replay output for the strict Experiment 4 run.
- Contains per-event replay decisions and timing results for all evaluated policies.

exp4/replay_metrics_exp4_strict_raw.csv
- Raw policy-level metrics from the strict replay run.
- Includes all internal policy names before final renaming to the paper/presentation naming convention.

exp4/replay_metrics_exp4_strict.csv
- Final policy comparison metrics for strict Experiment 4.
- Policies are aligned to the final naming convention:
  baseline, event_triggered, adaptive.

exp4/exp4_summary_table_strict.csv
- Compact final summary table for Experiment 4.
- Contains the main reported metrics:
  coverage, p95 latency, compute cost, operator effort estimate, and SLO compliance.

exp4/replay_timeline_events.png
- Timeline figure showing hourly event counts during strict replay.

exp4/replay_timeline_latency.png
- Timeline figure showing hourly mean latency during strict replay.

exp4/replay_timeline_policy_state.png
- Timeline figure showing adaptive policy state over time during strict replay.

Notes
=====
- Experiment 3 strict includes camera, bioacoustics, and session-level drone integration.
- Experiment 4 strict is the final Campaign 2 camera-only replay result.
- Earlier weak or auxiliary replay outputs are not included here as primary submission artifacts.
