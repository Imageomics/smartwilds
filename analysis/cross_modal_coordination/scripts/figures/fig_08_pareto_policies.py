#!/usr/bin/env python3
"""Figure 8 — Per-policy Pareto: coverage vs total energy on Campaign 2 recorded
camera trace, laptop tier (Exp 4).

Scope caveat (in caption): Exp 4 was run only on the Campaign 2 recorded camera
trace at laptop tier with a single seed — not on the synthesized CS1/CS2/CS3/CS4
traces, not across tiers, not across seeds. So this is a 4-point single-workload
view, not a multi-workload Pareto frontier.

Source: data/paper_results/exp4_policy_metrics.csv
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import RESULTS_DIR, DATA_DIR  # noqa: E402

SRC = DATA_DIR / "paper_results" / "exp4_policy_metrics.csv"
OUT_PDF = HERE / "fig_08_pareto_policies.pdf"
OUT_PNG = HERE / "fig_08_pareto_policies.png"

# Okabe-Ito-derived colors per policy + distinct markers so overlapping
# points (event_triggered and control_theoretic both land at coverage=0.10,
# energy=9.9 kJ) stay readable.
POLICY_COLOR = {
    "process_all": "#0173B2",       # blue
    "event_triggered": "#DE8F05",   # orange
    "adaptive": "#029E73",          # green
    "control_theoretic": "#CC78BC", # purple
}
POLICY_MARKER = {
    "process_all": "o",
    "event_triggered": "D",
    "adaptive": "s",
    "control_theoretic": "^",
}
POLICY_DISPLAY = {
    "process_all": "process_all",
    "event_triggered": "event_triggered",
    "adaptive": "adaptive",
    "control_theoretic": "control_theoretic",
}

plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
})


def main() -> None:
    df = pd.read_csv(SRC)
    df["total_energy_kj"] = df["total_energy_j"] / 1000.0
    df["coverage"] = df["coverage_pct"]  # already in [0, 1]

    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    # event_triggered and control_theoretic land at the same (coverage,
    # energy) point on this single-trace dataset; nudge control_theoretic
    # slightly along x so both markers are visible.
    x_offset = {"control_theoretic": 1.4}
    annot_offsets = {
        "process_all": (10, 2),
        "event_triggered": (10, -14),
        "adaptive": (10, 2),
        "control_theoretic": (10, 12),
    }
    for _, row in df.iterrows():
        policy = row["policy"]
        x = row["total_energy_kj"] + x_offset.get(policy, 0.0)
        y = row["coverage"]
        ax.scatter(
            x, y,
            color=POLICY_COLOR.get(policy, "#444"),
            edgecolor="#222", s=130, linewidth=1.5, zorder=3,
            marker=POLICY_MARKER.get(policy, "o"),
            label=POLICY_DISPLAY.get(policy, policy),
        )
        dx, dy = annot_offsets.get(policy, (8, -4))
        ax.annotate(
            f"{row['mean_energy_j']:.2f} J/event",
            (x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=8,
            color="#333",
        )

    ax.set_xlabel("Total energy (kJ) — Campaign 2 recorded camera trace")
    ax.set_ylabel("Coverage (fraction processed)")
    ax.set_xlim(0, max(df["total_energy_kj"]) * 1.15)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", framealpha=0.9, title="policy")

    fig.suptitle("Per-policy coverage vs energy (laptop tier, single seed, recorded trace)",
                 fontsize=10, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
    print(f"wrote {OUT_PDF}")
    print(f"wrote {OUT_PNG}")
    print(f"figure size: {fig.get_size_inches()} in")


if __name__ == "__main__":
    main()
