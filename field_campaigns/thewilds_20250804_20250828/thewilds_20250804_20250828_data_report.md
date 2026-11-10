# Data Report: thewilds_20250804_20250828

**Date Range:** August 4 - August 28, 2025
**Location:** The Wilds Conservation Center, southeastern Ohio
**Total Size:** ~448 GB
**Total Files:** ~224,062
**Modalities:** Bioacoustics, camera traps, citizen science, drones, JotForm logs

---

## Directory Structure

```
thewilds_20250804_20250828/                                      [448 GB]
|
|-- bioacoustics/                                                [196 GB]
|   |-- The_Wilds_Bioacoustic_Log2025-09-08_19_00_30.csv         [master JotForm log, 28 entries]
|   |-- TW02-SM04/
|   |   |-- metadata.md
|   |   |-- SM04_Summary.txt
|   |   +-- Data/                                                [659 .wav files]
|   |-- TW05-SM06/
|   |   |-- metadata.md
|   |   |-- SM06_Summary.txt
|   |   |-- 2MM18027_Summary.txt
|   |   +-- Data/                                                [100 .wav files]
|   |-- TW06-SM05/
|   |   |-- metadata.md
|   |   |-- SM05_Summary.txt
|   |   |-- 2MM18157_Summary.txt
|   |   +-- Data/                                                [508 .wav files]
|   |-- TW07-SM02/
|   |   |-- metadata.md
|   |   |-- SM002_Summary.txt
|   |   +-- audio_files/Data/                                    [339 .wav files]
|   |-- TW08-SM03/
|   |   |-- metadata.md
|   |   |-- SM03_Summary.txt
|   |   +-- Data/                                                [341 .wav files]
|   +-- TW09-SM01/
|       |-- metadata.md
|       |-- SM01_Summary.txt
|       +-- Data/                                                [195 .wav files]
|
|-- camera_traps/                                                [211 GB]
|   |-- The_Wilds_Camera_Trap_Log2025-09-08_19_01_08.csv         [master JotForm log, 30 entries]
|   |-- TW01-CT02/
|   |   +-- SD02_20250804_20250811/
|   |       |-- metadata.txt
|   |       +-- images/                                          [26,573 JPG across 109MEDIA-137MEDIA]
|   |-- TW02-CT01/
|   |   |-- metadata.txt
|   |   |-- SD01_20250804_20250811/
|   |   |   +-- images/                                          [JPG across 100MEDIA-130MEDIA]
|   |   |-- SD11_20250811_20250818/
|   |   |   +-- [100MEDIA-130MEDIA with JPG files]
|   |   +-- SD13_20250818_20250828/                              [EMPTY -- battery died]
|   |   Total: 61,217 JPG
|   |-- TW04-CT03/
|   |   |-- SD03_20250807_20250811/
|   |   |   |-- metadata.txt
|   |   |   +-- images/100MEDIA/                                 [JPG files]
|   |   +-- SD02_20250811_20250828/
|   |       |-- metadata.txt
|   |       |-- images/100MEDIA/                                 [JPG files]
|   |       +-- videos/                                          [67 AVI files]
|   |   Total: 984 JPG + 67 AVI
|   |-- TW06-CT04/
|   |   |-- metadata.txt
|   |   |-- images/                                              [13,173 JPG across 100MEDIA-113MEDIA]
|   |   +-- SD02_20250811_20250828/
|   |       |-- metadata.txt
|   |       +-- images/                                          [27,734 JPG across 100MEDIA-127MEDIA]
|   |   Total: 40,907 JPG
|   |-- TW06-CT05/
|   |   +-- SD05_20250825_20250828/
|   |       |-- metadata.txt
|   |       +-- images/                                          [84 jpg + 84 mp4]
|   |-- TW07-CT05/
|   |   +-- metadata.txt                                         [no images -- all photos were people]
|   |-- TW09_CT02/
|   |   |-- metadata.txt
|   |   |-- SD22_20250811_20250818/                              [JPG across 100MEDIA-131MEDIA]
|   |   +-- SD23_20250818_20250828/                              [JPG across 100MEDIA-143MEDIA]
|   |   Total: 90,834 JPG
|   |-- TW09-CT05/
|   |   |-- metadata.txt
|   |   +-- SD05_20250811_20250814/                              [9 jpg + 6 mp4 + metadata]
|   +-- TW11-CT06/
|       +-- SD06_20250818_20250828/
|           |-- metadata.txt
|           +-- images/                                          [89 jpg + 23 mp4]
|
|-- citizen_science/                                             [8.9 GB]
|   [991 files -- UUID-named photos/videos from participants]
|   - 395 .jpeg, 340 .JPG, ~136 .heic/.HEIC, 91 .MOV/.mov, 47 .MP4/.mp4, 6 .jpg
|
|-- drones/                                                      [33 GB]
|   |-- 20250811_DJI_01/
|   |   |-- metadata/ExportCSV_2025-08-11_[10-29-13].csv
|   |   +-- videos/                                              [DJI_0001.MOV, DJI_0002.MOV]
|   |-- 20250811_parrot_01/
|   |   |-- metadata/                                            [EMPTY]
|   |   +-- videos/                                              [P5180524.MP4, P5190525.MP4, P5190526.MP4]
|   |-- 20250818_parrot_01/
|   |   |-- metadata/*.json
|   |   +-- videos/                                              [P5760583.MP4, P5760584.MP4, P5760585.MP4]
|   |-- 20250818_parrot_02/
|   |   |-- metadata/*.json
|   |   +-- videos/                                              [P5770586.MP4, P5770587.MP4, P5770588.MP4]
|   |-- 20250825_parrot_01/
|   |   |-- metadata/*.json
|   |   +-- videos/                                              [P6140626.MP4, P6140627.MP4]
|   |-- 20250825_parrot_02/
|   |   |-- metadata/*.json
|   |   +-- videos/                                              [EMPTY]
|   |-- 20250825_parrot_03/
|   |   |-- metadata/*.json
|   |   +-- videos/                                              [EMPTY]
|   +-- 20250825_parrot_04/
|       |-- metadata/*.json
|       +-- videos/                                              [EMPTY]
|
|-- field_notes/                                                 [EMPTY]
|
+-- jotforms/                                                    [4 CSV files]
    |-- The_Wilds_Bioacoustic_Log2025-08-09_11_18_13.csv
    |-- The_Wilds_Bioacoustic_Log2025-08-12_21_39_45.csv
    |-- The_Wilds_Camera_Trap_Log2025-08-09_11_17_50.csv
    +-- The_Wilds_Camera_Trap_Log2025-08-12_21_37_57.csv
```

