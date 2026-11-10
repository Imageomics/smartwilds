#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gc
import json
import math
import os
from pathlib import Path
import platform
import random
import resource
import socket
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any

from PIL import Image, UnidentifiedImageError
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bioclip_helper import BioClipHelper  # noqa: E402
from hf_sam3_detector import HuggingFaceSAM3TextDetector  # noqa: E402


DEFAULT_MODEL_ID = "facebook/sam3"
DEFAULT_PROMPTS = ["animal", "person", "vehicle"]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.fmean(values))


def _safe_stdev(values: list[float]) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    return float(statistics.pstdev(values))


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * (percentile / 100.0)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return float(ordered[lower])
    lower_value = ordered[lower]
    upper_value = ordered[upper]
    weight = rank - lower
    return float(lower_value + ((upper_value - lower_value) * weight))


def _summarize_series(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "min": None,
            "mean": None,
            "std": None,
            "p50": None,
            "p90": None,
            "p95": None,
            "max": None,
        }
    return {
        "count": len(values),
        "min": float(min(values)),
        "mean": _safe_mean(values),
        "std": _safe_stdev(values),
        "p50": _percentile(values, 50.0),
        "p90": _percentile(values, 90.0),
        "p95": _percentile(values, 95.0),
        "max": float(max(values)),
    }


def _read_proc_status_mb(key: str) -> float | None:
    status_path = Path("/proc/self/status")
    if not status_path.exists():
        return None
    try:
        with status_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.startswith(f"{key}:"):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    return None
                return float(parts[1]) / 1024.0
    except OSError:
        return None
    return None


def _max_rss_mb() -> float | None:
    try:
        return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0
    except (AttributeError, ValueError):
        return None


def _get_cuda_device_name(device: str) -> str | None:
    if not str(device).startswith("cuda") or not torch.cuda.is_available():
        return None
    try:
        return str(torch.cuda.get_device_name(0))
    except RuntimeError:
        return None


def _synchronize(device: str) -> None:
    if str(device).startswith("cuda") and torch.cuda.is_available():
        torch.cuda.synchronize()


def _torch_cuda_memory_stats() -> dict[str, float | None]:
    if not torch.cuda.is_available():
        return {
            "allocated_mb": None,
            "reserved_mb": None,
            "max_allocated_mb": None,
            "max_reserved_mb": None,
        }
    return {
        "allocated_mb": torch.cuda.memory_allocated() / (1024.0 ** 2),
        "reserved_mb": torch.cuda.memory_reserved() / (1024.0 ** 2),
        "max_allocated_mb": torch.cuda.max_memory_allocated() / (1024.0 ** 2),
        "max_reserved_mb": torch.cuda.max_memory_reserved() / (1024.0 ** 2),
    }


