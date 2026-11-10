# Data Report: thewilds_20250630_20250703

**Date Range:** June 30 - July 3, 2025
**Location:** The Wilds Conservation Center, southeastern Ohio
**Total Size:** ~100 GB
**Total Files:** ~20,390

---

## Directory Structure

```
thewilds_20250630_20250703/                              [100 GB]
|
|-- data_summary.md                                      [working notes]
|
|-- field_notes/                                         [10 MB]
|   |-- equipment.csv
|   |-- field_notes_20250630.md
|   |-- field_notes_20250804.md
|   |-- site_descriptions.md
|
|-- bioacoustics/                                        [6.0 GB]
|   |-- bioacoustic.txt                                  [tree listing]
|   |-- The_Wilds_Bioacoustic_Log2025-06-30_21_54_59.csv [JotForm deployment log]
|   |-- The_Wilds_Bioacoustic_Log2025-07-04_20_18_38.csv [JotForm pickup log]
|   |-- TW05-SM01/
|   |   |-- metadata.md
|   |   +-- SD01_20250630_20250703/                      [144 .wav files]
|   |-- TW06-SM03/
|   |   |-- metadata.md
|   |   +-- SD03_20250630_20250703/                      [77 .wav files]
|   |-- TW07-SM02/
|   |   |-- metadata.md
|   |   +-- SD02_20250630_20250703/                      [12 .wav files]
|   +-- TW08-SM04/
|       |-- metadata.md
|       +-- SD04_20250630_20250703/                      [78 .wav files]
|
|-- camera_traps/                                        [49 GB]
|   |-- camera_trap.txt                                  [tree listing]
|   |-- The_Wilds_Camera_Trap_Log2025-06-30_21_56_00.csv [JotForm deployment log]
|   |-- The_Wilds_Camera_Trap_Log2025-07-04_20_18_08.csv [JotForm pickup log]
|   |-- TW01-CT02/
|   |   +-- SD02_20250630_20250703/
|   |       |-- metadata.txt
|   |       +-- images/
|   |           |-- sam-env.yml                          [conda env spec]
|   |           |-- sam-env-full.yml                     [conda env full spec]
|   |           |-- chunk1/                              [2,602 files: JPG + MP4]
|   |           |-- chunk2/                              [2,602 files: JPG + MP4]
|   |           |-- chunk3/                              [2,602 files: JPG + MP4]
|   |           +-- chunk4/                              [2,602 files: JPG + MP4]
|   |-- TW02-CT03/
|   |   +-- SD03_20250630_20250703/
|   |       |-- metadata.txt
|   |       +-- images/                                  [55 files: JPG + AVI]
|   |-- TW03-CT01/
|   |   +-- SD01_20250630_20250703/
|   |       |-- metadata.txt
|   |       +-- images/
|   |           |-- 100MEDIA/ through 108MEDIA/          [8,867 files across 9 folders]
|   +-- TW04-CT04/
|       +-- SD04_20250630_20250704/
|           |-- metadata.txt
|           +-- 101MEDIA/                                [684 files: JPG + MP4]
|
+-- drones/                                              [46 GB]
    |-- 20250701_parrotanafi_1/
    |   |-- metadata/
    |   |   |-- 0914_2025-07-01T083438-0400_10D6BC_0018.json
    |   |   +-- mission_notes.txt
    |   +-- video_files/
    |       |-- VID_001.MP4, VID_002.MP4, VID_003.MP4, VID_004.MP4
    |-- 20250703_parrotanafi_1/
    |   |-- metadata/
    |   |   |-- 0914_2025-07-03T154754-0400_16A458_0019.json
    |   |   |-- 0914_2025-07-03T155059-0400_54039C_001A.json
    |   |   +-- mission_notes_1.txt
    |   +-- video_files/
    |       |-- VID_001.MP4, VID_002.MP4, VID_003.MP4
    |-- 20250703_parrotanafi_2/
    |   |-- metadata/
    |   |   |-- 0914_2025-07-03T162104-0400_BF7B18_001D.json
    |   |   +-- mission_notes_2.txt
    |   +-- video_files/
    |       |-- VID_001.MP4, VID_002.MP4, VID_003.MP4
    |-- 20250703_parrotanafi_3/
    |   |-- metadata/
    |   |   |-- 0914_2025-07-03T165620-0400_D602EB_001F.json
    |   |   +-- mission_notes_3.txt
    |   +-- video_files/
    |       |-- VID_001.MP4, VID_002.MP4
    |-- 20250703_parrotanafi_4/
    |   |-- metadata/
    |   |   |-- 0914_2025-07-03T172345-0400_75DB7A_0021.json
    |   |   +-- mission_notes_4.txt
    |   +-- video_files/
    |       |-- VID_001.MP4, VID_002.MP4, VID_003.MP4
    +-- 20250703_parrotanafi_5/
        |-- metadata/
        |   |-- 0914_2025-07-03T172555-0400_0F0BAD_0008.json
        |   +-- mission_notes_5.txt
        +-- videos/
            |-- VID_001.MP4 through VID_005.MP4
```

