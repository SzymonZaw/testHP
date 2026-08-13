"""Minimal example of the Stage 1 biological data model."""

from datetime import date, datetime, timezone

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


person = Person(id="P001")
timepoint = Timepoint(id="T0", date=date(2026, 8, 13), label="baseline")
location = AnatomicalLocation(id="skin", name="Skin", level="tissue")
biomarker = Biomarker(
    id="cell_area",
    name="Cell area",
    category="morphology",
    unit="px2",
)

measurement = Measurement(
    id="M001",
    subject_id=person.id,
    timepoint_id=timepoint.id,
    modality="microscopy",
    biomarker=biomarker,
    value=123.4,
    measured_at=datetime.now(timezone.utc),
    anatomical_location=location,
    uncertainty=Uncertainty(confidence=0.91, quality_score=0.95),
    source="microscope-01",
    model_version="morphology-v1",
)

observation = Observation(
    id="O001",
    subject_id=person.id,
    timepoint_id=timepoint.id,
    name="skin_cell_area",
    value=measurement.value,
    observed_at=measurement.measured_at,
    anatomical_location=location,
    uncertainty=measurement.uncertainty,
    source_measurement_ids=[measurement.id],
)

state = BiologicalState(subject_id=person.id, timepoint_id=timepoint.id)
state.add_observation(observation)
state.set_dimension("skin_morphology", 0.82)

print(state)
