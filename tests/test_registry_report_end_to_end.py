from backend.registry_report import build_registry_report
from backend.multiscale_registry import MultiscaleRegistry
from backend.anatomy_foundation import AnatomicalStructure, Geometry, SpatialReference


def test_registry_report_connects_snapshot_and_longitudinal_layers():
    registry = MultiscaleRegistry()
    registry.add_anatomy(AnatomicalStructure(
        structure_id="a1", subject_id="s1", hand_id="h1", timepoint_id="T1",
        anatomical_identity="skin", geometry=Geometry("g1", "volume", "f1"),
        source_data_ids=("d1",), spatial_reference=SpatialReference("f1"),
    ))
    report = build_registry_report(
        registry,
        subject_id="s1", hand_id="h1", timepoint_id="T1",
        longitudinal_observations=[
            {"subject_id": "s1", "zone": "cell:c1", "metric": "age",
             "timepoint": "T0", "value": 40.0},
            {"subject_id": "s1", "zone": "cell:c1", "metric": "age",
             "timepoint": "T1", "value": 42.0},
        ],
    )
    assert report["anatomy"][0]["structure_id"] == "a1"
    assert report["trends"][0]["delta"] == 2.0
    assert report["attention"][0]["zone_id"] == "cell:c1"
    # No registry cell exists for c1, so spatial projection must not invent coordinates.
    assert report["spatial_attention"] == []
