#!/usr/bin/env python3
"""Stage the SmartWilds per-modality Hugging Face dataset directories.

One directory per modality (camera traps, bioacoustics, drones, citizen
science) plus the umbrella ``smartwilds`` dataset, each laid out like
imageomics/kabr-behavior-telemetry:

    <repo>/README.md                 dataset card (filled in separately)
    <repo>/data/events.csv           Darwin Core Event table
    <repo>/data/occurrences.csv      Darwin Core Occurrence table
    <repo>/data/...                  modality-specific per-file tables
    <repo>/metadata/                 sensor settings, data dictionary, provenance
    <repo>/scripts/                  generator / georeferencing / this script
    <repo>/media_manifest.csv        one row per raw file: release path, bytes,
                                     include flag, exclusion reason

Inputs are read from the frozen snapshot ``darwin_core_latest_20261008`` and
are never modified. Two release repairs are applied to the staged copies and
audited in ``RELEASE_BUILD_AUDIT.json``:

1. Curated camera-trap Occurrences that bypassed timestamp correction are
   re-timed from the corrected camera timestamp map.
2. ``associatedMedia`` is rewritten from absolute cluster paths to
   release-relative ``media/...`` paths; drone frames in the purged scratch
   workspace fall back to their retained original video (the snapshot's own
   documented policy).

Media files are NOT copied here. ``media_manifest.csv`` is the packaging input.

Usage:
    python release/scripts/build_hf_release.py [--out DIR]
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path("/fs/ess/PAS2136/TheWilds2025")
SNAP = ROOT / "processing_output/darwin_core_latest_20261008"
TS_MAP = ROOT / "processing_output/detections/drone_camera_analysis/camera_time_mapping"
SENSOR_MD = ROOT / "documentation/sensor_configurations.md"
CAMPAIGNS = ["thewilds_20250630_20250703", "thewilds_20250804_20250828", "thewilds_20250908_20250908"]
PROJECT_PREFIX = str(ROOT) + "/"
SCRATCH_PREFIX = "/fs/scratch/PAS2136/smartwilds_detection/"
STUDY_START, STUDY_END = "2025-06-30", "2025-09-08"

REPOS = {
    "camera_traps": "smartwilds-camera-traps",
    "bioacoustics": "smartwilds-bioacoustics",
    "drones": "smartwilds-drones",
    "citizen_science": "smartwilds-citizen-science",
    "core": "smartwilds",
}

audit = {"snapshot": SNAP.name, "built_utc": None, "repos": {}, "blocked": [], "errors": []}


def read(path, **kw):
    return pd.read_csv(path, dtype=str, keep_default_na=False, **kw)


def readable(path):
    return os.access(path, os.R_OK)


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_media(abs_path):
    """/fs/ess/.../TheWilds2025/<campaign>/<modality>/<rest> -> media/<campaign>/<rest>."""
    if not abs_path.startswith(PROJECT_PREFIX):
        return None
    parts = abs_path[len(PROJECT_PREFIX):].split("/")
    if parts[0] not in CAMPAIGNS or len(parts) < 3:
        return None
    return "/".join(["media", parts[0]] + parts[2:])


BIRD_WATER = ROOT / "processing_output/detections/drone_camera_analysis/aquatic_bird_analysis/bird_water_association_per_box.csv"
PATH_REWRITES = [
    (str(BIRD_WATER), "analysis/bird_water_association_per_box.csv"),
    ("/fs/ess/PAS2699/object_detection_datasets/smartwilds/", "smartwilds_review_subset/"),
    (PROJECT_PREFIX, "TheWilds2025/"),
]


def strip_cluster_paths(df):
    """Rewrite remaining absolute cluster paths in free-text columns to
    release-relative (shipped) or project-relative (provenance-only) forms."""
    for c in df.columns:
        col = df[c]
        if col.str.contains("/fs/", regex=False).any():
            for a, b in PATH_REWRITES:
                col = col.str.replace(a, b, regex=False)
            df[c] = col
    return df


def parse_md_tables(md_path):
    """Return {"## section / ### heading": DataFrame} for every pipe table."""
    tables, section, heading, rows = {}, "", None, []
    for line in Path(md_path).read_text().splitlines() + [""]:
        if line.startswith("## "):
            section = heading = line[3:].strip()
        elif line.startswith("### "):
            heading = section + " / " + line[4:].strip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                rows.append(cells)
        elif rows:
            tables[heading] = pd.DataFrame(rows[1:], columns=rows[0])
            rows = []
    return tables


def media_inventory(modality, exclude=lambda rel: None):
    """One row per raw file under every campaign's <modality>/ directory."""
    rows = []
    for camp in CAMPAIGNS:
        base = ROOT / camp / modality
        if not base.is_dir():
            continue
        for dirpath, _, files in os.walk(base):
            for fn in files:
                src = Path(dirpath) / fn
                rel = rel_media(str(src))
                reason = exclude(rel) or ""
                try:
                    size = src.stat().st_size
                except OSError:
                    size, reason = "", reason or "unreadable_source"
                rows.append({"release_path": rel, "source_path": str(src.relative_to(ROOT)),
                             "bytes": size, "include": "false" if reason else "true",
                             "exclusion_reason": reason})
    return pd.DataFrame(rows).sort_values("release_path").reset_index(drop=True)


