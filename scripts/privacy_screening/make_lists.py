#!/usr/bin/env python3
"""Build the media lists for person screening (MegaDetector v5a).

images_shard{0..N-1}.txt  camera-trap JPGs + citizen-science stills (HEIC
                          originals are screened through their converted JPEGs)
videos.txt                camera-trap clips, citizen-science videos, drone videos
"""
import csv
import os
from pathlib import Path

ROOT = Path(os.environ.get("SMARTWILDS_ARCHIVE", ".")).resolve()  # field archive root
OUT = Path(__file__).resolve().parent
CAMPAIGNS = ["thewilds_20250630_20250703", "thewilds_20250804_20250828", "thewilds_20250908_20250908"]
IMG = {".jpg", ".jpeg"}
VID = {".mp4", ".avi", ".mov"}
N_SHARDS = 4

images, videos = [], []
for camp in CAMPAIGNS:
    for modality in ("camera_traps", "citizen_science", "drones"):
        base = ROOT / camp / modality
        if not base.is_dir():
            continue
        for dirpath, _, files in os.walk(base):
            if "/TW07-CT05" in dirpath:  # excluded deployment (no media retained)
                continue
            for fn in sorted(files):
                ext = Path(fn).suffix.lower()
                p = str(Path(dirpath) / fn)
                if ext in IMG and modality != "drones":
                    images.append(p)
                elif ext in VID:
                    videos.append(p)

images.sort()
for i in range(N_SHARDS):
    (OUT / f"images_shard{i}.txt").write_text("\n".join(images[i::N_SHARDS]) + "\n")
(OUT / "videos.txt").write_text("\n".join(sorted(videos)) + "\n")
print(f"images={len(images)} videos={len(videos)}")
