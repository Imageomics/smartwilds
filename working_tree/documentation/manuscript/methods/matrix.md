# Methods draft — revised subsections and tables
## SmartWilds multi-sensor paper

---

## 2.4 AI-assisted annotation pipeline

Each modality was processed using a domain-specific AI annotation pipeline
(Table 1). All pipelines convert raw sensor output into the unified observation
schema (Section 2.3); the comparison across modalities therefore rests on a
common representation rather than on modality-specific formats. The pipeline is
model-agnostic: each stage accepts any detection or classification backend that
produces bounding boxes, species labels, and confidence scores, enabling
straightforward replacement of individual models as the state of the art
advances.

**Camera traps.** Images were first passed through MegaDetector v5 to separate
animal detections from blank frames and to produce bounding-box crops. Crops
were then classified to species using BioCLIP v2, a vision-language model
trained on biological imagery. Detections below a confidence threshold of [XX]
were flagged for manual review by the annotator (Bharath). SAM3 was used for
instance segmentation on a subset of images to support morphological trait
extraction and individual re-identification via coat-pattern comparison.

**Depth estimation and GPS association.** To move camera trap detections from
site-level to local (metre-scale) spatial resolution, we applied monocular
depth estimation to each annotated image. The detection bounding-box centroid
was projected to an estimated ground distance using camera mounting height and
tilt angle as calibration parameters. This estimated position was then
associated with the nearest GPS collar fix within a [XX]-minute temporal
window, assigning the detection a candidate individual identity and a
georeferenced location. Depth estimation accuracy was evaluated against [XX]
detections with known positions [from drone orthophoto / GPS ground truth],
yielding a median positional error of [XX] m (IQR [XX]–[XX] m). Although
imperfect, this precision is sufficient to assign detections to habitat patches
at the spatial grain used in the occupancy analysis (Section 2.6). The pipeline
accepts alternative depth estimation backends; we used [current SOTA model] for
all results reported here.

**ARUs.** Audio files were processed with BirdNET (v2.4) to classify bird
vocalizations in 3-second windows across each recording. Detections with
confidence ≥ [XX] were retained. A subset of detections was also processed with
Perch for cross-model comparison. Tanishka validated a stratified random sample
of [XX] detections against spectrograms and, where available, concurrent
observer logs.

**Drone video.** Frames were extracted at [XX] fps and passed through YOLO with
SAHI (sliced inference) to detect animals at typical flight altitudes of
[XX]–[XX] m. OWL-ViT was used for open-vocabulary detection of target species.
Species classification of drone detections is more uncertain than camera trap
classification owing to the overhead perspective and variable resolution;
detections were assigned to species where confidence exceeded [XX] and otherwise
retained at genus or functional-group level.

**Citizen science.** Photographs and videos collected by visiting researchers
and students during field campaigns were manually annotated by Jenna to species
level. All observations were georeferenced from device metadata or from
deployment site coordinates where GPS was unavailable.

**Text data.** Unstructured and semi-structured text files (field notes,
deployment logs, drone mission notes, JotForm CSVs, bioacoustic summaries) were
processed using an LLM-based extraction pipeline to identify species mentions,
habitat descriptions, and temporal references. Extracted records were linked to
the unified schema by site ID and date. LLM extraction outputs were manually
reviewed for false positives (hallucinated species) and false negatives (missed
mentions) on a random sample of [XX] documents, achieving a precision of [XX]
and recall of [XX].

MEE LLM disclosure: Large language models (Claude [version], Anthropic) were
used in the text-data extraction pipeline described above and to assist with
code generation during data processing. All AI-generated code was reviewed,
tested, and validated by the authors. The corresponding author takes
responsibility for all outputs.

---

**Table 1. AI-assisted annotation pipeline by modality.**

