"""Track whether biological-aging deviations persist or change over time."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class TemporalAgingDeviation:
    identifier: str
    observations: int
    first_deviation: Optional[float]
    latest_deviation: Optional[float]
    change: Optional[float]
    slope_per_day: Optional[float]
    direction: str
    persistence: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def analyze_temporal_aging_deviation(
    identifier: str,
    points: Iterable[Dict[str, Any]],
) -> TemporalAgingDeviation:
    """Classify a deviation trajectory without making a clinical decision."""
    ordered: List[Dict[str, Any]] = sorted(
        [p for p in points if p.get("deviation") is not None and p.get("observed_at") is not None],
        key=lambda p: p["observed_at"],
    )
    if not ordered:
        return TemporalAgingDeviation(identifier, 0, None, None, None, None, "unknown", "insufficient", 0.0)

    first = float(ordered[0]["deviation"])
    latest = float(ordered[-1]["deviation"])
    change = latest - first
    confidence = sum(max(0.0, min(1.0, float(p.get("confidence", 0.0)))) for p in ordered) / len(ordered)

    slope = None
    if len(ordered) >= 2:
        start = ordered[0]["observed_at"]
        end = ordered[-1]["observed_at"]
        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace("Z", "+00:00"))
        if isinstance(end, str):
            end = datetime.fromisoformat(end.replace("Z", "+00:00"))
        days = (end - start).total_seconds() / 86400.0
        slope = change / days if days > 0 else None

    if len(ordered) < 2 or confidence < 0.5:
        direction = "unknown" if len(ordered) < 2 else "uncertain"
        persistence = "insufficient"
    else:
        direction = "increasing" if change > 0.5 else "decreasing" if change < -0.5 else "stable"
        persistence = "persistent" if abs(latest) >= 5.0 and abs(first) >= 5.0 else "transient"

    return TemporalAgingDeviation(
        identifier, len(ordered), first, latest, change, slope, direction, persistence, confidence
    )
