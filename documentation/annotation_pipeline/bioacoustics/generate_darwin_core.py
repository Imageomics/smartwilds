#!/usr/bin/env python3
"""
Generate Darwin Core Events and Occurrences from BirdNET bioacoustic analysis.

Input:  WildsBird_Sunrise_Sunset.csv (534 recording events, sunrise/sunset schedule)
        WildsBird_Every_Hour.csv     (1180 recording events, hourly schedule)
        Sensor metadata from deployment records

Output: darwin_core_events_bioacoustics.csv     (hierarchical: project → campaign → deployment → recording)
        darwin_core_occurrences_bioacoustics.csv (one row per species per recording with count > 0)

Each WAV recording = one Event.
Each species detected in that recording = one Occurrence (with detection count).
"""

import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
OUTPUT_DIR = BASE_DIR / "processing_output" / "darwin_core" / "bioacoustics"

# ─── Sensor deployment metadata ───────────────────────────────────────────────

DEPLOYMENTS = {
    # Campaign 1: June 30 – July 3, 2025
    "SM01_C1": {
        "recorderID": "SM01", "serialNumber": "2MM15088",
        "siteID": "TW05", "siteName": "Lake Trail Gate O",
        "lat": 39.83537, "lon": -81.73842,
        "deployDate": "2025-06-30", "retrieveDate": "2025-07-03",
        "schedule": "5-min clips every hour (intended 1hr sunrise/sunset — config error)",
        "dutyCycle": "8.3% (5 min/hr)",
        "orientation": "East, facing away from wind and road",
        "height_m": 1.5, "campaign": "20250630_20250703",
        "observer": "Tanishka Wani",
    },
    "SM03_C1": {
        "recorderID": "SM03", "serialNumber": "2MM18173",
        "siteID": "TW06", "siteName": "Zebra Shelter",
        "lat": 39.83518, "lon": -81.73087,
        "deployDate": "2025-06-30", "retrieveDate": "2025-07-03",
        "schedule": "5 min every hour, top of hour, 24/7",
        "dutyCycle": "8.3% (5 min/hr, 24/7)",
        "orientation": "Southeast",
        "height_m": 2.0, "campaign": "20250630_20250703",
        "observer": "Tanishka Wani",
    },
    "SM02_C1": {
        "recorderID": "SM02", "serialNumber": "2MM15093",
        "siteID": "TW07", "siteName": "Zipline Tower",
        "lat": 39.83288, "lon": -81.73455,
        "deployDate": "2025-06-30", "retrieveDate": "2025-07-03",
        "schedule": "1 hour at sunrise + 1 hour at sunset",
        "dutyCycle": "~14% (2 hrs/day)",
        "orientation": "Southwest",
        "height_m": 1.5, "campaign": "20250630_20250703",
        "observer": "Tanishka Wani",
    },
    "SM04_C1": {
        "recorderID": "SM04", "serialNumber": "2MM18039",
        "siteID": "TW08", "siteName": "Fence with Vegetation",
        "lat": 39.82900, "lon": -81.74378,
        "deployDate": "2025-06-30", "retrieveDate": "2025-07-03",
        "schedule": "5 min every hour, top of hour, 24/7",
        "dutyCycle": "8.3% (5 min/hr, 24/7)",
        "orientation": "Southwest",
        "height_m": 1.5, "campaign": "20250630_20250703",
        "observer": "Tanishka Wani",
    },
    # Campaign 2: August 4 – 28, 2025
    "SM04_C2": {
        "recorderID": "SM04", "serialNumber": "2MM18039",
        "siteID": "TW02", "siteName": "Nomad Ridge Shelter",
        "lat": 39.82957, "lon": -81.73295,
        "deployDate": "2025-08-04", "retrieveDate": "2025-08-28",
        "schedule": "5 min every hour",
        "dutyCycle": "8.3% (5 min/hr)",
        "orientation": "Right side of shelter",
        "height_m": 1.5, "campaign": "20250804_20250828",
        "observer": "Jenna Kline",
    },
    "SM06_C2": {
        "recorderID": "SM06",
        "siteID": "TW05", "siteName": "Lake Trail Gate O",
        "lat": 39.82866, "lon": -81.73758,
        "deployDate": "2025-08-04", "retrieveDate": "2025-08-28",
        "schedule": "Sunrise to sunset (continuous)",
        "dutyCycle": "~50-60% (sunrise-sunset)",
        "orientation": "Gate post",
        "height_m": 1.5, "campaign": "20250804_20250828",
        "observer": "Jenna Kline",
    },
    "SM05_C2": {
        "recorderID": "SM05",
        "siteID": "TW06", "siteName": "Zebra Shelter",
        "lat": 39.82870, "lon": -81.73756,
        "deployDate": "2025-08-04", "retrieveDate": "2025-08-28",
        "schedule": "15 min every hour",
        "dutyCycle": "25% (15 min/hr)",
        "orientation": "Zebra Shelter",
        "height_m": 1.5, "campaign": "20250804_20250828",
        "observer": "Jenna Kline",
    },
    "SM02_C2": {
        "recorderID": "SM02", "serialNumber": "2MM15093",
        "siteID": "TW07", "siteName": "Zipline Tower",
        "lat": 39.82891, "lon": -81.74392,
        "deployDate": "2025-08-04", "retrieveDate": "2025-08-28",
        "schedule": "Sunrise to sunset (continuous)",
        "dutyCycle": "~50-60% (sunrise-sunset)",
        "orientation": "Zipline tower",
        "height_m": 1.5, "campaign": "20250804_20250828",
        "observer": "Jenna Kline",
    },
    "SM03_C2": {
        "recorderID": "SM03",
        "siteID": "TW08", "siteName": "Fence with Vegetation",
        "lat": 39.82892, "lon": -81.74392,
        "deployDate": "2025-08-04", "retrieveDate": "2025-08-28",
        "schedule": "Sunrise to sunset (continuous)",
        "dutyCycle": "~50-60% (sunrise-sunset)",
        "orientation": "Fence",
        "height_m": 1.5, "campaign": "20250804_20250828",
        "observer": "Jenna Kline",
    },
    "SM01_C2": {
        "recorderID": "SM01", "serialNumber": "2MM15088",
        "siteID": "TW09", "siteName": "Dock",
        "lat": 39.83418, "lon": -81.73783,
        "deployDate": "2025-08-14", "retrieveDate": "2025-08-28",
        "schedule": "Sunrise to sunset (continuous)",
        "dutyCycle": "~50-60% (sunrise-sunset)",
        "orientation": "Left side of dock",
        "height_m": 1.5, "campaign": "20250804_20250828",
        "observer": "Jenna Kline",
    },
}

