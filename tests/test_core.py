import unittest
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


class TestCore(unittest.TestCase):
    def test_measurement_preserves_provenance_and_quality(self):
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

        self.assertEqual(measurement.subject_id, "P001")
        self.assertEqual(measurement.uncertainty.quality_score, 0.95)
        self.assertEqual(measurement.anatomical_location.level, "tissue")

    def test_biological_state_rejects_wrong_subject_or_timepoint(self):
        state = BiologicalState(subject_id="P001", timepoint_id="T0")
        observation = Observation(
            id="O001",
            subject_id="P002",
            timepoint_id="T0",
            name="example",
            value=1.0,
            observed_at=datetime.now(timezone.utc),
        )

        with self.assertRaises(ValueError):
            state.add_observation(observation)

    def test_biological_state_stores_dimensions(self):
        state = BiologicalState(subject_id="P001", timepoint_id="T0")
        state.set_dimension("skeletal_age", 57.2)

        self.assertEqual(state.get_dimension("skeletal_age"), 57.2)
        self.assertIsNone(state.get_dimension("unknown"))

    def test_uncertainty_validates_probability_range(self):
        with self.assertRaises(ValueError):
            Uncertainty(confidence=1.5)


if __name__ == "__main__":
    unittest.main()
