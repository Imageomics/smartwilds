"""
CS3 — Focal CT → CT network (10s SLO).

Pattern (mosaic_execution_plan_v2 §3, CS3 row): synthesize multi-site CT
traces under corridor-movement assumption: detection at site S_i raises
trigger probability at adjacent S_{i±1} within a 10s window. Multi-node
coordination + propagation under network constraints is what's exercised.

v1 implementation note. The synthesize() core does not yet have site-aware
combinator logic — `conditional_scale` filters by modality, not by adjacent-
site relationships. CS3 currently produces a same-modality conditional scale:
within 10s of any CT detection, additional CT events are duplicated (intensity
boost), which exercises the multi-node story at the trace level but does NOT
yet carry the corridor-adjacency semantics. A follow-up extension will plumb
adjacency through the combinator.

Until then, downstream consumers should treat CS3 as the "CT-network burst
intensity" case study, with adjacency promoted to future work in §VI.B.
"""

from __future__ import annotations

import sys
from pathlib import Path

THIS = Path(__file__).resolve()
ROOT = THIS.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from base_recipe import DEFAULT_DURATION_SECONDS, CaseStudy

SYNTH_DIR = THIS.parents[2] / "exp6_1_synthesis"
if str(SYNTH_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTH_DIR))

from schemas import Recipe, SLOEdge  # noqa: E402

NAME = "CS3_focal_ct_network"
NETWORK_PROPAGATION_WINDOW_SECONDS = 10.0
NEIGHBOR_DENSITY_BOOST = 1.5  # corridor-movement raises adjacent-site probability


def build(
    intensity_multiplier: float = 1.0,
    duration_seconds: float = DEFAULT_DURATION_SECONDS,
    seed: int = 3,
) -> CaseStudy:
    recipe = Recipe(
        modality_mix=("camera_trap",),
        combinator="conditional_scale",
        duration_seconds=duration_seconds,
        density={"camera_trap": NEIGHBOR_DENSITY_BOOST},
        intensity_multiplier=intensity_multiplier,
        slo_chain=(
            SLOEdge(
                trigger="camera_trap",
                response="camera_trap",
                latency_budget_seconds=NETWORK_PROPAGATION_WINDOW_SECONDS,
            ),
        ),
        seed=seed,
        name=f"{NAME}_{intensity_multiplier:g}x",
    )
    return CaseStudy(
        name=NAME,
        description="Focal CT detection → adjacent CT activation in 10s. Multi-node coordination under corridor-movement assumption (adjacency stub: per-modality scaling pending site-aware combinator).",
        recipe=recipe,
        slo_compliance_seconds=NETWORK_PROPAGATION_WINDOW_SECONDS,
    )