class NvidiaSmiMonitor:
    def __init__(self, interval_s: float) -> None:
        self.interval_s = interval_s
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._samples: list[dict[str, Any]] = []

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=max(2.0, self.interval_s + 1.0))

    def _run(self) -> None:
        while not self._stop_event.is_set():
            sample = self._query_nvidia_smi()
            if sample is not None:
                self._samples.append(sample)
            self._stop_event.wait(self.interval_s)

    @staticmethod
    def _query_nvidia_smi() -> dict[str, Any] | None:
        command = [
            "nvidia-smi",
            "--query-gpu=index,name,utilization.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ]
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            return None

        rows = []
        for line in completed.stdout.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) != 5:
                continue
            try:
                rows.append(
                    {
                        "gpu_index": int(parts[0]),
                        "gpu_name": parts[1],
                        "utilization_gpu_pct": float(parts[2]),
                        "memory_used_mb": float(parts[3]),
                        "memory_total_mb": float(parts[4]),
                    }
                )
            except ValueError:
                continue

        if not rows:
            return None

        first = rows[0]
        return {
            "gpu_index": first["gpu_index"],
            "gpu_name": first["gpu_name"],
            "utilization_gpu_pct": first["utilization_gpu_pct"],
            "memory_used_mb": first["memory_used_mb"],
            "memory_total_mb": first["memory_total_mb"],
            "gpu_count": len(rows),
            "captured_at": _iso_now(),
        }

    def summary(self) -> dict[str, Any]:
        if not self._samples:
            return {
                "sample_count": 0,
                "gpu_name": None,
                "gpu_count": None,
                "avg_utilization_gpu_pct": None,
                "peak_utilization_gpu_pct": None,
                "avg_memory_used_mb": None,
                "peak_memory_used_mb": None,
                "memory_total_mb": None,
            }

        utilization = [sample["utilization_gpu_pct"] for sample in self._samples]
        memory_used = [sample["memory_used_mb"] for sample in self._samples]
        last = self._samples[-1]
        return {
            "sample_count": len(self._samples),
            "gpu_name": last["gpu_name"],
            "gpu_count": last["gpu_count"],
            "avg_utilization_gpu_pct": _safe_mean(utilization),
            "peak_utilization_gpu_pct": max(utilization),
            "avg_memory_used_mb": _safe_mean(memory_used),
            "peak_memory_used_mb": max(memory_used),
            "memory_total_mb": last["memory_total_mb"],
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark one SAM3 drone folder or COCO image list.",
    )
    parser.add_argument("--coco-json", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--tag", default=None)
    parser.add_argument("--max-images", type=int, default=100)
    parser.add_argument("--sample-mode", choices=("first", "random"), default="first")
    parser.add_argument("--sample-stride", type=int, default=1)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--warmup-batches", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--prompts", nargs="+", default=list(DEFAULT_PROMPTS))
    parser.add_argument("--confidence-threshold", type=float, default=0.5)
    parser.add_argument("--mask-threshold", type=float, default=0.5)
    parser.add_argument("--nms-iou", type=float, default=0.5)
    parser.add_argument("--return-masks", action="store_true")
    parser.add_argument("--enable-bioclip", action="store_true")
    parser.add_argument("--bioclip-device", default=None)
    parser.add_argument("--bioclip-batch-size", type=int, default=None)
    parser.add_argument("--gpu-poll-interval-s", type=float, default=1.0)
    return parser.parse_args()


def _load_coco_records(coco_json: Path, image_root: Path) -> tuple[dict[str, Any], list[tuple[dict[str, Any], Path]]]:
    with coco_json.open("r", encoding="utf-8") as handle:
        coco = json.load(handle)

    records: list[tuple[dict[str, Any], Path]] = []
    for image_info in coco.get("images", []):
        image_path = image_root / image_info["file_name"]
        if image_path.exists():
            records.append((image_info, image_path))
    return coco, records


def _sample_records(
    records: list[tuple[dict[str, Any], Path]],
    *,
    sample_stride: int,
    max_images: int | None,
    sample_mode: str,
    random_seed: int,
) -> list[tuple[dict[str, Any], Path]]:
    filtered = records[::sample_stride]
    if max_images is None or max_images <= 0 or len(filtered) <= max_images:
        return filtered

    if sample_mode == "random":
        rng = random.Random(random_seed)
        selected_indices = sorted(rng.sample(range(len(filtered)), k=max_images))
        return [filtered[index] for index in selected_indices]

    return filtered[:max_images]


