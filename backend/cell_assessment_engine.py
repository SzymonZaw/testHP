"""Infer a conservative cell state from a CellObservation.

This module is intentionally a deterministic baseline. It converts explicit
measurement signals into a CellStateAssessment while preserving evidence and
provenance. A future statistical/ML model can implement the same contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .anatomy_foundation import CellStateAssessment, Evidence
from .cell_observation import CellObservation
from .data_foundation import Provenance


@dataclass(frozen=True)
class CellAssessmentResult:
    assessment: CellStateAssessment
    signals: tuple[str, ...]


@dataclass(frozen=True)
class CellAssessmentEngine:
    """Rule-based baseline for CellObservation -> CellStateAssessment."""

    pathological_threshold: float = 0.8
    senescence_threshold: float = 0.8
    stress_threshold: float = 0.8

    def assess(
        self,
        observation: CellObservation,
        *,
        assessment_id: str | None = None,
        assessed_at: str | None = None,
        provenance: Provenance | None = None,
    ) -> CellAssessmentResult:
        observation.validate()
        measurements = observation.measurements
        signals: list[str] = []

        pathological = _score(measurements, ("disease_probability", "damage_score"))
        senescence = _score(measurements, ("senescence_score",))
        stress = _score(measurements, ("stress_score", "inflammation_score"))

        if _truthy(measurements.get("pathological")) or (
            pathological is not None and pathological >= self.pathological_threshold
        ):
            state = "pathological"
            confidence = pathological if pathological is not None else 1.0
            signals.append("pathological signal exceeded baseline threshold")
        elif _truthy(measurements.get("senescent")) or (
            senescence is not None and senescence >= self.senescence_threshold
        ):
            state = "senescent"
            confidence = senescence if senescence is not None else 1.0
            signals.append("senescence signal exceeded baseline threshold")
        elif _truthy(measurements.get("stressed")) or (
            stress is not None and stress >= self.stress_threshold
        ):
            state = "stressed"
            confidence = stress if stress is not None else 1.0
            signals.append("stress signal exceeded baseline threshold")
        elif measurements:
            state = "normal"
            confidence = 0.5
            signals.append("measurements present without a positive abnormal-state signal")
        else:
            state = "unknown"
            confidence = None
            signals.append("no measurements available")

        rule_evidence = Evidence(
            evidence_id=f"rule:{observation.observation_id}",
            source_data_ids=observation.source_data_ids,
            kind="deterministic_cell_state_rule",
            value={
                "signals": tuple(signals),
                "measurement_keys": tuple(sorted(measurements)),
            },
            confidence=confidence,
            provenance=provenance or observation.provenance,
        )
        assessment = CellStateAssessment(
            assessment_id=assessment_id or f"cell-assessment:{observation.observation_id}",
            cell_id=observation.cell_id,
            state=state,
            confidence=confidence,
            evidence=observation.evidence + (rule_evidence,),
            provenance=provenance or observation.provenance,
            assessed_at=assessed_at or datetime.now(timezone.utc).isoformat(),
        )
        assessment.validate()
        return CellAssessmentResult(assessment=assessment, signals=tuple(signals))

    def assess_to_dict(self, observation: CellObservation) -> Mapping[str, Any]:
        return self.assess(observation).assessment.__dict__.copy()


def assess_cell_observation(observation: CellObservation) -> CellStateAssessment:
    return CellAssessmentEngine().assess(observation).assessment


def _score(measurements: Mapping[str, Any], keys: tuple[str, ...]) -> float | None:
    values = [float(measurements[key]) for key in keys if _number(measurements.get(key))]
    if not values:
        return None
    return max(0.0, min(1.0, max(values)))


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _truthy(value: Any) -> bool:
    return value is True
