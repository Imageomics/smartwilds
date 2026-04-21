# path_config.py
from pathlib import Path

# ===== OSC shared dataset =====
DATA_ROOT = Path("/fs/ess/PAS2136/TheWilds2025")

# Campaign directories
CAMPAIGN1_ROOT = DATA_ROOT / "thewilds_20250630_20250703"
CAMPAIGN2_ROOT = DATA_ROOT / "thewilds_20250804_20250828"
CAMPAIGN3_ROOT = DATA_ROOT / "thewilds_20250908_20250908"

# Raw data
CAMERA_TRAP_ROOT = CAMPAIGN2_ROOT / "camera_traps"
DRONE_ROOT = CAMPAIGN2_ROOT / "drones"
BIOACOUSTIC_ROOT = DATA_ROOT / "BioacousticAnalysis"
PRACTICE_ROOT = DATA_ROOT / "practice"

# Existing processed outputs in shared dataset
PROCESSING_ROOT = DATA_ROOT / "processing_output"

ARRIVAL_RATE_ROOT = PROCESSING_ROOT / "experimental_results" / "cross_modal_arrival_rates" / "results"
REPLAY_ROOT = PROCESSING_ROOT / "experimental_results" / "replay_policy_comparison_campaign2"
CORRELATION_ROOT = PROCESSING_ROOT / "experimental_results" / "cross_modal_event_correlation"
DETECTIONS_ROOT = PROCESSING_ROOT / "detections"
DARWIN_CORE_ROOT = PROCESSING_ROOT / "darwin_core"

# Existing CSVs you may want to reuse
TIMESTAMPS_CAMERA_TRAP_CSV = ARRIVAL_RATE_ROOT / "timestamps_camera_trap.csv"
TIMESTAMPS_DRONE_CSV = ARRIVAL_RATE_ROOT / "timestamps_drone.csv"
CAMERA_TRACE_EVENTS_CSV = REPLAY_ROOT / "camera_trace_events.csv"
CAMERA_TIMELAPSE_SUMMARY_CSV = REPLAY_ROOT / "camera_timelapse_summary.csv"

# ===== Your own writable workspace on OSC =====
USER_ROOT = Path("/users/PAS2136/yuanyang")
WORK_ROOT = USER_ROOT / "wilds_work"
SCRIPTS_ROOT = WORK_ROOT / "scripts"
OUTPUTS_ROOT = WORK_ROOT / "outputs"
LOGS_ROOT = WORK_ROOT / "logs"
TMP_ROOT = WORK_ROOT / "tmp"

# Outputs for your current project
EXP3_ROOT = OUTPUTS_ROOT / "exp3_resource_model"
EXP4_ROOT = OUTPUTS_ROOT / "exp4_replay"

EXP3_TABLE_CSV = EXP3_ROOT / "resource_model_summary.csv"
EXP3_POLICY_CSV = EXP3_ROOT / "policy_comparison.csv"

DRONE_TRACE_CAMPAIGN2_CSV = EXP4_ROOT / "drone_trace_campaign2.csv"
CAMERA_TRACE_CAMPAIGN2_CSV = EXP4_ROOT / "camera_trace_campaign2.csv"
MULTIMODAL_REPLAY_INPUT_CSV = EXP4_ROOT / "multimodal_replay_input_campaign2.csv"
REPLAY_RESULTS_CSV = EXP4_ROOT / "replay_results_campaign2.csv"

def ensure_output_dirs() -> None:
    for p in [
        WORK_ROOT, SCRIPTS_ROOT, OUTPUTS_ROOT, LOGS_ROOT, TMP_ROOT,
        EXP3_ROOT, EXP4_ROOT
    ]:
        p.mkdir(parents=True, exist_ok=True)