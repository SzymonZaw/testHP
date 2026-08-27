import pytest

from backend.anatomy_foundation import CellObject, Evidence
from backend.cell_age import estimate_cell_age
from backend.data_foundation import Provenance, SpatialReference, Uncertainty


def test_cell_age_requires_evidence_and_model_identity():
    cell = CellObject("c1", "t1", "s1", "h1", "T0", {"x": 1}, "keratinocyte", {}, {}, {}, (), ("slide1",), SpatialReference("hand-frame"))
    evidence = Evidence("e1", ("slide1",), "morphology", {"area": 10})
    estimate = estimate_cell_age(
        estimate_id="age1", cell=cell, biological_age_years=42.0,
        evidence=(evidence,), uncertainty=Uncertainty(interval=(39.0, 45.0)),
        provenance=Provenance(source_object_ids=("e1",)), model_id="research-model",
        model_version="1", assessed_at="2026-08-27T00:00:00+00:00")
    assert estimate.cell_id == "c1"
    assert estimate.biological_age_years == 42.0


def test_cell_age_rejects_negative_values_and_missing_evidence():
    cell = CellObject("c1", "t1", "s1", "h1", "T0", {"x": 1}, "keratinocyte", {}, {}, {}, (), ("slide1",), SpatialReference("hand-frame"))
    with pytest.raises(ValueError):
        estimate_cell_age(
            estimate_id="age1", cell=cell, biological_age_years=-1,
            evidence=(), uncertainty=Uncertainty(), provenance=Provenance(),
            model_id="research-model", model_version="1",
            assessed_at="2026-08-27T00:00:00+00:00")
