import pytest

from backend.multiscale_state_delta import compare_multiscale_state_vectors


def snapshot(timepoint, *, age=1.0, attention=0.2, confidence=0.8, status="observed", level="cell"):
    return {
        "subject_id": "s1",
        "hand_id": "h1",
        "timepoint_id": timepoint,
        "levels": [
            {
                "level": level,
                "object_count": 10,
                "changed_objects": 2,
                "mean_age_delta": age,
                "attention_score": attention,
                "confidence": confidence,
                "status": status,
                "source_cell_ids": ["c1", "c2"],
            }
        ],
    }


def test_compares_adjacent_snapshots_without_reordering():
    result = compare_multiscale_state_vectors([
        snapshot("T0", age=1.0, attention=0.2),
        snapshot("T1", age=2.5, attention=0.7),
        snapshot("T2", age=4.0, attention=0.4),
    ])

    assert [(x["from_timepoint_id"], x["to_timepoint_id"]) for x in result] == [
        ("T0", "T1"),
        ("T1", "T2"),
    ]
    assert result[0]["mean_age_delta_change"] == 1.5
    assert result[0]["attention_score_change"] == 0.5


def test_compares_all_shared_levels_and_unions_source_cells():
    first = snapshot("T0")
    second = snapshot("T1")
    second["levels"].append({
        "level": "tissue",
        "object_count": 2,
        "changed_objects": 1,
        "mean_age_delta": 1.5,
        "attention_score": 0.6,
        "confidence": 0.9,
        "status": "attention",
        "source_cell_ids": ["c1", "c3"],
    })

    result = compare_multiscale_state_vectors([first, second])

    assert [x["level"] for x in result] == ["cell"]
    assert result[0]["source_cell_ids"] == ["c1", "c2"]


def test_skips_levels_missing_from_one_endpoint_instead_of_fabricating_values():
    first = snapshot("T0")
    second = snapshot("T1")
    second["levels"] = []

    assert compare_multiscale_state_vectors([first, second]) == []


def test_rejects_mixed_subject_or_hand_history():
    second = snapshot("T1")
    second["subject_id"] = "s2"

    with pytest.raises(ValueError, match="subject and hand identity"):
        compare_multiscale_state_vectors([snapshot("T0"), second])


def test_rejects_duplicate_timepoints():
    with pytest.raises(ValueError, match="duplicate timepoints"):
        compare_multiscale_state_vectors([snapshot("T0"), snapshot("T0")])


def test_requires_two_snapshots():
    with pytest.raises(ValueError, match="at least two"):
        compare_multiscale_state_vectors([snapshot("T0")])
