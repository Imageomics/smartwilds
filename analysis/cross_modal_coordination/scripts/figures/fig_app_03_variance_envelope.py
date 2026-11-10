#!/usr/bin/env python3
"""Figure 3 (appendix) — Variance envelope: synthesis spread vs natural spread.

For each (modality, statistic) pair, scatter the per-site natural values and
the per-seed synthesis values side by side; the width-ratio test passes when
synth spread fits inside the natural envelope (or below 1.2× of it for
non-gating cells).

Layout: 3 rows (statistics: B, CV, diurnal KS) × 3 cols (modalities:
camera_trap, bioacoustic, drone). Citizen science excluded — only one site
in Campaign 2 → no natural-envelope baseline.

Source: exp6_2a_trace_fidelity/results/variance_envelope.{csv,json}
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import RESULTS_DIR, DATA_DIR  # noqa: E402

DATA = DATA_DIR / "paper_results"
SRC_CSV = DATA / "variance_envelope.csv"
SRC_JSON = DATA / "variance_envelope.json"
OUT_PDF = HERE / "fig_app_03_variance_envelope.pdf"
OUT_PNG = HERE / "fig_app_03_variance_envelope.png"

MODALITY_COLOR = {
    "camera_trap": "#0173B2",
    "bioacoustic": "#DE8F05",
    "drone": "#029E73",
}

STATS = [
    ("burstiness_B", "Burstiness $B$"),
    ("cv", "CV"),
    ("diurnal_ks_vs_aggregate", "Diurnal KS"),
]
MODALITIES = ["camera_trap", "bioacoustic", "drone"]

plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
})


def main() -> None:
    df = pd.read_csv(SRC_CSV)
    with open(SRC_JSON) as f:
        verdicts = json.load(f)["verdicts"]

    fig, axes = plt.subplots(3, 3, figsize=(7.0, 6.5))

    for r, (stat, stat_label) in enumerate(STATS):
        for c, modality in enumerate(MODALITIES):
            ax = axes[r, c]
            sub = df[(df["modality"] == modality) & (df["metric"] == stat)]
            nat = sub[sub["source"] == "natural"]["value"].to_numpy()
            syn = sub[sub["source"] == "synthesis"]["value"].to_numpy()

            color = MODALITY_COLOR[modality]
            # Scatter at jittered x positions
            rng = np.random.default_rng(2026)
            ax.scatter(
                rng.uniform(-0.18, 0.18, size=len(nat)) + 0,
                nat,
                color="#888", edgecolor="#333", marker="o", s=36,
                label="natural (per site)" if (r, c) == (0, 0) else None,
            )
            ax.scatter(
                rng.uniform(-0.18, 0.18, size=len(syn)) + 1,
                syn,
                color=color, edgecolor="#222", marker="o", s=22, alpha=0.85,
                label="synthesis (per seed)" if (r, c) == (0, 0) else None,
            )

            # Natural envelope band [p05, p95]
            if len(nat) >= 2:
                lo, hi = np.percentile(nat, 5), np.percentile(nat, 95)
                ax.axhspan(lo, hi, color="#888", alpha=0.10, zorder=0)

            # Width-ratio annotation
            v = verdicts.get(modality, {}).get(stat)
            if v is not None:
                wr = v["width_ratio"]
                gating = v["is_gating"]
                pass_ = v["pass"]
                tag = "PASS" if pass_ else "FAIL"
                wr_text = f"width ratio = {wr:.3g}\n{tag}" + ("" if gating else " (non-gating)")
                ax.text(
                    0.5, 1.02, wr_text, transform=ax.transAxes,
                    ha="center", va="bottom", fontsize=8,
                    color="#222" if pass_ else "#a33",
                )

            ax.set_xticks([0, 1])
            ax.set_xticklabels(["natural", "synth"], fontsize=8)
            ax.set_xlim(-0.5, 1.5)
            if c == 0:
                ax.set_ylabel(stat_label)
            if r == 0:
                ax.set_title(modality.replace("_", " "), fontsize=10, pad=18)
            ax.grid(alpha=0.25, axis="y")

    handles = [
        plt.Line2D([], [], marker="o", color="#888", linestyle="",
                   markeredgecolor="#333", markersize=7, label="natural (per-site)"),
        plt.Line2D([], [], marker="o", color="#0173B2", linestyle="",
                   markeredgecolor="#222", markersize=6, label="synthesis (per-seed, color = modality)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, -0.02))

    fig.suptitle("Variance envelope: synthesis spread vs natural per-site spread", fontsize=11, y=1.00)
    fig.tight_layout(rect=(0, 0.03, 1, 0.99))
    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
    print(f"wrote {OUT_PDF}")
    print(f"wrote {OUT_PNG}")
    print(f"figure size: {fig.get_size_inches()} in")


if __name__ == "__main__":
    main()
