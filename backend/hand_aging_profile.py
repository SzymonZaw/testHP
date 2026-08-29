"""Auditable hand-level biological aging profile.

This module summarizes analytical aging signals. It does not diagnose disease
or prescribe treatment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .multiscale_aging_deviation import MultiscaleAgingDeviation


@dataclass(frozen=True)
class HandAgingProfile:
    hand_id: str
    biological_age: float | None
    aging_rate: float | None
    regions: tuple[MultiscaleAgingDeviation, ...]
    fastest_aging_regions: tuple[str, ...]
    slowest_aging_regions: tuple[str, ...]
    confidence: float | None
    uncertainty: float | None
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "hand_id": self.hand_id,
            "biological_age": self.biological_age,
            "aging_rate": self.aging_rate,
            "regions": tuple(region.to_dict() for region in self.regions),
            "fastest_aging_regions": self.fastest_aging_regions,
            "slowest_aging_regions": self.slowest_aging_regions,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
        }


def build_hand_aging_profile(
    hand_id: str,
    regions: Iterable[MultiscaleAgingDeviation],
    *,
    biological_age: float | None = None,
    aging_rate: float | None = None,
) -> HandAgingProfile:
    """Build a hand profile from regional analytical signals.

    Regional deviations are ranked by value. Ties are retained. Missing
    deviations are excluded from ranking rather than treated as zero.
    """
    items = tuple(regions)
    usable = tuple(item for item in items if item.deviation is not None)
    if biological_age is not None and biological_age < 0:
        raise ValueError("biological_age cannot be negative")
    if aging_rate is not None and aging_rate < 0:
        raise ValueError("aging_rate cannot be negative")

    if usable:
        maximum = max(item.deviation for item in usable)
        minimum = min(item.deviation for item in usable)
        fastest = tuple(item.node_id for item in usable if item.deviation == maximum)
        slowest = tuple(item.node_id for item in usable if item.deviation == minimum)
    else:
        fastest = ()
        slowest = ()

    confidences = tuple(item.confidence for item in items if item.confidence is not None)
    confidence = min(confidences) if confidences else None
    uncertainties = tuple(item.uncertainty for item in items if item.uncertainty is not None)
    uncertainty = max(uncertainties) if uncertainties else None
    evidence = tuple(sorted({eid for item in items for eid in item.evidence_ids}))
    provenance = tuple(sorted({p for item in items for p in item.provenance} | {"hand_aging_profile"}))

    return HandAgingProfile(
        hand_id=hand_id,
        biological_age=biological_age,
        aging_rate=aging_rate,
        regions=items,
        fastest_aging_regions=fastest,
        slowest_aging_regions=slowest,
        confidence=confidence,
        uncertainty=uncertainty,
        evidence_ids=evidence,
        provenance=provenance,
    )