---

## File Type Summary

| Extension | Count | Description |
|-----------|-------|-------------|
| .JPG | ~220,855 | Camera trap images (bulk of dataset) |
| .wav | 2,142 | Bioacoustic recordings |
| .mp4/.MP4 | ~171 | Camera trap + drone video |
| .AVI | 67 | Camera trap video (TW04-CT03 only) |
| .MOV | 2 | DJI drone video |
| .jpg | ~183 | Smart camera traps (Reveal Pro) + citizen science |
| .jpeg | 395 | Citizen science photos |
| .heic/.HEIC | ~136 | Citizen science photos (Apple format) |
| .mov/.MOV | 91 | Citizen science video |
| .csv | 5 | JotForm logs |
| .txt | ~19 | Metadata + Song Meter summaries |
| .md | 6 | Bioacoustic sensor metadata |
| .json | 6 | Parrot drone flight logs |

---

## Bioacoustics (2,142 .wav files, 196 GB)

### Recorder Details

| Site | Song Meter | Location | GPS | Deploy | Retrieve | Recording Mode | Storage | WAV Count |
|------|-----------|----------|-----|--------|----------|----------------|---------|-----------|
| TW02 | SM04 | Nomad Ridge Shelter, right side | 39.82957, -81.73295 | Aug 4 | Aug 28 | 5 min every hour | 26.06 GB | 659 |
| TW05 | SM06 | Lake Trail Gate O | 39.82866, -81.73758 | Aug 4 | Aug 28 | Sunrise to sunset | 16.62 GB | 100 |
| TW06 | SM05 | Zebra Shelter | 39.82870, -81.73756 | Aug 4 | Aug 28 | 15 min every hour | 21.82 GB | 508 |
| TW07 | SM02 | Zipline Tower | 39.82891, -81.74392 | Aug 4 | Aug 28 | Sunrise to sunset | 56.44 GB | 339 |
| TW08 | SM03 | Fence with Vegetation | 39.82892, -81.74392 | Aug 4 | Aug 28 | Sunrise to sunset | 56.69 GB | 341 |
| TW09 | SM01 | Dock, left side | 39.83418, -81.73783 | Aug 14 | Aug 28 | Sunrise to sunset | 32.38 GB | 195 |

