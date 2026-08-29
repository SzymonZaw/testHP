from core.data_contract import build_ingest_bundle, validate_submission


def valid_submission():
    return {
        "subject_id": "subject-001",
        "metadata": {"chronological_age_years": 42},
        "timepoints": [
            {
                "timepoint_id": "T0",
                "acquisition_time": "2026-08-29T10:00:00+02:00",
                "hand_observations": [
                    {
                        "hand_side": "right",
                        "view": "dorsal",
                        "file": {"path": "T0/hand/right/dorsal.jpg", "modality": "hand_image"},
                    }
                ],
            }
        ],
    }


def test_valid_minimum_submission():
    assert validate_submission(valid_submission()) == []


def test_missing_hand_is_rejected():
    submission = valid_submission()
    submission["timepoints"][0]["hand_observations"] = []
    errors = validate_submission(submission)
    assert any("hand_observations" in error for error in errors)


def test_ingest_bundle_maps_artifact_to_domain_objects():
    bundle = build_ingest_bundle(valid_submission())
    assert len(bundle.measurements) == 1
    assert len(bundle.observations) == 1
    assert len(bundle.evidence) == 1
    assert bundle.observations[0].biological_level == "macro"
    assert bundle.evidence[0].artifact_ids == ["artifact:T0/hand/right/dorsal.jpg"]
    assert set(bundle.missing_levels) == {"tissue", "cellular", "molecular"}
