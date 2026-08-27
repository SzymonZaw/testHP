from backend.multiscale_state_vector import build_multiscale_state_vector


def test_state_vector_orders_levels_and_preserves_cell_lineage():
    result = build_multiscale_state_vector(
        subject_id="s1",
        hand_id="h1",
        timepoint_id="T1",
        trends=[
            {"zone_id": "skin", "level": "anatomy", "metric": "biological_age_years", "cell_count": 2, "changed_cells": 1, "mean_delta": 1.0, "status": "attention", "source_cell_ids": ("c1", "c2")},
            {"zone_id": "t1", "level": "tissue", "metric": "biological_age_years", "cell_count": 2, "changed_cells": 1, "mean_delta": 1.0, "status": "attention", "source_cell_ids": ("c1", "c2")},
            {"zone_id": "h1", "level": "hand", "metric": "biological_age_years", "cell_count": 2, "changed_cells": 1, "mean_delta": 1.0, "status": "attention", "source_cell_ids": ("c1", "c2")},
            {"zone_id": "c1", "level": "cell", "metric": "biological_age_years", "cell_count": 1, "changed_cells": 1, "mean_delta": 1.0, "status": "observed_change", "source_cell_ids": ("c1",)},
        ],
        attention=[
            {"zone_id": "skin", "level": "anatomy", "score": 0.8},
            {"zone_id": "t1", "level": "tissue", "score": 0.5},
            {"zone_id": "h1", "level": "hand", "score": 0.4},
            {"zone_id": "c1", "level": "cell", "score": 0.7},
        ],
    )

    assert result["overall_status"] == "attention"
    assert [item["level"] for item in result["levels"]] == ["cell", "tissue", "anatomy", "hand"]
    assert result["levels"][-1]["source_cell_ids"] == ["c1", "c2"]
    assert result["levels"][-1]["attention_score"] == 0.4


def test_state_vector_does_not_invent_missing_observations():
    result = build_multiscale_state_vector(
        subject_id="s1",
        hand_id="h1",
        timepoint_id="T1",
        trends=[],
    )

    assert result["overall_status"] == "insufficient_observation"
    assert result["levels"] == []


def test_state_vector_keeps_observed_without_attention_as_observed():
    result = build_multiscale_state_vector(
        subject_id="s1",
        hand_id="h1",
        timepoint_id="T1",
        trends=[
            {"zone_id": "h1", "level": "hand", "metric": "biological_age_years", "cell_count": 3, "changed_cells": 0, "mean_delta": 0.0, "status": "stable_observation", "source_cell_ids": ("c1", "c2", "c3")},
        ],
    )

    assert result["overall_status"] == "observed"
    assert result["levels"][0]["status"] == "observed"
    assert result["levels"][0]["attention_score"] is None
