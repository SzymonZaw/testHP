from backend.anatomy_foundation import CellObject, Geometry, SpatialReference
from backend.biological_state import BiologicalAgeEstimate, BiologicalStateAssessment
from backend.canonical_cell_state import build_canonical_cell_state
from backend.data_foundation import Provenance, Uncertainty


def cell():
    return CellObject(
        "c1", "t1", "s1", "h1", "T1", {"x": 1.0, "y": 2.0, "z": 3.0},
        "keratinocyte", {"area": 12.5}, {"diameter": 4.0}, {"area": 3.0},
        (), ("dataset-1",), SpatialReference("frame:T1"), 0.95,
    )


def test_canonical_state_contains_cell_and_age():
    age = BiologicalAgeEstimate(
        "age1", "s1", "h1", "T1", "c1", 42.0,
        Uncertainty(kind="test", interval=(40.0, 44.0)), (), Provenance(),
        "2026-08-27T00:00:00+00:00", "model", "1",
    )
    canonical = build_canonical_cell_state(cell(), age_estimate=age)
    data = canonical.to_dict()
    assert data["cell"]["cell_id"] == "c1"
    assert data["state"]["biological_age_years"] == 42.0
    assert data["state"]["tissue_id"] == "t1"


def test_missing_assessment_remains_uncertain():
    canonical = build_canonical_cell_state(cell())
    assert canonical.state.state == "uncertain"
    assert canonical.state.biological_age_years is None
