"""
base_recipe.py — Exp 6.3 case study library: shared scaffolding.

A case study is a *recipe*, not a trace (execution plan v2 §3). Each CS
module exports `build(intensity_multiplier, duration_seconds, seed) -> CaseStudy`.

CaseStudy bundles the synthesis Recipe with two extras the bare Recipe can't
carry on its own:

    slo_compliance_seconds  — the systems-level SLO that the *replay harness*
                              checks. Distinct from any window the synthesis
                              combinator uses internally (e.g. CS2: 60s
                              sensitivity window, 2s response SLO).
    description             — one-line provenance string for figures/tables.

Keeping these on CaseStudy rather than extending SLOEdge avoids a schema change
to the synthesis core for what is, fundamentally, downstream metadata.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

THIS = Path(__file__).resolve()
SYNTH_DIR = THIS.parents[1] / "02_synthesize"
if str(SYNTH_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTH_DIR))

from schemas import Recipe  # noqa: E402


@dataclass(frozen=True)
class CaseStudy:
    name: str
    description: str
    recipe: Recipe
    slo_compliance_seconds: float

    def __post_init__(self):
        if self.slo_compliance_seconds <= 0:
            raise ValueError(f"slo_compliance_seconds must be positive, got {self.slo_compliance_seconds}")
        if not self.recipe.modality_mix:
            raise ValueError("recipe.modality_mix must be non-empty")


DEFAULT_DURATION_DAYS = 25  # v2.1: matches Campaign 2 main dataset span (Aug 4-28)
DEFAULT_DURATION_SECONDS = DEFAULT_DURATION_DAYS * 86400.0
