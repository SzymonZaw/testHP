"""Quality metadata for evidence-derived inference and forecasts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class InferenceQuality:
    confidence: float
    uncertainty: float
    observation_count: int
    history_span_days: float
    stability: str
    quality: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def assess_inference_quality(
    snapshots: Iterable[Any],
    now: Optional[datetime] = None,
) -> InferenceQuality:
    """Describe evidence strength without changing the underlying inference."""
    items = list(snapshots)
    if not items:
        return InferenceQuality(0.0, 1.0, 0, 0.0, "unknown", "insufficient", "No inference snapshots are available.")

    confidences = [float(getattr(item.inference, "confidence", 0.0) or 0.0) for item in items]
    confidence = max(0.0, min(1.0, sum(confidences) / len(confidences)))
    uncertainty = 1.0 - confidence
    dates = [item.observed_at for item in items]
    span = max(0.0, (max(dates) - min(dates)).total_seconds() / 86400.0)

    states = [getattr(item.inference, "health_state", "unknown") for item in items]
    stable = len(set(states[-3:])) <= 1
    stability = "high" if stable and len(items) >= 3 else "medium" if len(items) >= 2 else "low"

    if len(items) < 2:
        quality = "insufficient"
        reason = "A single snapshot cannot establish temporal stability."
    elif confidence < 0.5:
        quality = "limited"
        reason = "Inference confidence is low."
    elif confidence < 0.75:
        quality = "moderate"
        reason = "Inference has moderate confidence and should retain uncertainty."
    else:
        quality = "good"
        reason = "Multiple snapshots provide a reasonably consistent evidence base."

    return InferenceQuality(confidence, uncertainty, len(items), span, stability, quality, reason)
