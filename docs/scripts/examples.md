# Example: quickstart

`examples/quickstart.py` shows the minimum a user should do before computing
anything from the tables.

```bash
pip install -r requirements.txt
python examples/quickstart.py darwin_core/smartwilds-camera-traps darwin_core/smartwilds-bioacoustics
```

Pass one or more dataset folders (each with `data/events.csv` and
`data/occurrences.csv`, or a downloaded Hugging Face dataset). They share one
Event hierarchy, so modalities can be combined. The script:

1. **Applies a verification floor.** Prints the `identificationVerificationStatus`
   distribution and separates machine labels (`unverified`, `machine-resolved`)
   from human-reviewed ones.
2. **Joins Occurrences to Events** and walks up to the deployment, then counts
   Occurrences per deployment.
3. **Summarizes by class rank**, which is far more reliable than species rank.
4. **Extracts a drone frame** if a drone dataset with `data/detections.csv`
   and its video is present: `frame_index` is the native frame index, so any
   detection can be rendered from the raw video with OpenCV.

!!! tip
    The folders in `darwin_core/` use `events.csv` / `occurrences.csv` directly
    (no `data/` level). Either pass a downloaded dataset folder, or point the
    script at a folder laid out as `data/events.csv`.
