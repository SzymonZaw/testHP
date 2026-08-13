# models/monai_pipeline.py

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np

try:
    import torch
except ImportError as exc:
    raise ImportError(
        "PyTorch is required for monai_pipeline.py. "
        "Install it with: pip install torch"
    ) from exc

try:
    from PIL import Image
except ImportError as exc:
    raise ImportError(
        "Pillow is required for monai_pipeline.py. "
        "Install it with: pip install pillow"
    ) from exc

try:
    import monai
    from monai.transforms import (
        Compose,
        EnsureChannelFirst,
        EnsureType,
        LoadImage,
        RandFlip,
        RandRotate,
        Resize,
        ScaleIntensity,
        ToTensor,
    )
except ImportError as exc:
    raise ImportError(
        "MONAI is required for monai_pipeline.py. "
        "Install it with: pip install monai"
    ) from exc


PathLike = Union[str, Path]


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class MONAIConfig:
    """
    Configuration for the MONAI preprocessing pipeline.

    The configuration is intentionally conservative:
    preprocessing should not destroy biological information.

    Parameters
    ----------
    image_size:
        Target spatial size (height, width).

    normalize:
        Normalize intensity values.

    scale_intensity:
        Scale image intensities to a standard range.

    augment:
        Enable random training augmentations.

    rotation_range:
        Rotation range in radians.

    flip_probability:
        Probability of random horizontal/vertical flips.

    device:
        "cuda", "cpu" or "auto".

    output_dtype:
        Torch dtype used by the pipeline.
    """

    image_size: Optional[Tuple[int, int]] = None

    normalize: bool = True
    scale_intensity: bool = True

    augment: bool = False

    rotation_range: float = 0.15
    flip_probability: float = 0.5

    device: str = "auto"

    output_dtype: torch.dtype = torch.float32


# ============================================================================
# DEVICE UTILITIES
# ============================================================================


def resolve_device(device: str = "auto") -> torch.device:
    """
    Resolve computation device.

    Parameters
    ----------
    device:
        "auto", "cuda", "cpu"
    """

    device = device.lower()

    if device == "auto":
        return torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

    if device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA was requested but is not available."
            )

        return torch.device("cuda")

    if device == "cpu":
        return torch.device("cpu")

    raise ValueError(
        f"Unsupported device: {device}"
    )


# ============================================================================
# IMAGE LOADING
# ============================================================================


