#!/bin/bash

set -euo pipefail

BASE_OUTPUT_ROOT="${BASE_OUTPUT_ROOT:-/fs/scratch/PAS2136/smartwilds_detection}"
CHUNK_SUMMARY_JSON="${CHUNK_SUMMARY_JSON:-$BASE_OUTPUT_ROOT/camera_trap_sam3_chunk_summary.json}"
RUN_SCRIPT="${RUN_SCRIPT:-/fs/ess/PAS2699/object_detection_datasets/smartwilds/sam3_predictor_hf/run_predict_sam3_text.sh}"
LOG_ROOT="${LOG_ROOT:-$BASE_OUTPUT_ROOT/slurm_logs}"
OVERWRITE="${OVERWRITE:-0}"
DRY_RUN="${DRY_RUN:-0}"
TIME_LIMIT="${TIME_LIMIT:-01:00:00}"

mkdir -p "$LOG_ROOT"

submitted=0
skipped=0

if [[ ! -f "$CHUNK_SUMMARY_JSON" ]]; then
    echo "Missing chunk summary JSON: $CHUNK_SUMMARY_JSON" >&2
    exit 1
fi

while IFS=$'\t' read -r collection camera_trap chunk_index image_count image_root coco_json output_json viz_dir; do
    if [[ ! -d "$image_root" ]]; then
        echo "Skipping missing image root: $image_root"
        skipped=$((skipped + 1))
        continue
    fi

    if [[ ! -f "$coco_json" ]]; then
        echo "Skipping missing COCO JSON: $coco_json"
        skipped=$((skipped + 1))
        continue
    fi

    if [[ -f "$output_json" && "$OVERWRITE" != "1" ]]; then
        echo "Skipping existing prediction output: $output_json"
        skipped=$((skipped + 1))
        continue
    fi

    mkdir -p "$(dirname "$output_json")"

    job_name="hf_sam3_ct_${collection}_${camera_trap}_${chunk_index}"
    job_name="$(printf '%s' "$job_name" | tr -c '[:alnum:]_-' '_' | cut -c 1-128)"
    log_path="$LOG_ROOT/${job_name}_%j.txt"
    existing_job_ids="$(squeue -h -u "$USER" -n "$job_name" -o %A 2>/dev/null || true)"

    if [[ -n "$existing_job_ids" ]]; then
        echo "Skipping already queued job: $job_name ($existing_job_ids)"
        skipped=$((skipped + 1))
        continue
    fi

    submit_cmd=(
        sbatch
        --time "$TIME_LIMIT"
        --job-name "$job_name"
        --output "$log_path"
        --export "ALL,IMAGE_PATH=$image_root,COCO_JSON=$coco_json,IMAGE_ROOT=$image_root,OUTPUT_JSON=$output_json,VIZ_DIR=$viz_dir"
        "$RUN_SCRIPT"
    )

    echo "Submitting $job_name ($image_count images)"

    if [[ "$DRY_RUN" == "1" ]]; then
        printf 'DRY RUN:'
        printf ' %q' "${submit_cmd[@]}"
        printf '\n'
    else
        "${submit_cmd[@]}"
    fi

    submitted=$((submitted + 1))
done < <(
    jq -r '.[] | [.collection, .camera_trap, .chunk_index, .image_count, .image_root, .coco_json, .output_json, .viz_dir] | @tsv' "$CHUNK_SUMMARY_JSON"
)

echo "Finished camera-trap chunk submission pass. submitted=$submitted skipped=$skipped dry_run=$DRY_RUN"
