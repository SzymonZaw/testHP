import pytest

from backend.anatomy_foundation import CellObject, Geometry, TissueRegion
from backend.cell_intelligence import make_prediction, observation_from_cell
from backend.data_foundation import Provenance, SpatialReference, Uncertainty
from backend.tissue_intelligence import observe_tissue, summarize_tissue_states


def make_tissue():
    return TissueRegion(
        "t1", "a1", "s1", "h1", "T0", "epidermis",
        Geometry("g1", "segmentation", "hand-frame"), ("slide1",),
        SpatialReference("hand-frame", "registered", transform={"type": "identity"}),
        provenance=Provenance(source_object_ids=("slide1",), method="segmentation", method_version="1"),
    )


def make_cell(cell_id, area):
    return CellObject(
        cell_id, "t1", "s1", "h1", "T0", {"x": 1.0, "y": 2.0, "z": 3.0}, "keratinocyte",
        {"area": area}, {"diameter": 4.0}, {"area": 3.0}, (), ("slide1",),
        SpatialReference("hand-frame", "registered", transform={"type": "identity"}),
        provenance=Provenance(source_object_ids=("slide1",), method="segmentation", method_version="1"),
    )


def prediction(cell, state, prediction_id):
    observation = observation_from_cell(cell, f"{prediction_id}:obs")
    return make_prediction(
        prediction_id=prediction_id, cell=cell, observation=observation,
        state=state, confidence=0.9, uncertainty=Uncertainty(kind="model", score=0.1),
        model_id="cell-model", model_version="1", assessed_at="2026-08-27T00:00:00+00:00",
    )


def test_observe_tissue_aggregates_numeric_cell_features_and_lineage():
    observation = observe_tissue(make_tissue(), (make_cell("c1", 10), make_cell("c2", 20)), "tobs")
    observation.validate()
    assert observation.cell_count == 2
    assert observation.feature_means["area"] == 15
    assert observation.source_object_ids == ("slide1",)


def test_tissue_state_summary_preserves_cell_prediction_lineage():
    tissue = make_tissue()
    predictions = (prediction(make_cell("c1", 10), "normal", "p1"), prediction(make_cell("c2", 20), "normal", "p2"), prediction(make_cell("c3", 30), "atypical", "p3"))
    summary = summarize_tissue_states(tissue, predictions, summary_id="ts1", assessed_at="2026-08-27T00:00:00+00:00")
    summary.validate()
    assert summary.dominant_state == "normal"
    assert summary.confidence == pytest.approx(2 / 3)
    assert summary.state_fractions["atypical"] == pytest.approx(1 / 3)
    assessment = summary.to_assessment()
    assert assessment.target_object_id == "t1"
    assert set(assessment.evidence[0].source_object_ids) == {"p1", "p2", "p3"}


def test_tissue_summary_rejects_prediction_from_other_timepoint():
    tissue = make_tissue()
    bad = prediction(make_cell("c1", 10), "normal", "p1")
    bad = bad.__class__(**{**bad.__dict__, "timepoint_id": "T1"})
    with pytest.raises(ValueError, match="tissue/subject/hand/timepoint"):
        summarize_tissue_states(tissue, (bad,), summary_id="ts1", assessed_at="2026-08-27T00:00:00+00:00")
