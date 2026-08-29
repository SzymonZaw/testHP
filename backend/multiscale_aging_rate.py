"""Conservative aggregation of longitudinal aging-rate signals."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pstdev
from typing import Iterable

from .aging_rate import AgingRateEstimate


@dataclass(frozen=True)
class MultiscaleAgingRate:
    """Aggregated aging signal with disagreement and uncertainty preserved."""

    level: str
    node_id: str
    aging_rate: float | None
    trend: str
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
            "aging_rate": self.aging_rate,
            "trend": self.trend,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "disagreement": self.disagreement,
            "source_node_ids": self.source_node_ids,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
        }


def aggregate_aging_rates(
    signals: Iterable[AgingRateEstimate],
    *,
    level: str,
    node_id: str,
) -> MultiscaleAgingRate:
    """Aggregate child aging rates conservatively.

    Rates are averaged only across available numeric signals. Confidence is
    capped by the least-confident source, while uncertainty includes source
    uncertainty plus observed disagreement. Conflicting directional trends are
    explicitly reported rather than collapsed into a misleading label.
    """
    items = tuple(signals)
    usable = tuple(item for item in items if item.aging_rate is not None)
    source_ids = tuple(sorted({item.node_id for item in items}))
    evidence = tuple(sorted({eid for item in items for eid in item.evidence_ids}))
    provenance = tuple(sorted({p for item in items for p in item.provenance} | {"multiscale_aging_rate_rollup"}))
    if not usable:
        return MultiscaleAgingRate(level, node_id, None, "insufficient_data", None, None, None, source_ids, evidence, provenance)

    rates = tuple(float(item.aging_rate) for item in usable)
    estimate = fmean(rates)
    disagreement = pstdev(rates) if len(rates) > 1 else 0.0
    confidences = tuple(item.confidence for item in usable if item.confidence is not None)
    confidence = min(confidences) if confidences else None
    uncertainties = tuple(item.uncertainty for item in usable if item.uncertainty is not None)
    uncertainty = (max(uncertainties) if uncertainties else 0.0) + disagreement

    trends = {item.trend for item in usable}
    if len(trends) > 1:
        trend = "mixed"
    elif estimate > 1.0:
        trend = "accelerating"
    elif estimate < 0.0:
        trend = "improving"
    else:
        trend = "aging"

    if disagreement > 0.5 and confidence is not None:
        confidence = confidence * 0.5

    return MultiscaleAgingRate(
        level, node_id, estimate, trend, confidence, uncertainty, disagreement,
        source_ids, evidence, provenance,
    )
