#!/usr/bin/env python3
"""Exp 3 predicted hardware feasibility model."""

from __future__ import annotations

import argparse
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
EXP3_ROOT = ROOT.parent
V2_ROOT = EXP3_ROOT.parent
TRACE_DIR = V2_ROOT / "exp6_3_case_studies" / "traces"
MANIFEST = TRACE_DIR / "manifest.json"
BENCHMARK = EXP3_ROOT / "3.1" / "benchmark_table.csv"
RESULTS = ROOT / "results"
POLICY_DIR = ROOT

if str(POLICY_DIR) not in sys.path:
    sys.path.insert(0, str(POLICY_DIR))

from policies import get_policy  # noqa: E402

POLICIES = ("process_all", "event_triggered", "adaptive", "control_theoretic")

MODALITY_MODEL = {
    "camera_trap": "megadetector",
    "bioacoustic": "birdnet",
    "drone": "sam3",
    "citizen_science": "bioclip",
}


def load_manifest() -> list[dict]:
    with open(MANIFEST) as f:
        return json.load(f)


@lru_cache(maxsize=None)
def policy_hourly_rates(trace_path: str, policy_name: str) -> tuple[pd.DataFrame, dict[str, int]]:
    policy = get_policy(policy_name)
    state = {
        "queue_depth": 0,
        "current_rate": 0.0,
        "x": 0.0,
    }
    action_counts = {"process": 0, "drop": 0, "defer": 0}

    events = pd.read_csv(trace_path)
    events = events.dropna(subset=["timestamp", "modality"])
    columns = list(events.columns)
    processed_records = []

    for idx, values in enumerate(events.itertuples(index=False, name=None)):
        event = dict(zip(columns, values))
        state["current_rate"] = idx + 1
        action = policy.decide(event, state)
        action_counts[action] = action_counts.get(action, 0) + 1
        if action == "defer":
            state["queue_depth"] = state.get("queue_depth", 0) + 1
            continue
        if action == "drop":
            continue

        state["queue_depth"] = max(0, state.get("queue_depth", 0) - 1)
        processed_records.append(
            {
                "timestamp": event["timestamp"],
                "modality": event["modality"],
            }
        )

    if not processed_records:
        return pd.DataFrame(columns=["modality", "p95_rate_per_hour", "mean_rate_per_hour"]), action_counts

    df = pd.DataFrame(processed_records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp", "modality"])
    if df.empty:
        return pd.DataFrame(columns=["modality", "p95_rate_per_hour", "mean_rate_per_hour"]), action_counts
    df["hour"] = df["timestamp"].dt.floor("h")
    hourly = df.groupby(["modality", "hour"]).size().rename("count").reset_index()
    rates = (
        hourly.groupby("modality")["count"]
        .agg(p95_rate_per_hour=lambda s: float(s.quantile(0.95)), mean_rate_per_hour="mean")
        .reset_index()
    )
    return rates, action_counts


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
    if policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}")

    slo_target_ms = float((slo_chain or [{}])[0].get("latency_budget_seconds", 0.0)) * 1000.0
    rates, action_counts = policy_hourly_rates(str(trace_path), policy)
    bench = benchmark_table[benchmark_table["tier"] == tier].set_index("model")

    total_util = 0.0
    worst_p95 = 0.0
    bottleneck = "none"
    bottleneck_util = -1.0
    modality_details = []
    unsupported = []

    for _, row in rates.iterrows():
        modality = str(row["modality"])
        model = MODALITY_MODEL.get(modality)
        if model is None or model not in bench.index:
            continue
        rate = float(row["p95_rate_per_hour"])
        service_ms = pd.to_numeric(bench.loc[model, "latency_ms"], errors="coerce")
        if pd.isna(service_ms):
            unsupported.append(f"{modality}:{model}")
            continue
        service_ms = float(service_ms)
        util, p95 = mm1_p95_ms(rate, service_ms)
        total_util += util
        if util > bottleneck_util:
            bottleneck_util = util
            bottleneck = f"{modality}:{model}"
        worst_p95 = max(worst_p95, p95)
        modality_details.append(f"{modality}:{model}:rate={rate:.2f}/h,util={util:.2f}%")

    if unsupported:
        worst_p95 = math.inf
        bottleneck = "unsupported:" + "+".join(unsupported)
        slo_met = False
        verdict = "infeasible"
        modality_details.append("unsupported=" + ",".join(unsupported))
    else:
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
        "details": "; ".join(
            [
                f"policy_actions=process:{action_counts.get('process', 0)},"
                f"drop:{action_counts.get('drop', 0)},defer:{action_counts.get('defer', 0)}",
                *modality_details,
            ]
        ),
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
