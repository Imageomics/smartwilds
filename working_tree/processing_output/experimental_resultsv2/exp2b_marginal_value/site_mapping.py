"""
Shared helper: TW## site coordinates + nearest-site assignment for per-event lat/lon.

Primary source: processing_output/darwin_core/text_data/site_selection_rationale.csv
(Darwin Core table; matches camera-trap EXIF GPS. See data hygiene note below.)

Data hygiene:
  TW05 and TW06 are listed at identical coords in site_selection_rationale.csv, but
  sensor_configurations.md shows they are physically distinct (~700 m apart) with
  different ARU deployment positions. This creates an ambiguous neighborhood for
  drone detections over the Gate O / Zebra Shelter region. Effect on the marginal-
  value analysis: any drone detection close to that cluster may be assigned to
  either site consistently (via sorted nearest match). Flag in prose if needed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path("/fs/ess/PAS2136/TheWilds2025")
SITE_TABLE = BASE_DIR / "processing_output" / "darwin_core" / "text_data" / "site_selection_rationale.csv"

EARTH_R_M = 6_371_000.0


def load_sites() -> pd.DataFrame:
    """Return DataFrame with columns site_id, lat, lon (one row per TW##)."""
    df = pd.read_csv(SITE_TABLE)
    df = df.rename(columns={
        "siteID": "site_id",
        "decimalLatitude": "lat",
        "decimalLongitude": "lon",
    })
    return df[["site_id", "lat", "lon"]].dropna().reset_index(drop=True)


def haversine_m(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Haversine distance in meters. Inputs are degrees; shapes broadcast."""
    lat1r, lat2r = np.radians(lat1), np.radians(lat2)
    dlat = lat2r - lat1r
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    return 2 * EARTH_R_M * np.arcsin(np.sqrt(a))


def assign_tw_site(
    lats: np.ndarray,
    lons: np.ndarray,
    sites: pd.DataFrame | None = None,
    max_dist_m: float = 200.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    For each (lat, lon) point, return (tw_site, distance_m) to the nearest site.
    Points with distance > max_dist_m get tw_site = None.

    Vectorized: O(n_points * n_sites) — fine for n_sites <= 20.
    """
    if sites is None:
        sites = load_sites()
    n_points = len(lats)
    site_lats = sites["lat"].values
    site_lons = sites["lon"].values
    site_ids = sites["site_id"].values

    # Broadcast: (n_points, n_sites) distance matrix
    lats_b = np.asarray(lats)[:, None]
    lons_b = np.asarray(lons)[:, None]
    d = haversine_m(lats_b, lons_b, site_lats[None, :], site_lons[None, :])

    idx = np.argmin(d, axis=1)
    nearest = d[np.arange(n_points), idx]
    out_site = np.where(nearest <= max_dist_m, site_ids[idx], None)
    return out_site, nearest
