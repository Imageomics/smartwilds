# Guidelines to give the agent

Prompting with the documentation standards we wanted to follow, rather than
describing the desired output from scratch, was the single biggest time saver.
These are the documents we kept in the agent's context (or packaged as a
reusable skill) for every documentation task.

| Resource | Use |
|---|---|
| [FAIR² Drones Data Standard](https://github.com/Imageomics/fair_drones): `TEMPLATE.md`, `QUICKSTART_GUIDE.md` | Dataset card structure and required metadata for drone and multi-sensor wildlife datasets: Darwin Core Event and Occurrence fields, platform and sensor metadata, annotation and quality fields |
| [Imageomics dataset card template](https://imageomics.github.io/Imageomics-guide/wiki-guide/HF_DatasetCard_Template_Imageomics/), part of the Imageomics Guide (Campolongo et al., 2026) | Base card template for biodiversity and computer-vision datasets, which the FAIR² template extends |
| [`guidelines/ACKNOWLEDGEMENTS.md`](https://github.com/Imageomics/smartwilds/blob/main/guidelines/ACKNOWLEDGEMENTS.md) | The funder acknowledgements and disclaimer, to be copied verbatim, never paraphrased |
| [Hugging Face dataset cards](https://huggingface.co/docs/hub/datasets-cards) | YAML front matter and card conventions |
| [Darwin Core terms](https://dwc.tdwg.org/terms/) | Term definitions for Events and Occurrences, so column names, event types, and the verification-status vocabulary follow the standard |
| [KABR behavior telemetry dataset](https://huggingface.co/datasets/imageomics/kabr-behavior-telemetry) | A completed FAIR² Drones card and processing scripts to imitate |
| The project's own field notes, sensor configuration tables, and processing logs | The facts |

## Local copies

The FAIR² Drones files are in the repository under `guidelines/`, ready to
hand to an agent:

- [`guidelines/FAIR2_DRONES_README.md`](https://github.com/Imageomics/smartwilds/blob/main/guidelines/FAIR2_DRONES_README.md)
- [`guidelines/FAIR2_DRONES_QUICKSTART_GUIDE.md`](https://github.com/Imageomics/smartwilds/blob/main/guidelines/FAIR2_DRONES_QUICKSTART_GUIDE.md)
- [`guidelines/FAIR2_DRONES_TEMPLATE.md`](https://github.com/Imageomics/smartwilds/blob/main/guidelines/FAIR2_DRONES_TEMPLATE.md)

??? note "FAIR² Drones quick-start checklist"
    --8<-- "guidelines/FAIR2_DRONES_QUICKSTART_GUIDE.md"

## Packaging as a skill

The guidelines are small enough to include verbatim. A minimal skill directory
for a coding agent:

```
skills/dataset-documentation/
├── SKILL.md            # when to use, the steps, the review checklist
├── TEMPLATE.md         # FAIR² Drones dataset card template
├── QUICKSTART_GUIDE.md # FAIR² Drones checklist
├── ACKNOWLEDGEMENTS.md # funder language, copied exactly
└── dwc_terms.md        # the Darwin Core terms the project uses, with definitions
```

`SKILL.md` should state the order of operations (inventory, summarize,
cross-check, draft, review), the rule that numbers are computed rather than
copied, and the rule that missing information is recorded as missing.

## References

- Wilkinson, M. D. et al. (2016). The FAIR Guiding Principles for scientific
  data management and stewardship. *Scientific Data* 3, 160018.
  <https://doi.org/10.1038/sdata.2016.18>
- Wieczorek, J. et al. (2012). Darwin Core: an evolving community-developed
  biodiversity data standard. *PLoS ONE* 7(1), e29715.
  <https://doi.org/10.1371/journal.pone.0029715>
- Kline, J. and Campolongo, E. G. (2026). FAIR² Drones Data Standard for
  Wildlife Datasets. <https://github.com/Imageomics/fair_drones>
- Campolongo, E. G., Thompson, M. J., Zhang, N., Duan, Y., Bradley, J., & Lapp, H.
  (2026). Imageomics Guide (Version 2.3.1) [Computer software].
  <https://doi.org/10.5281/zenodo.17817610>
- Barnas, A. F. et al. (2020). A standardized protocol for reporting methods
  when using drones for wildlife research. *Journal of Unmanned Vehicle
  Systems* 8(2), 89–98. <https://doi.org/10.1139/juvs-2019-0011>
