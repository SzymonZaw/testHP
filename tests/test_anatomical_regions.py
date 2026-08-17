from backend.anatomical_regions import map_anatomical_regions


def test_maps_mediapipe_landmarks_to_regions():
    landmarks = [{"x": i / 21, "y": i / 21, "z": 0.0} for i in range(21)]
    regions = map_anatomical_regions(landmarks)
    assert [r["region_id"] for r in regions] == ["wrist", "thumb", "index", "middle", "ring", "little"]
    assert regions[1]["landmark_indices"] == [1, 2, 3, 4]
    assert regions[1]["mapping_method"] == "landmark-group"


def test_partial_landmarks_are_supported():
    landmarks = [{"x": 0.5, "y": 0.5, "z": 0.0}] * 6
    regions = map_anatomical_regions(landmarks)
    assert {r["region_id"] for r in regions} == {"wrist", "thumb", "index"}
