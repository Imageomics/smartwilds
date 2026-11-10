#!/usr/bin/env python3
"""Plot the Exp 3 predicted feasibility heatmap."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import ListedColormap


ROOT = Path(__file__).resolve().parent
IN = ROOT / "results" / "predicted_feasibility_grid.csv"
OUT = ROOT / "results" / "predicted_feasibility_heatmap.pdf"

VERDICT_VALUE = {"feasible": 0, "degraded": 1, "infeasible": 2}
COLORS = ListedColormap(["#2ca25f", "#f0c419", "#de2d26"])


def main() -> None:
    df = pd.read_csv(IN)
    df["row_label"] = df["case_study"].astype(str) + " / " + df["policy"].astype(str)
    pivot = df.pivot_table(index="row_label", columns="tier", values="verdict", aggfunc="first")
    values = pivot.map(VERDICT_VALUE.get).astype(int)

    fig_w = max(7.0, 1.25 * len(values.columns))
    fig_h = max(5.0, 0.35 * len(values.index))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.imshow(values.to_numpy(), cmap=COLORS, vmin=0, vmax=2, aspect="auto")
    ax.set_xticks(range(len(values.columns)))
    ax.set_xticklabels(values.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(values.index)))
    ax.set_yticklabels(values.index)
    ax.set_xlabel("Hardware tier")
    ax.set_ylabel("Case study / policy")
    ax.set_title("Exp 3 predicted feasibility grid")

    for y in range(values.shape[0]):
        for x in range(values.shape[1]):
            verdict = pivot.iloc[y, x]
            ax.text(x, y, verdict, ha="center", va="center", fontsize=7, color="black")

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