# BirdNET analysis parameters (from BirdNET_analysis_params.csv)
BIRDNET_PARAMS = {
    "model": "BirdNET Analyzer",
    "version": "2.4",
    "segmentLength": 3.0,
    "sampleRate": 48000,
    "segmentOverlap": 0.0,
    "minSegmentLength": 1.0,
    "bandpassMin": 0,
    "bandpassMax": 15000,
    "mergeConsecutive": True,
    "audioSpeed": 1.0,
    "fileSplitDuration": 600,
}


def lookup_deployment(file_id: str, location: str, dt_str: str) -> dict:
    """Match a recording to its deployment based on recorder ID, site, and date."""
    # Extract recorder ID from file_id (e.g., SM04_20250812_190000 → SM04)
    recorder_id = file_id.split("_")[0]

    # Normalize recorder IDs (SM001 → SM01, 2MM18157 → SM05)
    id_map = {"SM001": "SM01", "SM002": "SM02", "2MM18157": "SM05", "2MM18027": "SM06"}
    recorder_id = id_map.get(recorder_id, recorder_id)

    date_str = dt_str[:10] if dt_str else ""

    # Try matching by recorder + campaign date range
    for key, dep in DEPLOYMENTS.items():
        if dep["recorderID"] == recorder_id:
            if dep["deployDate"] <= date_str <= dep["retrieveDate"]:
                return dep

    # Fallback: match by location
    for key, dep in DEPLOYMENTS.items():
        if dep["siteID"] == location:
            if dep["deployDate"] <= date_str <= dep["retrieveDate"]:
                return dep

    return None


