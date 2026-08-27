import pytest

from backend.anatomy_foundation import CellObject, Evidence
from backend.cell_biology import CellBiologicalProfile, assess_profile
from backend.data_foundation import Provenance, SpatialReference


def _cell():
    return CellObject("c1", "t1", "s1", "h1", "T0", {"x": 1.0}, "keratinocyte", {"area": 10}, {"diameter": 4}, {"area": 3}, (), ("slide1",), SpatialReference("hand-frame"))


def test_profile_preserves_cell_measurements_and_completeness():
    profile = CellBiologicalProfile.from_cell(_cell(), markers={"marker_a": 0.8}, evidence_ids=("e1",))
    assert profile.cell_id == "c1"
    assert profile.morphology["area"] == 10
    assert profile.completeness == pytest.approx(1.0)


def test_assessment_requires_linked_evidence():
    profile = CellBiologicalProfile.from_cell(_cell(), evidence_ids=("e1",))
    evidence = Evidence("e2", ("slide1",), "morphology", {"area": 10})
    with pytest.raises(ValueError):
        assess_profile(assessment_id="a1", profile=profile, state="normal", confidence=0.9, evidence=(evidence,), assessed_at="2026-08-27T00:00:00+00:00", provenance=Provenance())


def test_assessment_is_not_allowed_without_evidence():
    profile = CellBiologicalProfile.from_cell(_cell())
    with pytest.raises(ValueError):
        assess_profile(assessment_id="a1", profile=profile, state="unknown", confidence=None, evidence=(), assessed_at="2026-08-27T00:00:00+00:00", provenance=Provenance())
