"""
Camera deployment metadata with known issues and date ranges.
Used for validating timestamps extracted from filenames and EXIF data.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple

# Deployment date ranges for each site/camera
# Format: "TW##-CT##" -> (deploy_date, retrieve_date, known_issues_description)
DEPLOYMENTS = {
    # June-July 2025 Campaign (thewilds_20250630_20250703)
    "TW01-CT02": {
        "campaign": "20250630_20250703",
        "deploy_date": datetime(2025, 6, 30),
        "retrieve_date": datetime(2025, 7, 3),
        "issues": None
    },
    "TW02-CT03": {
        "campaign": "20250630_20250703",
        "deploy_date": datetime(2025, 6, 30),
        "retrieve_date": datetime(2025, 7, 3),
        "issues": None
    },
    "TW03-CT01": {
        "campaign": "20250630_20250703",
        "deploy_date": datetime(2025, 6, 30),
        "retrieve_date": datetime(2025, 7, 3),
        "issues": None
    },
    "TW04-CT04": {
        "campaign": "20250630_20250703",
        "deploy_date": datetime(2025, 6, 30),
        "retrieve_date": datetime(2025, 7, 3),
        "issues": None
    },

    # August 2025 Campaign (thewilds_20250804_20250828)
    "TW01-CT02": {
        "campaign": "20250804_20250828",
        "deploy_date": datetime(2025, 8, 4, 9, 0),
        "retrieve_date": datetime(2025, 8, 11, 9, 0),
        "lat": 39.498459,
        "lon": -81.442737,
        "issues": None
    },
    "TW02-CT01": {
        "campaign": "20250804_20250828",
        "deploy_date": datetime(2025, 8, 4, 9, 0),
        "retrieve_date": datetime(2025, 8, 28),
        "lat": 39.498394,
        "lon": -81.442751,
        "issues": "Camera clock set incorrectly: initial dates recorded as Oct-31-2023, then Sept 2023 instead of Aug 2025",
        "timestamp_corrections": {
            # Map from recorded timestamp to actual timestamp
            (2023, 10, 31): (2025, 8, 4),   # 10-31-23 -> 08-04-25
            (2023, 11, 1): (2025, 8, 5),    # 11-01-23 -> 08-05-25
            (2023, 9, 7): (2025, 8, 7),     # 09-07-23 -> 08-07-25
            (2023, 9, 8): (2025, 8, 8),     # 09-08-23 -> 08-08-25
            (2023, 9, 9): (2025, 8, 9),     # 09-09-23 -> 08-09-25
            (2023, 9, 10): (2025, 8, 10),   # 09-10-23 -> 08-10-25
            (2023, 9, 11): (2025, 8, 11),   # 09-11-23 -> 08-11-25
        },
        "retrieve_dates": [
            {"date": datetime(2025, 8, 11), "reason": "SD card replaced and batteries"},
            {"date": datetime(2025, 8, 18), "reason": "SD card replaced"},
            {"date": datetime(2025, 8, 28), "reason": "Final retrieval"},
        ]
    },
    "TW04-CT03": {
        "campaign": "20250804_20250828",
        "deploy_date": datetime(2025, 8, 11, 9, 0),
        "retrieve_date": datetime(2025, 8, 28),
        "issues": "No data collected after 2025-08-25",
        "data_cutoff": datetime(2025, 8, 25)
    },
    "TW06-CT04": {
        "campaign": "20250804_20250828",
        "deploy_date": datetime(2025, 8, 4, 9, 50),
        "retrieve_date": datetime(2025, 8, 11),
        "issues": None
    },
    "TW06-CT05": {
        "campaign": "20250804_20250828",
        "deploy_date": datetime(2025, 8, 25),
        "retrieve_date": datetime(2025, 8, 28),
        "issues": None
    },
    "TW07-CT05": {
        "campaign": "20250804_20250828",
        "deploy_date": datetime(2025, 8, 4),
        "retrieve_date": datetime(2025, 8, 12),
        "issues": None
    },
    "TW09_CT02": {
        "campaign": "20250804_20250828",
        "deploy_date": datetime(2025, 8, 4),
        "retrieve_date": datetime(2025, 8, 28),
        "issues": "Data missing between 2025-08-18 and 2025-08-25 (battery died)"
    },
    "TW09-CT05": {
        "campaign": "20250804_20250828",
        "deploy_date": datetime(2025, 8, 4),
        "retrieve_date": datetime(2025, 8, 28),
        "issues": None
    },
    "TW11-CT06": {
        "campaign": "20250804_20250828",
        "deploy_date": datetime(2025, 8, 18),
        "retrieve_date": datetime(2025, 8, 28),
        "issues": None
    },
}


def get_deployment_info(site_cam: str) -> Optional[dict]:
    """Get deployment info for a site/camera."""
    for key, info in DEPLOYMENTS.items():
        if key == site_cam:
            return info
    return None


def get_valid_date_range(site_cam: str) -> Optional[Tuple[datetime, datetime]]:
    """Get the valid date range (with padding) for a camera."""
    info = get_deployment_info(site_cam)
    if not info:
        return None

    # Add 1 day padding before deployment and after retrieval for safety
    start = info["deploy_date"] - timedelta(days=1)
    end = info["retrieve_date"] + timedelta(days=1)
    return start, end


def should_apply_timestamp_correction(site_cam: str, year: int, month: int, day: int) -> Optional[Tuple[int, int, int]]:
    """
    Check if a timestamp needs correction. Returns corrected (year, month, day) or None.
    """
    info = get_deployment_info(site_cam)
    if not info or "timestamp_corrections" not in info:
        return None

    corrections = info["timestamp_corrections"]
    key = (year, month, day)
    if key in corrections:
        return corrections[key]
    return None


def validate_timestamp(site_cam: str, timestamp) -> Tuple[bool, Optional[str]]:
    """
    Validate a timestamp for a given camera.
    Returns (is_valid, reason_if_invalid)
    """
    import pandas as pd

    date_range = get_valid_date_range(site_cam)
    if not date_range:
        return False, f"Unknown camera: {site_cam}"

    start, end = date_range

    if timestamp < start or timestamp > end:
        return False, f"Outside valid date range {start.date()} to {end.date()}"

    return True, None
