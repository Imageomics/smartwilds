from __future__ import annotations

from pathlib import Path
import pandas as pd

INPUT = Path("outputs/tables/arrivals/drone_trace_campaign2.csv")
OUTPUT = Path("outputs/tables/arrivals/drone_arrival_summary.csv")

CAMPAIGN2_START = pd.Timestamp("2025-08-04 00:00:00")
CAMPAIGN2_END = pd.Timestamp("2025-08-28 23:59:59")


def main() -> None:
    df = pd.read_csv(INPUT)
    df["arrival_dt"] = pd.to_datetime(df["arrival_dt"], errors="coerce")
    df = df.dropna(subset=["arrival_dt"]).copy()

    total_hours = (CAMPAIGN2_END - CAMPAIGN2_START).total_seconds() / 3600.0
    total_events = int(len(df))

    avg_rate_per_hour = total_events / total_hours if total_hours > 0 else 0.0
    avg_rate_per_sec = avg_rate_per_hour / 3600.0

    daily_counts = (
        df.assign(day=df["arrival_dt"].dt.floor("D"))
          .groupby("day")
          .size()
          .rename("daily_events")
          .reset_index()
    )

    if len(daily_counts) > 0:
        p95_daily = float(daily_counts["daily_events"].quantile(0.95))
        peak_daily = int(daily_counts["daily_events"].max())
    else:
        p95_daily = 0.0
        peak_daily = 0

    # convert daily counts to per-hour equivalents over a 24h day
    p95_rate_per_hour = p95_daily / 24.0
    peak_rate_per_hour = peak_daily / 24.0
    p95_rate_per_sec = p95_rate_per_hour / 3600.0
    peak_rate_per_sec = peak_rate_per_hour / 3600.0

    out = pd.DataFrame([{
        "sensor_group": "drone_campaign2",
        "total_events": total_events,
        "campaign_start": CAMPAIGN2_START,
        "campaign_end": CAMPAIGN2_END,
        "total_hours": total_hours,
        "active_days": int(len(daily_counts)),
        "avg_rate_per_hour": avg_rate_per_hour,
        "p95_rate_per_hour": p95_rate_per_hour,
        "peak_rate_per_hour": peak_rate_per_hour,
        "avg_rate_per_sec": avg_rate_per_sec,
        "p95_rate_per_sec": p95_rate_per_sec,
        "peak_rate_per_sec": peak_rate_per_sec,
    }])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False)

    print(f"Saved drone arrival summary: {OUTPUT}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
