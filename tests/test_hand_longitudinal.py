from backend.hand_longitudinal import (
    HAND_ZONES,
    HandTimepoint,
    SubjectRef,
    compare_numeric_observations,
    make_observation,
    rank_zones_by_change,
)


def test_hand_zones_are_stable():
    assert HAND_ZONES == ("wrist", "palm", "thumb", "index", "middle", "ring", "little")


def test_observation_requires_subject_session_and_timepoint():
    observation = make_observation(
        subject_id="S1",
        session_id="S1-T0",
        timepoint="T0",
        hand_id="left-hand-1",
        laterality="left",
        zone="palm",
        observation_type="geometry",
        metric="palm_width",
        value=82.5,
        unit="mm",
    )
    assert observation.value == 82.5


def test_timepoint_rejects_mismatched_subject():
    record = HandTimepoint(SubjectRef("S1", "SESSION-T0", "T0"))
    observation = make_observation(
        subject_id="S2",
        session_id="SESSION-T0",
        timepoint="T0",
        hand_id="left-hand-1",
        laterality="left",
        zone="palm",
        observation_type="geometry",
        metric="palm_width",
        value=82.5,
        unit="mm",
    )
    try:
        record.add(observation)
    except ValueError as exc:
        assert "subject_id" in str(exc)
    else:
        raise AssertionError("mismatched subject should be rejected")


def test_baseline_comparison_is_observational():
    baseline = [make_observation(
        subject_id="S1", session_id="S1-T0", timepoint="T0", hand_id="left-hand-1",
        laterality="left", zone="index", observation_type="geometry",
        metric="finger_length", value=72.0, unit="mm",
    )]
    current = [make_observation(
        subject_id="S1", session_id="S1-T1", timepoint="T1", hand_id="left-hand-1",
        laterality="left", zone="index", observation_type="geometry",
        metric="finger_length", value=73.0, unit="mm",
    )]
    changes = compare_numeric_observations(baseline, current)
    assert changes[0]["delta"] == 1.0
    assert changes[0]["evidence_level"] == "observed_change"
    assert changes[0]["interpretation"] is None


def test_zone_ranking_is_not_a_diagnosis():
    ranked = rank_zones_by_change([
        {"zone": "index", "relative_change": 0.2},
        {"zone": "palm", "relative_change": -0.05},
    ])
    assert ranked[0]["zone"] == "index"
    assert ranked[0]["interpretation"] is None
    assert ranked[0]["reason"] == "largest measured change relative to baseline"
