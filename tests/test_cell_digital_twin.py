from backend.anatomy_foundation import CellObject, SpatialReference
from backend.canonical_cell_state import build_canonical_cell_state
from backend.cell_digital_twin import build_cell_digital_twin


def make_cell():
    return CellObject(
        "c1", "t1", "s1", "h1", "T1",
        {"x": 1.0, "y": 2.0, "z": 3.0},
        "keratinocyte", {"area": 12.5}, {"diameter": 4.0}, {"area": 3.0},
        (), ("dataset-1",), SpatialReference("frame:T1"), 0.95,
    )


def test_cell_twin_preserves_canonical_snapshot_identity():
    twin = build_cell_digital_twin(build_canonical_cell_state(make_cell()))
    data = twin.to_dict()
    assert data["identity"] == {
        "cell_id": "c1",
        "subject_id": "s1",
        "hand_id": "h1",
        "tissue_id": "t1",
        "timepoint_id": "T1",
    }
    assert data["snapshot"]["cell"]["cell_id"] == "c1"
    assert data["snapshot"]["state"]["state"] == "uncertain"


def test_cell_twin_rejects_mismatched_trajectory():
    from backend.longitudinal_cells import CellTimepointRecord, build_cell_trajectory

    trajectory = build_cell_trajectory([CellTimepointRecord("other", "s1", "h1", "T1")])
    try:
        build_cell_digital_twin(build_canonical_cell_state(make_cell()), trajectory=trajectory)
    except ValueError as exc:
        assert "identity" in str(exc)
    else:
        raise AssertionError("expected identity mismatch to be rejected")


def test_cell_twin_requires_snapshot_timepoint_in_trajectory():
    from backend.longitudinal_cells import CellTimepointRecord, build_cell_trajectory

    trajectory = build_cell_trajectory([CellTimepointRecord("c1", "s1", "h1", "T0")])
    try:
        build_cell_digital_twin(build_canonical_cell_state(make_cell()), trajectory=trajectory)
    except ValueError as exc:
        assert "snapshot timepoint" in str(exc)
    else:
        raise AssertionError("expected missing snapshot timepoint to be rejected")
