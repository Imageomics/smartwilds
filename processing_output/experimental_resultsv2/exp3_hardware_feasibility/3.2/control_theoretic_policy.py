from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Action = Literal["process", "drop", "defer"]


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"true", "1", "yes"}
    return bool(v)


@dataclass
class ControlTheoreticPolicy:
    # Minimal aggregate-state controller parameters from Yuanyang's Exp 4 code.
    a: float = 0.93
    b: float = 0.9
    kh: float = 0.04
    u0: float = 0.50
    target_x: float = 9.0
    name: str = "control_theoretic"

    def decide(self, event: dict[str, Any], state: dict[str, Any]) -> Action:
        x = float(state.get("x", 0.0))

        modality = str(event.get("modality", ""))
        recipe_step = str(event.get("recipe_step", ""))
        event_type = str(event.get("event_type", ""))

        high_priority = _as_bool(event.get("high_priority", False))
        positive = _as_bool(event.get("positive", False))
        confidence = float(event.get("confidence", 0.0) or 0.0)

        d = 1.0
        if modality == "drone":
            d = 2.0
        elif modality in {"camera_trap", "camera_traps"}:
            d = 1.0
        elif modality in {"bioacoustic", "acoustic"}:
            d = 0.8

        if "interleave" in recipe_step or "conditional_scale" in recipe_step:
            d += 0.5
        if high_priority or positive or event_type == "motion" or confidence >= 0.8:
            d += 0.5

        u = self.kh * (x - self.target_x) + self.u0
        u = max(0.0, min(1.0, u))

        if "conditional_scale" in recipe_step:
            if u >= 0.85:
                action = "process"
                effort = 1.0
            elif u >= 0.35:
                action = "defer"
                effort = 0.5
            else:
                action = "drop"
                effort = 0.0
        elif "interleave" in recipe_step or modality == "drone":
            if u >= 0.70:
                action = "process"
                effort = 1.0
            elif u >= 0.20:
                action = "defer"
                effort = 0.5
            else:
                action = "drop"
                effort = 0.0
        elif modality in {"camera_trap", "bioacoustic"}:
            action = "process"
            effort = 1.0
        elif high_priority or positive or event_type == "motion":
            action = "process"
            effort = 1.0
        elif u >= 0.20:
            action = "defer"
            effort = 0.5
        else:
            action = "drop"
            effort = 0.0

        x_next = self.a * x + d - self.b * effort
        state["x"] = max(0.0, x_next)
        return action
