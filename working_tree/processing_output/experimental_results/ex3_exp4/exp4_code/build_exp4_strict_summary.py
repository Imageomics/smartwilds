from __future__ import annotations

from pathlib import Path
import pandas as pd

INPUT = Path("outputs/tables/arrivals/replay_metrics_exp4_strict.csv")
OUTPUT = Path("outputs/tables/arrivals/exp4_summary_table_strict.csv")

def main() -> None:
    df = pd.read_csv(INPUT).copy()

    out = df[[
        "policy",
        "coverage",
        "p95_latency_ms",
        "compute_cost_sec",
        "operator_effort_estimate",
        "slo_compliance",
    ]].sort_values("policy").reset_index(drop=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False)

    print(f"Saved strict Exp 4 summary: {OUTPUT}")
    print(out.to_string(index=False))

if __name__ == "__main__":
    main()
