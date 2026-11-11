# Example: quickstart

`examples/quickstart.py` shows the minimum a user should do before computing
anything from the tables.

```bash
pip install -r requirements.txt
huggingface-cli download --repo-type dataset ABC-Center/smartwilds_metadata --local-dir smartwilds_metadata
python examples/quickstart.py smartwilds_metadata/smartwilds-camera-traps smartwilds_metadata/smartwilds-bioacoustics
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

