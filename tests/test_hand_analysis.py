from pathlib import Path

from backend.hand_analysis import ZONE_LANDMARKS, _priority, _zone_summary, run_hand_analysis


def test_hand_zone_contract_is_stable():
    assert list(ZONE_LANDMARKS) == [
        "wrist",
        "palm",
        "thumb",
        "index",
        "middle",
        "ring",
        "little",
    ]
    assert ZONE_LANDMARKS["index"] == [5, 6, 7, 8]
    assert ZONE_LANDMARKS["middle"] == [9, 10, 11, 12]


def test_priority_is_technical_quality_only():
    assert _priority(0.95) == "normal"
    assert _priority(0.80) == "review"
    assert _priority(0.40) == "high"


def test_zone_summary_is_grouped_and_sorted_by_review_priority():
    zones = [
        {"id": "palm", "confidence": 0.90},
        {"id": "palm", "confidence": 0.70},
        {"id": "index", "confidence": 0.40},
    ]
    summary = _zone_summary(zones)
    assert summary[0]["id"] == "index"
    assert summary[0]["review_priority"] == "high"
    assert summary[0]["observations"] == 1
    assert summary[1]["id"] == "palm"
    assert summary[1]["mean_confidence"] == 0.8


def test_empty_local_hand_input_is_explicitly_insufficient(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.hand_analysis.OWN_HAND_ROOT", Path(tmp_path))
    result = run_hand_analysis()

    assert result["status"] == "insufficient_data"
    assert result["stage"] == "H0"
    assert result["files"] == 0
    assert result["hand_instances"] == 0
    assert result["digital_twin"] is None
    assert result["limitations"]
    assert "No supported images" in result["limitations"][0]
    assert result["evidence_contract"]["medical_conclusions"] == []


def test_hand_analysis_never_exposes_medical_conclusions_on_missing_model(monkeypatch, tmp_path):
    image = Path(tmp_path) / "1.jpg"
    image.write_bytes(b"not-an-image")
    monkeypatch.setattr("backend.hand_analysis.OWN_HAND_ROOT", Path(tmp_path))

    result = run_hand_analysis()

    assert result["files"] == 1
    assert result["evidence_contract"]["medical_conclusions"] == []
    assert all("diagnos" not in str(item).lower() for item in result["limitations"])
