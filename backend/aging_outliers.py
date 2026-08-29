"""Regional outlier detection for hand aging profiles.

This module produces an analytical prioritization signal only. It does not
make a diagnosis or prescribe treatment.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable

from .hand_aging_profile import HandAgingProfile
from .multiscale_aging_deviation import MultiscaleAgingDeviation


@dataclass(frozen=True)
class AgingOutlier:
    level: str
    node_id: str
    observed_deviation: float | None
    hand_baseline: float | None
    relative_deviation: float | None
    outlier_score: float | None
    direction: str
    confidence: float | None
    uncertainty: float | None
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "node_id": self.node_id,
            "observed_deviation": self.observed_deviation,
            "hand_baseline": self.hand_baseline,
            "relative_deviation": self.relative_deviation,
            "outlier_score": self.outlier_score,
            "direction": self.direction,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
        }


def detect_aging_outliers(
    profile: HandAgingProfile,
    *,
    level: str = "region",
    threshold: float = 0.5,
) -> tuple[AgingOutlier, ...]:
    """Detect regional deviations from a robust hand baseline.

    The baseline is the median regional deviation. ``outlier_score`` is the
    absolute distance from that baseline. Missing deviations are retained as
    insufficient-data records and never treated as zero.
    """
    if threshold < 0:
        raise ValueError("threshold cannot be negative")

    regions: tuple[MultiscaleAgingDeviation, ...] = tuple(profile.regions)
    usable = tuple(region for region in regions if region.deviation is not None)
    if not usable:
        return tuple(
            AgingOutlier(level, region.node_id, None, None, None, None,
                         "insufficient_data", region.confidence, region.uncertainty,
                         region.evidence_ids,
                         tuple(sorted(set(region.provenance) | {"aging_outlier_detection"})))
            for region in regions
        )

    baseline = float(median(float(region.deviation) for region in usable))
    results: list[AgingOutlier] = []
    for region in regions:
        evidence = region.evidence_ids
        provenance = tuple(sorted(set(region.provenance) | {"aging_outlier_detection"}))
        if region.deviation is None:
            results.append(AgingOutlier(level, region.node_id, None, baseline, None, None,
                                        "insufficient_data", region.confidence, region.uncertainty,
                                        evidence, provenance))
            continue
        relative = float(region.deviation) - baseline
        score = abs(relative)
        if score < threshold:
            direction = "within_hand_baseline"
        elif relative > 0:
            direction = "higher_than_hand_baseline"
        else:
            direction = "lower_than_hand_baseline"
        results.append(AgingOutlier(level, region.node_id, float(region.deviation), baseline,
                                    relative, score, direction, region.confidence,
                                    region.uncertainty, evidence, provenance))

    return tuple(sorted(results, key=lambda item: (-(item.outlier_score or 0.0), item.node_id)))
