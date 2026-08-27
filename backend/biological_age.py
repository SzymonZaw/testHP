from __future__ import annotations

"""Research baseline for estimating biological age at cell level.

This is not a clinical age-determination model. It produces a transparent,
evidence-linked estimate that can later be replaced by a validated model.
"""

from dataclasses import dataclass
from typing import Any
import uuid

from .anatomy_foundation import CellObject, Evidence
from .data_foundation import BiologicalAgeEstimate, Provenance, Uncertainty


@dataclass(frozen=True)
class BiologicalAgeResult:
    estimate: BiologicalAgeEstimate
    rationale: tuple[str, ...]


class BiologicalAgeEngine:
    model_id = "research-rule-cell-age"
    model_version = "1"

    def estimate(
        self,
        cell: CellObject,
        *,
        observations: dict[str, Any],
        source_data_ids: tuple[str, ...],
        assessed_at: str,
        estimate_id: str | None = None,
    ) -> BiologicalAgeResult:
        cell.validate()
        if not source_data_ids:
            raise ValueError("source_data_ids are required")
        if not assessed_at.strip():
            raise ValueError("assessed_at is required")

        age = observations.get("estimated_age_years")
        interval = observations.get("age_interval")
        if age is None:
            raise ValueError("estimated_age_years is required for the baseline engine")
        if not isinstance(age, (int, float)) or age < 0 or age > 200:
            raise ValueError("estimated_age_years must be between 0 and 200")
        if interval is None:
            half_width = float(observations.get("uncertainty_years", 5.0))
            if half_width < 0:
                raise ValueError("uncertainty_years must be non-negative")
            interval = (max(0.0, float(age) - half_width), float(age) + half_width)
        if len(interval) != 2 or interval[0] < 0 or interval[1] < interval[0]:
            raise ValueError("age_interval must be a non-negative ordered pair")

        confidence = observations.get("confidence")
        if confidence is not None and (not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1):
            raise ValueError("confidence must be between 0 and 1")

        provenance = Provenance(source_object_ids=source_data_ids, method=self.model_id, method_version=self.model_version)
        evidence = (Evidence(
            evidence_id=f"evidence_{uuid.uuid4().hex[:12]}",
            source_data_ids=source_data_ids,
            kind="cell_age_observation",
            value=dict(observations),
            confidence=confidence,
            provenance=provenance,
        ),)
        estimate = BiologicalAgeEstimate(
            estimate_id=estimate_id or f"age_{uuid.uuid4().hex[:12]}",
            subject_id=cell.subject_id,
            hand_id=cell.hand_id,
            timepoint_id=cell.timepoint_id,
            target_object_id=cell.cell_id,
            estimated_age_years=float(age),
            uncertainty=Uncertainty(kind="age_interval", interval=(float(interval[0]), float(interval[1]))),
            evidence=evidence,
            provenance=provenance,
            assessed_at=assessed_at,
            model_id=self.model_id,
            model_version=self.model_version,
        )
        estimate.validate()
        return BiologicalAgeResult(estimate, ("estimated_age_years supplied", "age interval preserved as explicit uncertainty"))