def process_aggregated_csv(csv_path: str, schedule_type: str):
    """Process an aggregated BirdNET CSV into events and occurrences."""
    events = []
    occurrences = []
    occ_num = 0
    species_total = defaultdict(int)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        species_cols = [
            c for c in reader.fieldnames
            if c not in ("datetime", "location", "file_ID", "total_birds", "1", "")
        ]

        for row in reader:
            dt_str = row.get("datetime", "")
            location = row.get("location", "")
            file_id = row.get("file_ID", "")
            total_birds = int(row.get("total_birds", 0))

            # Parse datetime
            date_str = dt_str[:10] if dt_str else ""
            time_str = dt_str[11:19] if len(dt_str) > 10 else ""

            # Match to deployment
            dep = lookup_deployment(file_id, location, dt_str)
            if dep is None:
                dep = {
                    "siteID": location, "siteName": location,
                    "lat": 39.83, "lon": -81.74,
                    "schedule": schedule_type, "dutyCycle": "",
                    "recorderID": file_id.split("_")[0], "campaign": "",
                }

            # Create recording event
            event_id = f"TheWilds_2025_ARU_{file_id}"

            sampling_protocol = (
                f"Passive acoustic monitoring; Wildlife Acoustics Song Meter Micro 2; "
                f"Schedule: {dep.get('schedule', schedule_type)}; "
                f"Duty cycle: {dep.get('dutyCycle', '')}; "
                f"Annotated by {BIRDNET_PARAMS['model']} v{BIRDNET_PARAMS['version']} "
                f"(segment={BIRDNET_PARAMS['segmentLength']}s, "
                f"SR={BIRDNET_PARAMS['sampleRate']}Hz, "
                f"bandpass={BIRDNET_PARAMS['bandpassMin']}-{BIRDNET_PARAMS['bandpassMax']}Hz)"
            )

            event = {
                "eventID": event_id,
                "parentEventID": f"TheWilds_2025_ARU_deployment_{dep.get('siteID', location)}_{dep.get('campaign', '')}",
                "eventType": "AudioRecording",
                "eventDate": date_str,
                "eventTime": time_str,
                "samplingProtocol": sampling_protocol,
                "sampleSizeValue": 1,
                "sampleSizeUnit": "WAV recording",
                "locality": f"The Wilds - {dep.get('siteName', location)}",
                "locationID": dep.get("siteID", location),
                "decimalLatitude": dep.get("lat", ""),
                "decimalLongitude": dep.get("lon", ""),
                "coordinateUncertaintyInMeters": 50,
                "geodeticDatum": "WGS84",
                "country": "United States",
                "stateProvince": "Ohio",
                "county": "Muskingum",
                "datasetID": "TheWilds_2025_bioacoustics",
                "datasetName": "The Wilds 2025 Multi-Modal Survey - Bioacoustics",
                "recordedBy": dep.get("observer", ""),
                "fieldNotes": (
                    f"Recording: {file_id}.wav; "
                    f"Recorder: {dep.get('recorderID', '')}; "
                    f"Total BirdNET detections: {total_birds}; "
                    f"Schedule type: {schedule_type}"
                ),
            }
            events.append(event)

            # Create occurrences for each detected species
            for sp_col in species_cols:
                count = int(row.get(sp_col, 0))
                if count == 0:
                    continue

                occ_num += 1
                common_name = sp_col.replace("_", " ")
                species_total[common_name] += count

                occ = {
                    "occurrenceID": f"TheWilds_2025_ARU_{occ_num:06d}",
                    "eventID": event_id,
                    "catalogNumber": f"ARU_{file_id}_{sp_col}",

                    # Taxonomy — BirdNET provides common names; scientific names are
                    # in the raw CSVs but not the aggregated. Leave for downstream enrichment.
                    "scientificName": "",
                    "kingdom": "Animalia",
                    "phylum": "Chordata",
                    "class": "Aves",
                    "order": "",
                    "family": "",
                    "genus": "",
                    "specificEpithet": "",
                    "taxonRank": "species",
                    "vernacularName": common_name,

                    # Observation
                    "occurrenceStatus": "present",
                    "individualCount": count,
                    "basisOfRecord": "MachineObservation",
                    "recordedBy": f"Song Meter Micro 2 ({dep.get('recorderID', '')})",
                    "identifiedBy": f"BirdNET Analyzer v{BIRDNET_PARAMS['version']}",
                    "identificationVerificationStatus": "unverified",
                    "identificationRemarks": (
                        f"Automated classification by BirdNET; "
                        f"{count} detection(s) in recording {file_id}.wav; "
                        f"segment={BIRDNET_PARAMS['segmentLength']}s, "
                        f"bandpass={BIRDNET_PARAMS['bandpassMin']}-{BIRDNET_PARAMS['bandpassMax']}Hz"
                    ),

                    # Temporal
                    "eventDate": date_str,
                    "eventTime": time_str,

                    # Spatial
                    "decimalLatitude": dep.get("lat", ""),
                    "decimalLongitude": dep.get("lon", ""),
                    "coordinateUncertaintyInMeters": 50,
                    "geodeticDatum": "WGS84",
                    "locality": f"The Wilds - {dep.get('siteName', location)}",
                    "locationID": dep.get("siteID", location),
                    "country": "United States",
                    "stateProvince": "Ohio",
                    "county": "Muskingum",

                    # Provenance
                    "establishmentMeans": "wild",
                    "degreeOfEstablishment": "native",
                    "occurrenceRemarks": "",
                    "associatedMedia": f"{file_id}.wav",

                    # Dataset
                    "datasetID": "TheWilds_2025_bioacoustics",
                    "datasetName": "The Wilds 2025 Multi-Modal Survey - Bioacoustics",
                }
                occurrences.append(occ)

    return events, occurrences, species_total


