import numpy as np
import pytest

from analysis.reprogramming import (
    YAMANAKA_FACTORS,
    marker_score,
    summarize_reprogramming,
    timepoint_effect,
    validate_expression,
)


def test_validate_expression_rejects_negative_values():
    with pytest.raises(ValueError, match="negative"):
        validate_expression(np.array([[1.0, -1.0]], dtype=np.float32))


def test_summary_reports_marker_coverage():
    expression = np.array(
        [[1, 2, 0, 4], [2, 3, 1, 5]],
        dtype=np.float32,
    )
    class FakeAnnData:
        X = expression
        var_names = ["POU5F1", "SOX2", "NANOG", "COL1A1"]

    result = summarize_reprogramming(FakeAnnData())

    assert result.n_observations == 2
    assert result.n_features == 4
    assert all(result.factor_coverage[name] for name in ("POU5F1", "SOX2"))
    assert result.factor_coverage["KLF4"] is False
    assert result.factor_coverage["MYC"] is False
    assert result.pluripotency_marker_coverage["NANOG"] is True
    assert result.fibroblast_marker_coverage["COL1A1"] is True


def test_marker_score_uses_available_markers():
    expression = np.array([[2, 4], [6, 8]], dtype=np.float32)
    class FakeAnnData:
        X = expression
        var_names = ["NANOG", "SOX2"]

    score = marker_score(FakeAnnData(), ["NANOG", "DPPA4"])

    np.testing.assert_allclose(score, [2.0, 6.0])


def test_timepoint_effect_returns_feature_names_and_effects():
    expression = np.array(
        [[1, 2], [1, 2], [3, 2], [3, 2]],
        dtype=np.float32,
    )
    result = timepoint_effect(expression, [0, 1], [2, 3])

    assert list(result["feature_names"]) == ["0", "1"]
    np.testing.assert_allclose(result["mean_difference"], [-2.0, 0.0])
    assert result["standardized_effect"][0] < 0
