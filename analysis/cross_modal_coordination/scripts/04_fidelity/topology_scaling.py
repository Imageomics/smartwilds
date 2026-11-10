#!/usr/bin/env python3
"""
topology_scaling.py — sensor-network topology scaling test.

Replaces the multi-level generalization sweep per the 2026-04-27 scope decision.
Tests two deployment scaling strategies:

    A. Independent scaling — more sites, same density per site.
       Mechanism: subset recorded Campaign-2 timestamps by site, compute aggregate B.
       Predicted: B decreases with n_sites (CLT for independent superposition);
       mean rate scales linearly.

    B. Correlated scaling — same sites, higher density per site.
       Mechanism: synthesize at varying Recipe.intensity_multiplier, identity recipe.
       Predicted (empirical): B preserved or rising.
       Engine behavior: B preserved exactly under rate multiplication.
       Test: do these match? Documents the framework's correlated-scaling model
       as conservative — real correlated scaling may exceed the prediction.

Outputs:
    results/topology_scaling.csv    long-form per-cell B/CV/mean_rate
    results/topology_scaling.json   summary + direction-of-effect verdicts
    results/topology_scaling.{png,pdf}   two-panel figure for §V.A inline

Usage:
    python topology_scaling.py
    python topology_scaling.py --n-seeds 10 --n-combos 5
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --- portable paths: resolved by scripts/paths.py, overridable via env vars ---
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import BASE_DIR, RESULTS_DIR, TIMESTAMPS_DIR  # noqa: E402
SYNTH_DIR = Path(__file__).resolve().parents[1] / "02_synthesize"
OUT_DIR = RESULTS_DIR / "fidelity"


sys.path.insert(0, str(SYNTH_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from schemas import Recipe  # noqa: E402
from synthesize import synthesize, load_primitives, load_independence_bounds  # noqa: E402
from fidelity_metrics import burstiness_from_timestamps  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

CAMPAIGN2_START = pd.Timestamp("2025-08-04")
CAMPAIGN2_END = pd.Timestamp("2025-08-29")  # exclusive
DEFAULT_DURATION_DAYS = 25  # Campaign 2 span


def _load_campaign2_timestamps(modality: str) -> pd.DataFrame:
    """Load timestamps_<modality>.csv, restrict to Campaign 2 window."""
    path = TIMESTAMPS_DIR / f"timestamps_{modality}.csv"
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df[(df["timestamp"] >= CAMPAIGN2_START) & (df["timestamp"] < CAMPAIGN2_END)]
    return df


def _ba_site_label(row: pd.Series) -> str:
    """Bioacoustic site label combines site + schedule (matches primitives' per_site keys)."""
    return f"{row['site']}|{row.get('schedule', 'unknown')}"


# --------------------------------------------------------------------------
# A — Independent scaling (empirical from recorded timestamps)
# --------------------------------------------------------------------------

def independent_scaling_empirical(
    modality: str,
    schedule_filter: str | None = None,
    n_combos_max: int = 10,
    rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """
    For modality M: subset by site (and optionally schedule, for bioacoustic).
    For n ∈ {1, ..., k}: sample up to n_combos_max site combinations of size n,
    compute aggregate B/CV/mean_rate over the combined timestamps.

    Returns long-form DataFrame with columns:
        modality, schedule, n_sites, combo_id, sites_csv, n_events, B, cv, mean_rate
    """
    rng = rng or np.random.default_rng(0)
    df = _load_campaign2_timestamps(modality)

    # Filter to bioacoustic schedule regime if requested
    if schedule_filter is not None:
        if "schedule" not in df.columns:
            raise ValueError(f"{modality} has no schedule column; cannot filter")
        df = df[df["schedule"] == schedule_filter]

    sites = sorted(df["site"].unique())
    if len(sites) == 0:
        log.warning(f"  {modality} (schedule={schedule_filter}): no sites")
        return pd.DataFrame()

    rows = []
    schedule_label = schedule_filter or ""
    for n in range(1, len(sites) + 1):
        all_combos = list(combinations(sites, n))
        if len(all_combos) > n_combos_max:
            picked = rng.choice(len(all_combos), size=n_combos_max, replace=False)
            combos = [all_combos[i] for i in picked]
        else:
            combos = all_combos

        for combo_id, sites_subset in enumerate(combos):
            sub = df[df["site"].isin(sites_subset)]
            if len(sub) < 2:
                continue
            ts = sub["timestamp"].sort_values()
            mean_rate, cv, B = burstiness_from_timestamps(ts)
            rows.append({
                "modality": modality,
                "schedule": schedule_label,
                "n_sites": n,
                "combo_id": combo_id,
                "sites_csv": ",".join(sites_subset),
                "n_events": len(sub),
                "B": B,
                "cv": cv,
                "mean_rate_per_hour": mean_rate,
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# B — Correlated scaling (synthesis with intensity_multiplier)
# --------------------------------------------------------------------------

def correlated_scaling_synth(
    modality: str,
    primitives: dict,
    multipliers: tuple[float, ...] = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0),
    n_seeds: int = 5,
    duration_seconds: float = DEFAULT_DURATION_DAYS * 86400.0,
    independence_bounds: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    For modality M: synthesize under varying intensity_multiplier; compute B/CV/mean_rate.

    Returns long-form DataFrame with columns:
        modality, multiplier, seed, n_events, B, cv, mean_rate_per_hour
    """
    rows = []
    for k in multipliers:
        for seed in range(n_seeds):
            recipe = Recipe(
                modality_mix=(modality,),
                combinator="concatenate",
                duration_seconds=duration_seconds,
                density={},
                intensity_multiplier=float(k),
                slo_chain=(),
                seed=seed,
                name=f"corr_scale_{modality}_k{k}",
            )
            event_log = synthesize(
                recipe,
                primitives={modality: primitives[modality]},
                independence_bounds=independence_bounds,
            )
            ts = pd.to_datetime(event_log["timestamp"]).sort_values()
            if len(ts) < 2:
                continue
            mean_rate, cv, B = burstiness_from_timestamps(ts)
            rows.append({
                "modality": modality,
                "multiplier": float(k),
                "seed": seed,
                "n_events": len(ts),
                "B": B,
                "cv": cv,
                "mean_rate_per_hour": mean_rate,
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Verdicts
# --------------------------------------------------------------------------

def independent_verdict(df_a: pd.DataFrame) -> dict:
    """
    Direction-of-effect report on B vs n_sites per panel.

    Reports linear-regression slope, sign, and magnitude. We deliberately do NOT
    gate pass/fail on a single direction: the naive CLT prediction (more
    independent sites → B decreases) assumes truly independent processes.
    Real deployments often share temporal structure (shared diurnal, weather,
    cross-site animal movement) so a positive slope is itself a finding —
    "sites at this deployment are not independent in the CLT sense."
    """
    out = {"per_panel": []}
    if df_a.empty:
        return out
    for (m, sched), g in df_a.groupby(["modality", "schedule"], dropna=False):
        n_to_meanB = g.groupby("n_sites")["B"].mean().sort_index()
        if len(n_to_meanB) < 2:
            continue
        # Linear fit B ~ n_sites
        n = n_to_meanB.index.to_numpy(dtype=float)
        b = n_to_meanB.to_numpy(dtype=float)
        slope, intercept = np.polyfit(n, b, 1) if len(n) >= 2 else (float("nan"), float("nan"))
        if slope < -0.01:
            direction = "decreasing (CLT prediction holds — sites approximately independent)"
        elif slope > 0.01:
            direction = "increasing (sites share temporal structure — CLT does NOT apply)"
        else:
            direction = "approximately flat (sensor cadence dominates)"
        out["per_panel"].append({
            "modality": m,
            "schedule": sched,
            "n_sites_range": [int(n_to_meanB.index.min()), int(n_to_meanB.index.max())],
            "B_at_min_n": float(n_to_meanB.iloc[0]),
            "B_at_max_n": float(n_to_meanB.iloc[-1]),
            "delta_B": float(n_to_meanB.iloc[-1] - n_to_meanB.iloc[0]),
            "slope_per_site": float(slope),
            "direction": direction,
        })
    return out


def correlated_verdict(df_b: pd.DataFrame, b_tolerance: float = 0.05) -> dict:
    """Pass if B is preserved within tolerance across multipliers (engine-level prediction)."""
    out = {"per_modality": [], "n_pass": 0, "n_total": 0}
    if df_b.empty:
        return out
    for m, g in df_b.groupby("modality"):
        per_k = g.groupby("multiplier")["B"].mean()
        b_range = float(per_k.max() - per_k.min())
        passed = b_range <= b_tolerance
        out["per_modality"].append({
            "modality": m,
            "multipliers": sorted(per_k.index.tolist()),
            "B_min": float(per_k.min()),
            "B_max": float(per_k.max()),
            "B_range": b_range,
            "tolerance": b_tolerance,
            "pass": bool(passed),
        })
        out["n_total"] += 1
        if passed:
            out["n_pass"] += 1
    return out


# --------------------------------------------------------------------------
# Plot
# --------------------------------------------------------------------------

PANEL_COLORS = {
    "camera_trap": "#1f77b4",
    "bioacoustic|hourly": "#d62728",
    "bioacoustic|sunrise_sunset": "#ff7f0e",
    "drone": "#2ca02c",
    "citizen_science": "#9467bd",
}


def _panel_key(modality: str, schedule: str) -> str:
    if modality == "bioacoustic" and schedule:
        return f"{modality}|{schedule}"
    return modality


def make_figure(df_a: pd.DataFrame, df_b: pd.DataFrame, out_path: Path):
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11, 4.5))

    # Panel A: B vs n_sites
    if not df_a.empty:
        for (m, sched), g in df_a.groupby(["modality", "schedule"], dropna=False):
            key = _panel_key(m, sched)
            color = PANEL_COLORS.get(key, "gray")
            agg = g.groupby("n_sites")["B"].agg(["mean", "std"]).reset_index()
            ax_a.errorbar(
                agg["n_sites"], agg["mean"], yerr=agg["std"].fillna(0),
                marker="o", color=color, label=key, capsize=3,
            )
    ax_a.set_xlabel("n_sites (independent scaling)")
    ax_a.set_ylabel("Burstiness B")
    ax_a.set_title("A. Independent scaling: B vs site count")
    ax_a.axhline(0, color="gray", linewidth=0.5, linestyle=":")
    ax_a.grid(True, alpha=0.3)
    ax_a.legend(fontsize=8, loc="best")

    # Panel B: B vs intensity_multiplier
    if not df_b.empty:
        for m, g in df_b.groupby("modality"):
            color = PANEL_COLORS.get(m, "gray")
            agg = g.groupby("multiplier")["B"].agg(["mean", "std"]).reset_index()
            ax_b.errorbar(
                agg["multiplier"], agg["mean"], yerr=agg["std"].fillna(0),
                marker="s", color=color, label=m, capsize=3,
            )
    ax_b.set_xscale("log")
    ax_b.set_xlabel("intensity_multiplier (correlated scaling)")
    ax_b.set_ylabel("Burstiness B")
    ax_b.set_title("B. Correlated scaling: B vs density")
    ax_b.axhline(0, color="gray", linewidth=0.5, linestyle=":")
    ax_b.grid(True, alpha=0.3, which="both")
    ax_b.legend(fontsize=8, loc="best")

    fig.suptitle("Sensor-network topology scaling — extends Kline et al. 2024", fontsize=12)
    plt.tight_layout()
    for ext in ("png", "pdf"):
        p = out_path.with_suffix(f".{ext}")
        fig.savefig(p, dpi=150)
        log.info(f"  wrote {p}")
    plt.close(fig)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n-seeds", type=int, default=5,
                   help="Synthesis seeds per cell in panel B (default 5)")
    p.add_argument("--n-combos", type=int, default=10,
                   help="Max site combinations per n_sites in panel A (default 10)")
    p.add_argument("--duration-days", type=int, default=DEFAULT_DURATION_DAYS,
                   help="Synthesis horizon in days for panel B (default 25 = Campaign 2)")
    p.add_argument("--multipliers", type=float, nargs="+",
                   default=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
                   help="Intensity multipliers for panel B")
    args = p.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)

    # ---------------------------- Panel A: empirical ----------------------------
    log.info("Panel A: independent scaling (empirical from Campaign-2 timestamps)")
    a_dfs = []

    log.info("  camera_trap (5 sites, n in 1..5)")
    a_dfs.append(independent_scaling_empirical("camera_trap", n_combos_max=args.n_combos, rng=rng))

    log.info("  bioacoustic | hourly (split per §1a)")
    a_dfs.append(independent_scaling_empirical("bioacoustic", schedule_filter="hourly",
                                                n_combos_max=args.n_combos, rng=rng))

    log.info("  bioacoustic | sunrise_sunset")
    a_dfs.append(independent_scaling_empirical("bioacoustic", schedule_filter="sunrise_sunset",
                                                n_combos_max=args.n_combos, rng=rng))

    df_a = pd.concat([d for d in a_dfs if not d.empty], ignore_index=True) if a_dfs else pd.DataFrame()
    log.info(f"  panel A: {len(df_a)} rows")

    # ---------------------------- Panel B: synthesis ----------------------------
    log.info("Panel B: correlated scaling (synthesis with intensity_multiplier)")
    primitives_all = load_primitives(("camera_trap", "bioacoustic", "drone", "citizen_science"))
    bounds = load_independence_bounds()

    b_dfs = []
    for m in ("camera_trap", "bioacoustic", "drone", "citizen_science"):
        log.info(f"  {m} | multipliers={args.multipliers} | seeds={args.n_seeds}")
        b_dfs.append(correlated_scaling_synth(
            m, primitives_all,
            multipliers=tuple(args.multipliers),
            n_seeds=args.n_seeds,
            duration_seconds=args.duration_days * 86400.0,
            independence_bounds=bounds,
        ))
    df_b = pd.concat([d for d in b_dfs if not d.empty], ignore_index=True) if b_dfs else pd.DataFrame()
    log.info(f"  panel B: {len(df_b)} rows")

    # ---------------------------- Output ----------------------------
    df_a_tagged = df_a.assign(panel="A_independent") if not df_a.empty else df_a
    df_b_tagged = df_b.assign(panel="B_correlated") if not df_b.empty else df_b
    long = pd.concat([df_a_tagged, df_b_tagged], ignore_index=True)
    long.to_csv(OUT_DIR / "topology_scaling.csv", index=False)
    log.info(f"  wrote {OUT_DIR / 'topology_scaling.csv'}")

    verdict_a = independent_verdict(df_a)
    verdict_b = correlated_verdict(df_b)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_days": args.duration_days,
        "multipliers": list(args.multipliers),
        "n_seeds_panel_b": args.n_seeds,
        "n_combos_max_panel_a": args.n_combos,
        "panel_A_independent": verdict_a,
        "panel_B_correlated": verdict_b,
    }
    with open(OUT_DIR / "topology_scaling.json", "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"  wrote {OUT_DIR / 'topology_scaling.json'}")

    make_figure(df_a, df_b, OUT_DIR / "topology_scaling")

    # Console summary
    print("\n=== Panel A (independent scaling, empirical) ===")
    for v in verdict_a["per_panel"]:
        print(f"  {v['modality']:14s}|{v['schedule']:18s}  n {v['n_sites_range']}  "
              f"B {v['B_at_min_n']:+.3f}→{v['B_at_max_n']:+.3f}  ΔB={v['delta_B']:+.3f}  "
              f"slope={v['slope_per_site']:+.3f}/site")
        print(f"    → {v['direction']}")

    print("\n=== Panel B (correlated scaling, synthesis) ===")
    for v in verdict_b["per_modality"]:
        print(f"  {v['modality']:18s}  B range [{v['B_min']:.3f}, {v['B_max']:.3f}]  "
              f"width {v['B_range']:.3f} (tol {v['tolerance']})  "
              f"{'PASS' if v['pass'] else 'FAIL'}")
    print(f"  Overall: {verdict_b['n_pass']}/{verdict_b['n_total']} modalities preserve B under rate scaling")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
