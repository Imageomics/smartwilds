#!/usr/bin/env python3
"""Figure 4 (appendix) — Intensity scaling: B vs k for all four modalities.

Single panel per the figures_checklist (CV and mean-rate panels are dropped
because the same information rides on top of B vs k). Adds shaded bands for
the per-modality natural envelope so the "drone synthesis escapes envelope"
finding is visible at a glance.

Source: exp6_2a_trace_fidelity/results/generalization_sweep_l2.json (per_cell)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import RESULTS_DIR, DATA_DIR  # noqa: E402

DATA = DATA_DIR / "paper_results"
SRC = DATA / "generalization_sweep_l2.json"
OUT_PDF = HERE / "fig_app_04_intensity_sweep.pdf"
OUT_PNG = HERE / "fig_app_04_intensity_sweep.png"

COLOR = {
    "camera_trap": "#0173B2",
    "bioacoustic": "#DE8F05",
    "drone": "#029E73",
    "citizen_science": "#CC78BC",
}
MARKER = {"camera_trap": "o", "bioacoustic": "s", "drone": "D", "citizen_science": "^"}

plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
})


def main() -> None:
    payload = json.loads(SRC.read_text())
    df = pd.DataFrame(payload["per_cell"])

    # Natural-envelope bands per modality (p05–p95)
    bands = {}
    for entry in payload["per_modality_summary"]:
        if entry.get("envelope_B_band") is not None:
            lo, hi = entry["envelope_B_band"]
            bands[entry["modality"]] = (lo, hi)

    fig, ax = plt.subplots(figsize=(7.0, 3.5))

    # Shaded natural envelope bands first so points sit on top
    for modality, (lo, hi) in bands.items():
        ax.axhspan(lo, hi, color=COLOR[modality], alpha=0.10, zorder=0)

    for modality in ["camera_trap", "bioacoustic", "drone", "citizen_science"]:
        sub = df[df["modality"] == modality].sort_values("intensity_multiplier")
        ax.errorbar(
            sub["intensity_multiplier"], sub["B_mean"],
            yerr=sub["B_std"].fillna(0),
            marker=MARKER[modality], color=COLOR[modality], label=modality,
            linewidth=1.5, markersize=6, capsize=3,
        )

    ax.set_xscale("log")
    ax.axhline(0, color="#999", linewidth=0.6, linestyle=":")
    ax.set_xlabel("intensity_multiplier $k$ (correlated scaling)")
    ax.set_ylabel("Burstiness $B$ (mean ± std across 5 seeds)")
    ax.set_ylim(-0.8, 1.0)
    ax.legend(loc="center right", framealpha=0.9, ncol=1)
    ax.grid(alpha=0.25, which="both")

    # Annotate the natural envelope shading
    ax.text(
        0.99, 0.02,
        "shaded bands = natural per-site envelope (p05–p95)",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="#444",
    )

    fig.tight_layout()
    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
    print(f"wrote {OUT_PDF}")
    print(f"wrote {OUT_PNG}")
    print(f"figure size: {fig.get_size_inches()} in")


if __name__ == "__main__":
    main()
