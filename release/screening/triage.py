#!/usr/bin/env python3
"""Triage MegaDetector person detections into release / review.

Rule: a person whose box is shorter than MIN_ID_PX pixels in the native image
cannot be individually identified (the face is then at most ~1/8 of the box,
i.e. < 10 px), so the file can be released as is. Any person box at or above
MIN_ID_PX, at confidence >= CONF, sends the file to human review. Review
decides: release (false positive / not identifiable) or scrub (blur boxes).

Outputs (in results/):
  person_screening_images.csv   one row per still with any person >= CONF
  person_screening_videos.csv   one row per video with any person >= CONF
  review_sheets/*.jpg           person crops for every file in the review queue
"""
import glob
import json
import os
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageOps

D = Path(__file__).resolve().parent
RES = D / "results"
ROOT = "/fs/ess/PAS2136/TheWilds2025/"
CONF = 0.2
MIN_ID_PX = 80


def modality(p):
    return p[len(ROOT):].split("/")[1]


def load_images():
    rows = []
    for shard in range(4):
        f = RES / f"images_shard{shard}.json"
        if not f.exists():
            f = RES / f"images_shard{shard}.ckpt.json"  # partial run
        if not f.exists():
            continue
        data = json.load(open(f))
        for im in data.get("images") or data.get("checkpoint") or []:
            ps = [d for d in im.get("detections") or [] if d["category"] == "2" and d["conf"] >= CONF]
            if not ps:
                continue
            H = im.get("height") or Image.open(im["file"]).size[1]
            W = im.get("width") or Image.open(im["file"]).size[0]
            hpx = [d["bbox"][3] * H for d in ps]
            rows.append({"file": im["file"], "modality": modality(im["file"]), "width": W, "height": H,
                         "n_person": len(ps), "max_conf": max(d["conf"] for d in ps),
                         "max_person_h_px": round(max(hpx)), "boxes": json.dumps([d["bbox"] for d in ps])})
    df = pd.DataFrame(rows)
    if len(df):
        df["decision"] = (df.max_person_h_px >= MIN_ID_PX).map({True: "review", False: "release_too_small"})
    return df


def load_videos():
    frames, summaries = [], []
    for f in glob.glob(str(RES / "videos_task*.jsonl")):
        for line in open(f):
            r = json.loads(line)
            if r.get("summary"):
                summaries.append(r)
                continue
            ps = [d for d in r["persons"] if d["conf"] >= CONF]
            if ps:
                frames.append({"file": r["file"], "frame": r["frame"],
                               "max_conf": max(d["conf"] for d in ps),
                               "max_person_h_px": max(d["bbox"][3] * r["height"] for d in ps),
                               "boxes": [d["bbox"] for d in ps]})
    fr = pd.DataFrame(frames)
    if not len(fr):
        return pd.DataFrame(), fr
    v = fr.groupby("file").agg(frames_with_person=("frame", "size"), max_conf=("max_conf", "max"),
                               max_person_h_px=("max_person_h_px", "max")).reset_index()
    v["max_person_h_px"] = v.max_person_h_px.round()
    v["modality"] = v.file.map(modality)
    v["decision"] = (v.max_person_h_px >= MIN_ID_PX).map({True: "review", False: "release_too_small"})
    return v, fr


def sheets(df, name, per_sheet=24, thumb=300):
    out = RES / "review_sheets"
    out.mkdir(exist_ok=True)
    tiles = []
    for _, r in df.sort_values("max_person_h_px", ascending=False).iterrows():
        im = ImageOps.exif_transpose(Image.open(r.file)).convert("RGB")
        W, H = im.size
        boxes = json.loads(r.boxes)
        b = max(boxes, key=lambda b: b[3])
        pad = 0.25
        x0, y0 = max(0, (b[0] - pad * b[2]) * W), max(0, (b[1] - pad * b[3]) * H)
        x1, y1 = min(W, (b[0] + (1 + pad) * b[2]) * W), min(H, (b[1] + (1 + pad) * b[3]) * H)
        crop = im.crop((int(x0), int(y0), int(x1), int(y1)))
        crop.thumbnail((thumb, thumb))
        tile = Image.new("RGB", (thumb, thumb + 28), "white")
        tile.paste(crop, ((thumb - crop.size[0]) // 2, 0))
        ImageDraw.Draw(tile).text((3, thumb + 2), f"{len(tiles)} h={int(r.max_person_h_px)} c={r.max_conf:.2f}\n"
                                  f"{'/'.join(r.file.split('/')[-3:])[:48]}", fill="black")
        tiles.append(tile)
    for s in range(0, len(tiles), per_sheet):
        cols = 6
        group = tiles[s:s + per_sheet]
        sheet = Image.new("RGB", (cols * thumb, ((len(group) + cols - 1) // cols) * (thumb + 28)), "white")
        for k, t in enumerate(group):
            sheet.paste(t, ((k % cols) * thumb, (k // cols) * (thumb + 28)))
        sheet.save(out / f"{name}_{s // per_sheet:03d}.jpg", quality=80)


if __name__ == "__main__":
    img = load_images()
    vid, frames = load_videos()
    img.to_csv(RES / "person_screening_images.csv", index=False)
    vid.to_csv(RES / "person_screening_videos.csv", index=False)
    if len(frames):
        frames.to_csv(RES / "person_screening_video_frames.csv", index=False)
    for name, df in (("images", img), ("videos", vid)):
        if len(df):
            print(name, df.groupby(["modality", "decision"]).size().to_dict())
    if len(img):
        sheets(img[img.decision == "review"].reset_index(drop=True), "images_review")
