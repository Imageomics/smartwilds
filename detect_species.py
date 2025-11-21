#!/usr/bin/env python3
"""
Wildlife Detection and Species Identification Pipeline

This script uses:
1. MegaDetector v5 - to detect animals, people, and vehicles
2. BioCLIP v2 - for species identification on detected animals

Filters out photos with people and focuses on wildlife species identification.
"""

import pandas as pd
import torch
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from PIL import Image
import json
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WildlifeDetector:
    """
    Combines MegaDetector for animal detection and BioCLIP for species identification.
    """

    def __init__(self, confidence_threshold: float = 0.2):
        """
        Initialize the detector.

        Args:
            confidence_threshold: Minimum confidence for MegaDetector detections (default: 0.2)
        """
        self.confidence_threshold = confidence_threshold
        self.megadetector = None
        self.bioclip_model = None
        self.bioclip_processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Using device: {self.device}")

    def load_megadetector(self):
        """Load MegaDetector v5 model."""
        import urllib.request
        import sys

        logger.info("Loading MegaDetector v5...")

        # Define model path in cache directory
        cache_dir = Path.home() / ".cache" / "megadetector"
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_path = cache_dir / "md_v5a.0.0.pt"

        # Download model if not cached
        if not model_path.exists():
            logger.info(f"Downloading MegaDetector v5 to {model_path}...")
            url = 'https://github.com/microsoft/CameraTraps/releases/download/v5.0/md_v5a.0.0.pt'

            try:
                urllib.request.urlretrieve(url, model_path)
                logger.info("Download complete!")
            except Exception as e:
                logger.error(f"Error downloading MegaDetector: {e}")
                raise
        else:
            logger.info(f"Using cached model from {model_path}")

        # Load model - need to handle PyTorch 2.6+ weights_only change
        try:
            logger.info("Loading model weights...")

            # Get YOLOv5 code
            yolov5_dir = Path.home() / ".cache" / "torch" / "hub" / "ultralytics_yolov5_master"

            # Ensure YOLOv5 repo is downloaded
            if not yolov5_dir.exists():
                logger.info("Downloading YOLOv5 repository...")
                torch.hub.load('ultralytics/yolov5', 'yolov5s', trust_repo=True)

            # Add YOLOv5 to path
            if str(yolov5_dir) not in sys.path:
                sys.path.insert(0, str(yolov5_dir))

            # Import YOLOv5 modules
            from models.experimental import attempt_load

            # Patch torch.load to use weights_only=False for this model
            # MegaDetector is from Microsoft's official repository - trusted source
            original_load = torch.load

            def patched_load(f, *args, **kwargs):
                # Force weights_only=False for trusted MegaDetector weights
                kwargs['weights_only'] = False
                return original_load(f, *args, **kwargs)

            torch.load = patched_load

            try:
                self.megadetector = attempt_load(str(model_path), device=self.device)
                self.megadetector.eval()
                logger.info("MegaDetector loaded successfully")
            finally:
                # Restore original torch.load
                torch.load = original_load

        except Exception as e:
            logger.error(f"Error loading MegaDetector: {e}")
            raise

    def load_bioclip(self):
        """Load BioCLIP v2 model from HuggingFace."""
        try:
            import open_clip

            logger.info("Loading BioCLIP v2 from HuggingFace...")
            model_name = "hf-hub:imageomics/bioclip-2"

            # Load model and preprocessing transforms
            self.bioclip_model, _, self.bioclip_preprocess = open_clip.create_model_and_transforms(model_name)
            self.bioclip_tokenizer = open_clip.get_tokenizer(model_name)

            self.bioclip_model = self.bioclip_model.to(self.device)
            self.bioclip_model.eval()

            logger.info("BioCLIP v2 loaded successfully")

        except Exception as e:
            logger.error(f"Error loading BioCLIP: {e}")
            raise

    def detect_objects(self, image_path: Path) -> Dict:
        """
        Run MegaDetector on an image.

        Returns:
            Dictionary with detection results including animals, people, and vehicles
        """
        try:
            import torchvision.transforms as T

            image = Image.open(image_path).convert('RGB')

            # Convert PIL image to tensor and resize to 640 (standard YOLOv5 input size)
            img_resized = T.Resize((640, 640))(image)
            img_tensor = T.ToTensor()(img_resized)  # Converts to [C, H, W] and normalizes to [0, 1]
            img_tensor = img_tensor.unsqueeze(0).to(self.device)  # Add batch dimension [1, C, H, W]

            # Run YOLOv5 inference
            with torch.no_grad():
                raw_predictions = self.megadetector(img_tensor)

                # YOLOv5 returns a tuple: (predictions, training_outputs)
                # predictions shape: [batch, num_detections, 5 + num_classes]
                # For MegaDetector: [1, num_detections, 5 + 3] = [1, num_detections, 8]
                # Format: [x_center, y_center, width, height, objectness, class1_conf, class2_conf, class3_conf]

                # Apply NMS (non-maximum suppression) if not already applied
                from utils.general import non_max_suppression
                predictions = non_max_suppression(raw_predictions, conf_thres=self.confidence_threshold, iou_thres=0.45)
                predictions = predictions[0]  # Get detections for first (only) image

            # MegaDetector categories: 0=animal, 1=person, 2=vehicle
            detections = {
                'animals': [],
                'people': [],
                'vehicles': [],
            }

            # Parse results
            # After NMS, predictions shape: [num_detections, 6] where each row is [x1, y1, x2, y2, confidence, class]
            if predictions is not None and len(predictions) > 0:
                for detection in predictions:
                    det_list = detection.tolist()
                    x1, y1, x2, y2, confidence, cls = det_list[:6]

                    # Convert to normalized [x, y, width, height] format
                    # Coordinates are in the 640x640 space
                    x = x1 / 640
                    y = y1 / 640
                    width = (x2 - x1) / 640
                    height = (y2 - y1) / 640

                    det_info = {
                        'confidence': float(confidence),
                        'bbox': [x, y, width, height]
                    }

                    # MegaDetector uses 0-indexed classes
                    if int(cls) == 0:  # animal
                        detections['animals'].append(det_info)
                    elif int(cls) == 1:  # person
                        detections['people'].append(det_info)
                    elif int(cls) == 2:  # vehicle
                        detections['vehicles'].append(det_info)

            return detections

        except Exception as e:
            logger.error(f"Error detecting objects in {image_path}: {e}")
            return {'animals': [], 'people': [], 'vehicles': [], 'error': str(e)}

    def crop_detection(self, image: Image.Image, bbox: List[float],
                       padding: float = 0.1) -> Image.Image:
        """
        Crop image to bounding box with padding.

        Args:
            image: PIL Image
            bbox: [x, y, width, height] in normalized coordinates (0-1)
            padding: Fraction to expand bbox (default: 0.1 = 10%)

        Returns:
            Cropped PIL Image
        """
        img_width, img_height = image.size

        # Convert normalized bbox to pixel coordinates
        x, y, w, h = bbox
        x1 = int(x * img_width)
        y1 = int(y * img_height)
        x2 = int((x + w) * img_width)
        y2 = int((y + h) * img_height)

        # Add padding
        pad_w = int(w * img_width * padding)
        pad_h = int(h * img_height * padding)

        x1 = max(0, x1 - pad_w)
        y1 = max(0, y1 - pad_h)
        x2 = min(img_width, x2 + pad_w)
        y2 = min(img_height, y2 + pad_h)

        return image.crop((x1, y1, x2, y2))

    def identify_species(self, image_path: Path, animal_bboxes: List[Dict],
                        top_k: int = 5) -> List[Dict]:
        """
        Identify species using BioCLIP for detected animals.

        Args:
            image_path: Path to image
            animal_bboxes: List of animal bounding boxes from MegaDetector
            top_k: Number of top predictions to return

        Returns:
            List of species predictions for each detected animal
        """
        try:
            image = Image.open(image_path).convert('RGB')
            all_predictions = []

            for idx, bbox_info in enumerate(animal_bboxes):
                bbox = bbox_info['bbox']

                # Crop to animal detection
                cropped = self.crop_detection(image, bbox)

                # Process with BioCLIP
                inputs = self.bioclip_processor(images=cropped, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.bioclip_model(**inputs)

                # Get predictions
                # Note: BioCLIP may have different output structure
                # This is a placeholder - adjust based on actual model API
                predictions = self._parse_bioclip_output(outputs, top_k)

                all_predictions.append({
                    'detection_index': idx,
                    'bbox': bbox,
                    'confidence': bbox_info['confidence'],
                    'species_predictions': predictions
                })

            return all_predictions

        except Exception as e:
            logger.error(f"Error identifying species in {image_path}: {e}")
            return []

    def _parse_bioclip_output(self, outputs, top_k: int = 5) -> List[Dict]:
        """
        Parse BioCLIP model outputs to get species predictions.

        Note: This needs to be adapted based on BioCLIP v2's actual output format.
        """
        # Placeholder - adjust based on actual BioCLIP v2 API
        # BioCLIP likely uses CLIP-style architecture with text-image similarity

        # Common approach would be to compare image embeddings with species class embeddings
        # For now, return placeholder structure
        return [
            {'species': 'unknown', 'confidence': 0.0}
        ]

    def classify_with_species_list(self, image_path: Path, animal_bboxes: List[Dict],
                                   species_list: List[str]) -> List[Dict]:
        """
        Classify animals using a predefined list of species.

        Args:
            image_path: Path to image
            animal_bboxes: List of animal detections
            species_list: List of possible species names

        Returns:
            List of predictions with species from the provided list
        """
        try:
            image = Image.open(image_path).convert('RGB')
            all_predictions = []

            # Tokenize species names
            text_tokens = self.bioclip_tokenizer(species_list).to(self.device)

            for idx, bbox_info in enumerate(animal_bboxes):
                bbox = bbox_info['bbox']
                cropped = self.crop_detection(image, bbox)

                # Preprocess image
                image_tensor = self.bioclip_preprocess(cropped).unsqueeze(0).to(self.device)

                with torch.no_grad():
                    # Get image and text features
                    image_features = self.bioclip_model.encode_image(image_tensor)
                    text_features = self.bioclip_model.encode_text(text_tokens)

                    # Normalize features
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)

                    # Calculate similarity
                    similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                    probs = similarity[0]

                # Get top predictions
                top_probs, top_indices = torch.topk(probs, k=min(5, len(species_list)))

                predictions = [
                    {
                        'species': species_list[idx.item()],
                        'confidence': prob.item()
                    }
                    for prob, idx in zip(top_probs, top_indices)
                ]

                all_predictions.append({
                    'detection_index': idx,
                    'bbox': bbox,
                    'megadetector_confidence': bbox_info['confidence'],
                    'species_predictions': predictions,
                    'top_species': predictions[0]['species'],
                    'species_confidence': predictions[0]['confidence']
                })

            return all_predictions

        except Exception as e:
            logger.error(f"Error in species classification: {e}")
            return []


