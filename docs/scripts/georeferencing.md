# Georeferencing

`scripts/georeferencing/` estimates animal ground positions from detection
boxes. Both scripts are provenance-heavy on purpose: every output row carries a
status, so unreliable projections are flagged rather than silently mixed in.

## Camera traps: `geolocate_camera_trap_treeoflife_predictions.py`

A pinhole-model projection of the bottom-center of each box, using the
camera's GPS position, bearing, horizontal field of view, and an assumed
target height from `camera_geolocation_config.csv`. It wraps the geometry of
[Imageomics/camera-trap-geolocation](https://github.com/Imageomics/camera-trap-geolocation);
point `CAMERA_TRAP_GEOLOCATION_SRC` at its `src/` directory.

```bash
export CAMERA_TRAP_GEOLOCATION_SRC=/path/to/camera-trap-geolocation/src
python scripts/georeferencing/geolocate_camera_trap_treeoflife_predictions.py \
  --input-dir  <per-camera Tree-of-Life prediction CSVs> \
  --config-csv scripts/georeferencing/camera_geolocation_config.csv \
  --output-dir <output directory> \
  [--top1-score-min 0.3] [--rank species] [--max-distance-m 500] [--overwrite]
```

Estimates beyond `--max-distance-m` are kept but flagged `out_of_range`.

## Drones: `geolocate_drone_treeoflife_predictions.py`

A ground-ray projection using the aircraft's telemetry (position, altitude,
gimbal pitch) and per-platform field of view from
`drone_projection_config.csv`. Each prediction row is joined back to the
processed detection CSV to recover pose fields, then the box's bottom-center
ray is intersected with a flat ground plane.

```bash
python scripts/georeferencing/geolocate_drone_treeoflife_predictions.py \
  --prediction-dir <per-video *.treeoflife_predictions.csv> \
  --detection-dir  <processed *_detections.csv with pose metadata> \
  --config-csv     scripts/georeferencing/drone_projection_config.csv \
  --output-dir     <output directory> \
  [--min-altitude-m 1.0] [--max-ground-range-m 300] [--min-depression-deg 2.0] [--overwrite]
```

| `georef_status` | Meaning |
|---|---|
| `ok` | Projected |
| `invalid_altitude` | Altitude below `--min-altitude-m` |
| `missing_drone_gps` | No aircraft position for the frame |
| `horizon_ray` | Ray too shallow (depression below `--min-depression-deg`) |
| `out_of_range` | Projected range beyond `--max-ground-range-m` |

The method, its assumptions, and the per-platform parameters are in the
[supplemental material](../SUPPLEMENTAL.md#s6-drone-ground-projection). The
two configuration CSVs used for the release are shipped in this directory.
