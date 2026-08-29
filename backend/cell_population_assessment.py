from __future__ import annotations

"""Evidence-preserving aggregation of cell-state assessments."""

from dataclasses import dataclass
from typing import Any

from .anatomy_foundation import CellStateAssessment
from .data_foundation import Provenance, Uncertainty


@dataclass(frozen=True)
class CellPopulationAssessment:
    """Descriptive population signal; it is not a clinical diagnosis."""

    population_id: str
    cell_ids: tuple[str, ...]
    cell_count: int
    state_distribution: dict[str, int]
    dominant_state: str
    confidence: float | None
    uncertainty: Uncertainty
    evidence_ids: tuple[str, ...]
    provenance: Provenance

    def validate(self) -> None:
        if self.cell_count != len(self.cell_ids):
            raise ValueError("cell_count must match cell_ids")
        if self.cell_count != sum(self.state_distribution.values()):
            raise ValueError("state distribution must account for every cell")
        if self.cell_count and not self.dominant_state:
            raise ValueError("dominant_state is required for a non-empty population")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.uncertainty.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "population_id": self.population_id,
            "cell_ids": self.cell_ids,
            "cell_count": self.cell_count,
            "state_distribution": self.state_distribution,
            "dominant_state": self.dominant_state,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
        }


def aggregate_cell_state_assessments(
    population_id: str,
    assessments: tuple[CellStateAssessment, ...] | list[CellStateAssessment],
) -> CellPopulationAssessment:
    """Aggregate cell assessments while retaining the weakest confidence and lineage."""
    items = tuple(assessments)
    for item in items:
        item.validate()

    if not items:
        return CellPopulationAssessment(
            population_id=population_id,
            cell_ids=(),
            cell_count=0,
            state_distribution={},
            dominant_state="unknown",
            confidence=None,
            uncertainty=Uncertainty(kind="insufficient_observation", details={"reason": "no_cell_assessments"}),
            evidence_ids=(),
            provenance=Provenance(source_object_ids=(), method="cell_state_aggregation", validation_status="insufficient_data"),
        )

    state_distribution: dict[str, int] = {}
    confidences: list[float] = []
    evidence_ids: set[str] = set()
    source_ids: set[str] = set()
    for item in items:
        state_distribution[item.state] = state_distribution.get(item.state, 0) + 1
        if item.confidence is not None:
            confidences.append(item.confidence)
        evidence_ids.add(item.assessment_id)
        evidence_ids.update(e.evidence_id for e in item.evidence)
        source_ids.update(item.provenance.source_object_ids)

    dominant_state = min(
        state_distribution,
        key=lambda state: (-state_distribution[state], state),
    )
    confidence = min(confidences) if confidences else None
    result = CellPopulationAssessment(
        population_id=population_id,
        cell_ids=tuple(sorted(item.cell_id for item in items)),
        cell_count=len(items),
        state_distribution=dict(sorted(state_distribution.items())),
        dominant_state=dominant_state,
        confidence=confidence,
        uncertainty=Uncertainty(
            kind="population_aggregation",
            score=1.0 - confidence if confidence is not None else None,
            details={"assessment_count": len(items)},
        ),
        evidence_ids=tuple(sorted(evidence_ids)),
        provenance=Provenance(
            source_object_ids=tuple(sorted(source_ids | {item.assessment_id for item in items})),
            method="cell_state_aggregation",
            method_version="1",
            validation_status="validated",
        ),
    )
    result.validate()
    return result
