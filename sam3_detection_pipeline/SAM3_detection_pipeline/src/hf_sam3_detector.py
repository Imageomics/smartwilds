from __future__ import annotations

"""Hugging Face SAM3 text detector wrapper for SmartWilds."""

from collections.abc import Sequence
import gc
from typing import Any, TypeAlias

import numpy as np
import torch
from PIL import Image
from torchvision.ops import nms

ImageLike: TypeAlias = Image.Image | np.ndarray
Detection: TypeAlias = dict[str, Any]
Detections: TypeAlias = list[Detection]


class HuggingFaceSAM3TextDetector:
    """Run text-guided SAM3 via Hugging Face Transformers."""

    def __init__(
        self,
        *,
        prompts: Sequence[str],
        device: str,
        model_id: str,
        confidence_threshold: float,
        mask_threshold: float,
        nms_iou: float,
        return_masks: bool = False,
    ) -> None:
        if not prompts:
            raise ValueError("prompts must not be empty")

        self.prompts = list(prompts)
        self.device = device
        self.model_id = model_id
        self.confidence_threshold = confidence_threshold
        self.mask_threshold = mask_threshold
        self.nms_iou = nms_iou
        self.return_masks = return_masks
        self.category_id_by_name = {
            prompt: index + 1 for index, prompt in enumerate(self.prompts)
        }

        if self.device == "cuda":
            torch.backends.cudnn.benchmark = True

        try:
            from transformers import Sam3Model, Sam3Processor
        except ImportError as exc:
            raise ImportError(
                "Hugging Face SAM3 inference requires a Transformers install that "
                "provides Sam3Model and Sam3Processor. Activate the intended conda "
                "environment or install/update transformers there."
            ) from exc

        self.model = Sam3Model.from_pretrained(self.model_id).to(self.device)
        self.model.eval()
        self.processor = Sam3Processor.from_pretrained(self.model_id)

    def close(self) -> None:
        del self.model
        del self.processor
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @staticmethod
    def _to_pil_image(image: ImageLike) -> Image.Image:
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        return Image.fromarray(np.asarray(image)).convert("RGB")

    @staticmethod
    def _to_cpu_tensor(value: Any) -> torch.Tensor:
        if isinstance(value, torch.Tensor):
            return value.detach().cpu()
        return torch.as_tensor(value)

    def _post_process(self, outputs: Any, inputs: Any) -> list[dict[str, Any]]:
        original_sizes = inputs.get("original_sizes")
        if isinstance(original_sizes, torch.Tensor):
            target_sizes = original_sizes.detach().cpu().tolist()
        else:
            target_sizes = original_sizes

        return self.processor.post_process_instance_segmentation(
            outputs,
            threshold=self.confidence_threshold,
            mask_threshold=self.mask_threshold,
            target_sizes=target_sizes,
        )

    def _format_prompt_results(
        self,
        result: dict[str, Any],
        prompt: str,
    ) -> Detections:
        boxes = self._to_cpu_tensor(result.get("boxes", torch.empty((0, 4))))
        scores = self._to_cpu_tensor(result.get("scores", torch.empty((0,))))
        masks = result.get("masks")
        mask_tensor = self._to_cpu_tensor(masks) if masks is not None else None

        detections: Detections = []
        for index, (box, score) in enumerate(zip(boxes, scores)):
            detection: Detection = {
                "xyxy": [float(value) for value in box.tolist()],
                "score": float(score.item()),
                "category_id": self.category_id_by_name[prompt],
                "category_name": prompt,
            }
            if self.return_masks and mask_tensor is not None and index < len(mask_tensor):
                detection["mask"] = mask_tensor[index].numpy().astype(bool)
            detections.append(detection)

        return detections

    def _apply_nms(self, detections: Detections) -> Detections:
        if len(detections) <= 1:
            return sorted(detections, key=lambda detection: detection["score"], reverse=True)

        boxes = torch.tensor([detection["xyxy"] for detection in detections], dtype=torch.float32)
        scores = torch.tensor([detection["score"] for detection in detections], dtype=torch.float32)
        keep = nms(boxes, scores, self.nms_iou).tolist()
        filtered = [detections[index] for index in keep]
        filtered.sort(key=lambda detection: detection["score"], reverse=True)
        return filtered

    def detect_batch(self, images: Sequence[ImageLike]) -> list[Detections]:
        if not images:
            return []

        pil_images = [self._to_pil_image(image) for image in images]
        grouped_detections: list[Detections] = [[] for _ in pil_images]

        for prompt in self.prompts:
            inputs = self.processor(
                images=pil_images,
                text=[prompt] * len(pil_images),
                return_tensors="pt",
            ).to(self.device)

            with torch.inference_mode():
                outputs = self.model(**inputs)

            results = self._post_process(outputs, inputs)
            for image_index, result in enumerate(results):
                grouped_detections[image_index].extend(
                    self._format_prompt_results(result, prompt)
                )

            del inputs
            del outputs
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        return [self._apply_nms(detections) for detections in grouped_detections]

    def detect_image(self, image: ImageLike) -> Detections:
        return self.detect_batch([image])[0]
