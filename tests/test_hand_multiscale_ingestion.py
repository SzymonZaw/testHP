from pathlib import Path

from PIL import Image

from backend.multiscale_pipeline import analyze_hand, build_multiscale_run


def _write_hand_set(root: Path) -> None:
    t0 = root / "T0"
    t0.mkdir(parents=True)
    for view in ("front", "back", "thumb", "side_left", "side_right"):
        Image.new("RGB", (20, 30), (120, 80, 60)).save(t0 / f"{view}.jpg")


def test_analyze_hand_reads_standardized_t0_views(tmp_path: Path):
    root = tmp_path / "own_cohort"
    _write_hand_set(root)

    records = analyze_hand(root, "own_cohort", "T0")

    assert len({r.source_id for r in records}) == 5
    assert {r.provenance["view"] for r in records} == {"front", "back", "thumb", "side_left", "side_right"}
    assert all(r.subject_id == "own_cohort" for r in records)
    assert all(r.provenance["timepoint"] == "T0" for r in records)
    assert any(r.region_id == "hand.thumb" for r in records)


def test_build_multiscale_run_puts_hand_records_into_twin(tmp_path: Path):
    raw = tmp_path / "raw"
    _write_hand_set(raw / "hand" / "own_cohort")

    payload = build_multiscale_run(raw, "own_cohort", "T0")

    assert payload["hand"]["files_found"] == 5
    assert len(payload["hand"]["records"]) == 30
    assert len(payload["digital_twin"]["history"]) == 1
    assert payload["digital_twin"]["history"][0]["timepoint"] == "T0"
    assert len(payload["digital_twin"]["history"][0]["record_ids"]) == 30
    assert len(payload["digital_twin"]["evidence"]) == 30
    assert payload["digital_twin"]["zones"]["thumb"]["id"] == "hand.thumb"


def test_hand_missing_timepoint_falls_back_to_cohort_root(tmp_path: Path):
    root = tmp_path / "own_cohort"
    root.mkdir(parents=True)
    Image.new("RGB", (10, 10), (1, 2, 3)).save(root / "front.jpg")

    records = analyze_hand(root, "own_cohort", "T2")

    assert len(records) == 6
    assert all(r.provenance["timepoint"] == "T2" for r in records)
