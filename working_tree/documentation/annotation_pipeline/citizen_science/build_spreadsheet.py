#!/usr/bin/env python3
"""Combine species annotations with Google Photos JSON metadata to produce a spreadsheet.
Uses EXIF datetime when available, falls back to JSON (UTC converted to EST).
All datetimes are output in EST."""

import csv
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS

BASE = Path("/Users/kline.377/Downloads/Takeout 2")
ALBUMS = [
    BASE / "Google Photos" / "The Wilds Summer 2025 Fieldwork",
    BASE / "Google Photos" / "The Wilds 9-8-25",
]
IMAGE_DIRS = [
    BASE / "photos_videos",
    *ALBUMS,
]
CSV_FILES = [
    BASE / "wilds_species_annotations (1).csv",
    BASE / "wilds_species_annotations (2).csv",
]
OUTPUT = BASE / "wilds_species_datetime.csv"

# EST is UTC-5; EDT (summer) is UTC-4. The Wilds fieldwork was summer 2025, so EDT.
EDT = timezone(timedelta(hours=-4))
FMT = "%b %-d, %Y, %-I:%M:%S %p EST"


def find_json(filename: str) -> dict | None:
    """Find and parse the JSON sidecar for a given image filename."""
    stem = Path(filename).stem

    for album in ALBUMS:
        for p in album.glob(f"{stem}*json"):
            if p.suffix == ".json":
                with open(p) as f:
                    return json.load(f)
    return None


def get_exif_datetime(filename: str) -> str:
    """Extract datetime from image EXIF data. Cameras were set to local time (EST/EDT)."""
    for d in IMAGE_DIRS:
        filepath = d / filename
        if filepath.exists():
            try:
                img = Image.open(filepath)
                exif_data = img._getexif()
                if exif_data:
                    # Prefer DateTimeOriginal
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == "DateTimeOriginal":
                            dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                            return dt.strftime(FMT)
                    # Fall back to DateTime
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == "DateTime":
                            dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                            return dt.strftime(FMT)
            except Exception:
                continue
    return ""


def json_to_est(formatted: str) -> str:
    """Use the JSON formatted time as-is (already local/EST despite UTC label)."""
    # "Sep 8, 2025, 10:07:44 PM UTC" -> parse and reformat with EST label
    clean = formatted.replace(" UTC", "")
    try:
        dt = datetime.strptime(clean, "%b %d, %Y, %I:%M:%S %p")
        return dt.strftime(FMT)
    except ValueError:
        return clean + " EST"


def main():
    rows = []
    for csv_file in CSV_FILES:
        with open(csv_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

    output_rows = []
    missing_dt = []

    for row in rows:
        filename = row["filename"]
        species = row.get("species", "").strip()
        contains_humans = row.get("contains_humans", "").strip().lower()
        equipment = row.get("equipment", "").strip().lower()

        # Skip photos with people or equipment
        if contains_humans == "yes" or equipment == "yes":
            continue

        # Skip rows with no species annotation
        if not species:
            continue

        # Prefer EXIF (already in local/EST time)
        datetime_str = get_exif_datetime(filename)

        # Fall back to JSON timestamp (UTC -> EST conversion)
        if not datetime_str:
            meta = find_json(filename)
            if meta and "photoTakenTime" in meta:
                datetime_str = json_to_est(meta["photoTakenTime"]["formatted"])

        if not datetime_str:
            missing_dt.append(filename)

        output_rows.append({
            "filename": filename,
            "species": species,
            "datetime_EST": datetime_str,
        })

    # Write output CSV
    with open(OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "species", "datetime_EST"])
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} rows to {OUTPUT}")
    if missing_dt:
        print(f"Warning: no datetime for {len(missing_dt)} files:")
        for fn in missing_dt:
            print(f"  {fn}")
    else:
        print("All rows have datetime values!")


if __name__ == "__main__":
    main()
