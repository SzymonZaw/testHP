from datetime import datetime

from digital_twin.individual_cell import IndividualCellState
from digital_twin.spatial import CellLocation, HandRegion, SpatialPoint, TissueRegion
from digital_twin.twin import DigitalTwin


def test_twin_snapshot_roundtrip_preserves_all_layers(tmp_path):
    twin = DigitalTwin(subject_id="subject-1", metadata={"study": "demo"})
    twin.tissue_state.update({"thickness": 1.2, "tissue_abnormality_score": 0.2})
    twin.cell_state.update({"total_cell_count": 100, "cellular_abnormality_score": 0.1})
    twin.biological_age.biological_age = 42.5
    twin.biological_age.age_acceleration = 2.5
    twin.risk_state.overall_risk = 0.15
    twin.temporal_state.add_timepoint("t0", biological_age=42.5, overall_risk=0.15)

    region = HandRegion(region_id="palm", name="Palm", side="left")
    tissue = TissueRegion(tissue_id="skin-1", tissue_type="skin", region_id="palm")
    tissue.add_cell(CellLocation(
        cell_id="cell-1",
        position=SpatialPoint(1, 2, 3),
        tissue_id="skin-1",
        cell_type="keratinocyte",
        confidence=0.99,
    ))
    region.add_tissue(tissue)
    twin.spatial_model.add_region(region)
    twin.add_cell_state(IndividualCellState(
        cell_id="cell-1",
        observed_at=datetime(2026, 1, 1),
        senescence=0.2,
        abnormality=0.1,
        biological_age=41.0,
        confidence=0.95,
    ))

    path = tmp_path / "twin.json"
    twin.save(path)
    restored = DigitalTwin.load(path)

    assert restored.snapshot() == twin.snapshot()
    assert restored.temporal_state.get_timepoint("t0") is not None
    assert restored.spatial_model.locate_cell("cell-1").position.x == 1
    assert restored.cell_state_history("cell-1")[0].senescence == 0.2


def test_load_supports_legacy_snapshot_without_new_layers(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text('{"subject_id": "legacy"}', encoding="utf-8")

    twin = DigitalTwin.load(path)

    assert twin.subject_id == "legacy"
    assert twin.spatial_model.regions == {}
    assert twin.cell_timeline.states == {}
