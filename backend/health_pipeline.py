from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .biological_age_contract import BiologicalAgeAssessment
from .cell_state_contract import CellHealthAssessment
from .pathology_contract import PathologySignal
from .risk_intervention_contract import InterventionMapEntry, RiskMapEntry


@dataclass(frozen=True)
class CellHealthPipelineResult:
    health: CellHealthAssessment
    biological_age: BiologicalAgeAssessment | None = None
    pathology: tuple[PathologySignal, ...] = ()


def assessable_result(*, health: CellHealthAssessment, biological_age: BiologicalAgeAssessment | None = None, pathology: tuple[PathologySignal, ...] = ()) -> CellHealthPipelineResult:
    """Package model outputs without claiming clinical diagnosis or treatment."""
    health.validate()
    if biological_age:
        biological_age.validate()
    for signal in pathology:
        signal.validate()
    return CellHealthPipelineResult(health, biological_age, pathology)
