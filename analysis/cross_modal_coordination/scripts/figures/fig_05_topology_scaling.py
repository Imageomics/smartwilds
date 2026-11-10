#!/usr/bin/env python3
"""Figure 5 — Sensor-network topology scaling (PROMOTED to main text).

Two side-by-side panels:
  A) Independent scaling: B vs n_sites (CLT-style decrease for independent
     superposition of bursty arrivals).
  B) Correlated scaling: B vs intensity_multiplier on log-x (same sites, more
     density per site).

Color mapping per figures_checklist.md (project-wide consistency):
  - camera_trap        = blue       (#0173B2)
  - bioacoustic-hourly = solid orange (#DE8F05)
  - bioacoustic-chorus = dashed orange (#DE8F05, dashed)
  - drone              = green      (#029E73)
  - citizen_science    = purple     (#CC78BC)

Source: exp6_2a_trace_fidelity/results/topology_scaling.csv
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import RESULTS_DIR, DATA_DIR  # noqa: E402

SRC = DATA_DIR / "paper_results" / "topology_scaling.csv"
OUT_PDF = HERE / "fig_05_topology_scaling.pdf"
OUT_PNG = HERE / "fig_05_topology_scaling.png"

COLOR = {
    "camera_trap": "#0173B2",
    "bioacoustic": "#DE8F05",
    "drone": "#029E73",
    "citizen_science": "#CC78BC",
}

plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 12,
})


def _agg(group: pd.DataFrame, x_col: str) -> pd.DataFrame:
    """Mean ± std of B at each x value within a group."""
    return (
        group.groupby(x_col)["B"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "B_mean", "std": "B_std", "count": "n"})
    )


def main() -> None:
    df = pd.read_csv(SRC)

    panel_a = df[df["panel"] == "A_independent"].copy()
    panel_b = df[df["panel"] == "B_correlated"].copy()

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(7.0, 3.0))

    # --- Panel A: independent scaling ----
    # Camera trap (single combined series across all sites)
    ct = _agg(panel_a[panel_a["modality"] == "camera_trap"], "n_sites")
    axA.errorbar(
        ct["n_sites"], ct["B_mean"], yerr=ct["B_std"].fillna(0),
        marker="o", color=COLOR["camera_trap"], label="camera_trap",
        linewidth=1.5, markersize=6, capsize=3,
    )

    # Bioacoustic split by schedule regime
    ba_hourly = _agg(panel_a[(panel_a["modality"] == "bioacoustic") & (panel_a["schedule"] == "hourly")], "n_sites")
    axA.errorbar(
        ba_hourly["n_sites"], ba_hourly["B_mean"], yerr=ba_hourly["B_std"].fillna(0),
        marker="s", color=COLOR["bioacoustic"], linestyle="-",
        label="bioacoustic|hourly", linewidth=1.5, markersize=6, capsize=3,
    )
    ba_chorus = _agg(panel_a[(panel_a["modality"] == "bioacoustic") & (panel_a["schedule"] == "sunrise_sunset")], "n_sites")
    axA.errorbar(
        ba_chorus["n_sites"], ba_chorus["B_mean"], yerr=ba_chorus["B_std"].fillna(0),
        marker="D", color=COLOR["bioacoustic"], linestyle="--",
        label="bioacoustic|chorus", linewidth=1.5, markersize=6, capsize=3,
    )

    axA.axhline(0, color="#999", linewidth=0.6, linestyle=":")
    axA.set_xlabel("n_sites (independent scaling)")
    axA.set_ylabel("Burstiness $B$")
    axA.set_title("A. B vs site count", fontsize=11)
    axA.set_ylim(-0.95, 1.05)
    # Camera trap occupies B ∈ [+0.13, +0.87], bioacoustic-hourly B ∈
    # [−0.78, −0.62], chorus is flat at B ≈ +0.19. The empty zone is the
    # right half of the panel at B ∈ [−0.4, +0.4] (chorus stops at n=2).
    # Anchor the legend there.
    axA.legend(loc="center", bbox_to_anchor=(0.78, 0.42),
               framealpha=0.9, fontsize=8)
    axA.grid(alpha=0.25)

    # --- Panel B: correlated scaling ----
    for modality in ["camera_trap", "bioacoustic", "drone", "citizen_science"]:
        sub = _agg(panel_b[panel_b["modality"] == modality], "multiplier")
        axB.errorbar(
            sub["multiplier"], sub["B_mean"], yerr=sub["B_std"].fillna(0),
            marker="o", color=COLOR[modality], label=modality,
            linewidth=1.5, markersize=5, capsize=3,
        )

    axB.set_xscale("log")
    axB.axhline(0, color="#999", linewidth=0.6, linestyle=":")
    axB.set_xlabel("intensity_multiplier (correlated scaling)")
    axB.set_ylabel("Burstiness $B$")
    axB.set_title("B. B vs density", fontsize=11)
    axB.set_ylim(-0.45, 1.05)
    axB.legend(loc="center right", framealpha=0.9)
    axB.grid(alpha=0.25, which="both")

    fig.suptitle("Sensor-network topology scaling (extends Kline et al. 2024)", fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
    print(f"wrote {OUT_PDF}")
    print(f"wrote {OUT_PNG}")
    print(f"figure size: {fig.get_size_inches()} in")


if __name__ == "__main__":
    main()
