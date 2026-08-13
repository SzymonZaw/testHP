# models/cellpose_model.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

try:
    from cellpose import models
except ImportError as exc:
    raise ImportError(
        "Cellpose is not installed. "
        "Install it with: pip install cellpose"
    ) from exc


PathLike = Union[str, Path]


@dataclass
class CellposeConfig:
    """
    Configuration for the Cellpose segmentation model.
    """

    model_type: str = "cyto3"

    # Cellpose inference parameters
    diameter: Optional[float] = None
    channels: Tuple[int, int] = (0, 0)

    # Segmentation thresholds
    flow_threshold: float = 0.4
    cellprob_threshold: float = 0.0

    # Hardware
    gpu: bool = True

    # Output options
    normalize: bool = True
    resample: bool = True
    augment: bool = False


class CellposeModel:
    """
    Wrapper around Cellpose for cell/nuclei segmentation.

    Main responsibilities:
        - load Cellpose model
        - segment single images
        - segment batches
        - save masks
        - create segmentation overlays
        - expose Cellpose outputs in a consistent format

    Typical usage:

        config = CellposeConfig(
            model_type="cyto3",
            gpu=True
        )

        model = CellposeModel(config)

        result = model.segment("image.png")

        model.save_mask(
            result["masks"],
            "mask.png"
        )
    """

    def __init__(
        self,
        config: Optional[CellposeConfig] = None,
    ) -> None:
        self.config = config or CellposeConfig()

        self.model = self._load_model()

    # ------------------------------------------------------------------
    # MODEL INITIALIZATION
    # ------------------------------------------------------------------

    def _load_model(self):
        """
        Load the requested Cellpose model.
        """

        return models.CellposeModel(
            gpu=self.config.gpu,
            model_type=self.config.model_type,
        )

    # ------------------------------------------------------------------
    # IMAGE LOADING
    # ------------------------------------------------------------------

    @staticmethod
    def load_image(
        image_path: PathLike,
    ) -> np.ndarray:
        """
        Load image from disk and return numpy array.

        Supports:
            PNG
            JPG/JPEG
            TIFF/TIF

        Returns:
            np.ndarray
        """

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        image = Image.open(image_path)

        return np.asarray(image)

    # ------------------------------------------------------------------
    # IMAGE VALIDATION
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_image(
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Validate and normalize image representation.
        """

        if not isinstance(image, np.ndarray):
            raise TypeError(
                "Image must be a numpy.ndarray."
            )

        if image.ndim not in (2, 3):
            raise ValueError(
                "Image must be 2D grayscale or 3D RGB/RGBA."
            )

        if image.dtype != np.uint8:
            image = CellposeModel._convert_to_uint8(image)

        return image

    @staticmethod
    def _convert_to_uint8(
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert arbitrary numeric image to uint8.
        """

        image = image.astype(np.float32)

        min_value = np.nanmin(image)
        max_value = np.nanmax(image)

        if max_value <= min_value:
            return np.zeros_like(
                image,
                dtype=np.uint8,
            )

        image = (
            (image - min_value)
            / (max_value - min_value)
            * 255.0
        )

        return np.clip(
            image,
            0,
            255,
        ).astype(np.uint8)

    # ------------------------------------------------------------------
    # SINGLE IMAGE SEGMENTATION
    # ------------------------------------------------------------------

    def segment(
        self,
        image: Union[PathLike, np.ndarray],
        diameter: Optional[float] = None,
        channels: Optional[Tuple[int, int]] = None,
        flow_threshold: Optional[float] = None,
        cellprob_threshold: Optional[float] = None,
    ) -> dict:
        """
        Segment cells in a single image.

        Parameters
        ----------
        image:
            Path to image or numpy array.

        diameter:
            Expected cell diameter in pixels.
            None allows Cellpose to estimate it.

        channels:
            Cellpose channel specification.

        flow_threshold:
            Flow error threshold.

        cellprob_threshold:
            Cell probability threshold.

        Returns
        -------
        dict
            {
                "masks": np.ndarray,
                "flows": ...,
                "styles": ...,
                "diameter": ...
            }
        """

        if isinstance(image, (str, Path)):
            image = self.load_image(image)

        image = self._validate_image(image)

        diameter = (
            diameter
            if diameter is not None
            else self.config.diameter
        )

        channels = (
            channels
            if channels is not None
            else self.config.channels
        )

        flow_threshold = (
            flow_threshold
            if flow_threshold is not None
            else self.config.flow_threshold
        )

        cellprob_threshold = (
            cellprob_threshold
            if cellprob_threshold is not None
            else self.config.cellprob_threshold
        )

        result = self.model.eval(
            image,
            diameter=diameter,
            channels=channels,
            flow_threshold=flow_threshold,
            cellprob_threshold=cellprob_threshold,
            normalize=self.config.normalize,
            resample=self.config.resample,
            augment=self.config.augment,
        )

        masks, flows, styles, diams = result

        return {
            "masks": masks,
            "flows": flows,
            "styles": styles,
            "diameter": diams,
        }

    # ------------------------------------------------------------------
    # BATCH SEGMENTATION
    # ------------------------------------------------------------------

    def segment_batch(
        self,
        images: Iterable[Union[PathLike, np.ndarray]],
        diameter: Optional[float] = None,
        channels: Optional[Tuple[int, int]] = None,
    ) -> List[dict]:
        """
        Segment multiple images.
        """

        results = []

        for image in images:
            result = self.segment(
                image=image,
                diameter=diameter,
                channels=channels,
            )

            results.append(result)

        return results

    # ------------------------------------------------------------------
    # DIRECTORY SEGMENTATION
    # ------------------------------------------------------------------

    def segment_directory(
        self,
        input_dir: PathLike,
        output_dir: PathLike,
        extensions: Optional[Tuple[str, ...]] = None,
    ) -> List[Path]:
        """
        Segment every image in a directory.

        Example:

            raw/images/lesions/

        becomes:

            processed/cells/
        """

        input_dir = Path(input_dir)
        output_dir = Path(output_dir)

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if extensions is None:
            extensions = (
                ".png",
                ".jpg",
                ".jpeg",
                ".tif",
                ".tiff",
            )

        image_paths = [
            path
            for path in input_dir.rglob("*")
            if path.suffix.lower() in extensions
        ]

        saved_paths = []

        for image_path in image_paths:

            result = self.segment(image_path)

            output_name = (
                image_path.stem
                + "_mask.png"
            )

            output_path = (
                output_dir
                / output_name
            )

            self.save_mask(
                result["masks"],
                output_path,
            )

            saved_paths.append(output_path)

        return saved_paths

    # ------------------------------------------------------------------
    # MASK PROCESSING
    # ------------------------------------------------------------------

    @staticmethod
    def get_binary_mask(
        masks: np.ndarray,
    ) -> np.ndarray:
        """
        Convert instance segmentation mask
        to a binary mask.

        Cellpose masks contain:

            0 = background
            1..N = individual cells
        """

        return (
            masks > 0
        ).astype(np.uint8)

    @staticmethod
    def get_instance_count(
        masks: np.ndarray,
    ) -> int:
        """
        Return number of detected cells.
        """

        if masks.size == 0:
            return 0

        return int(
            masks.max()
        )

    # ------------------------------------------------------------------
    # CELL STATISTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_cell_statistics(
        masks: np.ndarray,
    ) -> List[dict]:
        """
        Calculate basic statistics for every segmented cell.

        Returns:
            [
                {
                    "cell_id": 1,
                    "area": ...,
                    "centroid_x": ...,
                    "centroid_y": ...
                },
                ...
            ]
        """

        statistics = []

        cell_ids = np.unique(masks)

        cell_ids = cell_ids[
            cell_ids != 0
        ]

        for cell_id in cell_ids:

            ys, xs = np.where(
                masks == cell_id
            )

            if len(xs) == 0:
                continue

            statistics.append(
                {
                    "cell_id": int(cell_id),
                    "area": int(len(xs)),
                    "centroid_x": float(xs.mean()),
                    "centroid_y": float(ys.mean()),
                    "bbox_x_min": int(xs.min()),
                    "bbox_y_min": int(ys.min()),
                    "bbox_x_max": int(xs.max()),
                    "bbox_y_max": int(ys.max()),
                }
            )

        return statistics

    # ------------------------------------------------------------------
    # SAVE MASK
    # ------------------------------------------------------------------

    @staticmethod
    def save_mask(
        masks: np.ndarray,
        output_path: PathLike,
    ) -> None:
        """
        Save instance segmentation mask as TIFF/PNG.

        PNG is suitable for smaller masks.
        TIFF is preferable for large microscopy images.
        """

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if output_path.suffix.lower() in (
            ".tif",
            ".tiff",
        ):
            image = Image.fromarray(
                masks.astype(np.uint16)
            )
        else:
            image = Image.fromarray(
                np.clip(
                    masks,
                    0,
                    255,
                ).astype(np.uint8)
            )

        image.save(
            output_path
        )

    # ------------------------------------------------------------------
    # SAVE BINARY MASK
    # ------------------------------------------------------------------

    @staticmethod
    def save_binary_mask(
        masks: np.ndarray,
        output_path: PathLike,
    ) -> None:
        """
        Save binary cell mask.
        """

        binary = (
            masks > 0
        ).astype(np.uint8) * 255

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        Image.fromarray(
            binary
        ).save(
            output_path
        )

    # ------------------------------------------------------------------
    # OVERLAY
    # ------------------------------------------------------------------

    @staticmethod
    def create_overlay(
        image: np.ndarray,
        masks: np.ndarray,
        alpha: float = 0.5,
    ) -> np.ndarray:
        """
        Create an RGB segmentation overlay.

        Each cell receives a deterministic pseudo-color.
        """

        image = CellposeModel._validate_image(
            image
        )

        if image.ndim == 2:
            image_rgb = np.stack(
                [image] * 3,
                axis=-1,
            )
        elif image.shape[-1] == 4:
            image_rgb = image[..., :3]
        else:
            image_rgb = image.copy()

        image_rgb = image_rgb.astype(
            np.float32
        )

        overlay = image_rgb.copy()

        cell_ids = np.unique(masks)

        cell_ids = cell_ids[
            cell_ids != 0
        ]

        for cell_id in cell_ids:

            # Deterministic color
            rng = np.random.default_rng(
                int(cell_id)
            )

            color = rng.integers(
                50,
                255,
                size=3,
            )

            mask = (
                masks == cell_id
            )

            overlay[mask] = (
                (1.0 - alpha)
                * overlay[mask]
                + alpha * color
            )

        return np.clip(
            overlay,
            0,
            255,
        ).astype(np.uint8)

    # ------------------------------------------------------------------
    # SAVE OVERLAY
    # ------------------------------------------------------------------

    def save_overlay(
        self,
        image: Union[PathLike, np.ndarray],
        masks: np.ndarray,
        output_path: PathLike,
        alpha: float = 0.5,
    ) -> None:
        """
        Create and save segmentation overlay.
        """

        if isinstance(image, (str, Path)):
            image = self.load_image(image)

        overlay = self.create_overlay(
            image,
            masks,
            alpha=alpha,
        )

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        Image.fromarray(
            overlay
        ).save(
            output_path
        )

    # ------------------------------------------------------------------
    # COMPLETE PROCESSING PIPELINE
    # ------------------------------------------------------------------

    def process_image(
        self,
        image_path: PathLike,
        output_dir: PathLike,
        save_overlay: bool = True,
        save_binary: bool = True,
    ) -> dict:
        """
        Complete segmentation pipeline for one image.

        Outputs:

            *_mask.png
            *_binary.png
            *_overlay.png

        Returns segmentation results and statistics.
        """

        image_path = Path(
            image_path
        )

        output_dir = Path(
            output_dir
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        image = self.load_image(
            image_path
        )

        result = self.segment(
            image
        )

        masks = result[
            "masks"
        ]

        mask_path = (
            output_dir
            / f"{image_path.stem}_mask.tiff"
        )

        self.save_mask(
            masks,
            mask_path,
        )

        binary_path = None

        if save_binary:

            binary_path = (
                output_dir
                / f"{image_path.stem}_binary.png"
            )

            self.save_binary_mask(
                masks,
                binary_path,
            )

        overlay_path = None

        if save_overlay:

            overlay_path = (
                output_dir
                / f"{image_path.stem}_overlay.png"
            )

            self.save_overlay(
                image,
                masks,
                overlay_path,
            )

        statistics = (
            self.get_cell_statistics(
                masks
            )
        )

        return {
            "image": image_path,
            "masks": masks,
            "mask_path": mask_path,
            "binary_path": binary_path,
            "overlay_path": overlay_path,
            "cell_count": len(statistics),
            "cell_statistics": statistics,
            "diameter": result[
                "diameter"
            ],
            "flows": result[
                "flows"
            ],
            "styles": result[
                "styles"
            ],
        }


# ======================================================================
# CONVENIENCE FUNCTION
# ======================================================================


def segment_image(
    image_path: PathLike,
    output_dir: Optional[PathLike] = None,
    model_type: str = "cyto3",
    gpu: bool = True,
) -> dict:
    """
    Convenience function for quick segmentation.

    Example:

        result = segment_image(
            "image.png",
            "processed/cells"
        )
    """

    config = CellposeConfig(
        model_type=model_type,
        gpu=gpu,
    )

    model = CellposeModel(
        config
    )

    if output_dir is None:

        image = model.load_image(
            image_path
        )

        return model.segment(
            image
        )

    return model.process_image(
        image_path,
        output_dir,
    )


# ======================================================================
# COMMAND LINE INTERFACE
# ======================================================================


def main() -> None:
    """
    Simple command-line interface.

    Example:

        python models/cellpose_model.py \
            --input data/raw/images \
            --output data/processed/cells
    """

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Cellpose cell segmentation"
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="Input image or directory",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=str,
        help="Output directory",
    )

    parser.add_argument(
        "--model",
        default="cyto3",
        type=str,
        help="Cellpose model type",
    )

    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Disable GPU",
    )

    args = parser.parse_args()

    config = CellposeConfig(
        model_type=args.model,
        gpu=not args.cpu,
    )

    model = CellposeModel(
        config
    )

    input_path = Path(
        args.input
    )

    output_path = Path(
        args.output
    )

    if input_path.is_file():

        result = model.process_image(
            input_path,
            output_path,
        )

        print(
            f"Processed: {input_path}"
        )

        print(
            f"Detected cells: "
            f"{result['cell_count']}"
        )

    elif input_path.is_dir():

        saved = model.segment_directory(
            input_path,
            output_path,
        )

        print(
            f"Processed {len(saved)} images."
        )

    else:

        raise FileNotFoundError(
            f"Input path does not exist: "
            f"{input_path}"
        )


if __name__ == "__main__":
    main()