WAV filename pattern: `SMXXX_YYYYMMDD_HHMMSS.wav` (e.g., `SM002_20250805_123002.wav`)

Summary files (SM*_Summary.txt) contain sensor health logs in CSV format with columns: DATE, TIME, LAT, NS, LON, EW, POWER(V), #FILES -- one-minute resolution.

### Audio File Locations

| Station | Directory | File Count |
|---------|-----------|------------|
| TW02-SM04 | bioacoustics/TW02-SM04/Data/ | 659 .wav |
| TW05-SM06 | bioacoustics/TW05-SM06/Data/ | 100 .wav |
| TW06-SM05 | bioacoustics/TW06-SM05/Data/ | 508 .wav |
| TW07-SM02 | bioacoustics/TW07-SM02/audio_files/Data/ | 339 .wav |
| TW08-SM03 | bioacoustics/TW08-SM03/Data/ | 341 .wav |
| TW09-SM01 | bioacoustics/TW09-SM01/Data/ | 195 .wav |

### Master Bioacoustic Log

File: bioacoustics/The_Wilds_Bioacoustic_Log2025-09-08_19_00_30.csv
- 28 entries covering deployments, check-ins, and pickups from Aug 4 to Aug 25
- Columns: Submission Date, Dropoff or Pickup?, Site ID, Difficulty Rating, Latitude, Longitude, Bioacoustic ID, SD Card ID, File Upload, Notes, Team Member Name, SD Card Storage, Battery Status, Team Member Email, DateTime

---

## Camera Traps (~220,855 JPG + ~183 jpg + 67 AVI + ~113 mp4, 211 GB)

### Camera Trap Details

**TW01-CT02** (Nomad Ridge Shelter, east side, facing SE) -- metadata.txt
- Camera: GardePro T5NG, SD02 (256GB)
- GPS: 39.49.8459, 081.44.2737
- Deploy: Aug 4 / Retrieve: Aug 11
- Config: Photo only (4MP, 3-photo burst), High PIR
- **Data: 26,573 JPG** across 109MEDIA-137MEDIA (30.22 GB)
- Note: Removed from TW01, relocated to dock
- Location: camera_traps/TW01-CT02/SD02_20250804_20250811/images/

**TW02-CT01** (Nomad Ridge Shelter, west side, facing SW) -- metadata.txt
- Camera: GardePro T5NG
- GPS: 39.49.8394, 081.44.2751
- Deploy: Aug 4 / Retrieve: Aug 28 (3 SD card swaps)
- Config: Photo only (4MP, 3-photo burst)
- **Data: 61,217 JPG** across 3 SD periods
- **DATE ERROR:** Camera clock set incorrectly (showed Oct 31 2023 initially, then Sep instead of Aug). Correction mapping provided in metadata.
- Battery died between Aug 18-25; SD13 period is empty
- Location: camera_traps/TW02-CT01/SD01_20250804_20250811/, SD11_20250811_20250818/, SD13_20250818_20250828/

