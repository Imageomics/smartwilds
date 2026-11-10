#!/bin/bash

# Setup output directory structure for camera trap processing
#
# Usage:
#   ./setup_output_directories.sh [--base-dir /path/to/TheWilds2025] [--output-root /custom/output/path]
#
# This script creates an organized directory structure for:
# - Annotated images (from camera detection)
# - Darwin Core metadata (Events, Occurrences, Platform specs)
# - Intermediate processing files
# - Validation reports
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
BASE_DIR=""
OUTPUT_ROOT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-dir)
            BASE_DIR="$2"
            shift 2
            ;;
        --output-root)
            OUTPUT_ROOT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Set defaults if not provided
if [ -z "$BASE_DIR" ]; then
    BASE_DIR="/fs/ess/PAS2136/TheWilds2025"
fi

if [ -z "$OUTPUT_ROOT" ]; then
    OUTPUT_ROOT="$BASE_DIR/processing_output"
fi

# Validate base directory
if [ ! -d "$BASE_DIR" ]; then
    echo -e "${RED}Error: Base directory not found: $BASE_DIR${NC}"
    exit 1
fi

# Header
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   Setting up Output Directory Structure"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}Base directory: ${NC}$BASE_DIR"
echo -e "${BLUE}Output root: ${NC}$OUTPUT_ROOT"
echo ""

# Create main directories
echo -e "${YELLOW}Creating main directories...${NC}"
mkdir -p "$OUTPUT_ROOT/annotated_images"
mkdir -p "$OUTPUT_ROOT/darwin_core_metadata"
mkdir -p "$OUTPUT_ROOT/intermediate_processing"
mkdir -p "$OUTPUT_ROOT/validation_reports"
echo -e "${GREEN}✓ Main directories created${NC}"

# Campaign directories
campaigns=("20250630_20250703" "20250804_20250828")

for campaign in "${campaigns[@]}"; do
    echo ""
    echo -e "${YELLOW}Setting up campaign: $campaign${NC}"

    mkdir -p "$OUTPUT_ROOT/annotated_images/$campaign"
    mkdir -p "$OUTPUT_ROOT/darwin_core_metadata/$campaign"
    mkdir -p "$OUTPUT_ROOT/intermediate_processing/$campaign"

    echo -e "${GREEN}✓ Campaign directories created${NC}"
done

# Per-camera directories for June campaign
echo ""
echo -e "${YELLOW}Setting up June deployment cameras (20250630_20250703)...${NC}"
june_cameras=("TW01-CT02" "TW02-CT03" "TW03-CT01" "TW04-CT04")

for camera in "${june_cameras[@]}"; do
    mkdir -p "$OUTPUT_ROOT/annotated_images/20250630_20250703/$camera"
    mkdir -p "$OUTPUT_ROOT/intermediate_processing/20250630_20250703/$camera"
done

echo -e "${GREEN}✓ Created ${#june_cameras[@]} camera directories for June campaign${NC}"

# Per-camera directories for August campaign
echo ""
echo -e "${YELLOW}Setting up August deployment cameras (20250804_20250828)...${NC}"
august_cameras=("TW01-CT02" "TW02-CT01" "TW04-CT03" "TW06-CT04" "TW06-CT05" "TW07-CT05" "TW09_CT02" "TW09-CT05" "TW11-CT06")

for camera in "${august_cameras[@]}"; do
    mkdir -p "$OUTPUT_ROOT/annotated_images/20250804_20250828/$camera"
    mkdir -p "$OUTPUT_ROOT/intermediate_processing/20250804_20250828/$camera"
done

echo -e "${GREEN}✓ Created ${#august_cameras[@]} camera directories for August campaign${NC}"

# Create directory structure summary file
echo ""
echo -e "${YELLOW}Creating directory inventory file...${NC}"

cat > "$OUTPUT_ROOT/.structure_manifest.txt" << 'EOF'
Camera Trap Processing Output Directory Structure
Generated: $(date)

Directory Organization:
=======================

annotated_images/
  ├── 20250630_20250703/     [June deployment]
  │   ├── TW01-CT02/
  │   ├── TW02-CT03/
  │   ├── TW03-CT01/
  │   └── TW04-CT04/
  │
  └── 20250804_20250828/     [August deployment]
      ├── TW01-CT02/
      ├── TW02-CT01/
      ├── TW04-CT03/
      ├── TW06-CT04/
      ├── TW06-CT05/
      ├── TW07-CT05/
      ├── TW09_CT02/
      ├── TW09-CT05/
      └── TW11-CT06/

darwin_core_metadata/
  ├── 20250630_20250703/
  │   ├── darwin_core_events.csv
  │   ├── darwin_core_occurrences.csv
  │   ├── platform_specifications.json
  │   └── processing_report.json
  │
  └── 20250804_20250828/
      ├── darwin_core_events.csv
      ├── darwin_core_occurrences.csv
      ├── platform_specifications.json
      └── processing_report.json

intermediate_processing/
  ├── 20250630_20250703/
  │   ├── TW01-CT02/
  │   ├── TW02-CT03/
  │   ├── TW03-CT01/
  │   └── TW04-CT04/
  │
  └── 20250804_20250828/
      ├── TW01-CT02/
      ├── TW02-CT01/
      ├── TW04-CT03/
      ├── TW06-CT04/
      ├── TW06-CT05/
      ├── TW07-CT05/
      ├── TW09_CT02/
      ├── TW09-CT05/
      └── TW11-CT06/

validation_reports/
  ├── timestamp_validation_report.csv
  ├── detection_quality_metrics.json
  ├── missing_coordinates_report.csv
  └── processing_errors.log

Total deployments: 13
Total campaigns: 2
  - 20250630_20250703: 4 cameras
  - 20250804_20250828: 9 cameras

To understand the full directory structure, see:
  OUTPUT_DIRECTORY_STRUCTURE.md
EOF

echo -e "${GREEN}✓ Directory inventory created${NC}"

# Set permissions
echo ""
echo -e "${YELLOW}Setting permissions...${NC}"
find "$OUTPUT_ROOT" -type d -exec chmod 755 {} \;
echo -e "${GREEN}✓ Permissions set${NC}"

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Directory setup complete!${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Count directories created
annot_dirs=$(find "$OUTPUT_ROOT/annotated_images" -type d | wc -l)
darwin_dirs=$(find "$OUTPUT_ROOT/darwin_core_metadata" -type d | wc -l)
inter_dirs=$(find "$OUTPUT_ROOT/intermediate_processing" -type d | wc -l)

echo -e "${BLUE}Summary:${NC}"
echo "  Annotated image directories: $annot_dirs"
echo "  Darwin Core metadata directories: $darwin_dirs"
echo "  Intermediate processing directories: $inter_dirs"
echo ""

echo -e "${BLUE}Output root: ${NC}$OUTPUT_ROOT"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Run detection pipeline:"
echo "     python camera_trap_detections.py --annotated-dir $OUTPUT_ROOT/annotated_images/..."
echo ""
echo "  2. Run timestamp validation:"
echo "     python make_events_validated.py --output $OUTPUT_ROOT/intermediate_processing/..."
echo ""
echo "  3. Generate Darwin Core metadata:"
echo "     python process_all_camera_traps.py --output-dir $OUTPUT_ROOT/darwin_core_metadata/..."
echo ""
echo "  See OUTPUT_DIRECTORY_STRUCTURE.md for detailed workflow"
echo ""
