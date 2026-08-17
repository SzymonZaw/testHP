from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class LongitudinalChange:
    subject_id: str
    zone: str
    metric: str
    timepoints: list[str]
    values: list[float]
    delta: float | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "zone": self.zone,
            "metric": self.metric,
            "timepoints": self.timepoints,
            "values": self.values,
            "delta": self.delta,
            "status": self.status,
        }


def compare_observations(subject_id: str, observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare numeric observations by zone/metric across timepoints.

    Only observations with explicit numeric values are compared. Missing data are
    represented as unavailable rather than interpreted as normal.
    """
    groups: dict[tuple[str, str], list[tuple[str, float]]] = {}
    for obs in observations:
        zone = str(obs.get("zone") or obs.get("zone_id") or "unknown")
        metric = str(obs.get("metric") or "unknown")
        value = obs.get("value")
        timepoint = str(obs.get("timepoint") or "unknown")
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and timepoint != "unknown":
            groups.setdefault((zone, metric), []).append((timepoint, float(value)))

    results: list[dict[str, Any]] = []
    order_key = lambda item: (item[0], item[1])
    for (zone, metric), values in sorted(groups.items()):
        values.sort(key=order_key)
        timepoints = [x[0] for x in values]
        numeric = [x[1] for x in values]
        delta = round(numeric[-1] - numeric[0], 12) if len(numeric) >= 2 else None
        results.append(LongitudinalChange(
            subject_id=subject_id,
            zone=zone,
            metric=metric,
            timepoints=timepoints,
            values=numeric,
            delta=delta,
            status="observed_change" if delta is not None and delta != 0 else ("stable_observation" if delta == 0 else "insufficient_timepoints"),
        ).to_dict())
    return results


def load_longitudinal_records(root: Path, subject_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")) if root.exists() else []:
        try:
            import json
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = payload if isinstance(payload, list) else payload.get("observations", []) if isinstance(payload, dict) else []
        for item in items:
            if isinstance(item, dict) and str(item.get("subject_id", subject_id)) == subject_id:
                records.append(item)
    return records
