import pytest

from backend.anatomy_foundation import CellObject, CellStateAssessment, SpatialReference, Evidence
from backend.biological_state import BiologicalAgeEstimate, InterpretationEvidence
from backend.data_foundation import Provenance, Uncertainty
from decision.spatial_cell_signals import project_cell_signals


def cell(cell_id, x):
    return CellObject(cell_id, "t1", "s1", "h1", "T0", {"x": x, "y": 2.0, "z": 3.0}, "keratinocyte", {}, {"diameter": 4}, {}, (), ("slide1",), SpatialReference("hand-frame"))


def assessment(cell_id):
    return CellStateAssessment("a-" + cell_id, cell_id, "senescent", 0.8, (Evidence("e-" + cell_id, ("slide1",), "morphology", {}, 0.9),), Provenance(), "2026-08-27T00:00:00+00:00")


def age(cell_id):
    return BiologicalAgeEstimate("age-" + cell_id, "s1", "h1", "T0", cell_id, 47, Uncertainty(kind="test", interval=(46, 48)), (InterpretationEvidence("ae-" + cell_id, ("slide1",), "age", {}, 0.9),), Provenance(), "2026-08-27T00:00:00+00:00", "age-model", "1")


def test_projection_preserves_where_and_joins_observations():
    result = project_cell_signals("t1", [cell("c1", 1), cell("c2", 9)], [assessment("c1")], [age("c1")])
    assert result[0].position == {"x": 1, "y": 2.0, "z": 3.0}
    assert result[0].state == "senescent"
    assert result[0].biological_age_years == 47
    assert result[1].state is None


def test_projection_rejects_cross_tissue_assessments():
    with pytest.raises(ValueError):
        project_cell_signals("t1", [cell("c1", 1)], [assessment("c2")])
