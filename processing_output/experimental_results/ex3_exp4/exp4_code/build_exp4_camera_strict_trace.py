from __future__ import annotations

from pathlib import Path
import pandas as pd

INPUT = Path("outputs/tables/arrivals/replay_trace_labeled.csv")
OUTPUT = Path("outputs/tables/arrivals/replay_trace_exp4_strict_camera.csv")

def main() -> None:
    df = pd.read_csv(INPUT).copy()

    # strict: Campaign 2 camera trace only
    if "modality" in df.columns:
        df = df[df["modality"].astype(str).str.lower().isin(["camera", "camera_traps"])].copy()

    if "arrival_dt" not in df.columns:
        raise ValueError("Expected arrival_dt in replay_trace_labeled.csv")
    if "sensor_id" not in df.columns:
        raise ValueError("Expected sensor_id in replay_trace_labeled.csv")

    out = pd.DataFrame()
    out["event_time"] = pd.to_datetime(df["arrival_dt"], errors="coerce")
    out["site_cam"] = df["sensor_id"].astype(str)
    out["session"] = ""
    out["path"] = df.get("image_names", "").astype(str)
    out["modality"] = "camera_traps"

    # keep motion/timelapse semantics as explicit event type
    if "camera_trigger_type" in df.columns:
        trig = df["camera_trigger_type"].astype(str).str.lower()
        out["event_type"] = trig.where(trig.ne(""), "camera_event")
    else:
        out["event_type"] = "camera_event"

    out["sensor_id"] = df["sensor_id"].astype(str)

    # extras that policies / evaluation may use
    out["event_id"] = df.get("event_id", pd.Series(range(len(df)))).astype(str)
    out["positive"] = df.get("positive", False)
    out["high_priority"] = df.get("high_priority", False)
    out["service_seconds"] = df.get("service_seconds", 0.0)
    out["compute_units"] = df.get("compute_units", 0.0)
    out["is_timelapse"] = df.get("is_timelapse", False)

    out = out.dropna(subset=["event_time"]).sort_values("event_time").reset_index(drop=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False)

    print(f"Saved strict camera replay trace: {OUTPUT}")
    print(f"Rows written: {len(out)}")
    print(out.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
