from __future__ import annotations

from pathlib import Path
import pandas as pd

TRACE_INPUT = Path("outputs/tables/benchmark/trace_driven_multimodal_resource_table.csv")
BENCH_INPUT = Path("outputs/tables/benchmark/benchmark_summary.csv")
CAMERA_INPUT = Path("outputs/tables/arrivals/arrival_summary.csv")
AUDIO_INPUT = Path("outputs/tables/arrivals/audio_arrival_summary.csv")
DRONE_TRACE_INPUT = Path("outputs/tables/arrivals/drone_trace_campaign2.csv")
DRONE_ARRIVAL_INPUT = Path("outputs/tables/arrivals/drone_arrival_summary.csv")

STRICT_TRACE_OUTPUT = Path("outputs/tables/benchmark/trace_driven_multimodal_resource_table_strict.csv")
STRICT_SUMMARY_OUTPUT = Path("outputs/tables/benchmark/exp3_summary_table_strict.csv")
STRICT_MODALITY_OUTPUT = Path("outputs/tables/benchmark/exp3_modality_table_strict.csv")


def util_percent(rate_per_hour: float, service_ms: float) -> float:
    return float(rate_per_hour) * float(service_ms) / 36000.0


def main() -> None:
    trace_df = pd.read_csv(TRACE_INPUT)
    bench_df = pd.read_csv(BENCH_INPUT)
    cam_df = pd.read_csv(CAMERA_INPUT)
    audio_df = pd.read_csv(AUDIO_INPUT)
    drone_trace_df = pd.read_csv(DRONE_TRACE_INPUT)
    drone_arrival_df = pd.read_csv(DRONE_ARRIVAL_INPUT)

    # ---- derive drone service time from observed weak trace ----
    drone_nonzero = drone_trace_df[drone_trace_df["video_count"] > 0].copy()
    if len(drone_nonzero) > 0:
        drone_service_ms = float((drone_nonzero["service_seconds"] * 1000.0).mean())
    else:
        drone_service_ms = 0.0

    drone_avg_rate = float(drone_arrival_df.iloc[0]["avg_rate_per_hour"])
    drone_busy_rate = float(drone_arrival_df.iloc[0]["p95_rate_per_hour"])
    drone_worst_rate = float(drone_arrival_df.iloc[0]["peak_rate_per_hour"])

    scenario_to_drone_rate = {
        "nominal": drone_avg_rate,
        "busy": drone_busy_rate,
        "worst_case": drone_worst_rate,
    }

    # ---- strict trace-driven policy table ----
    strict_rows = []
    for _, row in trace_df.iterrows():
        scenario = str(row["scenario"])
        drone_rate = scenario_to_drone_rate.get(scenario, drone_avg_rate)
        drone_cpu_util = util_percent(drone_rate, drone_service_ms)

        aggregate_strict = float(row["aggregate_util_percent"]) + drone_cpu_util

        strict_rows.append({
            **row.to_dict(),
            "drone_rate_per_hour": drone_rate,
            "drone_service_ms": drone_service_ms,
            "drone_cpu_util_percent": drone_cpu_util,
            "aggregate_util_percent_strict": aggregate_strict,
            "single_node_feasibility_strict": "safe" if aggregate_strict < 100.0 else "unsafe",
        })

    strict_trace_df = pd.DataFrame(strict_rows)
    STRICT_TRACE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    strict_trace_df.to_csv(STRICT_TRACE_OUTPUT, index=False)

    # ---- strict summary table ----
    summary = strict_trace_df[[
        "scenario",
        "policy",
        "camera_rate_per_hour",
        "audio_rate_per_hour",
        "drone_rate_per_hour",
        "cpu_util_percent",
        "gpu_util_percent",
        "drone_cpu_util_percent",
        "aggregate_util_percent_strict",
        "single_node_feasibility_strict",
    ]].copy()

    summary = summary.rename(columns={
        "aggregate_util_percent_strict": "aggregate_util_percent",
        "single_node_feasibility_strict": "single_node_feasibility",
    })
    summary.to_csv(STRICT_SUMMARY_OUTPUT, index=False)

    # ---- modality-level strict table ----
    # camera aggregate from site-level arrival summary
    camera_avg_rate = float(cam_df["avg_rate_per_hour"].mean())
    camera_p95_rate = float(cam_df["avg_rate_per_hour"].quantile(0.95))
    camera_peak_rate = float(cam_df["avg_rate_per_hour"].max())

    # audio aggregate from site-level arrival summary
    audio_avg_rate = float(audio_df["avg_rate_per_hour"].sum())
    audio_p95_rate = float(audio_df["p95_rate_per_hour"].sum())
    audio_peak_rate = float(audio_df["peak_rate_per_hour"].sum())

    # benchmark latencies
    birdnet_ms = float(
        bench_df.loc[bench_df["model"].astype(str).str.lower() == "birdnet", "mean_latency_ms"].iloc[0]
    )
    yolo_ms = float(
        bench_df.loc[bench_df["model"].astype(str).str.lower() == "yolo", "mean_latency_ms"].iloc[0]
    )
    bioclip_ms = float(
        bench_df.loc[bench_df["model"].astype(str).str.lower() == "bioclip", "mean_latency_ms"].iloc[0]
    )

    modality_rows = [
        {
            "modality": "camera_traps",
            "modeling_assumption": "YOLO detection only, per image event",
            "reference_model": "YOLO",
            "reference_latency_ms": yolo_ms,
            "avg_rate_per_hour": camera_avg_rate,
            "p95_rate_per_hour": camera_p95_rate,
            "peak_rate_per_hour": camera_peak_rate,
            "required_util_avg_percent": util_percent(camera_avg_rate, yolo_ms),
            "required_util_p95_percent": util_percent(camera_p95_rate, yolo_ms),
            "required_util_peak_percent": util_percent(camera_peak_rate, yolo_ms),
            "single_node_feasibility_peak": "safe" if util_percent(camera_peak_rate, yolo_ms) < 100.0 else "unsafe",
        },
        {
            "modality": "bioacoustics",
            "modeling_assumption": "BirdNET per audio clip",
            "reference_model": "BirdNET",
            "reference_latency_ms": birdnet_ms,
            "avg_rate_per_hour": audio_avg_rate,
            "p95_rate_per_hour": audio_p95_rate,
            "peak_rate_per_hour": audio_peak_rate,
            "required_util_avg_percent": util_percent(audio_avg_rate, birdnet_ms),
            "required_util_p95_percent": util_percent(audio_p95_rate, birdnet_ms),
            "required_util_peak_percent": util_percent(audio_peak_rate, birdnet_ms),
            "single_node_feasibility_peak": "safe" if util_percent(audio_peak_rate, birdnet_ms) < 100.0 else "unsafe",
        },
        {
            "modality": "drone",
            "modeling_assumption": "Session-level drone event using observed weak replay service time",
            "reference_model": "drone_session_empirical",
            "reference_latency_ms": drone_service_ms,
            "avg_rate_per_hour": drone_avg_rate,
            "p95_rate_per_hour": drone_busy_rate,
            "peak_rate_per_hour": drone_worst_rate,
            "required_util_avg_percent": util_percent(drone_avg_rate, drone_service_ms),
            "required_util_p95_percent": util_percent(drone_busy_rate, drone_service_ms),
            "required_util_peak_percent": util_percent(drone_worst_rate, drone_service_ms),
            "single_node_feasibility_peak": "safe" if util_percent(drone_worst_rate, drone_service_ms) < 100.0 else "unsafe",
        },
        {
            "modality": "camera_classification_reference",
            "modeling_assumption": "BioCLIP reference for secondary image classification",
            "reference_model": "BioCLIP",
            "reference_latency_ms": bioclip_ms,
            "avg_rate_per_hour": camera_avg_rate,
            "p95_rate_per_hour": camera_p95_rate,
            "peak_rate_per_hour": camera_peak_rate,
            "required_util_avg_percent": util_percent(camera_avg_rate, bioclip_ms),
            "required_util_p95_percent": util_percent(camera_p95_rate, bioclip_ms),
            "required_util_peak_percent": util_percent(camera_peak_rate, bioclip_ms),
            "single_node_feasibility_peak": "safe" if util_percent(camera_peak_rate, bioclip_ms) < 100.0 else "unsafe",
        },
    ]

    modality_df = pd.DataFrame(modality_rows)
    modality_df.to_csv(STRICT_MODALITY_OUTPUT, index=False)

    print(f"Saved strict trace-driven table: {STRICT_TRACE_OUTPUT}")
    print(f"Saved strict summary table: {STRICT_SUMMARY_OUTPUT}")
    print(f"Saved strict modality table: {STRICT_MODALITY_OUTPUT}")
    print()
    print(strict_trace_df.to_string(index=False))
    print()
    print(modality_df.to_string(index=False))


if __name__ == "__main__":
    main()
