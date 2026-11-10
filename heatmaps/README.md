# wilds_multimodal_data
Analysis of multi-modal dataset collected at The Wilds Summer 2025

## Overview
This repository contains code for analyzing animal density patterns using multiple sensor modalities deployed at The Wilds. The analysis focuses on creating heat maps to visualize spatial distribution patterns from different data sources.

## Sensor Modalities
The project analyzes data from four sensor types:
- **Camera Trap** - Ground-level camera traps capturing animal movements
- **Bioacoustic** - Audio sensors detecting animal vocalizations
- **Drone** - Aerial imagery from drone surveys
- **Citizen Science** - Images submitted by visitors and community members

## Repository Structure
Each sensor modality has its own directory:
- `camera_trap/` - Camera trap heat map analysis
- `bioacoustic/` - Bioacoustic sensor heat map analysis
- `drone/` - Drone imagery heat map analysis
- `citizen_science/` - Citizen science image heat map analysis

## Branch Workflow
To keep the code organized, development for each modality should be done in dedicated branches:
- `camera-trap-heatmaps` - Camera trap analysis work
- `bioacoustic-heatmaps` - Bioacoustic analysis work
- `drone-heatmaps` - Drone imagery analysis work
- `citizen-science-heatmaps` - Citizen science analysis work

### Creating a Branch for Your Modality
```bash
# Example: Working on camera trap heat maps
git checkout -b camera-trap-heatmaps
cd camera_trap
# Make your changes...
```

## Installation
Install required dependencies:
```bash
pip install -r requirements.txt
```

## Goals
- Generate spatial density heat maps for each sensor modality
- Identify high-activity zones and animal distribution patterns
- Enable multi-modal comparison and integration of findings