---

## File Type Summary

| Extension | Count  | Description |
|-----------|--------|-------------|
| .JPG      | ~15,081 | Camera trap images |
| .MP4      | ~4,937  | Camera trap videos + drone videos |
| .wav      | 311    | Bioacoustic audio recordings |
| .AVI      | 16     | Camera trap videos (TW02-CT03 only) |
| .txt      | 12     | Metadata, notes, tree listings |
| .md       | 8      | Field notes, metadata, summaries |
| .json     | 7      | Drone flight telemetry |
| .csv      | 5      | JotForm logs, equipment inventory |
| .yml      | 2      | Conda environment specs |

---

## Field Notes

### Site Descriptions (field_notes/site_descriptions.md)

10 monitoring sites established:

| Site ID | Name | GPS | Habitat | Selection Reason |
|---------|------|-----|---------|-----------------|
| TW01 | Nomad Ridge Shelter (East) | 39.49.8459, 081.44.2737 | Hill above lake | High deer activity at lake |
| TW02 | Nomad Ridge Shelter (West) | 39.49.8394, 081.44.2751 | Hill above lake | High deer activity at lake |
| TW03 | Old giraffe feeder (Pasture D) | 39.50.2021, 081.44.1644 | Near salt lick and lake | High deer activity near salt lick |
| TW04 | Lake Trail (NW facing) | 39.50.0572, 081.44.3604 | Overlooking lake, on tree | High deer activity along lake trail |
| TW05 | Lake Trail Gate O | 39.50.1224, 081.44.3053 | Mounted on gate | Easy access, high bird activity |
| TW06 | Zebra Shelter | 39.50.1109, 081.43.8523 | Open plain | Animal activity around shelter |
| TW07 | Zipline Tower | 39.49.9727, 081.44.0732 | Open field | Easy access, bird activity |
| TW08 | Fence with Vegetation | 39.49.7387, 081.44.6265 | Dense vegetation | Bird activity |
| TW09 | Dock | 39.49.6789, 081.44.5000 | Open water | Takin and Pere David's deer activity |
| TW10 | Fence near lake entrance | (no GPS) | Dense vegetation | Pere David's deer activity |

GPS from Garmin InReach; JotForm GPS from iPhone Apple Maps.

### Field Notes - June 30, 2025 (Deployment Day) (field_notes/field_notes_20250630.md)

Multiple team members recorded observations:

**JENNA:** Installed camera traps first, then sound meters, then visited rhinos. CT01 and CT03 at Nomad Ridge Shelter facing each side of lake. CT02 at Pasture D giraffe feeder/salt lick. CT04 at Lake Trail facing NW. Sound meters at Lake Trail Gate O, Zebra Shelter, Zip Tower, and Fence with vegetation.

**BHARATH:** Animals were receptive to human presence; deer were curious. Concerns about 4th camera trap deployment -- lake ripples may trigger motion detection. Locations covered open areas; more wooded areas would provide geographic diversity.

**PENELOPE:** Currently breeding season for deer. Sites 1+2 had normal herd split into two groups with two males. Males "croak" to mark territory. Animals wading in water due to warm weather. Need mounting solutions for areas without trees/poles.

**ALLY BONNEY:** CT02 at Nomad Shelter overlooks land bridge between two lakes where deer congregate. JotForms did not work in parts of The Wilds; paper copies used. Heavy rain in morning, cleared up during deployment. Running pump at 4th camera trap site may cause noise pollution.

**TANISHKA:** CT01 at salt lick near old giraffe feeder. Observed 3 female and 1 male wild cows. Bioacoustic recorder 1 near Gate O for bird calls. Cloudy and breezy, JotForm connectivity issues.

### Field Notes - August 4, 2025 (Second Deployment Visit) (field_notes/field_notes_20250804.md)

