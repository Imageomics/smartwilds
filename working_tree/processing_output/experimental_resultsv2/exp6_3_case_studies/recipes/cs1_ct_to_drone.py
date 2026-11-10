"""
CS1 — Camera trap → Drone (5s SLO).

Pattern (mosaic_execution_plan_v2 §3, CS1 row): CT motion-trigger bursts from
high-activity sites concatenated with drone flight windows keyed to detections;
drone events synthesized as response traces within 5s of CT detection.

Synthesis maps cleanly to `interleave`: baseline CT + drone draws from the
fitted rate models, then for every CT trigger we insert one drone response
event at a uniform offset in [0.1, 5.0] seconds. Burst response under cross-
modal trigger is the systems property exercised.
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

NAME = "CS1_ct_to_drone"
SLO_SECONDS = 5.0


def build(
    intensity_multiplier: float = 1.0,
    duration_seconds: float = DEFAULT_DURATION_SECONDS,
    seed: int = 1,
) -> CaseStudy:
    recipe = Recipe(
        modality_mix=("camera_trap", "drone"),
        combinator="interleave",
        duration_seconds=duration_seconds,
        density={},
        intensity_multiplier=intensity_multiplier,
        slo_chain=(SLOEdge(trigger="camera_trap", response="drone", latency_budget_seconds=SLO_SECONDS),),
        seed=seed,
        name=f"{NAME}_{intensity_multiplier:g}x",
    )
    return CaseStudy(
        name=NAME,
        description="Camera trap motion trigger → drone dispatch within 5s. Burst response under cross-modal trigger.",
        recipe=recipe,
        slo_compliance_seconds=SLO_SECONDS,
    )
