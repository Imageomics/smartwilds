# Goal of paper:
- document data collection
- document data analysis
- document metadata and schema required to support cross-modal coordination
- report characteristics of the dataset
    - by modality
    - arrival rates
    - temporal/spatial resolution
    - analysis
    - characterization

## Potential Venue:
SenSys
submissions as a full or short paper on Visions, Experiences, Tools, Datasets, and Benchmarks:

Visions, grand challenges, or new directions
Experiences, insights, challenges, and lessons learned from real-world deployments
Benchmarks for evaluating systems, models, algorithms, or tools
Tools, toolkits, or frameworks that advance research in embedded AI and sensing systems
Datasets that support research in embedded AI and sensing systems
Frameworks that advance research in embedded AI and sensing systems

TOSN (journal)
The ACM Transactions on Sensor Networks (TOSN) serves as a central, archival venue for the interdisciplinary sensor network research community. It covers research contributions that introduce new concepts, techniques, analyses, or architectures, as well as applied contributions that report on development of new tools and systems or experiences and experiments with high-impact, innovative applications. The Transactions places special attention to contributions on systemic approaches to sensor networks.

# Caveats
- dataset covers June/July, August (main), Sept (drone)
- some data issues, have been solved
- drone flights also conducted in Oct'


## Data sources and references - latest: /fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_latest_20260724

/fs/ess/PAS2136/TheWilds2025/documentation/manuscript/matrix_empirical_20260907.md 


/fs/ess/PAS2136/TheWilds2025/documentation/data_documentation_guidelines

/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline

/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_june_june2026
/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_latest_20260724
/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core
/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata

/fs/ess/PAS2136/TheWilds2025/documentation/annotation_pipeline/MULTI_MODAL_ARCHITECTURE.md


\paragraph{Relationship to the companion papers.}
\smartwilds supports three papers with deliberately disjoint scopes. A
companion \emph{workload} paper~\cite{smartwilds_workload} characterizes
the deployment's arrival processes, service demand, and scheduling
implications in full and derives replayable traces. A companion
\emph{ecological} paper~\cite{smartwilds_ecology} analyzes the research
questions the dataset answers about the biological community.
\emph{This} paper is about the artifact: how the observations were
collected, documented, related, quality-controlled, and made reusable,
and how a practitioner should use them. We summarize the workload in
\S\ref{sec:characterization} only far enough to show what the release
makes measurable, and report no ecological results at all.
\TODO{Both companion citations are placeholders in references.bib ---
please supply titles, venues, and years.}


Distributed systems are complex and challenging to design and maintain. 
Without a solid understanding of the system's behavior under various conditions, it is difficult to build a distributed system, or demonstrate an improvement to one, without a baseline. 
For multi-modal sensing in the field, that baseline does not exist. 
A practioner deciding how many cameras and recorders a site needs, how much inference compute to place at the edge versus the backhaul, what a coordination policy will cost in communication, or whether a trigger from an acoustic sensor to a drone would pay for itself, has no measured deployment to reason against.
These systems questions are typically answerable from trace datasets.
However, system traces in these applications are scarce. 

A growing class of applications makes this gap in cross-modal sensing particularly urgent: observation of dynamic, remote, and resource-constrained environments.
Domains including climate resilience, coastal monitoring disaster response, digital agriculture, ecology and biodiversity, conservation, and security and defense all need to sense the environment in order to make timely decisions.
In such dynamic systems, decision-makers require high-resolution, actionable information about changing conditions, and the ability to adapt sensing strategies in response to new data.
Each operates where power,
connectivity, and human attention are scarce, so what to sense and what
to transmit become decisions the system must make for itself.
The subjects under observation are often mobile, episodic, or rare, so uniform sampling is wasteful and adaptive.

Adaptive, cross-modal sensing is a natural solution to these problems \cite{pollock2021adaptive}, but it is not yet a practical one.
Environmental sensor networks established long-term observation under field constraints~\cite{metzger2019neon,staccone2021neon}, and ecological sensing specialized around living systems~\cite{lahozmonfort2021monitoring}.
Newly cost-effective technologies have made it possible to deploy large-scale sensor networks, including cellular camera traps,
programmable recorder duty cycles, 10\,Hz drone telemetry, and
on-device foundation models now mean one modality's observation can
change another's behavior. 
However, available datasets do not support the systems questions that arise in such multi- and cross-modal deployments.
Ecological datasets are optimized for taxonomic reuse~\cite{wieczorek2012darwincore,ahumada2020wildlifeinsights} and
computer-vision datasets for model training~\cite{liang2021multibench}.
Both domains discard the operational record a systems question needs, including device
schedules, trigger semantics, clock provenance, spatial support, and an
record of when sensors were off or broken.  

We present \smartwild, a dataset and benchmark for designing and evaluating multi- and cross-modal sensing systems, and a practitioner's guide to its reuse.
Across three 2025 field campaigns at The Wilds
conservation center we ran 13 camera-trap installations, 10 acoustic
recorder deployments, and 16 drone flight sessions, and collected
citizen-science submissions from park visitors, totalling 561\,GB of raw data.
We document the data engineering process required to make it usable, designing a cross-modal Event and Occurrence model, reconciling device records against field records, distinguishing six kinds of ``no data,'' and documenting the residual uncertainty none of this removes.
With \smartwilds a practioner can replay the deployment as an arrival
process at either the acquisition or the inference layer.
The acquisition layer lets a designer answer what-if questions about sensor count and placement, and the inference layer lets them answer what-if questions about compute, communication, and cross-modal triggering.
Users may also vary sensor
count and placement against measured per-device yield, size inference
compute against measured detection rates and their tails, estimate
communication cost against real volumes and duty cycles, and evaluate a
cross-modal trigger against the measured temporal asymmetry between
persistent and episodic modalities. 
Previous datasets support only one of these questions at a time, and none support any of them against measurement rather than assumption.

