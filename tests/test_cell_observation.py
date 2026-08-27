import pytest

from backend.anatomy_foundation import CellObject
from backend.cell_observation import CellObservation, build_cell_observation
from backend.data_foundation import SpatialReference


def cell():
    return CellObject(
        "c1", "t1", "s1", "h1", "T1", {"x": 1.0, "y": 2.0, "z": 3.0},
        "keratinocyte", {}, {}, {}, (), ("img1",), SpatialReference("f1"),
    )


def test_observation_is_anchored_to_cell_identity():
    observation = build_cell_observation(
        cell(), observation_id="o1", modality="histology",
        source_data_ids=("img1",), measurements={"area_um2": 120.0},
    )
    assert observation.matches_cell(cell())
    assert observation.measurements["area_um2"] == 120.0


def test_observation_requires_source_data():
    with pytest.raises(ValueError, match="source data"):
        build_cell_observation(cell(), observation_id="o1", modality="histology", source_data_ids=())


def test_observation_rejects_mismatched_assessment_cell():
    from backend.anatomy_foundation import CellStateAssessment

    assessment = CellStateAssessment("a1", "other-cell", "normal", 0.9, (), __import__("backend.data_foundation", fromlist=["Provenance"]).Provenance(), "2026-08-27T00:00:00+00:00")
    observation = CellObservation(
        "o1", "c1", "s1", "h1", "t1", "T1", "histology", ("img1",),
        SpatialReference("f1"), assessment=assessment,
    )
    with pytest.raises(ValueError, match="match observation cell"):
        observation.validate()
