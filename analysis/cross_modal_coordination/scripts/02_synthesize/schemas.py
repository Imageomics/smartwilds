"""
schemas.py — Exp 6.1 synthesis engine: type definitions.

Recipe describes *what to synthesize* (modality mix, intensity, combinator choice,
SLO chain). EventLog is the unified output schema consumed by the Exp 4 replay
harness; it matches the v1 timestamps_combined.csv schema so downstream tooling
works without modification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

CombinatorName = Literal["concatenate", "interleave", "conditional_scale", "prior_inject"]
ModalityName = Literal["camera_trap", "bioacoustic", "drone", "citizen_science"]


@dataclass(frozen=True)
class SLOEdge:
    """One cross-modal trigger → response edge in an SLO chain."""
    trigger: ModalityName
    response: ModalityName
    latency_budget_seconds: float


@dataclass(frozen=True)
class Recipe:
    """
    Self-describing synthesis configuration. Deterministic given seed.

    modality_mix: which modalities to include in the output event log. An
        empty list is invalid; use the identity recipe (all four) for sanity
        testing.
    density: per-modality density multiplier applied on top of the fitted
        baseline rate. Keys are modality names; missing keys default to 1.0.
    intensity_multiplier: global scale factor across all modalities (used by
        Exp 6.4 scaling sweeps). Stacks with density.
    combinator: which trace-combining function is invoked after per-modality
        Poisson draws. See combinators.py.
    slo_chain: ordered list of trigger→response edges used by the conditional_
        scale combinator and by the downstream replay harness for SLO checks.
    duration_seconds: total synthesis horizon. Rates are applied across this
        window; diurnal structure from primitives is preserved.
    seed: RNG seed. Two runs with the same recipe + seed produce identical
        event logs (load-bearing for fidelity comparisons).
    """
    modality_mix: tuple[ModalityName, ...]
    combinator: CombinatorName
    duration_seconds: float
    density: dict[ModalityName, float] = field(default_factory=dict)
    intensity_multiplier: float = 1.0
    slo_chain: tuple[SLOEdge, ...] = ()
    seed: int = 0
    name: str = "unnamed"

    def density_for(self, modality: ModalityName) -> float:
        return float(self.density.get(modality, 1.0)) * float(self.intensity_multiplier)


# Unified event log schema. Matches v1 timestamps_combined.csv.
# The synthesize() function returns a pandas DataFrame with these columns.
EVENT_LOG_COLUMNS: tuple[str, ...] = (
    "timestamp",      # pd.Timestamp (UTC)
    "modality",       # ModalityName
    "site",           # TW##-CT## for camera, TW## for acoustics, mission_id for drones, "unknown" for citsci
    "source_file",    # provenance string; "synthetic:<recipe.name>:<step>" for synthesized events
    "confidence",     # optional [0,1] confidence; NaN if not applicable
    "recipe_step",    # which combinator step produced this event (for debugging)
)


def identity_recipe(duration_seconds: float, seed: int = 0) -> Recipe:
    """Recipe that should reproduce recorded-trace statistics. Used by identity_test."""
    return Recipe(
        modality_mix=("camera_trap", "bioacoustic", "drone", "citizen_science"),
        combinator="concatenate",
        duration_seconds=duration_seconds,
        density={},
        intensity_multiplier=1.0,
        slo_chain=(),
        seed=seed,
        name="identity",
    )
