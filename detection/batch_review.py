#!/usr/bin/env python3
"""
Batch Detection Review Tool

Quick tool to generate annotated images for all detections
and create a review spreadsheet.
"""

import pandas as pd
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def draw_detections(image_path: Path, detections: dict, species_results: list,
                    output_path: Path):
    """
    Draw bounding boxes and species labels on image.

    Args:
        image_path: Path to original image
        detections: Detection dictionary
        species_results: Species identification results
        output_path: Path to save annotated image
    """
    try:
        img = Image.open(image_path).convert('RGB')
        draw = ImageDraw.Draw(img)

        img_width, img_height = img.size

        # Try to load a font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
        except:
            font = ImageFont.load_default()
            font_small = font

        # Draw animal bounding boxes with species labels
        for i, animal in enumerate(detections.get('animals', [])):
            bbox = animal['bbox']  # [x, y, width, height] normalized
            x1 = int(bbox[0] * img_width)
            y1 = int(bbox[1] * img_height)
            x2 = int((bbox[0] + bbox[2]) * img_width)
            y2 = int((bbox[1] + bbox[3]) * img_height)

            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline='lime', width=4)

            # Get species label
            if i < len(species_results):
                sp_result = species_results[i]
                if sp_result['species_predictions']:
                    top_pred = sp_result['species_predictions'][0]
                    species = top_pred['species']
                    conf = top_pred['confidence']

                    # Draw background for text
                    text = f"{species} ({conf:.1%})"
                    bbox_text = draw.textbbox((x1, y1 - 25), text, font=font)
                    draw.rectangle(bbox_text, fill='lime')
                    draw.text((x1, y1 - 25), text, fill='black', font=font)

                    # Draw detection confidence
                    det_conf_text = f"Det: {animal['confidence']:.1%}"
                    draw.text((x1, y2 + 5), det_conf_text, fill='lime', font=font_small)

        # Draw people bounding boxes
        for person in detections.get('people', []):
            bbox = person['bbox']
            x1 = int(bbox[0] * img_width)
            y1 = int(bbox[1] * img_height)
            x2 = int((bbox[0] + bbox[2]) * img_width)
            y2 = int((bbox[1] + bbox[3]) * img_height)

            draw.rectangle([x1, y1, x2, y2], outline='red', width=4)

            bbox_text = draw.textbbox((x1, y1 - 25), "PERSON", font=font)
            draw.rectangle(bbox_text, fill='red')
            draw.text((x1, y1 - 25), "PERSON", fill='white', font=font)

        # Draw vehicle bounding boxes
        for vehicle in detections.get('vehicles', []):
            bbox = vehicle['bbox']
            x1 = int(bbox[0] * img_width)
            y1 = int(bbox[1] * img_height)
            x2 = int((bbox[0] + bbox[2]) * img_width)
            y2 = int((bbox[1] + bbox[3]) * img_height)

            draw.rectangle([x1, y1, x2, y2], outline='cyan', width=4)

            bbox_text = draw.textbbox((x1, y1 - 25), "VEHICLE", font=font)
            draw.rectangle(bbox_text, fill='cyan')
            draw.text((x1, y1 - 25), "VEHICLE", fill='black', font=font)

        # Save annotated image
        img.save(output_path, quality=95)
        logger.debug(f"Saved annotated image: {output_path}")

    except Exception as e:
        logger.error(f"Error annotating {image_path}: {e}")


def create_review_spreadsheet(df: pd.DataFrame, output_path: str):
    """
    Create a review spreadsheet with editable columns.

    Args:
        df: DataFrame with detection results
        output_path: Path to save review CSV
    """
    # Create review columns
    review_df = df.copy()

    # Add review columns
    review_df['reviewed'] = False
    review_df['corrected_species'] = review_df['species_detected']
    review_df['mistake_type'] = ''  # misidentification, missed_animal, false_positive, etc.
    review_df['notes'] = ''
    review_df['image_quality'] = ''  # good, blurry, occluded, etc.

    # Select relevant columns for review
    review_columns = [
        'filename',
        'num_animals',
        'num_people',
        'num_vehicles',
        'species_detected',
        'total_animals_identified',
        'avg_species_confidence',
        'reviewed',
        'corrected_species',
        'mistake_type',
        'notes',
        'image_quality',
        'file_path'
    ]

    review_df = review_df[review_columns]

    # Save to CSV
    review_df.to_csv(output_path, index=False)
    logger.info(f"Created review spreadsheet: {output_path}")

    return review_df