def _profile_detect_batch(
    detector: HuggingFaceSAM3TextDetector,
    images: list[Image.Image],
) -> tuple[list[list[dict[str, Any]]], dict[str, Any]]:
    pil_images = [detector._to_pil_image(image) for image in images]
    grouped_detections: list[list[dict[str, Any]]] = [[] for _ in pil_images]
    prompt_records: list[dict[str, float | str]] = []

    prompt_processor_total_s = 0.0
    prompt_to_device_total_s = 0.0
    prompt_model_total_s = 0.0
    prompt_postprocess_total_s = 0.0
    prompt_format_total_s = 0.0

    for prompt in detector.prompts:
        prompt_start = time.perf_counter()
        processor_start = prompt_start
        inputs = detector.processor(
            images=pil_images,
            text=[prompt] * len(pil_images),
            return_tensors="pt",
        )
        processor_end = time.perf_counter()

        inputs = inputs.to(detector.device)
        _synchronize(detector.device)
        to_device_end = time.perf_counter()

        with torch.inference_mode():
            outputs = detector.model(**inputs)
        _synchronize(detector.device)
        model_end = time.perf_counter()

        results = detector._post_process(outputs, inputs)
        postprocess_end = time.perf_counter()

        for image_index, result in enumerate(results):
            grouped_detections[image_index].extend(
                detector._format_prompt_results(result, prompt)
            )
        format_end = time.perf_counter()

        processor_s = processor_end - processor_start
        to_device_s = to_device_end - processor_end
        model_s = model_end - to_device_end
        postprocess_s = postprocess_end - model_end
        format_s = format_end - postprocess_end

        prompt_processor_total_s += processor_s
        prompt_to_device_total_s += to_device_s
        prompt_model_total_s += model_s
        prompt_postprocess_total_s += postprocess_s
        prompt_format_total_s += format_s

        prompt_records.append(
            {
                "prompt": prompt,
                "processor_s": processor_s,
                "to_device_s": to_device_s,
                "model_s": model_s,
                "postprocess_s": postprocess_s,
                "format_s": format_s,
                "prompt_total_s": format_end - prompt_start,
            }
        )

        del inputs
        del outputs
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    nms_start = time.perf_counter()
    final_detections = [detector._apply_nms(detections) for detections in grouped_detections]
    nms_end = time.perf_counter()

    return final_detections, {
        "prompt_timings": prompt_records,
        "prompt_processor_total_s": prompt_processor_total_s,
        "prompt_to_device_total_s": prompt_to_device_total_s,
        "prompt_model_total_s": prompt_model_total_s,
        "prompt_postprocess_total_s": prompt_postprocess_total_s,
        "prompt_format_total_s": prompt_format_total_s,
        "nms_s": nms_end - nms_start,
        "sam3_total_s": (
            prompt_processor_total_s
            + prompt_to_device_total_s
            + prompt_model_total_s
            + prompt_postprocess_total_s
            + prompt_format_total_s
            + (nms_end - nms_start)
        ),
    }


def _count_detections(batch_detections: list[list[dict[str, Any]]]) -> tuple[int, int]:
    total = 0
    animals = 0
    for detections in batch_detections:
        total += len(detections)
        animals += sum(
            1
            for detection in detections
            if str(detection.get("category_name", "")).lower() == "animal"
        )
    return total, animals


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _write_batch_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


