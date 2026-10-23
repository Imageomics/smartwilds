#!/usr/bin/env python3
"""Generate reproducible arrival-trace inputs from the frozen Darwin Core snapshot.

This analysis product deliberately replaces legacy primitive JSON files whose
timestamp inputs are no longer retained. It does not modify Darwin Core data.
Every output arrival row links to a canonical Event or Occurrence source record.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Callable

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent
EVENTS_SOURCE = SNAPSHOT_DIR / "events_all_modalities.csv"
OCCURRENCES_SOURCE = SNAPSHOT_DIR / "occurrences_all_modalities.csv"
DRONE_SOURCE = SNAPSHOT_DIR / "drones" / "darwin_core_occurrences_drones.csv"
OUT_DIR = SNAPSHOT_DIR / "analysis" / "arrival_traces_v2"

CAMPAIGN_2_START = datetime(2025, 8, 4, 0, 0, 0)
CAMPAIGN_2_END = datetime(2025, 8, 29, 0, 0, 0)
CAMPAIGN_2_HOURS = 600
EXACT_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EXACT_TIME = re.compile(r"^\d{2}:\d{2}:\d{2}$")
CURATED_DRONE_PREFIX = "TheWilds_2025_drone_BIRD_CURATED_"

OUTPUT_FIELDS = [
    "arrivalID",
    "streamID",
    "analysisLayer",
    "analysisUnit",
    "modality",
    "sourceRecordType",
    "sourceID",
    "eventID",
    "eventDate",
    "eventTime",
    "timestamp",
    "timestampPrecision",
    "timeEligible",
    "campaign",
    "basisOfRecord",
    "associatedMedia",
    "sourceSnapshot",
]

STREAMS = (
    {
        "stream_id": "camera_machine_occurrence",
        "output_name": "camera_machine_occurrence_arrivals.csv",
        "analysis_layer": "inference",
        "analysis_unit": "one retained machine-derived camera Occurrence",
        "modality": "camera_traps",
        "source_file": OCCURRENCES_SOURCE,
        "source_record_type": "Occurrence",
        "selector": lambda row: row.get("modality_type") == "camera_traps"
        and row.get("basisOfRecord") == "MachineObservation",
    },
    {
        "stream_id": "acoustic_wav_recording",
        "output_name": "acoustic_wav_recording_arrivals.csv",
        "analysis_layer": "acquisition",
        "analysis_unit": "one AudioRecording Event representing one retained WAV recording",
        "modality": "bioacoustics",
        "source_file": EVENTS_SOURCE,
        "source_record_type": "AudioRecording",
        "selector": lambda row: row.get("eventType") == "AudioRecording",
    },
    {
        "stream_id": "bioacoustic_machine_occurrence",
        "output_name": "bioacoustic_machine_occurrence_arrivals.csv",
        "analysis_layer": "inference",
        "analysis_unit": "one retained machine-derived bioacoustic Occurrence",
        "modality": "bioacoustics",
        "source_file": OCCURRENCES_SOURCE,
        "source_record_type": "Occurrence",
        "selector": lambda row: row.get("modality_type") == "bioacoustics_complete"
        and row.get("basisOfRecord") == "MachineObservation",
    },
    {
        "stream_id": "drone_machine_detection_crop",
        "output_name": "drone_machine_detection_crop_arrivals.csv",
        "analysis_layer": "inference",
        "analysis_unit": "one retained machine-derived drone detection crop; one source DwC Occurrence",
        "modality": "drones",
        "source_file": DRONE_SOURCE,
        "source_record_type": "Occurrence",
        "selector": lambda row: not is_curated_drone_record(row)
        and row.get("basisOfRecord") == "MachineObservation",
    },
    {
        "stream_id": "citizen_science_curated_occurrence",
        "output_name": "citizen_science_curated_occurrence_arrivals.csv",
        "analysis_layer": "curated_observation",
        "analysis_unit": "one retained curated citizen-science taxon Occurrence",
        "modality": "citizen_science",
        "source_file": OCCURRENCES_SOURCE,
        "source_record_type": "Occurrence",
        "selector": lambda row: row.get("modality_type") == "citizen_science",
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_curated_drone_record(row: dict[str, str]) -> bool:
    return (
        row.get("occurrenceID", "").startswith(CURATED_DRONE_PREFIX)
        or "review subset" in row.get("occurrenceRemarks", "").lower()
    )


def campaign_for(event_date: str) -> str:
    if not EXACT_DATE.fullmatch(event_date):
        return "unparseable_or_interval"
    if "2025-06-30" <= event_date <= "2025-07-03":
        return "campaign1"
    if "2025-08-04" <= event_date <= "2025-08-28":
        return "campaign2"
    if event_date == "2025-09-08":
        return "campaign3"
    return "outside_defined_campaigns"


def timestamp_fields(event_date: str, event_time: str) -> tuple[str, str, str]:
    if not EXACT_DATE.fullmatch(event_date):
        return "", "unparseable_or_interval", "false"
    if not event_time:
        return "", "date", "false"
    if not EXACT_TIME.fullmatch(event_time):
        return "", "interval_or_nonsecond", "false"
    timestamp = f"{event_date}T{event_time}"
    datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    return timestamp, "second", "true"


def source_id(row: dict[str, str], source_record_type: str) -> str:
    return row["eventID"] if source_record_type == "AudioRecording" else row["occurrenceID"]


def source_event_id(row: dict[str, str], source_record_type: str) -> str:
    return row["eventID"]


def build_stream(spec: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    source_file = spec["source_file"]
    assert isinstance(source_file, Path)
    selector = spec["selector"]
    assert callable(selector)
    stream_id = str(spec["stream_id"])
    source_record_type = str(spec["source_record_type"])
    output_path = OUT_DIR / str(spec["output_name"])

    selected_rows = 0
    source_ids: set[str] = set()
    timestamp_precision = Counter()
    by_campaign = Counter()
    time_eligible_by_campaign = Counter()
    campaign2_timestamps: list[datetime] = []

    with source_file.open(newline="", encoding="utf-8") as source_handle, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as output_handle:
        reader = csv.DictReader(source_handle)
        writer = csv.DictWriter(output_handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()

        for row in reader:
            if not selector(row):
                continue
            selected_rows += 1
            identifier = source_id(row, source_record_type)
            if identifier in source_ids:
                raise ValueError(f"{stream_id}: duplicate source ID {identifier}")
            source_ids.add(identifier)

            event_date = row.get("eventDate", "")
            event_time = row.get("eventTime", "")
            timestamp, precision, eligible = timestamp_fields(event_date, event_time)
            campaign = campaign_for(event_date)
            timestamp_precision[precision] += 1
            by_campaign[campaign] += 1
            if eligible == "true":
                time_eligible_by_campaign[campaign] += 1
                if campaign == "campaign2":
                    campaign2_timestamps.append(
                        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                    )

            writer.writerow(
                {
                    "arrivalID": f"TheWilds_2025_arrival_v2_{stream_id}_{selected_rows:06d}",
                    "streamID": stream_id,
                    "analysisLayer": spec["analysis_layer"],
                    "analysisUnit": spec["analysis_unit"],
                    "modality": spec["modality"],
                    "sourceRecordType": source_record_type,
                    "sourceID": identifier,
                    "eventID": source_event_id(row, source_record_type),
                    "eventDate": event_date,
                    "eventTime": event_time,
                    "timestamp": timestamp,
                    "timestampPrecision": precision,
                    "timeEligible": eligible,
                    "campaign": campaign,
                    "basisOfRecord": row.get("basisOfRecord", ""),
                    "associatedMedia": row.get("associatedMedia", ""),
                    "sourceSnapshot": SNAPSHOT_DIR.name,
                }
            )

    campaign2_timestamps.sort()
    for timestamp in campaign2_timestamps:
        if not CAMPAIGN_2_START <= timestamp < CAMPAIGN_2_END:
            raise ValueError(f"{stream_id}: timestamp outside Campaign 2: {timestamp}")

    intervals = [
        (later - earlier).total_seconds()
        for earlier, later in zip(campaign2_timestamps, campaign2_timestamps[1:])
    ]
    mean_interarrival = statistics.fmean(intervals) if intervals else None
    cv = (
        statistics.pstdev(intervals) / mean_interarrival
        if len(intervals) >= 2 and mean_interarrival and mean_interarrival > 0
        else None
    )
    burstiness = (cv - 1) / (cv + 1) if cv is not None else None
    timed_campaign2_rows = time_eligible_by_campaign["campaign2"]

    summary = {
        "stream_id": stream_id,
        "analysis_layer": spec["analysis_layer"],
        "analysis_unit": spec["analysis_unit"],
        "modality": spec["modality"],
        "source_file": str(source_file.relative_to(SNAPSHOT_DIR)),
        "source_sha256": sha256(source_file),
        "output_file": output_path.name,
        "output_sha256": sha256(output_path),
        "source_record_type": source_record_type,
        "counts": {
            "selected_source_rows": selected_rows,
            "by_campaign": dict(sorted(by_campaign.items())),
            "time_eligible_by_campaign": dict(sorted(time_eligible_by_campaign.items())),
            "timestamp_precision": dict(sorted(timestamp_precision.items())),
        },
        "campaign2_statistics": {
            "window_start": CAMPAIGN_2_START.isoformat(),
            "window_end_exclusive": CAMPAIGN_2_END.isoformat(),
            "window_hours": CAMPAIGN_2_HOURS,
            "time_eligible_arrivals": timed_campaign2_rows,
            "observation_window_rate_per_hour": timed_campaign2_rows / CAMPAIGN_2_HOURS,
            "interarrival_interval_count": len(intervals),
            "mean_interarrival_seconds": mean_interarrival,
            "interarrival_cv_population": cv,
            "burstiness_B": burstiness,
        },
        "validation": {
            "unique_source_ids": len(source_ids),
            "selected_source_rows_equal_unique_source_ids": len(source_ids) == selected_rows,
            "campaign2_timestamps_within_window": True,
        },
    }
    return summary, {
        "stream_id": stream_id,
        "source_file": str(source_file.relative_to(SNAPSHOT_DIR)),
        "source_sha256": sha256(source_file),
        "output_file": output_path.name,
        "output_sha256": sha256(output_path),
    }


def main() -> None:
    for source in (EVENTS_SOURCE, OCCURRENCES_SOURCE, DRONE_SOURCE):
        if not source.exists():
            raise SystemExit(f"Missing canonical source: {source}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stream_summaries = []
    inputs = []
    for spec in STREAMS:
        summary, manifest_entry = build_stream(spec)
        stream_summaries.append(summary)
        inputs.append(manifest_entry)

    expected = {
        "camera_machine_occurrence": 208054,
        "acoustic_wav_recording": 2060,
        "bioacoustic_machine_occurrence": 8865,
        "drone_machine_detection_crop": 53238,
        "citizen_science_curated_occurrence": 242,
    }
    observed = {
        summary["stream_id"]: summary["campaign2_statistics"]["time_eligible_arrivals"]
        for summary in stream_summaries
    }
    if observed != expected:
        raise SystemExit(f"Unexpected Campaign 2 timed counts: {observed}")

    contract = {
        "product": "The Wilds 2025 reproducible arrival traces v2",
        "product_type": "derived analysis inputs and summaries; not Darwin Core tables or extensions",
        "source_snapshot": SNAPSHOT_DIR.name,
        "campaign2_window": {
            "start": CAMPAIGN_2_START.isoformat(),
            "end_exclusive": CAMPAIGN_2_END.isoformat(),
            "nominal_hours": CAMPAIGN_2_HOURS,
            "timestamp_timezone_policy": "Source-local civil time; no UTC conversion is asserted by the source tables.",
        },
        "rate_definition": "time-eligible arrivals divided by the fixed 600-hour Campaign 2 observation window",
        "interarrival_definition": "successive sorted second-level timestamps within Campaign 2; equal timestamps yield zero-second intervals",
        "cv_definition": "population standard deviation divided by mean inter-arrival interval",
        "burstiness_definition": "B = (CV - 1) / (CV + 1)",
        "streams": stream_summaries,
        "unavailable_streams": [
            {
                "stream_id": "camera_image_capture_acquisition",
                "reason": "The frozen snapshot retains machine detections but not a timestamped manifest of all camera image captures, including images without detections.",
                "not_substituted_with": "camera_machine_occurrence",
                "recovery_requirement": "Retain a corrected, one-row-per-image capture timestamp manifest with source image identifiers and checksum.",
            }
        ],
        "validation": {
            "expected_campaign2_time_eligible_counts": expected,
            "observed_campaign2_time_eligible_counts": observed,
            "all_expected_counts_match": observed == expected,
        },
        "generated_by": str(Path(__file__).relative_to(SNAPSHOT_DIR)),
    }
    (OUT_DIR / "arrival_trace_contract_v2.json").write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "input_manifest_v2.json").write_text(
        json.dumps(
            {
                "source_snapshot": SNAPSHOT_DIR.name,
                "inputs": inputs,
                "generator": str(Path(__file__).relative_to(SNAPSHOT_DIR)),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(contract["validation"], indent=2))


if __name__ == "__main__":
    main()
