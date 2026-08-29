"""Conservative biological-age estimation from longitudinal assessment signals."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Iterable

from .observation_identity import CellIdentity


@dataclass(frozen=True)
class BiologicalAgeEstimate:
    """An auditable biological-age estimate with an explicit uncertainty interval."""

    level: str
    node_id: str
    age_estimate: float | None
    age_interval: tuple[float, float] | None
    confidence: float | None
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "node_id": self.node_id,
            "age_estimate": self.age_estimate,
            "age_interval": self.age_interval,
            "confidence": self.confidence,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
        }


def estimate_biological_age(
    ages: Iterable[float],
    *,
    level: str,
    node_id: str,
    confidence: float | None = None,
    uncertainty: float = 0.0,
    evidence_ids: Iterable[str] = (),
    provenance: Iterable[str] = (),
) -> BiologicalAgeEstimate:
    """Estimate age conservatively from supplied biological-age observations.

    The model is deliberately transparent: it reports the mean of available
    estimates and expands the interval by the supplied uncertainty. It does not
    infer chronological age, disease, or treatment recommendations.
    """
    values = tuple(float(age) for age in ages)
    if any(age < 0 for age in values):
        raise ValueError("biological age cannot be negative")
    if uncertainty < 0:
        raise ValueError("uncertainty cannot be negative")
    if confidence is not None and not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if not values:
        return BiologicalAgeEstimate(
            level=level,
            node_id=node_id,
            age_estimate=None,
            age_interval=None,
            confidence=confidence,
            evidence_ids=tuple(sorted(set(evidence_ids))),
            provenance=tuple(sorted(set(provenance))),
        )

    estimate = fmean(values)
    interval = (max(0.0, min(values) - uncertainty), max(values) + uncertainty)
    return BiologicalAgeEstimate(
        level=level,
        node_id=node_id,
        age_estimate=estimate,
        age_interval=interval,
        confidence=confidence,
        evidence_ids=tuple(sorted(set(evidence_ids))),
        provenance=tuple(sorted(set(provenance))),
    )


def estimate_hand_age(
    cells: Iterable[tuple[CellIdentity, float]],
    *,
    hand_id: str,
    confidence: float | None = None,
    uncertainty: float = 0.0,
) -> BiologicalAgeEstimate:
    """Convenience roll-up for cell age estimates belonging to one hand."""
    cells = tuple(cells)
    for identity, _ in cells:
        if identity.hand_id != hand_id:
            raise ValueError(f"cell {identity.cell_id} belongs to another hand")
    return estimate_biological_age(
        (age for _, age in cells),
        level="hand",
        node_id=hand_id,
        confidence=confidence,
        uncertainty=uncertainty,
        provenance=("cell_biological_age_rollup",),
    )