class MONAIImageLoader:
    """
    Image loading utility.

    Supports common image formats and uses MONAI where appropriate.
    """

    SUPPORTED_EXTENSIONS = (
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".bmp",
    )

    def __init__(
        self,
        ensure_channel_first: bool = True,
    ) -> None:

        self.ensure_channel_first = (
            ensure_channel_first
        )

        self.loader = LoadImage(
            image_only=True
        )

    def load(
        self,
        image_path: PathLike,
    ) -> np.ndarray:
        """
        Load image and return numpy array.
        """

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        image = self.loader(
            str(image_path)
        )

        image = np.asarray(image)

        if self.ensure_channel_first:
            image = self._ensure_channel_first(
                image
            )

        return image

    @staticmethod
    def _ensure_channel_first(
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert image to C,H,W representation.
        """

        if image.ndim == 2:
            return image[None, ...]

        if image.ndim == 3:

            # H,W,C
            if image.shape[-1] in (1, 3, 4):
                return np.moveaxis(
                    image,
                    -1,
                    0,
                )

            # Already C,H,W
            return image

        raise ValueError(
            "Expected 2D or 3D image."
        )


# ============================================================================
# BASIC IMAGE OPERATIONS
# ============================================================================


class MONAIImageProcessor:
    """
    Basic deterministic image preprocessing.

    This class is intentionally separate from augmentation.
    """

    def __init__(
        self,
        config: MONAIConfig,
    ) -> None:

        self.config = config

    def build_transform(self):
        """
        Build deterministic MONAI transform.
        """

        transforms = [
            EnsureType(
                data_type="numpy"
            ),
        ]

        if self.config.image_size is not None:

            transforms.append(
                Resize(
                    spatial_size=self.config.image_size,
                    mode="bilinear",
                )
            )

        if self.config.scale_intensity:

            transforms.append(
                ScaleIntensity()
            )

        transforms.append(
            EnsureType(
                data_type="tensor"
            )
        )

        return Compose(
            transforms
        )

    def process(
        self,
        image: np.ndarray,
    ) -> torch.Tensor:
        """
        Apply deterministic preprocessing.
        """

        image = np.asarray(
            image
        )

        transform = self.build_transform()

        result = transform(
            image
        )

        result = result.to(
            dtype=self.config.output_dtype
        )

        return result


# ============================================================================
# AUGMENTATION
# ============================================================================


class MONAIAugmentation:
    """
    Training-time image augmentation.

    Augmentation should only be enabled for training.
    """

    def __init__(
        self,
        config: MONAIConfig,
    ) -> None:

        self.config = config

    def build_transform(self):
        """
        Build augmentation transform.
        """

        transforms = []

        if self.config.image_size is not None:

            transforms.append(
                Resize(
                    spatial_size=self.config.image_size,
                    mode="bilinear",
                )
            )

        transforms.extend(
            [
                RandFlip(
                    prob=self.config.flip_probability,
                    spatial_axis=0,
                ),
                RandFlip(
                    prob=self.config.flip_probability,
                    spatial_axis=1,
                ),
                RandRotate(
                    range_x=self.config.rotation_range,
                    prob=0.5,
                    mode="bilinear",
                ),
            ]
        )

        if self.config.scale_intensity:

            transforms.append(
                ScaleIntensity()
            )

        transforms.append(
            EnsureType(
                data_type="tensor"
            )
        )

        return Compose(
            transforms
        )

    def process(
        self,
        image: np.ndarray,
    ) -> torch.Tensor:
        """
        Apply random training augmentation.
        """

        transform = self.build_transform()

        result = transform(
            image
        )

        return result.to(
            dtype=self.config.output_dtype
        )


# ============================================================================
# MAIN MONAI PIPELINE
# ============================================================================


class MONAIPipeline:
    """
    Main MONAI image preprocessing pipeline.

    Responsibilities
    ----------------
    1. Load images.
    2. Convert to channel-first representation.
    3. Resize when configured.
    4. Normalize/scale intensity.
    5. Apply optional training augmentation.
    6. Convert to PyTorch tensors.
    7. Move tensors to the selected device.
    8. Create batches.

    It does NOT:
        - perform Cellpose segmentation
        - perform SAM2 segmentation
        - extract DINOv2 embeddings
        - perform pathology classification

    Those responsibilities belong to their respective modules.
    """

    def __init__(
        self,
        config: Optional[MONAIConfig] = None,
    ) -> None:

        self.config = (
            config
            or MONAIConfig()
        )

        self.device = resolve_device(
            self.config.device
        )

        self.loader = (
            MONAIImageLoader()
        )

        self.processor = (
            MONAIImageProcessor(
                self.config
            )
        )

        self.augmentation = (
            MONAIAugmentation(
                self.config
            )
        )

    # ------------------------------------------------------------------------
    # LOAD
    # ------------------------------------------------------------------------

    def load(
        self,
        image_path: PathLike,
    ) -> np.ndarray:
        """
        Load one image.
        """

        return self.loader.load(
            image_path
        )

    # ------------------------------------------------------------------------
    # PREPROCESS
    # ------------------------------------------------------------------------

    def preprocess(
        self,
        image: Union[PathLike, np.ndarray],
        training: bool = False,
    ) -> torch.Tensor:
        """
        Preprocess image.

        Parameters
        ----------
        image:
            Image path or numpy array.

        training:
            If True, apply random augmentation.
        """

        if isinstance(
            image,
            (str, Path),
        ):
            image = self.load(
                image
            )

        image = np.asarray(
            image
        )

        if training and self.config.augment:

            tensor = (
                self.augmentation.process(
                    image
                )
            )

        else:

            tensor = (
                self.processor.process(
                    image
                )
            )

        tensor = tensor.to(
            self.device
        )

        return tensor

    # ------------------------------------------------------------------------
    # BATCH
    # ------------------------------------------------------------------------

    def create_batch(
        self,
        images: Sequence[
            Union[PathLike, np.ndarray]
        ],
        training: bool = False,
    ) -> torch.Tensor:
        """
        Preprocess a collection of images
        and return a batched tensor.

        Output:
            B,C,H,W
        """

        tensors = []

        for image in images:

            tensor = self.preprocess(
                image,
                training=training,
            )

            tensors.append(
                tensor
            )

        if not tensors:
            raise ValueError(
                "No images provided."
            )

        batch = torch.stack(
            tensors,
            dim=0,
        )

        return batch

    # ------------------------------------------------------------------------
    # SINGLE IMAGE -> MODEL INPUT
    # ------------------------------------------------------------------------

    def prepare_model_input(
        self,
        image: Union[PathLike, np.ndarray],
        training: bool = False,
    ) -> torch.Tensor:
        """
        Prepare a single image for neural network inference.

        Ensures batch dimension:

            C,H,W
                ->
            1,C,H,W
        """

        tensor = self.preprocess(
            image,
            training=training,
        )

        if tensor.ndim == 3:

            tensor = tensor.unsqueeze(
                dim=0
            )

        elif tensor.ndim == 4:
            pass

        else:
            raise ValueError(
                f"Unexpected tensor shape: "
                f"{tuple(tensor.shape)}"
            )

        return tensor

    # ------------------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------------------

    @staticmethod
    def tensor_to_numpy(
        tensor: torch.Tensor,
    ) -> np.ndarray:
        """
        Convert tensor to numpy.
        """

        return (
            tensor.detach()
            .cpu()
            .numpy()
        )

    @staticmethod
    def save_tensor(
        tensor: torch.Tensor,
        output_path: PathLike,
    ) -> None:
        """
        Save preprocessed tensor to .pt file.
        """

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        torch.save(
            tensor.detach().cpu(),
            output_path,
        )

    # ------------------------------------------------------------------------
    # PROCESS IMAGE
    # ------------------------------------------------------------------------

    def process_image(
        self,
        image_path: PathLike,
        output_path: Optional[PathLike] = None,
        training: bool = False,
    ) -> torch.Tensor:
        """
        Load, preprocess and optionally save one image.
        """

        tensor = self.prepare_model_input(
            image_path,
            training=training,
        )

        if output_path is not None:

            self.save_tensor(
                tensor,
                output_path,
            )

        return tensor

    # ------------------------------------------------------------------------
    # DIRECTORY
    # ------------------------------------------------------------------------

    def process_directory(
        self,
        input_dir: PathLike,
        output_dir: PathLike,
        training: bool = False,
        extensions: Optional[
            Tuple[str, ...]
        ] = None,
    ) -> List[Path]:
        """
        Process every supported image in a directory.

        Directory structure is preserved.
        """

        input_dir = Path(
            input_dir
        )

        output_dir = Path(
            output_dir
        )

        if not input_dir.exists():
            raise FileNotFoundError(
                f"Input directory does not exist: "
                f"{input_dir}"
            )

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
                ".bmp",
            )

        image_paths = [
            p
            for p in input_dir.rglob("*")
            if p.is_file()
            and p.suffix.lower()
            in extensions
        ]

        saved_paths = []

        for image_path in image_paths:

            relative_path = (
                image_path.relative_to(
                    input_dir
                )
            )

            output_path = (
                output_dir
                / relative_path
            )

            output_path = (
                output_path.with_suffix(
                    ".pt"
                )
            )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.process_image(
                image_path,
                output_path,
                training=training,
            )

            saved_paths.append(
                output_path
            )

        return saved_paths


# ============================================================================
# MEDICAL IMAGE HELPERS
# ============================================================================


class MedicalImageUtils:
    """
    Utility functions for medical/biological images.
    """

    @staticmethod
    def percentile_normalize(
        image: np.ndarray,
        lower: float = 1.0,
        upper: float = 99.0,
    ) -> np.ndarray:
        """
        Robust percentile normalization.

        Useful when images have different intensity ranges.
        """

        image = image.astype(
            np.float32
        )

        low = np.percentile(
            image,
            lower,
        )

        high = np.percentile(
            image,
            upper,
        )

        if high <= low:

            return np.zeros_like(
                image
            )

        image = (
            image - low
        ) / (
            high - low
        )

        return np.clip(
            image,
            0.0,
            1.0,
        )

    @staticmethod
    def standardize(
        image: np.ndarray,
        epsilon: float = 1e-8,
    ) -> np.ndarray:
        """
        Z-score standardization.
        """

        image = image.astype(
            np.float32
        )

        mean = image.mean()
        std = image.std()

        return (
            image - mean
        ) / (
            std + epsilon
        )

    @staticmethod
    def rgb_to_grayscale(
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert RGB image to grayscale.

        Uses standard luminance coefficients.
        """

        if image.ndim != 3:
            raise ValueError(
                "Expected RGB image."
            )

        if image.shape[-1] != 3:
            raise ValueError(
                "Expected image with 3 channels."
            )

        image = image.astype(
            np.float32
        )

        grayscale = (
            0.299 * image[..., 0]
            + 0.587 * image[..., 1]
            + 0.114 * image[..., 2]
        )

        return grayscale

    @staticmethod
    def ensure_float32(
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert image to float32.
        """

        return image.astype(
            np.float32
        )


# ============================================================================
# DATASET WRAPPER
# ============================================================================


class MONAIImageDataset(
    torch.utils.data.Dataset
):
    """
    Lightweight PyTorch Dataset using MONAI preprocessing.

    Expected directory:

        root/
            image_001.png
            image_002.png
            image_003.png
    """

    def __init__(
        self,
        image_paths: Sequence[PathLike],
        pipeline: MONAIPipeline,
        training: bool = False,
    ) -> None:

        self.image_paths = [
            Path(p)
            for p in image_paths
        ]

        self.pipeline = pipeline
        self.training = training

    def __len__(self) -> int:
        return len(
            self.image_paths
        )

    def __getitem__(
        self,
        index: int,
    ) -> Dict[str, Any]:

        image_path = (
            self.image_paths[index]
        )

        tensor = (
            self.pipeline.prepare_model_input(
                image_path,
                training=self.training,
            )
        )

        return {
            "image": tensor.squeeze(
                dim=0
            ),
            "path": str(
                image_path
            ),
        }


# ============================================================================
# DATASET DISCOVERY
# ============================================================================


def discover_images(
    root: PathLike,
    extensions: Optional[
        Tuple[str, ...]
    ] = None,
) -> List[Path]:
    """
    Recursively discover images.
    """

    root = Path(root)

    if not root.exists():
        raise FileNotFoundError(
            f"Directory does not exist: "
            f"{root}"
        )

    if extensions is None:

        extensions = (
            ".png",
            ".jpg",
            ".jpeg",
            ".tif",
            ".tiff",
            ".bmp",
        )

    paths = [
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower()
        in extensions
    ]

    return sorted(
        paths
    )


# ============================================================================
# DATALOADER
# ============================================================================


def create_dataloader(
    image_paths: Sequence[PathLike],
    pipeline: MONAIPipeline,
    batch_size: int = 8,
    shuffle: bool = False,
    num_workers: int = 0,
    training: bool = False,
):
    """
    Create a PyTorch DataLoader.
    """

    dataset = MONAIImageDataset(
        image_paths=image_paths,
        pipeline=pipeline,
        training=training,
    )

    return torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=(
            pipeline.device.type == "cuda"
        ),
    )


# ============================================================================
# QUICK INFERENCE FUNCTION
# ============================================================================


def preprocess_image(
    image_path: PathLike,
    image_size: Optional[
        Tuple[int, int]
    ] = None,
    device: str = "auto",
) -> torch.Tensor:
    """
    Convenience function.

    Example:

        tensor = preprocess_image(
            "image.png",
            image_size=(224, 224)
        )
    """

    config = MONAIConfig(
        image_size=image_size,
        device=device,
    )

    pipeline = MONAIPipeline(
        config
    )

    return pipeline.prepare_model_input(
        image_path
    )


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    """
    Command line interface.

    Example:

        python models/monai_pipeline.py \
            --input data/raw/images \
            --output data/processed/images
    """

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "MONAI medical image preprocessing pipeline"
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
        "--size",
        nargs=2,
        type=int,
        default=None,
        metavar=("HEIGHT", "WIDTH"),
        help="Target image size",
    )

    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force CPU",
    )

    parser.add_argument(
        "--augment",
        action="store_true",
        help="Enable training augmentation",
    )

    args = parser.parse_args()

    image_size = None

    if args.size is not None:

        image_size = (
            args.size[0],
            args.size[1],
        )

    config = MONAIConfig(
        image_size=image_size,
        device=(
            "cpu"
            if args.cpu
            else "auto"
        ),
        augment=args.augment,
    )

    pipeline = MONAIPipeline(
        config
    )

    input_path = Path(
        args.input
    )

    output_dir = Path(
        args.output
    )

    if input_path.is_file():

        output_path = (
            output_dir
            / f"{input_path.stem}.pt"
        )

        pipeline.process_image(
            input_path,
            output_path,
            training=args.augment,
        )

        print(
            f"Processed: {input_path}"
        )

        print(
            f"Saved: {output_path}"
        )

    elif input_path.is_dir():

        saved_paths = (
            pipeline.process_directory(
                input_path,
                output_dir,
                training=args.augment,
            )
        )

        print(
            f"Processed "
            f"{len(saved_paths)} images."
        )

    else:

        raise FileNotFoundError(
            f"Input path does not exist: "
            f"{input_path}"
        )


if __name__ == "__main__":
    main()