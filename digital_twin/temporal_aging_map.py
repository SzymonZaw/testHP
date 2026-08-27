"""Build temporal aging-deviation maps from longitudinal observations."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .temporal_aging_deviation import TemporalAgingDeviation, analyze_temporal_aging_deviation


def build_temporal_aging_map(nodes: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze longitudinal deviation points for each region/tissue node."""
    items: List[TemporalAgingDeviation] = []
    for node in nodes:
        identifier = str(node["identifier"])
        items.append(analyze_temporal_aging_deviation(identifier, node.get("points", [])))

    ranked = sorted(
        items,
        key=lambda item: abs(item.change or 0.0) * item.confidence,
        reverse=True,
    )
    return {
        "items": [item.to_dict() for item in items],
        "ranked": [item.to_dict() for item in ranked],
        "persistent": [item.to_dict() for item in ranked if item.persistence == "persistent"],
        "increasing": [item.to_dict() for item in ranked if item.direction == "increasing"],
    }
