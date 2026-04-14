from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def _parse_scientific_name(label: str) -> str:
    marker = " with common name "
    if marker in label:
        return label.split(marker, 1)[0].strip()
    return label.strip()


def _build_detection_label_lines(det) -> list[str]:
    lines = [f"SAM3: {det['category_name']} {det['score']:.2f}"]

    bioclip = det.get("bioclip")
    if not bioclip:
        return lines

    zero_shot_predictions = bioclip.get("zero_shot", {}).get("predictions", [])
    if zero_shot_predictions:
        top_zero_shot = zero_shot_predictions[0]
        scientific_name = _parse_scientific_name(str(top_zero_shot.get("label", "")))
        score = float(top_zero_shot.get("score", 0.0))
        lines.append(f"BioCLIP: {scientific_name} {score:.2f}")

    return lines


def draw_detections(image_path: Path, detections, output_path: Path):
    try:
        with Image.open(image_path) as opened_image:
            image = cv2.cvtColor(
                np.array(opened_image.convert("RGB")),
                cv2.COLOR_RGB2BGR,
            )
    except OSError:
        return

    for det in detections:
        x1, y1, x2, y2 = [int(round(value)) for value in det["xyxy"]]
        mask = det.get("mask")
        if mask is not None:
            overlay = image.copy()
            overlay[np.asarray(mask, dtype=bool)] = (80, 200, 255)
            image = cv2.addWeighted(overlay, 0.35, image, 0.65, 0)

        label_lines = _build_detection_label_lines(det)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        padding = 4
        line_gap = 4
        text_sizes = [
            cv2.getTextSize(line, font, font_scale, thickness)
            for line in label_lines
        ]
        max_text_width = max(size[0][0] for size in text_sizes)
        line_heights = [size[0][1] + size[1] for size in text_sizes]
        text_block_height = sum(line_heights) + (line_gap * (len(label_lines) - 1))
        box_top = max(0, y1 - text_block_height - (2 * padding) - 6)
        box_bottom = box_top + text_block_height + (2 * padding)
        box_right = min(image.shape[1], x1 + max_text_width + (2 * padding))
        overlay = image.copy()
        cv2.rectangle(
            overlay,
            (x1, box_top),
            (box_right, box_bottom),
            (255, 255, 255),
            thickness=-1,
        )
        image = cv2.addWeighted(overlay, 0.6, image, 0.4, 0)

        current_y = box_top + padding
        for line, (size, baseline), line_height in zip(label_lines, text_sizes, line_heights):
            text_y = current_y + size[1]
            cv2.putText(
                image,
                line,
                (x1 + padding, text_y),
                font,
                font_scale,
                (0, 0, 0),
                thickness,
                cv2.LINE_AA,
            )
            current_y += line_height + line_gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)
