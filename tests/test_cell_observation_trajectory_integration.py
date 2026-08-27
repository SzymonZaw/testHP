from backend.anatomy_foundation import CellObject, CellStateAssessment, Evidence, SpatialReference
from backend.biological_state import BiologicalAgeEstimate, Uncertainty, Provenance
from backend.cell_digital_twin import build_cell_digital_twin_from_observation
from backend.cell_observation import CellObservation
from backend.longitudinal_cells import CellTimepointRecord, build_cell_trajectory


def make_cell(timepoint="T1"):
    return CellObject(
        "c1", "t1", "s1", "h1", timepoint,
        {"x": 1.0, "y": 2.0, "z": 3.0}, "keratinocyte",
        {"area": 12.5}, {"diameter": 4.0}, {"area": 3.0},
        (), (f"dataset-{timepoint}",), SpatialReference(f"frame:{timepoint}"), 0.95,
    )


def make_observation(timepoint="T1", state="normal"):
    evidence = Evidence(f"obs:{timepoint}", (f"dataset-{timepoint}",), "cell_observation", {"timepoint": timepoint}, 0.9)
    assessment = CellStateAssessment(
        f"assessment:{timepoint}", "c1", state, 0.9, (evidence,),
        Provenance(), f"2026-08-27T00:00:00+00:00",
    )
    return CellObservation(
        observation_id=f"observation:{timepoint}", cell_id="c1", subject_id="s1", hand_id="h1",
        timepoint_id=timepoint, assessment=assessment, morphology={"area": 12.5},
        size={"diameter": 4.0}, nucleus={"area": 3.0}, neighbors=(),
        source_data_ids=(f"dataset-{timepoint}",), spatial_reference=SpatialReference(f"frame:{timepoint}"),
        confidence=0.9,
    )


def make_age(timepoint, years):
    return BiologicalAgeEstimate(
        f"age:{timepoint}", "s1", "h1", timepoint, "c1", years,
        Uncertainty(kind="test", interval=(years - 1, years + 1)),
        (f"dataset-{timepoint}",), Provenance(),
        "2026-08-27T00:00:00+00:00", "test-model", "1",
    )


def test_observation_builds_canonical_twin_and_longitudinal_trajectory():
    t0 = CellTimepointRecord("c1", "s1", "h1", "T0", biological_age=make_age("T0", 40.0))
    t1 = CellTimepointRecord("c1", "s1", "h1", "T1", assessment=make_observation("T1").assessment, biological_age=make_age("T1", 42.0))
    trajectory = build_cell_trajectory([t1, t0])

    twin = build_cell_digital_twin_from_observation(
        make_cell(), make_observation("T1"), age_estimate=make_age("T1", 42.0), trajectory=trajectory,
    )
    data = twin.to_dict()

    assert data["snapshot"]["state"]["state"] == "normal"
    assert data["snapshot"]["age_estimate"]["estimated_age_years"] == 42.0
    assert [point["timepoint_id"] for point in data["trajectory"]["points"]] == ["T0", "T1"]
    assert data["trajectory"]["points"][1]["biological_age_years"] == 42.0
    assert len(data["observations"]) == 1


def test_observation_cannot_be_attached_to_wrong_timepoint_cell():
    try:
        build_cell_digital_twin_from_observation(make_cell("T1"), make_observation("T0"))
    except ValueError as exc:
        assert "match supplied cell" in str(exc)
    else:
        raise AssertionError("expected observation identity mismatch to be rejected")
