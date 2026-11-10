#!/usr/bin/env python3
"""
make_event_tables.py — derive per-modality event tables from the combined trace.

Why this exists
---------------
synthesize.py routes two modalities through a timestamp bootstrap rather than
the change-point rate model:

    BOOTSTRAP_IAT_MODALITIES = ("bioacoustic", "citizen_science")

That path reads data/timestamps/timestamps_<modality>.csv. If the file is
absent it returns an empty array *silently* (INFO-level only), so synthesis
appears to succeed while emitting zero events for those modalities. Camera trap
and drone are unaffected -- they use the change-point model in the primitives.

This script regenerates those tables from the combined recorded trace.

Redistribution
--------------
Only the permitted derived columns are written: timestamp, modality, site,
label. The combined file's `source_file` column contains paths into the raw
field archive and is deliberately dropped -- see data/README.md.

Usage
-----
    python make_event_tables.py --combined /path/to/timestamps_combined.csv
    python make_event_tables.py --combined ... --all      # all four modalities
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import TIMESTAMPS_DIR  # noqa: E402

BOOTSTRAP_MODALITIES = ("bioacoustic", "citizen_science")
ALL_MODALITIES = ("bioacoustic", "citizen_science", "camera_trap", "drone")

# Columns safe to redistribute. `source_file` is excluded on purpose.
KEEP = ("timestamp", "modality", "site", "label")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--combined", type=Path, required=True,
                    help="timestamps_combined.csv from the recording phase")
    ap.add_argument("--all", action="store_true",
                    help="also emit camera_trap and drone (not needed for synthesis)")
    ap.add_argument("--out", type=Path, default=TIMESTAMPS_DIR)
    args = ap.parse_args()

    if not args.combined.exists():
        raise SystemExit(
            f"\nNot found: {args.combined}\n"
            f"This file is part of the field archive and is not redistributed "
            f"with the repository. See data/README.md.\n"
        )

    header = pd.read_csv(args.combined, nrows=0).columns
    usecols = [c for c in KEEP if c in header]
    if "timestamp" not in usecols or "modality" not in usecols:
        raise SystemExit(f"\n{args.combined} lacks required columns 'timestamp'/'modality'.\n")

    dropped = [c for c in header if c not in usecols]
    print(f"reading {args.combined}")
    print(f"  keeping {usecols}")
    print(f"  dropping {len(dropped)} column(s), incl. any raw-archive paths: {dropped}")

    df = pd.read_csv(args.combined, usecols=usecols)
    args.out.mkdir(parents=True, exist_ok=True)

    wanted = ALL_MODALITIES if args.all else BOOTSTRAP_MODALITIES
    for modality in wanted:
        sub = df[df["modality"] == modality].copy()
        if sub.empty:
            print(f"  {modality:16s} 0 rows — SKIPPED (not present in combined trace)")
            continue
        sub = sub.sort_values("timestamp")
        dest = args.out / f"timestamps_{modality}.csv"
        sub.to_csv(dest, index=False)
        print(f"  {modality:16s} {len(sub):7d} rows -> {dest.name}"
              f"  [{sub['timestamp'].min()} .. {sub['timestamp'].max()}]")

    print("\nDone. Re-run synthesis; bioacoustic and citizen_science will now draw events.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
