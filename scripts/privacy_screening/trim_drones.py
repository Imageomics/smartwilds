#!/usr/bin/env python3
"""Plan and apply launch/landing trims for drone videos with people.

People in drone footage are expected only near launch and landing (the
operators). For each drone video with person detections (conf >= CONF):

  * person frames within EDGE_S seconds of the start  -> trim the start
  * person frames within EDGE_S seconds of the end    -> trim the end
  * person frames in the middle                       -> listed for review,
                                                         never auto-trimmed

Cuts are lossless stream copies (``ffmpeg -c copy``) at keyframes. MP4
cannot re-mux Parrot's timed-metadata data track, so for trimmed videos it is
written losslessly to a sidecar (raw packets + pts index), with a MARGIN_S safety margin. Every
trimmed video is verified by decoding its first frame and comparing it with
the source frame at ``trim_start_frame``.

Usage:
  trim_drones.py plan    # review package: results/drone_trim_plan.csv,
                         # results/DRONE_TRIM_PLAN.md, results/trim_review/*.jpg
  trim_drones.py apply   # trims ONLY rows with approved=yes; writes copies to
                         # release/media_scrubbed/ and results/drone_trims.csv
"""
import subprocess
import sys
from pathlib import Path

import av
import imageio_ffmpeg
import numpy as np
import pandas as pd

D = Path(__file__).resolve().parent
RES = D / "results"
ROOT = "/fs/ess/PAS2136/TheWilds2025/"
OUT_ROOT = Path(ROOT) / "release/media_scrubbed"
CONF, EDGE_S, MARGIN_S = 0.2, 120.0, 2.0


def keyframes(path):
    with av.open(path) as c:
        v = c.streams.video[0]
        ks = [float(p.pts * v.time_base) for p in c.demux(v) if p.is_keyframe and p.pts is not None]
        dur = float(v.duration * v.time_base) if v.duration else float(c.duration / av.time_base)
        return sorted(ks), dur, float(v.average_rate), v.frames


STAGED = Path(ROOT) / "release/hf_smartwilds_20261022/smartwilds-drones"


def screened_drone_frames():
    """Person hits (conf >= CONF) and the list of fully screened drone videos,
    read straight from the screening output so partial runs can be planned."""
    import glob, json
    hits, done = [], set()
    for f in glob.glob(str(RES / "videos_task*.jsonl")):
        for line in open(f):
            r = json.loads(line)
            if "/drones/" not in r["file"]:
                continue
            if r.get("summary"):
                done.add(r["file"])
                continue
            ps = [d for d in r["persons"] if d["conf"] >= CONF]
            if ps:
                hits.append({"file": r["file"], "frame": r["frame"], "width": r["width"], "height": r["height"],
                             "max_conf": max(d["conf"] for d in ps), "boxes": [d["bbox"] for d in ps]})
    return pd.DataFrame(hits), done


def labels_by_video():
    """Labelled drone detections per source video: frame index, taxon, status.
    Machine detections come from data/detections.csv; the 644 curated goose
    records carry their frame only in the lake_json reference."""
    det = pd.read_csv(STAGED / "data/detections.csv", dtype={"frame_index": "Int64"})
    det["file"] = det.video_path.map(lambda p: ROOT + "/".join([p.split("/")[1], "drones"] + p.split("/")[2:]))
    det["status"] = "unverified"
    oc = pd.read_csv(STAGED / "data/occurrences.csv", dtype=str, keep_default_na=False,
                     usecols=["associatedMedia", "occurrenceRemarks", "identificationVerificationStatus",
                              "vernacularName", "scientificName"])
    cur = oc[oc.identificationVerificationStatus == "validated"].copy()
    cur["frame_index"] = pd.to_numeric(cur.occurrenceRemarks.str.extract(r"_(\d{6})_detections\.json")[0])
    cur["file"] = cur.associatedMedia.map(lambda p: ROOT + "/".join([p.split("/")[1], "drones"] + p.split("/")[2:]))
    cur["status"] = "validated"
    cols = ["file", "frame_index", "vernacularName", "scientificName", "status"]
    return pd.concat([det[cols], cur[cols]], ignore_index=True)


def grab(path, t):
    """Frame at time t (or the last frame before the end of the video)."""
    from PIL import Image
    last = None
    with av.open(path) as c:
        v = c.streams.video[0]
        c.seek(int(max(t, 0) / v.time_base), stream=v, backward=True)
        for f in c.decode(v):
            last = f
            if f.pts * v.time_base >= t - 0.02:
                return f.to_image()
    return last.to_image() if last is not None else Image.new("RGB", (640, 360), "gray")


