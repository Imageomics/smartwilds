# Events vs. Occurrences: Quick Reference

## The Key Distinction

### Events = Survey Sessions (SURVEY LOCATIONS)
**Answer**: "Where was the camera deployed and for how long?"

Each row = one camera deployment
```
eventID: TW02-CT01_20250804_20250828
eventDate: 2025-08-04 to 2025-08-28
decimalLatitude: 39.498394   ← Where the CAMERA is located
decimalLongitude: -81.442751 ← Where the CAMERA is located
samplingEffort: 24 days, continuous 24/7 monitoring
```

### Occurrences = Species Observations (ANIMAL LOCATIONS)
**Answer**: "Which animals were detected and where were they?"

Each row = one species detection in a camera image
```
occurrenceID: TW02-CT01_20250810T134530_001
eventID: TW02-CT01_20250804_20250828  ← Links back to survey session
scientificName: Odocoileus virginianus
decimalLatitude: 39.4985    ← Where the ANIMAL was detected (GPS projected)
decimalLongitude: -81.4422  ← Where the ANIMAL was detected (GPS projected)
associatedOccurrences: Distance: 2.3m, Angle: 15°
```

## Geographic Relationships

### One Camera Multi-year:
```
Event 1: TW02-CT01_20250630_20250703 (June-July)
  → lat: 39.498394, lon: -81.442751

Event 2: TW02-CT01_20250804_20250828 (August)
  → lat: 39.498394, lon: -81.442751  (Same camera, same location)

100+ Occurrences across both events at various animal locations
  → Different lat/lon for each detection (animal GPS projected)
```

### Multiple Animals, One Event:
```
Event: TW02-CT01_20250804_20250828 (Camera location)
  → lat: 39.498394, lon: -81.442751

Occurrence 1: TW02-CT01_20250810T090000_001
  → lat: 39.4986, lon: -81.4420  (Deer detected 100m north)

Occurrence 2: TW02-CT01_20250810T140000_001
  → lat: 39.4982, lon: -81.4428  (Deer detected 400m south)

Occurrence 3: TW02-CT01_20250815T110000_001
  → lat: 39.4987, lon: -81.4421  (Bird detected 80m northeast)
```

## Data Flow

```
Camera Trap Images
     ↓
Camera Location (GPS from deployment log)
     ↓
darwin_core_events.csv
  (Survey session metadata + camera location)
     ↓
     └──→ Animal Detection (YOLO + BioCLIP)
            +
            Distance & Angle Estimation
            +
            GPS Projection (Vincenty geodetics)
            ↓
         darwin_core_occurrences.csv
           (Detection metadata + animal location)
```

## Implementation Details

### darwin_core_events.csv
- **Source**: `camera_deployment_metadata.py` (lat/lon extracted from field metadata.txt)
- **Key columns**: eventID, eventDate, latitude (camera), longitude (camera), samplingProtocol, samplingEffort
- **Uncertainty**: ±5 meters (camera placement accuracy with GPS)

### darwin_core_occurrences.csv
- **Source**: `detections_with_validated_timestamps.csv` (animal_lat/animal_lon from depth estimation)
- **Key columns**: occurrenceID, eventID (links to event), scientificName, latitude (animal), longitude (animal)
- **Uncertainty**: ±50 meters (depth estimation uncertainty)
- **Fallback**: If depth estimation fails, uses camera_lat/camera_lon

## Querying Examples

### Find all survey sessions and their camera locations:
```python
import pandas as pd

events = pd.read_csv('darwin_core_events.csv')
# All unique camera locations
print(events[['eventID', 'decimalLatitude', 'decimalLongitude']])
```

### Find all animals detected at specific location:
```python
occurrences = pd.read_csv('darwin_core_occurrences.csv')
events = pd.read_csv('darwin_core_events.csv')

# Merge to find camera location for each detection
merged = occurrences.merge(events[['eventID', 'decimalLatitude', 'decimalLongitude']],
                           on='eventID',
                           suffixes=('_animal', '_camera'))

# Find animals detected near camera (distance < 50m)
nearby = merged[(merged['distance_m'] < 50)]
```

### Map all detections by species:
```python
occurrences = pd.read_csv('darwin_core_occurrences.csv')

# Group by species
for species in occurrences['scientificName'].unique():
    species_detections = occurrences[occurrences['scientificName'] == species]
    print(f"{species}: {len(species_detections)} detections")
    print(f"  Geographic extent: {species_detections['decimalLatitude'].min()} to {species_detections['decimalLatitude'].max()}")
```

## Coordinate Uncertainty

### Event coordinates (Camera location):
```
coordinateUncertaintyInMeters: 5

Represents:
- GPS accuracy of camera placement during deployment
- Static (camera doesn't move)
- Typical ±5m accuracy for handheld GPS
```

### Occurrence coordinates (Animal location):
```
coordinateUncertaintyMeters: 50

Represents:
- Accumulated uncertainty from:
  - Bbox height → distance estimation
  - Distance + angle → GPS projection
  - Animal may not be directly in front of camera
- Dynamic (animal location varies per detection)
```

## Standards Compliance

Both follow **Darwin Core Standard** for biodiversity data:
- ✓ Complete taxonomic hierarchy for occurrences
- ✓ WGS84 coordinate system
- ✓ Explicit uncertainty quantification
- ✓ Event/Occurrence linkage
- ✓ Sampling protocol documentation
- ✓ Machine-readable format (CSV)
- ✓ Ready for GBIF submission

---

**TL;DR**: Events hold camera locations + deployment info. Occurrences hold animal locations + species info. Link them via eventID!
