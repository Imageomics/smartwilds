from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from control_theoretic_policy import ControlTheoreticPolicy

Action = Literal["process", "drop", "defer"]


class Policy(Protocol):
    name: str

    def decide(self, event: dict[str, Any], state: dict[str, Any]) -> Action:
        ...


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"true", "1", "yes"}
    return bool(v)


@dataclass
class ProcessAllPolicy:
    name: str = "process_all"

    def decide(self, event: dict[str, Any], state: dict[str, Any]) -> Action:
        return "process"


@dataclass
class EventTriggeredPolicy:
    name: str = "event_triggered"

    def decide(self, event: dict[str, Any], state: dict[str, Any]) -> Action:
        recipe_step = str(event.get("recipe_step", ""))

        if "interleave(" in recipe_step:
            return "process"
        if "conditional_scale(" in recipe_step:
            return "process"

        high_priority = _as_bool(event.get("high_priority", False))
        positive = _as_bool(event.get("positive", False))
        event_type = str(event.get("event_type", ""))
        is_timelapse = _as_bool(event.get("is_timelapse", False))

        if high_priority or positive or event_type == "motion":
            return "process"
        if is_timelapse:
            return "drop"

        return "drop"


@dataclass
class AdaptivePolicy:
    high_rate_threshold: float = 5000.0
    name: str = "adaptive"

    def decide(self, event: dict[str, Any], state: dict[str, Any]) -> Action:
        modality = str(event.get("modality", ""))
        recipe_step = str(event.get("recipe_step", ""))
        current_rate = float(state.get("current_rate", 0.0))

        if modality in {"camera_trap", "bioacoustic"} and "conditional_scale" not in recipe_step:
            return "process"

        if "conditional_scale" in recipe_step:
            if current_rate > self.high_rate_threshold:
                return "defer"
            return "process"

        if current_rate > self.high_rate_threshold:
            return "defer"

        return "process"


def get_policy(name: str) -> Policy:
    if name == "process_all":
        return ProcessAllPolicy()
    if name == "event_triggered":
        return EventTriggeredPolicy()
    if name == "adaptive":
        return AdaptivePolicy()
    if name == "control_theoretic":
        return ControlTheoreticPolicy()
    raise ValueError(f"Unknown policy: {name}")
