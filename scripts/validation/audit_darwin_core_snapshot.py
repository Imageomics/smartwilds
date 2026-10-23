#!/usr/bin/env python3
"""Read-only integrity audit for a frozen Darwin Core snapshot."""
import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME = re.compile(r"^\d{2}:\d{2}(?::\d{2})?$")
MODS = {
    "camera_traps": ("camera_traps/darwin_core_events_camera_traps.csv", "camera_traps/darwin_core_occurrences_camera_traps.csv", "TheWilds_2025_camera_traps"),
    "bioacoustics_complete": ("bioacoustics_complete/darwin_core_events_bioacoustics_complete.csv", "bioacoustics_complete/darwin_core_occurrences_bioacoustics_complete.csv", "TheWilds_2025_bioacoustics"),
    "drones": ("drones/darwin_core_events_drones.csv", "drones/darwin_core_occurrences_drones.csv", "TheWilds_2025_drones"),
    "citizen_science": ("citizen_science/darwin_core_events_citizen_science.csv", "citizen_science/darwin_core_occurrences_citizen_science.csv", "TheWilds_2025_citizen_science"),
    "text_data": ("text_data/darwin_core_events_text.csv", "text_data/darwin_core_occurrences_text.csv", "TheWilds_2025_text_data"),
}
EVENT_REQUIRED = {"eventID", "parentEventID", "eventType", "eventDate", "decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters"}
OCC_REQUIRED = {"occurrenceID", "eventID", "scientificName", "taxonRank", "basisOfRecord", "eventDate", "eventTime", "decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters", "associatedMedia"}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_header(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle), [])


def row_hash(row, fields):
    text = "\x1f".join(name + "=" + row.get(name, "") for name in fields)
    return hashlib.sha256(text.encode()).hexdigest()


def good_date(value):
    parts = value.split("/")
    if not value or len(parts) not in (1, 2) or any(not DATE.fullmatch(x) for x in parts):
        return False
    try:
        values = [date.fromisoformat(x) for x in parts]
    except ValueError:
        return False
    return len(values) == 1 or values[0] <= values[1]


def good_time(value):
    parts = value.split("/")
    if len(parts) not in (1, 2) or any(not TIME.fullmatch(x) for x in parts):
        return False
    try:
        parsed = [datetime.strptime(x, "%H:%M:%S" if len(x) == 8 else "%H:%M") for x in parts]
    except ValueError:
        return False
    return len(parsed) == 1 or parsed[0] <= parsed[1]


def add(items, severity, code, message, evidence=None):
    items.append({"severity": severity, "code": code, "message": message, "evidence": evidence})


def ancestor(event_id, events):
    seen = set()
    current = event_id
    while current and current not in seen:
        seen.add(current)
        row = events.get(current)
        if not row:
            return None
        if row.get("parentEventID") == "TheWilds_2025":
            return current
        current = row.get("parentEventID", "")
    return None


