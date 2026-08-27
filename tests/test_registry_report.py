from backend.anatomy_foundation import AnatomicalStructure, CellObject, Geometry, HandCoordinateSystem, SpatialReference, TissueRegion
from backend.multiscale_registry import MultiscaleRegistry
from backend.registry_report import build_registry_report


def test_registry_report_reads_canonical_records():
    registry = MultiscaleRegistry()
    registry.add_coordinate_system(HandCoordinateSystem("f", "s1", "h1"))
    sr = SpatialReference("f")
    anatomy = AnatomicalStructure("a1", "s1", "h1", "T1", "skin", Geometry("g1", "volume", "f"), (), sr)
    tissue = TissueRegion("t1", "a1", "s1", "h1", "T1", "epidermis", Geometry("g2", "segmentation", "f"), (), sr)
    cell = CellObject("c1", "t1", "s1", "h1", "T1", {"x": 1, "y": 2, "z": 3}, "keratinocyte", {}, {}, {}, (), (), sr)
    registry.add_anatomy(anatomy)
    registry.add_tissue(tissue)
    registry.add_cell(cell)

    report = build_registry_report(registry, subject_id="s1", hand_id="h1", timepoint_id="T1")
    assert [x["structure_id"] for x in report["anatomy"]] == ["a1"]
    assert [x["tissue_id"] for x in report["tissues"]] == ["t1"]
    assert [x["cell_id"] for x in report["cells"]] == ["c1"]
    assert report["assessments"] == []
    assert report["biological_age"] == []