def main():
    print("=" * 60)
    print("Bioacoustics Darwin Core Generation")
    print("=" * 60)

    all_events = []
    all_occurrences = []
    all_species = defaultdict(int)

    # Project-level event
    all_events.append({
        "eventID": "TheWilds_2025_bioacoustics",
        "parentEventID": "TheWilds_2025",
        "eventType": "Project",
        "eventDate": "2025-06-30/2025-08-28",
        "samplingProtocol": (
            "Passive acoustic monitoring using Wildlife Acoustics Song Meter Micro 2 recorders; "
            "Multiple recording schedules: 5 min/hr, 15 min/hr, 1hr sunrise+sunset, continuous sunrise-sunset; "
            "All recordings analyzed with BirdNET Analyzer v2.4"
        ),
        "sampleSizeValue": "",
        "sampleSizeUnit": "",
        "locality": "The Wilds Conservation Center, Muskingum County, Ohio, USA",
        "locationID": "",
        "decimalLatitude": 39.83,
        "decimalLongitude": -81.74,
        "coordinateUncertaintyInMeters": 5000,
        "geodeticDatum": "WGS84",
        "country": "United States",
        "stateProvince": "Ohio",
        "county": "Muskingum",
        "datasetID": "TheWilds_2025_bioacoustics",
        "datasetName": "The Wilds 2025 Multi-Modal Survey - Bioacoustics",
        "recordedBy": "Tanishka Wani; Jenna Kline",
        "fieldNotes": (
            "10 Song Meter Micro 2 deployments across 6 sites, 2 campaigns. "
            "2,453 WAV files totaling 202 GB. "
            "Analyzed with BirdNET: 3s segments, 48kHz, 0-15kHz bandpass."
        ),
    })

    # Deployment-level events
    for key, dep in sorted(DEPLOYMENTS.items()):
        dep_event = {
            "eventID": f"TheWilds_2025_ARU_deployment_{dep['siteID']}_{dep['campaign']}",
            "parentEventID": "TheWilds_2025_bioacoustics",
            "eventType": "SensorDeployment",
            "eventDate": f"{dep['deployDate']}/{dep['retrieveDate']}",
            "samplingProtocol": (
                f"Song Meter Micro 2 ({dep['recorderID']}); "
                f"Schedule: {dep['schedule']}; Duty cycle: {dep['dutyCycle']}; "
                f"Orientation: {dep.get('orientation', '')}; "
                f"Height: {dep.get('height_m', '')}m"
            ),
            "sampleSizeValue": "",
            "sampleSizeUnit": "",
            "locality": f"The Wilds - {dep['siteName']}",
            "locationID": dep["siteID"],
            "decimalLatitude": dep["lat"],
            "decimalLongitude": dep["lon"],
            "coordinateUncertaintyInMeters": 50,
            "geodeticDatum": "WGS84",
            "country": "United States",
            "stateProvince": "Ohio",
            "county": "Muskingum",
            "datasetID": "TheWilds_2025_bioacoustics",
            "datasetName": "The Wilds 2025 Multi-Modal Survey - Bioacoustics",
            "recordedBy": dep.get("observer", ""),
            "fieldNotes": (
                f"Recorder: {dep['recorderID']} (SN: {dep.get('serialNumber', 'unknown')}); "
                f"Campaign: {dep['campaign']}"
            ),
        }
        all_events.append(dep_event)

    # Process sunrise/sunset recordings
    ss_path = BASE_DIR / "BioacousticAnalysis" / "WildsBird_Sunrise_Sunset.csv"
    print(f"\nProcessing sunrise/sunset recordings: {ss_path}")
    events, occs, sp_counts = process_aggregated_csv(str(ss_path), "sunrise_sunset")
    all_events.extend(events)
    all_occurrences.extend(occs)
    for sp, ct in sp_counts.items():
        all_species[sp] += ct
    print(f"  {len(events)} recording events, {len(occs)} occurrences")

    # Process hourly recordings
    hr_path = BASE_DIR / "BioacousticAnalysis" / "WildsBird_Every_Hour.csv"
    print(f"Processing hourly recordings: {hr_path}")
    events, occs, sp_counts = process_aggregated_csv(str(hr_path), "every_hour")
    all_events.extend(events)
    all_occurrences.extend(occs)
    for sp, ct in sp_counts.items():
        all_species[sp] += ct
    print(f"  {len(events)} recording events, {len(occs)} occurrences")

    # Write outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Events
    events_path = OUTPUT_DIR / "darwin_core_events_bioacoustics.csv"
    all_keys = []
    seen = set()
    for e in all_events:
        for k in e.keys():
            if k not in seen:
                all_keys.append(k)
                seen.add(k)
    with open(events_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_events)
    print(f"\nWrote {len(all_events)} Events to {events_path}")

    # Occurrences
    occ_path = OUTPUT_DIR / "darwin_core_occurrences_bioacoustics.csv"
    if all_occurrences:
        fieldnames = list(all_occurrences[0].keys())
        with open(occ_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_occurrences)
    print(f"Wrote {len(all_occurrences)} Occurrences to {occ_path}")

    # Summary
    print(f"\n{'='*60}")
    print("Bioacoustics Darwin Core Summary")
    print(f"{'='*60}")
    recording_events = len([e for e in all_events if e["eventType"] == "AudioRecording"])
    deployment_events = len([e for e in all_events if e["eventType"] == "SensorDeployment"])
    print(f"  Event hierarchy:")
    print(f"    1 Project event")
    print(f"    {deployment_events} Deployment events (with sensor configs)")
    print(f"    {recording_events} Recording events (individual WAV files)")
    print(f"  Occurrence records: {len(all_occurrences)}")
    print(f"  Unique species:     {len(all_species)}")

    print(f"\n  Top 20 species by detection count:")
    for sp, count in sorted(all_species.items(), key=lambda x: -x[1])[:20]:
        print(f"    {sp:<35} {count:>7}")

    total_det = sum(all_species.values())
    print(f"\n  Total detections: {total_det:,}")


if __name__ == "__main__":
    main()