def _write_per_image_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = _parse_args()

    if args.batch_size <= 0:
        raise ValueError("--batch-size must be greater than 0")
    if args.sample_stride <= 0:
        raise ValueError("--sample-stride must be greater than 0")
    if args.max_images is not None and args.max_images == 0:
        raise ValueError("--max-images must be positive or omitted")

    coco_json = Path(args.coco_json)
    image_root = Path(args.image_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark_id = args.tag or f"{image_root.name}_bs{args.batch_size}"
    bioclip_device = args.bioclip_device or ("cpu" if str(args.device).startswith("cuda") else args.device)
    bioclip_batch_size = args.bioclip_batch_size or (1 if str(bioclip_device).startswith("cuda") else 16)

    coco, all_records = _load_coco_records(coco_json, image_root)
    benchmark_records = _sample_records(
        all_records,
        sample_stride=args.sample_stride,
        max_images=args.max_images,
        sample_mode=args.sample_mode,
        random_seed=args.random_seed,
    )

    if not benchmark_records:
        raise RuntimeError("No benchmark records were selected")

    started_at = _iso_now()
    monitor = None
    if str(args.device).startswith("cuda"):
        monitor = NvidiaSmiMonitor(interval_s=args.gpu_poll_interval_s)
        monitor.start()

    rss_before_model_mb = _read_proc_status_mb("VmRSS")
    model_init_start = time.perf_counter()
    detector = HuggingFaceSAM3TextDetector(
        prompts=args.prompts,
        device=args.device,
        model_id=args.model_id,
        confidence_threshold=args.confidence_threshold,
        mask_threshold=args.mask_threshold,
        nms_iou=args.nms_iou,
        return_masks=args.return_masks,
    )
    _synchronize(args.device)
    model_init_end = time.perf_counter()
    rss_after_model_mb = _read_proc_status_mb("VmRSS")

    bioclip_helper = None
    bioclip_init_s = 0.0
    if args.enable_bioclip:
        bioclip_init_start = time.perf_counter()
        bioclip_helper = BioClipHelper(
            zero_shot_device=bioclip_device,
            batch_size=bioclip_batch_size,
        )
        bioclip_init_s = time.perf_counter() - bioclip_init_start

    if torch.cuda.is_available() and str(args.device).startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()

    warmup_total_s = 0.0
    if args.warmup_batches > 0:
        warmup_records = benchmark_records[: min(len(benchmark_records), args.warmup_batches * args.batch_size)]
        if warmup_records:
            warmup_images = []
            for _, image_path in warmup_records:
                with Image.open(image_path) as opened_image:
                    warmup_images.append(opened_image.convert("RGB"))
            warmup_start = time.perf_counter()
            detections, _ = _profile_detect_batch(detector, warmup_images)
            if bioclip_helper is not None:
                detections = bioclip_helper.annotate_batch(warmup_images, detections)
            _ = detections
            warmup_total_s = time.perf_counter() - warmup_start
            del warmup_images
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    batch_records: list[dict[str, Any]] = []
    per_image_rows: list[dict[str, Any]] = []

    batch_wall_series: list[float] = []
    batch_image_read_series: list[float] = []
    batch_sam3_series: list[float] = []
    batch_bioclip_series: list[float] = []
    batch_prompt_processor_series: list[float] = []
    batch_prompt_to_device_series: list[float] = []
    batch_prompt_model_series: list[float] = []
    batch_prompt_postprocess_series: list[float] = []
    batch_prompt_format_series: list[float] = []
    batch_nms_series: list[float] = []
    per_image_total_series: list[float] = []
    per_image_sam3_series: list[float] = []

    total_detections = 0
    total_animal_detections = 0
    unreadable_images = 0
    processed_images = 0

    benchmark_wall_start = time.perf_counter()
    try:
        for batch_index, start in enumerate(range(0, len(benchmark_records), args.batch_size)):
            selected_records = benchmark_records[start:start + args.batch_size]
            valid_records: list[tuple[dict[str, Any], Path]] = []
            batch_images: list[Image.Image] = []

            if torch.cuda.is_available() and str(args.device).startswith("cuda"):
                torch.cuda.reset_peak_memory_stats()

            batch_start = time.perf_counter()
            image_read_start = batch_start
            for image_info, image_path in selected_records:
                try:
                    with Image.open(image_path) as opened_image:
                        batch_images.append(opened_image.convert("RGB"))
                    valid_records.append((image_info, image_path))
                except (OSError, UnidentifiedImageError):
                    unreadable_images += 1
            image_read_end = time.perf_counter()

            if not batch_images:
                continue

            sam3_start = image_read_end
            batch_sam_detections, sam3_breakdown = _profile_detect_batch(detector, batch_images)
            sam3_end = time.perf_counter()

            bioclip_s = 0.0
            batch_detections = batch_sam_detections
            if bioclip_helper is not None:
                bioclip_start = time.perf_counter()
                batch_detections = bioclip_helper.annotate_batch(batch_images, batch_sam_detections)
                bioclip_s = time.perf_counter() - bioclip_start

            batch_end = time.perf_counter()

            batch_total_detections, batch_animal_detections = _count_detections(batch_detections)
            total_detections += batch_total_detections
            total_animal_detections += batch_animal_detections
            processed_images += len(valid_records)

            batch_wall_s = batch_end - batch_start
            image_read_s = image_read_end - image_read_start
            sam3_total_s = sam3_end - sam3_start
            per_image_total_s = batch_wall_s / len(valid_records)
            per_image_sam3_s = sam3_total_s / len(valid_records)

            batch_wall_series.append(batch_wall_s)
            batch_image_read_series.append(image_read_s)
            batch_sam3_series.append(sam3_total_s)
            batch_bioclip_series.append(bioclip_s)
            batch_prompt_processor_series.append(sam3_breakdown["prompt_processor_total_s"])
            batch_prompt_to_device_series.append(sam3_breakdown["prompt_to_device_total_s"])
            batch_prompt_model_series.append(sam3_breakdown["prompt_model_total_s"])
            batch_prompt_postprocess_series.append(sam3_breakdown["prompt_postprocess_total_s"])
            batch_prompt_format_series.append(sam3_breakdown["prompt_format_total_s"])
            batch_nms_series.append(sam3_breakdown["nms_s"])
            per_image_total_series.extend([per_image_total_s] * len(valid_records))
            per_image_sam3_series.extend([per_image_sam3_s] * len(valid_records))

            cuda_stats = _torch_cuda_memory_stats()
            batch_record = {
                "batch_index": batch_index,
                "start_image_index": start,
                "batch_size": len(valid_records),
                "image_read_s": image_read_s,
                "sam3_total_s": sam3_total_s,
                "bioclip_s": bioclip_s,
                "batch_wall_s": batch_wall_s,
                "per_image_total_s_approx": per_image_total_s,
                "per_image_sam3_s_approx": per_image_sam3_s,
                "num_detections": batch_total_detections,
                "num_animal_detections": batch_animal_detections,
                "prompt_processor_total_s": sam3_breakdown["prompt_processor_total_s"],
                "prompt_to_device_total_s": sam3_breakdown["prompt_to_device_total_s"],
                "prompt_model_total_s": sam3_breakdown["prompt_model_total_s"],
                "prompt_postprocess_total_s": sam3_breakdown["prompt_postprocess_total_s"],
                "prompt_format_total_s": sam3_breakdown["prompt_format_total_s"],
                "nms_s": sam3_breakdown["nms_s"],
                "torch_cuda_allocated_mb": cuda_stats["allocated_mb"],
                "torch_cuda_reserved_mb": cuda_stats["reserved_mb"],
                "torch_cuda_max_allocated_mb": cuda_stats["max_allocated_mb"],
                "torch_cuda_max_reserved_mb": cuda_stats["max_reserved_mb"],
                "image_files": [str(image_path) for _, image_path in valid_records],
                "prompt_timings": sam3_breakdown["prompt_timings"],
            }
            batch_records.append(batch_record)

            for (image_info, image_path), detections in zip(valid_records, batch_detections):
                per_image_rows.append(
                    {
                        "benchmark_id": benchmark_id,
                        "batch_index": batch_index,
                        "image_id": image_info.get("id"),
                        "file_name": image_info.get("file_name"),
                        "image_path": str(image_path),
                        "approx_total_latency_s": per_image_total_s,
                        "approx_sam3_latency_s": per_image_sam3_s,
                        "num_detections": len(detections),
                        "num_animal_detections": sum(
                            1
                            for detection in detections
                            if str(detection.get("category_name", "")).lower() == "animal"
                        ),
                    }
                )

            del batch_images
            del batch_sam_detections
            del batch_detections
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    finally:
        benchmark_wall_s = time.perf_counter() - benchmark_wall_start
        if bioclip_helper is not None:
            bioclip_helper.close()
        detector.close()
        if monitor is not None:
            monitor.stop()

    finished_at = _iso_now()
    gpu_monitor_summary = monitor.summary() if monitor is not None else {
        "sample_count": 0,
        "gpu_name": None,
        "gpu_count": None,
        "avg_utilization_gpu_pct": None,
        "peak_utilization_gpu_pct": None,
        "avg_memory_used_mb": None,
        "peak_memory_used_mb": None,
        "memory_total_mb": None,
    }
    overall_cuda_stats = _torch_cuda_memory_stats()

    summary = {
        "benchmark_id": benchmark_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "device": args.device,
            "cuda_device_name": _get_cuda_device_name(args.device),
        },
        "config": {
            "coco_json": str(coco_json),
            "image_root": str(image_root),
            "output_dir": str(output_dir),
            "tag": args.tag,
            "max_images": args.max_images,
            "sample_mode": args.sample_mode,
            "sample_stride": args.sample_stride,
            "random_seed": args.random_seed,
            "warmup_batches": args.warmup_batches,
            "batch_size": args.batch_size,
            "model_id": args.model_id,
            "prompts": list(args.prompts),
            "confidence_threshold": args.confidence_threshold,
            "mask_threshold": args.mask_threshold,
            "nms_iou": args.nms_iou,
            "return_masks": args.return_masks,
            "enable_bioclip": args.enable_bioclip,
            "bioclip_device": bioclip_device if args.enable_bioclip else None,
            "bioclip_batch_size": bioclip_batch_size if args.enable_bioclip else None,
        },
        "dataset": {
            "num_images_in_coco": len(coco.get("images", [])),
            "num_existing_images": len(all_records),
            "num_benchmarked_images": processed_images,
            "unreadable_images": unreadable_images,
        },
        "timings": {
            "model_init_s": model_init_end - model_init_start,
            "bioclip_init_s": bioclip_init_s,
            "warmup_total_s": warmup_total_s,
            "benchmark_wall_s": benchmark_wall_s,
            "images_per_second": (
                (processed_images / benchmark_wall_s) if benchmark_wall_s > 0 else None
            ),
            "batches_per_second": (
                (len(batch_records) / benchmark_wall_s) if benchmark_wall_s > 0 else None
            ),
            "total_image_read_s": sum(batch_image_read_series),
            "total_sam3_s": sum(batch_sam3_series),
            "total_bioclip_s": sum(batch_bioclip_series),
            "total_prompt_processor_s": sum(batch_prompt_processor_series),
            "total_prompt_to_device_s": sum(batch_prompt_to_device_series),
            "total_prompt_model_s": sum(batch_prompt_model_series),
            "total_prompt_postprocess_s": sum(batch_prompt_postprocess_series),
            "total_prompt_format_s": sum(batch_prompt_format_series),
            "total_nms_s": sum(batch_nms_series),
        },
        "latency_stats": {
            "batch_wall_s": _summarize_series(batch_wall_series),
            "batch_image_read_s": _summarize_series(batch_image_read_series),
            "batch_sam3_s": _summarize_series(batch_sam3_series),
            "batch_bioclip_s": _summarize_series(batch_bioclip_series),
            "per_image_total_s": _summarize_series(per_image_total_series),
            "per_image_sam3_s": _summarize_series(per_image_sam3_series),
        },
        "counts": {
            "num_batches": len(batch_records),
            "num_detections": total_detections,
            "num_animal_detections": total_animal_detections,
            "mean_detections_per_image": (
                total_detections / processed_images if processed_images > 0 else None
            ),
        },
        "resources": {
            "process_rss_mb_before_model": rss_before_model_mb,
            "process_rss_mb_after_model": rss_after_model_mb,
            "process_rss_mb_final": _read_proc_status_mb("VmRSS"),
            "process_max_rss_mb": _max_rss_mb(),
            "torch_cuda_allocated_mb_final": overall_cuda_stats["allocated_mb"],
            "torch_cuda_reserved_mb_final": overall_cuda_stats["reserved_mb"],
            "torch_cuda_peak_allocated_mb": overall_cuda_stats["max_allocated_mb"],
            "torch_cuda_peak_reserved_mb": overall_cuda_stats["max_reserved_mb"],
            "nvidia_smi": gpu_monitor_summary,
        },
    }

    _write_json(output_dir / "summary.json", summary)
    _write_batch_records(output_dir / "batch_records.jsonl", batch_records)
    _write_per_image_csv(output_dir / "per_image_latency.csv", per_image_rows)

    print(f"Benchmark complete: {benchmark_id}")
    print(f"Summary JSON: {output_dir / 'summary.json'}")
    print(f"Batch records: {output_dir / 'batch_records.jsonl'}")
    print(f"Per-image CSV: {output_dir / 'per_image_latency.csv'}")
    print(f"Images processed: {processed_images}")
    print(f"Throughput (images/s): {summary['timings']['images_per_second']}")
    print(f"P95 per-image latency (s): {summary['latency_stats']['per_image_total_s']['p95']}")


if __name__ == "__main__":
    main()
