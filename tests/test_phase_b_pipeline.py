import pytest

from backend.anatomy_foundation import Geometry, SpatialReference, TissueRegion
from backend.anatomy_segmentation import SegmentationEvidence, segmentation_to_anatomy
from backend.cell_pipeline import CellSegmentationEvidence, cell_from_segmentation
from backend.tissue_histology import bind_histology


def test_segmentation_requires_source_and_explicit_registration():
    evidence = SegmentationEvidence("seg1", ("mri1",), "mri", "muscle", "mri-frame", Geometry("g1", "volume", "hand-frame"), "test-model")
    anatomy = segmentation_to_anatomy(evidence, structure_id="a1", subject_id="s1", hand_id="h1", timepoint_id="t1", hand_frame="hand-frame", registration_id="reg1", confidence=.8)
    assert anatomy.spatial_reference.transform["registration_id"] == "reg1"


def test_tissue_and_histology_preserve_subject_hand_timepoint():
    tissue = TissueRegion("t1", "a1", "s1", "h1", "tp1", "dermis", Geometry("g", "volume", "hand-frame"), ("mri1",), SpatialReference("hand-frame"), .9)
    histology = bind_histology(histology_id="hist1", tissue=tissue, image_data_id="slide1", method="H&E", region_geometry=Geometry("hg", "surface", "hand-frame"), spatial_reference=SpatialReference("hand-frame"))
    assert (histology.subject_id, histology.hand_id, histology.timepoint_id) == ("s1", "h1", "tp1")


def test_cell_pipeline_requires_source_and_matching_segmentation():
    evidence = CellSegmentationEvidence("seg", "t1", ("slide1",), ({"cell_id": "c1"},), "cellpose")
    cell = cell_from_segmentation(evidence, {"cell_id": "c1", "position": {"x": 1}}, subject_id="s1", hand_id="h1", timepoint_id="tp1", hand_frame="hand-frame")
    assert cell.cell_id == "c1"
    with pytest.raises(ValueError):
        cell_from_segmentation(evidence, {"cell_id": "c2"}, subject_id="s1", hand_id="h1", timepoint_id="tp1", hand_frame="hand-frame")
