## Title: "Multi-Sensor Fusion for Biodiversity Assessment: Accuracy, Complementarity, and
Cost-Effectiveness Trade-off

● Focus: Sensor effectiveness, multi-sensor integration, ecological recommendations
● Audience: Ecologists, conservation practitioners, monitoring program designers
● Key Contribution: Validate sensor accuracy with ground truth, demonstrate multi-sensor fusion improves biodiversity estimate

How well do different sensor modalities capture
wildlife biodiversity?
Coauthors: ABC (Justin, Laura, Sara, Kaitlyn, Oisin, David, Marta), Timm

Sensor                  Biodiversity Metric
                Species Richness        Species     Abundance Land use
Camera trap
ARU
Drone
GPS
Citizen science

# ground truth 
As for species numbers, in mid-July we had:
- 9 (1 male and 8 female) P horses
- 101 (44 male and 57 female) Pere David's deer
- 40 (19 male and 21 female) takin
 

## ideas for AI analysis 
- ablation study of accuracy of each modality alone vs combined
- use fine-tuned yolo for detections w/ ablations
- use bioclip for species classification

## comparisons
make species by modality heat maps - will show citizen science captures more species, but thin on spatial/temporal coverage; camera traps capture more species than drones but less than ARUs, etc.

## metrics
### Species Richness
● What it measures: The number of different species present in an area
● Unit: Count of species (no unit)
● Example: A forest plot contains 12 bird species
● Key point: Doesn't tell you anything about how many individuals of each species exist

### Abundance
● What it measures: The number of individuals of a species (or total individuals)
● Unit: Count of individuals (no standardization by area)
● Example: There are 450 robins in the forest
● Key point: Absolute number without reference to space

### Density
● What it measures: The number of individuals per unit area or volume
● Unit: Individuals per area (e.g., birds/hectare, fish/m³)
● Example: There are 15 robins per hectare
● Key point: Abundance standardized by area, allowing spatial comparisons


Ideas for comparisons
Use JSDM - Laura P and Oisin to estimate habitat usage for species by modality
What happens when you combine all 3 modalities?
First steps: species ID and counting
References:
- Assessing the camera trap methodologies used to estimate density of unmarked
populations
- Understanding co-occurrence by modelling species simultaneously with a Joint Species
Distribution Model (JSDM)
-

## Visualizations to do

1. Date, time, location, sensor modality, and observations in tabular format
a. Observation of a particular individual at a particular time and location (who,
where, when)
b. Metrics for observations = count of animals by species
c. Support to add more observation details later (example: sex, age, behavior)
d. Convert annotated camera trap, acoustic, drone, and citizen science data to
tabular format (team to provide annotated data)
e. Join GPS data so it can be cross-referenced with other modalities
2. Visualization of observations temporally and spatially
a. Google Earth might be a good place to start: The Wilds Google Earth
b. See MoveBank as an example:
https://www.movebank.org/cms/webapp?gwt_fragment=page=search_map
(ideally we would want a small, MVP version of this)
c. Want visualization to link back to sub-directory in HuggingFace (organized by
modality and time range) SmartWilds HF
d. Goal: website or dashboard to make it easy for ecologists and computer
scientists who are interested in using the data to quickly see all the data
available, and drill down by modality/time/observation
3. Analysis of strengths and weaknesses of each modality in capturing specific events (like
deer crossing lake) and general land-use patterns for the deer.
a. Goal: quantify the relative strengths and weaknesses of the different sensing
modalities
b. See metrics below: spatial, temporal, detection/species, efficiency
c. Radar charts might be a good option to visualize these


                Metric Description Examples / Notes
Spatial Range Maximum area over which the sensor can collect data
without relocation GPS collars: entire home range; Camera
traps: fixed location; Drones: up to
battery/flyable distance
Spatial
Granularity /
Resolution
How finely the sensor can
localize animal presence or
behavior
GPS: ~1–10 m; Camera traps: fixed
field-of-view, can detect exact position in
frame; Drones: sub-meter resolution in
imagery
Temporal Range /
Deployment
Duration
How long the sensor can
function unattended
GPS: months–years; Camera traps:
weeks–months; Drones: hours per flight;
Bioacoustics: weeks–months depending on
battery
Temporal
Granularity /
Sampling Rate
Frequency of data collection GPS: hourly; Camera traps: event-triggered
or time-lapse; Drones: video at 30–60 fps;
Bioacoustics: continuous or triggered
recordings
Species
Detectability
Which animals can be
reliably detected
Cryptic species (bioacoustics), large
ungulates (camera traps/drones),
wide-ranging (GPS)
Behavior Detail Level of behavioral
information obtainable
Drones: posture, interactions; Camera traps:
limited to frame; Bioacoustics: vocalizations;
GPS: movement patterns only
Ease of Use /
Operator Effort
Human time required for
deployment, monitoring, and
maintenance
Drones: high; Camera traps: low–medium;
GPS: low once deployed; Bioacoustics:
low–medium
Energy
Efficiency
Battery life or energy
consumption per unit time
Drones: limited by flight time; GPS collars:
months; Camera traps: weeks–months;
Bioacoustics: weeks
Storage Capacity
/ Data Volume
Amount of data generated
and storage needed
Drones/video: high; Camera traps:
moderate; GPS: low; Bioacoustics:
moderate–high


Summary Metrics:
Coverage Efficiency = (Spatial Range × Temporal Range) / Operational Effort
Data Resolution Index = Combined measure of spatial + temporal granularity
Species Coverage Score = Number of species detectable / effort required
Tools used for data annotation by modality
Modality Team Member Tools
Camera Traps Bharath SAMv2, Megadetector
Drone videos Anirudh, Vedant, Rugved OWL
Acoustics Tanishka Perch, BirdNet
GPS Ally TBD
Citizen science Jenna Megadetector, BioClip