**TW04-CT03** (Lake Trail, NW facing) -- metadata.txt
- Camera: GardePro A3
- GPS: 39.50.0572, 081.44.3604
- Deploy: Aug 4 (reset Aug 7) / Retrieve: Aug 28
- Config: Photo (8MP, 3-burst) + Video (1080p, 10s)
- **Data: 984 JPG + 67 AVI**
- Note: Camera reset on Aug 7 (no data from initial deploy). No data after Aug 25.
- Location: camera_traps/TW04-CT03/SD03_20250807_20250811/ and SD02_20250811_20250828/

**TW06-CT04** (Zebra Shelter, facing NW) -- metadata.txt
- Camera: Trail Camera G600
- GPS: 39.50.1224, 081.44.3053
- Deploy: Aug 4 / Retrieve: Aug 28
- Config: Motion detection, Photo (8MP, 5-burst) + Video (1080p, 10s)
- **Data: 40,907 JPG** across two SD card periods
- Note: Battery at 100% (unusual)
- Location: camera_traps/TW06-CT04/images/ and SD02_20250811_20250828/images/

**TW06-CT05** (Zebra Shelter, inside, facing N) -- metadata.txt
- Camera: Reveal Pro 3.0
- Deploy: Aug 25 / Retrieve: Aug 28
- Config: Photo (4K) + Video (720p, 10s)
- **Data: 84 jpg + 84 mp4** (168 files)
- Note: Installed late in deployment to capture ungulate activity inside shelter
- Location: camera_traps/TW06-CT05/SD05_20250825_20250828/images/

**TW07-CT05** (Zipline Tower, facing N) -- metadata.txt only
- Camera: Reveal Pro 3.0
- GPS: 39.49.9727, 081.44.0732
- Deploy: Aug 7 / Retrieve: Aug 11
- **Data: None uploaded -- all photos were of people** (triggered by tour buses)
- Note: Camera subsequently relocated to dock
- Location: camera_traps/TW07-CT05/

**TW09-CT02** (Dock, left side, overlooking lake, facing S) -- metadata.txt
- Camera: GardePro T5NG
- Deploy: Aug 11 / Retrieve: Aug 28
- Config: Photo only (4MP, 3-burst)
- **Data: 90,834 JPG** across two SD card periods (largest camera trap dataset)
- **Data gap:** Battery died Aug 18-25
- Location: camera_traps/TW09_CT02/SD22_20250811_20250818/ and SD23_20250818_20250828/

**TW09-CT05** (Dock, right side, overlooking lake, facing SE) -- metadata.txt
- Camera: Reveal Pro 3.0
- Deploy: Aug 11 / Retrieve: Aug 14
- Config: Photo (4K) + Video (720p, 10s)
- **Data: 9 jpg + 6 mp4** (very small capture)
- Note: Issues with image detection reported
- Location: camera_traps/TW09-CT05/SD05_20250811_20250814/

**TW11-CT06** (Fence overlooking lake, dock-right, facing NE) -- metadata.txt
- Camera: Reveal Pro 3.0
- GPS: 39.83438, -81.73930
- Deploy: Aug 11 (initial), Aug 18 (re-deployed) / Retrieve: Aug 28
- Config: Photo (4K) + Video (FHD 1080p, 15s)
- **Data: 89 jpg + 23 mp4** (112 files)
- Note: Battery issues; no data from initial deployment. 1 bar of service. No photos retrievable from phone app.
- Location: camera_traps/TW11-CT06/SD06_20250818_20250828/images/

### Master Camera Trap Log

File: camera_traps/The_Wilds_Camera_Trap_Log2025-09-08_19_01_08.csv
- 30 entries covering deployments, pickups, and check-ins from Aug 4 to Aug 25
- Columns: Submission Date, Dropoff or Pickup?, Site ID, Accessible?, Difficulty Rating, Latitude, Longitude, Camera Trap ID, SD Card ID, Notes, Record camera heading, Battery status, SD Card Storage, Data Quality Report, File Upload, Team Member Name, Team Member Email, DateTime

