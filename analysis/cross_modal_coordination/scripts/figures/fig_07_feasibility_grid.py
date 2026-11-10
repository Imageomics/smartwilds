#!/usr/bin/env python3
"""Figure 7 — Predicted feasibility grid.

Layout per figures_checklist.md (Option D, 2-column-wide):
  - Rows: 4 case studies × 4 policies = 16. Manuscript order CS1..CS4
    (CS1 = Acoustic→CT, leadoff); within each case, policies in canonical order.
  - Columns: 5 hardware tiers, ordered most-to-least-powerful left-to-right
    (RTX, Jetson, Laptop, Pi5+TPU, Pi4 CPU).
  - Cells: F/I label only (the predicted-grid post-SAM3-removal has no
    degraded cells, so D is dropped from the legend; ratios in CSV).

Source: data/paper_results/master_feasibility.csv (already remapped to
manuscript case labels by build_master_feasibility.py).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import RESULTS_DIR, DATA_DIR  # noqa: E402

SRC = DATA_DIR / "paper_results" / "master_feasibility.csv"
OUT_PDF = HERE / "fig_07_feasibility_grid.pdf"
OUT_PNG = HERE / "fig_07_feasibility_grid.png"

# Okabe-Ito-derived pastel: F (green), I (red). D is included in the colormap
# so the LABEL_VALUE→CMAP mapping stays stable if a future grid produces D
# cells, but the legend below only shows F/I to match the current data.
CMAP = ListedColormap(["#a8e0c5", "#fde8a0", "#f5b8b1"])  # F, D, I
LABEL_VALUE = {"F": 0, "D": 1, "I": 2}

# Most → least powerful left-to-right
TIER_ORDER = ["workstation_rtx", "jetson_orin_nano", "field_laptop", "pi5_coral", "pi4_cpu"]
TIER_DISPLAY = {
    "workstation_rtx": "RTX",
    "jetson_orin_nano": "Jetson",
    "field_laptop": "Laptop",
    "pi5_coral": "Pi5+TPU",
    "pi4_cpu": "Pi4 CPU",
}

# Manuscript labels, natural numeric order
CASE_ORDER = ["CS1", "CS2", "CS3", "CS4"]

POLICY_ORDER = ["process_all", "event_triggered", "adaptive", "control_theoretic"]
POLICY_DISPLAY = {
    "process_all": "all",
    "event_triggered": "event",
    "adaptive": "adaptive",
    "control_theoretic": "ctrl",
}

# Style — Okabe-Ito body palette, paper-grade font sizes
plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 12,
})


def main() -> None:
    df = pd.read_csv(SRC)

    # Build (case, policy) row order
    df["case_idx"] = df["case_study"].map({c: i for i, c in enumerate(CASE_ORDER)})
    df["policy_idx"] = df["policy"].map({p: i for i, p in enumerate(POLICY_ORDER)})
    df = df.sort_values(["case_idx", "policy_idx"]).reset_index(drop=True)
    df["row_label"] = df["case_study"] + " / " + df["policy"].map(POLICY_DISPLAY)

    # Pivot to (rows, tiers) with consistent ordering
    row_order = df["row_label"].drop_duplicates().tolist()
    pivot_label = (
        df.pivot_table(index="row_label", columns="tier", values="label", aggfunc="first", sort=False)
        .reindex(index=row_order, columns=TIER_ORDER)
    )
    values = pivot_label.map(LABEL_VALUE.get).astype(int)

    # Anchored cells (Exp 3.5 calibration)
    measured = df[df["measured"].astype(str).str.lower() == "true"][
        ["row_label", "tier"]
    ].drop_duplicates()

    # 2-column-wide figure: ~7 in × 4.5 in
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.imshow(values.to_numpy(), cmap=CMAP, vmin=0, vmax=2, aspect="auto")

    # Axes
    ax.set_xticks(range(len(TIER_ORDER)))
    ax.set_xticklabels([TIER_DISPLAY[t] for t in TIER_ORDER], rotation=0)
    ax.set_yticks(range(len(row_order)))
    ax.set_yticklabels(row_order)
    ax.set_xlabel("Hardware tier (most → least powerful)")
    ax.set_ylabel("Case study / policy")

    # White gridlines between cells for readability
    ax.set_xticks([x - 0.5 for x in range(1, len(TIER_ORDER))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(row_order))], minor=True)
    ax.grid(which="minor", color="white", linewidth=1.4)
    ax.tick_params(which="minor", length=0)

    # Heavier separator between case-study row blocks
    for case_break in range(4, len(row_order), 4):
        ax.axhline(case_break - 0.5, color="#444", linewidth=0.9)

    # No per-cell text — color alone (green/red) carries verdict, legend
    # below decodes it. F/I text in master_feasibility.csv for anyone who
    # needs the exact label.

    # Highlight measured cells with a heavy black border + asterisk
    row_index = {label: i for i, label in enumerate(row_order)}
    col_index = {tier: i for i, tier in enumerate(TIER_ORDER)}
    for _, m in measured.iterrows():
        y = row_index.get(m["row_label"])
        x = col_index.get(m["tier"])
        if y is None or x is None:
            continue
        rect = Rectangle(
            (x - 0.5, y - 0.5), 1.0, 1.0,
            fill=False, edgecolor="#222", linewidth=2.0, zorder=5,
        )
        ax.add_patch(rect)
        ax.text(
            x + 0.36, y - 0.32, "★", ha="center", va="center",
            fontsize=10, color="#222", weight="bold", zorder=6,
        )

    # Legend under the figure (no D entry — current grid has no degraded cells)
    legend_handles = [
        Patch(facecolor="#a8e0c5", edgecolor="#222", label="F = feasible"),
        Patch(facecolor="#f5b8b1", edgecolor="#222", label="I = infeasible"),
    ]
    if len(measured):
        legend_handles.append(
            Patch(facecolor="white", edgecolor="#222", linewidth=2.0,
                  label="★ measured (Exp 3.5)"),
        )
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=len(legend_handles),
        frameon=False,
        fontsize=9,
    )

    fig.tight_layout()
    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
    print(f"wrote {OUT_PDF}")
    print(f"wrote {OUT_PNG}")
    print(f"figure size: {fig.get_size_inches()} in")
    print(f"rows: {len(row_order)}, cols: {len(TIER_ORDER)}")


if __name__ == "__main__":
    main()
