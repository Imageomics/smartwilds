Notes
- Text observations are loaded with explicit eventTime when present; rows without eventTime remain date-only.
- A common active bin means every modality in the combination has at least one event in the same site and same time bin.
- This is stricter than comparing broad min/max coverage windows.
- If the best_combo_size is less than 4, then a true four-modality co-located study is not possible with the current data.

Best overlap by window
- 1h: combo_size=0, modalities=none, site=none, bins=0
- 6h: combo_size=0, modalities=none, site=none, bins=0
- 24h: combo_size=2, modalities=camera_traps + text_observations, site=TW01, bins=1
