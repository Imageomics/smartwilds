Assumptions
- Camera traps use one detection row as one event timestamp; filtered CSVs are preferred when present.
- Acoustics use WildsBird_Every_Hour.csv and mark a bin active when total_birds > 0.
- Drone events are assigned to the nearest camera-trap site within the existing 50 m valid-match threshold.
- Drone events treat non-animal labels 'person' and 'vehicle' as non-events.
- Text observations are opportunistic rather than continuous sensing, so they are daily-only by default.
- Text rows total: 30; with explicit eventTime: 19; used: 24.
- include_subdaily_text: False
- Pairwise Jaccard is computed only across sites that are present in both modalities.
- A matrix cell is NA when the modality pair has no overlapping sites or no active bins in the comparable sites.
