"""
synthesize.py — Exp 6.1 core synthesis engine.

    synthesize(recipe, primitives, independence_bounds) → EventLog

Pipeline (matches execution plan §Exp 6.1):

    1. Load per-modality rate models, diurnal profiles, per-site variances
       from Exp 1 primitives JSON.
    2. Load independence bounds from Exp 2.A (at what scale can modalities
       be treated as independent?)
    3. Parse recipe: modality mix, density, intensity, combinator, SLO chain.
    4. For each modality in mix: draw Poisson realizations using the fitted
       rate model, scaled by density × intensity. Preserve diurnal structure.
    5. Apply combinator (concatenate / interleave / conditional_scale /
       prior_inject) to produce unified event log.
    6. Return DataFrame with EVENT_LOG_COLUMNS schema — same as recorded
       traces, so downstream tooling (replay engine, feasibility grid)
       consumes synthesized and recorded traces interchangeably.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from combinators import get as get_combinator
from schemas import EVENT_LOG_COLUMNS, Recipe

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
PRIMITIVES_DIR = BASE_DIR / "processing_output" / "experimental_resultsv2" / "exp1_characterization" / "primitives"
INDEPENDENCE_DIR = BASE_DIR / "processing_output" / "experimental_results" / "exp2_cross_modal_event_correlation"

log = logging.getLogger(__name__)


def load_primitives(modalities: tuple[str, ...]) -> dict[str, dict]:
    """Load per-modality primitives JSON written by exp1_characterization/export_primitives.py."""
    out = {}
    for m in modalities:
        path = PRIMITIVES_DIR / f"{m}.json"
        if not path.exists():
            raise FileNotFoundError(f"Primitives JSON not found: {path}. Run export_primitives.py first.")
        with open(path) as f:
            out[m] = json.load(f)
    return out


def load_independence_bounds(window_hours: int = 24) -> pd.DataFrame:
    """Load Jaccard cross-modal matrix at given window; returns NaN-filled if not present."""
    path = INDEPENDENCE_DIR / f"{window_hours}h" / f"correlation_matrix_{window_hours}h.csv"
    if not path.exists():
        # Fallback: v1 aggregate output
        alt = BASE_DIR / "processing_output" / "experimental_results" / "exp1_cross_modal_arrival_rates" / "results" / f"cross_modal_correlation_{window_hours}h.csv"
        if alt.exists():
            return pd.read_csv(alt, index_col=0)
        log.warning(f"Independence bounds not found at {path} or {alt}; synthesis will assume full independence")
        return pd.DataFrame()
    return pd.read_csv(path, index_col=0)


CHANGE_POINT_THRESHOLD = "0.99"  # which significance level to use from rate_model


def _draw_from_change_points(
    change_points: list[list[float]],
    horizon_seconds: float,
    multiplier: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Sample event times from a piecewise-constant λ(t) defined by change points.

    change_points is a sorted list of (t_seconds, rate_per_sec) pairs. Each
    pair opens a segment whose rate r_i applies until the next change point.
    The segments naturally encode burstiness — real traces alternate long
    low-rate gaps with dense high-rate bursts — so sampling per-segment
    reproduces the arrival-process burstiness that a flat rate + diurnal
    modulation discards.

    Horizons beyond the recorded change-point span cap at t_max rather than
    tiling. Tiling inflated counts disproportionately when early segments
    contained dense bursts (drone missions concentrated at the start of the
    rate function); any longer-than-recorded horizon should be produced by
    recipe-level density/intensity scaling, not by replaying the rate
    function verbatim.
    """
    pts = sorted(change_points, key=lambda p: p[0])
    times = np.asarray([p[0] for p in pts], dtype=float)
    rates = np.asarray([p[1] for p in pts], dtype=float) * multiplier
    t_max = float(times[-1]) if len(times) else 0.0
    if t_max <= 0 or horizon_seconds <= 0 or len(times) < 2:
        return np.asarray([], dtype=float)

    effective_horizon = min(horizon_seconds, t_max)
    seg_starts = times[:-1]
    seg_ends = np.minimum(times[1:], effective_horizon)
    widths = np.maximum(seg_ends - seg_starts, 0.0)
    seg_rates = rates[:-1]
    active = (widths > 0) & (seg_rates > 0) & (seg_starts < effective_horizon)
    if not active.any():
        return np.asarray([], dtype=float)

    expected = seg_rates[active] * widths[active]
    counts = rng.poisson(expected)
    if counts.sum() == 0:
        return np.asarray([], dtype=float)

    drawn: list[np.ndarray] = []
    for a, b, n in zip(seg_starts[active], seg_ends[active], counts):
        if n > 0:
            drawn.append(rng.uniform(a, b, size=n))
    return np.sort(np.concatenate(drawn)) if drawn else np.asarray([], dtype=float)


