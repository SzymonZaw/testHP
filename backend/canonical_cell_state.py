from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .anatomy_foundation import CellObject, CellStateAssessment
from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment
from .cell_biological_state import CellBiologicalState, EvidenceBundle, EvidenceItem


@dataclass(frozen=True)
class CanonicalCellState:
    """Single read model joining morphology, health assessment and biological age."""

    cell: CellObject
    state: CellBiologicalState
    state_assessment: CellStateAssessment | BiologicalStateAssessment | None = None
    age_estimate: BiologicalAgeEstimate | None = None

    def validate(self) -> None:
        self.cell.validate()
        self.state.validate()
        if self.state.cell_id != self.cell.cell_id:
            raise ValueError("canonical state and cell must share cell_id")
        if self.state.tissue_id != self.cell.tissue_id:
            raise ValueError("canonical state and cell must share tissue_id")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "cell": {
                "cell_id": self.cell.cell_id,
                "tissue_id": self.cell.tissue_id,
                "cell_type": self.cell.cell_type,
                "position": dict(self.cell.position),
                "morphology": dict(self.cell.morphology),
                "size": dict(self.cell.size),
                "nucleus": dict(self.cell.nucleus),
                "spatial_reference": self.cell.spatial_reference,
            },
            "state": self.state.to_dict(),
            "state_assessment": self.state_assessment.to_dict() if self.state_assessment is not None else None,
            # Keep the canonical read model serializable even when an upstream
            # age record is still incomplete. Validation remains the responsibility
            # of registry insertion/assessment boundaries.
            "age_estimate": asdict(self.age_estimate) if self.age_estimate is not None else None,
        }


def build_canonical_cell_state(
    cell: CellObject,
    *,
    state_assessment: CellStateAssessment | BiologicalStateAssessment | None = None,
    age_estimate: BiologicalAgeEstimate | None = None,
) -> CanonicalCellState:
    """Project existing registry records into one evidence-preserving state.

    Existing assessment values remain authoritative; this function does not
    infer a diagnosis or invent missing biological-age data.
    """
    state = "uncertain"
    uncertainty = 1.0
    evidence: list[EvidenceItem] = []

    if isinstance(state_assessment, CellStateAssessment):
        state_map = {"normal": "normal", "pathological": "abnormal", "unknown": "uncertain"}
        state = state_map.get(state_assessment.state, "uncertain")
        confidence = state_assessment.confidence
        uncertainty = 1.0 - confidence if confidence is not None else 1.0
        for item in state_assessment.evidence:
            evidence.append(EvidenceItem(
                item.evidence_id, item.source_data_ids, item.kind, item.value,
                item.confidence if item.confidence is not None else confidence or 0.0,
            ))
    elif isinstance(state_assessment, BiologicalStateAssessment):
        state = "normal" if state_assessment.state == "normal" else "abnormal"
        uncertainty_obj = state_assessment.uncertainty
        uncertainty = float(uncertainty_obj.score) if uncertainty_obj.score is not None else 1.0
        for item in state_assessment.evidence:
            evidence.append(EvidenceItem(
                item.evidence_id, item.source_object_ids, item.kind, item.value,
                item.confidence if item.confidence is not None else state_assessment.confidence,
            ))

    if not evidence:
        evidence.append(EvidenceItem(
            evidence_id=f"cell:{cell.cell_id}:observation",
            source_object_ids=cell.source_data_ids or (f"cell:{cell.cell_id}",),
            kind="cell_observation",
            value={"morphology": cell.morphology, "size": cell.size, "nucleus": cell.nucleus},
            confidence=cell.confidence if cell.confidence is not None else 0.0,
        ))

    age = age_estimate.estimated_age_years if age_estimate is not None else None
    canonical = CellBiologicalState(
        cell_id=cell.cell_id,
        subject_id=cell.subject_id,
        hand_id=cell.hand_id,
        timepoint_id=cell.timepoint_id,
        state=state,
        biological_age_years=age,
        uncertainty=max(0.0, min(1.0, uncertainty)),
        evidence=EvidenceBundle(tuple(evidence)),
        spatial_reference=cell.spatial_reference.frame_id,
        tissue_id=cell.tissue_id,
    )
    return CanonicalCellState(cell, canonical, state_assessment, age_estimate)