We document the process we used to make the release trustworthy, and the lessons it teaches about what a future deployment should record redundantly so that defects are detectable and repairable, including characterizing the workload at two layers, sensor acquisition and inference output.
During data quality checks, we uncovered commonly encountered errors including clock drift or reset, schedule mismatches, and battery failures \cite{lahozmonfort2021monitoring,ahumada2020wildlifeinsights}.
Our analysis shows that these errors are effectively certain, and that the only way to make them detectable is to record the same state in two places, which we document in our field protocols.
We found that modalities share no provisioning regime, as arrival rates span three orders of magnitude (0.40--367.8 arrivals/hour) and burstiness runs from $+0.10$, for acoustic file acquisition where the duty cycle dominates and arrivals are near-Poisson, to $+0.99$ for drone detections confined to single flight hours. 
And measuring the same stream at two layers --- sensor
acquisition and inference output --- shows inference \emph{amplifies}
burstiness everywhere ($B{=}+0.35\!\to\!+0.76$ for cameras,
$+0.10\!\to\!+0.53$ for acoustics), because detections cluster in the
few captures containing animals. 


\paragraph{Terminology.}
We use \emph{Event} and \emph{Occurrence} in their Darwin Core
sense~\cite{wieczorek2012darwincore,tdwgDarwinCore}: a Darwin Core Event
is a sampling act, an Occurrence an organism record. Neither means what
``event'' means in systems work, where it denotes an arrival in a
stream. We therefore reserve the capitalized terms for the Darwin Core
record types and say \emph{arrival} for the systems sense.
Table~\ref{tab:glossary} fixes the vocabulary both communities overload.


\paragraph{Scope.}
The drone campaigns were flown for \emph{population estimation and
behavioral observation}, not per-animal geolocation. The drone's own
GPS, which places a detection in a known pasture, is the operative
spatial reference and is adequate for that purpose; per-animal ground
projection is an optional refinement we compute where telemetry permits
but do not rely on (\S\ref{sec:scope}).

\subsection{Research Questions}

\begin{description}
    \item[RQ1:] What must a field deployment release in order to serve
    as a baseline for cross-modal sensing systems research --- that is,
    to let a designer answer what-if questions about sensor count,
    inference compute, communication cost, and cross-modal triggering
    against measurement rather than assumption?

    \item[RQ2:] How can a shared data model integrate heterogeneous
    observations without discarding their modality-specific spatial,
    temporal, and semantic properties?

    \item[RQ3:] What does the resulting baseline reveal about
    cross-modal sensing as a systems workload?

    \item[RQ4:] Given that metadata defects are certain, what should
    future deployments record redundantly so those defects are
    detectable and the baseline is trustworthy?
\end{description}

\subsection{Contributions}

\begin{itemize}
    \item \textbf{A baseline for cross-modal sensing systems research}
    (\S\ref{sec:campaign}, \S\ref{sec:release}). 561\,GB of raw
    observations from three campaigns, harmonized into 2{,}404 Darwin
    Core Events and 552{,}964 Occurrences, released with the operational
    metadata that makes the sensing system itself reconstructible:
    per-device duty cycles and trigger semantics, corrected timestamps
    with per-image confidence, data volumes, field and service logs, and
    failure records.

    \item \textbf{A data model for cross-modal field observations}
    (\S\ref{sec:model}): a four-level Event hierarchy, a typed
    identifier scheme spanning fixed sensors and moving platforms, a
    provenance chain from raw asset to inferred Occurrence, per-record
    verification status, and six explicitly distinguished kinds of
    missingness. Because manual annotation does not scale to
    sensor-network volumes --- our human-reviewed records are 0.4\% of
    the release --- we label with state-of-the-art models and publish
    model identity, parameters, and per-rank accuracy as first-class
    content, which is what lets labels be re-derived when better models
    arrive (\S\ref{sec:provenance}).

    \item \textbf{A two-layer workload characterization}
    (\S\ref{sec:characterization}): arrival rates, burstiness, and
    diurnal structure at both the sensor acquisition and the inference
    output layer, with the finding that inference systematically
    amplifies burstiness.

    \item \textbf{A quality-control experience report organized around
    detectability} (\S\ref{sec:qc}): 17 defect classes, each paired with
    source that detected it, the repair applied, the data
    fraction touched, and the residual uncertainty --- including the two
    for which no second record existed. From these we derive seven
    instrumentation requirements (\S\ref{sec:lessons}), led by
    deliberate redundancy in deployment records.

    \item \textbf{A practitioner's guide to reuse}
    (\S\ref{sec:using}): which entry point serves which question, what
    each record supports, and how the artifact transfers to remote
    dynamic sensing outside ecology.
\end{itemize}

Supplemental material accompanying the release carries the full
inventories, field dictionary, repair tables, standards crosswalk, and
validator documentation referenced throughout.
