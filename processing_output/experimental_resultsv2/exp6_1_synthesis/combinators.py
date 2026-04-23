"""
combinators.py — Exp 6.1 synthesis engine: trace combinators.

Four combinators compose per-modality Poisson draws into a unified event log:

    concatenate       union of independent streams (identity default)
    interleave        union + guaranteed response events within SLO latency
                      of each trigger detection
    conditional_scale trigger fires → response modality rate multiplied for
                      a window (models sensitivity-raising, e.g. CS2)
    prior_inject      inject a prior-modality stream whose events reshape the
                      rate of other modalities for surrounding windows

Each combinator has the same signature:
    fn(streams: dict[modality, DataFrame], recipe: Recipe, rng: np.random.Generator) -> DataFrame

Inputs arrive pre-drawn from synthesize.py. Combinators are responsible only
for the merge logic. This keeps per-modality Poisson drawing in one place.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from schemas import EVENT_LOG_COLUMNS, Recipe


CombinatorFn = Callable[[dict[str, pd.DataFrame], Recipe, np.random.Generator], pd.DataFrame]


def _empty_log() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object") for c in EVENT_LOG_COLUMNS})


def _stamp_step(df: pd.DataFrame, step: str) -> pd.DataFrame:
    df = df.copy()
    df["recipe_step"] = step
    return df


def concatenate(streams: dict[str, pd.DataFrame], recipe: Recipe, rng: np.random.Generator) -> pd.DataFrame:
    """Union of all streams, sorted by timestamp. Identity default — no inter-stream coupling."""
    parts = [_stamp_step(df, "concatenate") for df in streams.values() if len(df)]
    if not parts:
        return _empty_log()
    out = pd.concat(parts, ignore_index=True)
    return out.sort_values("timestamp").reset_index(drop=True)


def interleave(streams: dict[str, pd.DataFrame], recipe: Recipe, rng: np.random.Generator) -> pd.DataFrame:
    """
    Concatenate baseline streams, then ensure every SLO-chain trigger detection
    has a response event within its latency budget. Response events are drawn
    from the response modality's rate model around the trigger time.

    Case study CS1 (CT→Drone, 5s) is the canonical user of this combinator.
    """
    out = concatenate(streams, recipe, rng)
    for edge in recipe.slo_chain:
        trig = out[out["modality"] == edge.trigger]
        if trig.empty:
            continue
        # For each trigger, insert one response event within [0, latency_budget]
        offsets = rng.uniform(0.1, edge.latency_budget_seconds, size=len(trig))
        response_ts = pd.to_datetime(trig["timestamp"].values) + pd.to_timedelta(offsets, unit="s")
        # Inherit site from trigger; response modality name from edge
        resp = pd.DataFrame({
            "timestamp": response_ts,
            "modality": edge.response,
            "site": trig["site"].values,
            "source_file": [f"synthetic:{recipe.name}:interleave({edge.trigger}→{edge.response})"] * len(trig),
            "confidence": np.nan,
            "recipe_step": f"interleave({edge.trigger}→{edge.response})",
        })
        out = pd.concat([out, resp], ignore_index=True)
    return out.sort_values("timestamp").reset_index(drop=True)


def conditional_scale(
    streams: dict[str, pd.DataFrame], recipe: Recipe, rng: np.random.Generator
) -> pd.DataFrame:
    """
    After a trigger fires, multiply the response modality's rate inside a
    latency-budget window (models CS2: acoustic → CT sensitivity doubled for 60s).

    Implementation: take the response stream's events that fall in any trigger
    window, duplicate them with a jittered offset scaled by (density-1), then
    merge.
    """
    out = concatenate(streams, recipe, rng)
    for edge in recipe.slo_chain:
        trig = out[out["modality"] == edge.trigger]
        resp_mask = out["modality"] == edge.response
        if trig.empty or not resp_mask.any():
            continue
        window_ns = int(edge.latency_budget_seconds * 1e9)
        resp = out[resp_mask].copy()
        # Work in int64 nanoseconds throughout to avoid object-dtype demotion
        # from np.where's mixed Timedelta/scalar branches (a real footgun).
        trig_ns = np.asarray(pd.to_datetime(trig["timestamp"].values), dtype="datetime64[ns]").view("int64")
        resp_ns = np.asarray(pd.to_datetime(resp["timestamp"].values), dtype="datetime64[ns]").view("int64")
        trig_ns = np.sort(trig_ns)
        idx = np.searchsorted(trig_ns, resp_ns)
        SENTINEL = np.iinfo(np.int64).max
        left_idx = np.clip(idx - 1, 0, len(trig_ns) - 1)
        right_idx = np.clip(idx, 0, len(trig_ns) - 1)
        left = np.where(idx > 0, resp_ns - trig_ns[left_idx], SENTINEL)
        right = np.where(idx < len(trig_ns), trig_ns[right_idx] - resp_ns, SENTINEL)
        nearest = np.minimum(left, right)
        in_window = nearest <= window_ns
        scaled = resp[in_window].copy()
        density = recipe.density_for(edge.response)
        n_extra = max(0, int(round((density - 1.0) * len(scaled))))
        if n_extra and len(scaled):
            chosen = scaled.sample(n=n_extra, replace=True, random_state=int(rng.integers(0, 2**31)))
            jitter = rng.uniform(-edge.latency_budget_seconds / 2, edge.latency_budget_seconds / 2, size=n_extra)
            chosen = chosen.copy()
            chosen["timestamp"] = pd.to_datetime(chosen["timestamp"]) + pd.to_timedelta(jitter, unit="s")
            chosen["source_file"] = f"synthetic:{recipe.name}:conditional_scale({edge.trigger}→{edge.response})"
            chosen["recipe_step"] = f"conditional_scale({edge.trigger}→{edge.response})"
            out = pd.concat([out, chosen], ignore_index=True)
    return out.sort_values("timestamp").reset_index(drop=True)


def prior_inject(streams: dict[str, pd.DataFrame], recipe: Recipe, rng: np.random.Generator) -> pd.DataFrame:
    """
    CS4 pattern. Citizen-science events act as priors that reshape other
    modalities' rates inside the following latency window.
    For v1 we implement the simplest possible version: concatenate, then
    for each prior-modality event, scale all other modalities' rates inside
    the window by recipe.density_for(target_modality).

    TODO: tighten once CS4 recipe parameters are finalized.
    """
    return conditional_scale(streams, recipe, rng)


REGISTRY: dict[str, CombinatorFn] = {
    "concatenate": concatenate,
    "interleave": interleave,
    "conditional_scale": conditional_scale,
    "prior_inject": prior_inject,
}


def get(name: str) -> CombinatorFn:
    if name not in REGISTRY:
        raise KeyError(f"Unknown combinator: {name}. Known: {sorted(REGISTRY)}")
    return REGISTRY[name]
