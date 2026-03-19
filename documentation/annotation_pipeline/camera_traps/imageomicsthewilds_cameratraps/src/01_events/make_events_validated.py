"""
Enhanced camera trap event extraction with timestamp validation and manual review flagging.

This module extends the basic timestamp extraction with:
1. Date range validation based on deployment metadata
2. Filename vs EXIF timestamp cross-checking
3. Timestamp corrections for cameras with known clock issues
4. Comprehensive flagging for manual review

Output CSV includes additional columns for validation:
- timestamp: extracted or corrected timestamp
- timestamp_source: 'filename', 'exif', or 'corrected'
- validation_flag: reason for manual review (if any)
- exif_datetime: original EXIF datetime (for reference if used)
"""

import re
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
from PIL import Image, ExifTags
from camera_deployment_metadata import (
    get_deployment_info,
    get_valid_date_range,
    should_apply_timestamp_correction,
    validate_timestamp,
)

IDX = "index.csv"
OUT = "events_validated.csv"

# EXIF tag id mapping
TAGS = ExifTags.TAGS
NAME2ID = {v: k for k, v in TAGS.items()}
DTO_ID = NAME2ID.get("DateTimeOriginal", None)
DT_ID = NAME2ID.get("DateTime", None)

# Regex to extract timestamp from filename: YYMMDDHHMMSS
RE = re.compile(r"_(\d{12})_")


def ts_from_filename(name: str) -> Optional[pd.Timestamp]:
    """Extract timestamp from filename (YYMMDDHHMMSS format)."""
    m = RE.search(name)
    if not m:
        return None
    s = m.group(1)  # YYMMDDHHMMSS
    year = 2000 + int(s[0:2])
    mo = int(s[2:4])
    d = int(s[4:6])
    hh = int(s[6:8])
    mm = int(s[8:10])
    ss = int(s[10:12])
    return pd.Timestamp(year=year, month=mo, day=d, hour=hh, minute=mm, second=ss)


def ts_from_exif(path: Path) -> Optional[pd.Timestamp]:
    """Extract timestamp from EXIF metadata."""
    try:
        img = Image.open(path)
        exif = img.getexif()
        if not exif:
            return None
        val = None
        if DTO_ID is not None and DTO_ID in exif:
            val = exif.get(DTO_ID)
        elif DT_ID is not None and DT_ID in exif:
            val = exif.get(DT_ID)
        if val is None:
            return None
        # Common format: "YYYY:MM:DD HH:MM:SS"
        return pd.to_datetime(str(val), format="%Y:%m:%d %H:%M:%S", errors="coerce")
    except Exception:
        return None


def apply_timestamp_correction(
    site_cam: str, timestamp: pd.Timestamp
) -> Tuple[Optional[pd.Timestamp], bool]:
    """
    Apply timestamp correction if known issue exists for this camera.
    Returns (corrected_timestamp, was_corrected)
    """
    correction = should_apply_timestamp_correction(
        site_cam, timestamp.year, timestamp.month, timestamp.day
    )
    if correction:
        new_year, new_month, new_day = correction
        corrected = timestamp.replace(year=new_year, month=new_month, day=new_day)
        return corrected, True
    return timestamp, False


def validate_and_flag_timestamp(
    site_cam: str,
    timestamp: pd.Timestamp,
    timestamp_source: str,
    filename_ts: Optional[pd.Timestamp],
    exif_ts: Optional[pd.Timestamp],
) -> Tuple[pd.Timestamp, str, Optional[str]]:
    """
    Validate timestamp and generate flags for manual review.

    Returns:
        (final_timestamp, source_used, validation_flag_or_none)
    """
    flags = []

    # Check if timestamps disagree
    if filename_ts is not None and exif_ts is not None:
        # If they differ by more than 1 second, flag it
        if abs((filename_ts - exif_ts).total_seconds()) > 1:
            flags.append(
                f"EXIF_MISMATCH: filename={filename_ts.isoformat()} vs exif={exif_ts.isoformat()}"
            )

    # Check against deployment date range
    is_valid, reason = validate_timestamp(site_cam, timestamp)
    if not is_valid:
        flags.append(f"OUT_OF_RANGE: {reason}")

    # Check for timestamp corrections applied
    info = get_deployment_info(site_cam)
    if info and "timestamp_corrections" in info:
        flags.append(f"CORRECTED: camera clock was set incorrectly")

    # Check for known data gaps
    if info and "data_cutoff" in info:
        if timestamp > info["data_cutoff"]:
            flags.append(f"AFTER_KNOWN_CUTOFF: data collection stopped at {info['data_cutoff'].date()}")

    # Compile final flag
    final_flag = None
    if flags:
        final_flag = "; ".join(flags)

    return timestamp, timestamp_source, final_flag


def process_events():
    """Main processing function."""
    df = pd.read_csv(IDX)

    rows = []
    stats = {
        "total_images": len(df),
        "missing_ts": 0,
        "exif_used": 0,
        "corrected": 0,
        "flagged_for_review": 0,
    }

    for _, r in df.iterrows():
        p = Path(r["path"])
        site_cam = r["site_cam"]

        # Extract timestamp from filename
        filename_ts = ts_from_filename(p.name)

        # Extract timestamp from EXIF
        exif_ts = ts_from_exif(p)

        # Determine which to use
        ts = filename_ts
        ts_source = "filename"

        if ts is None:
            ts = exif_ts
            ts_source = "exif"
            if ts is not None:
                stats["exif_used"] += 1

        # Apply corrections if needed
        was_corrected = False
        if ts is not None:
            ts, was_corrected = apply_timestamp_correction(site_cam, ts)
            if was_corrected:
                stats["corrected"] += 1

        # Validate and flag
        if ts is None or pd.isna(ts):
            stats["missing_ts"] += 1
            continue

        final_ts, source, flag = validate_and_flag_timestamp(
            site_cam, ts, ts_source, filename_ts, exif_ts
        )

        if flag is not None:
            stats["flagged_for_review"] += 1

        rows.append(
            {
                "timestamp": final_ts,
                "site_cam": site_cam,
                "session": r["session"],
                "path": r["path"],
                "timestamp_source": source,
                "validation_flag": flag,
                "filename_timestamp": filename_ts,
                "exif_timestamp": exif_ts,
            }
        )

    # Create output dataframe
    ev = pd.DataFrame(rows).sort_values(["site_cam", "timestamp"]).reset_index(drop=True)
    ev.to_csv(OUT, index=False)

    # Print statistics
    print(f"\n=== Camera Trap Event Extraction Summary ===")
    print(f"Output: {OUT}")
    print(f"Total rows: {len(ev)}")
    print(f"Total images processed: {stats['total_images']}")
    print(f"Missing timestamp: {stats['missing_ts']}")
    print(f"EXIF used (filename missing): {stats['exif_used']}")
    print(f"Timestamps corrected: {stats['corrected']}")
    print(f"Flagged for manual review: {stats['flagged_for_review']}")
    print(f"\nImages per camera:")
    print(ev.groupby("site_cam").size())

    # Print flagged images for review
    flagged = ev[ev["validation_flag"].notna()]
    if len(flagged) > 0:
        print(f"\n=== Images Flagged for Manual Review ({len(flagged)}) ===")
        for cam in flagged["site_cam"].unique():
            cam_flagged = flagged[flagged["site_cam"] == cam]
            print(f"\n{cam}:")
            for _, row in cam_flagged.iterrows():
                print(f"  {row['timestamp'].isoformat()}: {row['validation_flag']}")
                print(f"    Path: {row['path']}")


if __name__ == "__main__":
    process_events()
