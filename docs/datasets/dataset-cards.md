# Dataset cards

One card per dataset, in the Hugging Face dataset-card format with FAIR² and
Darwin Core front matter. The cards are the `README.md` of each dataset when
published; their sources are kept here.

| Card | Dataset |
|---|---|
| [`smartwilds.md`](https://github.com/Imageomics/smartwilds/blob/main/metadata/smartwilds.md) | Study level: merged Event table, text records, sensor configurations, arrival traces |
| [`smartwilds-camera-traps.md`](https://github.com/Imageomics/smartwilds/blob/main/metadata/smartwilds-camera-traps.md) | Camera traps |
| [`smartwilds-bioacoustics.md`](https://github.com/Imageomics/smartwilds/blob/main/metadata/smartwilds-bioacoustics.md) | Bioacoustics |
| [`smartwilds-drones.md`](https://github.com/Imageomics/smartwilds/blob/main/metadata/smartwilds-drones.md) | Drones |
| [`smartwilds-citizen-science.md`](https://github.com/Imageomics/smartwilds/blob/main/metadata/smartwilds-citizen-science.md) | Citizen science |

Alongside the cards: [`DEFECT_INVENTORY.md`](../DEFECT_INVENTORY.md) and its
machine-readable twin `defect_inventory.csv`, and the card images under
`metadata/images/`.

## How the cards were written

The cards follow the [FAIR² Drones Data Standard](https://github.com/Imageomics/fair_drones)
template, which extends the [Imageomics dataset card template](https://imageomics.github.io/Imageomics-guide/wiki-guide/HF_DatasetCard_Template_Imageomics/)
with Darwin Core coverage fields, platform specifications, and annotation
quality fields. They were drafted by LLM coding agents from the tables and the
field notes with those templates as context, then edited by the authors; see
[How we used the agents](../AGENT_ASSISTED_DOCUMENTATION.md).
