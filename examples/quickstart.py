#!/usr/bin/env python3
"""SmartWilds quickstart: load the Darwin Core tables, filter by verification
status, join Occurrences to their Events, and pull one drone frame.

Usage:
    python examples/quickstart.py <path to a SmartWilds dataset folder>...

Each argument is a downloaded SmartWilds dataset (for example
`huggingface-cli download --repo-type dataset <repo> --local-dir <dir>`).
Pass several to combine modalities; they share one Event hierarchy.
"""
import sys
from pathlib import Path

import pandas as pd


def load(root):
    root = Path(root)
    ev = pd.read_csv(root / "data/events.csv", dtype=str, keep_default_na=False)
    oc = pd.read_csv(root / "data/occurrences.csv", dtype=str, keep_default_na=False)
    return ev, oc


def main(roots):
    events, occs = zip(*(load(r) for r in roots))
    ev, oc = pd.concat(events, ignore_index=True), pd.concat(occs, ignore_index=True)
    print(f"{len(ev):,} Events, {len(oc):,} Occurrences")

    # 1. Pick a verification floor BEFORE analysis: most labels are machine
    #    predictions (see the dataset card for per-rank accuracy).
    print(oc.identificationVerificationStatus.value_counts().to_string(), "\n")
    verified = oc[oc.identificationVerificationStatus != "unverified"]
    print(f"human-verified Occurrences: {len(verified):,}")

    # 2. Join each Occurrence to its Event, then walk up to the deployment.
    parent = ev.set_index("eventID").parentEventID
    etype = ev.set_index("eventID").eventType
    oc = oc.assign(eventType=oc.eventID.map(etype))
    deploy = oc.eventID.where(oc.eventType == "SensorDeployment", oc.eventID.map(parent))
    oc = oc.assign(deploymentID=deploy)
    print("\nOccurrences per deployment (top 5):")
    print(oc.deploymentID.value_counts().head().to_string())

    # 3. Class-rank summary, which is far more reliable than species rank.
    print("\nOccurrences by class (top 5):")
    print(oc["class"].replace("", "(none)").value_counts().head().to_string())

    # 4. Drone frames: data/detections.csv maps each detection to a raw video
    #    and frame index; extract any frame with OpenCV.
    for r in roots:
        det_path = Path(r) / "data/detections.csv"
        if det_path.exists():
            det = pd.read_csv(det_path)
            row = det.iloc[0]
            print(f"\nfirst drone detection: {row.video_path} frame {row.frame_index} "
                  f"box=({row.bbox_x}, {row.bbox_y}, {row.bbox_w}, {row.bbox_h})")
            video = Path(r) / row.video_path
            if video.exists():
                import cv2
                cap = cv2.VideoCapture(str(video))
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(row.frame_index))
                ok, frame = cap.read()
                if ok:
                    cv2.imwrite("drone_frame.jpg", frame)
                    print("wrote drone_frame.jpg")
            else:
                print("(video not downloaded; fetch media/ to extract frames)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
