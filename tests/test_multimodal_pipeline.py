import unittest

from core import AnatomicalLocation, BiologicalState, Observation
from pipelines.multimodal_pipeline import fuse_states


class MultimodalPipelineTests(unittest.TestCase):
    def _state(self, modality: str) -> BiologicalState:
        state = BiologicalState(subject_id="person-001", timepoint_id="T0")
        state.add_observation(
            Observation(
                id=f"{modality}-observation",
                subject_id="person-001",
                timepoint_id="T0",
                name=f"{modality}_marker",
                value=1.0,
                observed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                anatomical_location=AnatomicalLocation(id="skin", name="Skin", level="tissue"),
            )
        )
        state.set_dimension("marker", 1.0)
        return state

    def test_multiple_modalities_share_one_state(self):
        fused = fuse_states([
            ("cell", self._state("cell")),
            ("tissue", self._state("tissue")),
            ("rna", self._state("rna")),
        ])
        self.assertEqual(fused.modality_names, ["cell", "rna", "tissue"])
        self.assertEqual(len(fused.state.observations), 3)
        self.assertIn("cell.marker", fused.state.dimensions)
        self.assertIn("rna.marker", fused.state.dimensions)
        self.assertIn("tissue.marker", fused.state.dimensions)

    def test_subject_mismatch_is_rejected(self):
        first = self._state("cell")
        other = BiologicalState(subject_id="person-002", timepoint_id="T0")
        with self.assertRaises(ValueError):
            fuse_states([("cell", first), ("rna", other)])

    def test_timepoint_mismatch_is_rejected(self):
        first = self._state("cell")
        other = BiologicalState(subject_id="person-001", timepoint_id="T1")
        with self.assertRaises(ValueError):
            fuse_states([("cell", first), ("rna", other)])


if __name__ == "__main__":
    unittest.main()