def generate_html_report(df: pd.DataFrame, annotated_dir: Path, output_path: str):
    """
    Generate HTML report for easy browsing.

    Args:
        df: DataFrame with detection results
        annotated_dir: Directory with annotated images
        output_path: Path to save HTML report
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Wildlife Detection Review</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            h1 {
                color: #333;
            }
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .image-card {
                background: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .image-card img {
                width: 100%;
                height: auto;
                border-radius: 4px;
            }
            .info {
                margin-top: 10px;
            }
            .info h3 {
                margin: 5px 0;
                color: #2c3e50;
            }
            .info p {
                margin: 5px 0;
                color: #7f8c8d;
            }
            .species {
                font-weight: bold;
                color: #27ae60;
            }
            .confidence {
                color: #3498db;
            }
            .filter-buttons {
                margin: 20px 0;
            }
            .filter-buttons button {
                padding: 10px 20px;
                margin-right: 10px;
                border: none;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                cursor: pointer;
            }
            .filter-buttons button:hover {
                background-color: #2980b9;
            }
            .notes-section {
                margin-top: 10px;
                padding: 10px;
                background-color: #fff3cd;
                border-radius: 4px;
                border-left: 4px solid #ffc107;
            }
            textarea {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                resize: vertical;
            }
        </style>
    </head>
    <body>
        <h1>🔍 Wildlife Detection Review</h1>
        <p>Review and annotate detection results</p>

        <div class="filter-buttons">
            <button onclick="filterImages('all')">All Images</button>
            <button onclick="filterImages('animals')">With Animals</button>
            <button onclick="filterImages('people')">With People</button>
            <button onclick="filterImages('vehicles')">With Vehicles</button>
        </div>

        <div class="image-grid" id="imageGrid">
    """

    # Add each image
    for idx, row in df.iterrows():
        filename = row['filename']
        annotated_filename = f"annotated_{filename}"
        annotated_path = annotated_dir / annotated_filename

        # Skip if annotated image doesn't exist
        if not annotated_path.exists():
            continue

        has_animals = row['contains_animals']
        has_people = row['contains_people']
        has_vehicles = row['num_vehicles'] > 0

        classes = []
        if has_animals:
            classes.append('animals')
        if has_people:
            classes.append('people')
        if has_vehicles:
            classes.append('vehicles')

        html += f"""
        <div class="image-card" data-classes="{' '.join(classes)}">
            <img src="annotated_images/{annotated_filename}" alt="{filename}">
            <div class="info">
                <h3>{filename}</h3>
                <p><strong>Animals:</strong> {row['num_animals']} |
                   <strong>People:</strong> {row['num_people']} |
                   <strong>Vehicles:</strong> {row['num_vehicles']}</p>
                <p class="species">Species: {row['species_detected'] if row['species_detected'] else 'None detected'}</p>
                <p class="confidence">Avg Confidence: {row['avg_species_confidence']:.1%}</p>

                <div class="notes-section">
                    <strong>Review Notes:</strong>
                    <textarea rows="3" placeholder="Add notes about mistakes or corrections..."
                              id="notes_{idx}">{row.get('notes', '')}</textarea>
                </div>
            </div>
        </div>
        """

    html += """
        </div>

        <script>
            function filterImages(category) {
                const cards = document.querySelectorAll('.image-card');
                cards.forEach(card => {
                    if (category === 'all') {
                        card.style.display = 'block';
                    } else {
                        const classes = card.getAttribute('data-classes');
                        card.style.display = classes.includes(category) ? 'block' : 'none';
                    }
                });
            }

            // Auto-save notes to localStorage
            document.querySelectorAll('textarea').forEach(textarea => {
                textarea.addEventListener('change', function() {
                    localStorage.setItem(this.id, this.value);
                });

                // Load saved notes
                const savedValue = localStorage.getItem(textarea.id);
                if (savedValue) {
                    textarea.value = savedValue;
                }
            });
        </script>
    </body>
    </html>
    """

    with open(output_path, 'w') as f:
        f.write(html)

    logger.info(f"Created HTML review report: {output_path}")


def main():
    """Main entry point."""
    csv_path = "wildlife_detections.csv"
    json_path = "wildlife_detections.json"

    # Check if files exist
    if not Path(csv_path).exists():
        print(f"Error: {csv_path} not found")
        return

    if not Path(json_path).exists():
        print(f"Error: {json_path} not found")
        return

    # Load data
    logger.info("Loading detection results...")
    df = pd.read_csv(csv_path)
    with open(json_path, 'r') as f:
        detailed_data = json.load(f)

    # Create output directory
    output_dir = Path("annotated_images")
    output_dir.mkdir(exist_ok=True)

    # Generate annotated images
    logger.info("Generating annotated images...")
    for item in tqdm(detailed_data, desc="Annotating images"):
        filename = item['filename']
        image_path = Path(item['file_path'])

        if not image_path.exists():
            logger.warning(f"Image not found: {image_path}")
            continue

        output_path = output_dir / f"annotated_{filename}"
        species_results = item.get('species_results', [])

        draw_detections(image_path, item['detections'], species_results, output_path)

    # Create review spreadsheet
    logger.info("Creating review spreadsheet...")
    review_csv = "wildlife_detections_review.csv"
    create_review_spreadsheet(df, review_csv)

    # Generate HTML report
    logger.info("Generating HTML report...")
    html_report = "detection_review.html"
    generate_html_report(df, output_dir, html_report)

    # Summary
    print("\n" + "="*80)
    print("✅ Batch review preparation complete!")
    print("="*80)
    print(f"📁 Annotated images: {output_dir}/")
    print(f"📊 Review spreadsheet: {review_csv}")
    print(f"🌐 HTML report: {html_report}")
    print("\nNext steps:")
    print("1. Open detection_review.html in your browser to visually review all images")
    print("2. Edit wildlife_detections_review.csv to correct species labels")
    print("3. Or run: python review_detections.py for interactive review")
    print("="*80)


if __name__ == "__main__":
    main()