Equipment installations during this visit:
- **Stop 1 (Nomad Ridge Shelter):** 2 camera traps (CT01, CT02) + 1 acoustic sensor. Camera: hybrid mode, high PIR sensitivity, no video. Sound meter: hourly, 15 min/hr.
- **Stop 2 (Zebra Shelter):** 1 camera trap + 1 acoustic sensor. Few animals detected at giraffe feeder previously; fewer trees = less false triggers.
- **Grevy's:** Stopped to see new foal, no sensor installed.
- **Stop 3 (Pasture D):** Drove past. Herd of phorses and 2 Pere David's deer grazing.
- **Stop 4 (Lake Trail Gate O):** 1 acoustic sensor for bird calls.
- **Stop 5 (Lake Trail lakeshore):** 1 camera trap for water activity.
- **Stop 6 (Fence with vegetation):** 1 acoustic sensor.
- **Stop 7 (Zipline Tower):** 1 acoustic sensor. Heard guests on zipline, may affect recordings.

Notes: No drone flights. All equipment functioning. Used JotForm. Next steps: return Thursday to check SD cards, use MegaDetector pipeline for quick field processing.

### Equipment Inventory (field_notes/equipment.csv)

| ID | Model | Manufacturer | Owner | Power | Storage | Condition |
|----|-------|-------------|-------|-------|---------|-----------|
| CT01 | T5NG | GardePro | ICICLE SmartFields | 8 AA | 256GB SD | New |
| CT02 | T5NG | GardePro | ICICLE SmartFields | 8 AA | SD Card | New |
| CT03 | T5NG | GardePro | Tanya Berger-Wolf | 8 AA | 32GB SD | Used Good |
| CT04 | G600 | Trail Camera | Tanya Berger-Wolf | 8 AA | 32GB SD | Used Good |
| CT05 | Pro 3.0 Reveal Cellular | Tactacam | ICICLE SmartFields | 8 AA | 32GB SD | New |
| SM01 | Song Meter Micro 2 | Wildlife Acoustics | ICICLE SmartFields | 4 AA | 256GB microSD | New (SN: 2MM15088) |
| SM02 | Song Meter Micro 2 | Wildlife Acoustics | ICICLE SmartFields | 4 AA | 256GB microSD | New |
| SM03 | Song Meter Micro 2 | Wildlife Acoustics | Tanya Berger-Wolf | 4 AA | 256GB microSD | Used Good |
| SM04 | Song Meter Micro 2 | Wildlife Acoustics | Tanya Berger-Wolf | 4 AA | 256GB microSD | Used Good |
| GPS | InReach Mini 2 | Garmin | Tanya Berger-Wolf | Charger | NA | Used Good |

Additional supplies: Charge bank (AluraTek), battery tester (BT-168), pliers, scissors, 500 zip ties, duct/gorilla/masking tape, orange flagging tape (acoustics), pink flagging tape (cameras), sharpies, ziplock bags, 24 AA batteries, SD cards (1x256GB, 1x32GB, 2x16GB), Micro SD cards (2x1TB, 2x64GB, 40x64GB), 3 binoculars (10x42).

---

## Bioacoustics (311 .wav files, 6.0 GB)

### Deployment Log (JotForm - June 30)

| Site | ID | SD Card | Location | Deployed By | DateTime |
|------|----|---------|----------|-------------|----------|
| TW08 | SM04 | 4 | Branch of tree near gate H | Tanishka Wani | 2025-06-30 14:56 |
| TW06 | SM03 | 3 | Zebra shelter | Tanishka Wani | 2025-06-30 14:54 |
| TW05 | SM01 | 1 | Gate post at lake trail gate (Gate O) | Ally Bonney | 2025-06-30 01:30 |
| TW07 | SM02 | 2 | Zip tower | Bharath Pillai | 2025-06-30 02:00 |

### Pickup Log (JotForm - July 3)

All 4 recorders picked up by Bharath Pillai on July 3.

### Recorder Details

**TW05-SM01** (Lake Trail Gate O) -- metadata.md
- Recorder: SM01, Song Meter Micro 2, SN: 2MM15088
- GPS: 39.83537, -81.73842
- Deploy: 2025-06-30 14:56 / Retrieve: 2025-07-03 16:48
- Orientation: East, facing away from wind and road, ~1.5m height
- Schedule: Intended 1hr at sunrise/sunset, but was set to 5-min clips every hour
- **Data: 144 WAV files** (5-min clips at sunrise ~0503-0659 and sunset ~1959-2154)

**TW06-SM03** (Zebra Shelter) -- metadata.md
- Recorder: SM03, Song Meter Micro 2, SN: 2MM18173
- GPS: 39.83518, -81.73087
- Deploy: 2025-06-30 14:54 / Retrieve: 2025-07-03 16:15
- Orientation: Southeast, 2m height
- Schedule: 5 min every hour, at top of hour, 24/7
- **Data: 77 WAV files** (hourly 5-min clips, Jun 30 12:00 - Jul 3 16:00)