def process_images(
    image_folder: str,
    metadata_csv: Optional[str] = None,
    output_csv: str = "wildlife_detections.csv",
    output_json: str = "wildlife_detections.json",
    filter_people: bool = True,
    species_list: Optional[List[str]] = None,
    max_images: Optional[int] = None,
    location: str = "TheWilds"
) -> pd.DataFrame:
    """
    Process images with MegaDetector and BioCLIP.

    Args:
        image_folder: Path to folder with images
        metadata_csv: Optional CSV with existing metadata
        output_csv: Path to save CSV results
        output_json: Path to save detailed JSON results
        filter_people: If True, skip images with people
        species_list: Optional list of species to classify against
        max_images: Maximum number of images to process (for testing)
        location: Location name for all photos (default: "TheWilds")

    Returns:
        DataFrame with detection and species ID results
    """
    detector = WildlifeDetector()
    detector.load_megadetector()
    detector.load_bioclip()

    # Load existing metadata if provided
    metadata_df = None
    if metadata_csv and Path(metadata_csv).exists():
        metadata_df = pd.read_csv(metadata_csv)
        # Convert datetime_taken to datetime if it exists
        if 'datetime_taken' in metadata_df.columns:
            metadata_df['datetime_taken'] = pd.to_datetime(metadata_df['datetime_taken'], errors='coerce')
        image_paths = [Path(p) for p in metadata_df['file_path']]
    else:
        # Find all images in folder
        folder = Path(image_folder)
        image_paths = []
        for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
            image_paths.extend(folder.glob(f"**/*{ext}"))

    if max_images:
        image_paths = image_paths[:max_images]

    logger.info(f"Processing {len(image_paths)} images...")

    results = []
    detailed_results = []

    for image_path in tqdm(image_paths, desc="Processing images"):
        try:
            # Run MegaDetector
            detections = detector.detect_objects(image_path)

            num_animals = len(detections['animals'])
            num_people = len(detections['people'])
            num_vehicles = len(detections['vehicles'])

            # Skip if filtering people and people detected
            if filter_people and num_people > 0:
                logger.info(f"Skipping {image_path.name} - contains people")
                continue

            # Get metadata for this image if available
            date_time = None
            latitude = None
            longitude = None
            if metadata_df is not None:
                # Find matching row in metadata
                metadata_row = metadata_df[metadata_df['filename'] == image_path.name]
                if not metadata_row.empty:
                    date_time = metadata_row.iloc[0].get('datetime_taken')
                    latitude = metadata_row.iloc[0].get('latitude')
                    longitude = metadata_row.iloc[0].get('longitude')

            # Create result with new column structure
            result = {
                'file_ID': image_path.name,
                'recording/photo/frame': 'photo',
                'date_time': date_time if pd.notna(date_time) else None,
                'location': location,
                'Latitude': latitude if pd.notna(latitude) else None,
                'Longitude': longitude if pd.notna(longitude) else None,
                'num_animals': num_animals,
                'num_people': num_people,
                'num_vehicles': num_vehicles,
                'contains_animals': num_animals > 0,
                'contains_people': num_people > 0,
            }

            # Run species identification if animals detected
            animal_detections = []
            if num_animals > 0:
                if species_list:
                    species_results = detector.classify_with_species_list(
                        image_path, detections['animals'], species_list
                    )
                else:
                    species_results = detector.identify_species(
                        image_path, detections['animals']
                    )

                # Build structured animal detections with species
                from collections import Counter
                species_counts = Counter()
                all_confidences = []

                for idx, (animal, sp_result) in enumerate(zip(detections['animals'], species_results)):
                    detection_entry = {
                        "id": idx + 1,
                        "bbox": [
                            round(animal['bbox'][0], 4),
                            round(animal['bbox'][1], 4),
                            round(animal['bbox'][2], 4),
                            round(animal['bbox'][3], 4)
                        ]
                    }

                    # Add species information if available
                    if sp_result['species_predictions']:
                        top_pred = sp_result['species_predictions'][0]
                        detection_entry["species"] = top_pred['species']
                        detection_entry["confidence"] = round(top_pred['confidence'], 4)
                        species_counts[top_pred['species']] += 1
                        all_confidences.append(top_pred['confidence'])
                    else:
                        detection_entry["species"] = None
                        detection_entry["confidence"] = 0.0

                    animal_detections.append(detection_entry)

                # Format summary strings
                species_count_str = ', '.join([f"{species}: {count}" for species, count in sorted(species_counts.items())])

                result['animal_detections'] = json.dumps(animal_detections)  # JSON string for CSV
                result['species_counts'] = dict(species_counts)  # For JSON/dict access
                result['species_detected'] = species_count_str  # For CSV/readable format
                result['num_unique_species'] = len(species_counts)
                result['total_animals_identified'] = sum(species_counts.values())
                result['avg_species_confidence'] = sum(all_confidences) / len(all_confidences) if all_confidences else 0

                detailed_results.append({
                    'file_ID': image_path.name,
                    'file_path': str(image_path),
                    'date_time': str(date_time) if date_time else None,
                    'location': location,
                    'latitude': latitude,
                    'longitude': longitude,
                    'detections': detections,
                    'species_results': species_results,
                    'species_counts': dict(species_counts),
                    'animal_detections': animal_detections
                })
            else:
                result['animal_detections'] = '[]'
                result['species_counts'] = {}
                result['species_detected'] = ''
                result['num_unique_species'] = 0
                result['total_animals_identified'] = 0
                result['avg_species_confidence'] = 0

            results.append(result)

        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}")
            continue

    # Create DataFrame with specified column order
    df = pd.DataFrame(results)

    # Reorder columns to match requested structure
    column_order = [
        'file_ID', 'recording/photo/frame', 'date_time', 'location', 'Latitude', 'Longitude',
        'num_animals', 'num_people', 'num_vehicles', 'contains_animals', 'contains_people',
        'animal_detections', 'species_counts', 'species_detected', 'num_unique_species',
        'total_animals_identified', 'avg_species_confidence'
    ]

    # Only include columns that exist
    column_order = [col for col in column_order if col in df.columns]
    df = df[column_order]

    # Save results
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved CSV results to: {output_csv}")

    with open(output_json, 'w') as f:
        json.dump(detailed_results, f, indent=2, default=str)
    logger.info(f"Saved detailed JSON results to: {output_json}")

    # Print summary
    logger.info("\n=== Processing Summary ===")
    logger.info(f"Total images processed: {len(df)}")
    logger.info(f"Images with animals: {df['contains_animals'].sum()}")
    if filter_people:
        logger.info(f"Images with people (filtered out): N/A")
    else:
        logger.info(f"Images with people: {df['contains_people'].sum()}")
    logger.info(f"Images with species identified: {(df['num_unique_species'] > 0).sum()}")

    if len(df[df['contains_animals']]) > 0:
        logger.info(f"\nSpecies detection summary:")
        # Aggregate all species counts across images
        from collections import Counter
        total_species_counts = Counter()
        for species_dict in df['species_counts']:
            if isinstance(species_dict, dict):
                total_species_counts.update(species_dict)

        if total_species_counts:
            logger.info(f"Total animals identified by species:")
            for species, count in total_species_counts.most_common():
                logger.info(f"  {species}: {count}")

    return df


