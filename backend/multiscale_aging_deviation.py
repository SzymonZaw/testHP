"""Conservative multiscale aggregation of aging-deviation signals."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pstdev
from typing import Iterable

from .aging_deviation import AgingDeviation


@dataclass(frozen=True)
class MultiscaleAgingDeviation:
    level: str
    node_id: str
    deviation: float | None
    deviation_direction: str
    confidence: float | None
    uncertainty: float | None
    disagreement: float | None
    source_node_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "node_id": self.node_id,
            "deviation": self.deviation,
            "deviation_direction": self.deviation_direction,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "disagreement": self.disagreement,
            "source_node_ids": self.source_node_ids,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
        }


def aggregate_aging_deviations(
    signals: Iterable[AgingDeviation],
    *,
    level: str,
    node_id: str,
) -> MultiscaleAgingDeviation:
    """Aggregate child deviations while preserving disagreement and uncertainty."""
    items = tuple(signals)
    usable = tuple(item for item in items if item.deviation is not None)
    source_ids = tuple(sorted({item.node_id for item in items}))
    evidence = tuple(sorted({eid for item in items for eid in item.evidence_ids}))
    provenance = tuple(sorted({p for item in items for p in item.provenance} | {"multiscale_aging_deviation_rollup"}))
    if not usable:
        return MultiscaleAgingDeviation(level, node_id, None, "insufficient_data", None, None, None, source_ids, evidence, provenance)

    values = tuple(float(item.deviation) for item in usable)
    deviation = fmean(values)
    disagreement = pstdev(values) if len(values) > 1 else 0.0
    confidences = tuple(item.confidence for item in usable if item.confidence is not None)
    confidence = min(confidences) if confidences else None
    uncertainties = tuple(item.uncertainty for item in usable if item.uncertainty is not None)
    uncertainty = (max(uncertainties) if uncertainties else 0.0) + disagreement

    directions = {item.deviation_direction for item in usable}
    if len(directions) > 1:
        direction = "mixed"
    elif deviation > 0:
        direction = "faster_than_expected"
    elif deviation < 0:
        direction = "slower_than_expected"
    else:
        direction = "within_expected_range"

    if disagreement > 0.5 and confidence is not None:
        confidence *= 0.5

    return MultiscaleAgingDeviation(level, node_id, deviation, direction, confidence, uncertainty,
                                     disagreement, source_ids, evidence, provenance)