def review_sheet(path, g, start, end, fps, dur, out):
    from PIL import ImageDraw, Image
    W = 360
    tiles = []
    g = g.sort_values("frame")
    if len(g) > 12:
        g = g.iloc[np.linspace(0, len(g) - 1, 12).round().astype(int)]
    for _, r in g.iterrows():
        im = grab(path, r.frame / fps).convert("RGB")
        d = ImageDraw.Draw(im)
        for b in r.boxes:
            x, y, w, h = b[0] * im.width, b[1] * im.height, b[2] * im.width, b[3] * im.height
            d.rectangle([x, y, x + w, y + h], outline=(255, 0, 0), width=max(3, im.width // 300))
        tiles.append((im, f"person t={r.frame / fps:.1f}s conf={r.max_conf:.2f}", (200, 0, 0)))
    if start > 0:
        tiles.append((grab(path, start), f"FIRST KEPT t={start:.1f}s", (0, 140, 0)))
    if end < dur - 0.5:
        tiles.append((grab(path, max(end - 1.0 / fps, 0)), f"LAST KEPT t={end:.1f}s", (0, 140, 0)))
    cols = 4
    th = int(W * 9 / 16)
    sheet = Image.new("RGB", (cols * W, ((len(tiles) + cols - 1) // cols) * (th + 22) + 30), "white")
    dd = ImageDraw.Draw(sheet)
    dd.text((5, 5), "/".join(path.split("/")[-4:]) + f"   duration {dur:.0f}s   proposed keep "
            f"{start:.1f}-{end:.1f}s", fill="black")
    for k, (im, lab, col) in enumerate(tiles):
        im = im.copy()
        im.thumbnail((W, th))
        X, Y = (k % cols) * W, 30 + (k // cols) * (th + 22)
        sheet.paste(im, (X, Y))
        dd.rectangle([X, Y, X + im.width - 1, Y + im.height - 1], outline=col, width=3)
        dd.text((X + 3, Y + th + 4), lab, fill=col)
    sheet.save(out, quality=82)


def plan():
    hits, done = screened_drone_frames()
    labels = labels_by_video()
    sheets = RES / "trim_review"
    sheets.mkdir(exist_ok=True)
    rows = []
    for path, g in hits.groupby("file"):
        ks, dur, fps, nframes = keyframes(path)
        t = g.frame / fps
        launch, land = t[t <= EDGE_S], t[t >= dur - EDGE_S]
        middle = g[(t > EDGE_S) & (t < dur - EDGE_S)]
        start = next((k for k in ks if k >= launch.max() + MARGIN_S), dur) if len(launch) else 0.0
        end = max((k for k in ks if k <= land.min() - MARGIN_S), default=0.0) if len(land) else dur
        s_f, e_f = int(round(start * fps)), int(round(end * fps))
        lab = labels[labels.file == path]
        cut = lab[(lab.frame_index < s_f) | (lab.frame_index >= e_f)]
        rows.append({
            "video": path[len(ROOT):], "screening_complete": path in done,
            "duration_s": round(dur, 1), "fps": round(fps, 3), "frames": nframes,
            "person_frames_launch": len(launch), "person_frames_landing": len(land),
            "person_frames_middle": len(middle),
            "middle_person_times_s": ";".join(f"{x:.1f}" for x in middle.frame / fps),
            "max_person_conf": round(g.max_conf.max(), 3),
            "proposed_keep_start_s": round(start, 3), "proposed_keep_end_s": round(end, 3),
            "seconds_removed": round(dur - max(0.0, end - start), 1),
            "labels_in_video": len(lab), "labels_removed": len(cut),
            "validated_labels_removed": int((cut.status == "validated").sum()),
            "taxa_removed": "; ".join(f"{k} ({v})" for k, v in
                                      cut.vernacularName.replace("", "(no common name)").value_counts().head(5).items()),
            "FLAG_overlaps_labels": "YES" if len(cut) else "",
            "FLAG_middle_people": "YES" if len(middle) else "",
            "FLAG_entire_video_removed": "YES" if end - start <= 0 else "",
            "action_proposed": ("withhold_or_review" if end - start <= 0 else
                                "trim" if (len(launch) or len(land)) else "review_only"),
            "approved": "", "reviewer_notes": "",
            "review_sheet": f"trim_review/{'__'.join(path.split('/')[-4:])}.jpg",
        })
        review_sheet(path, g, start, end, fps, dur, RES / rows[-1]["review_sheet"])
    p = pd.DataFrame(rows).sort_values("video")
    no_people = sorted(f[len(ROOT):] for f in done if f not in set(hits.file if len(hits) else []))
    p.to_csv(RES / "drone_trim_plan.csv", index=False)
    md = ["# Drone trim plan (for review; nothing has been edited)", "",
          f"Person screening: MegaDetector v5a, conf >= {CONF}, one frame every 2 s. "
          f"Launch/landing window: first/last {EDGE_S:.0f} s; cuts at keyframes with a {MARGIN_S:.0f} s margin.",
          "To approve a trim, set `approved` to `yes` in `drone_trim_plan.csv` "
          "(optionally edit `proposed_keep_start_s` / `proposed_keep_end_s`). `apply` trims only approved rows.", "",
          "| Video | Dur (s) | People launch/land/middle | Keep (s) | Removed (s) | Labels removed | Flags |",
          "|---|---:|---|---|---:|---:|---|"]
    for _, r in p.iterrows():
        flags = ", ".join(x for x, c in (("ENTIRE VIDEO", r.FLAG_entire_video_removed),
                                         ("overlaps labels", r.FLAG_overlaps_labels),
                                         ("people mid-flight", r.FLAG_middle_people)) if c)
        md.append(f"| `{'/'.join(r.video.split('/')[-3:])}` | {r.duration_s:.0f} | "
                  f"{r.person_frames_launch}/{r.person_frames_landing}/{r.person_frames_middle} | "
                  f"{r.proposed_keep_start_s:.1f}-{r.proposed_keep_end_s:.1f} | {r.seconds_removed:.1f} | "
                  f"{r.labels_removed} ({r.validated_labels_removed} validated) | {flags} |")
    md += ["", f"Screened drone videos with no person detections ({len(no_people)}): no trim proposed.", ""]
    md += [f"- `{v}`" for v in no_people]
    (RES / "DRONE_TRIM_PLAN.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


def first_frame(path, seek_frame=None, fps=None):
    with av.open(path) as c:
        v = c.streams.video[0]
        if seek_frame:
            target = seek_frame / fps
            c.seek(int(target / v.time_base), stream=v, backward=True)
            for f in c.decode(v):
                if f.pts * v.time_base >= target - 0.5 / fps:
                    return f.to_ndarray(format="rgb24").astype(np.int16)
        return next(c.decode(v)).to_ndarray(format="rgb24").astype(np.int16)


def export_data_track(src, start, end, dst):
    """MP4 cannot re-mux Parrot's timed-metadata track, so keep its raw packets
    for the kept interval as a lossless sidecar: <video>.metadata_track.bin plus
    an index CSV (pts_s relative to the trimmed video, byte offset, size)."""
    rows, n = [], 0
    with av.open(src) as c:
        if not c.streams.data:
            return 0
        s = c.streams.data[0]
        with open(f"{dst}.metadata_track.bin", "wb") as out:
            for pkt in c.demux(s):
                if pkt.pts is None:
                    continue
                t = float(pkt.pts * s.time_base)
                if start <= t < end:
                    b = bytes(pkt)
                    rows.append({"pts_s": round(t - start, 6), "source_pts_s": round(t, 6),
                                 "offset": n, "size": len(b)})
                    out.write(b)
                    n += len(b)
    pd.DataFrame(rows).to_csv(f"{dst}.metadata_track_index.csv", index=False)
    return len(rows)


def apply():
    p = pd.read_csv(RES / "drone_trim_plan.csv", keep_default_na=False)
    p = p[p.approved.str.strip().str.lower() == "yes"]
    if not len(p):
        sys.exit("No approved rows in drone_trim_plan.csv; nothing trimmed.")
    p = p.assign(file=ROOT + p.video, cut_start_s=p.proposed_keep_start_s.astype(float),
                 cut_end_s=p.proposed_keep_end_s.astype(float), frames=p.frames.astype(int),
                 fps=p.fps.astype(float))
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out_rows = []
    for _, r in p.iterrows():
        rel = r.file[len(ROOT):].split("/")
        dst = OUT_ROOT / "/".join(["media", rel[0]] + rel[2:])
        dst.parent.mkdir(parents=True, exist_ok=True)
        cmd = [ff, "-y", "-v", "error", "-ss", f"{r.cut_start_s:.6f}", "-to", f"{r.cut_end_s:.6f}", "-i", r.file,
               "-map", "0", "-map", "-0:d", "-c", "copy", "-map_metadata", "0", "-movflags", "use_metadata_tags",
               str(dst)]
        subprocess.run(cmd, check=True)
        n_meta = export_data_track(r.file, r.cut_start_s, r.cut_end_s, dst)
        start_frame = int(round(r.cut_start_s * r.fps))
        diff = float(np.abs(first_frame(str(dst)) - first_frame(r.file, start_frame, r.fps)).mean()) \
            if start_frame else 0.0
        with av.open(str(dst)) as c:
            kept = c.streams.video[0].frames
            streams = len(c.streams)
        out_rows.append({"file": r.file, "trimmed_path": str(dst), "trim_start_s": r.cut_start_s,
                         "trim_end_s": r.cut_end_s, "trim_start_frame": start_frame,
                         "kept_frames": kept, "source_frames": r.frames, "streams": streams,
                         "metadata_packets": n_meta,
                         "first_frame_mean_abs_diff": round(diff, 3)})
        print(out_rows[-1], flush=True)
    pd.DataFrame(out_rows).to_csv(RES / "drone_trims.csv", index=False)


if __name__ == "__main__":
    {"plan": plan, "apply": apply}[sys.argv[1]]()
