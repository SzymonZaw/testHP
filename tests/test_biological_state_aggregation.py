from datetime import datetime

from core import AnatomicalLocation, BiologicalStateAggregator, Evidence, Observation


def make_observation(oid, location, level="macro", metadata=None):
    return Observation(
        id=oid,
        subject_id="s1",
        timepoint_id="T0",
        name=oid,
        value=1,
        observed_at=datetime(2026, 1, 1),
        anatomical_location=location,
        biological_level=level,
        metadata=metadata or {},
    )


def test_empty_scope_is_explicitly_insufficient():
    palm = AnatomicalLocation("palm", "Palm", "site")
    aggregator = BiologicalStateAggregator([], [], [palm])
    summary = aggregator.summarize_location("palm")
    assert summary.count == 0
    assert summary.status == "insufficient_evidence"


def test_parent_summary_uses_explicit_descendant_evidence():
    palm = AnatomicalLocation("palm", "Palm", "site")
    central = AnatomicalLocation("central", "Central palm", "site", parent_id="palm")
    obs = make_observation("o1", central, "cellular")
    evidence = Evidence(id="e1", subject_id="s1", observation_id="o1")
    aggregator = BiologicalStateAggregator([obs], [evidence], [palm, central])

    summary = aggregator.summarize_location("palm", include_descendants=True)
    assert summary.evidence_ids == ("e1",)
    assert summary.count == 1
    assert summary.status == "observed"


def test_state_does_not_invent_interpretation_without_validated_value():
    palm = AnatomicalLocation("palm", "Palm", "site")
    obs = make_observation("o1", palm)
    evidence = Evidence(id="e1", subject_id="s1", observation_id="o1")
    state = BiologicalStateAggregator([obs], [evidence], [palm]).build_state("s1", "T0", location_id="palm")

    assert state.evidence_count == 1
    assert state.availability == "observed"
    assert state.interpretations == {}


def test_validated_interpretation_is_scoped_to_evidence():
    palm = AnatomicalLocation("palm", "Palm", "site")
    obs = make_observation(
        "o1", palm, metadata={"validated_interpretations": {"damage": "none_observed"}}
    )
    evidence = Evidence(id="e1", subject_id="s1", observation_id="o1")
    state = BiologicalStateAggregator([obs], [evidence], [palm]).build_state("s1", "T0", location_id="palm")

    assert state.interpretation("damage") == "none_observed"
