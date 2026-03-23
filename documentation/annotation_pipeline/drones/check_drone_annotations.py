#!/usr/bin/env python3
"""
Check drone annotation quality across all detection CSVs.

Flags issues for manual review:
- Labels not matching known Wilds species
- Low-confidence detections
- Non-animal labels (sky, grass, etc.)
- Per-mission and per-video summaries
- Confidence distribution by label

Output:
    processing_output/detections/drones/annotation_review/
        quality_report.txt          - Human-readable summary
        flagged_detections.csv      - Detections needing manual review
        label_mapping_review.csv    - All unique labels with suggested mappings
        per_video_summary.csv       - Stats per video file
"""

import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
DETECTIONS_DIR = BASE_DIR / "processing_output" / "detections" / "drones"
OUTPUT_DIR = DETECTIONS_DIR / "annotation_review"

# Species actually present at The Wilds (from taxon map + known residents)
VALID_SPECIES = {
    "Pere David's deer", "Elaphurus",       # Elaphurus davidianus
    "Grevy's zebra", "zebra",               # Equus grevyi
    "Sichuan takin", "Budorcas",            # Budorcas taxicolor
    "Przewalski's horse", "Equus", "horse", # Equus ferus przewalskii
    "Greater One-horned Rhino", "rhinoceros", "Ceratotherium",  # rhinos
    "Southern White Rhino",
    "Fringe-eared Oryx", "Scimitar-horned Oryx", "oryx",  # Oryx spp.
    "banteng", "Bos",                       # Bos javanicus
    "bison",                                # Bison bison
    "Giraffa",                              # Giraffa camelopardalis
    "white-tailed deer", "Odocoileus", "deer",  # Odocoileus virginianus (native)
    "Milu deer",                            # = Pere David's deer
    "coyote", "Canis",                      # Canis latrans (native)
    "bird", "songbird", "hawk", "raptor", "heron", "waterfowl",  # birds
    "Struthio", "ostrich",                  # Struthio camelus (nearby pastures)
    "Camelus", "camel",                     # Camelus spp. (nearby pastures)
}

# Labels that are plausible misclassifications (map to likely true species)
PLAUSIBLE_MAPPING = {
    "Pere David's deer": "Pere David's deer",
    "Elaphurus": "Pere David's deer",
    "Milu deer": "Pere David's deer",
    "elk": "Pere David's deer",          # BioCLIP confuses large cervids
    "Cervus": "Pere David's deer",       # large deer -> likely Pere David's
    "Grevy's zebra": "Grevy's zebra",
    "zebra": "Grevy's zebra",
    "donkey": "Grevy's zebra",           # equid confusion
    "Sichuan takin": "Sichuan takin",
    "Budorcas": "Sichuan takin",
    "muskox": "Sichuan takin",           # stocky bovid confusion
    "goat": "Sichuan takin",             # bovid confusion
    "Przewalski's horse": "Przewalski's horse",
    "Equus": "Przewalski's horse",
    "horse": "Przewalski's horse",
    "rhinoceros": "Rhino (check species)",
    "Ceratotherium": "White Rhino",
    "oryx": "Oryx (check species)",
    "antelope": "Oryx (check species)",
    "eland": "Oryx (check species)",     # large antelope confusion
    "Taurotragus": "Oryx (check species)",  # eland genus -> likely oryx
    "banteng": "Banteng",
    "Bos": "Banteng",
    "cattle": "Banteng",                 # bovid confusion
    "cow": "Banteng",
    "bison": "Bison",
    "Giraffa": "Giraffe",
    "white-tailed deer": "White-tailed Deer",
    "Odocoileus": "White-tailed Deer",
    "deer": "Deer (check species)",
    "coyote": "Coyote",
    "Canis": "Coyote",
    "fox": "Coyote",                     # canid confusion
    "Struthio": "Ostrich",
    "ostrich": "Ostrich",
    "Camelus": "Camel",
    "camel": "Camel",
    "bird": "Bird",
    "songbird": "Bird",
    "hawk": "Bird",
    "raptor": "Bird",
    "heron": "Bird",
    "waterfowl": "Bird",
}

# Labels that are definitely wrong (not at The Wilds or non-animal)
NON_ANIMAL_LABELS = {"sky", "grass", "rock", "tree", "vegetation", "water", "c"}
IMPOSSIBLE_SPECIES = {"Lycaon", "wild dog", "human", "fish"}


# ─── Loading ──────────────────────────────────────────────────────────────────

