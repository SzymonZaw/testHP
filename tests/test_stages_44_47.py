from pathlib import Path

from PIL import Image

from backend.images_layer import inspect_skin_image, validate_skin_dataset
from backend.skin_longitudinal import compare_skin_observations
from backend.skin_ontology import ontology_snapshot


def test_skin_image_observation(tmp_path: Path):
    path = tmp_path / "normal_skin" / "sample.jpg"
    path.parent.mkdir()
    Image.new("RGB", (20, 10), (120, 130, 140)).save(path)
    obs = inspect_skin_image(path, "s1", "T0")
    assert obs["status"] == "available"
    assert obs["width"] == 20
    assert obs["height"] == 10
    assert obs["evidence_level"] == "observed"


def test_skin_validation_detects_duplicates(tmp_path: Path):
    root = tmp_path / "images"
    (root / "normal_skin").mkdir(parents=True)
    (root / "aging_skin").mkdir(parents=True)
    a = root / "normal_skin" / "a.jpg"
    b = root / "aging_skin" / "b.jpg"
    Image.new("RGB", (10, 10), (1, 2, 3)).save(a)
    b.write_bytes(a.read_bytes())
    result = validate_skin_dataset(root)
    assert result["total_images"] == 2
    assert result["duplicates"]


def test_skin_ontology_is_non_diagnostic():
    ontology = ontology_snapshot()
    assert "lesion_presence" in ontology["observation_types"]
    assert ontology["interpretation_policy"]["diagnosis_allowed"] is False


def test_skin_longitudinal_change():
    changes = compare_skin_observations([
        {"zone": "dorsal_hand", "metric": "brightness", "value": 0.4, "timepoint": "T0", "status": "available"},
        {"zone": "dorsal_hand", "metric": "brightness", "value": 0.6, "timepoint": "T1", "status": "available"},
    ])
    assert changes[0]["delta"] == 0.19999999999999996
    assert changes[0]["status"] == "observed_change"
