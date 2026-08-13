from datetime import date, datetime, timezone

import pytest

from core import (
    AnatomicalLocation,
    Biomarker,
    BiologicalState,
    Measurement,
    Observation,
    Person,
    Timepoint,
    Uncertainty,
)


def test_measurement_preserves_provenance_and_quality():
    person = Person(id="P001")
    timepoint = Timepoint(id="T0", date=date(2026, 8, 13), label="baseline")
    location = AnatomicalLocation(id="skin", name="Skin", level="tissue")
    biomarker = Biomarker(id="cell_area", name="Cell area", category="morphology", unit="px2")
    quality = Uncertainty(confidence=0.91, quality_score=0.95)

    measurement = Measurement(
        id="M001",
        subject_id=person.id,
        timepoint_id=timepoint.id,
        modality="microscopy",
        biomarker=biomarker,
        value=123.4,
        measured_at=datetime.now(timezone.utc),
        anatomical_location=location,
        uncertainty=quality,
        source="microscope-01",
        model_version="morphology-v1",
    )

    assert measurement.subject_id == "P001"
    assert measurement.uncertainty.quality_score == 0.95
    assert measurement.anatomical_location.level == "tissue"


def test_biological_state_rejects_wrong_subject_or_timepoint():
    state = BiologicalState(subject_id="P001", timepoint_id="T0")
    observation = Observation(
        id="O001",
        subject_id="P002",
        timepoint_id="T0",
        name="example",
        value=1.0,
        observed_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError):
        state.add_observation(observation)


def test_biological_state_stores_dimensions():
    state = BiologicalState(subject_id="P001", timepoint_id="T0")
    state.set_dimension("skeletal_age", 57.2)

    assert state.get_dimension("skeletal_age") == 57.2
    assert state.get_dimension("unknown") is None


def test_uncertainty_validates_probability_range():
    with pytest.raises(ValueError):
        Uncertainty(confidence=1.5)
