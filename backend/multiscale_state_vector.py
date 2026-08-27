from __future__ import annotations

"""Canonical observational state vector for the hand digital twin.

This module intentionally stays below diagnosis and intervention logic. It
turns evidence-backed multiscale trend/attention records into a stable,
serializable read model for later analytics and ML.
"""

from dataclasses import dataclass
from typing import Any, Iterable


_LEVEL_ORDER = {"cell": 0, "tissue": 1, "anatomy": 2, "hand": 3}


@dataclass(frozen=True)
class MultiscaleStateLevel:
    level: str
    object_count: int
    changed_objects: int
    mean_age_delta: float | None
    status: str
    attention_score: float | None
    confidence: float | None
    source_cell_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "object_count": self.object_count,
            "changed_objects": self.changed_objects,
            "mean_age_delta": self.mean_age_delta,
            "status": self.status,
            "attention_score": self.attention_score,
            "confidence": self.confidence,
            "source_cell_ids": list(self.source_cell_ids),
        }


@dataclass(frozen=True)
class MultiscaleStateVector:
    subject_id: str
    hand_id: str
    timepoint_id: str
    overall_status: str
    levels: tuple[MultiscaleStateLevel, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "hand_id": self.hand_id,
            "timepoint_id": self.timepoint_id,
            "overall_status": self.overall_status,
            "levels": [level.to_dict() for level in self.levels],
        }


def _status(items: list[dict[str, Any]]) -> str:
    if not items:
        return "insufficient_observation"
    if any(item.get("status") in {"attention", "high_attention"} for item in items):
        return "attention"
    if any(item.get("status") in {"observed_change", "stable_observation", "monitor"} for item in items):
        return "observed"
    return "insufficient_observation"


def _confidence(items: list[dict[str, Any]]) -> float | None:
    values = [
        float(item["confidence"])
        for item in items
        if isinstance(item.get("confidence"), (int, float))
        and not isinstance(item.get("confidence"), bool)
        and 0.0 <= float(item["confidence"]) <= 1.0
    ]
    return sum(values) / len(values) if values else None


def build_multiscale_state_vector(
    *,
    subject_id: str,
    hand_id: str,
    timepoint_id: str,
    trends: Iterable[dict[str, Any]],
    attention: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Build one deterministic observational state vector across all scales.

    ``trends`` are the evidence-backed measurements. ``attention`` is a
    derived prioritisation signal and never changes the underlying trend.
    Missing levels remain absent rather than being filled with synthetic
    zeroes.
    """
    trend_rows = [dict(item) for item in trends]
    attention_rows = [dict(item) for item in attention]

    levels: list[MultiscaleStateLevel] = []
    for level in ("cell", "tissue", "anatomy", "hand"):
        rows = [item for item in trend_rows if item.get("level", "cell") == level]
        if not rows:
            continue
        level_attention = [item for item in attention_rows if item.get("level") == level]
        observed = [
            item.get("mean_delta", item.get("delta"))
            for item in rows
            if isinstance(item.get("mean_delta", item.get("delta")), (int, float))
            and not isinstance(item.get("mean_delta", item.get("delta")), bool)
        ]
        deltas = [float(value) for value in observed]
        counts = [int(item.get("cell_count", 0) or 0) for item in rows]
        changed = [int(item.get("changed_cells", 0) or 0) for item in rows]
        source_ids = sorted({
            str(cell_id)
            for item in rows
            for cell_id in item.get("source_cell_ids", ())
            if cell_id
        })
        scores = [
            float(item["score"])
            for item in level_attention
            if isinstance(item.get("score"), (int, float)) and not isinstance(item.get("score"), bool)
        ]
        levels.append(
            MultiscaleStateLevel(
                level=level,
                object_count=sum(counts),
                changed_objects=sum(changed),
                mean_age_delta=(sum(deltas) / len(deltas)) if deltas else None,
                status=_status(rows),
                attention_score=max(scores) if scores else None,
                confidence=_confidence(rows),
                source_cell_ids=tuple(source_ids),
            )
        )

    overall = "insufficient_observation"
    if levels:
        statuses = {level.status for level in levels}
        if "attention" in statuses:
            overall = "attention"
        elif "observed" in statuses:
            overall = "observed"

    return MultiscaleStateVector(
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        overall_status=overall,
        levels=tuple(sorted(levels, key=lambda item: _LEVEL_ORDER[item.level])),
    ).to_dict()
