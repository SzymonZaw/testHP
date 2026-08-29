from backend.biological_hierarchy import BiologicalObservation
from backend.biological_timeline import BiologicalTimeline
from backend.biological_trajectory import BiologicalTrajectory


def obs(observation_id, timestamp, value):
    return BiologicalObservation(observation_id, "test", timestamp, {"marker": value}, confidence=0.9)


def test_trajectory_summarizes_observed_trend():
    timeline = BiologicalTimeline((
        obs("a", "2026-01-01", 0.80),
        obs("b", "2027-01-01", 0.70),
        obs("c", "2028-01-01", 0.60),
    ))
    trajectory = BiologicalTrajectory.from_timeline(timeline, "marker")

    assert trajectory.observation_count == 3
    assert trajectory.total_delta == -0.2
    assert trajectory.mean_delta == -0.1
    assert trajectory.direction == "decreasing"


def test_trajectory_needs_multiple_numeric_observations():
    timeline = BiologicalTimeline((obs("a", "2026-01-01", 0.80),))
    trajectory = BiologicalTrajectory.from_timeline(timeline, "marker")

    assert trajectory.observation_count == 0
    assert trajectory.direction == "insufficient_data"
    assert trajectory.mean_delta is None
