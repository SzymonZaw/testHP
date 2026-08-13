"""
SAM 2 model wrapper.

This module provides a reusable interface for:
- loading a local SAM 2 checkpoint,
- image segmentation,
- point-prompt segmentation,
- box-prompt segmentation,
- mask generation,
- exporting masks.

Expected project structure:

Doktorat_Kod/
├── models/
│   ├── checkpoints/
│   │   └── sam2/
│   │       └── <checkpoint>.pt
│   │
│   └── sam2_model.py
│
└── data/
    └── ...

The actual SAM 2 implementation is provided by the official
facebookresearch/sam2 package.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, Tuple, Union

import numpy as np

try:
    import torch
except ImportError as exc:
    raise ImportError(
        "PyTorch is required for SAM 2. "
        "Install it before using sam2_model.py."
    ) from exc

try:
    from PIL import Image
except ImportError as exc:
    raise ImportError(
        "Pillow is required for image loading."
    ) from exc


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

PathLike = Union[str, Path]
ImageInput = Union[
    str,
    Path,
    Image.Image,
    np.ndarray,
]

Point = Tuple[float, float]
Box = Tuple[float, float, float, float]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class SAM2Config:
    """
    Configuration for the SAM 2 wrapper.

    Parameters
    ----------
    checkpoint:
        Path to the SAM 2 checkpoint.

    model_cfg:
        SAM 2 model configuration name/path expected by the installed
        SAM 2 package.

    device:
        Torch device. If None, automatically selects CUDA, MPS, or CPU.

    confidence_threshold:
        Minimum confidence used when filtering predicted masks.

    multimask_output:
        Whether SAM 2 should return multiple masks for ambiguous prompts.

    """

    checkpoint: PathLike
    model_cfg: str

    device: Optional[str] = None

    confidence_threshold: float = 0.0

    multimask_output: bool = True


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def get_default_device() -> str:
    """
    Select the best available PyTorch device.

    Priority:
        CUDA -> MPS -> CPU
    """

    if torch.cuda.is_available():
        return "cuda"

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"

    return "cpu"


def _ensure_numpy_image(image: ImageInput) -> np.ndarray:
    """
    Convert supported image inputs to an RGB NumPy array.

    Returns
    -------
    np.ndarray
        Image with shape (H, W, 3), dtype uint8.
    """

    if isinstance(image, (str, Path)):
        image = Image.open(image)

    if isinstance(image, Image.Image):
        image = image.convert("RGB")
        return np.asarray(image)

    if isinstance(image, np.ndarray):
        array = image

        if array.ndim == 2:
            array = np.stack([array] * 3, axis=-1)

        if array.ndim != 3:
            raise ValueError(
                "NumPy image must have shape (H, W) or (H, W, C)."
            )

        if array.shape[-1] == 4:
            array = array[..., :3]

        if array.shape[-1] != 3:
            raise ValueError(
                "NumPy image must have 1, 3, or 4 channels."
            )

        if array.dtype != np.uint8:
            if np.issubdtype(array.dtype, np.floating):
                array = np.clip(array, 0.0, 1.0) * 255.0

            array = np.clip(array, 0, 255).astype(np.uint8)

        return array

    raise TypeError(
        "Unsupported image type. Use a file path, PIL.Image, "
        "or NumPy array."
    )


def _validate_points(
    points: Sequence[Point],
) -> np.ndarray:
    """
    Validate and convert point coordinates to NumPy format.
    """

    if len(points) == 0:
        raise ValueError("At least one point is required.")

    array = np.asarray(points, dtype=np.float32)

    if array.ndim != 2 or array.shape[1] != 2:
        raise ValueError(
            "Points must have shape (N, 2)."
        )

    return array


def _validate_labels(
    labels: Sequence[int],
    number_of_points: int,
) -> np.ndarray:
    """
    Validate point prompt labels.

    SAM convention:
        1 = foreground
        0 = background
    """

    if len(labels) != number_of_points:
        raise ValueError(
            "Number of labels must match number of points."
        )

    array = np.asarray(labels, dtype=np.int32)

    if not np.all(np.isin(array, [0, 1])):
        raise ValueError(
            "Point labels must contain only 0 or 1."
        )

    return array


def _validate_box(
    box: Box,
) -> np.ndarray:
    """
    Validate and convert a box prompt.

    Format:
        (x_min, y_min, x_max, y_max)
    """

    array = np.asarray(box, dtype=np.float32)

    if array.shape != (4,):
        raise ValueError(
            "Box must contain four values: "
            "(x_min, y_min, x_max, y_max)."
        )

    x_min, y_min, x_max, y_max = array

    if x_max <= x_min:
        raise ValueError(
            "x_max must be greater than x_min."
        )

    if y_max <= y_min:
        raise ValueError(
            "y_max must be greater than y_min."
        )

    return array


# ---------------------------------------------------------------------------
# SAM 2 wrapper
# ---------------------------------------------------------------------------

class SAM2Model:
    """
    High-level wrapper around SAM 2.

    The wrapper intentionally keeps SAM 2-specific implementation details
    isolated from the rest of the project.

    This means that the rest of the codebase can simply use:

        model.segment(...)
        model.segment_with_points(...)
        model.segment_with_box(...)

    without depending directly on SAM 2 internals.
    """

    def __init__(
        self,
        config: SAM2Config,
    ) -> None:

        self.config = config

        self.checkpoint = Path(config.checkpoint)

        if not self.checkpoint.exists():
            raise FileNotFoundError(
                f"SAM 2 checkpoint does not exist: "
                f"{self.checkpoint}"
            )

        self.device = (
            config.device
            if config.device is not None
            else get_default_device()
        )

        self.predictor = None
        self.model = None

        self._load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """
        Load the official SAM 2 implementation.

        The exact builder API can differ between SAM 2 package versions,
        therefore the import is isolated here.
        """

        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor
        except ImportError as exc:
            raise ImportError(
                "SAM 2 package is not installed or is not available "
                "in the current Python environment.\n\n"
                "Install the official SAM 2 repository/package first."
            ) from exc

        try:
            self.model = build_sam2(
                self.config.model_cfg,
                str(self.checkpoint),
                device=self.device,
            )
        except TypeError:
            # Compatibility with installations whose builder does not
            # expose device as a keyword argument.
            self.model = build_sam2(
                self.config.model_cfg,
                str(self.checkpoint),
            )

            self.model.to(self.device)

        self.predictor = SAM2ImagePredictor(self.model)

    # ------------------------------------------------------------------
    # Device
    # ------------------------------------------------------------------

    def to(self, device: str) -> "SAM2Model":
        """
        Move the underlying model to another device.
        """

        self.device = device

        if self.model is not None:
            self.model.to(device)

        return self

    # ------------------------------------------------------------------
    # Image preparation
    # ------------------------------------------------------------------

    def set_image(
        self,
        image: ImageInput,
    ) -> np.ndarray:
        """
        Set the current image for SAM 2 prediction.

        Returns
        -------
        np.ndarray
            RGB uint8 image used by the predictor.
        """

        array = _ensure_numpy_image(image)

        if self.predictor is None:
            raise RuntimeError(
                "SAM 2 predictor is not initialized."
            )

        with torch.inference_mode():
            self.predictor.set_image(array)

        return array

    # ------------------------------------------------------------------
    # Point-based segmentation
    # ------------------------------------------------------------------

    def segment_with_points(
        self,
        image: ImageInput,
        points: Sequence[Point],
        labels: Sequence[int],
        multimask_output: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        Segment an object using point prompts.

        Parameters
        ----------
        image:
            Input image.

        points:
            Sequence of (x, y) coordinates.

        labels:
            1 for foreground points.
            0 for background points.

        multimask_output:
            Whether to return multiple candidate masks.

        Returns
        -------
        dict
            Contains:
                masks
                scores
                logits
        """

        image_array = self.set_image(image)

        points_array = _validate_points(points)

        labels_array = _validate_labels(
            labels,
            number_of_points=len(points_array),
        )

        if multimask_output is None:
            multimask_output = self.config.multimask_output

        with torch.inference_mode():
            masks, scores, logits = self.predictor.predict(
                point_coords=points_array,
                point_labels=labels_array,
                multimask_output=multimask_output,
            )

        return {
            "masks": np.asarray(masks),
            "scores": np.asarray(scores),
            "logits": np.asarray(logits),
            "image_shape": image_array.shape[:2],
        }

    # ------------------------------------------------------------------
    # Box-based segmentation
    # ------------------------------------------------------------------

    def segment_with_box(
        self,
        image: ImageInput,
        box: Box,
        multimask_output: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        Segment an object using a bounding-box prompt.
        """

        image_array = self.set_image(image)

        box_array = _validate_box(box)

        if multimask_output is None:
            multimask_output = self.config.multimask_output

        with torch.inference_mode():
            masks, scores, logits = self.predictor.predict(
                box=box_array,
                multimask_output=multimask_output,
            )

        return {
            "masks": np.asarray(masks),
            "scores": np.asarray(scores),
            "logits": np.asarray(logits),
            "image_shape": image_array.shape[:2],
        }

    # ------------------------------------------------------------------
    # Combined point + box segmentation
    # ------------------------------------------------------------------

    def segment_with_box_and_points(
        self,
        image: ImageInput,
        box: Optional[Box] = None,
        points: Optional[Sequence[Point]] = None,
        labels: Optional[Sequence[int]] = None,
        multimask_output: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        Segment using a combination of box and point prompts.

        At least one prompt type must be supplied.
        """

        image_array = self.set_image(image)

        if box is None and points is None:
            raise ValueError(
                "At least one prompt must be supplied: "
                "box or points."
            )

        box_array = None

        if box is not None:
            box_array = _validate_box(box)

        points_array = None
        labels_array = None

        if points is not None:
            points_array = _validate_points(points)

            if labels is None:
                raise ValueError(
                    "Labels are required when points are supplied."
                )

            labels_array = _validate_labels(
                labels,
                number_of_points=len(points_array),
            )

        if multimask_output is None:
            multimask_output = self.config.multimask_output

        with torch.inference_mode():
            masks, scores, logits = self.predictor.predict(
                point_coords=points_array,
                point_labels=labels_array,
                box=box_array,
                multimask_output=multimask_output,
            )

        return {
            "masks": np.asarray(masks),
            "scores": np.asarray(scores),
            "logits": np.asarray(logits),
            "image_shape": image_array.shape[:2],
        }

    # ------------------------------------------------------------------
    # Best mask selection
    # ------------------------------------------------------------------

    def select_best_mask(
        self,
        result: dict[str, Any],
        threshold: Optional[float] = None,
    ) -> np.ndarray:
        """
        Select the highest-scoring mask.

        Returns
        -------
        np.ndarray
            Boolean mask with shape (H, W).
        """

        masks = np.asarray(result["masks"])
        scores = np.asarray(result["scores"])

        if masks.ndim == 2:
            return masks.astype(bool)

        if masks.ndim != 3:
            raise ValueError(
                "Expected masks with shape (N, H, W)."
            )

        if scores.ndim == 0:
            index = 0
        else:
            index = int(np.argmax(scores))

        selected = masks[index]

        if threshold is None:
            threshold = self.config.confidence_threshold

        if threshold > 0:
            if scores[index] < threshold:
                raise ValueError(
                    f"Best SAM 2 mask score "
                    f"({scores[index]:.4f}) is below "
                    f"the configured threshold ({threshold:.4f})."
                )

        return selected.astype(bool)

    # ------------------------------------------------------------------
    # Mask utilities
    # ------------------------------------------------------------------

    @staticmethod
    def mask_area(mask: np.ndarray) -> int:
        """
        Calculate mask area in pixels.
        """

        mask = np.asarray(mask).astype(bool)

        return int(mask.sum())

    @staticmethod
    def mask_bbox(
        mask: np.ndarray,
    ) -> Optional[Box]:
        """
        Calculate bounding box from a binary mask.

        Returns None if the mask is empty.
        """

        mask = np.asarray(mask).astype(bool)

        ys, xs = np.where(mask)

        if len(xs) == 0:
            return None

        x_min = float(xs.min())
        y_min = float(ys.min())

        x_max = float(xs.max())
        y_max = float(ys.max())

        return (
            x_min,
            y_min,
            x_max,
            y_max,
        )

    @staticmethod
    def mask_centroid(
        mask: np.ndarray,
    ) -> Optional[Point]:
        """
        Calculate the centroid of a binary mask.
        """

        mask = np.asarray(mask).astype(bool)

        ys, xs = np.where(mask)

        if len(xs) == 0:
            return None

        return (
            float(xs.mean()),
            float(ys.mean()),
        )

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------

    @staticmethod
    def save_mask(
        mask: np.ndarray,
        output_path: PathLike,
    ) -> Path:
        """
        Save a binary segmentation mask as PNG.
        """

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        mask = np.asarray(mask).astype(bool)

        image = Image.fromarray(
            (mask.astype(np.uint8) * 255),
            mode="L",
        )

        image.save(output_path)

        return output_path

    @staticmethod
    def save_overlay(
        image: ImageInput,
        mask: np.ndarray,
        output_path: PathLike,
        alpha: float = 0.5,
    ) -> Path:
        """
        Save a simple segmentation overlay.

        The overlay uses a transparent red mask.
        """

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        image_array = _ensure_numpy_image(image)

        mask = np.asarray(mask).astype(bool)

        if image_array.shape[:2] != mask.shape:
            raise ValueError(
                "Image and mask dimensions do not match."
            )

        alpha = float(np.clip(alpha, 0.0, 1.0))

        overlay = image_array.astype(np.float32).copy()

        # Red overlay.
        overlay[mask, 0] = (
            (1.0 - alpha) * overlay[mask, 0]
            + alpha * 255.0
        )

        overlay[mask, 1] = (
            (1.0 - alpha) * overlay[mask, 1]
        )

        overlay[mask, 2] = (
            (1.0 - alpha) * overlay[mask, 2]
        )

        overlay = np.clip(
            overlay,
            0,
            255,
        ).astype(np.uint8)

        Image.fromarray(overlay).save(output_path)

        return output_path

    # ------------------------------------------------------------------
    # Information
    # ------------------------------------------------------------------

    def info(self) -> dict[str, Any]:
        """
        Return information about the loaded model.
        """

        return {
            "checkpoint": str(self.checkpoint),
            "model_cfg": self.config.model_cfg,
            "device": self.device,
            "confidence_threshold": (
                self.config.confidence_threshold
            ),
            "multimask_output": (
                self.config.multimask_output
            ),
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_sam2_model(
    checkpoint: PathLike,
    model_cfg: str,
    device: Optional[str] = None,
    confidence_threshold: float = 0.0,
    multimask_output: bool = True,
) -> SAM2Model:
    """
    Convenience factory for creating a SAM 2 model.

    Example
    -------
    model = create_sam2_model(
        checkpoint="models/checkpoints/sam2/model.pt",
        model_cfg="configs/sam2.1/sam2.1_hiera_l.yaml",
    )
    """

    config = SAM2Config(
        checkpoint=checkpoint,
        model_cfg=model_cfg,
        device=device,
        confidence_threshold=confidence_threshold,
        multimask_output=multimask_output,
    )

    return SAM2Model(config)


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("SAM 2 model wrapper")
    print("-------------------")
    print(
        "This module is intended to be imported by the project "
        "pipeline rather than executed directly."
    )