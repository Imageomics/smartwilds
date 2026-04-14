#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path


LATENCY_METRIC_CHOICES = (
    "per_image_total_p50_s",
    "per_image_total_p95_s",
    "per_image_sam3_p50_s",
    "per_image_sam3_p95_s",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert SAM3 benchmark summaries into edge-capacity tables.",
    )
    parser.add_argument(
        "--benchmark-summaries",
        nargs="+",
        required=True,
        help="One or more summary.json paths or glob patterns.",
    )
    parser.add_argument("--scenario-csv", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument(
        "--latency-metric",
        choices=LATENCY_METRIC_CHOICES,
        default="per_image_total_p95_s",
    )
    return parser.parse_args()


def _expand_paths(patterns: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for pattern in patterns:
        matches = [Path(match) for match in glob.glob(pattern)]
        if matches:
            expanded.extend(matches)
        else:
            expanded.append(Path(pattern))
    deduplicated = []
    seen = set()
    for path in expanded:
        resolved = str(path)
        if resolved in seen:
            continue
        seen.add(resolved)
        deduplicated.append(path)
    return deduplicated


def _load_summary(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_scenarios(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def _as_float(row: dict[str, str], key: str, default: float | None) -> float | None:
    value = row.get(key, "")
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def _latency_metric_value(summary: dict, metric_name: str) -> float | None:
    if metric_name == "per_image_total_p50_s":
        return summary["latency_stats"]["per_image_total_s"]["p50"]
    if metric_name == "per_image_total_p95_s":
        return summary["latency_stats"]["per_image_total_s"]["p95"]
    if metric_name == "per_image_sam3_p50_s":
        return summary["latency_stats"]["per_image_sam3_s"]["p50"]
    if metric_name == "per_image_sam3_p95_s":
        return summary["latency_stats"]["per_image_sam3_s"]["p95"]
    raise ValueError(f"Unsupported latency metric: {metric_name}")


def main() -> None:
    args = _parse_args()

    summary_paths = _expand_paths(args.benchmark_summaries)
    scenarios = _load_scenarios(Path(args.scenario_csv))
    rows: list[dict[str, object]] = []

    for summary_path in summary_paths:
        summary = _load_summary(summary_path)
        measured_images_per_second = summary["timings"]["images_per_second"]
        latency_value = _latency_metric_value(summary, args.latency_metric)

        for scenario in scenarios:
            arrival_rate = _as_float(scenario, "arrival_rate_images_per_sec", None)
            if arrival_rate is None:
                raise ValueError(
                    "Each scenario row must define arrival_rate_images_per_sec"
                )

            activation_fraction = _as_float(scenario, "activation_fraction", 1.0) or 0.0
            burst_factor = _as_float(scenario, "burst_factor", 1.0) or 0.0
            slo_seconds = _as_float(scenario, "slo_seconds", None)
            required_images_per_second = arrival_rate * activation_fraction * burst_factor

            throughput_feasible = (
                measured_images_per_second is not None
                and measured_images_per_second >= required_images_per_second
            )
            latency_feasible = (
                True
                if slo_seconds is None or latency_value is None
                else latency_value <= slo_seconds
            )
            single_node_feasible = bool(throughput_feasible and latency_feasible)
            utilization = (
                required_images_per_second / measured_images_per_second
                if measured_images_per_second not in (None, 0)
                else None
            )

            rows.append(
                {
                    "benchmark_id": summary.get("benchmark_id"),
                    "summary_json": str(summary_path),
                    "scenario_id": scenario.get("scenario_id", ""),
                    "policy": scenario.get("policy", ""),
                    "notes": scenario.get("notes", ""),
                    "arrival_rate_images_per_sec": arrival_rate,
                    "activation_fraction": activation_fraction,
                    "burst_factor": burst_factor,
                    "required_throughput_images_per_sec": required_images_per_second,
                    "measured_images_per_sec": measured_images_per_second,
                    "estimated_utilization": utilization,
                    "latency_metric": args.latency_metric,
                    "latency_value_s": latency_value,
                    "slo_seconds": slo_seconds,
                    "throughput_feasible": throughput_feasible,
                    "latency_feasible": latency_feasible,
                    "single_node_feasible": single_node_feasible,
                    "batch_size": summary["config"]["batch_size"],
                    "num_benchmarked_images": summary["dataset"]["num_benchmarked_images"],
                    "model_init_s": summary["timings"]["model_init_s"],
                    "torch_cuda_peak_allocated_mb": summary["resources"]["torch_cuda_peak_allocated_mb"],
                    "nvidia_smi_peak_memory_used_mb": summary["resources"]["nvidia_smi"]["peak_memory_used_mb"],
                    "nvidia_smi_peak_utilization_gpu_pct": summary["resources"]["nvidia_smi"]["peak_utilization_gpu_pct"],
                }
            )

    if not rows:
        raise RuntimeError("No rows were produced")

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote edge-capacity analysis to {output_path}")
    print(f"Rows: {len(rows)}")


if __name__ == "__main__":
    main()
