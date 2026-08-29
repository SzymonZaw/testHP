import unittest

from user_input_validator_v1 import validate_user_package


class UserInputValidatorTests(unittest.TestCase):
    def test_valid_hand_image_package_is_accepted(self):
        package = {
            "subject": {"subject_id": "demo-001"},
            "acquisition": {
                "timepoint_id": "T0",
                "acquisition_time": "2026-08-29T12:00:00Z",
                "anatomical_site": "hand",
                "laterality": "right",
            },
            "inputs": [{
                "input_id": "img-001",
                "kind": "hand_images",
                "uri": "file:///input/hand.jpg",
                "format": "jpg",
                "provenance": {"source_type": "user"},
            }],
        }
        report = validate_user_package(package)
        self.assertTrue(report.valid_contract)
        self.assertTrue(report.ready_for_any_processing)
        self.assertEqual(report.status, "READY")

    def test_missing_wsi_metadata_is_incomplete_not_accepted(self):
        package = {
            "subject": {"subject_id": "demo-001"},
            "acquisition": {
                "timepoint_id": "T0",
                "acquisition_time": "2026-08-29T12:00:00Z",
            },
            "inputs": [{
                "input_id": "wsi-001",
                "kind": "tissue_wsi",
                "uri": "file:///input/sample.svs",
                "format": "svs",
                "provenance": {"source_type": "research_dataset"},
                "sample_id": "sample-001",
                "metadata": {"tissue_type": "skin"},
            }],
        }
        report = validate_user_package(package)
        self.assertFalse(report.ready_for_any_processing)
        self.assertEqual(report.status, "INCOMPLETE")
        self.assertTrue(any(f.code == "INPUT_INCOMPLETE" for f in report.findings))
        self.assertTrue(any("specimen_id" in f.message for f in report.warnings))

    def test_invalid_provenance_is_reported(self):
        package = {
            "subject": {"subject_id": "demo-001"},
            "acquisition": {"timepoint_id": "T0", "acquisition_time": "2026-08-29T12:00:00Z"},
            "inputs": [{
                "input_id": "img-001",
                "kind": "hand_video",
                "uri": "file:///input/hand.mp4",
                "format": "mp4",
                "provenance": {"source_type": "unknown"},
            }],
        }
        report = validate_user_package(package)
        self.assertEqual(report.status, "INCOMPLETE")
        self.assertTrue(any("provenance.source_type" in f.message for f in report.warnings))

    def test_unsupported_kind_invalidates_contract(self):
        package = {
            "subject": {"subject_id": "demo-001"},
            "acquisition": {"timepoint_id": "T0", "acquisition_time": "2026-08-29T12:00:00Z"},
            "inputs": [{
                "input_id": "x",
                "kind": "magic_scan",
                "uri": "file:///input/x",
                "format": "bin",
                "provenance": {"source_type": "user"},
            }],
        }
        report = validate_user_package(package)
        self.assertFalse(report.valid_contract)
        self.assertEqual(report.status, "INVALID")


if __name__ == "__main__":
    unittest.main()
