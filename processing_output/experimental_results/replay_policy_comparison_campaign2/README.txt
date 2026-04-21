Assumptions
- Campaign 2 replay window is August 4, 2025 through August 28, 2025 inclusive.
- Camera replay trace uses raw camera-trap images whose filename timestamps are parseable and fall inside Campaign 2.
- Camera traps without recoverable event times are excluded from the replay trace rather than assigned invented timestamps.
- Included camera traps: TW01-CT02, TW02-CT01, TW09_CT02
- Excluded camera traps: TW04-CT03, TW06-CT04, TW06-CT05, TW07-CT05, TW09-CT05, TW11-CT06
- Camera capture events are clustered from images arriving within the configured cluster-gap window.
- Timelapse is inferred from dominant repeated cadence runs; non-timelapse clusters are treated as motion-like.
- Acoustic trigger threshold: max BirdNET confidence > 0.70
- Camera service time: 1.50s per image; camera cost: 1.00 units per image.
- Audio service time: 30.00s per hourly file; audio cost: 20.00 units per file.
- Adaptive policy enters elevated mode after 3 processed positive events in 1h and stays elevated for 1.0h.
- Adaptive policy batch-processes backlog after idle gaps > 2.0h.
- Coverage is computed over positive trace events; operator effort is proxied by processed event count.
- Latency SLO threshold: 300.0s

Timelapse Summary
- TW01-CT02: cadence=60, timelapse_clusters=7126, motion_clusters=1224
- TW02-CT01: cadence=60, timelapse_clusters=5737, motion_clusters=22
- TW09_CT02: cadence=60, timelapse_clusters=23521, motion_clusters=2112
