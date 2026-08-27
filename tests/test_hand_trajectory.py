import pytest

from decision.hand_trajectory import analyze_hand_trajectory


def test_hand_trajectory_detects_change_and_orders_timepoints():
    result = analyze_hand_trajectory(
        "s1", "h1",
        [("T2", 2.0, {"senescence_fraction": 0.30}),
         ("T0", 0.0, {"senescence_fraction": 0.10}),
         ("T1", 1.0, {"senescence_fraction": 0.20})],
    )
    assert result.timepoints == ("T0", "T1", "T2")
    assert result.signal == "changing_observation"
    assert result.trends[0].direction == "increasing"


def test_hand_trajectory_reports_insufficient_evidence():
    result = analyze_hand_trajectory("s1", "h1", [("T0", 0.0, {"marker": 1.0})], expected_timepoints=3)
    assert result.signal == "insufficient_evidence"
    assert result.evidence_fraction == pytest.approx(1 / 3)


def test_hand_trajectory_rejects_duplicate_timepoints():
    with pytest.raises(ValueError):
        analyze_hand_trajectory("s1", "h1", [("T0", 0.0, {}), ("T0", 1.0, {})])
