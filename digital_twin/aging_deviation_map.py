"""Build an observational aging-deviation map from a DigitalTwin."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .aging_deviation import AgingDeviation, build_aging_deviation, rank_aging_deviations


def build_deviation_map(
    baseline_age: Optional[float],
    nodes: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Create a hierarchical deviation payload from already-derived age estimates.

    ``nodes`` should contain ``level``, ``identifier``, ``biological_age`` and
    optionally ``confidence``. The function is intentionally independent from
    DigitalTwin internals so callers can use it with API/database projections.
    """
    deviations: List[AgingDeviation] = []
    for node in nodes:
        deviations.append(
            build_aging_deviation(
                level=str(node["level"]),
                identifier=str(node["identifier"]),
                baseline_age=baseline_age,
                observed_age=node.get("biological_age"),
                confidence=float(node.get("confidence", 0.0)),
            )
        )

    ranked = rank_aging_deviations(deviations)
    return {
        "baseline_age": baseline_age,
        "items": [item.to_dict() for item in deviations],
        "ranked": [item.to_dict() for item in ranked],
        "reliable_items": [item.to_dict() for item in ranked if item.severity != "insufficient"],
    }
