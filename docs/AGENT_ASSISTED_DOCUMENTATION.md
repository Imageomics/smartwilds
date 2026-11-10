# How LLM coding agents were used to document SmartWilds

The SmartWilds documentation (the per-campaign data reports, the Darwin Core
tables and their data dictionaries, the dataset cards, the supplement, and the
defect inventory) was produced with LLM coding agents working directly in the
project's file system, under the direction of the authors. This note records
what the agents did, what they were given, and what we learned, so that the
approach can be reused and so that readers know which parts of the
documentation were machine-assisted.

## What the agents did

**Inventorying the archive.** The agents walked each campaign directory and
wrote the data reports in `field_campaigns/`: file counts and sizes per
modality and deployment, the metadata and log files present, naming
conventions, and anything that looked wrong (a camera whose clock reported
2023, a deployment that ran out of battery, drone flights with no telemetry
file). A human then checked each report against the field notes.

**Summarizing the records.** For every modality the agents tabulated the
Darwin Core Events and Occurrences: counts per deployment, per taxon, per
verification status, and per campaign; the date range of each table; and the
share of records with coordinates, times, and media links. Those summaries
became the inventories in `docs/SUPPLEMENTAL.md` (S2, S9, S12) and the counts
in the dataset cards.

**Finding errors and discrepancies.** Most rows of
`docs/DEFECT_INVENTORY.md` were first noticed by an agent cross-checking two
things that should agree: the file inventory against the Event table (WAV
files with no Event; a drone video never processed), the Occurrence dates
against their parent Event's span (curated records that had bypassed the
timestamp correction), the string `nan` where a date should be, duplicate
identifiers after an annotation update, and media references pointing at a
scratch workspace that no longer existed. The inventory records, for each
defect, what made it visible; that column is in large part a record of these
checks. The field notes were part of the evidence, not just context: the time
of day of the 2025-08-11 drone flights (defect 15) was recovered from the
video containers only after the field log and the day's JotForm check-ins
settled which aircraft wrote local time and which wrote UTC.

**Automated QA/QC.** The checks that proved useful were turned into scripts
so they run on every rebuild rather than once: the read-only table audit
(`scripts/validation/audit_darwin_core_snapshot.py`) and the release-build
checks (dates inside Event spans and the study window, no sentinel strings, no
archive paths, every media reference resolving to an included file, checksums
for every shipped file). The agents wrote the first versions of these scripts
and the audit reports they emit.

**Drafting and maintaining documentation.** Dataset cards, the data
dictionaries (generated from the tables), the supplement, and this
repository's READMEs were drafted by agents from the tables and the field
notes, then edited by the authors. When a table changed, the agents were asked
to find every number in the documentation that depended on it and either
update it or flag it. The dated "before" copies and JSON audit records that
accompany each repair exist so that this re-derivation can be checked.

## What the agents were given

Prompting with the documentation standards we wanted to follow, rather than
describing the desired output from scratch, was the single biggest time saver.
The agents were given, as context for every documentation task:

- the **FAIR² Drones Data Standard** (template, quick-start checklist, and the
  KABR worked example), which fixes the section order of a dataset card, the
  Darwin Core Event and Occurrence fields to report, the platform and sensor
  metadata to capture, and the annotation and quality fields;
- the **Imageomics dataset card template**, which the FAIR² template extends,
  and the Hugging Face dataset-card conventions it builds on;
- the **Darwin Core** term definitions, so that column names, event types, and
  the verification-status vocabulary followed the standard rather than being
  invented;
- the project's own field notes, sensor configuration tables, and processing
  logs.

With those in context, the agents produced cards and inventories in the
expected structure on the first pass, and the review effort went into checking
numbers and wording rather than restructuring. Giving the agent a standard also
made omissions visible: an empty template section is a prompt to go and find
the missing information (or to record, as in S8 of the supplement, that it is
genuinely absent and why).

The guidelines are small enough to include verbatim in an agent's context or
to package as a reusable skill:

| Resource | Use |
|---|---|
| FAIR² Drones Data Standard, <https://imageomics.github.io/fair_drones/> (`TEMPLATE.md`, `QUICKSTART_GUIDE.md`) | Dataset card structure and required metadata for drone and multi-sensor wildlife datasets |
| Imageomics dataset card template, <https://imageomics.github.io/Imageomics-guide/wiki-guide/HF_DatasetCard_Template_Imageomics/> | Base card template for biodiversity and computer-vision datasets |
| Hugging Face dataset cards, <https://huggingface.co/docs/hub/datasets-cards> | YAML front matter and card conventions |
| Darwin Core, <https://dwc.tdwg.org/terms/> | Term definitions for Events and Occurrences |
| KABR behavior telemetry dataset, <https://huggingface.co/datasets/imageomics/kabr-behavior-telemetry> | A completed FAIR² Drones card and processing scripts to imitate |

## Limits and review

The agents did not decide what the data mean. Every repair in the defect
inventory was chosen by the authors; the agents proposed candidates and
implemented the chosen one with a before-copy and an audit record. Numbers in
the documentation were recomputed from the tables, not copied from earlier
prose, and the authors spot-checked them against independent counts. Where a
figure could not be recomputed from the released tables, the supplement says
so. Agent-drafted text was edited for accuracy and tone before release, and
remaining uncertainties are marked in the documents rather than resolved by
guesswork.

One class of text is never drafted: funder acknowledgements. Grant support
language, award numbers, and the funders' disclaimer are copied exactly from
`guidelines/ACKNOWLEDGEMENTS.md`; an agent that paraphrases or shortens them
produces a wrong acknowledgement, and the review checks for it.

## References

- Wilkinson, M. D. et al. (2016). The FAIR Guiding Principles for scientific
  data management and stewardship. *Scientific Data* 3, 160018.
  <https://doi.org/10.1038/sdata.2016.18>
- Wieczorek, J. et al. (2012). Darwin Core: an evolving community-developed
  biodiversity data standard. *PLoS ONE* 7(1), e29715.
  <https://doi.org/10.1371/journal.pone.0029715>
- Kline, J. and Campolongo, E. G. (2026). FAIR² Drones Data Standard for
  Wildlife Datasets. <https://imageomics.github.io/fair_drones/>
- Kline, J. M., Potlapally, A., and Campolongo, E. G. (2026). SmartWilds:
  Integrating, Aligning, and Documenting Multi-Modal Field Sensing Data. Under
  review.
- Barnas, A. F. et al. (2020). A standardized protocol for reporting methods
  when using drones for wildlife research. *Journal of Unmanned Vehicle
  Systems* 8(2), 89–98. <https://doi.org/10.1139/juvs-2019-0011>
- Campolongo, E. G., Thompson, M. J., Zhang, N., Duan, Y., Bradley, J., & Lapp, H.
  (2026). Imageomics Guide (Version 2.3.1) [Computer software].
  <https://doi.org/10.5281/zenodo.17817610>