def load_all_detections():
    """Load all detection CSVs, returning list of dicts with added mission field."""
    all_rows = []
    files = sorted(DETECTIONS_DIR.glob("*_detections.csv"))

    for f in files:
        # Parse mission from filename: 20250701_parrotanafi_1_VID_001_detections.csv
        parts = f.stem.replace("_detections", "")
        # Mission = everything before the video name
        # e.g. "20250701_parrotanafi_1" from "20250701_parrotanafi_1_VID_001"
        name_parts = parts.split("_")
        # Find where video name starts (VID_xxx or DJI_xxxx or P followed by digits)
        mission_parts = []
        video_parts = []
        in_video = False
        for p in name_parts:
            if not in_video and p in ("VID", "DJI") or (not in_video and p.startswith("P") and p[1:].isdigit()):
                in_video = True
            if in_video:
                video_parts.append(p)
            else:
                mission_parts.append(p)
        mission = "_".join(mission_parts)
        video_name = "_".join(video_parts) if video_parts else parts

        with open(f, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row["_mission"] = mission
                row["_video_name"] = video_name
                row["_source_file"] = f.name
                all_rows.append(row)

    return all_rows


def load_frame_summaries():
    """Load all frame summary CSVs for blank frame stats."""
    summaries = {}
    files = sorted(DETECTIONS_DIR.glob("*_frame_summary.csv"))
    for f in files:
        key = f.stem.replace("_frame_summary", "")
        total = 0
        blank = 0
        with open(f, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                total += 1
                if row.get("is_blank") == "1":
                    blank += 1
        summaries[key] = {"total_frames": total, "blank_frames": blank}
    return summaries


# ─── Analysis ─────────────────────────────────────────────────────────────────

def classify_label(label):
    """Classify a detection label as valid, plausible, impossible, or non-animal."""
    if label in NON_ANIMAL_LABELS:
        return "non_animal"
    if label in IMPOSSIBLE_SPECIES:
        return "impossible"
    if label in VALID_SPECIES:
        return "valid"
    if label in PLAUSIBLE_MAPPING:
        return "plausible"
    return "unknown"


def analyze_detections(rows):
    """Compute quality metrics across all detections."""
    stats = {
        "total": len(rows),
        "label_counts": Counter(),
        "label_confidence": defaultdict(list),
        "label_class": {},
        "per_mission": defaultdict(lambda: {"count": 0, "labels": Counter()}),
        "per_video": defaultdict(lambda: {
            "count": 0, "labels": Counter(),
            "conf_scores": [], "mission": "",
        }),
        "flagged": [],
    }

    for row in rows:
        label = row.get("bioclip_label", "")
        conf = float(row.get("bioclip_score", 0))
        yolo_conf = float(row.get("yolo_conf", 0))
        mission = row["_mission"]
        video = row["_source_file"]
        classification = classify_label(label)

        stats["label_counts"][label] += 1
        stats["label_confidence"][label].append(conf)
        stats["label_class"][label] = classification

        stats["per_mission"][mission]["count"] += 1
        stats["per_mission"][mission]["labels"][label] += 1

        stats["per_video"][video]["count"] += 1
        stats["per_video"][video]["labels"][label] += 1
        stats["per_video"][video]["conf_scores"].append(conf)
        stats["per_video"][video]["mission"] = mission

        # Flag for review
        flag_reasons = []
        if classification == "impossible":
            flag_reasons.append(f"impossible_species:{label}")
        if classification == "non_animal":
            flag_reasons.append(f"non_animal:{label}")
        if classification == "unknown":
            flag_reasons.append(f"unknown_label:{label}")
        if conf < 0.4:
            flag_reasons.append(f"low_bioclip_conf:{conf:.3f}")
        if yolo_conf < 0.3:
            flag_reasons.append(f"low_yolo_conf:{yolo_conf:.3f}")

        if flag_reasons:
            stats["flagged"].append({
                **row,
                "_flag_reasons": "; ".join(flag_reasons),
                "_label_class": classification,
                "_suggested_species": PLAUSIBLE_MAPPING.get(label, "NEEDS_REVIEW"),
            })

    return stats


# ─── Output ───────────────────────────────────────────────────────────────────

def write_quality_report(stats, frame_summaries):
    """Write human-readable quality report."""
    report_path = OUTPUT_DIR / "quality_report.txt"
    with open(report_path, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("DRONE ANNOTATION QUALITY REPORT\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Total detections: {stats['total']:,}\n")
        f.write(f"Unique labels:    {len(stats['label_counts'])}\n")
        f.write(f"Flagged:          {len(stats['flagged']):,} "
                f"({100*len(stats['flagged'])/stats['total']:.1f}%)\n\n")

        # Classification breakdown
        class_counts = Counter()
        class_detection_counts = Counter()
        for label, cls in stats["label_class"].items():
            class_counts[cls] += 1
            class_detection_counts[cls] += stats["label_counts"][label]

        f.write("─── Label Classification ───\n\n")
        for cls in ["valid", "plausible", "impossible", "non_animal", "unknown"]:
            n_labels = class_counts.get(cls, 0)
            n_dets = class_detection_counts.get(cls, 0)
            pct = 100 * n_dets / stats["total"] if stats["total"] else 0
            f.write(f"  {cls:<15} {n_labels:>3} labels  {n_dets:>8,} detections ({pct:5.1f}%)\n")
        f.write("\n")

        # All labels sorted by count
        f.write("─── All Labels by Count ───\n\n")
        f.write(f"  {'Label':<25} {'Count':>8}  {'Mean Conf':>9}  {'Med Conf':>9}  {'Class':<12}  Suggested\n")
        f.write(f"  {'─'*25} {'─'*8}  {'─'*9}  {'─'*9}  {'─'*12}  {'─'*20}\n")
        for label, count in stats["label_counts"].most_common():
            confs = stats["label_confidence"][label]
            cls = stats["label_class"][label]
            suggested = PLAUSIBLE_MAPPING.get(label, "NEEDS_REVIEW")
            f.write(f"  {label:<25} {count:>8,}  {mean(confs):>9.4f}  {median(confs):>9.4f}  {cls:<12}  {suggested}\n")
        f.write("\n")

        # Impossible species detail
        f.write("─── IMPOSSIBLE SPECIES (definitely not at The Wilds) ───\n\n")
        for label in sorted(IMPOSSIBLE_SPECIES):
            if label in stats["label_counts"]:
                count = stats["label_counts"][label]
                confs = stats["label_confidence"][label]
                f.write(f"  {label:<20} {count:>6,} detections  "
                        f"conf: {mean(confs):.3f} mean, {min(confs):.3f}-{max(confs):.3f} range\n")
        f.write("\n")

        # Non-animal labels
        f.write("─── NON-ANIMAL LABELS ───\n\n")
        for label in sorted(NON_ANIMAL_LABELS):
            if label in stats["label_counts"]:
                count = stats["label_counts"][label]
                f.write(f"  {label:<20} {count:>6,} detections\n")
        f.write("\n")

        # Per-mission summary
        f.write("─── Per-Mission Summary ───\n\n")
        for mission in sorted(stats["per_mission"]):
            m = stats["per_mission"][mission]
            f.write(f"  {mission}\n")
            f.write(f"    Total detections: {m['count']:,}\n")
            f.write(f"    Top labels: ")
            top = m["labels"].most_common(5)
            f.write(", ".join(f"{l} ({c:,})" for l, c in top))
            f.write("\n\n")

        # Per-video summary
        f.write("─── Per-Video Summary ───\n\n")
        f.write(f"  {'Video File':<55} {'Dets':>6}  {'Mean Conf':>9}  Top Labels\n")
        f.write(f"  {'─'*55} {'─'*6}  {'─'*9}  {'─'*30}\n")
        for video in sorted(stats["per_video"]):
            v = stats["per_video"][video]
            avg_conf = mean(v["conf_scores"]) if v["conf_scores"] else 0
            top = v["labels"].most_common(3)
            top_str = ", ".join(f"{l}({c})" for l, c in top)
            f.write(f"  {video:<55} {v['count']:>6}  {avg_conf:>9.4f}  {top_str}\n")
        f.write("\n")

        # Frame summary stats
        if frame_summaries:
            total_frames = sum(s["total_frames"] for s in frame_summaries.values())
            blank_frames = sum(s["blank_frames"] for s in frame_summaries.values())
            f.write("─── Frame Coverage ───\n\n")
            f.write(f"  Total frames analyzed: {total_frames:,}\n")
            f.write(f"  Blank frames (no detections): {blank_frames:,} ({100*blank_frames/total_frames:.1f}%)\n")
            f.write(f"  Frames with detections: {total_frames - blank_frames:,} ({100*(total_frames-blank_frames)/total_frames:.1f}%)\n\n")

        # Recommendations
        f.write("=" * 70 + "\n")
        f.write("RECOMMENDATIONS\n")
        f.write("=" * 70 + "\n\n")
        f.write("1. REMOVE non-animal labels (sky, grass, rock, etc.) — these are YOLO false positives\n")
        f.write("2. REMOVE impossible species (ostrich, camel, wild dog, etc.) — BioCLIP misclassifications\n")
        f.write("3. REVIEW label_mapping_review.csv for suggested species remapping\n")
        f.write("4. REVIEW flagged_detections.csv for low-confidence detections\n")
        f.write("5. Consider raising YOLO confidence threshold (many detections at <0.3)\n")
        f.write("6. Consider raising BioCLIP threshold (many labels at ~0.5 are wrong)\n\n")

    print(f"Wrote quality report to {report_path}")


def write_flagged_detections(stats):
    """Write flagged detections to CSV for manual review."""
    flagged_path = OUTPUT_DIR / "flagged_detections.csv"
    if not stats["flagged"]:
        print("No flagged detections.")
        return

    fieldnames = [
        "_flag_reasons", "_label_class", "_suggested_species",
        "_mission", "_source_file", "video", "frame_number", "frame_time_sec",
        "bioclip_label", "bioclip_score", "yolo_conf",
        "xmin", "ymin", "xmax", "ymax", "frame_width", "frame_height",
    ]

    with open(flagged_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(stats["flagged"])

    print(f"Wrote {len(stats['flagged']):,} flagged detections to {flagged_path}")


def write_label_mapping(stats):
    """Write label mapping review CSV."""
    mapping_path = OUTPUT_DIR / "label_mapping_review.csv"
    rows = []
    for label, count in stats["label_counts"].most_common():
        confs = stats["label_confidence"][label]
        rows.append({
            "bioclip_label": label,
            "count": count,
            "pct_of_total": f"{100*count/stats['total']:.2f}",
            "mean_confidence": f"{mean(confs):.4f}",
            "median_confidence": f"{median(confs):.4f}",
            "min_confidence": f"{min(confs):.4f}",
            "max_confidence": f"{max(confs):.4f}",
            "classification": stats["label_class"][label],
            "suggested_species": PLAUSIBLE_MAPPING.get(label, "NEEDS_REVIEW"),
            "action": "KEEP" if stats["label_class"][label] == "valid"
                      else "REMAP" if label in PLAUSIBLE_MAPPING
                      else "REMOVE" if stats["label_class"][label] in ("impossible", "non_animal")
                      else "REVIEW",
        })

    with open(mapping_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} label mappings to {mapping_path}")


def write_per_video_summary(stats, frame_summaries):
    """Write per-video summary CSV."""
    summary_path = OUTPUT_DIR / "per_video_summary.csv"
    rows = []
    for video in sorted(stats["per_video"]):
        v = stats["per_video"][video]
        key = video.replace("_detections.csv", "")
        fs = frame_summaries.get(key, {})
        confs = v["conf_scores"]
        top = v["labels"].most_common(5)

        # Count flags for this video
        flag_count = sum(
            1 for f in stats["flagged"]
            if f["_source_file"] == video
        )

        rows.append({
            "video_file": video,
            "mission": v["mission"],
            "total_detections": v["count"],
            "unique_labels": len(v["labels"]),
            "mean_confidence": f"{mean(confs):.4f}" if confs else "",
            "total_frames": fs.get("total_frames", ""),
            "blank_frames": fs.get("blank_frames", ""),
            "detection_rate": f"{100*(fs['total_frames']-fs['blank_frames'])/fs['total_frames']:.1f}%"
                              if fs.get("total_frames") else "",
            "flagged_count": flag_count,
            "top_labels": "; ".join(f"{l} ({c})" for l, c in top),
        })

    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} video summaries to {summary_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Drone Annotation Quality Check")
    print("=" * 60)

    print("\nLoading detections...")
    rows = load_all_detections()
    print(f"  Loaded {len(rows):,} detections from {len(set(r['_source_file'] for r in rows))} files")

    print("Loading frame summaries...")
    frame_summaries = load_frame_summaries()
    print(f"  Loaded {len(frame_summaries)} frame summaries")

    print("\nAnalyzing...")
    stats = analyze_detections(rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    write_quality_report(stats, frame_summaries)
    write_flagged_detections(stats)
    write_label_mapping(stats)
    write_per_video_summary(stats, frame_summaries)

    # Print quick summary
    print(f"\n{'='*60}")
    print("Quick Summary")
    print(f"{'='*60}")

    class_counts = Counter()
    for label, cls in stats["label_class"].items():
        class_counts[cls] += stats["label_counts"][label]

    for cls in ["valid", "plausible", "impossible", "non_animal", "unknown"]:
        n = class_counts.get(cls, 0)
        pct = 100 * n / stats["total"]
        print(f"  {cls:<15} {n:>8,} ({pct:5.1f}%)")

    print(f"\n  Flagged for review: {len(stats['flagged']):,}")
    print(f"\n  Review files in: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
