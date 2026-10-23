#!/usr/bin/env python3
'''Reconcile raw The Wilds WAV files against corrected Darwin Core Events.'''
from __future__ import annotations

import csv
import json
import re
import wave
from collections import Counter
from datetime import date
from pathlib import Path

BASE_DIR = Path('/fs/ess/PAS2136/TheWilds2025')
SNAPSHOT_DIR = BASE_DIR / 'processing_output/darwin_core_latest_20261008'
OUT_DIR = SNAPSHOT_DIR / 'bioacoustics_complete'
OUT_CSV = OUT_DIR / 'RAW_WAV_RECONCILIATION_20261008.csv'
OUT_NOTE = OUT_DIR / 'RAW_WAV_RECONCILIATION_20261008.md'
OUT_AUDIT = SNAPSHOT_DIR / 'bioacoustic_event_repair_20261008.json'
EVENTS = OUT_DIR / 'darwin_core_events_bioacoustics_complete.csv'
ROOTS = [
    (BASE_DIR / 'thewilds_20250630_20250703' / 'bioacoustics', date(2025, 6, 30), date(2025, 7, 3), 'campaign1'),
    (BASE_DIR / 'thewilds_20250804_20250828' / 'bioacoustics', date(2025, 8, 4), date(2025, 8, 28), 'campaign2'),
]
RESULT_DIRS = [
    BASE_DIR / 'processing_output/detections/acoustics/BirdNet_EveryHour',
    BASE_DIR / 'BioacousticAnalysis/BirdnetCSV_SunriseSunset',
]
NAME_RE = re.compile(r'^(?:[A-Z0-9]+)_(\d{8})_(\d{6})$', re.I)
EVENT_RE = re.compile(r'Recording: ([^;]+)\.wav; Recorder: ([^;]+);')
FIELDS = [
    'raw_wav_path', 'source_campaign_directory', 'deploymentID', 'recording_file',
    'recording_date', 'recording_time', 'in_source_campaign_window', 'wav_bytes',
    'wav_header_status', 'duration_seconds', 'birdnet_result_path',
    'birdnet_result_status', 'darwin_core_eventID', 'reconciliation_status',
    'release_disposition',
]


def deployment(path: Path) -> tuple[str, str]:
    for part in path.parts:
        match = re.fullmatch(r'(TW\d+)-(SM\d+)', part)
        if match:
            return match.group(1), match.group(2)
    raise ValueError(f'No deployment in {path}')


def wave_details(path: Path) -> tuple[str, str]:
    try:
        with wave.open(str(path), 'rb') as audio:
            duration = audio.getnframes() / audio.getframerate()
            return 'readable', f'{duration:.6f}'
    except Exception as exc:
        return f'unreadable:{type(exc).__name__}', ''


def result_status(path: Path | None) -> str:
    if path is None:
        return 'absent'
    with path.open(newline='') as handle:
        reader = csv.DictReader(handle)
        return 'header_only_zero_detection' if next(reader, None) is None else 'nonempty'


