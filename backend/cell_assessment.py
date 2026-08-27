from __future__ import annotations

"""Evidence-first cell-state assessment contracts and research baseline engine.

The baseline is deliberately conservative and is not a clinical diagnostic
model. It turns explicitly supplied generic anomaly observations into a
versioned assessment while preserving source evidence and uncertainty.
"""

from dataclasses import dataclass
from typing import Any
import uuid

from .anatomy_foundation import CellObject, CellState, Evidence
from .data_foundation import Provenance, Uncertainty


def build_cell_state_assessment(cell: CellObject, *, assessment_id: str, state: CellState, confidence: float | None, evidence: tuple[Evidence, ...], provenance: Provenance, assessed_at: str):
    cell.validate()
    if not assessment_id.strip(): raise ValueError("assessment_id is required")
    if confidence is not None and not 0 <= confidence <= 1: raise ValueError("confidence must be between 0 and 1")
    if not evidence: raise ValueError("cell state assessment requires evidence")
    if not assessed_at.strip(): raise ValueError("assessed_at is required")
    for item in evidence:
        if not item.evidence_id.strip(): raise ValueError("evidence_id is required")
        if not item.source_data_ids: raise ValueError("cell evidence requires source_data_ids")
        if item.confidence is not None and not 0 <= item.confidence <= 1: raise ValueError("evidence confidence must be between 0 and 1")
    from .anatomy_foundation import CellStateAssessment
    assessment = CellStateAssessment(assessment_id=assessment_id, cell_id=cell.cell_id, state=state, confidence=confidence, evidence=evidence, provenance=provenance, assessed_at=assessed_at)
    assessment.validate()
    return assessment


@dataclass(frozen=True)
class CellAssessmentResult:
    assessment: Any
    rationale: tuple[str, ...]


class CellAssessmentEngine:
    """Conservative deterministic baseline; a trained model can replace it later."""
    model_id = "research-rule-cell-state"
    model_version = "1"

    def __init__(self, *, suspicious_threshold: float = 0.5, abnormality_threshold: float = 0.8) -> None:
        if not 0 <= suspicious_threshold <= abnormality_threshold <= 1: raise ValueError("thresholds must satisfy 0 <= suspicious <= abnormality <= 1")
        self.suspicious_threshold, self.abnormality_threshold = suspicious_threshold, abnormality_threshold

    def assess(self, cell: CellObject, *, observations: dict[str, Any], source_data_ids: tuple[str, ...], assessed_at: str, assessment_id: str | None = None) -> CellAssessmentResult:
        cell.validate()
        if not source_data_ids: raise ValueError("source_data_ids are required")
        score, rationale, known = self._score(observations)
        if not known:
            state, confidence, uncertainty = "unknown", None, Uncertainty(kind="insufficient_evidence", score=1.0)
        elif score >= self.abnormality_threshold:
            state, confidence, uncertainty = "pathological", score, Uncertainty(kind="rule_margin", score=1.0-score)
        elif score >= self.suspicious_threshold:
            state, confidence, uncertainty = "stressed", score, Uncertainty(kind="rule_margin", score=1.0-score)
        else:
            state, confidence, uncertainty = "normal", 1.0-score, Uncertainty(kind="rule_margin", score=score)
        provenance = Provenance(source_object_ids=source_data_ids, method=self.model_id, method_version=self.model_version)
        evidence = (Evidence(f"evidence_{uuid.uuid4().hex[:12]}", source_data_ids, "cell_observation", dict(observations), provenance=provenance),)
        assessment = build_cell_state_assessment(cell, assessment_id=assessment_id or f"assessment_{uuid.uuid4().hex[:12]}", state=state, confidence=confidence, evidence=evidence, provenance=provenance, assessed_at=assessed_at)
        return CellAssessmentResult(assessment, tuple(rationale))

    def _score(self, observations: dict[str, Any]) -> tuple[float, list[str], bool]:
        score, rationale, known = 0.0, [], False
        anomaly = observations.get("anomaly_score")
        if anomaly is not None:
            if not isinstance(anomaly, (int, float)) or not 0 <= anomaly <= 1: raise ValueError("anomaly_score must be between 0 and 1")
            score, known = float(anomaly), True
            rationale.append("anomaly_score supplied")
        flags = observations.get("morphology_flags", ())
        if flags:
            known = True
            count = len(tuple(flags))
            score = max(score, min(1.0, 0.25 * count))
            rationale.append(f"{count} morphology flag(s) supplied")
        return score, rationale, known
