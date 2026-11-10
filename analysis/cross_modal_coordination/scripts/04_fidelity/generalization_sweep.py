#!/usr/bin/env python3
"""
generalization_sweep.py — Exp 6.2.A L2 (intensity-scaling) generalization sweep.

Scope (per 2026-04-27 decision): L2 only. Tests whether the synthesis engine,
under intensity_multiplier scaling on an identity recipe, produces traces whose
burstiness/CV/rate stay within the natural per-site envelope established in
Exp 1. This is the methodology Figure 9 input.

Distinct from topology_scaling.py Panel B (same data axis, different gate):
    Panel B asked "is B preserved across k within ±0.05?" — the answer is
    "no for 3/4 modalities" but the gate was always too tight (engine-level
    rate amplification doesn't preserve B exactly for finite-horizon mixtures
    of segment-rate Poisson processes).
    This script asks "does B(k) stay within the natural per-site variance
    envelope from variance_envelope.json?" — the variance-envelope criterion
    that defends the rest of 6.2.A. Same defensibility argument, extended to
    intensity scaling.

Pass criterion per cell (modality, k):
    B(k) within [p05, p95] of natural per-site B distribution
    CV(k) within [p05, p95] of natural per-site CV distribution
    (mean rate is reported but not gated — it scales by k by construction)

Outputs:
    results/generalization_sweep_l2.csv     long-form per-cell B/CV/rate
    results/generalization_sweep_l2.json    summary + per-modality breaking k
    results/generalization_sweep_l2.{png,pdf}   3-panel Figure 9 (B, CV, rate)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --- portable paths: resolved by scripts/paths.py, overridable via env vars ---
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import RESULTS_DIR  # noqa: E402

SYNTH_DIR = Path(__file__).resolve().parents[1] / "02_synthesize"
OUT_DIR = RESULTS_DIR / "fidelity"          # same directory variance_envelope.py writes to
ENVELOPE_PATH = OUT_DIR / "variance_envelope.json"

sys.path.insert(0, str(SYNTH_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from schemas import Recipe  # noqa: E402
from synthesize import synthesize, load_primitives, load_independence_bounds  # noqa: E402
from fidelity_metrics import burstiness_from_timestamps  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

DEFAULT_MULTIPLIERS = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0)
DEFAULT_DURATION_DAYS = 25  # Campaign 2
MODALITIES = ("camera_trap", "bioacoustic", "drone", "citizen_science")


def load_envelope() -> dict:
    if not ENVELOPE_PATH.exists():
        raise FileNotFoundError(
            f"variance_envelope.json missing at {ENVELOPE_PATH}; "
            "run variance_envelope.py first to establish the natural envelope."
        )
    with open(ENVELOPE_PATH) as f:
        return json.load(f)["natural_envelope"]


def envelope_band(envelope: dict, modality: str, metric: str) -> tuple[float, float] | None:
    """Return (p05, p95) band for the natural envelope, or None if not available."""
    if modality not in envelope:
        return None
    if metric not in envelope[modality]:
        return None
    e = envelope[modality][metric]
    return float(e["p05"]), float(e["p95"])


def synth_one_cell(modality: str, k: float, primitives: dict, bounds: pd.DataFrame,
                   duration_seconds: float, seed: int) -> tuple[float, float, float, int]:
    """Synthesize one (modality, k, seed) cell. Returns (mean_rate_per_hour, cv, B, n_events)."""
    recipe = Recipe(
        modality_mix=(modality,),
        combinator="concatenate",
        duration_seconds=duration_seconds,
        density={},
        intensity_multiplier=float(k),
        slo_chain=(),
        seed=seed,
        name=f"l2_{modality}_k{k}",
    )
    event_log = synthesize(recipe, primitives={modality: primitives[modality]}, independence_bounds=bounds)
    if event_log.empty:
        return 0.0, 0.0, 0.0, 0
    ts = pd.to_datetime(event_log["timestamp"]).sort_values()
    if len(ts) < 2:
        return 0.0, 0.0, 0.0, len(ts)
    mean_rate, cv, B = burstiness_from_timestamps(ts)
    return mean_rate, cv, B, len(ts)


def sweep(multipliers: tuple[float, ...], n_seeds: int, duration_days: int) -> pd.DataFrame:
    primitives = load_primitives(MODALITIES)
    bounds = load_independence_bounds()
    duration_seconds = duration_days * 86400.0

    rows = []
    for m in MODALITIES:
        for k in multipliers:
            for seed in range(n_seeds):
                mr, cv, B, n = synth_one_cell(m, k, primitives, bounds, duration_seconds, seed)
                rows.append({
                    "modality": m,
                    "intensity_multiplier": float(k),
                    "seed": seed,
                    "mean_rate_per_hour": mr,
                    "cv": cv,
                    "burstiness_B": B,
                    "n_events": n,
                })
            log.info(f"  {m} k={k}: {n_seeds} seeds done")
    return pd.DataFrame(rows)


def evaluate_against_envelope(df: pd.DataFrame, envelope: dict) -> dict:
    """For each (modality, k): mean B/CV across seeds, pass iff inside [p05, p95] envelope."""
    out = {"per_cell": [], "per_modality_summary": []}
    for m in MODALITIES:
        sub = df[df["modality"] == m]
        if sub.empty:
            continue
        b_band = envelope_band(envelope, m, "burstiness_B")
        cv_band = envelope_band(envelope, m, "cv")

        per_modality = {
            "modality": m,
            "envelope_available": b_band is not None,
            "envelope_B_band": list(b_band) if b_band else None,
            "envelope_CV_band": list(cv_band) if cv_band else None,
            "cells": [],
            "first_break_k_B": None,
            "first_break_k_CV": None,
        }

        for k, g in sub.groupby("intensity_multiplier"):
            B_mean = float(g["burstiness_B"].mean())
            B_std = float(g["burstiness_B"].std()) if len(g) > 1 else 0.0
            cv_mean = float(g["cv"].mean())
            cv_std = float(g["cv"].std()) if len(g) > 1 else 0.0
            mr_mean = float(g["mean_rate_per_hour"].mean())

            # Pass = mean inside envelope p05–p95. n/a if no envelope (citsci).
            B_pass: bool | None = None
            CV_pass: bool | None = None
            if b_band is not None:
                B_pass = bool(b_band[0] <= B_mean <= b_band[1])
            if cv_band is not None:
                CV_pass = bool(cv_band[0] <= cv_mean <= cv_band[1])

            cell = {
                "modality": m,
                "intensity_multiplier": float(k),
                "n_seeds": int(len(g)),
                "B_mean": B_mean, "B_std": B_std,
                "CV_mean": cv_mean, "CV_std": cv_std,
                "mean_rate_per_hour": mr_mean,
                "B_in_envelope": B_pass,
                "CV_in_envelope": CV_pass,
            }
            per_modality["cells"].append(cell)
            out["per_cell"].append(cell)

        # First k > 1 at which we leave the envelope
        for cell in sorted(per_modality["cells"], key=lambda c: c["intensity_multiplier"]):
            if cell["intensity_multiplier"] <= 1.0:
                continue
            if per_modality["first_break_k_B"] is None and cell["B_in_envelope"] is False:
                per_modality["first_break_k_B"] = cell["intensity_multiplier"]
            if per_modality["first_break_k_CV"] is None and cell["CV_in_envelope"] is False:
                per_modality["first_break_k_CV"] = cell["intensity_multiplier"]

        out["per_modality_summary"].append(per_modality)
    return out


# --------------------------------------------------------------------------
# Plot — Figure 9 (L2 only)
# --------------------------------------------------------------------------

PANEL_COLORS = {
    "camera_trap": "#1f77b4",
    "bioacoustic": "#d62728",
    "drone": "#2ca02c",
    "citizen_science": "#9467bd",
}


def make_figure(df: pd.DataFrame, envelope: dict, out_stem: Path):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    ax_B, ax_CV, ax_R = axes

    for m in MODALITIES:
        sub = df[df["modality"] == m]
        if sub.empty:
            continue
        color = PANEL_COLORS[m]

        # Mean ± std across seeds at each k
        agg = sub.groupby("intensity_multiplier").agg(
            B_mean=("burstiness_B", "mean"),
            B_std=("burstiness_B", "std"),
            CV_mean=("cv", "mean"),
            CV_std=("cv", "std"),
            R_mean=("mean_rate_per_hour", "mean"),
            R_std=("mean_rate_per_hour", "std"),
        ).reset_index().sort_values("intensity_multiplier")
        ks = agg["intensity_multiplier"].to_numpy(dtype=float)

        ax_B.errorbar(ks, agg["B_mean"], yerr=agg["B_std"].fillna(0),
                      marker="o", color=color, label=m, capsize=3)
        ax_CV.errorbar(ks, agg["CV_mean"], yerr=agg["CV_std"].fillna(0),
                       marker="s", color=color, label=m, capsize=3)
        ax_R.errorbar(ks, agg["R_mean"], yerr=agg["R_std"].fillna(0),
                      marker="^", color=color, label=m, capsize=3)

        # Envelope shading on B and CV panels
        b_band = envelope_band(envelope, m, "burstiness_B")
        cv_band = envelope_band(envelope, m, "cv")
        if b_band is not None:
            ax_B.axhspan(b_band[0], b_band[1], color=color, alpha=0.08)
        if cv_band is not None:
            ax_CV.axhspan(cv_band[0], cv_band[1], color=color, alpha=0.08)

    for ax, ylabel, title in (
        (ax_B, "Burstiness B", "A. B vs intensity"),
        (ax_CV, "CV of IAT", "B. CV vs intensity"),
        (ax_R, "Mean rate (events/h)", "C. Mean rate vs intensity"),
    ):
        ax.set_xscale("log")
        ax.set_xlabel("intensity multiplier k")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.axvline(1.0, color="gray", linewidth=0.5, linestyle=":")
        ax.grid(True, alpha=0.3, which="both")
        ax.legend(fontsize=8, loc="best")
    ax_R.set_yscale("log")  # rate spans 4 orders of magnitude across modalities

    fig.suptitle(
        "Synthesis under intensity scaling vs natural per-site envelope",
        fontsize=12,
    )
    plt.tight_layout()
    for ext in ("png", "pdf"):
        p = out_stem.with_suffix(f".{ext}")
        fig.savefig(p, dpi=150)
        log.info(f"  wrote {p}")
    plt.close(fig)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n-seeds", type=int, default=5)
    p.add_argument("--duration-days", type=int, default=DEFAULT_DURATION_DAYS)
    p.add_argument("--multipliers", type=float, nargs="+", default=list(DEFAULT_MULTIPLIERS))
    args = p.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log.info(f"L2 sweep — multipliers={args.multipliers} seeds={args.n_seeds} horizon={args.duration_days}d")
    df = sweep(tuple(args.multipliers), args.n_seeds, args.duration_days)

    csv_path = OUT_DIR / "generalization_sweep_l2.csv"
    df.to_csv(csv_path, index=False)
    log.info(f"  wrote {csv_path}")

    envelope = load_envelope()
    summary = evaluate_against_envelope(df, envelope)
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()
    summary["multipliers"] = list(args.multipliers)
    summary["n_seeds"] = args.n_seeds
    summary["duration_days"] = args.duration_days
    summary["envelope_source"] = str(ENVELOPE_PATH)

    json_path = OUT_DIR / "generalization_sweep_l2.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"  wrote {json_path}")

    make_figure(df, envelope, OUT_DIR / "generalization_sweep_l2")

    # Console summary
    print("\n=== L2 sweep summary (mean across seeds; envelope = per-site p05–p95 from Exp 1) ===")
    for mod_summary in summary["per_modality_summary"]:
        m = mod_summary["modality"]
        b_band = mod_summary["envelope_B_band"]
        cv_band = mod_summary["envelope_CV_band"]
        if b_band:
            print(f"\n{m}  envelope: B [{b_band[0]:+.3f}, {b_band[1]:+.3f}]   CV [{cv_band[0]:.2f}, {cv_band[1]:.2f}]")
        else:
            print(f"\n{m}  envelope: n/a (single site)")
        for cell in sorted(mod_summary["cells"], key=lambda c: c["intensity_multiplier"]):
            B_mark = "PASS" if cell["B_in_envelope"] else ("FAIL" if cell["B_in_envelope"] is False else "n/a")
            CV_mark = "PASS" if cell["CV_in_envelope"] else ("FAIL" if cell["CV_in_envelope"] is False else "n/a")
            print(f"  k={cell['intensity_multiplier']:5.1f}  "
                  f"B={cell['B_mean']:+.3f}±{cell['B_std']:.3f} [{B_mark}]   "
                  f"CV={cell['CV_mean']:7.2f}±{cell['CV_std']:6.2f} [{CV_mark}]   "
                  f"rate={cell['mean_rate_per_hour']:9.2f}/h   n={cell['n_seeds']}")
        print(f"  first break (k>1): B@{mod_summary['first_break_k_B']}  CV@{mod_summary['first_break_k_CV']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
