"""
CS2 — Acoustic → Camera trap sensitivity-raise (60s window, 2s response SLO).

Pattern (execution plan v2 §3, CS2 row): BirdNET high-confidence
acoustic detections interleaved with CT sensitivity-raised response windows.
Recipe simulates CT trigger rate doubling for 60s after each acoustic
detection. Fine-grained trigger latency / state-change propagation is what
the systems harness exercises; the systems-level SLO for the trigger →
sensitivity-raise transition is 2s.

Two distinct durations live here:
    - synthesis_window = 60s  — how long the doubled rate stays in effect.
                                Encoded in the SLOEdge.latency_budget_seconds
                                because that is what `conditional_scale`
                                consumes when picking response events to
                                duplicate.
    - slo_compliance   =  2s  — what the replay harness checks. Carried on
                                the CaseStudy wrapper, not the Recipe.

The synth-vs-SLO split is intentional and documented in base_recipe.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

THIS = Path(__file__).resolve()
ROOT = THIS.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from base_recipe import DEFAULT_DURATION_SECONDS, CaseStudy

SYNTH_DIR = THIS.parents[2] / "02_synthesize"
if str(SYNTH_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTH_DIR))

from schemas import Recipe, SLOEdge  # noqa: E402

NAME = "CS2_acoustic_to_ct"
SYNTHESIS_WINDOW_SECONDS = 60.0
SLO_SECONDS = 2.0
CT_DENSITY_BOOST = 2.0  # "doubling" per execution plan


def build(
    intensity_multiplier: float = 1.0,
    duration_seconds: float = DEFAULT_DURATION_SECONDS,
    seed: int = 2,
) -> CaseStudy:
    recipe = Recipe(
        modality_mix=("bioacoustic", "camera_trap"),
        combinator="conditional_scale",
        duration_seconds=duration_seconds,
        # Density on the RESPONSE modality (CT) drives how many extra events
        # conditional_scale duplicates inside each acoustic-trigger window.
        density={"camera_trap": CT_DENSITY_BOOST},
        intensity_multiplier=intensity_multiplier,
        slo_chain=(
            SLOEdge(
                trigger="bioacoustic",
                response="camera_trap",
                latency_budget_seconds=SYNTHESIS_WINDOW_SECONDS,
            ),
        ),
        seed=seed,
        name=f"{NAME}_{intensity_multiplier:g}x",
    )
    return CaseStudy(
        name=NAME,
        description="Acoustic high-confidence detection raises CT sensitivity (2x rate) for 60s; SLO for the trigger transition is 2s.",
        recipe=recipe,
        slo_compliance_seconds=SLO_SECONDS,
    )
