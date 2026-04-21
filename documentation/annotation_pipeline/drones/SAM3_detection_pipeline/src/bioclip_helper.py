from __future__ import annotations

from collections.abc import Sequence
import gc
from typing import Any

from PIL import Image
import torch


SMARTWILDS_ZERO_SHOT_SPECIES = [
    "aves with common name bird",
    "Mammalia with common name mammal",
]


def _clip_box_to_image(
    xyxy: list[float],
    image_width: int,
    image_height: int,
    expansion_factor: float,
) -> list[int] | None:
    x1, y1, x2, y2 = xyxy
    width = x2 - x1
    height = y2 - y1
    if width <= 0 or height <= 0:
        return None

    center_x = x1 + (width / 2.0)
    center_y = y1 + (height / 2.0)
    expanded_width = width * expansion_factor
    expanded_height = height * expansion_factor

    clipped_x1 = max(0, int(center_x - (expanded_width / 2.0)))
    clipped_y1 = max(0, int(center_y - (expanded_height / 2.0)))
    clipped_x2 = min(image_width, int(center_x + (expanded_width / 2.0)))
    clipped_y2 = min(image_height, int(center_y + (expanded_height / 2.0)))

    if clipped_x2 <= clipped_x1 or clipped_y2 <= clipped_y1:
        return None
    return [clipped_x1, clipped_y1, clipped_x2, clipped_y2]


def _normalize_prediction_groups(raw: Any, batch_size: int) -> list[list[dict[str, Any]]]:
    empty = [[] for _ in range(batch_size)]
    if raw is None:
        return empty
    if not isinstance(raw, list):
        raise ValueError(f"Unexpected BioCLIP output type: {type(raw)!r}")
    if not raw:
        return empty

    if all(isinstance(item, list) for item in raw):
        grouped = [list(item) for item in raw[:batch_size]]
        if len(grouped) < batch_size:
            grouped.extend([[] for _ in range(batch_size - len(grouped))])
        return grouped

    if all(isinstance(item, dict) for item in raw):
        grouped = [[] for _ in range(batch_size)]
        assigned_any = False
        for entry in raw:
            local_index = entry.get("file_name")
            try:
                local_index = int(local_index)
            except (TypeError, ValueError):
                local_index = None

            if local_index is None:
                if batch_size == 1:
                    grouped[0].append(entry)
                continue

            if 0 <= local_index < batch_size:
                grouped[local_index].append(entry)
                assigned_any = True

        if assigned_any or batch_size == 1:
            return grouped

    raise ValueError("Unable to map BioCLIP predictions back to image crops")


def _format_zero_shot_predictions(
    predictions: list[dict[str, Any]],
    *,
    topk: int,
) -> list[dict[str, float | str]]:
    return sorted(
        (
            {
                "label": str(prediction.get("classification", "")),
                "score": float(prediction.get("score", 0.0)),
            }
            for prediction in predictions
            if isinstance(prediction, dict)
        ),
        key=lambda prediction: prediction["score"],
        reverse=True,
    )[:topk]


class BioClipHelper:
    def __init__(
        self,
        *,
        zero_shot_device: str = "cpu",
        zero_shot_species: list[str] | None = None,
        zero_shot_topk: int = 3,
        batch_size: int = 16,
        crop_expansion_factor: float = 1.0,
        animal_category_names: tuple[str, ...] = ("animal",),
    ) -> None:
        self.zero_shot_device = zero_shot_device
        self.zero_shot_species = zero_shot_species or list(SMARTWILDS_ZERO_SHOT_SPECIES)
        self.zero_shot_topk = zero_shot_topk
        self.batch_size = batch_size
        self.crop_expansion_factor = crop_expansion_factor
        self.animal_category_names = {name.lower() for name in animal_category_names}
        self._zero_shot_classifier = None

    def close(self) -> None:
        self._zero_shot_classifier = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _get_zero_shot_classifier(self):
        if self._zero_shot_classifier is not None:
            return self._zero_shot_classifier

        try:
            from bioclip import CustomLabelsClassifier
        except ImportError as exc:
            raise ImportError(
                "BioCLIP is required for zero-shot classification in this script."
            ) from exc

        self._zero_shot_classifier = CustomLabelsClassifier(
            cls_ary=self.zero_shot_species,
            device=self.zero_shot_device,
        )
        return self._zero_shot_classifier

    def _predict_zero_shot(self, crops: list[Image.Image]) -> list[list[dict[str, Any]]]:
        classifier = self._get_zero_shot_classifier()
        predictions: list[list[dict[str, Any]]] = []

        for start in range(0, len(crops), self.batch_size):
            batch = crops[start:start + self.batch_size]
            try:
                raw = classifier.predict(
                    batch,
                    k=self.zero_shot_topk,
                    batch_size=min(self.batch_size, len(batch)),
                )
                predictions.extend(_normalize_prediction_groups(raw, len(batch)))
            except RuntimeError:
                for crop in batch:
                    raw = classifier.predict([crop], k=self.zero_shot_topk, batch_size=1)
                    predictions.extend(_normalize_prediction_groups(raw, 1))

        return predictions

    def annotate_batch(
        self,
        images: Sequence[Image.Image],
        batch_detections: Sequence[list[dict[str, Any]]],
    ) -> list[list[dict[str, Any]]]:
        if len(images) != len(batch_detections):
            raise ValueError("images and batch_detections must have the same length")

        enriched_batch = [
            [dict(detection) for detection in detections]
            for detections in batch_detections
        ]
        crops: list[Image.Image] = []
        crop_targets: list[tuple[int, int]] = []

        for image_index, (image, detections) in enumerate(zip(images, batch_detections)):
            image_width, image_height = image.size
            for detection_index, detection in enumerate(detections):
                category_name = str(detection.get("category_name", "")).lower()
                if category_name not in self.animal_category_names:
                    continue

                crop_box = _clip_box_to_image(
                    detection["xyxy"],
                    image_width=image_width,
                    image_height=image_height,
                    expansion_factor=self.crop_expansion_factor,
                )
                if crop_box is None:
                    continue

                crop = image.crop(tuple(crop_box))
                if crop.size[0] <= 0 or crop.size[1] <= 0:
                    continue

                crops.append(crop)
                crop_targets.append((image_index, detection_index))

        if not crops:
            return enriched_batch

        zero_shot_predictions = self._predict_zero_shot(crops)
        for (image_index, detection_index), predictions in zip(crop_targets, zero_shot_predictions):
            enriched_batch[image_index][detection_index]["bioclip"] = {
                "zero_shot": {
                    "predictions": _format_zero_shot_predictions(
                        predictions,
                        topk=self.zero_shot_topk,
                    ),
                }
            }

        return enriched_batch

    def annotate_detections(
        self,
        image: Image.Image,
        detections: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return self.annotate_batch([image], [detections])[0]
