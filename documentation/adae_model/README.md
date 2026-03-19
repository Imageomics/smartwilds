# Characterizing and Modeling AI-Driven Animal Ecology Studies at the Edge

This repo provides instructions for extracting workload information from AI-Driven Animal Ecology (ADAE) studies.
We also provide instructions for modelling ADAE studies as time-varying Poisson arrival rates.
These simulated workloads can be used to test different scaling techniques (independent and correlated) and validate edge computing systems for ADAE studies in the field.

![Figure: Workflow of AI-Driven Animal Ecology Study](images/SEC%20figures%20(1).png)
Figure 1: Workflow of AI-Driven Animal Ecology Studies

<details>
  <summary><strong>Paper Abstract</strong></summary>
  <p>
  Platforms that run artificial intelligence (AI)
  pipelines on edge computing resources are transforming the
  fields of animal ecology and biodiversity, enabling novel wildlife
  studies in animals’ natural habitats. With emerging remote sens-
  ing hardware, e.g., camera traps and drones, and sophisticated
  AI models in situ, edge computing will be more significant in
  future AI-driven animal ecology (ADAE) studies. However, the
  study’s objectives, the species of interest, its behaviors, range,
  and habitat, and camera placement affect the demand for edge
  resources at runtime. If edge resources are under-provisioned,
  studies can miss opportunities to adapt the settings of camera
  traps and drones to improve the quality and relevance of
  captured data. This paper presents salient features of ADAE
  studies that can be used to model latency, throughput objectives,
  and provision edge resources. Drawing from studies that span
  over fifty animal species, four geographic locations, and multiple
  remote sensing methods, we characterized common patterns
  in ADAE studies, revealing increasingly complex workflows
  involving various computer vision tasks with strict service
  level objectives (SLO). ADAE workflow demands will soon
  exceed individual edge devices’ compute and memory resources,
  requiring multiple networked edge devices to meet performance
  demands. We developed a framework to scale traces from prior
  studies and replay them offline on representative edge platforms,
  allowing us to capture throughput and latency data across
  edge configurations. We used the data to calibrate queuing and
  machine learning models that predict performance on unseen
  edge configurations, achieving errors as low as 19%
  </p>
</details>


<br>


## Step 1: Extract arrival rates from real ADAE Studies

We provide links to the raw data linked below. Alternatively, you have use the cleaned data provided in the [data](/data) directory and skip to Step 2.


### Camera trap dataset from LILA BC
Data: [Orinoquía Camera Traps](https://lila.science/datasets/orinoquia-camera-traps/) \
Code: [extract_camtrap.py](extract_camtrap.py)

### Drone dataset from KABR 
Data: [KABR Telemetry](https://huggingface.co/datasets/imageomics/KABR-telemetry) \
Code: [extract_kabr.py](extract_kabr.py)

## Step 2: Model ADAE workloads 
Use [change_points.py](change_points.py) to extract change points and arrival rates for the time-varying Poisson process.

Visualize and analyze data with the [Jupyter notebook](PlotADAEWorkloads.ipynb) provided.


## 

![Figure: ADAE Studies in the Field](images/lit%20review%20graphics%20(3).png)
Figure 2: ADAE Studies in the field using networks of camera traps and drones 

## Acknowledgements
This work was funded by the National Science Foundation (NSF) grant OAC-2112006 (ICICLE AI Institute).