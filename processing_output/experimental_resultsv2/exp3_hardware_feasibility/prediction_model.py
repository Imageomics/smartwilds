#!/usr/bin/env python3
"""Exp 3 predicted hardware feasibility model."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
V2_ROOT = ROOT.parent
TRACE_DIR = V2_ROOT / "exp6_3_case_studies" / "traces"
MANIFEST = TRACE_DIR / "manifest.json"
BENCHMARK = ROOT / "benchmark_table.csv"
RESULTS = ROOT / "results"

POLICIES = ("process_all", "event_triggered", "adaptive", "control_theoretic")
POLICY_PROCESS_FRACTION = {
    "process_all": {"camera_trap": 1.0, "bioacoustic": 1.0, "drone": 1.0, "citizen_science": 1.0},
    "event_triggered": {"camera_trap": 0.45, "bioacoustic": 0.30, "drone": 0.35, "citizen_science": 1.0},
    "adaptive": {"camera_trap": 0.65, "bioacoustic": 0.50, "drone": 0.55, "citizen_science": 1.0},
    "control_theoretic": {"camera_trap": 0.55, "bioacoustic": 0.45, "drone": 0.45, "citizen_science": 1.0},
}

MODALITY_MODEL = {
    "camera_trap": "megadetector",
    "bioacoustic": "birdnet",
    "drone": "sam3",
    "citizen_science": "bioclip",
}


def load_manifest() -> list[dict]:
    with open(MANIFEST) as f:
        return json.load(f)


def hourly_rates(trace_path: Path) -> pd.DataFrame:
    df = pd.read_csv(trace_path, usecols=["timestamp", "modality"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp", "modality"])
    if df.empty:
        return pd.DataFrame(columns=["modality", "p95_rate_per_hour", "mean_rate_per_hour"])
    df["hour"] = df["timestamp"].dt.floor("h")
    hourly = df.groupby(["modality", "hour"]).size().rename("count").reset_index()
    return (
        hourly.groupby("modality")["count"]
        .agg(p95_rate_per_hour=lambda s: float(s.quantile(0.95)), mean_rate_per_hour="mean")
        .reset_index()
    )


def mm1_p95_ms(arrival_rate_per_hour: float, service_ms: float) -> tuple[float, float]:
    """Return (utilization_pct, M/M/1 p95 response time in ms)."""
    lam_per_ms = float(arrival_rate_per_hour) / 3_600_000.0
    rho = lam_per_ms * float(service_ms)
    if rho >= 1.0:
        return rho * 100.0, math.inf
    # Exponential response-time tail for M/M/1: P(R > t) = exp(-(mu-lambda)t).
    p95 = -math.log(0.05) * float(service_ms) / max(1.0 - rho, 1e-9)
    return rho * 100.0, p95


def predict_cell(
    trace_path: Path,
    tier: str,
    policy: str,
    benchmark_table: pd.DataFrame,
    slo_chain: list[dict] | None = None,
) -> dict:
    if policy not in POLICY_PROCESS_FRACTION:
        raise ValueError(f"unknown policy {policy!r}")

    slo_target_ms = float((slo_chain or [{}])[0].get("latency_budget_seconds", 0.0)) * 1000.0
    rates = hourly_rates(trace_path)
    bench = benchmark_table[benchmark_table["tier"] == tier].set_index("model")

    total_util = 0.0
    worst_p95 = 0.0
    bottleneck = "none"
    bottleneck_util = -1.0
    modality_details = []

    for _, row in rates.iterrows():
        modality = str(row["modality"])
        model = MODALITY_MODEL.get(modality)
        if model is None or model not in bench.index:
            continue
        fraction = POLICY_PROCESS_FRACTION[policy].get(modality, 1.0)
        rate = float(row["p95_rate_per_hour"]) * fraction
        service_ms = float(bench.loc[model, "latency_ms"])
        util, p95 = mm1_p95_ms(rate, service_ms)
        total_util += util
        if util > bottleneck_util:
            bottleneck_util = util
            bottleneck = f"{modality}:{model}"
        worst_p95 = max(worst_p95, p95)
        modality_details.append(f"{modality}:{model}:rate={rate:.2f}/h,util={util:.2f}%")

    slo_met = worst_p95 <= slo_target_ms if slo_target_ms > 0 else False
    if total_util < 70.0 and slo_met:
        verdict = "feasible"
    elif total_util < 100.0 and (slo_target_ms <= 0 or worst_p95 <= 1.25 * slo_target_ms):
        verdict = "degraded"
    else:
        verdict = "infeasible"

    return {
        "utilization_pct": total_util,
        "p95_latency_ms": worst_p95,
        "bottleneck_modality": bottleneck,
        "verdict": verdict,
        "slo_met": bool(slo_met),
        "details": "; ".join(modality_details),
    }


def run_grid() -> pd.DataFrame:
    benchmark_table = pd.read_csv(BENCHMARK)
    tiers = list(dict.fromkeys(benchmark_table["tier"].astype(str)))
    rows = []
    for case in load_manifest():
        trace_path = V2_ROOT / "exp6_3_case_studies" / case["trace_path"]
        slo_seconds = float(case["slo_compliance_seconds"])
        slo_chain = [{"latency_budget_seconds": slo_seconds}]
        for tier in tiers:
            for policy in POLICIES:
                pred = predict_cell(trace_path, tier, policy, benchmark_table, slo_chain)
                rows.append(
                    {
                        "case_study": case["case_study"],
                        "workload": case["name"],
                        "tier": tier,
                        "policy": policy,
                        "utilization_pct_predicted": round(pred["utilization_pct"], 3),
                        "p95_latency_ms_predicted": round(pred["p95_latency_ms"], 3) if math.isfinite(pred["p95_latency_ms"]) else math.inf,
                        "slo_target_ms": slo_seconds * 1000.0,
                        "slo_met_predicted": pred["slo_met"],
                        "bottleneck": pred["bottleneck_modality"],
                        "verdict": pred["verdict"],
                        "measured": False,
                        "calibration_gap_pct": "",
                        "modeling_notes": pred["details"],
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=RESULTS / "predicted_feasibility_grid.csv")
    args = parser.parse_args()
    if not BENCHMARK.exists():
        raise FileNotFoundError(f"{BENCHMARK} not found; run benchmark_table.py first")
    df = run_grid()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"wrote {args.out}")
    print(df[["case_study", "tier", "policy", "utilization_pct_predicted", "p95_latency_ms_predicted", "verdict"]].to_string(index=False))


if __name__ == "__main__":
    main()
