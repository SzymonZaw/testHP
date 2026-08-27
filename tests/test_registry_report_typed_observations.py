import pytest

from backend.anatomy_foundation import AnatomicalStructure, Geometry, SpatialReference
from backend.longitudinal_observation import LongitudinalObservation
from backend.multiscale_registry import MultiscaleRegistry
from backend.registry_report import build_registry_report


def make_registry():
    registry = MultiscaleRegistry()
    registry.add_anatomy(AnatomicalStructure(
        structure_id="a1", subject_id="s1", hand_id="h1", timepoint_id="T1",
        anatomical_identity="skin", geometry=Geometry("g1", "volume", "f1"),
        source_data_ids=("d1",), spatial_reference=SpatialReference("f1"),
    ))
    return registry


def obs(timepoint: str, value: float) -> LongitudinalObservation:
    return LongitudinalObservation(
        observation_id=f"o-{timepoint}", subject_id="s1", hand_id="h1",
        timepoint_id=timepoint, zone_id="c1", level="cell", metric="age",
        value=value, spatial_reference=f"hand-frame:{timepoint}", cell_id="c1",
        tissue_id="t1",
    )


def test_typed_observations_drive_t0_t1_trend_and_context():
    report = build_registry_report(
        make_registry(), subject_id="s1", hand_id="h1", timepoint_id="T1",
        longitudinal_observations=[obs("T0", 40.0), obs("T1", 42.0)],
    )
    assert report["trends"][0]["delta"] == 2.0
    assert report["attention"][0]["zone_id"] == "c1"


def test_report_rejects_observation_from_other_hand():
    foreign = LongitudinalObservation(
        observation_id="o1", subject_id="s1", hand_id="h2", timepoint_id="T1",
        zone_id="c1", level="cell", metric="age", value=42.0, cell_id="c1",
    )
    with pytest.raises(ValueError, match="context"):
        build_registry_report(make_registry(), subject_id="s1", hand_id="h1", timepoint_id="T1", longitudinal_observations=[foreign])
