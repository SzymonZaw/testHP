import numpy as np

from backend.hand_surface import SUPPORTED_VIEWS
from backend.photo_reconstruction import _foreground_mask, infer_view, normalize_view


def test_view_vocabulary_is_canonical():
    assert SUPPORTED_VIEWS == ("front", "back", "side_left", "side_right", "thumb")


def test_view_assignment_accepts_metadata_aliases():
    assert normalize_view("left") == "side_left"
    assert normalize_view("right") == "side_right"
    assert normalize_view("kciuk") == "thumb"
    assert normalize_view("side-right") == "side_right"


def test_view_assignment_falls_back_to_filename():
    assert infer_view("patient_front_01.jpg") == "front"
    assert infer_view("hand-side_left.png") == "side_left"
    assert infer_view("hand_side-right.webp") == "side_right"
    assert infer_view("kciuk.jpg") == "thumb"
    assert infer_view("hand_unknown.jpg") is None


def test_foreground_mask_does_not_treat_opaque_jpeg_as_alpha_mask():
    image = np.full((40, 40, 3), 240, dtype=np.uint8)
    image[10:30, 15:25] = 80
    mask = _foreground_mask(image, None)
    assert mask[20, 20]
    assert not mask[0, 0]
