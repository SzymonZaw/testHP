import numpy as np

from pipeline.benchmark_adapters import (
    labels_from_type_map,
    load_instance_masks,
    load_pannuke_npz,
    validate_sample,
)


def test_instance_masks_and_majority_labels(tmp_path):
    inst = np.array([[0, 1, 1], [2, 2, 0]], dtype=np.uint16)
    typ = np.array([[0, 1, 1], [2, 2, 0]], dtype=np.uint8)
    path = tmp_path / "sample.npz"
    np.savez(path, img=np.zeros((2, 3, 3), dtype=np.uint8), inst_map=inst, type_map=typ)

    sample = load_pannuke_npz(path)
    assert len(load_instance_masks(sample.instances)) == 2
    assert labels_from_type_map(inst, typ) == {1: 1, 2: 2}
    qc = validate_sample(sample)
    assert qc["instance_count"] == 2
    assert qc["has_labels"] is True


def test_invalid_instance_shape(tmp_path):
    path = tmp_path / "bad.npz"
    np.savez(path, img=np.zeros((2, 2, 3), dtype=np.uint8), inst_map=np.zeros((2, 2, 1)))
    sample = load_pannuke_npz(path)
    try:
        load_instance_masks(sample.instances)
    except ValueError as exc:
        assert "2D" in str(exc)
    else:
        raise AssertionError("expected 2D validation error")