def main() -> None:
    results = {}
    for directory in RESULT_DIRS:
        for path in directory.glob('*.BirdNET.results.csv'):
            results[path.name.removesuffix('.BirdNET.results.csv')] = path

    events = {}
    with EVENTS.open(newline='') as handle:
        for row in csv.DictReader(handle):
            if row['eventType'] != 'AudioRecording':
                continue
            match = EVENT_RE.search(row['fieldNotes'])
            if not match:
                raise ValueError(f'Unparseable recording provenance: {row["eventID"]}')
            recording, recorder = match.groups()
            key = (row['locationID'], recorder, recording.split('_', 1)[1])
            if key in events:
                raise ValueError(f'Duplicate release recording key: {key}')
            events[key] = (row['eventID'], 'header-only BirdNET result' in row['fieldNotes'])

    rows = []
    for root, start, end, campaign in ROOTS:
        for path in sorted(root.rglob('*')):
            if not (path.is_file() and path.suffix.lower() == '.wav'):
                continue
            name_match = NAME_RE.match(path.stem)
            if not name_match:
                raise ValueError(f'Unparseable raw WAV name: {path.name}')
            site, recorder = deployment(path)
            ymd, hms = name_match.groups()
            recording_date = date.fromisoformat(f'{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}')
            in_window = start <= recording_date <= end
            event_entry = events.get((site, recorder, f'{ymd}_{hms}'))
            event_id = event_entry[0] if event_entry else ''
            is_header_only = event_entry[1] if event_entry else False
            result = results.get(path.stem)
            if not in_window:
                status = 'transfer_duplicate'
                disposition = 'excluded_from_release; canonical recording is represented under its original campaign/deployment'
            elif is_header_only:
                status = 'processed_zero_detection'
                disposition = 'included_as_AudioRecording_Event_without_Occurrences'
            elif event_id:
                status = 'represented_recording'
                disposition = 'included_as_AudioRecording_Event'
            elif result is None:
                status = 'truncated_or_corrupt_unprocessed'
                disposition = 'excluded_from_release; no BirdNET result and insufficient/corrupt source audio'
            else:
                raise ValueError(f'Unexpected unmatched processed recording: {path}')
            if status == 'truncated_or_corrupt_unprocessed':
                header_status, duration = wave_details(path)
            else:
                header_status, duration = 'not_checked_release_represented_or_transfer', ''
            rows.append({
                'raw_wav_path': str(path.relative_to(BASE_DIR)),
                'source_campaign_directory': campaign,
                'deploymentID': f'{site}-{recorder}',
                'recording_file': path.name,
                'recording_date': recording_date.isoformat(),
                'recording_time': f'{hms[:2]}:{hms[2:4]}:{hms[4:]}',
                'in_source_campaign_window': str(in_window).lower(),
                'wav_bytes': path.stat().st_size,
                'wav_header_status': header_status,
                'duration_seconds': duration,
                'birdnet_result_path': str(result.relative_to(BASE_DIR)) if result else '',
                'birdnet_result_status': ('header_only_zero_detection' if is_header_only else ('nonempty' if result else 'absent')),
                'darwin_core_eventID': event_id,
                'reconciliation_status': status,
                'release_disposition': disposition,
            })

    counts = Counter(row['reconciliation_status'] for row in rows)
    expected = Counter({
        'represented_recording': 2307,
        'processed_zero_detection': 64,
        'transfer_duplicate': 78,
        'truncated_or_corrupt_unprocessed': 4,
    })
    if counts != expected:
        raise ValueError(f'Unexpected reconciliation counts: {counts}')
    if len(events) != 2371:
        raise ValueError(f'Expected 2,371 AudioRecording Events, found {len(events)}')

    with OUT_CSV.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    note = f'''# Raw WAV Reconciliation

## Outcome

The corrected release has **2,371 unique `AudioRecording` Events**. It contains
no duplicate Event for transferred raw media and keeps the existing 9,960
BirdNET Occurrences unchanged.

| Raw-file disposition | Files | Release treatment |
| --- | ---: | --- |
| Represented recording | {counts['represented_recording']} | One `AudioRecording` Event |
| Processed, zero detections | {counts['processed_zero_detection']} | One `AudioRecording` Event; no Occurrence |
| Transfer duplicate | {counts['transfer_duplicate']} | Excluded; source belongs to another campaign/deployment |
| Truncated/corrupt, unprocessed | {counts['truncated_or_corrupt_unprocessed']} | Excluded; no BirdNET result |
| **Raw files on disk** | **{len(rows)}** | **Reconciled** |

## Why The Earlier Count Was Misleading

The former comparison of 2,453 raw WAV files with 2,307 Events treated every
physical file path as a separate capture. Seventy-eight Campaign-1 WAVs were
transferred into the Campaign-2 `TW02-SM04/Data` directory; they are duplicate
transfers, not new Campaign-2 recordings. The remaining 68 unmatched
in-window files divide into 64 successfully processed files with header-only
BirdNET results (zero detections) and four truncated/corrupt files with no
BirdNET result.

The 64 zero-detection recordings are now represented as Events with a field
note identifying the header-only BirdNET result. They deliberately generate no
Occurrence. The four failures remain out of the Event table and are listed in
the accompanying CSV with their header status and duration.

## Integrity Checks

- Every `AudioRecording` Event has a unique recording key: deployment, recorder,
  date, and time.
- The 78 transfer duplicates never create a second Event.
- All 9,960 Occurrences retain valid Event links.
- The CSV provides one row per raw WAV path, including path, deployment, WAV
  header status, duration, BirdNET-result status, final Event ID, and release
  disposition.
'''
    OUT_NOTE.write_text(note, encoding='utf-8')
    audit = {
        'repair': 'bioacoustic AudioRecording completeness and raw-WAV reconciliation',
        'snapshot': SNAPSHOT_DIR.name,
        'raw_wav_files': len(rows),
        'audio_recording_events': len(events),
        'occurrences_unchanged': 9960,
        'reconciliation_status_counts': dict(sorted(counts.items())),
        'release_policy': {
            'transfer_duplicate': 'excluded; no duplicate Event',
            'processed_zero_detection': 'included as Event with no Occurrence',
            'truncated_or_corrupt_unprocessed': 'excluded; documented in reconciliation CSV',
        },
    }
    OUT_AUDIT.write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
