"""Conservative inference helpers for cell health and biological-age estimates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class CellInference:
    health_state: str
    biological_age: Optional[float]
    age_uncertainty: Optional[float]
    confidence: float
    evidence_ids: tuple[str, ...]
    rationale: tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "health_state": self.health_state,
            "biological_age": self.biological_age,
            "age_uncertainty": self.age_uncertainty,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
            "rationale": list(self.rationale),
        }


def infer_cell(evidence: Iterable[Any]) -> CellInference:
    items = list(evidence)
    ids = tuple(str(getattr(item, "evidence_id")) for item in items)
    if not items:
        return CellInference("insufficient_evidence", None, None, 0.0, ids, ("No evidence available.",))

    confidences = [max(0.0, min(1.0, float(getattr(item, "confidence", 0.0)))) for item in items]
    confidence = sum(confidences) / len(confidences)
    ages = []
    abnormality = []
    for item in items:
        feature = str(getattr(item, "feature", "")).lower()
        value = getattr(item, "value", None)
        if isinstance(value, (int, float)):
            if "age" in feature:
                ages.append(float(value))
            if "abnormal" in feature:
                abnormality.append(float(value))

    rationale = [f"{len(items)} evidence item(s) available."]
    if confidence < 0.5:
        return CellInference("insufficient_evidence", sum(ages) / len(ages) if ages else None, 1.0 - confidence, confidence, ids, tuple(rationale + ["Evidence confidence is below 0.5."]))

    if abnormality:
        score = sum(abnormality) / len(abnormality)
        if score >= 0.7:
            health = "abnormal_candidate"
            rationale.append(f"Mean abnormality signal is {score:.2f}.")
        elif score <= 0.3:
            health = "healthy_candidate"
            rationale.append(f"Mean abnormality signal is {score:.2f}.")
        else:
            health = "insufficient_evidence"
            rationale.append(f"Mean abnormality signal is intermediate ({score:.2f}).")
    else:
        health = "insufficient_evidence"
        rationale.append("No abnormality feature was available.")

    age = sum(ages) / len(ages) if ages else None
    age_uncertainty = (1.0 - confidence) * max(age or 1.0, 1.0) if age is not None else None
    if age is not None:
        rationale.append(f"Biological age is an evidence-weighted estimate from {len(ages)} age signal(s).")
    else:
        rationale.append("No biological-age feature was available.")
    return CellInference(health, age, age_uncertainty, confidence, ids, tuple(rationale))
