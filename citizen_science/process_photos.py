#!/usr/bin/env python3
"""
Process citizen science photos from The Wilds with their JSON metadata.
Extracts photo information including timestamps, GPS coordinates, and prepares
data for wildlife detection and species identification.
"""

import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Dict, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_matching_json(image_path: Path) -> Optional[Path]:
    """
    Find the corresponding JSON file for an image.
    Google Takeout creates JSON files with various naming patterns.
    """
    # Try common patterns
    possible_json_paths = [
        image_path.with_suffix('.json'),
        image_path.parent / f"{image_path.stem}.json",
        image_path.parent / f"{image_path.name}.json",
    ]

    # Also try with additional extensions (Google Takeout quirk)
    for ext in ['.j.json', '..json']:
        possible_json_paths.append(
            image_path.parent / f"{image_path.stem}{ext}"
        )

    for json_path in possible_json_paths:
        if json_path.exists():
            return json_path

    return None


def extract_json_metadata(json_path: Path) -> Dict:
    """
    Extract metadata from Google Takeout JSON file.
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        metadata = {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
        }

        # Extract photo taken time
        if 'photoTakenTime' in data and 'timestamp' in data['photoTakenTime']:
            timestamp = int(data['photoTakenTime']['timestamp'])
            metadata['datetime_taken'] = datetime.fromtimestamp(timestamp)
        else:
            metadata['datetime_taken'] = None

        # Extract GPS coordinates
        geo_data = data.get('geoData', {})
        metadata['latitude'] = geo_data.get('latitude', 0.0)
        metadata['longitude'] = geo_data.get('longitude', 0.0)
        metadata['altitude'] = geo_data.get('altitude', 0.0)

        # Check if GPS data is valid (Google sets 0.0 if no GPS data)
        if metadata['latitude'] == 0.0 and metadata['longitude'] == 0.0:
            metadata['has_gps'] = False
        else:
            metadata['has_gps'] = True

        return metadata

    except Exception as e:
        logger.error(f"Error reading {json_path}: {e}")
        return {}


def extract_exif_gps(image_path: Path) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract GPS coordinates from image EXIF data as fallback.
    """
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()

        if not exif_data:
            return None, None

        gps_info = {}
        for tag, value in exif_data.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for gps_tag in value:
                    sub_decoded = GPSTAGS.get(gps_tag, gps_tag)
                    gps_info[sub_decoded] = value[gps_tag]

        if not gps_info:
            return None, None

        # Convert GPS coordinates to decimal degrees
        def convert_to_degrees(value):
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)

        lat = lon = None
        if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
            lat = convert_to_degrees(gps_info['GPSLatitude'])
            if gps_info['GPSLatitudeRef'] == 'S':
                lat = -lat

        if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
            lon = convert_to_degrees(gps_info['GPSLongitude'])
            if gps_info['GPSLongitudeRef'] == 'W':
                lon = -lon

        return lat, lon

    except Exception as e:
        logger.debug(f"Could not extract EXIF GPS from {image_path}: {e}")
        return None, None


def get_image_dimensions(image_path: Path) -> Tuple[int, int]:
    """
    Get image width and height.
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting dimensions for {image_path}: {e}")
        return 0, 0


def process_photo_folder(
    folder_path: str,
    output_csv: str = "photo_metadata.csv",
    image_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.heic')
) -> pd.DataFrame:
    """
    Process all photos in a folder and extract metadata.

    Args:
        folder_path: Path to folder containing images and JSON files
        output_csv: Path to save the CSV output
        image_extensions: Tuple of valid image extensions to process

    Returns:
        DataFrame containing all photo metadata
    """
    folder = Path(folder_path)

    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")

    logger.info(f"Processing photos in: {folder}")

    # Get all image files
    image_files = []
    for ext in image_extensions:
        image_files.extend(folder.glob(f"*{ext}"))
        image_files.extend(folder.glob(f"*{ext.upper()}"))

    logger.info(f"Found {len(image_files)} image files")

    results = []

    for image_path in image_files:
        logger.info(f"Processing: {image_path.name}")

        record = {
            'filename': image_path.name,
            'file_path': str(image_path),
            'file_size_mb': image_path.stat().st_size / (1024 * 1024),
        }

        # Get image dimensions
        width, height = get_image_dimensions(image_path)
        record['width'] = width
        record['height'] = height

        # Find and process JSON metadata
        json_path = find_matching_json(image_path)
        if json_path:
            record['has_json'] = True
            metadata = extract_json_metadata(json_path)
            record.update({
                'datetime_taken': metadata.get('datetime_taken'),
                'latitude': metadata.get('latitude'),
                'longitude': metadata.get('longitude'),
                'altitude': metadata.get('altitude'),
                'has_gps': metadata.get('has_gps', False),
                'title': metadata.get('title', ''),
                'description': metadata.get('description', ''),
            })

            # If JSON doesn't have GPS, try EXIF
            if not record['has_gps']:
                exif_lat, exif_lon = extract_exif_gps(image_path)
                if exif_lat is not None and exif_lon is not None:
                    record['latitude'] = exif_lat
                    record['longitude'] = exif_lon
                    record['has_gps'] = True
                    record['gps_source'] = 'exif'
                else:
                    record['gps_source'] = None
            else:
                record['gps_source'] = 'json'
        else:
            record['has_json'] = False
            record['datetime_taken'] = None
            record['latitude'] = None
            record['longitude'] = None
            record['altitude'] = None
            record['has_gps'] = False
            record['gps_source'] = None

            # Try EXIF for photos without JSON
            exif_lat, exif_lon = extract_exif_gps(image_path)
            if exif_lat is not None and exif_lon is not None:
                record['latitude'] = exif_lat
                record['longitude'] = exif_lon
                record['has_gps'] = True
                record['gps_source'] = 'exif'

        results.append(record)

    # Create DataFrame
    df = pd.DataFrame(results)

    # Sort by datetime if available
    if 'datetime_taken' in df.columns:
        df = df.sort_values('datetime_taken', na_position='last')

    # Save to CSV
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved metadata to: {output_csv}")

    # Print summary statistics
    logger.info("\n=== Processing Summary ===")
    logger.info(f"Total photos: {len(df)}")
    logger.info(f"Photos with JSON metadata: {df['has_json'].sum()}")
    logger.info(f"Photos with GPS coordinates: {df['has_gps'].sum()}")
    logger.info(f"Photos with datetime: {df['datetime_taken'].notna().sum()}")

    if df['has_gps'].sum() > 0:
        logger.info(f"\nGPS Sources:")
        logger.info(f"  From JSON: {(df['gps_source'] == 'json').sum()}")
        logger.info(f"  From EXIF: {(df['gps_source'] == 'exif').sum()}")

    return df


def main():
    """
    Main entry point for the script.
    """
    # Configuration
    input_folder = "/Users/kline.377/Downloads/Takeout/Google Photos/The Wilds Summer 2025 Fieldwork"
    output_csv = "/Users/kline.377/wilds_multimodal_data/photo_metadata.csv"

    # Process photos
    df = process_photo_folder(input_folder, output_csv)

    logger.info("\nFirst few rows:")
    print(df.head())

    logger.info("\nDataFrame info:")
    print(df.info())


if __name__ == "__main__":
    main()
