"""
Create multi-modal platform and sensor specifications for The Wilds 2025.

Documents hardware, sensor characteristics, and mission parameters
for all 4 modalities (Camera Traps, Bioacoustics, Drones, Citizen Science)
following FAIR² Drones standard for reproducibility and interoperability.

Output: Single unified JSON file documenting all 4 modality platforms.
"""

import json
from pathlib import Path


def create_platform_specifications(output_path="platform_specifications_all_modalities.json", include_modalities=None):
    """
    Generate comprehensive multi-modal platform and sensor specifications.

    Parameters:
    -----------
    output_path : str
        Path to output JSON file
    include_modalities : list, optional
        List of modalities to include. Default: all 4 modalities
        Options: "camera_traps", "bioacoustics", "drones", "citizen_science"
    """

    if include_modalities is None:
        include_modalities = ["camera_traps", "bioacoustics", "drones", "citizen_science"]

    platform_specs = {
        "metadata": {
            "version": "2.0-multimodal",
            "generated": "2026-03-17",
            "standard": "FAIR² Drones Data Standard + Darwin Core Extension",
            "description": "Multi-modal platform specifications for The Wilds 2025 biodiversity survey",
            "modalities_included": include_modalities,
            "study": "The Wilds 2025 Biodiversity Survey",
            "location": "The Wilds Conservation Center, Southeastern Ohio, USA"
        },

        "platforms": {}
    }

    # CAMERA TRAPS
    if "camera_traps" in include_modalities:
        platform_specs["platforms"]["camera_traps"] = {
            "__description": "4 camera trap models deployed in 13 locations across 2 campaigns",

            "Garde_Pro_T5NG": {
                "platform_type": "stationary_camera_trap",
                "category": "Passive Infrared (PIR) Triggered Camera Trap",
                "manufacturer": "Gardepro",
                "model": "Garde Pro T5NG",

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
                        "field_of_view_degrees": 55,
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
                    "timelapse_mode": {
                        "enabled": True,
                        "interval_hours": 1
                    }
                },

                "deployments": ["TW01-CT02", "TW02-CT01", "TW09-CT02"],
                "deployments_count": 3,
                "notes": "Configured with high PIR sensitivity for wildlife detection"
            },

            "Trail_Camera_G600": {
                "platform_type": "stationary_camera_trap",
                "manufacturer": "Trail Camera",
                "model": "G600",

                "sensors": {
                    "primary_camera": {
                        "type": "RGB",
                        "resolution_mp": 8,
                        "field_of_view_degrees": 55,
                        "video_capable": True
                    },
                    "pir_sensor": {
                        "type": "Passive Infrared",
                        "sensitivity": "High"
                    }
                },

                "deployments": ["TW06-CT04"],
                "deployments_count": 1,
                "notes": "Motion detection capable. Battery remained at 100% (unusual)."
            },

            "Garde_Pro_A3": {
                "platform_type": "stationary_camera_trap",
                "manufacturer": "Gardepro",
                "model": "Garde Pro A3",

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

                "deployments": ["TW04-CT03"],
                "deployments_count": 1,
                "notes": "Advanced model with video capability. No data after 2025-08-25 (equipment failure)."
            },

            "Reveal_Pro_3_0": {
                "platform_type": "stationary_camera_trap",
                "category": "Smart Camera Trap with Video",
                "manufacturer": "Reveal",
                "model": "Reveal Pro 3.0",

                "sensors": {
                    "primary_camera": {
                        "type": "RGB",
                        "resolution_photos_4k": True,
                        "video_resolution_options": ["720p", "1080p"],
                        "video_framerate_fps": [30, 15],
                        "field_of_view_degrees": 55
                    }
                },

                "recording_modes": {
                    "photo": "4K resolution",
                    "video": "720p-1080p, 10-15s clips"
                },

                "deployments": ["TW06-CT05", "TW09-CT05", "TW11-CT06"],
                "deployments_count": 3,
                "notes": "Latest model with 4K photo and video capability. Deployed late in survey (Aug 25-28 for TW06-CT05)"
            },

            "mission_parameters": {
                "campaign_1": {
                    "deployment_period": "2025-06-30 to 2025-07-03",
                    "total_cameras": 4,
                    "total_images_approximate": "~20K"
                },
                "campaign_2": {
                    "deployment_period": "2025-08-04 to 2025-08-28",
                    "total_cameras": 9,
                    "total_images_approximate": "~222K"
                }
            }
        }

    # BIOACOUSTICS
    if "bioacoustics" in include_modalities:
        platform_specs["platforms"]["bioacoustics"] = {
            "__description": "Wildlife Acoustics Song Meter 4 recorders deployed at 6 locations",

            "Wildlife_Acoustics_Song_Meter_4": {
                "platform_type": "stationary_acoustic_recorder",
                "category": "Stationary Sound Recording",
                "manufacturer": "Wildlife Acoustics",
                "model": "Song Meter 4",

                "sensors": {
                    "microphone": {
                        "type": "microphone_array",
                        "frequency_response_hz": [200, 12000],
                        "sensitivity_dbv_pa": -35,
                        "sample_rate_hz": 48000,
                        "bit_depth": 16,
                        "file_format": "WAV",
                        "channels": 1
                    },
                    "gps": {
                        "type": "built_in_gps",
                        "accuracy_m": 5,
                        "logging_interval": "continuous"
                    },
                    "power_monitoring": {
                        "battery_voltage_logging": "continuous",
                        "sd_card_storage_monitoring": "per_minute_resolution"
                    }
                },

                "recording_hardware": {
                    "storage_type": "SD card (SDHC/SDXC)",
                    "power_source": "battery"
                },

                "deployments": 6,
                "deployment_details": {
                    "TW02_SM04": {
                        "site_id": "TW02-SM04",
                        "location": "Nomad Ridge Shelter, right side",
                        "gps": [39.82957, -81.73295],
                        "deploy_date": "2025-08-04",
                        "retrieve_date": "2025-08-28",
                        "recording_schedule": "5 minutes every hour",
                        "deployment_days": 24,
                        "total_wav_files": 659,
                        "total_data_gb": 26.06
                    },
                    "TW05_SM06": {
                        "site_id": "TW05-SM06",
                        "location": "Lake Trail Gate O",
                        "gps": [39.82866, -81.73758],
                        "deploy_date": "2025-08-04",
                        "retrieve_date": "2025-08-28",
                        "recording_schedule": "Sunrise to sunset recording",
                        "deployment_days": 24,
                        "total_wav_files": 100,
                        "total_data_gb": 16.62
                    },
                    "TW06_SM05": {
                        "site_id": "TW06-SM05",
                        "location": "Zebra Shelter",
                        "gps": [39.82870, -81.73756],
                        "deploy_date": "2025-08-04",
                        "retrieve_date": "2025-08-28",
                        "recording_schedule": "15 minutes every hour",
                        "deployment_days": 24,
                        "total_wav_files": 508,
                        "total_data_gb": 21.82
                    },
                    "TW07_SM02": {
                        "site_id": "TW07-SM02",
                        "location": "Zipline Tower",
                        "gps": [39.82891, -81.74392],
                        "deploy_date": "2025-08-04",
                        "retrieve_date": "2025-08-28",
                        "recording_schedule": "Sunrise to sunset recording",
                        "deployment_days": 24,
                        "total_wav_files": 339,
                        "total_data_gb": 56.44
                    },
                    "TW08_SM03": {
                        "site_id": "TW08-SM03",
                        "location": "Fence with Vegetation",
                        "gps": [39.82892, -81.74392],
                        "deploy_date": "2025-08-04",
                        "retrieve_date": "2025-08-28",
                        "recording_schedule": "Sunrise to sunset recording",
                        "deployment_days": 24,
                        "total_wav_files": 341,
                        "total_data_gb": 56.69
                    },
                    "TW09_SM01": {
                        "site_id": "TW09-SM01",
                        "location": "Dock, left side",
                        "gps": [39.83418, -81.73783],
                        "deploy_date": "2025-08-14",
                        "retrieve_date": "2025-08-28",
                        "recording_schedule": "Sunrise to sunset recording",
                        "deployment_days": 14,
                        "total_wav_files": 195,
                        "total_data_gb": 32.38,
                        "note": "Deployed 10 days later than other sites"
                    }
                },

                "data_format": {
                    "filename_pattern": "SMXXX_YYYYMMDD_HHMMSS.wav",
                    "example_filename": "SM004_20250805_050000.wav",
                    "sensor_health_logs": "SM*_Summary.txt (DATE, TIME, LAT, NS, LON, EW, POWER(V), #FILES at 1-min resolution)"
                },

                "total_deployments": 6,
                "total_wav_files": 2142,
                "total_data_gb": 209.01,
                "notes": "All recordings processed with BirdCLIP v2 automated species classifier. Existing annotations in Darwin Core rectification format."
            }
        }

    # DRONES
    if "drones" in include_modalities:
        platform_specs["platforms"]["drones"] = {
            "__description": "2 drone platforms with 8 flight missions (5 with video, 3 metadata-only)",

            "DJI_Mavic": {
                "platform_type": "quadcopter_aerial_survey",
                "category": "Quadcopter Aerial Survey",
                "manufacturer": "DJI",
                "model": "Mavic (model identification TBD)",

                "sensors": {
                    "camera": {
                        "type": "RGB video",
                        "resolution_mp": "unknown",
                        "frame_rate_fps": 30,
                        "video_formats": ["MOV"]
                    },
                    "gps": {
                        "accuracy_m": 2,
                        "update_rate_hz": 10,
                        "reference_system": "WGS84"
                    }
                },

                "telemetry": {
                    "format": "CSV",
                    "fields": ["count (10Hz)", "latitude", "longitude", "batteryPercent"],
                    "update_rate_hz": 10
                },

                "flights": 1,
                "flight_details": {
                    "20250811_DJI_01": {
                        "flight_id": "20250811_DJI_01",
                        "date": "2025-08-11",
                        "location_gps": [39.834171, -81.737820],
                        "video_files": 2,
                        "video_format": "MOV",
                        "metadata_format": "CSV (10Hz telemetry)",
                        "status": "READY"
                    }
                }
            },

            "Parrot_Anafi_4K": {
                "platform_type": "quadcopter_aerial_survey",
                "category": "Quadcopter Aerial Survey",
                "manufacturer": "Parrot",
                "model": "Anafi 4K",
                "aircraft_serial_number": "PI040416BA8H083200",
                "firmware_version": "1.8.2",

                "sensors": {
                    "camera": {
                        "type": "RGB video",
                        "resolution_4k": True,
                        "frame_rate_fps": 30,
                        "video_formats": ["MP4"]
                    },
                    "gps": {
                        "accuracy_m": 2,
                        "update_rate_hz": 10,
                        "reference_system": "WGS84"
                    }
                },

                "telemetry": {
                    "formats": ["proprietary_json", "gutma_dx"],
                    "proprietary_json_fields": ["time", "battery_level", "controller_gps_latitude", "controller_gps_longitude",
                                               "flying_state", "product_gps_available", "product_gps_longitude", "product_gps_latitude",
                                               "speed_vx", "speed_vy", "speed_vz", "angle_phi", "angle_theta", "angle_psi", "altitude"],
                    "gutma_dx_fields": ["aircraft_info", "gcs_info", "battery_data", "flight_events", "telemetry_items"],
                    "update_rate_hz": 10
                },

                "flights_with_video": 4,
                "flights_metadata_only": 3,
                "total_flights_documented": 7,

                "flight_details": {
                    "20250811_parrot_01": {
                        "flight_id": "20250811_parrot_01",
                        "date": "2025-08-11",
                        "video_files": 3,
                        "video_format": "MP4",
                        "metadata_format": "MISSING",
                        "status": "INCOMPLETE (no telemetry data)"
                    },
                    "20250818_parrot_01": {
                        "flight_id": "20250818_parrot_01",
                        "date": "2025-08-18",
                        "video_files": 3,
                        "video_format": "MP4",
                        "metadata_format": "JSON (proprietary Parrot)",
                        "status": "READY"
                    },
                    "20250818_parrot_02": {
                        "flight_id": "20250818_parrot_02",
                        "date": "2025-08-18",
                        "video_files": 3,
                        "video_format": "MP4",
                        "metadata_format": "JSON (proprietary Parrot)",
                        "status": "READY"
                    },
                    "20250825_parrot_01": {
                        "flight_id": "20250825_parrot_01",
                        "date": "2025-08-25",
                        "video_files": 2,
                        "video_format": "MP4",
                        "metadata_format": "JSON (GUTMA DX standard)",
                        "status": "READY"
                    },
                    "20250825_parrot_02": {
                        "flight_id": "20250825_parrot_02",
                        "date": "2025-08-25",
                        "video_files": 0,
                        "metadata_format": "JSON (GUTMA DX standard)",
                        "status": "BLOCKED (no video data uploaded)",
                        "note": "Metadata present but videos missing - data loss"
                    },
                    "20250825_parrot_03": {
                        "flight_id": "20250825_parrot_03",
                        "date": "2025-08-25",
                        "video_files": 0,
                        "metadata_format": "JSON (GUTMA DX standard)",
                        "status": "BLOCKED (no video data uploaded)",
                        "note": "Metadata present but videos missing - data loss"
                    },
                    "20250825_parrot_04": {
                        "flight_id": "20250825_parrot_04",
                        "date": "2025-08-25",
                        "video_files": 0,
                        "metadata_format": "JSON (GUTMA DX standard)",
                        "status": "BLOCKED (no video data uploaded)",
                        "note": "Metadata present but videos missing - data loss"
                    }
                }
            },

            "mission_summary": {
                "total_flights": 8,
                "flights_with_complete_data": 5,
                "flights_with_metadata_only": 3,
                "total_video_files": 13,
                "deployment_period": "2025-08-11 to 2025-08-25",
                "data_loss_note": "3 flights (20250825_parrot_02/03/04) have telemetry but no video files"
            }
        }

    # CITIZEN SCIENCE
    if "citizen_science" in include_modalities:
        platform_specs["platforms"]["citizen_science"] = {
            "__description": "Crowdsourced mobile phone observations from park visitors",

            "smartphone_generic": {
                "platform_type": "mobile_phone_camera",
                "category": "Crowdsourced Observations",
                "manufacturers": ["Apple (various iOS versions)", "Google (Android)", "Samsung (Android)", "Other Android devices"],

                "sensors": {
                    "camera": {
                        "type": "built_in_mobile_device_camera",
                        "resolution_range_mp": [5, 50],
                        "resolution_variable": True
                    },
                    "gps": {
                        "type": "optional_mobile_gps",
                        "availability": "inconsistent across submissions",
                        "accuracy_m": "variable (±5m to ±100m typical)"
                    }
                },

                "submissions": 991,
                "total_data_gb": 8.9,

                "file_distribution": {
                    "photographs": {
                        "jpeg": 395,
                        "JPG": 340,
                        "jpg": 6,
                        "HEIC": 88,
                        "heic": 24,
                        "total_photos": 853
                    },
                    "videos": {
                        "MOV": 90,
                        "mov": 1,
                        "MP4": 47,
                        "mp4": 0,
                        "total_videos": 138
                    },
                    "total_files": 991
                },

                "file_naming": {
                    "pattern": "UUID-based or device-specific",
                    "example_uuid": "00113818-3AD3-4270-ADC0-F9D8105FB5B3_1_105_c.jpeg",
                    "example_ios": "IMG_XXXX.[JPEG|HEIC|MOV]",
                    "example_android": "device_specific_naming"
                },

                "metadata_status": "EXTERNAL_INDEX_REQUIRED",
                "metadata_notes": [
                    "No submission index file in citizen_science/ directory",
                    "Cannot link files to submitter information without external index",
                    "Expected format: citizen_science_index.csv with columns [file_uuid, submission_id, submitter_name, date_taken, location_coords, observation_notes]",
                    "User to provide index from JotForm submission logs"
                ],

                "data_characteristics": {
                    "coverage": "Non-systematic, opportunistic observations",
                    "location_accuracy": "Variable - dependent on submitter location capture",
                    "timestamp_accuracy": "Variable - dependent on device clock and submission workflow",
                    "observation_quality": "Awaiting manual curation and species identification"
                },

                "notes": "Crowdsourced data from park visitors. Highly heterogeneous in terms of equipment, technique, and observation annotation quality. Requires manual curation."
            }
        }

    # Add deployment summary
    platform_specs["summary"] = {
        "total_modalities": len(include_modalities),
        "study_period": "2025-06-30 to 2025-08-28",
        "study_location": "The Wilds Conservation Center, Southeastern Ohio",
        "study_area_hectares": 150,

        "deployment_counts": {
            "camera_traps": 13 if "camera_traps" in include_modalities else 0,
            "bioacoustics": 6 if "bioacoustics" in include_modalities else 0,
            "drones": 8 if "drones" in include_modalities else 0,
            "citizen_science": 991 if "citizen_science" in include_modalities else 0
        },

        "total_data_volume": {
            "camera_traps_images": "~224k JPG/jpg files (~211 GB)" if "camera_traps" in include_modalities else 0,
            "bioacoustics_audio": "2,142 WAV files (~209 GB)" if "bioacoustics" in include_modalities else 0,
            "drones_video": "13 video files (~33 GB)" if "drones" in include_modalities else 0,
            "citizen_science_media": "991 files (853 photos + 138 videos, ~8.9 GB)" if "citizen_science" in include_modalities else 0
        }
    }

    # Write to JSON with nice formatting
    with open(output_path, 'w') as f:
        json.dump(platform_specs, f, indent=2)

    print(f"✓ Generated multi-modal platform specifications: {output_path}")
    return platform_specs


if __name__ == "__main__":
    # Create output directory if it doesn't exist
    output_dir = Path("/fs/ess/PAS2136/TheWilds2025/processing_output/darwin_core_metadata")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "platform_specifications_all_modalities.json"
    create_platform_specifications(str(output_file))