def main():
    """
    Main entry point with example usage.
    """
    # Example configuration
    image_folder = "/Users/kline.377/Downloads/Takeout/Google Photos/The Wilds Summer 2025 Fieldwork"
    metadata_csv = "/Users/kline.377/wilds_multimodal_data/photo_metadata.csv"
    output_csv = "/Users/kline.377/wilds_multimodal_data/wildlife_detections.csv"
    output_json = "/Users/kline.377/wilds_multimodal_data/wildlife_detections.json"

    # Optional: Define expected species for The Wilds
    # (Ohio wildlife preserve - common species)
    species_list = [
        "Pere David's deer",
        "bison",
        "giraffe",
        "rhinoceros",
        "Grevy's zebra",
        "wild horse",
        "Sichan takin",
        "onager",
        "Scimitar-horned oryx",
        "ostrich",
        "fish"
    ]

    # Process images
    df = process_images(
        image_folder=image_folder,
        metadata_csv=metadata_csv,
        output_csv=output_csv,
        output_json=output_json,
        filter_people=True,  # Skip photos with people
        species_list=species_list,  # Use predefined species list
        #max_images=100,  # Remove this to process all images
        location="TheWilds"  # Location name for all photos
    )

    print("\n=== Results Preview ===")
    print(df.head())

    # Show only animal photos
    animal_photos = df[df['contains_animals']]
    print(f"\n=== Animal Photos ({len(animal_photos)}) ===")
    print(animal_photos[['file_ID', 'date_time', 'location', 'num_animals', 'species_detected', 'animal_detections']])


if __name__ == "__main__":
    main()
