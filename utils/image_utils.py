# utils/image_utils.py

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image


def load_image(
    path: str | Path,
    mode: str = "RGB",
) -> np.ndarray:
    """
    Load image as NumPy array.

    Returns
    -------
    np.ndarray
        Image with shape H x W x C.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    image = Image.open(path)

    if mode is not None:
        image = image.convert(mode)

    return np.asarray(image)


def save_image(
    image: np.ndarray,
    path: str | Path,
) -> Path:
    """
    Save NumPy image array.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if image.dtype != np.uint8:
        image = normalize_to_uint8(image)

    Image.fromarray(image).save(path)

    return path


def normalize_to_uint8(
    image: np.ndarray,
) -> np.ndarray:
    """
    Normalize arbitrary numeric image to uint8.
    """

    image = np.asarray(image)

    image = np.nan_to_num(
        image,
        nan=0.0,
        posinf=255.0,
        neginf=0.0,
    )

    image_min = image.min()
    image_max = image.max()

    if image_max == image_min:
        return np.zeros_like(
            image,
            dtype=np.uint8,
        )

    normalized = (
        (image - image_min)
        / (image_max - image_min)
        * 255.0
    )

    return normalized.astype(np.uint8)


def normalize_image(
    image: np.ndarray,
) -> np.ndarray:
    """
    Normalize image to floating-point [0, 1].
    """

    image = image.astype(np.float32)

    image_min = image.min()
    image_max = image.max()

    if image_max == image_min:
        return np.zeros_like(image)

    return (
        (image - image_min)
        / (image_max - image_min)
    )


def resize_image(
    image: np.ndarray,
    size: Tuple[int, int],
) -> np.ndarray:
    """
    Resize image.

    Parameters
    ----------
    size:
        (width, height)
    """

    pil_image = Image.fromarray(
        normalize_to_uint8(image)
    )

    resized = pil_image.resize(
        size,
        Image.Resampling.BILINEAR,
    )

    return np.asarray(resized)


def center_crop(
    image: np.ndarray,
    crop_size: Tuple[int, int],
) -> np.ndarray:
    """
    Center crop an image.

    Parameters
    ----------
    crop_size:
        (height, width)
    """

    height, width = image.shape[:2]
    crop_h, crop_w = crop_size

    if crop_h > height or crop_w > width:
        raise ValueError(
            "Crop size cannot be larger than image size."
        )

    y1 = (height - crop_h) // 2
    x1 = (width - crop_w) // 2

    return image[
        y1:y1 + crop_h,
        x1:x1 + crop_w,
    ]


def pad_image(
    image: np.ndarray,
    target_size: Tuple[int, int],
    value: int = 0,
) -> np.ndarray:
    """
    Pad image to target size.

    Parameters
    ----------
    target_size:
        (height, width)
    """

    target_h, target_w = target_size
    h, w = image.shape[:2]

    if target_h < h or target_w < w:
        raise ValueError(
            "Target size must be >= image size."
        )

    pad_h = target_h - h
    pad_w = target_w - w

    top = pad_h // 2
    bottom = pad_h - top

    left = pad_w // 2
    right = pad_w - left

    if image.ndim == 2:
        padding = (
            (top, bottom),
            (left, right),
        )
    else:
        padding = (
            (top, bottom),
            (left, right),
            (0, 0),
        )

    return np.pad(
        image,
        padding,
        mode="constant",
        constant_values=value,
    )


def image_shape(
    image: np.ndarray,
) -> dict:
    """
    Return basic image metadata.
    """

    if image.ndim == 2:
        h, w = image.shape
        channels = 1

    elif image.ndim == 3:
        h, w, channels = image.shape

    else:
        raise ValueError(
            f"Unsupported image dimensions: {image.shape}"
        )

    return {
        "height": int(h),
        "width": int(w),
        "channels": int(channels),
        "dtype": str(image.dtype),
    }


def rgb_to_grayscale(
    image: np.ndarray,
) -> np.ndarray:
    """
    Convert RGB image to grayscale.
    """

    if image.ndim != 3 or image.shape[-1] != 3:
        raise ValueError(
            "Expected RGB image with shape H x W x 3."
        )

    image = image.astype(np.float32)

    gray = (
        0.299 * image[..., 0]
        + 0.587 * image[..., 1]
        + 0.114 * image[..., 2]
    )

    return gray.astype(np.float32)


def get_image_channels(
    image: np.ndarray,
) -> int:
    """
    Return number of image channels.
    """

    if image.ndim == 2:
        return 1

    if image.ndim == 3:
        return image.shape[-1]

    raise ValueError(
        f"Unsupported image shape: {image.shape}"
    )