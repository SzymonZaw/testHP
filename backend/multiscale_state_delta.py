from __future__ import annotations

"""Longitudinal comparison of multiscale digital-twin state vectors.

This layer compares already-derived observational snapshots. It does not infer
clinical meaning, fill missing observations, or reorder user-supplied history.
"""

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class MultiscaleStateDelta:
    from_timepoint_id: str
    to_timepoint_id: str
    level: str
    object_count_delta: int
    changed_objects_delta: int
    mean_age_delta_change: float | None
    attention_score_change: float | None
    confidence_change: float | None
    status_from: str
    status_to: str
    source_cell_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_timepoint_id": self.from_timepoint_id,
            "to_timepoint_id": self.to_timepoint_id,
            "level": self.level,
            "object_count_delta": self.object_count_delta,
            "changed_objects_delta": self.changed_objects_delta,
            "mean_age_delta_change": self.mean_age_delta_change,
            "attention_score_change": self.attention_score_change,
            "confidence_change": self.confidence_change,
            "status_from": self.status_from,
            "status_to": self.status_to,
            "source_cell_ids": list(self.source_cell_ids),
        }


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _difference(current: Any, previous: Any) -> float | None:
    current_number = _number(current)
    previous_number = _number(previous)
    if current_number is None or previous_number is None:
        return None
    return current_number - previous_number


def _levels(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in snapshot.get("levels", ()):
        if not isinstance(item, dict):
            raise TypeError("state vector levels must be dictionaries")
        level = item.get("level")
        if not level:
            raise ValueError("state vector level is required")
        if level in result:
            raise ValueError(f"duplicate state vector level: {level}")
        result[str(level)] = item
    return result


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict):
        raise TypeError("state vectors must be dictionaries")
    for field in ("subject_id", "hand_id", "timepoint_id"):
        if not snapshot.get(field):
            raise ValueError(f"state vector {field} is required")
    _levels(snapshot)


def compare_multiscale_state_vectors(
    snapshots: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return adjacent longitudinal deltas for shared observed levels.

    Snapshots are compared in the order supplied. At least two snapshots are
    required. Levels absent from either endpoint are skipped instead of being
    represented by fabricated zeroes. This keeps the result faithful to the
    available observations.
    """
    history = list(snapshots)
    if len(history) < 2:
        raise ValueError("at least two state vectors are required")

    for snapshot in history:
        _validate_snapshot(snapshot)

    first = history[0]
    subject_id = first["subject_id"]
    hand_id = first["hand_id"]
    seen_timepoints: set[str] = set()
    for snapshot in history:
        if snapshot["subject_id"] != subject_id or snapshot["hand_id"] != hand_id:
            raise ValueError("state vector history must share subject and hand identity")
        timepoint_id = str(snapshot["timepoint_id"])
        if timepoint_id in seen_timepoints:
            raise ValueError("state vector history cannot contain duplicate timepoints")
        seen_timepoints.add(timepoint_id)

    deltas: list[MultiscaleStateDelta] = []
    for previous, current in zip(history, history[1:]):
        previous_levels = _levels(previous)
        current_levels = _levels(current)
        for level in sorted(set(previous_levels) & set(current_levels)):
            before = previous_levels[level]
            after = current_levels[level]
            before_ids = {str(item) for item in before.get("source_cell_ids", ()) if item}
            after_ids = {str(item) for item in after.get("source_cell_ids", ()) if item}
            deltas.append(
                MultiscaleStateDelta(
                    from_timepoint_id=str(previous["timepoint_id"]),
                    to_timepoint_id=str(current["timepoint_id"]),
                    level=level,
                    object_count_delta=int(after.get("object_count", 0) or 0)
                    - int(before.get("object_count", 0) or 0),
                    changed_objects_delta=int(after.get("changed_objects", 0) or 0)
                    - int(before.get("changed_objects", 0) or 0),
                    mean_age_delta_change=_difference(
                        after.get("mean_age_delta"), before.get("mean_age_delta")
                    ),
                    attention_score_change=_difference(
                        after.get("attention_score"), before.get("attention_score")
                    ),
                    confidence_change=_difference(
                        after.get("confidence"), before.get("confidence")
                    ),
                    status_from=str(before.get("status", "insufficient_observation")),
                    status_to=str(after.get("status", "insufficient_observation")),
                    source_cell_ids=tuple(sorted(before_ids | after_ids)),
                )
            )

    return [item.to_dict() for item in deltas]
