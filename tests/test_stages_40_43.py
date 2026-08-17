from pathlib import Path

from backend.availability import build_availability
from backend.longitudinal import compare_observations
from backend.provenance import attach_provenance, make_provenance
from backend.video_analysis import inspect_video


def test_longitudinal_change():
    result = compare_observations("own_cohort", [
        {"zone": "thumb.distal", "metric": "brightness", "timepoint": "T0", "value": 0.5},
        {"zone": "thumb.distal", "metric": "brightness", "timepoint": "T1", "value": 0.7},
    ])
    assert result[0]["delta"] == 0.2
    assert result[0]["status"] == "observed_change"


def test_missing_modality_is_unavailable():
    result = build_availability([{"modality": "hand", "status": "available"}])
    statuses = {x["modality"]: x["status"] for x in result["modalities"]}
    assert statuses["hand"] == "available"
    assert statuses["rna"] == "unavailable"


def test_provenance_is_attached():
    provenance = make_provenance(asset_id="asset_1", source="x.jpg", method="hand_analysis", confidence=0.8)
    observation = attach_provenance({"zone": "palm", "metric": "brightness", "value": 0.4}, provenance)
    assert observation["provenance"]["asset_id"] == "asset_1"
    assert observation["provenance"]["confidence"] == 0.8


def test_empty_video_is_unavailable(tmp_path: Path):
    video = tmp_path / "empty.mp4"
    video.write_bytes(b"")
    result = inspect_video(video)
    assert result["status"] == "unavailable"
    assert result["reason"] == "empty video file"
