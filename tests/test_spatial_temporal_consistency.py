"""v0.2 contract test: spatial hierarchy is reversible and time is lossless.

Synthetic data only. This validates identifiers, parent links and timeline
identity; it does not claim biological validity.
"""

from datetime import datetime, timedelta

from digital_twin.spatial import CellLocation, HandRegion, HandSpatialModel, SpatialPoint, TissueRegion
from digital_twin.twin import DigitalTwin
from digital_twin.individual_cell import IndividualCellState


def _make_twin():
    spatial = HandSpatialModel()
    for region_id in ("palm", "index"):
        region = HandRegion(region_id=region_id, name=region_id.title(), side="left")
        tissue = TissueRegion(tissue_id=f"{region_id}-skin", tissue_type="skin", region_id=region_id)
        region.add_tissue(tissue)
        spatial.add_region(region)
        for i in range(3):
            tissue.add_cell(CellLocation(
                cell_id=f"{region_id}-cell-{i}",
                point=SpatialPoint(float(i), 0.0, 0.0),
                tissue_id=tissue.tissue_id,
            ))
    return DigitalTwin("synthetic-v02", spatial_model=spatial)


def test_spatial_hierarchy_is_bidirectional_and_temporally_consistent():
    twin = _make_twin()
    t0 = datetime(2026, 1, 1)
    t1 = t0 + timedelta(days=30)
    cell_id = "index-cell-2"

    twin.add_cell_state(IndividualCellState(cell_id=cell_id, observed_at=t0, biological_age=35, abnormality=.10, confidence=.9))
    twin.add_cell_state(IndividualCellState(cell_id=cell_id, observed_at=t1, biological_age=37, abnormality=.20, confidence=.9))

    location = twin.spatial_model.find_cell(cell_id)
    assert location is not None
    assert location.tissue_id == "index-skin"

    tissue = twin.spatial_model.regions["index"].tissues[location.tissue_id]
    assert cell_id in tissue.cells
    assert twin.spatial_model.regions["index"].region_id == "index"

    # Reverse traversal: cell -> tissue -> region -> hand.
    assert tissue.region_id == "index"
    assert "index" in twin.spatial_model.regions
    assert location.point.x == 2.0

    timeline = twin.cell_timeline.states[cell_id]
    assert [state.observed_at for state in timeline] == [t0, t1]
    assert [state.biological_age for state in timeline] == [35, 37]
    assert [state.abnormality for state in timeline] == [.10, .20]

    # No identity drift: the same cell remains attached to the same spatial path.
    for state in timeline:
        assert state.cell_id == cell_id


def test_all_cells_have_unique_and_reversible_paths():
    twin = _make_twin()
    seen = set()
    for region_id, region in twin.spatial_model.regions.items():
        for tissue_id, tissue in region.tissues.items():
            assert tissue.region_id == region_id
            for cell_id, cell in tissue.cells.items():
                assert cell_id not in seen
                seen.add(cell_id)
                resolved = twin.spatial_model.find_cell(cell_id)
                assert resolved is not None
                assert resolved.tissue_id == tissue_id

    assert len(seen) == 6
