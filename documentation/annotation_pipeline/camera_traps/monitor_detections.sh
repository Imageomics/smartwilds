#!/bin/bash
# Monitor camera trap detection job progress
#
# Usage:
#   bash monitor_detections.sh              # Show status once
#   bash monitor_detections.sh --watch      # Refresh every 30 seconds
#   bash monitor_detections.sh --detail     # Show per-camera details

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESULTS_DIR="${SCRIPT_DIR}/detection_results"
LOGS_DIR="${SCRIPT_DIR}/logs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

show_status() {
    clear 2>/dev/null || true
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Camera Trap Detection Monitor  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    # SLURM job status
    echo -e "${CYAN}SLURM Jobs:${NC}"
    JOBS=$(squeue -u $USER -n ct-detect --format="%.8i %.4t %.10M %.6D %R" 2>/dev/null)
    if [ -z "$JOBS" ] || [ "$(echo "$JOBS" | wc -l)" -le 1 ]; then
        echo "  No active jobs"
    else
        echo "$JOBS" | head -20
    fi
    echo ""

    # Results summary
    echo -e "${CYAN}Detection Results:${NC}"
    echo -e "  $( printf '%-45s %10s %10s %s\n' 'Camera' 'Detections' 'Status' 'Size' )"
    echo "  $(printf '%0.s-' {1..80})"

    # Expected cameras (from the config)
    CAMERAS=(
        "TW01-CT02_20250630_20250703:10408"
        "TW01-CT02_20250804_20250828:26573"
        "TW02-CT01_20250804_20250828:61217"
        "TW02-CT03_20250630_20250703:55"
        "TW03-CT01_20250630_20250703:8867"
        "TW04-CT03_20250804_20250828:984"
        "TW04-CT04_20250630_20250703:684"
        "TW06-CT04_20250804_20250828:40907"
        "TW06-CT05_20250804_20250828:168"
        "TW09-CT05_20250804_20250828:15"
        "TW09_CT02_20250804_20250828:90834"
        "TW11-CT06_20250804_20250828:112"
    )

    TOTAL_DET=0
    DONE=0
    RUNNING=0
    PENDING=0

    for entry in "${CAMERAS[@]}"; do
        CAM_KEY="${entry%%:*}"
        EXPECTED="${entry##*:}"
        CSV="${RESULTS_DIR}/${CAM_KEY}_detections.csv"

        if [ -f "$CSV" ]; then
            DET_COUNT=$(tail -n +2 "$CSV" 2>/dev/null | wc -l)
            SIZE=$(du -h "$CSV" 2>/dev/null | cut -f1)
            TOTAL_DET=$((TOTAL_DET + DET_COUNT))
            DONE=$((DONE + 1))
            STATUS="${GREEN}DONE${NC}"
        else
            DET_COUNT="-"
            SIZE="-"
            # Check if there's an active SLURM task for this camera
            # Check log files for activity
            LOG_PATTERN="${LOGS_DIR}/ct-detect_*_*.out"
            ACTIVE_LOG=""
            for logfile in ${LOG_PATTERN}; do
                if [ -f "$logfile" ] && grep -q "$CAM_KEY" "$logfile" 2>/dev/null; then
                    # Check if the log is still being written to (modified in last 2 min)
                    if [ -n "$(find "$logfile" -mmin -2 2>/dev/null)" ]; then
                        ACTIVE_LOG="$logfile"
                    fi
                fi
            done

            if [ -n "$ACTIVE_LOG" ]; then
                STATUS="${YELLOW}RUNNING${NC}"
                RUNNING=$((RUNNING + 1))
                # Try to get progress from log
                LAST_LINE=$(tail -1 "$ACTIVE_LOG" 2>/dev/null)
                if echo "$LAST_LINE" | grep -qoP '\d+/\d+'; then
                    DET_COUNT="$(echo "$LAST_LINE" | grep -oP '\d+/\d+' | tail -1)"
                fi
            else
                STATUS="${RED}PENDING${NC}"
                PENDING=$((PENDING + 1))
            fi
        fi

        printf "  %-45s %10s ${STATUS}%10s %s\n" "$CAM_KEY" "$DET_COUNT" "" "$SIZE"
    done

    echo ""
    echo -e "${CYAN}Summary:${NC}"
    echo -e "  Completed: ${GREEN}${DONE}/12${NC} cameras"
    echo -e "  Running:   ${YELLOW}${RUNNING}${NC}"
    echo -e "  Pending:   ${RED}${PENDING}${NC}"
    echo -e "  Total detections so far: ${TOTAL_DET}"
    echo ""

    # Show recent log activity
    if [[ "$1" == "--detail" ]] || [[ "$2" == "--detail" ]]; then
        echo -e "${CYAN}Recent Log Activity:${NC}"
        LATEST_LOG=$(ls -t ${LOGS_DIR}/ct-detect_*.out 2>/dev/null | head -1)
        if [ -n "$LATEST_LOG" ]; then
            echo "  Latest: $LATEST_LOG"
            echo "  $(tail -5 "$LATEST_LOG" 2>/dev/null | sed 's/^/  /')"
        fi
        echo ""

        # Show any errors
        ERROR_COUNT=$(grep -l "ERROR\|FAILED\|Traceback" ${LOGS_DIR}/ct-detect_*.err 2>/dev/null | wc -l)
        if [ "$ERROR_COUNT" -gt 0 ]; then
            echo -e "  ${RED}Errors found in ${ERROR_COUNT} log file(s):${NC}"
            grep -l "ERROR\|FAILED\|Traceback" ${LOGS_DIR}/ct-detect_*.err 2>/dev/null | while read f; do
                echo "    $f"
                tail -3 "$f" | sed 's/^/      /'
            done
        fi
    fi

    # Disk usage
    if [ -d "$RESULTS_DIR" ]; then
        echo -e "${CYAN}Disk Usage:${NC}  $(du -sh "$RESULTS_DIR" 2>/dev/null | cut -f1) in ${RESULTS_DIR}"
    fi
}

# Main
if [[ "$1" == "--watch" ]]; then
    while true; do
        show_status "$@"
        echo ""
        echo -e "${BLUE}Refreshing in 30s... (Ctrl+C to stop)${NC}"
        sleep 30
    done
else
    show_status "$@"
fi
