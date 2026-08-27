import pytest

from backend.anatomy_foundation import CellObject, CellStateAssessment, SpatialReference, Evidence
from backend.biological_state import BiologicalAgeEstimate
from backend.data_foundation import Provenance, Uncertainty
from decision.multiscale_summary import summarize_tissue


def cell(cell_id: str) -> CellObject:
    return CellObject(
        cell_id, "t1", "s1", "h1", "T0", {"x": 0, "y": 0, "z": 0},
        "keratinocyte", {}, {"diameter": 4}, {}, (), ("slide1",),
        SpatialReference("hand-frame"),
    )


def assessment(cell_id: str, state: str, confidence: float = 0.8) -> CellStateAssessment:
    return CellStateAssessment(
        f"a-{cell_id}", cell_id, state, confidence,
        (Evidence(f"e-{cell_id}", ("slide1",), "morphology", {"area": 1}, confidence),),
        Provenance(), "2026-08-27T00:00:00+00:00",
    )


def age(cell_id: str, years: float) -> BiologicalAgeEstimate:
    return BiologicalAgeEstimate(
        f"age-{cell_id}", "s1", "h1", "T0", cell_id, years,
        Uncertainty(kind="test", interval=(years - 1, years + 1)),
        ( __import__("backend.biological_state", fromlist=["InterpretationEvidence"]).InterpretationEvidence(
            f"ae-{cell_id}", ("slide1",), "age", {"years": years}, 0.9
        ),), Provenance(), "2026-08-27T00:00:00+00:00", "age-model", "1",
    )


def test_summary_aggregates_cell_state_and_age():
    result = summarize_tissue(
        "t1", [cell("c1"), cell("c2")],
        [assessment("c1", "normal"), assessment("c2", "senescent", 0.6)],
        [age("c1", 41), age("c2", 47)],
    )
    assert result.cell_count == 2
    assert result.state_counts == {"normal": 1, "senescent": 1}
    assert result.assessed_fraction == 1.0
    assert result.mean_cell_confidence == pytest.approx(0.7)
    assert result.mean_biological_age_years == pytest.approx(44)
    assert result.biological_age_min_years == 41
    assert result.biological_age_max_years == 47
    assert result.signal == "observed"


def test_pathological_observation_is_explicit_but_not_a_treatment_decision():
    result = summarize_tissue("t1", [cell("c1")], [assessment("c1", "pathological")])
    assert result.signal == "pathology_observed"


def test_partial_assessment_is_insufficient_evidence():
    result = summarize_tissue("t1", [cell("c1"), cell("c2")], [assessment("c1", "normal")])
    assert result.assessed_fraction == 0.5
    assert result.signal == "insufficient_evidence"


def test_cross_tissue_objects_are_rejected():
    with pytest.raises(ValueError):
        summarize_tissue("t1", [cell("c1")], [assessment("c2", "normal")])
