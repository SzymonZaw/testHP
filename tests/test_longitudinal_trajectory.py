from backend.biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence
from backend.data_foundation import Provenance, Uncertainty
from decision.longitudinal_trajectory import build_longitudinal_trajectory


def assessment(aid, tp, cell, state):
    ev = InterpretationEvidence(f"ev-{aid}", ("slide",), "morphology", {}, 0.9)
    return BiologicalStateAssessment(
        aid, "s1", "h1", tp, cell, state, 0.9, (ev,),
        Uncertainty("test", score=0.1), Provenance(), f"2026-{tp[-2:]}-01T00:00:00+00:00",
    )


def age(eid, tp, cell, years):
    ev = InterpretationEvidence(f"ev-{eid}", ("slide",), "age", {}, 0.9)
    return BiologicalAgeEstimate(
        eid, "s1", "h1", tp, cell, years,
        Uncertainty("test", interval=(years - 1, years + 1)), (ev,), Provenance(),
        f"2026-{tp[-2:]}-01T00:00:00+00:00",
    )


def test_trajectory_tracks_age_trend_and_state_transition():
    result = build_longitudinal_trajectory(
        "s1", "h1",
        [assessment("a0", "T0", "c0", "normal"), assessment("a1", "T1", "c1", "senescent")],
        [age("e0", "T0", "c0", 42), age("e1", "T1", "c1", 45)],
    )
    assert [item.timepoint_id for item in result.timepoints] == ["T0", "T1"]
    assert result.biological_age_delta_years == 3
    assert result.biological_age_trend == "increasing"
    assert result.state_transitions == ("T1:normal->senescent",)


def test_trajectory_does_not_infer_trend_from_one_timepoint():
    result = build_longitudinal_trajectory(
        "s1", "h1", [assessment("a0", "T0", "c0", "normal")], [age("e0", "T0", "c0", 42)]
    )
    assert result.biological_age_delta_years is None
    assert result.biological_age_trend == "insufficient_evidence"
