#!/usr/bin/env python3
"""
Interactive Detection Review Tool

Allows manual review and correction of wildlife detections.
- View images with bounding boxes
- Edit species labels
- Add notes about mistakes
- Export corrected results
"""

import pandas as pd
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DetectionReviewer:
    """Interactive tool for reviewing and correcting detections."""

    def __init__(self, csv_path: str, json_path: str):
        """
        Initialize the reviewer.

        Args:
            csv_path: Path to wildlife_detections.csv
            json_path: Path to wildlife_detections.json
        """
        self.csv_path = Path(csv_path)
        self.json_path = Path(json_path)

        # Load data
        self.df = pd.read_csv(csv_path)
        with open(json_path, 'r') as f:
            self.detailed_data = json.load(f)

        # Create review data structure
        self.reviews = []
        self.current_index = 0

        # Load existing reviews if available
        self.review_file = self.csv_path.parent / "detection_reviews.json"
        if self.review_file.exists():
            with open(self.review_file, 'r') as f:
                self.reviews = json.load(f)

        logger.info(f"Loaded {len(self.df)} images for review")
        if self.reviews:
            logger.info(f"Found {len(self.reviews)} existing reviews")

    def save_reviews(self):
        """Save reviews to JSON file."""
        with open(self.review_file, 'w') as f:
            json.dump(self.reviews, f, indent=2)
        logger.info(f"Saved reviews to {self.review_file}")

    def export_corrected_csv(self, output_path: str):
        """
        Export corrected detections to CSV.

        Args:
            output_path: Path to save corrected CSV
        """
        # Create a copy of the dataframe
        corrected_df = self.df.copy()

        # Apply corrections from reviews
        for review in self.reviews:
            if 'corrected_species' in review and review['corrected_species']:
                idx = corrected_df[corrected_df['filename'] == review['filename']].index
                if len(idx) > 0:
                    corrected_df.loc[idx[0], 'species_detected'] = review['corrected_species']
                    corrected_df.loc[idx[0], 'reviewed'] = True
                    corrected_df.loc[idx[0], 'review_notes'] = review.get('notes', '')

        # Add reviewed column if not exists
        if 'reviewed' not in corrected_df.columns:
            corrected_df['reviewed'] = False
        if 'review_notes' not in corrected_df.columns:
            corrected_df['review_notes'] = ''

        corrected_df.to_csv(output_path, index=False)
        logger.info(f"Exported corrected CSV to {output_path}")

    def draw_detections(self, image_path: Path, detections: Dict,
                       output_path: Optional[Path] = None) -> Image.Image:
        """
        Draw bounding boxes on image.

        Args:
            image_path: Path to image
            detections: Detection dictionary with animals, people, vehicles
            output_path: Optional path to save annotated image

        Returns:
            PIL Image with annotations
        """
        img = Image.open(image_path).convert('RGB')
        draw = ImageDraw.Draw(img)

        img_width, img_height = img.size

        # Draw animal bounding boxes (green)
        for animal in detections.get('animals', []):
            bbox = animal['bbox']  # [x, y, width, height] normalized
            x1 = int(bbox[0] * img_width)
            y1 = int(bbox[1] * img_height)
            x2 = int((bbox[0] + bbox[2]) * img_width)
            y2 = int((bbox[1] + bbox[3]) * img_height)

            draw.rectangle([x1, y1, x2, y2], outline='green', width=3)

            # Add confidence label
            conf = animal['confidence']
            draw.text((x1, y1 - 20), f"Animal {conf:.2f}", fill='green')

        # Draw people bounding boxes (red)
        for person in detections.get('people', []):
            bbox = person['bbox']
            x1 = int(bbox[0] * img_width)
            y1 = int(bbox[1] * img_height)
            x2 = int((bbox[0] + bbox[2]) * img_width)
            y2 = int((bbox[1] + bbox[3]) * img_height)

            draw.rectangle([x1, y1, x2, y2], outline='red', width=3)
            draw.text((x1, y1 - 20), "Person", fill='red')

        # Draw vehicle bounding boxes (blue)
        for vehicle in detections.get('vehicles', []):
            bbox = vehicle['bbox']
            x1 = int(bbox[0] * img_width)
            y1 = int(bbox[1] * img_height)
            x2 = int((bbox[0] + bbox[2]) * img_width)
            y2 = int((bbox[1] + bbox[3]) * img_height)

            draw.rectangle([x1, y1, x2, y2], outline='blue', width=3)
            draw.text((x1, y1 - 20), "Vehicle", fill='blue')

        if output_path:
            img.save(output_path)
            logger.info(f"Saved annotated image to {output_path}")

        return img

    def review_image(self, index: int):
        """
        Review a specific image.

        Args:
            index: Index in the dataframe
        """
        if index >= len(self.df):
            logger.warning(f"Index {index} out of range")
            return

        row = self.df.iloc[index]
        filename = row['filename']

        print("\n" + "="*80)
        print(f"Review #{index + 1}/{len(self.df)}: {filename}")
        print("="*80)

        # Show current detection info
        print(f"\n📊 Detection Summary:")
        print(f"  Animals detected: {row['num_animals']}")
        print(f"  People detected: {row['num_people']}")
        print(f"  Vehicles detected: {row['num_vehicles']}")
        print(f"  Species identified: {row['species_detected']}")
        print(f"  Confidence: {row['avg_species_confidence']:.2%}")

        # Find detailed data
        detailed = None
        for item in self.detailed_data:
            if item['filename'] == filename:
                detailed = item
                break

        if detailed and 'species_results' in detailed:
            print(f"\n🔍 Detailed Species Predictions:")
            for i, sp_result in enumerate(detailed['species_results'], 1):
                print(f"\n  Detection {i}:")
                for j, pred in enumerate(sp_result['species_predictions'][:3], 1):
                    print(f"    {j}. {pred['species']}: {pred['confidence']:.2%}")

        # Check if already reviewed
        existing_review = None
        for review in self.reviews:
            if review['filename'] == filename:
                existing_review = review
                break

        if existing_review:
            print(f"\n✅ Previous Review:")
            print(f"  Corrected species: {existing_review.get('corrected_species', 'N/A')}")
            print(f"  Notes: {existing_review.get('notes', 'N/A')}")

        # Create annotated image
        if detailed:
            img_path = Path(row['file_path'])
            if img_path.exists():
                output_dir = self.csv_path.parent / "annotated_images"
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"annotated_{filename}"

                self.draw_detections(img_path, detailed['detections'], output_path)
                print(f"\n🖼️  Annotated image saved to: {output_path}")
            else:
                print(f"\n⚠️  Image not found at: {img_path}")

    def interactive_review(self):
        """Start interactive review session."""
        print("\n🔍 Interactive Detection Review Tool")
        print("="*80)
        print("Commands:")
        print("  n - Next image")
        print("  p - Previous image")
        print("  j <number> - Jump to image number")
        print("  c - Correct species for current image")
        print("  note - Add note about mistakes")
        print("  s - Show summary statistics")
        print("  export - Export corrected results")
        print("  q - Quit and save")
        print("="*80)

        self.current_index = 0

        while True:
            # Show only animals by default
            while self.current_index < len(self.df) and not self.df.iloc[self.current_index]['contains_animals']:
                self.current_index += 1

            if self.current_index >= len(self.df):
                print("\n✅ Reviewed all images with animals!")
                break

            self.review_image(self.current_index)

            # Get user input
            cmd = input("\n➤ Command: ").strip().lower()

            if cmd == 'n':
                self.current_index += 1
            elif cmd == 'p':
                self.current_index = max(0, self.current_index - 1)
            elif cmd.startswith('j '):
                try:
                    jump_to = int(cmd.split()[1]) - 1
                    if 0 <= jump_to < len(self.df):
                        self.current_index = jump_to
                    else:
                        print(f"Invalid index. Must be between 1 and {len(self.df)}")
                except ValueError:
                    print("Invalid jump command. Use: j <number>")
            elif cmd == 'c':
                self._correct_species()
            elif cmd == 'note':
                self._add_note()
            elif cmd == 's':
                self._show_summary()
            elif cmd == 'export':
                output_path = input("Export path (default: wildlife_detections_corrected.csv): ").strip()
                if not output_path:
                    output_path = str(self.csv_path.parent / "wildlife_detections_corrected.csv")
                self.export_corrected_csv(output_path)
            elif cmd == 'q':
                self.save_reviews()
                print("\n👋 Reviews saved. Goodbye!")
                break
            else:
                print("Unknown command. Type 'h' for help.")

    def _correct_species(self):
        """Correct species labels for current image."""
        row = self.df.iloc[self.current_index]
        filename = row['filename']

        print(f"\nCurrent: {row['species_detected']}")
        print("Enter corrected species counts (e.g., 'Grevy's zebra: 3, ostrich: 1')")
        print("Or enter individual species separated by commas")
        print("Press Enter to skip")

        corrected = input("➤ Corrected species: ").strip()

        if corrected:
            # Find or create review entry
            review = None
            for r in self.reviews:
                if r['filename'] == filename:
                    review = r
                    break

            if review is None:
                review = {
                    'filename': filename,
                    'original_species': row['species_detected'],
                    'corrected_species': corrected,
                    'notes': ''
                }
                self.reviews.append(review)
            else:
                review['corrected_species'] = corrected

            self.save_reviews()
            print("✅ Correction saved!")

    def _add_note(self):
        """Add notes about mistakes for current image."""
        row = self.df.iloc[self.current_index]
        filename = row['filename']

        print("\nAdd notes about what the model got wrong:")
        print("(e.g., 'Misidentified oryx as zebra', 'Missed one animal in background')")

        note = input("➤ Note: ").strip()

        if note:
            # Find or create review entry
            review = None
            for r in self.reviews:
                if r['filename'] == filename:
                    review = r
                    break

            if review is None:
                review = {
                    'filename': filename,
                    'original_species': row['species_detected'],
                    'notes': note
                }
                self.reviews.append(review)
            else:
                review['notes'] = note

            self.save_reviews()
            print("✅ Note saved!")

    def _show_summary(self):
        """Show summary statistics of reviews."""
        print("\n" + "="*80)
        print("📊 Review Summary")
        print("="*80)
        print(f"Total images: {len(self.df)}")
        print(f"Images with animals: {self.df['contains_animals'].sum()}")
        print(f"Images reviewed: {len(self.reviews)}")

        # Count types of issues
        with_corrections = sum(1 for r in self.reviews if 'corrected_species' in r and r['corrected_species'])
        with_notes = sum(1 for r in self.reviews if 'notes' in r and r['notes'])

        print(f"Images with corrections: {with_corrections}")
        print(f"Images with notes: {with_notes}")

        if with_notes > 0:
            print("\n📝 Common Issues:")
            for review in self.reviews:
                if review.get('notes'):
                    print(f"  - {review['filename']}: {review['notes']}")


def main():
    """Main entry point."""
    import sys

    # Default paths
    csv_path = "wildlife_detections.csv"
    json_path = "wildlife_detections.json"

    # Check if files exist
    if not Path(csv_path).exists():
        print(f"Error: {csv_path} not found")
        print("Please run detect_species.py first to generate detection results")
        sys.exit(1)

    if not Path(json_path).exists():
        print(f"Error: {json_path} not found")
        print("Please run detect_species.py first to generate detection results")
        sys.exit(1)

    # Create reviewer
    reviewer = DetectionReviewer(csv_path, json_path)

    # Start interactive review
    reviewer.interactive_review()


if __name__ == "__main__":
    main()
