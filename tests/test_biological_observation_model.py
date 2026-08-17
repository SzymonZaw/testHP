from core import AnatomicalLocation, Artifact, DigitalTwinState, Evidence, Measurement, Observation, Person, Timepoint


def test_artifact_can_represent_non_image_evidence():
    artifact = Artifact(
        id="ART-001",
        subject_id="SUBJECT-001",
        timepoint_id="T0",
        modality="rna",
        uri="data/raw/rna/sample.tsv",
        media_type="text/tab-separated-values",
    )
    assert artifact.modality == "rna"
    assert artifact.media_type.startswith("text/")


def test_observation_and_measurement_share_subject_timepoint_and_region():
    location = AnatomicalLocation("hand.palm", "Palm", "site", parent_id="hand")
    person = Person("SUBJECT-001")
    timepoint = Timepoint("T0", "2026-08-17")
    assert person.id == "SUBJECT-001"
    assert timepoint.id == "T0"
    measurement = Measurement(
        id="MEAS-001",
        subject_id=person.id,
        timepoint_id=timepoint.id,
        modality="rgb",
        biomarker={"name": "mean_brightness"},
        value=0.42,
        measured_at=timepoint.as_datetime(),
        anatomical_location=location,
        unit="0-1",
    )
    observation = Observation(
        id="OBS-001",
        subject_id=person.id,
        timepoint_id=timepoint.id,
        name="surface_brightness_observation",
        value="within_observed_range",
        observed_at=timepoint.as_datetime(),
        anatomical_location=location,
        source_measurement_ids=[measurement.id],
    )
    assert observation.source_measurement_ids == ["MEAS-001"]
    assert observation.anatomical_location.id == "hand.palm"


def test_evidence_links_observation_to_artifact():
    evidence = Evidence(
        id="EVID-001",
        subject_id="SUBJECT-001",
        observation_id="OBS-001",
        artifact_ids=["ART-001"],
        measurement_ids=["MEAS-001"],
        confidence=0.9,
    )
    assert evidence.artifact_ids == ["ART-001"]
    assert evidence.confidence == 0.9


def test_digital_twin_state_keeps_dimensions_separate():
    twin = DigitalTwinState(subject_id="SUBJECT-001", entity_id="hand-1", entity_type="body_part")
    twin.add_zone("hand.palm", name="Palm", parent_id="hand")
    twin.link_observation("OBS-001", timepoint_id="T0", zone_id="hand.palm")
    twin.set_dimension("cell_age", {"status": "not_available"})
    twin.set_dimension("pathology", {"status": "not_available"})
    twin.set_dimension("damage", {"status": "not_available"})

    assert set(twin.state_dimensions) == {"cell_age", "pathology", "damage"}
    assert twin.history[0]["zone_id"] == "hand.palm"
