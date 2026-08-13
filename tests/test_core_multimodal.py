import unittest
from datetime import datetime, timezone

from core.biomarker import Biomarker
from core.measurement import Measurement
from core.multimodal import MultimodalObservationLayer
from core.observation import Observation


class MultimodalTests(unittest.TestCase):
    def _measurement(self, identifier, modality):
        biomarker = Biomarker(identifier=f"b-{identifier}", name="cell_density")
        return Measurement(
            id=identifier,
            subject_id="person-001",
            timepoint_id="T1",
            modality=modality,
            biomarker=biomarker,
            value=1.0,
            measured_at=datetime.now(timezone.utc),
        )

    def test_collects_multiple_modalities(self):
        layer = MultimodalObservationLayer()
        layer.add(self._measurement("mri-1", "MRI"))
        layer.add(self._measurement("micro-1", "microscopy"))
        batch = layer.for_timepoint("person-001", "T1")
        self.assertEqual(batch.modalities, ("MRI", "microscopy"))
        self.assertEqual(len(batch.records), 2)

    def test_observation_modality_is_preserved(self):
        layer = MultimodalObservationLayer()
        observation = Observation(
            id="o-1", subject_id="person-001", timepoint_id="T1",
            name="morphology_score", value=0.8,
            observed_at=datetime.now(timezone.utc),
            metadata={"modality": "histology", "pipeline": "v1"},
        )
        layer.add(observation)
        self.assertEqual(layer.modalities, ("histology",))
        self.assertEqual(layer.for_modality("histology")[0].id, "o-1")

    def test_empty_modality_is_rejected(self):
        with self.assertRaises(ValueError):
            MultimodalObservationLayer().for_modality(" ")


if __name__ == "__main__":
    unittest.main()
