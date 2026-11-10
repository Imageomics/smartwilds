"""
fidelity_metrics.py — shared metric implementations for Exp 6.2.A / 6.2.B / 6.4.

Single source of truth for the five fidelity metrics in execution plan §Exp 6.2.A:

    burstiness_B          — |B_synth − B_real|               threshold 0.05
    cv_relative           — |CV_synth − CV_real| / CV_real    threshold 0.15
    diurnal_ks            — KS distance on hour-of-day dist   threshold 0.15
    independence_delta    — |J_synth − J_real| at 24h Jaccard threshold 0.05
    post_filter_rate_rel  — |r_synth − r_real| / r_real       threshold 0.20 (CT only)

Plus the helper computations that feed these (B, CV, diurnal profile).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

# Canonical thresholds (execution plan §Exp 6.2.A)
THRESHOLDS = {
    "burstiness_B": 0.05,
    "cv_relative": 0.15,
    "diurnal_ks": 0.15,
    "independence_delta": 0.05,
    "post_filter_rate_rel": 0.20,
}


def burstiness_from_timestamps(ts: pd.Series) -> tuple[float, float, float]:
    """
    Return (mean_rate_per_hour, cv, burstiness_B) from a timestamp series.
    Returns zeros for degenerate input (<2 events or zero-span).
    """
    if len(ts) < 2:
        return 0.0, 0.0, 0.0
    iat = pd.to_datetime(ts).sort_values().diff().dt.total_seconds().dropna()
    iat = iat[iat > 0]
    if len(iat) == 0:
        return 0.0, 0.0, 0.0
    mean_iat = iat.mean()
    std_iat = iat.std()
    mean_rate = 3600.0 / mean_iat if mean_iat > 0 else 0.0
    cv = std_iat / mean_iat if mean_iat > 0 else 0.0
    B = (cv - 1) / (cv + 1) if (cv + 1) > 0 else 0.0
    return float(mean_rate), float(cv), float(B)


def diurnal_profile(ts: pd.Series) -> np.ndarray:
    """Mean events-per-hour-of-day, normalized by days covered. 24-element array."""
    if len(ts) == 0:
        return np.zeros(24)
    ts = pd.to_datetime(ts)
    hours = ts.dt.hour
    counts = hours.value_counts().reindex(range(24), fill_value=0).sort_index()
    n_days = max(1.0, (ts.max() - ts.min()).total_seconds() / 86400.0)
    return (counts.values / n_days).astype(float)


def diurnal_ks_distance(ts_a: pd.Series, ts_b: pd.Series) -> float:
    """KS distance between two hour-of-day distributions."""
    if len(ts_a) < 2 or len(ts_b) < 2:
        return float("nan")
    h_a = pd.to_datetime(ts_a).dt.hour.values.astype(float)
    h_b = pd.to_datetime(ts_b).dt.hour.values.astype(float)
    return float(ks_2samp(h_a, h_b).statistic)


def burstiness_delta(B_real: float, B_synth: float) -> float:
    return abs(B_synth - B_real)


def cv_relative_delta(cv_real: float, cv_synth: float) -> float:
    return abs(cv_synth - cv_real) / cv_real if cv_real > 0 else float("inf")


def evaluate(real_ts: pd.Series, synth_ts: pd.Series) -> dict:
    """
    Full metric battery on real vs synth timestamp series.
    Missing metrics (independence, post_filter_rate) return None — caller
    supplies them from domain-specific inputs.
    """
    _, cv_r, B_r = burstiness_from_timestamps(real_ts)
    _, cv_s, B_s = burstiness_from_timestamps(synth_ts)
    return {
        "burstiness_B_real": B_r,
        "burstiness_B_synth": B_s,
        "burstiness_delta": burstiness_delta(B_r, B_s),
        "cv_real": cv_r,
        "cv_synth": cv_s,
        "cv_relative_delta": cv_relative_delta(cv_r, cv_s),
        "diurnal_ks": diurnal_ks_distance(real_ts, synth_ts),
    }


def verdict(metrics: dict) -> dict[str, bool]:
    """Return pass/fail per metric given the canonical thresholds."""
    out = {}
    out["burstiness_B"] = metrics.get("burstiness_delta", float("inf")) <= THRESHOLDS["burstiness_B"]
    out["cv_relative"] = metrics.get("cv_relative_delta", float("inf")) <= THRESHOLDS["cv_relative"]
    ks = metrics.get("diurnal_ks", float("inf"))
    out["diurnal_ks"] = (not np.isnan(ks)) and (ks <= THRESHOLDS["diurnal_ks"])
    return out
