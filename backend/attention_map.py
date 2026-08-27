from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AttentionZone:
    zone_id: str
    level: str
    metric: str
    score: float
    status: str
    cell_count: int
    changed_cells: int

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def build_attention_map(trends: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert observed multiscale trends into a bounded prioritisation map.

    This is an observational/research signal. It deliberately does not label
    a zone as diseased and does not recommend treatment.
    """
    result: list[AttentionZone] = []
    for item in trends:
        count = int(item.get("cell_count", 0) or 0)
        changed = int(item.get("changed_cells", 0) or 0)
        mean_delta = item.get("mean_delta")
        if count <= 0:
            continue
        change_fraction = min(1.0, max(0.0, changed / count))
        magnitude = min(1.0, abs(float(mean_delta)) / 10.0) if isinstance(mean_delta, (int, float)) and not isinstance(mean_delta, bool) else 0.0
        score = round(0.7 * change_fraction + 0.3 * magnitude, 6)
        status = "high_attention" if score >= 0.75 else "attention" if score >= 0.35 else "monitor"
        result.append(AttentionZone(str(item["zone_id"]), str(item["level"]), str(item["metric"]), score, status, count, changed))
    return [x.to_dict() for x in sorted(result, key=lambda x: (-x.score, x.level, x.zone_id, x.metric))]