**TW07-SM02** (Zipline Tower) -- metadata.md
- Recorder: SM02, Song Meter Micro 2, SN: 2MM15093
- GPS: 39.83288, -81.73455
- Deploy: 2025-06-30 02:00 / Retrieve: 2025-07-03 16:12
- Orientation: Southwest, facing away from gate, ~1.5m height
- Schedule: 1hr at sunrise and 1hr at sunset
- **Data: 12 WAV files** (two ~10-min recordings per day at sunrise/sunset)

**TW08-SM04** (Fence with Vegetation) -- metadata.md
- Recorder: SM04, Song Meter Micro 2, SN: 2MM18039
- GPS: 39.82900, -81.74378
- Deploy: 2025-06-30 14:56 / Retrieve: 2025-07-03 17:07
- Orientation: Southwest, facing away from gate, ~1.5m height
- Schedule: 5 min every hour, at top of hour, 24/7
- **Data: 78 WAV files** (hourly 5-min clips, Jun 30 12:00 - Jul 3 17:00)

### Audio File Locations

| Station | Directory | File Count |
|---------|-----------|------------|
| TW05-SM01 | bioacoustics/TW05-SM01/SD01_20250630_20250703/ | 144 .wav |
| TW06-SM03 | bioacoustics/TW06-SM03/SD03_20250630_20250703/ | 77 .wav |
| TW07-SM02 | bioacoustics/TW07-SM02/SD02_20250630_20250703/ | 12 .wav |
| TW08-SM04 | bioacoustics/TW08-SM04/SD04_20250630_20250703/ | 78 .wav |

---

## Camera Traps (~20,014 files, 49 GB)

### Deployment Log (JotForm - June 30)

| Site | CT ID | SD Card | Heading | Location | Deployed By | DateTime |
|------|-------|---------|---------|----------|-------------|----------|
| TW03 | CT01 | SD01 | S | Salt lick post, old giraffe feeder | Anirudh/Tanishka | 2025-06-30 13:00 |
| TW04 | CT04 | SD04 | NW | Lake trail | Bharath Pillai | 2025-06-30 13:17 |
| TW02 | CT03 | SD03 | SW | Nomad shelter | Penelope Covey | 2025-06-30 12:42 |
| TW01 | CT02 | SD02 | -- | Shelter beam overlooking two lakes | Ally Bonney | 2025-06-30 12:30 |

### Pickup Log (JotForm - July 3)

All 4 camera traps picked up by Bharath Pillai on July 3.

### Camera Trap Details

**TW01-CT02** (Nomad Ridge Shelter, East, facing SE) -- metadata.txt
- Camera: CT02 (GardePro T5NG), SD02 (256GB)
- Deploy: 2025-06-30 12:30 / Retrieve: 2025-07-03 16:00
- Config: Hybrid mode (Photo 4MP 3-burst + Video 1080p 10s MP4 with sound), High PIR, Timelapse hourly, 24hr, Info strip ON
- Weather: Heavy rain/stormy to hot/humid/sunny, mild breeze
- **Data: ~10,408 files** in 4 chunks (JPG + MP4), date range Jun 30 12:18 - Jul 2 06:50
- Location: camera_traps/TW01-CT02/SD02_20250630_20250703/images/chunk1-4/

**TW02-CT03** (Nomad Ridge Shelter, West, facing SW) -- metadata.txt
- Camera: CT03 (GardePro A3), SD03 (32GB)
- Deploy: 2025-06-30 12:42 / Retrieve: 2025-07-03 16:00
- Config: Photo 8MP 3-series + Video 1080p 10s AVI audio ON, Shot lag 10s, High sensor
- **Data: 55 files** (JPG + AVI), very low count suggests early battery death
- Location: camera_traps/TW02-CT03/SD03_20250630_20250703/images/

**TW03-CT01** (Pasture D Giraffe Feeder) -- metadata.txt
- Location: By the lake, salt lick nearby
- **Data: 8,867 files** across 9 folders (100MEDIA - 108MEDIA), date range Jun 30 13:05 - Jul 2 01:04
- Location: camera_traps/TW03-CT01/SD01_20250630_20250703/images/100MEDIA-108MEDIA/

**TW04-CT04** (Lake Trail) -- metadata.txt
- Camera: CT04, Photo 8MP 5-burst + Video 1080p 10s MP4 with sound, High PIR
- **Data: 684 files** in 101MEDIA (JPG + MP4), date range through Jul 3 18:11
- Note: Images appear to be upside down due to installation. Drone flown in front during collection to sync timestamps.
- Location: camera_traps/TW04-CT04/SD04_20250630_20250704/101MEDIA/

