from datetime import datetime

from digital_twin.biological_age import BiologicalAge
from digital_twin.cell_state import CellState
from digital_twin.individual_cell import IndividualCellState
from digital_twin.risk_state import RiskState
from digital_twin.spatial import CellLocation, HandRegion, HandSpatialModel, SpatialPoint, TissueRegion
from digital_twin.temporal_state import TemporalState
from digital_twin.tissue_state import TissueState
from digital_twin.twin import DigitalTwin


def build_twin() -> DigitalTwin:
    spatial = HandSpatialModel(coordinate_system="hand-mm", metadata={"scanner": "test"})
    region = HandRegion(region_id="palm", name="Palm", side="left")
    tissue = TissueRegion(tissue_id="skin-1", tissue_type="skin", region_id="palm")
    tissue.add_cell(CellLocation(
        cell_id="cell-1", position=SpatialPoint(1, 2, 3, "hand-mm"),
        tissue_id="skin-1", cell_type="keratinocyte", confidence=0.97,
    ))
    region.add_tissue(tissue)
    spatial.add_region(region)

    temporal = TemporalState()
    temporal.add_timepoint("T0", biological_age=42.0, overall_risk=0.12, tissue_state={"x": 1}, cell_state={"y": 2})

    twin = DigitalTwin(
        subject_id="subject-1",
        tissue_state=TissueState(thickness=1.2, confidence=0.91),
        cell_state=CellState(total_cell_count=1000, cellular_abnormality_score=0.08),
        biological_age=BiologicalAge(chronological_age=40, biological_age=42, confidence=0.88),
        risk_state=RiskState(overall_risk=0.12, confidence=0.85),
        temporal_state=temporal,
        spatial_model=spatial,
        metadata={"study": "roundtrip"},
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-02T00:00:00",
    )
    twin.add_cell_state(IndividualCellState(
        cell_id="cell-1", observed_at=datetime(2026, 1, 1),
        senescence=0.2, abnormality=0.1, biological_age=43.0,
        confidence=0.92, biomarkers={"marker_a": 1.4},
    ))
    return twin


def test_snapshot_roundtrip_preserves_all_layers(tmp_path):
    original = build_twin()
    path = tmp_path / "twin.json"

    original.save(path)
    restored = DigitalTwin.load(path)

    assert restored.snapshot() == original.snapshot()
    assert restored.tissue_state.thickness == 1.2
    assert restored.cell_state.total_cell_count == 1000
    assert restored.biological_age.biological_age == 42
    assert restored.risk_state.overall_risk == 0.12
    assert restored.temporal_state.get_timepoint("T0").biological_age == 42.0
    assert restored.spatial_model.regions["palm"].tissues["skin-1"].cells["cell-1"].position.z == 3
    assert restored.cell_state_history("cell-1")[0].biological_age == 43.0


def test_load_supports_snapshots_without_new_optional_layers(tmp_path):
    original = build_twin().snapshot()
    original.pop("cell_timeline")
    path = tmp_path / "legacy.json"
    path.write_text(__import__("json").dumps(original), encoding="utf-8")

    restored = DigitalTwin.load(path)

    assert restored.subject_id == "subject-1"
    assert restored.cell_timeline.states == {}
    assert restored.spatial_model.regions["palm"].tissues["skin-1"].cells["cell-1"].cell_type == "keratinocyte"
