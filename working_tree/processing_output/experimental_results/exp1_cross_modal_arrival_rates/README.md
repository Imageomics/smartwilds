# Cross-Modal Arrival Rates Analysis

Use methodology established in SEC '24 paper Characterizing and Profiling AI-Driven Animal Ecology Workloads to analyze arrival rates of events across camera trap, acoustic, drone, and citizen science modalities. 


Data location: /fs/ess/PAS2136/TheWilds2025/processing_output/detections

Steps:

1. Extract timestamps from all 4 modalities using `/fs/ess/PAS2136/TheWilds2025/documentation/adae_model/extract_wilds_multimodal.py` to create cumulative arrival distributions per modality
2. Apply ADAE methodology (`/fs/ess/PAS2136/TheWilds2025/documentation/adae_model/change_points.py`): detect change points in cumulative arrival distributions at thresholds [0.8, 0.95, 0.99, 0.995]
3. Fit time-varying Poisson processes per modality and recreate summary of results
4. Compute per-modality statistics: total events, mean arrival rate, coefficient of variation (CV), burstiness parameter B = (CV−1)/(CV+1)
5. Compare across modalities
6. Plot results: cumulative arrival distributions, change points, and summary statistics