### Image File Naming Patterns
- GardePro cameras: `NSCF0002_YYMMDDHHMMSS_NNNN.JPG` (e.g., `NSCF0002_250806134101_0016.JPG`)
- Images organized in numbered MEDIA folders (100MEDIA through ~143MEDIA)
- Reveal Pro / smart cameras: `SYFW00NNN.jpg` / `SYFW00NNN.mp4`

---

## Drones (13 video files, 33 GB)

8 flight sessions across 3 dates. Platforms: DJI and Parrot Anafi 4K.

### Flight Details

| Flight | Date | Platform | Videos | Metadata | Notes |
|--------|------|----------|--------|----------|-------|
| 20250811_DJI_01 | Aug 11 | DJI | DJI_0001.MOV, DJI_0002.MOV | 1 CSV (GPS + battery at 10Hz) | GPS: 39.834171, -81.737820 |
| 20250811_parrot_01 | Aug 11 | Parrot Anafi 4K | P5180524.MP4, P5190525.MP4, P5190526.MP4 | EMPTY | **No metadata file present** |
| 20250818_parrot_01 | Aug 18 | Parrot Anafi 4K | P5760583.MP4, P5760584.MP4, P5760585.MP4 | 1 JSON | Parrot telemetry format |
| 20250818_parrot_02 | Aug 18 | Parrot Anafi 4K | P5770586.MP4, P5770587.MP4, P5770588.MP4 | 1 JSON | Parrot telemetry format |
| 20250825_parrot_01 | Aug 25 | Parrot Anafi 4K | P6140626.MP4, P6140627.MP4 | 1 JSON (GUTMA DX format) | Aircraft SN: PI040416BA8H083200, firmware 1.8.2 |
| 20250825_parrot_02 | Aug 25 | Parrot Anafi 4K | EMPTY | 1 JSON | **No video files uploaded** |
| 20250825_parrot_03 | Aug 25 | Parrot Anafi 4K | EMPTY | 1 JSON | **No video files uploaded** |
| 20250825_parrot_04 | Aug 25 | Parrot Anafi 4K | EMPTY | 1 JSON | **No video files uploaded** |

### Video File Locations

| Flight | Directory |
|--------|-----------|
| 20250811_DJI_01 | drones/20250811_DJI_01/videos/ |
| 20250811_parrot_01 | drones/20250811_parrot_01/videos/ |
| 20250818_parrot_01 | drones/20250818_parrot_01/videos/ |
| 20250818_parrot_02 | drones/20250818_parrot_02/videos/ |
| 20250825_parrot_01 | drones/20250825_parrot_01/videos/ |

### Drone Metadata Formats

**DJI CSV:** Columns include count(10Hz), latitude, longitude, batteryPercent

**Parrot JSON (proprietary):** Fields include time, battery_level, controller_gps_latitude/longitude, flying_state, alert_state, wifi_signal, product_gps_available, product_gps_longitude/latitude, speed_vx/vy/vz, angle_phi/theta/psi, altitude

**Parrot JSON (GUTMA DX):** Standard flight logging format with aircraft info (serial number, product_name, firmware_version), GCS info, battery data, flight events (TOF, VIDEO start/stop, ENR, LDG, LND), and telemetry items (timestamp, gps_lon, gps_lat, gps_altitude, speed, battery_percent, angles)

---

## Citizen Science (991 files, 8.9 GB)

Location: citizen_science/

All files in a flat directory with UUID-based filenames (e.g., `00113818-3AD3-4270-ADC0-F9D8105FB5B3_1_105_c.jpeg`).

| Format | Count |
|--------|-------|
| .jpeg | 395 |
| .JPG | 340 |
| .heic/.HEIC | ~136 |
| .MOV/.mov | 91 |
| .MP4/.mp4 | 47 |
| .jpg | 6 |

Note: No accompanying metadata, labels, or index file within this directory.