def scalar(row, occurrence, counters):
    for name, value in row.items():
        if value.strip().lower() in {"nan", "nat"}:
            counters["null_literal:" + name] += 1
    day, clock = row.get("eventDate", ""), row.get("eventTime", "")
    if day and not good_date(day):
        counters["invalid_eventDate"] += 1
    if clock and not good_time(clock):
        counters["invalid_eventTime"] += 1
    lat, lon = row.get("decimalLatitude", ""), row.get("decimalLongitude", "")
    if bool(lat) != bool(lon):
        counters["unpaired_coordinates"] += 1
    for name, value, low, high in (("latitude", lat, -90, 90), ("longitude", lon, -180, 180), ("uncertainty", row.get("coordinateUncertaintyInMeters", ""), 0, float("inf"))):
        if value:
            try:
                number = float(value)
                if not math.isfinite(number) or not low <= number <= high:
                    counters["invalid_" + name] += 1
            except ValueError:
                counters["invalid_" + name] += 1
    for name in (("occurrenceID", "eventID", "scientificName", "eventDate", "basisOfRecord") if occurrence else ("eventID", "eventType")):
        if not row.get(name, "").strip():
            counters["missing_" + name] += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-dir", type=Path, default=ROOT)
    parser.add_argument("--stem", default="DARWIN_CORE_AUDIT_20261009")
    args = parser.parse_args()
    root = args.snapshot_dir.resolve()
    findings, tables = [], {}
    source_events, source_occurrences = {}, {}
    counts = {"events": {}, "occurrences": {}}
    event_fields = occurrence_fields = None

    for modality, (event_rel, occurrence_rel, _) in MODS.items():
        for kind, rel, required, key_name in (("events", event_rel, EVENT_REQUIRED, "eventID"), ("occurrences", occurrence_rel, OCC_REQUIRED, "occurrenceID")):
            path = root / rel
            fields = csv_header(path)
            missing = sorted(required - set(fields))
            if missing:
                add(findings, "ERROR", "missing_columns", "Required columns are absent.", {"table": rel, "columns": missing})
            previous = event_fields if kind == "events" else occurrence_fields
            if previous is None:
                if kind == "events": event_fields = fields
                else: occurrence_fields = fields
            elif fields != previous:
                add(findings, "INFO", "header_variance", "Modality headers differ because modality-specific extension fields vary.", rel)
            seen, total = set(), 0
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    total += 1
                    key = row[key_name]
                    if key in seen:
                        add(findings, "ERROR", "duplicate_source_id", "Duplicate identifier in source table.", {"table": rel, "id": key})
                    seen.add(key)
                    target = source_events if kind == "events" else source_occurrences
                    if key in target:
                        add(findings, "ERROR", "cross_modality_duplicate_id", "Identifier occurs in multiple modality files.", key)
                    target[key] = (modality, row_hash(row, fields), tuple(fields))
            counts[kind][modality] = total
            tables[rel] = {"rows": total, "sha256": sha(path)}

    event_path, occurrence_path = root / "events_all_modalities.csv", root / "occurrences_all_modalities.csv"
    events, event_counts, event_types = {}, Counter(), Counter()
    with event_path.open(newline="", encoding="utf-8") as handle:
        fields = csv_header(event_path)
        missing = sorted(EVENT_REQUIRED - set(fields))
        if missing: add(findings, "ERROR", "missing_merged_event_columns", "Merged Event columns are absent.", missing)
        for row in csv.DictReader(handle):
            scalar(row, False, event_counts)
            key = row["eventID"]
            if key in events: add(findings, "ERROR", "duplicate_merged_event_id", "Duplicate merged Event ID.", key)
            events[key] = row
            event_types[row["eventType"]] += 1
    tables["events_all_modalities.csv"] = {"rows": len(events), "sha256": sha(event_path)}
    roots = [x for x in events.values() if x["eventID"] == "TheWilds_2025" and not x["parentEventID"]]
    if len(roots) != 1: add(findings, "ERROR", "study_root", "Expected one parentless study root.", {"found": len(roots)})
    orphans, cycles = [], []
    for key, row in events.items():
        parent = row["parentEventID"]
        if parent and parent not in events: orphans.append({"eventID": key, "parentEventID": parent})
        seen, current = set(), key
        while current:
            if current in seen: cycles.append(key); break
            seen.add(current); current = events.get(current, {}).get("parentEventID", "")
    if orphans: add(findings, "ERROR", "orphan_events", "Event parent IDs are absent.", orphans[:20])
    if cycles: add(findings, "ERROR", "event_cycles", "Event hierarchy cycles detected.", cycles[:20])
    absent_events = sorted(set(source_events) - set(events))
    mismatched_events = [key for key, source in source_events.items() if key in events and row_hash(events[key], source[2]) != source[1]]
    event_extras = sorted(set(events) - set(source_events) - {"TheWilds_2025"})
    if absent_events: add(findings, "ERROR", "events_missing_from_merged", "Source Events absent from merged table.", absent_events[:20])
    if mismatched_events: add(findings, "ERROR", "event_value_mismatch", "Event source values differ in merged table.", mismatched_events[:20])
    if event_extras: add(findings, "WARNING", "unexpected_merged_event", "Unexpected merged Event rows.", event_extras[:20])

    occurrence_counts, modalities, basis, event_uses = Counter(), Counter(), Counter(), Counter()
    ids, mismatch, occurrence_extras, ancestry = set(), [], [], []
    media_paths, empty_media, nonlocal_media = defaultdict(set), Counter(), Counter()
    with occurrence_path.open(newline="", encoding="utf-8") as handle:
        fields = csv_header(occurrence_path)
        missing = sorted((OCC_REQUIRED | {"modality_type"}) - set(fields))
        if missing: add(findings, "ERROR", "missing_merged_occurrence_columns", "Merged Occurrence columns are absent.", missing)
        compare = [x for x in fields if x != "modality_type"]
        for row in csv.DictReader(handle):
            scalar(row, True, occurrence_counts)
            key, modality = row["occurrenceID"], row["modality_type"]
            if key in ids: add(findings, "ERROR", "duplicate_merged_occurrence_id", "Duplicate merged Occurrence ID.", key)
            ids.add(key); modalities[modality] += 1; basis[row["basisOfRecord"]] += 1; event_uses[row["eventID"]] += 1
            source = source_occurrences.get(key)
            if not source: occurrence_extras.append(key)
            elif source[0] != modality or row_hash(row, source[2]) != source[1]: mismatch.append(key)
            expected = MODS.get(modality, (None, None, None))[2]
            if expected and ancestor(row["eventID"], events) != expected: ancestry.append(key)
            media = row.get("associatedMedia", "").strip()
            if not media: empty_media[modality] += 1
            elif media.startswith("/"): media_paths[modality].add(media)
            else: nonlocal_media[modality] += 1
    tables["occurrences_all_modalities.csv"] = {"rows": len(ids), "sha256": sha(occurrence_path)}
    absent_occurrences = sorted(set(source_occurrences) - ids)
    if absent_occurrences: add(findings, "ERROR", "occurrences_missing_from_merged", "Source Occurrences absent from merged table.", absent_occurrences[:20])
    if occurrence_extras: add(findings, "ERROR", "merged_occurrences_not_in_sources", "Merged Occurrences absent from modality files.", occurrence_extras[:20])
    if mismatch: add(findings, "ERROR", "occurrence_value_mismatch", "Occurrence source values differ in merged table.", mismatch[:20])
    if ancestry: add(findings, "ERROR", "modality_ancestry_mismatch", "Occurrence modality conflicts with Event ancestry.", ancestry[:20])
    missing_media = {}
    for modality, paths in media_paths.items():
        absent = [item for item in paths if not Path(item).is_file()]
        if absent:
            missing_media[modality] = len(absent)
            add(findings, "WARNING", "missing_local_media", "Local associatedMedia paths do not exist.", {"modality": modality, "count": len(absent), "examples": absent[:10]})

    issues = dict(sorted((event_counts + occurrence_counts).items()))
    for code, count in issues.items():
        add(findings, "ERROR", code, "Scalar validation failed.", {"count": count})
    generator = root / "scripts/generate_darwin_core_latest_20261008.py"
    expected_root_date = None
    if generator.is_file():
        match = re.search(r'STUDY_ROOT_EVENT\s*=\s*\{.*?"eventDate"\s*:\s*"([^"]*)"', generator.read_text(), re.S)
        if match:
            expected_root_date = match.group(1)
            if expected_root_date != events["TheWilds_2025"]["eventDate"]:
                add(findings, "WARNING", "generator_release_root_date_drift", "Generator root date differs from released root date.", {"generator": expected_root_date, "release": events["TheWilds_2025"]["eventDate"]})

    zero_audio = [key for key, row in events.items() if row["eventType"] == "AudioRecording" and event_uses[key] == 0]
    zero_media = [key for key, row in events.items() if row["eventType"] == "MediaEvent" and event_uses[key] == 0]
    checks = {
        "source_to_merged_events": {"status": "pass" if not absent_events and not mismatched_events and not event_extras else "fail"},
        "source_to_merged_occurrences": {"status": "pass" if not absent_occurrences and not occurrence_extras and not mismatch else "fail"},
        "event_hierarchy": {"status": "pass" if len(roots) == 1 and not orphans and not cycles else "fail", "event_types": dict(event_types)},
        "occurrence_event_links_and_ancestry": {"status": "pass" if not ancestry and not occurrence_counts["missing_eventID"] else "fail"},
        "scalar_dates_times_coordinates": {"status": "pass" if not issues else "fail", "issues": issues},
        "media_paths": {"status": "warning" if missing_media else "pass", "checked_unique_local_paths": {x: len(y) for x, y in media_paths.items()}, "missing_local_paths": missing_media, "nonlocal_references": dict(nonlocal_media), "rows_without_media": dict(empty_media)},
        "zero_occurrence_events": {"status": "info", "AudioRecording": len(zero_audio), "MediaEvent": len(zero_media), "media_event_ids": zero_media},
        "generator_release_alignment": {"status": "warning" if expected_root_date != events["TheWilds_2025"]["eventDate"] else "pass", "generator_root_date": expected_root_date, "release_root_date": events["TheWilds_2025"]["eventDate"]},
        "modality_counts": {"status": "pass", "source_events": counts["events"], "source_occurrences": counts["occurrences"], "merged_occurrences": dict(modalities), "basis_of_record": dict(basis)},
    }
    errors = sum(x["severity"] == "ERROR" for x in findings)
    warnings = sum(x["severity"] == "WARNING" for x in findings)
    report = {"snapshot": str(root), "generated_at": datetime.now().isoformat(timespec="seconds"), "tables": tables, "checks": checks, "findings": findings, "summary": {"errors": errors, "warnings": warnings, "passing_checks": sum(x["status"] == "pass" for x in checks.values())}}
    base = root / args.stem
    base.with_suffix(".json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Darwin Core Snapshot Audit", "", "Errors: %d" % errors, "Warnings: %d" % warnings, "", "## Findings", ""]
    if not findings: lines.append("No errors or warnings found.")
    for item in findings:
        lines += ["### %s: %s" % (item["severity"], item["code"]), "", item["message"], "", json.dumps(item["evidence"], indent=2, sort_keys=True), ""]
    lines += ["## Check Status", ""]
    lines += ["- %s: %s" % (name, value["status"]) for name, value in checks.items()]
    base.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
