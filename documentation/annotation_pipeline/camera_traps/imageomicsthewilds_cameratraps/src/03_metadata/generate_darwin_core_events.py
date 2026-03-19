"""
Generate Darwin Core Event records for camera trap deployments.

Events represent distinct survey sessions (camera deployments). Each event
corresponds to one camera being deployed at one location for a specific time period.

This follows Darwin Core standards with TDWG compliance for biodiversity data.
See: https://dwc.tdwg.org/terms/
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from camera_deployment_metadata import DEPLOYMENTS


def generate_darwin_core_events(output_path="darwin_core_events.csv"):
    """
    Generate Darwin Core Event records from deployment metadata.

    Each row represents one camera trap deployment (session).
    Fields follow Darwin Core standard terminology.
    """

    events = []

    # Group deployments by camera and campaign
    processed_cameras = set()

    for site_cam, info in DEPLOYMENTS.items():
        # Create unique key to avoid duplicates
        campaign = info.get("campaign", "unknown")
        key = f"{site_cam}_{campaign}"

        if key in processed_cameras:
            continue
        processed_cameras.add(key)

        deploy_date = info["deploy_date"]
        retrieve_date = info["retrieve_date"]

        # Create eventID following standard format: <site>-<campaign_start>
        event_id = f"{site_cam}_{campaign}"

        event_record = {
            # Darwin Core required/recommended fields
            "eventID": event_id,
            "eventDate": deploy_date.strftime("%Y-%m-%d"),
            "eventTime": deploy_date.strftime("%H:%M:%S") if deploy_date.hour > 0 else "00:00:00",

            # Location metadata: Camera position
            "decimalLatitude": info.get("lat", ""),
            "decimalLongitude": info.get("lon", ""),
            "coordinateUncertaintyInMeters": 5,  # GPS accuracy for camera placement
            "geodeticDatum": "WGS84",
            "locality": f"TheWilds Site TW{site_cam.split('-')[0][-2:]}",  # Extract site number
            "habitat": "Mixed deciduous forest",  # TODO: From field notes

            # Sampling protocol
            "samplingProtocol": "Passive infrared camera trap (PIR trigger)",
            "sampleSizeValue": (retrieve_date - deploy_date).days,
            "sampleSizeUnit": "days",
            "samplingEffort": f"{(retrieve_date - deploy_date).days} days, continuous 24/7 monitoring",

            # Campaign information
            "eventRemarks": f"Camera {site_cam}, deployed {deploy_date.strftime('%Y-%m-%d')} to {retrieve_date.strftime('%Y-%m-%d')}",

            # Temporal coverage
            "eventEndDate": retrieve_date.strftime("%Y-%m-%d"),
            "eventEndTime": "23:59:59",

            # Camera-specific metadata
            "dynamicProperties": f"camera_id={site_cam}",

            # Quality/status flags
            "minimumElevationInMeters": "",  # From deployment logs
            "maximumElevationInMeters": "",
            "weather": "",  # From field notes
            "fieldNotes": info.get("issues", "No known issues"),
        }

        events.append(event_record)

    # Create DataFrame and save
    df = pd.DataFrame(events)

    # Reorder columns for readability (Darwin Core core fields first)
    core_cols = [
        'eventID', 'eventDate', 'eventEndDate', 'eventTime', 'eventEndTime',
        'samplingProtocol', 'samplingEffort',
        'decimalLatitude', 'decimalLongitude', 'coordinateUncertaintyInMeters',
        'geodeticDatum', 'locality', 'habitat',
        'sampleSizeValue', 'sampleSizeUnit',
        'minimumElevationInMeters', 'maximumElevationInMeters',
        'weather', 'fieldNotes', 'eventRemarks', 'dynamicProperties'
    ]

    # Keep only existing columns in correct order
    existing_cols = [c for c in core_cols if c in df.columns]
    df = df[existing_cols]

    df.to_csv(output_path, index=False)
    print(f"✓ Generated {len(df)} Darwin Core Event records")
    print(f"  Output: {output_path}")
    print(f"\n  Events by campaign:")
    for campaign in df['eventRemarks'].str.extract(r'deployed (\d{4}-\d{2}-\d{2})')[0].unique():
        count = len(df)
        print(f"    {campaign}: {count} cameras")

    return df


if __name__ == "__main__":
    generate_darwin_core_events()