---

## JotForm Logs (Early Snapshots)

Location: jotforms/

4 CSV files representing earlier partial snapshots of the field logging system. The master logs (dated 2025-09-08) in the bioacoustics/ and camera_traps/ directories contain all entries including later check-ins.

| File | Entries | Date Range | Content |
|------|---------|------------|---------|
| The_Wilds_Bioacoustic_Log2025-08-09_11_18_13.csv | 7 | Aug 4-7 | Initial bioacoustic deployments |
| The_Wilds_Bioacoustic_Log2025-08-12_21_39_45.csv | 6 | Aug 11 | Check-ins with storage/battery status |
| The_Wilds_Camera_Trap_Log2025-08-09_11_17_50.csv | 9 | Aug 4-7 | Initial camera trap deployments |
| The_Wilds_Camera_Trap_Log2025-08-12_21_37_57.csv | 3 | Aug 11 | Pickups/deployments with data quality |

---

## Site Location Summary

| Site ID | Name | GPS | Sensors Deployed |
|---------|------|-----|-----------------|
| TW01 | Nomad Ridge Shelter, east | 39.49.8459, 081.44.2737 | CT02 (Aug 4-11) |
| TW02 | Nomad Ridge Shelter, west/right | 39.49.8394, 081.44.2751 | CT01, SM04 |
| TW04 | Lake Trail | 39.50.0572, 081.44.3604 | CT03 |
| TW05 | Lake Trail Gate O | 39.82866, -81.73758 | SM06 |
| TW06 | Zebra Shelter | 39.50.1224, 081.44.3053 | CT04, CT05, SM05 |
| TW07 | Zipline Tower | 39.49.9727, 081.44.0732 | CT05 (relocated), SM02 |
| TW08 | Fence with Vegetation | 39.82892, -81.74392 | SM03 |
| TW09 | Dock | 39.83418, -81.73783 | CT02, CT05, SM01 |
| TW11 | Fence overlooking lake | 39.83438, -81.73930 | CT06 |

---

## Known Issues and Data Quality Notes

1. **TW02-CT01 date error:** Camera clock set incorrectly. First days show as Oct 31 2023; after attempted correction, dates show as September instead of August. Correction mapping provided in metadata.txt.
2. **TW07-CT05 (Zipline Tower):** All photos captured people (triggered by tour buses). No images uploaded. Camera relocated to dock.
3. **TW09-CT02 data gap:** Battery died between Aug 18-25, resulting in missing data for that week.
4. **TW04-CT03 data gaps:** No data collected from initial Aug 4 deploy (reset Aug 7). No data after Aug 25.
5. **TW11-CT06 battery issues:** Battery dead/empty on first check (Aug 18). Only collected data after re-deployment. Very limited cell connectivity (1 bar).
6. **TW02-CT01 SD13 empty:** Third SD card period (Aug 18-28) directory exists but contains no data (battery died ~Aug 25).
7. **Drone flights 20250825_parrot_02/03/04:** Metadata JSON files present but video directories are empty (videos not uploaded).
8. **Drone flight 20250811_parrot_01:** Video files present but no metadata file.
9. **SM04 summary data:** Contains data from before Aug 4 deployment (back to June 30), suggesting summary includes prior deployment data.
10. **field_notes/ directory:** Created Aug 11 but never populated.
11. **Citizen science data:** No metadata or index file accompanies the 991 media files -- file-to-observation linkage information is absent.

---

## Team Members (from JotForm logs)

- **Bharath Pillai** (pillai.105@buckeyemail.osu.edu) -- Initial deployments Aug 4-7
- **Ally Bonney** (bonney.21@osu.edu) -- Deployments and Aug 25 check-ins
- **Penelope Covey** (covey.64@osu.edu) -- Aug 11 and Aug 18 check-ins
- **Jenna Kline** (jennamkline) -- Aug 14 check-ins, bioacoustic sensor setup
- **Anirudh Potlapally** -- Aug 14 camera trap service