def check_tables(name, ev, oc, manifest, extra_event_ids=()):
    """Release checks the snapshot audit lacked: dates inside parent spans,
    sentinel strings, and every associatedMedia resolving to an included file."""
    res = {}
    ids = set(ev.eventID) | set(extra_event_ids)
    res["events"], res["occurrences"] = len(ev), len(oc)
    res["dangling_parentEventID"] = sorted({p for p in ev.parentEventID if p and p not in ids})
    res["occurrences_without_event"] = int((~oc.eventID.isin(ids)).sum())
    sentinel = re.compile(r"^(nan|none|null|-1|1970-01-01)$", re.I)
    res["sentinel_cells"] = {f"{t}.{c}": int(df[c].str.match(sentinel).sum())
                             for t, df in (("events", ev), ("occurrences", oc)) for c in df.columns
                             if df[c].str.match(sentinel).any()}
    span = ev.set_index("eventID").eventDate.str.split("/", expand=True)
    span.columns = ["a", "b"][: span.shape[1]]
    if "b" not in span:
        span["b"] = None
    span["b"] = span.b.fillna(span.a)
    single = oc[~oc.eventDate.str.contains("/")]
    j = single.join(span, on="eventID")
    res["occurrence_date_outside_event_span"] = int(((j.eventDate < j.a) | (j.eventDate > j.b)).sum())
    res["occurrence_date_outside_study"] = int(((single.eventDate < STUDY_START) | (single.eventDate > STUDY_END)).sum())
    res["occurrence_interval_dates"] = int(oc.eventDate.str.contains("/").sum())
    media = oc.associatedMedia[oc.associatedMedia != ""]
    res["absolute_media_paths"] = int(media.str.startswith("/").sum())
    res["cells_with_cluster_paths"] = int(sum(df[c].str.contains("/fs/", regex=False).sum()
                                             for df in (ev, oc) for c in df.columns))
    if manifest is not None:
        included = set(manifest.release_path[manifest.include == "true"])
        unresolved = media[~media.isin(included)]
        res["media_paths_not_in_included_manifest"] = int(len(unresolved))
        res["media_unresolved_examples"] = unresolved.drop_duplicates().head(5).tolist()
    res["pass"] = (not res["dangling_parentEventID"] and res["occurrences_without_event"] == 0
                   and not res["sentinel_cells"] and res["occurrence_date_outside_event_span"] == 0
                   and res["occurrence_date_outside_study"] == 0 and res["absolute_media_paths"] == 0
                   and res["cells_with_cluster_paths"] == 0
                   and res.get("media_paths_not_in_included_manifest", 0) == 0)
    return res


def write_repo(out, repo, files):
    d = out / repo
    for rel, obj in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(obj, pd.DataFrame):
            obj.to_csv(p, index=False)
        elif isinstance(obj, (dict, list)):
            p.write_text(json.dumps(obj, indent=2) + "\n")
        elif isinstance(obj, Path):
            shutil.copy2(obj, p)
        else:
            p.write_text(obj)
    return d