| Modality | Lead annotator | AI tools | Primary task |
|---|---|---|---|
| Camera traps | Anirudh | TBD | Animal detection, species classification, depth-based GPS association |
| Drone video | Anirudh |TBD | Animal detection, species classification |
| Bioacoustics (ARU) | Tanishka | BirdNET v2.4 | Species classification from vocalisations |
| Citizen science | Jenna | Manual annotation | Species identification, georeferencing |
| Text data | Jenna | LLM extraction | Structured record extraction from field notes and logs |

Camera trap and bioacoustic pipelines are AI-assisted and validated against
expert-annotated subsets. Citizen science data are manually annotated. Text data
extraction is LLM-assisted with manual validation.

---

## 2.5 Biodiversity metrics

For each modality and for multi-modal fusion, we computed three biodiversity
metrics. 
**Species richness** is the count of distinct species detected per
modality, standardised using XX to account for differences in
sampling effort. 
**Relative abundance** is the count of individuals per species per
unit effort (trap-nights for camera traps, recorder-hours for ARUs, flight-hours
for drones, observer-hours for citizen science, and document-count for text
data). 
**Land-use detection** is the binary presence or absence of each species at
each site aggregated over the deployment period.

---

## 2.6 Detection probability and recall against ground truth

9 (1 male and 8 female) P horses
101 (44 male and 57 female) Pere David's deer
40 (19 male and 21 female) takin
 

The managed setting at The Wilds provides unusually strong ground truth for
evaluating sensor recall.
During the summer 2025 campaign, there were 101 Milu
deer (44 males and 57 females), 40 Sichuan takin (19 males and 21 females), and 9
Przewalski's horses (1 male and 8 female) on site in the two pastured enclosures. These census counts were obtained from the park's animal management team and represent the total number of individuals of each species present during the deployment period.

We used these counts to estimate per-modality detection probability for managed
ungulate species as:

$$\hat{p}_m = \frac{N_{\text{detected},m}}{N_{\text{census}}}$$

where $N_{\text{detected},m}$ is the number of distinct individuals detected
by modality $m$ (using depth-estimated GPS association for camera traps, visual
re-identification for drones, and group count for ARUs and citizen science) and
$N_{\text{census}}$ is the census count for that species.

Note that $\hat{p}_m$ is a lower bound on true detection probability because
(a) not all individuals have equal probability of appearing in sensor coverage
areas and (b) individual re-identification from camera traps and drones is
imperfect. We report $\hat{p}_m$ with this caveat and compare it across
modalities to quantify the marginal gain from fusion. For the fused estimate we
use the union of individuals detected across all modalities. We do not apply
this analysis to bird species detected by ARUs or to species detected only in
text data, where individual-level ground truth is unavailable.


## 2.7 Cross-modal complementarity analysis

### Species overlap matrix

We constructed a modality × modality overlap matrix using the Jaccard
similarity $J(A,B) = |S_A \cap S_B| / |S_A \cup S_B|$ of detected species sets
$S_A$ and $S_B$ for each pair of modalities. Low Jaccard values indicate high
complementarity (each modality detects taxa the other misses). The matrix is
visualised as a heatmap.

### Species × modality detection matrix

A binary detection matrix (species × modality) was constructed for all species
detected across the deployment. Rows are clustered by taxonomic group (mammals,
birds, other); columns are ordered by modality. Taxa detected by only one
modality are highlighted as uniquely detected species. This matrix is the
primary empirical output of the study and directly populates the sensor ×
research-question framework.

### Ablation analysis

To quantify the marginal contribution of each modality to total detected
species richness, we performed an additive ablation: starting from the
lowest-cost modality, we computed cumulative species richness as modalities are
added in order of deployment cost. We also report the loss in richness when each
modality is removed from the full six-modality set. This produces a diminishing-
returns curve that is the empirical basis for the Pareto-optimal sensor
recommendations in the Discussion.

---

## 2.8 Sensor × research-question matrix

**Table 2. Sensor × research-question matrix.**

Capability ratings: **Strong** = primary use case, quantitative output
achievable with existing AI tools; *Partial* = detectable but with meaningful
uncertainty, taxon-limited coverage, or dependence on model performance;
— = sensor not suited to this dimension; *Context* = enriches interpretation
but does not provide direct detection.

