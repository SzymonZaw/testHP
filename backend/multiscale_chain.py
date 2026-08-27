from __future__ import annotations

"""Auditable links across the hand digital-twin scale hierarchy."""

from dataclasses import dataclass
from typing import Any

from .anatomy_foundation import AnatomicalStructure, CellObject, HistologyRegion, TissueRegion
from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment


@dataclass(frozen=True)
class MultiscaleChain:
    anatomy: AnatomicalStructure
    tissue: TissueRegion
    histology: HistologyRegion | None = None
    cell: CellObject | None = None
    state_assessment: BiologicalStateAssessment | None = None
    age_estimate: BiologicalAgeEstimate | None = None

    @property
    def context(self) -> tuple[str, str, str]:
        return (self.anatomy.subject_id, self.anatomy.hand_id, self.anatomy.timepoint_id)

    def validate(self) -> None:
        self.anatomy.validate(); self.tissue.validate(); context = self.context
        if self.tissue.anatomical_structure_id != self.anatomy.structure_id:
            raise ValueError("tissue is not linked to the supplied anatomical structure")
        if (self.tissue.subject_id, self.tissue.hand_id, self.tissue.timepoint_id) != context:
            raise ValueError("tissue and anatomy must share subject/hand/timepoint")
        if self.histology is not None:
            self.histology.validate()
            if self.histology.tissue_id != self.tissue.tissue_id:
                raise ValueError("histology is not linked to the supplied tissue")
            if (self.histology.subject_id, self.histology.hand_id, self.histology.timepoint_id) != context:
                raise ValueError("histology and tissue must share subject/hand/timepoint")
        if self.cell is not None:
            self.cell.validate()
            if self.cell.tissue_id != self.tissue.tissue_id:
                raise ValueError("cell is not linked to the supplied tissue")
            if (self.cell.subject_id, self.cell.hand_id, self.cell.timepoint_id) != context:
                raise ValueError("cell and tissue must share subject/hand/timepoint")
        if self.state_assessment is not None:
            self.state_assessment.validate()
            if self.cell is None or self.state_assessment.target_object_id != self.cell.cell_id:
                raise ValueError("cell state assessment must target the supplied cell")
            if (self.state_assessment.subject_id, self.state_assessment.hand_id, self.state_assessment.timepoint_id) != context:
                raise ValueError("state assessment and cell must share subject/hand/timepoint")
        if self.age_estimate is not None:
            self.age_estimate.validate()
            if self.cell is None or self.age_estimate.target_object_id != self.cell.cell_id:
                raise ValueError("biological age estimate must target the supplied cell")
            if (self.age_estimate.subject_id, self.age_estimate.hand_id, self.age_estimate.timepoint_id) != context:
                raise ValueError("age estimate and cell must share subject/hand/timepoint")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {"context": {"subject_id": self.anatomy.subject_id, "hand_id": self.anatomy.hand_id, "timepoint_id": self.anatomy.timepoint_id}, "anatomy_id": self.anatomy.structure_id, "tissue_id": self.tissue.tissue_id, "histology_id": self.histology.histology_id if self.histology else None, "cell_id": self.cell.cell_id if self.cell else None, "state_assessment_id": self.state_assessment.assessment_id if self.state_assessment else None, "age_estimate_id": self.age_estimate.estimate_id if self.age_estimate else None}


def build_multiscale_chain(anatomy: AnatomicalStructure, tissue: TissueRegion, histology: HistologyRegion | None = None, cell: CellObject | None = None, state_assessment: BiologicalStateAssessment | None = None, age_estimate: BiologicalAgeEstimate | None = None) -> MultiscaleChain:
    chain = MultiscaleChain(anatomy, tissue, histology, cell, state_assessment, age_estimate)
    chain.validate()
    return chain
