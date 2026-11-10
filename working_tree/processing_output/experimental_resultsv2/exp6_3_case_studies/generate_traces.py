#!/usr/bin/env python3
"""
generate_traces.py — Exp 6.3 trace generator.

For each case study, runs `synthesize()` at the requested intensities and
writes one event-log CSV per (case study, intensity) into
    exp6_3_case_studies/traces/{case_study_name}_{intensity}x.events.csv

Schema matches v1 timestamps_combined.csv (EVENT_LOG_COLUMNS in
exp6_1_synthesis/schemas.py), so the Exp 4 replay engine consumes these
files without modification — that is the handoff contract for Anirudh and
Yuanyang.

Usage:
    python generate_traces.py                       # all CS, 1x intensity
    python generate_traces.py --case CS1 --case CS2 # CS1 + CS2 only (Day-3 gate)
    python generate_traces.py --intensity 1 --intensity 2 --intensity 10
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

THIS = Path(__file__).resolve()
ROOT = THIS.parent
SYNTH_DIR = THIS.parents[1] / "exp6_1_synthesis"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SYNTH_DIR))

from base_recipe import DEFAULT_DURATION_SECONDS  # noqa: E402
from recipes import cs1_ct_to_drone, cs2_acoustic_to_ct, cs3_focal_ct_network, cs4_citsci_system  # noqa: E402
from synthesize import synthesize  # noqa: E402

CASE_BUILDERS = {
    "CS1": cs1_ct_to_drone.build,
    "CS2": cs2_acoustic_to_ct.build,
    "CS3": cs3_focal_ct_network.build,
    "CS4": cs4_citsci_system.build,
}

OUT_DIR = ROOT / "traces"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case", action="append", choices=list(CASE_BUILDERS), help="repeatable; default = all")
    p.add_argument("--intensity", type=float, action="append", help="repeatable; default = [1.0]")
    p.add_argument("--duration-seconds", type=float, default=DEFAULT_DURATION_SECONDS)
    p.add_argument("--seed", type=int, default=None, help="override per-CS default seed")
    args = p.parse_args()

    cases = args.case or list(CASE_BUILDERS)
    intensities = args.intensity or [1.0]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    for cs_name in cases:
        builder = CASE_BUILDERS[cs_name]
        for intensity in intensities:
            kwargs = {"intensity_multiplier": intensity, "duration_seconds": args.duration_seconds}
            if args.seed is not None:
                kwargs["seed"] = args.seed
            cs = builder(**kwargs)
            log.info(f"[{cs_name} @ {intensity:g}x] synthesizing — {cs.recipe.name}")
            event_log = synthesize(cs.recipe)
            out_path = OUT_DIR / f"{cs.name}_{intensity:g}x.events.csv"
            event_log.to_csv(out_path, index=False)
            n_total = len(event_log)
            modality_counts = event_log["modality"].value_counts().to_dict()
            log.info(f"[{cs_name} @ {intensity:g}x] wrote {n_total} events → {out_path.name}  ({modality_counts})")
            manifest.append({
                "case_study": cs_name,
                "name": cs.name,
                "description": cs.description,
                "intensity_multiplier": intensity,
                "slo_compliance_seconds": cs.slo_compliance_seconds,
                "duration_seconds": args.duration_seconds,
                "seed": cs.recipe.seed,
                "n_events": n_total,
                "modality_counts": {k: int(v) for k, v in modality_counts.items()},
                "trace_path": str(out_path.relative_to(ROOT)),
            })

    manifest_path = OUT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    log.info(f"manifest → {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
