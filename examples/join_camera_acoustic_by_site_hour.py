import pandas as pd

def load(root):
    ev = pd.read_csv(f"{root}/events.csv", dtype=str, keep_default_na=False)
    oc = pd.read_csv(f"{root}/occurrences.csv", dtype=str, keep_default_na=False)
    return ev, oc

# Download first:
#   huggingface-cli download --repo-type dataset ABC-Center/smartwilds_metadata --local-dir smartwilds_metadata
cam_ev, cam = load("smartwilds_metadata/smartwilds-camera-traps/data")
aru_ev, aru = load("smartwilds_metadata/smartwilds-bioacoustics/data")

# 1. Temporal key: corrected local timestamp, truncated to the hour.
for df in (cam, aru):
    df["t"] = pd.to_datetime(df.eventDate + " " + df.eventTime, errors="coerce")
    df["hour"] = df.t.dt.floor("h")

# 2. Spatial key: the site code on fixed sensors (TW01 ... TW11), plus the
#    campaign window from the deployment Event, because a few sensors moved
#    between campaigns.
def campaign(ev):
    dep = ev[ev.eventType == "SensorDeployment"].set_index("eventID")
    return dep.eventDate.str.slice(0, 7)          # "2025-06" or "2025-08"
cam["campaign"] = cam.eventID.map(cam_ev.set_index("eventID").parentEventID).map(campaign(cam_ev))
aru["campaign"] = aru.eventID.map(aru_ev.set_index("eventID").parentEventID).map(campaign(aru_ev))

# 3. Co-occurrence per site-hour: camera detections next to acoustic detections.
cam_h = cam.dropna(subset=["hour"]).groupby(["campaign", "locationID", "hour"]).size().rename("camera_occurrences")
aru_h = aru.dropna(subset=["hour"]).groupby(["campaign", "locationID", "hour"]).size().rename("acoustic_occurrences")
joined = pd.concat([cam_h, aru_h], axis=1).fillna(0).astype(int)
both = joined[(joined.camera_occurrences > 0) & (joined.acoustic_occurrences > 0)]
print(f"site-hours with both modalities: {len(both):,} of {len(joined):,}")
print(both.reset_index().groupby("locationID").size().rename("site_hours_with_both").to_string())