---

## Drones (20 video files, 46 GB)

All flights used a **Parrot Anafi** drone. 6 flight sessions across 2 days.

### Flight 1: 20250701_parrotanafi_1
- **Objective:** Survey Pere David's deer near edge of lake
- **Date/Time:** July 1, approx 8:30 AM
- **Lead Pilot:** Vedant Patil | Co-pilots: Jenna Kline, Rugved Katole
- **Observations:** Captured doe in the water, male decorating antlers with reeds
- **Metadata:** 0914_2025-07-01T083438-0400_10D6BC_0018.json (~1.7 MB, Parrot telemetry with GPS, battery, speed, altitude data)
- **Videos:** drones/20250701_parrotanafi_1/video_files/ -- VID_001.MP4, VID_002.MP4, VID_003.MP4, VID_004.MP4

### Flight 2: 20250703_parrotanafi_1
- **Date/Time:** July 3, ~3:47 PM
- **Lead Pilot:** Rugved Katole | Co-pilots: Jenna Kline, Vedant Patil
- **Metadata:** 2 JSON files
- **Videos:** drones/20250703_parrotanafi_1/video_files/ -- VID_001.MP4, VID_002.MP4, VID_003.MP4

### Flight 3: 20250703_parrotanafi_2
- **Date/Time:** July 3, ~4:21 PM
- **Lead Pilot:** Vedant Patil | Co-pilots: Jenna Kline, Rugved Katole
- **Metadata:** 1 JSON file
- **Videos:** drones/20250703_parrotanafi_2/video_files/ -- VID_001.MP4, VID_002.MP4, VID_003.MP4

### Flight 4: 20250703_parrotanafi_3
- **Date/Time:** July 3, ~4:56 PM
- **Lead Pilot:** Vedant Patil | Co-pilots: Jenna Kline, Rugved Katole
- **Metadata:** 1 JSON file
- **Videos:** drones/20250703_parrotanafi_3/video_files/ -- VID_001.MP4, VID_002.MP4

### Flight 5: 20250703_parrotanafi_4
- **Date/Time:** July 3, ~5:23 PM
- **Lead Pilot:** Rugved Katole | Co-pilot: Jenna Kline
- **Metadata:** 1 JSON file
- **Videos:** drones/20250703_parrotanafi_4/video_files/ -- VID_001.MP4, VID_002.MP4, VID_003.MP4

### Flight 6: 20250703_parrotanafi_5
- **Date/Time:** July 3, ~5:25 PM
- **Lead Pilot:** Vedant Patil | Co-pilot: Jenna Kline
- **Metadata:** 1 JSON file
- **Videos:** drones/20250703_parrotanafi_5/videos/ -- VID_001.MP4 through VID_005.MP4

---

## Known Issues and Data Quality Notes

1. **Battery failures:** All camera traps except CT04 ran out of battery before retrieval. TW01-CT02 and TW03-CT01 stopped ~July 2. TW02-CT03 captured only 55 files.
2. **Missing drone metadata:** JSON telemetry missing for parrotanafi_2 and parrotanafi_4 (July 3).
3. **Upside-down images:** TW04-CT04 images may be inverted due to installation orientation.
4. **Incorrect recording schedule:** TW05-SM01 was intended for 1-hour sunrise/sunset recording but was set to 5-min clips every hour.
5. **AVI format:** TW02-CT03 produced AVI video instead of MP4 (different camera model).
6. **Noise pollution:** Running pump at TW04 may affect acoustic and camera data.
7. **Misplaced files:** sam-env.yml and sam-env-full.yml conda specs in TW01-CT02 images directory (processing artifacts).
8. **Directory naming inconsistency:** Last drone flight uses `videos/` instead of `video_files/`.
9. **JotForm connectivity issues:** Multiple team members reported JotForm failures; paper copies used.

---

## Team Members

- **Jenna Kline** (kline377) -- Project lead, field coordination
- **Tanya Berger-Wolf** -- Equipment owner, PI
- **Bharath Pillai** (bharath06) -- Camera trap deployment, pickup, processing pipeline
- **Tanishka Wani** (wani.31@osu.edu) -- Bioacoustic metadata, camera trap deployment
- **Ally Bonney** (bonney.21@osu.edu) -- Camera trap deployment, field notes
- **Penelope Covey** (covey.64@osu.edu) -- Camera trap deployment
- **Anirudh** (potlapally.2@osu.edu) -- Camera trap deployment
- **Vedant Patil** -- Drone pilot
- **Rugved Katole** -- Drone co-pilot
