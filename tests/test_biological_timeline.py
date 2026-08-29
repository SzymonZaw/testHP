from backend.biological_hierarchy import BiologicalObservation
from backend.biological_timeline import BiologicalTimeline


def observation(observation_id, timestamp, value):
    return BiologicalObservation(
        observation_id=observation_id,
        source="test",
        timestamp=timestamp,
        values={"marker_x": value},
        confidence=0.9,
    )


def test_timeline_orders_observations_chronologically():
    timeline = BiologicalTimeline((
        observation("late", "2028-01-01", 0.6),
        observation("early", "2026-01-01", 0.8),
        observation("middle", "2027-01-01", 0.7),
    ))

    assert [item.observation_id for item in timeline.observations] == ["early", "middle", "late"]
    assert timeline.latest().observation_id == "late"


def test_timeline_calculates_observed_numeric_changes():
    timeline = BiologicalTimeline((
        observation("a", "2026-01-01", 0.8),
        observation("b", "2027-01-01", 0.7),
        observation("c", "2028-01-01", 0.7),
    ))

    changes = timeline.changes("marker_x")
    assert [change.delta for change in changes] == [-0.1, 0.0]
    assert [change.direction for change in changes] == ["decreasing", "stable"]


def test_timeline_ignores_non_numeric_values():
    timeline = BiologicalTimeline((
        BiologicalObservation("a", "2026-01-01", values={"state": "healthy"}),
        BiologicalObservation("b", "2027-01-01", values={"state": "abnormal"}),
    ))

    assert timeline.changes("state") == ()