TERMS = {
    # Darwin Core / Humboldt terms (https://dwc.tdwg.org/terms/)
    "eventID": "Darwin Core: unique Event identifier", "parentEventID": "Darwin Core: eventID of the parent Event",
    "eventType": "Darwin Core: Project, SensorDeployment, AudioRecording, MediaEvent, or ObservationSession",
    "eventDate": "Darwin Core: ISO 8601 date or date interval (start/end)",
    "eventTime": "Darwin Core: local time (or interval); blank when not recoverable",
    "samplingProtocol": "Darwin Core: sensor, schedule, and processing chain", "sampleSizeValue": "Darwin Core: sample size",
    "sampleSizeUnit": "Darwin Core: unit of sampleSizeValue", "fieldNotes": "Darwin Core: provenance and field notes",
    "occurrenceID": "Darwin Core: unique Occurrence identifier", "catalogNumber": "Darwin Core: source record identifier",
    "scientificName": "Darwin Core: top-1 model or annotator taxon", "taxonRank": "Darwin Core: rank of scientificName",
    "vernacularName": "Darwin Core: common name", "kingdom": "Darwin Core: rank", "phylum": "Darwin Core: rank",
    "class": "Darwin Core: rank", "order": "Darwin Core: rank", "family": "Darwin Core: rank", "genus": "Darwin Core: rank",
    "specificEpithet": "Darwin Core: rank", "occurrenceStatus": "Darwin Core: present",
    "individualCount": "Darwin Core: 1 per visual crop; number of BirdNET detections for acoustic rows",
    "basisOfRecord": "Darwin Core: MachineObservation or HumanObservation",
    "recordedBy": "Darwin Core: device or team", "identifiedBy": "Darwin Core: model (and version) or annotator",
    "identificationVerificationStatus": "Darwin Core: unverified | validated | verified by expert",
    "identificationRemarks": "Darwin Core: rank, top-1 score, bbox xywh (px), detector label",
    "decimalLatitude": "Darwin Core: WGS84; see dataGeneralizations for what the point represents",
    "decimalLongitude": "Darwin Core: WGS84", "coordinateUncertaintyInMeters": "Darwin Core: meters",
    "geodeticDatum": "Darwin Core: WGS84", "locality": "Darwin Core: named place",
    "locationID": "Darwin Core: site (TWxx) for fixed sensors; flight ID for drones",
    "occurrenceRemarks": "Darwin Core: projection status, timestamp method, repair notes (key=value; ...)",
    "associatedMedia": "Darwin Core: release-relative path to the source media file",
    "associatedReferences": "Darwin Core: release-relative supporting analysis file",
    "dataGeneralizations": "Darwin Core: what the coordinate represents", "informationWithheld": "Darwin Core",
    "datasetID": "Darwin Core: modality dataset identifier", "datasetName": "Darwin Core",
    "release_path": "Path of the file inside this dataset", "source_path": "Path in the project archive",
    "bytes": "File size", "include": "true if the file is distributed in media/",
    "exclusion_reason": "Why a file is not distributed",
    "has_human_detection": "true if any Occurrence on this image is labelled Homo sapiens",
    "occurrence_count": "Occurrences derived from this image",
    "video_path": "Release-relative path of the raw video", "detection_id": "<video>_<frame>_<k> from the SAM3 run",
    "frame_index": "0-based native frame index in the video (SAM3 sampled every 15th frame)",
    "bbox_x": "Box left, pixels, in the native frame", "bbox_y": "Box top, pixels", "bbox_w": "Box width, pixels",
    "bbox_h": "Box height, pixels", "top1_score": "BioCLIP Tree-of-Life top-1 score",
    "georef_status": "Ground-projection status (ok | invalid_altitude | missing_drone_gps | horizon_ray | out_of_range)",
}


def write_dictionary(d, repo):
    out = [f"# {repo} data dictionary", "",
           "Generated by `scripts/build_hf_release.py`. Darwin Core term definitions: "
           "<https://dwc.tdwg.org/terms/>. Columns not listed in a Darwin Core namespace are "
           "SmartWilds-specific.", ""]
    for p in sorted(d.rglob("*.csv")):
        rel = p.relative_to(d)
        df = pd.read_csv(p, dtype=str, keep_default_na=False, nrows=1000)
        n = sum(1 for _ in open(p)) - 1
        out += [f"## `{rel}`", "", f"{n:,} rows.", "", "| Column | Description | Example |", "|---|---|---|"]
        for c in df.columns:
            ex = next((v for v in df[c] if v), "")
            ex = (ex[:60] + "…") if len(ex) > 60 else ex
            out.append(f"| `{c}` | {TERMS.get(c, '')} | {ex.replace('|', '/')} |")
        out.append("")
    (d / "metadata").mkdir(exist_ok=True)
    (d / "metadata/DATA_DICTIONARY.md").write_text("\n".join(out) + "\n")