| Dimension | Scale | Camera trap | ARU | Drone | GPS collar | Citizen sci. | Text / notes |
|---|---|---|---|---|---|---|---|
| **WHO** | Morphological parts | *Partial* | — | *Partial* | — | *Partial* | — |
| | Individual identity | *Partial* | *Partial* ᵃ | *Partial* | **Strong** | *Partial* | *Context* |
| | Species | **Strong** | **Strong** | *Partial* | **Strong** | **Strong** | *Partial* |
| | Functional group | **Strong** | **Strong** | *Partial* | *Partial* | **Strong** | **Strong** |
| | Community composition | **Strong** | **Strong** | *Partial* | *Partial* | **Strong** | *Context* |
| **WHERE** | Fine-grained (<1 m) | — | — | **Strong** | — | — | — |
| | Local (1–100 m) | **Strong** ᵇ | *Partial* | **Strong** | **Strong** | *Partial* | — |
| | Habitat / site (100 m–1 km) | **Strong** | **Strong** | **Strong** | **Strong** | **Strong** | **Strong** |
| | Landscape (1–100 km) | — | *Partial* | *Partial* | **Strong** | *Partial* | — |
| | Regional / planetary | — | — | — | **Strong** | *Partial* | *Context* |
| **WHEN** | Instantaneous (<1 s) | **Strong** | **Strong** | **Strong** | *Partial* | *Partial* | — |
| | Event / diel (s–h) | **Strong** | **Strong** | *Partial* | **Strong** | — | — |
| | Campaign (days–weeks) | **Strong** | **Strong** | *Partial* | **Strong** | *Partial* | **Strong** |
| | Seasonal (months–years) | **Strong** | **Strong** | — | **Strong** | *Partial* | *Context* |
| | Cadence / burstiness | *Partial* (event-triggered) | **Strong** (continuous) | *Partial* (bursty flights) | **Strong** (continuous) | *Partial* (directable) | — |

ᵃ Acoustic individual identification (AIID) is achievable in principle for
vocal taxa with individual signatures, but remains an emerging capability
requiring deep learning methods and species-specific training data (Knight et
al. 2024, *Trends Ecol. Evol.*; verify citation).

ᵇ Local spatial resolution for camera traps is enabled by the monocular depth
estimation pipeline described in Section 2.4, which projects bounding-box
centroids to estimated ground positions. Without depth estimation, camera trap
spatial resolution is site-level only.

---

## 2.9 Deployment and annotation effort

**Table 3. Deployment effort, annotation effort, and AI tool maturity by
modality.**

Effort ratings: **High** = substantial specialist skill, time, or equipment
required; *Medium* = moderate effort, partially automatable; **Low** = minimal
effort, routine deployment or fully automated.

| Dimension | Camera trap | ARU | Drone | GPS collar | Citizen sci. | Text / notes |
|---|---|---|---|---|---|---|
| **Deployment effort** | **Low** (strap to tree; weeks unattended) | **Low** (easy to scale; autonomous recording) | **High** (pilot required; per-flight setup; bursty coverage) | **High** (animal capture and collaring) | **Low** (directable via BioBlitz / targeted event) | **Low** (passive; generated alongside other modalities) |
| **Annotation effort** | *Medium* (MegaDetector reduces blanks; BioCLIP classifies; human review of low-confidence detections) | *Medium* (BirdNET automates species ID; human validation of uncertain calls) | **High** (frame extraction; manual or semi-automated species ID from altitude) | **Low** (GPS tracks auto-logged; individual ID pre-assigned at collaring) | *Medium* (community ID on iNaturalist; expert validation of uncertain observations) | **Low** (LLM extraction automated; manual spot-check required) |
| **AI tools available** | **Mature** (MegaDetector, BioCLIP, SAM3, species-specific classifiers) | **Mature** (BirdNET, Perch; strong for birds) | *Developing* (YOLO+SAHI, OWL-ViT; accuracy degrades with altitude and oblique angle) | **Mature** (auto-logged; Movebank ecosystem) | *Developing* (iNaturalist AI ID; accuracy varies by taxon) | *Developing* (LLM extraction; hallucination risk requires validation) |
| **Key AI gaps** | Individual re-ID at scale; night-image classification | Individual AIID nascent; non-vocal taxa undetectable | Species ID from altitude; small or partially occluded animals | Few gaps for GPS track data itself | ID validation; observer-effort bias | Hallucination; completeness of species mentions |
| **Value of information for AI training** | **High** (large labelled image datasets; broad taxonomic coverage) | **High** (large audio corpora; BirdNET training data) | *Medium* (high-resolution imagery; labelled data scarce) | *Medium* (movement trajectories; limited species scope) | **High** (georeferenced, community-validated observations at global scale) | *Low–medium* (contextual labels; not primary training signal) |

