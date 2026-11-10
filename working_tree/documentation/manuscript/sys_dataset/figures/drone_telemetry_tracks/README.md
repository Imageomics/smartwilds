# Drone flight tracks

This directory contains a transparent overlay of recorded drone flight paths for the SmartWilds deployment map. The overlay is derived from original aircraft telemetry, not from detection coordinates or manual tracing.

## Files

- `drone_flight_tracks_overlay.png`: transparent 1564 x 1044 px overlay for the existing deployment figure.
- `drone_flight_tracks_overlay.svg`: equivalent editable vector overlay.
- `drone_flight_tracks.geojson`: simplified, map-coordinate flight paths.
- `drone_flight_tracks_manifest.json`: source-file and point-count provenance for every plotted flight.

## Scope and method

Fourteen flights have usable aircraft GPS telemetry: nine Parrot Anafi mission logs (July 1, July 3, and August 18), one August 11 DJI export, and four September 8 DJI AirData logs. Coordinates are retained only when finite, valid WGS84, and within the deployment area. Neighboring points closer than 1.25 m are omitted solely to reduce GPS jitter in the figure; gaps or jumps over 85 m are not connected. The rendered line receives a light five-point smoothing pass only; exported GeoJSON remains unsmoothed. One compact, white-haloed arrow at 62% of each plotted segment indicates travel direction. The August 25 Parrot sessions have no usable aircraft-GPS stream and are not shown.

The overlay uses the geographic extent registered to the supplied 1564 x 1044 deployment-map canvas: -81.7486 to -81.7244 longitude and 39.8273 to 39.8390 latitude.
