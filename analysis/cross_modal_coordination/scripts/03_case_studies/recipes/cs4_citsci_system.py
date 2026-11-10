"""
CS4 — Citizen science → all modalities (60s SLO).

Pattern (execution plan v2 §3, CS4 row): citizen-science events as
sampling priors. Scale all modality rates conditional on citsci-active vs.
idle periods. Operates at hour-level granularity. System-wide adaptive
response; slowest-cadence trigger.

Implementation. `prior_inject` combinator (currently a thin wrapper over
`conditional_scale`) duplicates response-modality events that fall inside the
prior window of any citsci event. Density on each response modality controls
the boost factor.

Boost rationale. Citsci events are visitor-driven and typically correlate
with daytime windows when other sensors should already see elevated activity.
A 1.25x boost is conservative (we are *biasing* sampling priority, not
asserting visitors cause wildlife to appear).
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

NAME = "CS4_citsci_system"
PRIOR_WINDOW_SECONDS = 60.0
RESPONSE_DENSITY_BOOST = 1.25


def build(
    intensity_multiplier: float = 1.0,
    duration_seconds: float = DEFAULT_DURATION_SECONDS,
    seed: int = 4,
) -> CaseStudy:
    response_modalities = ("camera_trap", "bioacoustic", "drone")
    recipe = Recipe(
        modality_mix=("citizen_science",) + response_modalities,
        combinator="prior_inject",
        duration_seconds=duration_seconds,
        density={m: RESPONSE_DENSITY_BOOST for m in response_modalities},
        intensity_multiplier=intensity_multiplier,
        slo_chain=tuple(
            SLOEdge(trigger="citizen_science", response=m, latency_budget_seconds=PRIOR_WINDOW_SECONDS)
            for m in response_modalities
        ),
        seed=seed,
        name=f"{NAME}_{intensity_multiplier:g}x",
    )
    return CaseStudy(
        name=NAME,
        description="Citsci event → 60s prior window scaling sampling priority on all sensor modalities. System-wide adaptive response.",
        recipe=recipe,
        slo_compliance_seconds=PRIOR_WINDOW_SECONDS,
    )
