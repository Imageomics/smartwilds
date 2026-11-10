from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

INPUT = Path("outputs/tables/benchmark/exp3_summary_table_strict.csv")
OUT = Path("outputs/figures/exp3_strict_aggregate_util.png")


def main() -> None:
    df = pd.read_csv(INPUT)

    scenarios = ["nominal", "busy", "worst_case"]
    policies = sorted(df["policy"].unique())

    fig, ax = plt.subplots(figsize=(10, 6))

    for policy in policies:
        sub = df[df["policy"] == policy].copy()
        sub["scenario"] = pd.Categorical(sub["scenario"], categories=scenarios, ordered=True)
        sub = sub.sort_values("scenario")
        ax.plot(sub["scenario"], sub["aggregate_util_percent"], marker="o", label=policy)

    ax.axhline(100.0, linestyle="--", linewidth=1.2)
    ax.set_title("Exp 3 strict: aggregate utilization by scenario and policy")
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Aggregate utilization (%)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=200)
    plt.close(fig)

    print(f"Saved figure: {OUT}")


if __name__ == "__main__":
    main()
