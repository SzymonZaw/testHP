import pytest

from backend.anatomy_foundation import CellObject
from backend.cell_intelligence import observation_from_cell, make_prediction
from backend.data_foundation import Provenance, SpatialReference, Uncertainty


def make_cell():
    return CellObject(
        "c1", "t1", "s1", "h1", "T0",
        {"x": 1.0, "y": 2.0, "z": 3.0}, "keratinocyte",
        {"area": 12.5}, {"diameter": 4.0}, {"area": 3.0}, (),
        ("slide1",), SpatialReference("hand-frame", "registered", transform={"type": "identity"}),
        provenance=Provenance(source_object_ids=("slide1",), method="segmentation", method_version="1"),
    )


def test_observation_is_derived_from_cell_and_preserves_lineage():
    observation = observation_from_cell(make_cell(), "obs1")
    observation.validate()
    assert observation.cell_id == "c1"
    assert observation.features["area"] == 12.5
    assert observation.features["size.diameter"] == 4.0
    assert observation.source_object_ids == ("slide1",)


def test_prediction_converts_to_biological_state_assessment():
    cell = make_cell()
    observation = observation_from_cell(cell, "obs1")
    prediction = make_prediction(
        prediction_id="pred1", cell=cell, observation=observation,
        state="normal", confidence=0.93,
        uncertainty=Uncertainty(kind="model", score=0.07),
        model_id="cell-state-test", model_version="1.0",
        assessed_at="2026-08-27T00:00:00+00:00",
    )
    assessment = prediction.to_assessment()
    assert assessment.target_object_id == "c1"
    assert assessment.state == "normal"
    assert assessment.model_id == "cell-state-test"
    assert assessment.evidence[0].source_object_ids == ("obs1",)


def test_prediction_rejects_mismatched_timepoint():
    cell = make_cell()
    observation = observation_from_cell(cell, "obs1")
    bad = observation.__class__(**{**observation.__dict__, "timepoint_id": "T1"})
    with pytest.raises(ValueError, match="cell/timepoint"):
        make_prediction(
            prediction_id="pred1", cell=cell, observation=bad,
            state="normal", confidence=0.9,
            uncertainty=Uncertainty(kind="model", score=0.1),
            model_id="m", model_version="1", assessed_at="2026-08-27T00:00:00+00:00",
        )
