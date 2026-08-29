import pytest

from research.claims import claim_status
from research.hand_vertical_benchmark import HandVerticalBenchmark
from research.validation import Evidence, EvidenceLevel, PredictionRecord, PredictionValidator, compare_against_baseline, require_evidence


def test_prediction_validator_reports_error_and_coverage():
    records = [
        PredictionRecord("a", 0.0, 1.0, 0.8, 0.1, "m1", Evidence(EvidenceLevel.LABELED_BENCHMARK)),
        PredictionRecord("b", 0.0, 1.0, 0.5, 0.2, "m1", Evidence(EvidenceLevel.LABELED_BENCHMARK)),
    ]
    report = PredictionValidator().evaluate(records, {"a": 0.7, "b": 0.9})
    assert report.count == 2
    assert report.mae == pytest.approx(0.25)
    assert 0.0 <= report.coverage <= 1.0


def test_evidence_gate_blocks_unvalidated_claim():
    with pytest.raises(PermissionError):
        require_evidence(Evidence(EvidenceLevel.LABELED_BENCHMARK), EvidenceLevel.EXTERNAL_VALIDATION, "cell_health")
    assert claim_status("cell_health", Evidence(EvidenceLevel.LABELED_BENCHMARK)) == "research_only"


def test_baseline_comparison_is_explicit():
    result = compare_against_baseline([1, 1], [2, 4])
    assert result["model_mae"] == pytest.approx(1.0)
    assert result["baseline_mae"] == pytest.approx(3.0)
    assert result["relative_improvement"] == pytest.approx(2 / 3)


def test_hand_vertical_benchmark_requires_overlap_and_reports_limitations():
    result = HandVerticalBenchmark().evaluate(
        {"a": 0.9, "b": 0.8},
        {"a": 0.7, "b": 0.7},
        {"a": 1.0, "b": 1.0},
        minimum_improvement=0.0,
    )
    assert result.passed
    assert result.n == 2
    assert "not clinical validation" in result.limitations[0].lower()
