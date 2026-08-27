import pytest

from backend.cell_biological_state import CellBiologicalState, EvidenceBundle, EvidenceItem


def evidence():
    return EvidenceBundle((EvidenceItem("e1", ("obs1",), "morphology", {"area": 12.5}, 0.91),))


def test_cell_state_preserves_evidence_and_context():
    state = CellBiologicalState(
        cell_id="c1", subject_id="s1", hand_id="h1", timepoint_id="T1",
        state="normal", biological_age_years=42.0, uncertainty=0.09,
        evidence=evidence(), tissue_id="t1", spatial_reference="frame:T1",
    )
    data = state.to_dict()
    assert data["state"] == "normal"
    assert data["biological_age_years"] == 42.0
    assert data["evidence"]["items"][0]["source_object_ids"] == ["obs1"]


def test_invalid_confidence_is_rejected():
    bad = EvidenceBundle((EvidenceItem("e1", ("obs1",), "test", {}, 1.2),))
    state = CellBiologicalState("c1", "s1", "h1", "T1", "uncertain", None, 0.5, bad)
    with pytest.raises(ValueError, match="confidence"):
        state.validate()


def test_invalid_state_is_rejected():
    state = CellBiologicalState("c1", "s1", "h1", "T1", "healthy", 40.0, 0.1, evidence())
    with pytest.raises(ValueError, match="state"):
        state.validate()
