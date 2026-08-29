"""End-to-end tests for the technology-neutral cell ML pipeline."""
from __future__ import annotations

from .anatomy_foundation import CellObject
from .cell_observation import CellObservation
from .data_foundation import SpatialReference
from .ml_adapters import model_output_to_cell_assessment, observation_to_model_input
from .reference_cell_model import ReferenceCellModel


def _observation(damage_score: float = 0.0) -> CellObservation:
    cell = CellObject(
        cell_id="cell-1",
        subject_id="subject-1",
        hand_id="hand-1",
        timepoint_id="t1",
        spatial_reference=SpatialReference(system="hand", coordinates=(1.0, 2.0, 3.0)),
    )
    return CellObservation.from_cell(
        cell,
        observation_id="obs-1",
        acquisition_id="acq-1",
        modality="microscopy",
        morphology={"damage_score": damage_score},
    )


def test_reference_model_pipeline() -> None:
    observation = _observation(0.9)
    model_input = observation_to_model_input(observation)
    output = ReferenceCellModel().predict(model_input)
    assessment = model_output_to_cell_assessment(observation, output)

    assert output.prediction == "pathological"
    assert assessment.cell_id == observation.cell_id
    assert assessment.state == "pathological"
    assert assessment.evidence[-1].kind == "ml_prediction"


def test_reference_model_marks_low_damage_normal() -> None:
    observation = _observation(0.1)
    output = ReferenceCellModel().predict(observation_to_model_input(observation))
    assessment = model_output_to_cell_assessment(observation, output)

    assert output.prediction == "normal"
    assert assessment.state == "normal"
