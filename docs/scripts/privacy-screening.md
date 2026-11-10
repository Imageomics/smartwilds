# Privacy screening

People appear in camera-trap images (visitors and staff), in visitor
photographs, and near drone launch and landing sites. `scripts/privacy_screening/`
finds them with MegaDetector v5a and triages them by identifiability before
release.

!!! info "The rule"
    A person whose box is shorter than 80 px in the native image cannot be
    identified (the face is then under about 10 px), so the file is released as
    is. Any person box at or above 80 px, at confidence ≥ 0.2, sends the file to
    human review. Review decides: release (false positive or not identifiable)
    or remove. Media in which a person can be individually identified are
    removed from the release; drone videos are trimmed losslessly at launch
    and landing instead of being dropped whole.

## Steps

1. **`make_lists.py`** lists every camera-trap and citizen-science still (in
   four shards) and every video under the campaign directories, skipping the
   withdrawn TW07-CT05 deployment.
2. **`run_screening.sh`** is the SLURM array job that was used: MegaDetector
   batch runs on the image shards and `screen_videos.py` on the video halves.
   It needs a GPU and a virtual environment with `megadetector`, `av`, and
   `imageio-ffmpeg`.
3. **`screen_videos.py`** samples frames (every second for camera and visitor
   clips, every two seconds for drone videos) and writes one JSON line per
   frame with a person detection.
4. **`triage.py`** turns the detector output into
   `person_screening_images.csv` and `person_screening_videos.csv` with a
   `release` / `review` decision per file, and renders crop sheets for the
   review queue.
5. **`trim_drones.py plan`** proposes lossless start and end trims for drone
   videos whose people are within two minutes of launch or landing, and lists
   mid-flight people for review. **`trim_drones.py apply`** trims only the rows
   a reviewer has marked `approved=yes`, verifying each output's first frame
   against the source.

```bash
export SMARTWILDS_ARCHIVE=/path/to/TheWilds2025
export MEGADETECTOR_WEIGHTS=/path/to/md_v5a.0.0.pt
python scripts/privacy_screening/make_lists.py
sbatch --account=<account> scripts/privacy_screening/run_screening.sh
python scripts/privacy_screening/triage.py
python scripts/privacy_screening/trim_drones.py plan     # then review results/drone_trim_plan.csv
python scripts/privacy_screening/trim_drones.py apply
```

Screening evidence is carried into the release: the camera image inventory and
media manifests have `privacyScreeningStatus`, `privacyScreeningMethod`,
`privacyHumanReviewStatus`, and `privacyEvidencePath` columns.
