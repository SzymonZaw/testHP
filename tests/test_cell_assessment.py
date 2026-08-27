import pytest

from backend.anatomy_foundation import CellObject, Evidence, Geometry, Provenance, SpatialReference
from backend.cell_assessment import build_cell_state_assessment


def make_cell():
    return CellObject(
        "cell-1", "tissue-1", "s1", "h1", "T0",
        {"x": 1.0, "y": 2.0, "z": 3.0}, "keratinocyte",
        {"area": 12.5}, {"diameter": 4.0}, {"area": 3.0},
        (), ("slide-1",), SpatialReference("hand-frame"),
    )


def make_evidence():
    return (Evidence("ev-1", ("slide-1",), "morphology", {"area": 12.5}, 0.9),)


def test_cell_state_assessment_is_bound_to_exact_cell():
    assessment = build_cell_state_assessment(
        make_cell(), assessment_id="a-1", state="senescent", confidence=0.82,
        evidence=make_evidence(), provenance=Provenance(),
        assessed_at="2026-08-27T00:00:00+00:00",
    )
    assert assessment.cell_id == "cell-1"
    assert assessment.state == "senescent"
    assert assessment.evidence[0].source_data_ids == ("slide-1",)


def test_cell_state_assessment_requires_traceable_evidence():
    with pytest.raises(ValueError, match="source_data_ids"):
        build_cell_state_assessment(
            make_cell(), assessment_id="a-1", state="normal", confidence=0.9,
            evidence=(Evidence("ev-1", (), "morphology", {}),),
            provenance=Provenance(), assessed_at="2026-08-27T00:00:00+00:00",
        )


def test_cell_state_assessment_rejects_invalid_confidence():
    with pytest.raises(ValueError, match="confidence"):
        build_cell_state_assessment(
            make_cell(), assessment_id="a-1", state="normal", confidence=1.1,
            evidence=make_evidence(), provenance=Provenance(),
            assessed_at="2026-08-27T00:00:00+00:00",
        )
