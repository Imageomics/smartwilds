# Camera Trap Timestamp Validation

This module provides enhanced timestamp extraction for camera trap images with comprehensive validation and flagging for manual review.

## Overview

The original `make_events.py` extracts timestamps from filenames and EXIF data but doesn't validate them. The enhanced pipeline adds:

1. **Date Range Validation**: Ensures timestamps fall within known deployment periods
2. **Filename vs EXIF Cross-Check**: Detects disagreement between filename and EXIF timestamps
3. **Timestamp Corrections**: Applies corrections for cameras with known clock issues (e.g., TW02-CT01)
4. **Manual Review Flags**: Comprehensive flagging system to identify images needing verification

## Files

### `camera_deployment_metadata.py`
Central repository for deployment dates, date ranges, and known issues. Contains:
- Deployment/retrieval dates for each camera
- Known timestamp correction mappings
- Data gap information
- Helper functions for validation

Update this file when:
- New camera metadata is documented
- Known clock issues are discovered
- Date corrections are needed

### `make_events_validated.py`
Enhanced event extraction script. Improvements over original `make_events.py`:
- Applies timestamp corrections from metadata
- Validates timestamps against deployment date ranges
- Detects filename/EXIF disagreement
- Generates validation flags for manual review
- Provides detailed statistics on corrections and flags

## Known Issues Handled

### TW02-CT01 (August 2025 Campaign)
**Issue**: Camera clock was set incorrectly
- Initial dates: Oct 31, 2023 instead of Aug 4, 2025
- After manual adjustment: Sept 2023 instead of Aug 2025

**Correction Applied**: Date correction mapping in `camera_deployment_metadata.py`
- 10-31-23 → 08-04-25
- 11-01-23 → 08-05-25
- 09-07-23 → 08-07-25
- ... (etc for remaining dates)

### TW04-CT03 (August 2025 Campaign)
**Issue**: No data collected after 2025-08-25 (equipment failure)
**Flag**: Images after this date are flagged for review

### TW09_CT02 (August 2025 Campaign)
**Issue**: Data gap from 2025-08-18 to 2025-08-25 (battery died)
**Flag**: Gap is documented in metadata for reference during analysis

## Output Format

`events_validated.csv` includes:

| Column | Description |
|--------|-------------|
| timestamp | Final timestamp (corrected if needed) |
| site_cam | Camera identifier (e.g., TW02-CT01) |
| session | Deployment session |
| path | Full path to image file |
| timestamp_source | Source of timestamp: 'filename', 'exif', or 'corrected' |
| validation_flag | Reason for manual review (if any) |
| filename_timestamp | Original timestamp from filename (for reference) |
| exif_timestamp | Original timestamp from EXIF (for reference) |

## Validation Flags

Images are flagged with one or more of:
- **OUT_OF_RANGE**: Timestamp outside known deployment period
- **EXIF_MISMATCH**: Filename and EXIF timestamps disagree (>1 second difference)
- **CORRECTED**: Timestamp was adjusted due to known camera clock issue
- **AFTER_KNOWN_CUTOFF**: Image after documented equipment failure date

## Usage

```bash
# From the events directory
python make_events_validated.py
```

This requires:
1. `index.csv` (from `00_indexing/index_images.py`)
2. `camera_deployment_metadata.py` in the same directory

### Output
- `events_validated.csv` - Main timestamped events file
- Console output showing:
  - Total images processed
  - Count of corrections applied
  - Count of images flagged for review
  - Detailed list of all flagged images by camera

## Manual Review Process

Images flagged for review should be examined to verify:

1. **OUT_OF_RANGE**:
   - Check if deployment dates in metadata are correct
   - Verify camera clock was actually set to timestamp in image
   - Note any discrepancies for final metadata

2. **EXIF_MISMATCH**:
   - Compare filename vs image EXIF timestamp
   - Determine which is more reliable
   - Update metadata corrections if needed

3. **CORRECTED**:
   - Verify the applied correction matches actual deployment dates
   - Check that corrected timestamp makes sense temporally

4. **AFTER_KNOWN_CUTOFF**:
   - Verify equipment failure date
   - Check if any images actually exist after failure
   - Update metadata if date is incorrect

## Future Enhancements

Potential additions:
- GPS coordinate validation using deployment logs
- Image count analysis to detect clock resets/jumps
- Automatic gap detection during processing
- Integration with field deployment logs
- Statistical analysis of timestamp corrections applied

## Integration with Downstream Processing

The `events_validated.csv` output can be used with downstream components:
- Pass `validation_flag` column to detection pipeline for filtering
- Use flagged images as candidates for manual annotation review
- Generate detailed reports on data quality by camera/deployment
- Track systematic issues for future equipment selection/configuration
