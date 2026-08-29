"""Deviation of observed biological aging from an explicit baseline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AgingDeviation:
    level: str
    node_id: str
    observed_rate: float | None
    expected_rate: float | None
    deviation: float | None
    deviation_direction: str
    confidence: float | None
    uncertainty: float | None
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    source_node_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "node_id": self.node_id,
            "observed_rate": self.observed_rate,
            "expected_rate": self.expected_rate,
            "deviation": self.deviation,
            "deviation_direction": self.deviation_direction,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
            "source_node_ids": self.source_node_ids,
        }


def estimate_aging_deviation(
    observed_rate: float | None,
    expected_rate: float | None,
    *,
    level: str,
    node_id: str,
    tolerance: float = 0.1,
    confidence: float | None = None,
    uncertainty: float | None = None,
    evidence_ids: Iterable[str] = (),
    provenance: Iterable[str] = (),
    source_node_ids: Iterable[str] = (),
) -> AgingDeviation:
    """Compare an observed rate with an explicitly supplied expected rate.

    No clinical meaning is assigned to the result. ``tolerance`` defines the
    neutral band around the expected rate and must be non-negative.
    """
    if tolerance < 0:
        raise ValueError("tolerance cannot be negative")
    if confidence is not None and not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if uncertainty is not None and uncertainty < 0:
        raise ValueError("uncertainty cannot be negative")

    evidence = tuple(sorted(set(evidence_ids)))
    provenance_values = tuple(sorted(set(provenance) | {"aging_deviation"}))
    sources = tuple(sorted(set(source_node_ids)))

    if observed_rate is None or expected_rate is None:
        return AgingDeviation(level, node_id, observed_rate, expected_rate, None,
                              "insufficient_data", confidence, uncertainty,
                              evidence, provenance_values, sources)

    deviation = float(observed_rate) - float(expected_rate)
    if abs(deviation) <= tolerance:
        direction = "within_expected_range"
    elif deviation > 0:
        direction = "faster_than_expected"
    else:
        direction = "slower_than_expected"

    return AgingDeviation(level, node_id, float(observed_rate), float(expected_rate), deviation,
                          direction, confidence, uncertainty, evidence, provenance_values, sources)