def write_checksums(d):
    lines = []
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.name not in ("CHECKSUMS.sha256", "README.md") and "images" not in p.parts:
            lines.append(f"{sha256(p)}  {p.relative_to(d)}")
    (d / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n")


# --------------------------------------------------------------------------
# Camera traps
# --------------------------------------------------------------------------
def build_camera(out, tables):
    ev = read(SNAP / "camera_traps/darwin_core_events_camera_traps.csv")
    oc = read(SNAP / "camera_traps/darwin_core_occurrences_camera_traps.csv")
    tmap = read(TS_MAP / "camera_image_timestamp_map.csv")
    tmap["key"] = tmap.camera_id.str.replace("-", "_") + "/" + tmap.sd_folder + "/" + tmap.filename
    tmap_by_key = tmap.drop_duplicates("key").set_index("key")
    tmap_by_path = tmap.set_index("image_path")
    rep = {}

    # Curated (goose/swan review) records point at copies in PAS2699; recover the raw image.
    def curated_source(p):
        f = p.rsplit("/", 1)[-1]
        i = f.find("camera_traps__")
        if i >= 0:
            s = f[i:].split("__")  # camera_traps, CAM, SD, MEDIA..., FILE
            key = s[1].replace("-", "_") + "/" + s[2] + "/" + s[-1]
        else:  # e.g. ..._TW01-CT02__SD02_...__images__chunk3__FILE.JPG
            s = f.split("__")
            key = s[0].rsplit("_", 1)[-1].replace("-", "_") + "/" + s[1] + "/" + s[-1]
        return tmap_by_key.image_path.get(key)

    curated = oc.associatedMedia.str.startswith("/fs/ess/PAS2699/")
    src = oc.loc[curated, "associatedMedia"].map(curated_source)
    rep["curated_media_unmapped"] = int(src.isna().sum())
    ok = src.dropna().index
    oc.loc[ok, "occurrenceRemarks"] = (oc.loc[ok, "occurrenceRemarks"] + "; review_subset_copy="
                                       + oc.loc[ok, "associatedMedia"])
    oc.loc[ok, "associatedMedia"] = src[ok]

    # Re-time every Occurrence from the corrected map; count what changes.
    ts = oc.associatedMedia.map(tmap_by_path.corrected_timestamp)
    rep["occurrences_without_map_row"] = int(ts.isna().sum())
    new_date, new_time = ts.str[:10], ts.str[11:19]
    changed = ts.notna() & ((oc.eventDate != new_date) | (oc.eventTime != new_time))
    rep["occurrences_retimed"] = int(changed.sum())
    rep["retimed_by_correction_method"] = (
        oc.loc[changed, "associatedMedia"].map(tmap_by_path.correction_method).value_counts().to_dict())
    note = "; release_20261022: date/time re-derived from corrected camera timestamp map"
    oc.loc[changed, "occurrenceRemarks"] = oc.loc[changed, "occurrenceRemarks"] + note
    oc.loc[changed, "eventDate"] = new_date[changed]
    oc.loc[changed, "eventTime"] = new_time[changed]

    oc["associatedMedia"] = oc.associatedMedia.map(lambda p: rel_media(p) or p)

    # Per-image table: every raw image (detections or not), release-relative.
    human = set(oc.associatedMedia[oc.scientificName.str.startswith("Homo")])
    images = tmap.drop(columns=["key"]).copy()
    images.insert(0, "release_path", images.image_path.map(rel_media))
    images = images.drop(columns=["image_path"])
    n_occ = oc.associatedMedia.value_counts()
    images["occurrence_count"] = images.release_path.map(n_occ).fillna(0).astype(int)
    images["has_human_detection"] = images.release_path.isin(human).map({True: "true", False: "false"})

    excl = lambda rel: "excluded_deployment_TW07-CT05_people_only" if "/TW07-CT05/" in rel else None
    manifest = media_inventory("camera_traps", excl)
    manifest["has_human_detection"] = manifest.release_path.isin(human).map({True: "true", False: "false"})

    c1 = tables["Camera Trap Configurations / Campaign 1: June 30 – July 3, 2025"].assign(campaign="thewilds_20250630_20250703")
    c2 = tables["Camera Trap Configurations / Campaign 2: August 4 – August 28, 2025"].assign(campaign="thewilds_20250804_20250828")
    cams = [t for t in (c1, c2) if "Camera" in t.columns]
    dep = pd.concat(cams, ignore_index=True)
    dep.insert(0, "deploymentID", dep.Site.str.extract(r"^(TW\d+)")[0] + "-" + dep.Camera)
    geo = read(SNAP / "scripts/georeferencing/camera_geolocation_config.csv")
    geo["camera_id"] = geo.camera_id.str.replace("_", "-")  # raw dir is TW09_CT02
    dep = dep.merge(geo[["collection", "camera_id", "path_contains", "camera_lat", "camera_lon", "hfov_deg", "bearing_deg",
                         "image_rotation_deg", "target_height_m", "config_source", "notes"]].rename(
                        columns={"notes": "geolocation_notes"}),
                    left_on=["campaign", "deploymentID"], right_on=["collection", "camera_id"], how="left"
                    ).drop(columns=["collection", "camera_id"]).fillna({"path_contains": ""})
    dep["images_on_disk"] = dep.apply(lambda r: int(((images.dataset == r.campaign) &
                                                      (images.camera_id.str.replace("_", "-") == r.deploymentID)
                                                      & (images.release_path.str.contains(r.path_contains, regex=False)
                                                         if r.path_contains else True)).sum()), axis=1)
    # A path-specific override (TW09-CT02 SD23, after the Aug 18 move) takes its
    # images away from the deployment's default row.
    for (camp, did), g in dep.groupby(["campaign", "deploymentID"]):
        if len(g) > 1:
            default = g.index[g.path_contains == ""]
            dep.loc[default, "images_on_disk"] -= g.loc[g.path_contains != "", "images_on_disk"].sum()
    dep["released"] = (dep.deploymentID != "TW07-CT05").map({True: "true", False: "false"})

    ev, oc = strip_cluster_paths(ev), strip_cluster_paths(oc)
    res = check_tables("camera_traps", ev, oc, manifest, extra_event_ids={"TheWilds_2025_camera_traps", "TheWilds_2025"})
    res.update(rep)
    res["images_total"] = len(images)
    res["images_with_human_detection"] = int((images.has_human_detection == "true").sum())
    files = {
        "data/events.csv": ev, "data/occurrences.csv": oc, "data/images.csv": images,
        "analysis/bird_water_association_per_box.csv": BIRD_WATER,
        "media_manifest.csv": manifest,
        "metadata/deployments.csv": dep,
        "metadata/camera_models.csv": tables["Camera Trap Configurations / Camera Models"],
        "metadata/camera_geolocation_config.csv": SNAP / "scripts/georeferencing/camera_geolocation_config.csv",
        "metadata/timestamp_summary_by_camera.csv": TS_MAP / "camera_timestamp_summary_by_camera.csv",
        "metadata/timestamp_summary_by_date.csv": TS_MAP / "camera_timestamp_summary_by_date.csv",
        "metadata/provenance/tw07_ct05_sensitive_media_disposition_20261008.json":
            SNAP / "tw07_ct05_sensitive_media_disposition_20261008.json",
        "metadata/provenance/curated_bird_dwc_update_audit_20260920_015706.json":
            SNAP / "curated_bird_dwc_update_audit_20260920_015706.json",
        "scripts/geolocate_camera_trap_treeoflife_predictions.py":
            SNAP / "scripts/georeferencing/geolocate_camera_trap_treeoflife_predictions.py",
        "scripts/generate_darwin_core_latest_20261008.py": SNAP / "scripts/generate_darwin_core_latest_20261008.py",
    }
    return files, res


# --------------------------------------------------------------------------
# Bioacoustics
# --------------------------------------------------------------------------
def build_bioacoustics(out, tables):
    ev = read(SNAP / "bioacoustics_complete/darwin_core_events_bioacoustics_complete.csv")
    oc = read(SNAP / "bioacoustics_complete/darwin_core_occurrences_bioacoustics_complete.csv")
    rec = read(SNAP / "bioacoustics_complete/RAW_WAV_RECONCILIATION_20261008.csv")
    rec.insert(0, "release_path", rec.raw_wav_path.map(lambda p: rel_media(PROJECT_PREFIX + p)))
    included = rec.release_disposition.str.startswith("included")
    path_by_event = rec[included].set_index("darwin_core_eventID").release_path
    # associatedMedia is a bare WAV filename; resolve it through the Event.
    oc["associatedMedia"] = oc.eventID.map(path_by_event).fillna(oc.associatedMedia)
    ev["associatedMedia"] = ev.eventID.map(path_by_event).fillna("")

    disposition = dict(zip(rec.release_path, rec.release_disposition))
    def excl(rel):
        d = disposition.get(rel)
        return None if d is None or d.startswith("included") else d.split(";")[0] + ":" + rec.loc[
            rec.release_path == rel, "reconciliation_status"].iloc[0]
    manifest = media_inventory("bioacoustics", excl)

    t = {k: v for k, v in tables.items() if k.startswith("Bioacoustic Recorder Configurations / Campaign")}
    dep = pd.concat([v.assign(campaign=("thewilds_20250630_20250703" if "June" in k else "thewilds_20250804_20250828"))
                     for k, v in t.items()], ignore_index=True)
    dep.insert(0, "deploymentID", dep.Site.str.extract(r"^(TW\d+)")[0] + "-" + dep.Recorder)
    dep.insert(1, "model", "Wildlife Acoustics Song Meter Micro 2")
    counts = rec.groupby(["source_campaign_directory", "deploymentID"]).release_disposition.agg(
        wav_paths="size", wav_released=lambda s: s.str.startswith("included").sum()).reset_index()
    counts["campaign"] = counts.source_campaign_directory.map(
        {"campaign1": "thewilds_20250630_20250703", "campaign2": "thewilds_20250804_20250828"})
    dep = dep.merge(counts.drop(columns="source_campaign_directory"), on=["campaign", "deploymentID"], how="left")
    birdnet = pd.DataFrame([{"software": "BirdNET Analyzer", "version": "2.4", "segment_length_s": 3.0,
                             "sample_rate_hz": 48000, "bandpass_hz": "0-15000",
                             "occurrence_unit": "one row per recording x species; individualCount = detections"}])
    ev, oc = strip_cluster_paths(ev), strip_cluster_paths(oc)
    res = check_tables("bioacoustics", ev, oc, manifest, extra_event_ids={"TheWilds_2025"})
    files = {
        "data/events.csv": ev, "data/occurrences.csv": oc, "data/recordings.csv": rec,
        "media_manifest.csv": manifest,
        "metadata/deployments.csv": dep, "metadata/birdnet_settings.csv": birdnet,
        "metadata/provenance/RAW_WAV_RECONCILIATION_20261008.md":
            SNAP / "bioacoustics_complete/RAW_WAV_RECONCILIATION_20261008.md",
        "metadata/provenance/bioacoustic_event_repair_20261008.json": SNAP / "bioacoustic_event_repair_20261008.json",
        "scripts/reconcile_bioacoustic_raw_wavs.py": SNAP / "scripts/reconcile_bioacoustic_raw_wavs.py",
    }
    return files, res


# --------------------------------------------------------------------------
# Drones
# --------------------------------------------------------------------------
def build_drones(out, tables):
    ev = read(SNAP / "drones/darwin_core_events_drones.csv")
    oc = read(SNAP / "drones/darwin_core_occurrences_drones.csv")
    manifest = media_inventory("drones")
    videos = manifest[manifest.release_path.str.lower().str.endswith((".mp4", ".mov"))]
    by_stem = {}
    for p in videos.release_path:
        flight_dir = p.split("/")[2]
        by_stem.setdefault((flight_dir, Path(p).stem), []).append(p)

    scratch = oc.associatedMedia.str.startswith(SCRATCH_PREFIX)
    def video_for(frame):
        rest = frame[len(SCRATCH_PREFIX):].split("/")  # campaign, drones, flight, ..., VID_frames, file
        stem = re.sub(r"_frames$", "", rest[-2])
        hits = by_stem.get((rest[2], stem), [])
        return hits[0] if len(hits) == 1 else None
    fallback = oc.loc[scratch, "associatedMedia"].map(video_for)
    rep = {"scratch_frame_rows": int(scratch.sum()),
           "scratch_frame_unique": int(oc.loc[scratch, "associatedMedia"].nunique()),
           "scratch_frame_rows_unmapped": int(fallback.isna().sum())}
    ok = fallback.dropna().index
    oc.loc[ok, "associatedMedia"] = fallback[ok]
    oc.loc[ok, "occurrenceRemarks"] = oc.loc[ok, "occurrenceRemarks"] + \
        "; associated_media_source=original_video_fallback_missing_scratch_frame"
    oc["associatedMedia"] = oc.associatedMedia.map(lambda p: rel_media(p) or p)
    # Per-detection table for frame extraction from the released raw videos.
    # detection_id = <video>_<frame:06d>_<k>; frame is the native frame index
    # (frames were sampled every 15th frame for SAM3).
    det = pd.DataFrame({
        "occurrenceID": oc.occurrenceID, "eventID": oc.eventID, "video_path": oc.associatedMedia,
        "detection_id": oc.occurrenceRemarks.str.extract(r"detection_id=([^;]+)")[0]})
    det["frame_index"] = det.detection_id.str.extract(r"_(\d{6})_\d+$")[0].astype("Int64")
    bbox = oc.identificationRemarks.str.extract(r"bbox xywh\(px\): \[([^\]]+)\]")[0].str.split(",", expand=True)
    for i, c in enumerate(["bbox_x", "bbox_y", "bbox_w", "bbox_h"]):
        det[c] = pd.to_numeric(bbox[i]).round(2)
    det["scientificName"], det["vernacularName"] = oc.scientificName, oc.vernacularName
    det["top1_score"] = pd.to_numeric(oc.identificationRemarks.str.extract(r"top1 score: ([0-9.eE-]+)")[0])
    det["georef_status"] = oc.occurrenceRemarks.str.extract(r"drone_georef_status=([^;]+)")[0]
    det = det[det.detection_id.notna()]  # the 644 curated review records carry no frame id
    rep["detections_with_frame_index"] = int(det.frame_index.notna().sum())
    # Remaining frame PNGs that exist on disk are derived products, not raw media.
    flights = ev[ev.eventType == "SensorDeployment"][["eventID", "eventDate", "locationID", "fieldNotes"]].copy()
    flights["platform"] = flights.locationID.map(
        lambda s: "DJI Air 2" if "djiair" in s else "DJI (unspecified airframe)" if "DJI" in s else "Parrot Anafi 4K")
    media_events = ev[ev.eventType == "MediaEvent"]
    flights["videos"] = flights.eventID.map(media_events.parentEventID.value_counts()).fillna(0).astype(int)
    flights["occurrences"] = flights.eventID.map(
        oc.eventID.map(media_events.set_index("eventID").parentEventID).value_counts()).fillna(0).astype(int)
    ev, oc = strip_cluster_paths(ev), strip_cluster_paths(oc)
    res = check_tables("drones", ev, oc, manifest, extra_event_ids={"TheWilds_2025"})
    res.update(rep)
    files = {
        "data/events.csv": ev, "data/occurrences.csv": oc, "data/detections.csv": det,
        "media_manifest.csv": manifest,
        "analysis/bird_water_association_per_box.csv": BIRD_WATER,
        "metadata/flights.csv": flights, "metadata/platforms.csv": tables["Drone Configurations"],
        "metadata/drone_projection_config.csv": SNAP / "scripts/georeferencing/drone_projection_config.csv",
        "metadata/provenance/invalid_drone_date_repair_20261008.json": SNAP / "invalid_drone_date_repair_20261008.json",
        "metadata/provenance/invalid_drone_coordinate_repair_20261009.json":
            SNAP / "invalid_drone_coordinate_repair_20261009.json",
        "metadata/provenance/drone_missing_media_repair_20261010.json": SNAP / "drone_missing_media_repair_20261010.json",
        "metadata/provenance/excluded_drone_media_event_repair_20261008.json":
            SNAP / "excluded_drone_media_event_repair_20261008.json",
        "scripts/geolocate_drone_treeoflife_predictions.py":
            SNAP / "scripts/georeferencing/geolocate_drone_treeoflife_predictions.py",
        "scripts/generate_darwin_core_latest_20261008.py": SNAP / "scripts/generate_darwin_core_latest_20261008.py",
    }
    return files, res


# --------------------------------------------------------------------------
# Citizen science and umbrella (need files that are currently owner-only)
# --------------------------------------------------------------------------
def build_citizen_science(out, tables):
    evp = SNAP / "citizen_science/darwin_core_events_citizen_science.csv"
    ocp = SNAP / "citizen_science/darwin_core_occurrences_citizen_science.csv"
    if not (readable(evp) and readable(ocp)):
        raise PermissionError(f"unreadable: {evp.name}, {ocp.name} (owner-only permissions)")
    ev, oc = read(evp), read(ocp)
    oc["associatedMedia"] = oc.associatedMedia.map(lambda p: rel_media(p) or p)
    manifest = media_inventory("citizen_science")
    ev, oc = strip_cluster_paths(ev), strip_cluster_paths(oc)
    res = check_tables("citizen_science", ev, oc, manifest, extra_event_ids={"TheWilds_2025"})
    return {"data/events.csv": ev, "data/occurrences.csv": oc, "media_manifest.csv": manifest,
            "metadata/provenance/citizen_science_media_reconciliation_20261008.json":
                SNAP / "citizen_science_media_reconciliation_20261008.json"}, res


def build_core(out, tables):
    evp = SNAP / "events_all_modalities.csv"
    files = {}
    if readable(evp):
        files["data/events_all_modalities.csv"] = read(evp)
    else:  # stage everything else; record the gap
        audit["blocked"].append({"repo": REPOS["core"], "reason": f"unreadable: {evp.name}; staged without it"})
    files.update({
             "data/text_events.csv": SNAP / "text_data/darwin_core_events_text.csv",
             "data/text_occurrences.csv": SNAP / "text_data/darwin_core_occurrences_text.csv",
             "data/site_selection_rationale.csv": SNAP / "text_data/site_selection_rationale.csv",
             "metadata/sensor_configurations.md": SENSOR_MD,
             "SUPPLEMENTAL.md": ROOT / "documentation/manuscript/sys_dataset/SUPPLEMENTAL.md",
             "metadata/DEFECT_INVENTORY.md": ROOT / "release/cards/DEFECT_INVENTORY.md",
             "metadata/defect_inventory.csv": ROOT / "release/cards/defect_inventory.csv",
             "metadata/provenance/DARWIN_CORE_AUDIT_20261010_FINAL.json": SNAP / "DARWIN_CORE_AUDIT_20261010_FINAL.json"})
    for p in (SNAP / "analysis/arrival_traces_v2").iterdir():
        files[f"analysis/arrival_traces_v2/{p.name}"] = p
    return files, {"note": "merged Occurrences are assembled from the staged modality tables at upload time"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "release/hf_smartwilds_20261022"))
    ap.add_argument("--only", nargs="*", choices=list(REPOS))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tables = parse_md_tables(SENSOR_MD)
    audit["built_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    builders = {"camera_traps": build_camera, "bioacoustics": build_bioacoustics, "drones": build_drones,
                "citizen_science": build_citizen_science, "core": build_core}
    for key, fn in builders.items():
        if args.only and key not in args.only:
            continue
        repo = REPOS[key]
        print(f"[{repo}] building ...", flush=True)
        card = ROOT / "release/cards" / f"{repo}.md"
        if card.exists():
            (out / repo).mkdir(parents=True, exist_ok=True)
            shutil.copy2(card, out / repo / "README.md")
        imgs = ROOT / "release/cards/images" / repo
        if imgs.is_dir():
            shutil.copytree(imgs, out / repo / "images", dirs_exist_ok=True)
        try:
            files, res = fn(out, tables)
        except PermissionError as e:
            audit["blocked"].append({"repo": repo, "reason": str(e)})
            print(f"[{repo}] BLOCKED: {e}", flush=True)
            continue
        files[f"scripts/{Path(__file__).name}"] = Path(__file__)
        d = write_repo(out, repo, files)
        write_dictionary(d, repo)
        write_checksums(d)
        audit["repos"][repo] = res
        print(f"[{repo}] {json.dumps({k: v for k, v in res.items() if not isinstance(v, (list, dict))})}",
              flush=True)
    (out / "RELEASE_BUILD_AUDIT.json").write_text(json.dumps(audit, indent=2, default=str) + "\n")
    return 0 if not audit["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
