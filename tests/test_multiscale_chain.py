import pytest

from backend.anatomy_foundation import AnatomicalStructure, CellObject, Geometry, HistologyRegion, TissueRegion
from backend.biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence
from backend.data_foundation import Provenance, SpatialReference, Uncertainty
from backend.multiscale_chain import build_multiscale_chain


CTX = dict(subject_id="s1", hand_id="h1", timepoint_id="T0")
SR = SpatialReference("hand-frame", "registered", transform={"type": "identity", "version": "1"})
PROV = Provenance(source_object_ids=("dataset-1",), method="test", method_version="1")


def make_objects():
    anatomy = AnatomicalStructure(
        "a1", **CTX, anatomical_identity="skin",
        geometry=Geometry("g1", "volume", "hand-frame"),
        source_data_ids=("dataset-1",), spatial_reference=SR, provenance=PROV,
    )
    tissue = TissueRegion(
        "t1", "a1", **CTX, tissue_type="epidermis",
        geometry=Geometry("g2", "segmentation", "hand-frame"),
        source_data_ids=("dataset-1",), spatial_reference=SR, provenance=PROV,
    )
    histology = HistologyRegion(
        "hist1", "t1", **CTX, method="H&E", image_data_id="slide1",
        region_geometry=Geometry("g3", "surface", "hand-frame"), spatial_reference=SR, provenance=PROV,
    )
    cell = CellObject(
        "c1", "t1", **CTX, position={"x": 1.0, "y": 2.0, "z": 3.0},
        cell_type="keratinocyte", morphology={"area": 12.5}, size={"diameter": 4.0},
        nucleus={"area": 3.0}, neighbors=(), source_data_ids=("dataset-1",),
        spatial_reference=SR, provenance=PROV,
    )
    evidence = InterpretationEvidence("e1", ("c1",), "morphology", {"area": 12.5}, 0.9, PROV)
    state = BiologicalStateAssessment(
        "as1", **CTX, target_object_id="c1", state="normal", confidence=0.9,
        evidence=(evidence,), uncertainty=Uncertainty("test", 0.1), provenance=PROV,
        assessed_at="2026-08-27T00:00:00+00:00", model_id="test-model", model_version="1",
    )
    age = BiologicalAgeEstimate(
        "age1", **CTX, target_object_id="c1", estimated_age_years=42.0,
        uncertainty=Uncertainty("test", interval=(39.0, 45.0)), evidence=(evidence,),
        provenance=PROV, assessed_at="2026-08-27T00:00:00+00:00", model_id="age-model", model_version="1",
    )
    return anatomy, tissue, histology, cell, state, age


def test_complete_chain_is_auditable():
    chain = build_multiscale_chain(*make_objects())
    assert chain.to_dict() == {
        "context": {"subject_id": "s1", "hand_id": "h1", "timepoint_id": "T0"},
        "anatomy_id": "a1", "tissue_id": "t1", "histology_id": "hist1", "cell_id": "c1",
        "state_assessment_id": "as1", "age_estimate_id": "age1",
    }


def test_state_and_age_must_target_chain_cell():
    anatomy, tissue, histology, cell, state, age = make_objects()
    bad_state = BiologicalStateAssessment(
        "as2", **CTX, target_object_id="other-cell", state="normal", confidence=0.9,
        evidence=state.evidence, uncertainty=state.uncertainty, provenance=PROV,
        assessed_at=state.assessed_at,
    )
    with pytest.raises(ValueError, match="state assessment must target"):
        build_multiscale_chain(anatomy, tissue, cell=cell, state_assessment=bad_state)


def test_chain_rejects_cross_context_tissue():
    anatomy, tissue, histology, cell, state, age = make_objects()
    bad_tissue = TissueRegion(
        "t2", "a1", subject_id="other", hand_id="h1", timepoint_id="T0", tissue_type="epidermis",
        geometry=tissue.geometry, source_data_ids=tissue.source_data_ids, spatial_reference=SR, provenance=PROV,
    )
    with pytest.raises(ValueError, match="share subject/hand/timepoint"):
        build_multiscale_chain(anatomy, bad_tissue)


def test_partial_chain_is_supported_but_still_validated():
    anatomy, tissue, *_ = make_objects()
    chain = build_multiscale_chain(anatomy, tissue)
    assert chain.to_dict()["cell_id"] is None
    assert chain.to_dict()["state_assessment_id"] is None
    assert chain.to_dict()["age_estimate_id"] is None
