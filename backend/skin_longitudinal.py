from __future__ import annotations

from typing import Any


def compare_skin_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[tuple[str, float]]] = {}
    for obs in observations:
        if obs.get("status") != "available":
            continue
        zone = str(obs.get("zone") or obs.get("region") or "skin")
        metric = str(obs.get("metric") or "brightness")
        value = obs.get("value")
        tp = str(obs.get("timepoint") or "unknown")
        if isinstance(value, (int, float)) and not isinstance(value, bool) and tp != "unknown":
            groups.setdefault((zone, metric), []).append((tp, float(value)))
    result = []
    for (zone, metric), values in sorted(groups.items()):
        values.sort(key=lambda x: x[0])
        nums = [v for _, v in values]
        delta = nums[-1] - nums[0] if len(nums) > 1 else None
        result.append({
            "zone": zone,
            "metric": metric,
            "timepoints": [t for t, _ in values],
            "values": nums,
            "delta": delta,
            "status": "observed_change" if delta not in (None, 0) else ("stable_observation" if delta == 0 else "insufficient_timepoints"),
            "evidence_level": "derived",
            "diagnosis": "not performed",
        })
    return result