def _draw_from_timestamp_bootstrap(
    modality: str,
    horizon_seconds: float,
    multiplier: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Fallback for sparse modalities whose change-point rate model is too coarse
    to reproduce arrival burstiness (bioacoustic: ~90 segments / 1714 events;
    citizen_science: 1 segment / 991 events).

    Samples recorded timestamps with replacement at a density set by the
    recipe multiplier and the ratio horizon / recorded_span. Preserves both
    the inter-arrival burstiness AND the hour-of-day structure — IAT-only
    bootstrap scrambled diurnal alignment because it accumulated gaps in
    random order, detaching visitor or schedule-concentrated events from
    their real time-of-day.
    """
    ts_file = BASE_DIR / "processing_output" / "experimental_results" / "exp1_cross_modal_arrival_rates" / "results" / f"timestamps_{modality}.csv"
    if not ts_file.exists():
        return np.asarray([], dtype=float)
    df = pd.read_csv(ts_file, usecols=["timestamp"])
    ts = pd.to_datetime(df["timestamp"], format="ISO8601", errors="coerce").dropna().sort_values()
    if len(ts) < 2:
        return np.asarray([], dtype=float)

    t_start = ts.iloc[0]
    t_end = ts.iloc[-1]
    recorded_span = (t_end - t_start).total_seconds()
    if recorded_span <= 0 or multiplier <= 0 or horizon_seconds <= 0:
        return np.asarray([], dtype=float)

    seconds = (ts - t_start).dt.total_seconds().to_numpy()

    expected_n = int(round(multiplier * len(seconds) * horizon_seconds / recorded_span))
    if expected_n <= 0:
        return np.asarray([], dtype=float)
    # Poisson the draw size so the number of events isn't deterministic —
    # otherwise the variance envelope collapses to zero for these modalities
    # and every seed produces an identical count, breaking 6.2.A.
    n = int(rng.poisson(expected_n))
    if n == 0:
        return np.asarray([], dtype=float)

    # Bootstrap timestamps from recorded pool. Each draw lands in
    # [0, recorded_span]; events beyond horizon are discarded (a single
    # scaling of time axis would skew diurnal; truncation preserves it).
    drawn = rng.choice(seconds, size=n, replace=True)
    drawn = drawn[drawn < horizon_seconds]
    return np.sort(drawn)


def _draw_from_flat_rate(
    modality_primitives: dict,
    horizon_seconds: float,
    multiplier: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Fallback: homogeneous Poisson modulated by diurnal profile (no burstiness)."""
    agg = modality_primitives["aggregate"]
    base_rate_per_sec = agg["mean_rate_per_hour"] / 3600.0
    diurnal = np.asarray(agg["diurnal_profile"], dtype=float)
    diurnal_norm = diurnal / diurnal.mean() if diurnal.sum() > 0 else np.ones(24)

    effective = base_rate_per_sec * multiplier
    if effective <= 0 or horizon_seconds <= 0:
        return np.asarray([], dtype=float)

    max_diurnal = diurnal_norm.max() if diurnal_norm.max() > 0 else 1.0
    n_candidates = rng.poisson(effective * horizon_seconds * max_diurnal)
    if n_candidates == 0:
        return np.asarray([], dtype=float)

    cand_t = rng.uniform(0.0, horizon_seconds, size=n_candidates)
    hours = ((cand_t / 3600.0).astype(int)) % 24
    p_accept = diurnal_norm[hours] / max_diurnal
    accept = rng.uniform(0.0, 1.0, size=n_candidates) < p_accept
    return np.sort(cand_t[accept])


BOOTSTRAP_IAT_MODALITIES = ("bioacoustic", "citizen_science")


def _draw_modality_stream(
    modality: str,
    modality_primitives: dict,
    recipe: Recipe,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Draw one modality's event stream. Uses the piecewise-constant change-point
    rate model for CT/drone (rich rate resolution captures burstiness). For
    bioacoustic / citizen_science, the change-point detector sees only ~90
    and 1 segments respectively — far too coarse to express the sub-segment
    clustering that drives their real burstiness (scheduled ARU windows;
    visitor-event concentration). Those modalities bootstrap inter-arrival
    times from the recorded timestamps file instead.
    """
    multiplier = recipe.density_for(modality)
    duration = recipe.duration_seconds

    if modality in BOOTSTRAP_IAT_MODALITIES:
        times = _draw_from_timestamp_bootstrap(modality, duration, multiplier, rng)
    else:
        rate_model = modality_primitives.get("rate_model", {})
        cps = rate_model.get("change_points", {}).get(CHANGE_POINT_THRESHOLD, [])
        if len(cps) >= 2:
            times = _draw_from_change_points(cps, duration, multiplier, rng)
        else:
            times = _draw_from_flat_rate(modality_primitives, duration, multiplier, rng)

    if len(times) == 0:
        return pd.DataFrame({c: [] for c in EVENT_LOG_COLUMNS})

    # Assign sites by sampling from per_site distribution weighted by n_events
    per_site = modality_primitives.get("per_site_variance", [])
    if per_site:
        sites = [s["site"] for s in per_site]
        weights = np.asarray([s["n_events"] for s in per_site], dtype=float)
        weights = weights / weights.sum() if weights.sum() > 0 else None
        assigned = rng.choice(sites, size=len(times), p=weights)
    else:
        assigned = np.full(len(times), "unknown")

    # Anchor at the modality's recorded start so hour-of-day aligns with the
    # rate model. Uniform-across-modalities anchors produced hour offsets that
    # pushed drone mission bursts (which happen mid-morning in the field) into
    # the wrong hour-of-day, inflating the diurnal KS distance by ~8 hours.
    date_range = modality_primitives.get("date_range") or []
    if date_range and date_range[0]:
        t0 = pd.Timestamp(date_range[0])
    else:
        t0 = pd.Timestamp("2025-07-01")
    return pd.DataFrame({
        "timestamp": t0 + pd.to_timedelta(times, unit="s"),
        "modality": modality,
        "site": assigned,
        "source_file": f"synthetic:{recipe.name}:{modality}",
        "confidence": np.nan,
        "recipe_step": "draw_modality_stream",
    })


def synthesize(
    recipe: Recipe,
    primitives: dict[str, dict] | None = None,
    independence_bounds: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Produce a synthesized event log for the given recipe.

    Deterministic given recipe.seed. Returns a DataFrame with EVENT_LOG_COLUMNS.
    """
    if primitives is None:
        primitives = load_primitives(recipe.modality_mix)
    if independence_bounds is None:
        independence_bounds = load_independence_bounds()

    # Independence bounds are currently advisory — logged for provenance,
    # not enforced by the combinator (combinator's correlated-stream logic is
    # driven by the SLO chain, not by the independence matrix).
    if not independence_bounds.empty:
        log.debug(f"Using independence bounds (shape={independence_bounds.shape})")

    rng = np.random.default_rng(recipe.seed)

    streams: dict[str, pd.DataFrame] = {}
    for m in recipe.modality_mix:
        streams[m] = _draw_modality_stream(m, primitives[m], recipe, rng)
        log.info(f"  drew {len(streams[m])} {m} events")

    combinator = get_combinator(recipe.combinator)
    event_log = combinator(streams, recipe, rng)

    # Schema conformance
    for c in EVENT_LOG_COLUMNS:
        if c not in event_log.columns:
            event_log[c] = pd.NA
    event_log = event_log[list(EVENT_LOG_COLUMNS)]
    return event_log.reset_index(drop=True)
