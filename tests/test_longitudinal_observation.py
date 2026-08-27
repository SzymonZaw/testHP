import pytest

from backend.longitudinal_observation import LongitudinalObservation


def test_cell_observation_preserves_multiscale_context():
    obs = LongitudinalObservation(
        observation_id="o1", subject_id="s1", hand_id="h1", timepoint_id="T1",
        zone_id="c1", level="cell", metric="biological_age_years", value=42.0,
        spatial_reference="hand-frame:T1", cell_id="c1", tissue_id="t1",
    )
    data = obs.to_dict()
    assert data["cell_id"] == "c1"
    assert data["tissue_id"] == "t1"
    assert data["spatial_reference"] == "hand-frame:T1"


def test_cell_observation_requires_cell_id():
    obs = LongitudinalObservation(
        observation_id="o1", subject_id="s1", hand_id="h1", timepoint_id="T1",
        zone_id="c1", level="cell", metric="age", value=42.0,
    )
    with pytest.raises(ValueError, match="cell_id"):
        obs.validate()
