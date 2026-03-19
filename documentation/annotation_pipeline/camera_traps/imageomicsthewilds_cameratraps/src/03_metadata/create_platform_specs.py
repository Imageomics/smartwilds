"""
Create platform and sensor specifications for the camera trap deployment.

Documents hardware, sensor characteristics, and mission parameters
following FAIR² Drones standard for reproducibility and interoperability.
"""

import json
from pathlib import Path


def create_platform_specifications(output_path="platform_specifications.json"):
    """
    Generate comprehensive platform and sensor specifications.

    This follows FAIR² Drones standard Section 3 (Platform Specifications)
    and documents all cameras used across campaigns.
    """

    platform_specs = {
        "metadata": {
            "version": "1.0",
            "generated": "2026-03-17",
            "standard": "FAIR² Drones Data Standard",
            "description": "Camera trap platform specifications for The Wilds 2025 survey"
        },

        # Primary camera models used in the survey
        "platforms": {
            "Garde Pro T5NG": {
                "__description": "Primary camera model used in Aug 2025 campaign",
                "platform_type": "Stationary camera trap",
                "manufacturer": "Gardepro (assumed, name from field notes)",
                "model": "Garde Pro T5NG",
                "platform_category": "Passive Infrared (PIR) Triggered Camera Trap",

                "physical_specs": {
                    "weight_kg": "unknown",
                    "dimensions_cm": "unknown",
                    "power_source": "Battery (AA/AAA)",
                    "typical_deployment_duration_days": 7,
                    "weatherproof_rating": "IP65 (assumed)"
                },

                "sensors": {
                    "primary_camera": {
                        "type": "RGB (color)",
                        "sensor_type": "CMOS",
                        "resolution_mp": 4,
                        "resolution_pixels": [2560, 1920],
                        "sensor_size_inches": "1/3 (assumed)",
                        "focal_length_mm": "unknown",
                        "field_of_view_degrees": 55,  # Typical for trail cameras
                        "pixel_size_microns": "unknown",
                        "bit_depth": 8,
                        "color_space": "RGB",
                        "frame_rate_fps": 1  # Triggered, not continuous
                    },

                    "pir_sensor": {
                        "type": "Passive Infrared",
                        "sensitivity": "High",
                        "trigger_delay_seconds": 3,
                        "cooldown_between_triggers_seconds": "user configurable"
                    }
                },

                "recording_modes": {
                    "photo_mode": {
                        "enabled": True,
                        "resolution": "4MP or 3-photo burst",
                        "burst_photos": 3,
                        "storage": "JPEG format"
                    },
                    "video_mode": {
                        "enabled": False,
                        "note": "Disabled for this deployment"
                    },
                    "timelapse_mode": {
                        "enabled": True,
                        "interval_hours": 1,
                        "note": "1-hour interval timelapse enabled"
                    }
                },

                "timekeeping": {
                    "clock_type": "Internal RTC",
                    "accuracy_minutes_per_month": "±5,
                    "user_settable": True,
                    "timezone_support": "Yes - Eastern Time used",
                    "date_format": "Y/M/D (2-digit year)",
                    "time_format": "24-hour",
                    "known_issues": "See camera_deployment_metadata.py for known clock issues by deployment"
                },

                "dating": {
                    "timestamp_embedding": "Filename + image metadata",
                    "filename_format": "{cameraID}_{YYMMDDHHMMSS}_{sequence}.JPG",
                    "example_filename": "NSCF0002_250804120030_0001.JPG"
                },

                "storage": {
                    "storage_type": "SD Card (SDHC/SDXC)",
                    "typical_capacity_gb": 256,
                    "file_format": "JPEG images, JPG extension",
                    "typical_deployment_capacity_gb": 30  # Per deployment
                },

                "deployments_count": 6,  # Used in 6 deployments across campaigns
                "notes": "Configured with high PIR sensitivity for wildlife detection"
            },

            "Trail Camera G600": {
                "__description": "Alternative camera model used in TW06",
                "platform_type": "Stationary camera trap",
                "manufacturer": "Trail Camera (generic designation)",
                "model": "G600",

                "physical_specs": {
                    "weight_kg": "unknown",
                    "power_source": "Battery"
                },

                "sensors": {
                    "primary_camera": {
                        "type": "RGB",
                        "resolution_mp": "unknown",
                        "field_of_view_degrees": 55
                    },
                    "pir_sensor": {
                        "type": "Passive Infrared",
                        "sensitivity": "High"
                    }
                },

                "deployments_count": 1,
                "notes": "Limited deployment - battery remained at 100% (unusual)"
            },

            "Garde Pro A3": {
                "__description": "Hybrid camera with video and photo modes",
                "platform_type": "Stationary camera trap",
                "manufacturer": "Gardepro (assumed)",
                "model": "Garde Pro A3",

                "physical_specs": {
                    "weight_kg": "unknown",
                    "power_source": "Battery"
                },

                "sensors": {
                    "primary_camera": {
                        "type": "RGB",
                        "resolution_mp": 8,
                        "video_resolution": "1920x1080p",
                        "video_framerate_fps": 30,
                        "field_of_view_degrees": 55
                    }
                },

                "recording_modes": {
                    "photo_burst": "8MP, 3 photos in series",
                    "video": "1920x1080p, 10s clips with audio"
                },

                "deployments_count": 1,
                "notes": "More advanced model with video capability. No data after 2025-08-25 (equipment failure)"
            }
        },

        # Mission-level parameters applicable to all deployments
        "mission_parameters": {
            "campaign_1": {
                "deployment_period": "2025-06-30 to 2025-07-03",
                "total_cameras": 4,
                "total_camera_days": "~12",
                "sites": ["TW01", "TW02", "TW03", "TW04"],
                "total_images_approximate": "~20K",
                "common_configuration": {
                    "mode": "Photo only with timelapse",
                    "resolution": "4MP",
                    "pir_sensitivity": "High",
                    "timelapse_interval_hours": 1,
                    "timezone": "USA Eastern",
                    "date_format": "Y/M/D"
                }
            },

            "campaign_2": {
                "deployment_period": "2025-08-04 to 2025-08-28",
                "total_cameras": 9,
                "total_camera_days": "~186",  # 9 cameras * ~20-25 days avg
                "sites": ["TW01", "TW02", "TW04", "TW06", "TW07", "TW09", "TW11"],
                "total_images_approximate": "~222K",
                "common_configuration": {
                    "mode": "Photo + Video or Photo only",
                    "resolution": "4MP or 8MP (video-capable units)",
                    "pir_sensitivity": "High",
                    "timelapse_interval_hours": 1,
                    "timezone": "USA Eastern",
                    "date_format": "Y/M/D"
                },
                "known_issues": [
                    "TW02-CT01: Camera clock set incorrectly (initial Oct 31 2023, then Sept 2023)",
                    "TW04-CT03: Equipment failure after 2025-08-25",
                    "TW09_CT02: Battery failure 2025-08-18 to 2025-08-25",
                    "TW06-CT04: Unusual battery level (100% at retrieval)"
                ]
            }
        },

        # Standardized field-of-view and distance estimation parameters
        "geometric_calibration": {
            "typical_hfov_degrees": 52,
            "typical_target_height_meters": 1.0,  # White-tailed deer
            "typical_altitude_meters": "~1.5",  # Height cameras mounted on trees
            "distance_estimation_method": "bbox height ratio from typical animal height"
        },

        # GPS and coordinate information
        "geospatial": {
            "coordinate_system": "WGS84 (EPSG:4326)",
            "camera_gps_accuracy_meters": 5,
            "study_site": "The Wilds Wildlife Research Center, Ohio",
            "approximate_bounds": {
                "north_latitude": 39.51,
                "south_latitude": 39.49,
                "west_longitude": -81.45,
                "east_longitude": -81.43,
                "area_hectares": 150  # Approximate study area
            }
        },

        # Data format specifications
        "data_formats": {
            "images": {
                "format": "JPEG",
                "quality": "Unknown (default trail camera compression)",
                "color_space": "RGB",
                "embedded_metadata": {
                    "timestamp": "Burned into image via on-screen display (OSD)",
                    "camera_id": "Burned into image (e.g., NSCF0002)",
                    "exif": "Yes - embedded by camera"
                }
            },

            "temporal_metadata": {
                "filename_timestamp": "Embedded in filename ({YYMMDDHHMMSS})",
                "exif_datetime": "Embedded in EXIF metadata",
                "uncertainty_seconds": 1  # Camera timestamp precision
            }
        },

        # Operational specifications
        "operational": {
            "trigger_mechanism": "PIR (Passive Infrared)",
            "minimum_trigger_interval_seconds": 3,
            "moonlight_detection": "Infrared night vision (model dependent)",
            "temperature_operating_range_celsius": "-20 to 60",
            "weather_resistance": "Weatherproof design, suitable for field deployment",
            "mounting": "Tree mounting at ~1.5-2.0 meters height (typical)"
        },

        # Data quality considerations
        "data_quality": {
            "temporal_resolution": "Continuous trigger-based (PIR-driven) + hourly timelapse",
            "spatial_resolution": "Fixed camera location",
            "detection_bias": "Triggered by animal heat signature - may miss small or cold animals",
            "user_notes": "See camera_deployment_metadata.py for per-camera issues and corrections"
        }
    }

    # Write to JSON with nice formatting
    with open(output_path, 'w') as f:
        json.dump(platform_specs, f, indent=2)

    print(f"✓ Generated platform specifications: {output_path}")
    return platform_specs


if __name__ == "__main__":
    create_platform_specifications()
