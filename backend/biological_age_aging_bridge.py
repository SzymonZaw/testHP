"""Bridge canonical biological-age estimates into aging-deviation signals.

The bridge keeps age estimates as observations/derived claims and requires an
explicit expected rate. It does not infer disease, treatment, or rejuvenation.
"""
from __future__ import annotations

from typing import Iterable

from .aging_deviation import AgingDeviation, estimate_aging_deviation
from .biological_state import BiologicalAgeEstimate


def _evidence_ids(estimates: Iterable[BiologicalAgeEstimate]) -> tuple[str, ...]:
    return tuple(sorted({evidence.evidence_id for estimate in estimates for evidence in estimate.evidence}))


def _confidence(estimates: Iterable[BiologicalAgeEstimate]) -> float | None:
    values = [evidence.confidence for estimate in estimates for evidence in estimate.evidence if evidence.confidence is not None]
    return min(values) if values else None


def _uncertainty_score(estimates: Iterable[BiologicalAgeEstimate]) -> float | None:
    values = [estimate.uncertainty.score for estimate in estimates if estimate.uncertainty.score is not None]
    return max(values) if values else None


def aging_deviation_from_age_estimates(
    estimates: Iterable[BiologicalAgeEstimate],
    *,
    expected_rate: float | None,
    level: str,
    node_id: str,
    elapsed_years: float | None = None,
    tolerance: float = 0.1,
) -> AgingDeviation:
    """Convert one or more chronological biological-age estimates to deviation.

    With two or more estimates, observed rate is the change in estimated
    biological age divided by explicit ``elapsed_years``. With one estimate,
    the observed rate is unavailable. No elapsed duration is guessed from
    opaque timepoint identifiers.
    """
    items = tuple(estimates)
    if not items:
        return estimate_aging_deviation(
            None, expected_rate, level=level, node_id=node_id,
            tolerance=tolerance, confidence=None, uncertainty=None,
            evidence_ids=(), provenance=("biological_age_aging_bridge",),
            source_node_ids=(),
        )

    if elapsed_years is not None and elapsed_years <= 0:
        raise ValueError("elapsed_years must be positive")

    ordered = items
    observed_rate: float | None = None
    if len(ordered) >= 2 and elapsed_years is not None:
        observed_rate = (ordered[-1].estimated_age_years - ordered[0].estimated_age_years) / elapsed_years

    provenance = {
        "biological_age_aging_bridge",
        *(estimate.provenance.method or "unknown" for estimate in ordered),
    }
    return estimate_aging_deviation(
        observed_rate,
        expected_rate,
        level=level,
        node_id=node_id,
        tolerance=tolerance,
        confidence=_confidence(ordered),
        uncertainty=_uncertainty_score(ordered),
        evidence_ids=_evidence_ids(ordered),
        provenance=provenance,
        source_node_ids=tuple(sorted({estimate.target_object_id for estimate in ordered})),
    )
