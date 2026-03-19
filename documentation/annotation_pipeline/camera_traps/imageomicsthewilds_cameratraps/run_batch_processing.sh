#!/bin/bash

# Batch process camera trap data - convenient shell wrapper
#
# Usage:
#   ./run_batch_processing.sh --base-dir /path/to/TheWilds2025 --output results
#   ./run_batch_processing.sh --metadata-only (generates Events/Occurrences only)
#   ./run_batch_processing.sh --help
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BASE_DIR=""
OUTPUT_DIR="./camera_trap_results"
METADATA_ONLY=false
DETECTIONS_DIR=""
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Functions
print_help() {
    cat << EOF
${BLUE}Camera Trap Batch Processing${NC}

Usage: $0 [options]

${YELLOW}Options:${NC}
  --base-dir DIR          Base directory containing camera trap data
  --output-dir DIR        Output directory (default: ./camera_trap_results)
  --detections-dir DIR    Directory with detection results
  --metadata-only         Generate only Events/Occurrences (skip batch processing)
  --campaign PATTERN      Process only matching campaigns (e.g., '20250804*')
  --camera PATTERN        Process only matching cameras (e.g., 'TW02-*')
  --continue-from CAMERA  Resume from specific camera
  --help                  Show this help message

${YELLOW}Examples:${NC}
  # Complete workflow from images to metadata
  $0 --base-dir /path/to/TheWilds2025 --output-dir ./results

  # Quick metadata generation only
  $0 --metadata-only --base-dir /path/to/TheWilds2025

  # Process specific campaign
  $0 --base-dir /path/to/TheWilds2025 --campaign '20250804*'

  # Resume interrupted processing
  $0 --base-dir /path/to/TheWilds2025 --continue-from TW06-CT05

${YELLOW}Output Structure:${NC}
  results/
  ├── thewilds_20250630_20250703/
  │   ├── TW01-CT02/
  │   │   ├── index.csv
  │   │   ├── events_validated.csv
  │   │   └── darwin_core_*.csv
  │   └── ...
  ├── thewilds_20250804_20250828/
  │   └── ...
  └── processing_report.json

EOF
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-dir)
            BASE_DIR="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --detections-dir)
            DETECTIONS_DIR="$2"
            shift 2
            ;;
        --metadata-only)
            METADATA_ONLY=true
            shift
            ;;
        --help)
            print_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate inputs
if [ -z "$BASE_DIR" ]; then
    log_error "Missing required option: --base-dir"
    echo "Use --help for usage information"
    exit 1
fi

if [ ! -d "$BASE_DIR" ]; then
    log_error "Base directory not found: $BASE_DIR"
    exit 1
fi

# Header
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   Camera Trap Batch Processing"
echo "═══════════════════════════════════════════════════════════"
echo ""
log_info "Base directory: $BASE_DIR"
log_info "Output directory: $OUTPUT_DIR"
log_info "Metadata only: $METADATA_ONLY"
[ -n "$DETECTIONS_DIR" ] && log_info "Detections directory: $DETECTIONS_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Main processing
if [ "$METADATA_ONLY" = true ]; then
    log_info "Running metadata-only generation..."
    echo ""

    METADATA_CMD=(
        "python" "$SCRIPT_DIR/process_all_camera_traps.py"
        "--base-dir" "$BASE_DIR"
        "--output-dir" "$OUTPUT_DIR"
    )

    if [ -n "$DETECTIONS_DIR" ]; then
        METADATA_CMD+=(
            "--detections-dir" "$DETECTIONS_DIR"
        )
    fi

    if ! python "$SCRIPT_DIR/process_all_camera_traps.py" \
        --base-dir "$BASE_DIR" \
        --output-dir "$OUTPUT_DIR" \
        ${DETECTIONS_DIR:+--detections-dir "$DETECTIONS_DIR"}; then
        log_error "Metadata generation failed"
        exit 1
    fi

    log_success "Metadata generation complete"

else
    log_info "Running complete batch processing pipeline..."
    echo ""

    BATCH_CMD=(
        "python" "$SCRIPT_DIR/batch_process_camera_traps.py"
        "--base-dir" "$BASE_DIR"
        "--find-campaigns"
        "--output-dir" "$OUTPUT_DIR"
    )

    if ! "${BATCH_CMD[@]}"; then
        log_error "Batch processing failed"
        exit 1
    fi

    log_success "Batch processing complete"
fi

# Final summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   Processing Complete"
echo "═══════════════════════════════════════════════════════════"
echo ""
log_success "Output saved to: $OUTPUT_DIR"
echo ""

# Show what was generated
if [ -f "$OUTPUT_DIR/darwin_core_events.csv" ]; then
    EVENT_COUNT=$(tail -n +2 "$OUTPUT_DIR/darwin_core_events.csv" | wc -l)
    log_info "Generated $EVENT_COUNT Event records"
fi

if [ -f "$OUTPUT_DIR/darwin_core_occurrences.csv" ]; then
    OCC_COUNT=$(tail -n +2 "$OUTPUT_DIR/darwin_core_occurrences.csv" | wc -l)
    log_info "Generated $OCC_COUNT Occurrence records"
fi

if [ -f "$OUTPUT_DIR/processing_report.json" ]; then
    log_info "Processing report: $OUTPUT_DIR/processing_report.json"
fi

echo ""
log_info "Next steps:"
echo "  1. Review output CSVs in $OUTPUT_DIR"
echo "  2. Validate with GBIF tools"
echo "  3. Submit to GBIF or upload to Zenodo"
echo ""