---

## Results tables (placeholders — to be filled from pipeline output)

**Table 4. Species richness by modality.**

| Modality | Species detected | Unique species ᵃ | Sampling effort |
|---|---|---|---|
| Camera traps | XX | XX | XX trap-nights |
| ARUs (bioacoustics) | XX | XX | XX recorder-hours |
| Drones | XX | XX | XX flight-hours |
| Citizen science | XX | XX | XX observer-hours |
| Text data | XX | XX | XX documents |
| **All modalities fused** | **XX** | — | — |

ᵃ Taxa detected by this modality only.

---

**Table 5. Per-modality detection probability for managed ungulate species
against mid-campaign census counts.**

| Species | Census *N* | Camera traps *p̂* | ARUs *p̂* | Drones *p̂* | Citizen sci. *p̂* | Fused *p̂* |
|---|---|---|---|---|---|---|
| Père David's deer (*Elaphurus davidianus*) | XX | XX | XX | XX | XX | XX |
| Takin (*Budorcas taxicolor*) | XX | XX | XX | XX | XX | XX |
| Przewalski's horse (*Equus ferus przewalskii*) | XX | XX | XX | XX | XX | XX |

*p̂* = proportion of census individuals detected by each modality over the
deployment period. Fused *p̂* uses the union of individuals detected across all
modalities. See Section 2.6 for caveats on individual re-identification.

---

**Table 6. Operational performance metrics by modality.**

| Metric | Camera trap | ARU | Drone | GPS collar | Citizen sci. | Text / notes |
|---|---|---|---|---|---|---|
| Spatial range | Fixed FOV (~10 m²) | Acoustic radius (~50–100 m) | Flight radius (~500 m per session) | Entire home range | Site-wide (directed event) | Site-wide context |
| Spatial resolution | Within frame; ~1–10 m with depth estimation | Site-level (~50 m) | Sub-metre | ~3–10 m (GPS fix) | Variable (device GPS) | Site-level |
| Temporal range | Weeks–months (unattended) | Weeks–months (unattended) | Hours per flight | Months–years | Event-concentrated (bursty) | Campaign duration |
| Temporal resolution | Event-triggered (PIR) | Continuous or duty-cycled | 30–60 fps video | Hourly to sub-hourly | Opportunistic / directed | Static record |
| Primary taxa | Large–medium mammals | Vocalising birds, bats | Large mammals, ungulates | Collared individual | Broad (observer-dependent) | All (observer-noted) |
| Behavioural detail | Limited (frame capture) | Vocalisations | Posture, group behaviour, interactions | Movement, activity patterns | Variable | Observer narrative |
| Deployment effort | Low | Low | High | High | Low | Low |
| Data volume | Moderate (~236,000 images, Campaign 1–2) | Moderate–high (2,453 WAV files, 202 GB) | High (4K video, 16 sessions) | Low (coordinate logs) | Low–moderate (991 files) | Negligible (~72 files) |

---

*Document generated as working draft for internal review. All XX placeholders
to be filled from SmartWilds annotation pipeline output. Citations marked
"verify" must be checked against Zotero collection before submission.*