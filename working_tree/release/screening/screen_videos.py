#!/usr/bin/env python3
"""Run MegaDetector v5a on frames sampled from every video and record person
detections.

Camera-trap and citizen-science clips are sampled once per second; drone
videos once every two seconds. Output: one JSON line per sampled frame that
has any person detection >= THRESHOLD.

Usage: screen_videos.py videos.txt out.jsonl [--task i --ntasks n]
"""
import argparse
import json
import sys

import cv2
from PIL import Image

from megadetector.detection.run_detector import load_detector

THRESHOLD = 0.1
PERSON = "2"

ap = argparse.ArgumentParser()
ap.add_argument("videos")
ap.add_argument("out")
ap.add_argument("--weights", default="/fs/ess/PAS2136/TheWilds2025/release/screening/md_v5a.0.0.pt")
ap.add_argument("--task", type=int, default=0)
ap.add_argument("--ntasks", type=int, default=1)
args = ap.parse_args()

videos = [v for v in open(args.videos).read().split("\n") if v][args.task::args.ntasks]
det = load_detector(args.weights)
with open(args.out, "a") as out:
    for n, path in enumerate(videos):
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, int(round(fps * (2.0 if "/drones/" in path else 1.0))))
        sampled = hits = 0
        for f in range(0, max(nframes, 1), step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f)
            ok, frame = cap.read()
            if not ok:
                break
            sampled += 1
            h, w = frame.shape[:2]
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            r = det.generate_detections_one_image(img, f"{path}#{f}", detection_threshold=THRESHOLD)
            persons = [d for d in r.get("detections", []) if d["category"] == PERSON]
            if persons:
                hits += 1
                out.write(json.dumps({"file": path, "frame": f, "fps": fps, "width": w, "height": h,
                                      "persons": persons}) + "\n")
        cap.release()
        out.write(json.dumps({"file": path, "summary": True, "fps": fps, "frames": nframes,
                              "sampled": sampled, "frames_with_person": hits}) + "\n")
        out.flush()
        print(f"[{n + 1}/{len(videos)}] {path} sampled={sampled} person_frames={hits}", flush=True)
