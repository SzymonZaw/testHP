# image_pipeline.py
"""
Image Pipeline
==============

Pipeline for processing dermatological / skin images.

Flow:
    raw image
        ↓
    image loading
        ↓
    preprocessing
        ↓
    SAM2 segmentation (optional)
        ↓
    DINOv2 embedding (optional)
        ↓
    result packaging
        ↓
    processed data / embeddings

The pipeline is designed to be used by:
    - main.py
    - multimodal_pipeline.py
    - training scripts
    - evaluation scripts

Expected project structure:

Doktorat_Kod/
├── data/
│   ├── raw/
│   │   └── images/
│   └── processed/
│       ├── images/
│       └── embeddings/
│
├── models/
│   ├── sam2_model.py
│   └── dinov2_model.py
│
├── pipeline/
│   ├── preprocessing.py
│   └── image_pipeline.py
│
└── outputs/
    ├── segmentations/
    └── embeddings/
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image

import torch


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------

PathLike = Union[str, Path]
ImageInput = Union[str, Path, Image.Image, np.ndarray]


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

@dataclass
class ImagePipelineConfig:
    """
    Configuration for the image processing pipeline.
    """

    image_size: int = 224

    normalize: bool = True

    use_segmentation: bool = True
    use_embedding: bool = True

    save_processed_images: bool = True
    save_embeddings: bool = True
    save_metadata: bool = True
    save_segmentation: bool = True

    output_images_dir: PathLike = "data/processed/images"
    output_embeddings_dir: PathLike = "data/processed/embeddings"
    output_segmentation_dir: PathLike = "outputs/segmentations"

    device: Optional[str] = None

    image_extensions: Tuple[str, ...] = (
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    )


# ---------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------

@dataclass
class ImagePipelineResult:
    """
    Result returned by ImagePipeline.process().
    """

    source_path: Optional[str]

    image_shape: Tuple[int, ...]

    processed_shape: Optional[Tuple[int, ...]]

    embedding_shape: Optional[Tuple[int, ...]]

    segmentation_available: bool

    embedding_available: bool

    embedding_path: Optional[str]

    processed_image_path: Optional[str]

    segmentation_path: Optional[str]

    metadata_path: Optional[str]

    metadata: Dict[str, Any]


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def _ensure_directory(path: PathLike) -> Path:
    """
    Create directory if necessary.
    """

    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    return path


def _to_numpy(image: Image.Image) -> np.ndarray:
    """
    Convert PIL image to RGB numpy array.
    """

    image = image.convert("RGB")

    return np.asarray(image)


def _normalize_uint8(image: np.ndarray) -> np.ndarray:
    """
    Normalize arbitrary image array to uint8 [0, 255].
    """

    image = np.asarray(image)

    if image.dtype == np.uint8:
        return image

    image = image.astype(np.float32)

    min_value = float(image.min())
    max_value = float(image.max())

    if max_value <= min_value:
        return np.zeros_like(image, dtype=np.uint8)

    image = (image - min_value) / (max_value - min_value)

    image = image * 255.0

    return image.astype(np.uint8)


def _tensor_to_numpy(tensor: torch.Tensor) -> np.ndarray:
    """
    Convert torch tensor to numpy array.
    """

    return tensor.detach().cpu().numpy()


# ---------------------------------------------------------------------
# Image Pipeline
# ---------------------------------------------------------------------

class ImagePipeline:
    """
    Main skin-image processing pipeline.

    The class intentionally keeps model dependencies optional so that
    preprocessing can still be used when SAM2 or DINOv2 is unavailable.
    """

    def __init__(
        self,
        config: Optional[ImagePipelineConfig] = None,
        sam2_model: Optional[Any] = None,
        dinov2_model: Optional[Any] = None,
        preprocessing: Optional[Any] = None,
    ):
        self.config = config or ImagePipelineConfig()

        self.sam2_model = sam2_model
        self.dinov2_model = dinov2_model
        self.preprocessing = preprocessing

        self.device = self._resolve_device()

        self.output_images_dir = _ensure_directory(
            self.config.output_images_dir
        )

        self.output_embeddings_dir = _ensure_directory(
            self.config.output_embeddings_dir
        )

        self.output_segmentation_dir = _ensure_directory(
            self.config.output_segmentation_dir
        )

        logger.info(
            "ImagePipeline initialized on device: %s",
            self.device,
        )

    # -----------------------------------------------------------------
    # Device
    # -----------------------------------------------------------------

    def _resolve_device(self) -> torch.device:
        """
        Select CUDA when available unless another device is explicitly
        requested.
        """

        if self.config.device is not None:
            return torch.device(self.config.device)

        if torch.cuda.is_available():
            return torch.device("cuda")

        return torch.device("cpu")

    # -----------------------------------------------------------------
    # Loading
    # -----------------------------------------------------------------

    def load_image(
        self,
        image: ImageInput,
    ) -> Tuple[Image.Image, Optional[str]]:
        """
        Load an image from path, PIL image or numpy array.

        Returns:
            PIL image
            source path if available
        """

        if isinstance(image, (str, Path)):
            path = Path(image)

            if not path.exists():
                raise FileNotFoundError(
                    f"Image does not exist: {path}"
                )

            pil_image = Image.open(path).convert("RGB")

            return pil_image, str(path)

        if isinstance(image, Image.Image):
            return image.convert("RGB"), None

        if isinstance(image, np.ndarray):
            array = _normalize_uint8(image)

            if array.ndim == 2:
                pil_image = Image.fromarray(array).convert("RGB")
            elif array.ndim == 3:
                pil_image = Image.fromarray(array).convert("RGB")
            else:
                raise ValueError(
                    "NumPy image must have shape HxW or HxWxC."
                )

            return pil_image, None

        raise TypeError(
            "Unsupported image type. "
            "Use path, PIL.Image.Image or numpy.ndarray."
        )

    # -----------------------------------------------------------------
    # Preprocessing
    # -----------------------------------------------------------------

    def preprocess_image(
        self,
        image: Image.Image,
    ) -> Image.Image:
        """
        Apply preprocessing.

        If pipeline/preprocessing.py exposes a compatible processor,
        it is used. Otherwise a safe default resize operation is applied.
        """

        if self.preprocessing is not None:

            processor = self.preprocessing

            # Object-style API
            if hasattr(processor, "process"):
                try:
                    result = processor.process(image)

                    if isinstance(result, Image.Image):
                        return result

                    if isinstance(result, np.ndarray):
                        return Image.fromarray(
                            _normalize_uint8(result)
                        ).convert("RGB")

                    if torch.is_tensor(result):
                        array = _tensor_to_numpy(result)

                        if array.ndim == 3 and array.shape[0] in (1, 3):
                            array = np.transpose(
                                array,
                                (1, 2, 0),
                            )

                        return Image.fromarray(
                            _normalize_uint8(array)
                        ).convert("RGB")

                except Exception as exc:
                    logger.warning(
                        "Custom preprocessing failed: %s. "
                        "Using fallback preprocessing.",
                        exc,
                    )

            # Callable API
            if callable(processor):

                try:
                    result = processor(image)

                    if isinstance(result, Image.Image):
                        return result

                    if isinstance(result, np.ndarray):
                        return Image.fromarray(
                            _normalize_uint8(result)
                        ).convert("RGB")

                except Exception as exc:
                    logger.warning(
                        "Callable preprocessing failed: %s. "
                        "Using fallback preprocessing.",
                        exc,
                    )

        # -------------------------------------------------------------
        # Fallback preprocessing
        # -------------------------------------------------------------

        return image.resize(
            (
                self.config.image_size,
                self.config.image_size,
            ),
            Image.Resampling.BILINEAR,
        )

    # -----------------------------------------------------------------
    # Image tensor
    # -----------------------------------------------------------------

    def image_to_tensor(
        self,
        image: Image.Image,
    ) -> torch.Tensor:
        """
        Convert PIL image to normalized CHW tensor.
        """

        array = np.asarray(
            image.convert("RGB"),
            dtype=np.float32,
        )

        array /= 255.0

        tensor = torch.from_numpy(array)

        tensor = tensor.permute(
            2,
            0,
            1,
        )

        return tensor

    # -----------------------------------------------------------------
    # Segmentation
    # -----------------------------------------------------------------

    def segment(
        self,
        image: Image.Image,
    ) -> Optional[Any]:
        """
        Run SAM2 segmentation if a SAM2 model has been supplied.

        The exact API is deliberately handled flexibly because
        sam2_model.py may expose different inference interfaces.
        """

        if not self.config.use_segmentation:
            return None

        if self.sam2_model is None:
            logger.debug(
                "SAM2 model not provided. Skipping segmentation."
            )

            return None

        model = self.sam2_model

        # -------------------------------------------------------------
        # Common high-level API
        # -------------------------------------------------------------

        if hasattr(model, "segment"):

            try:
                return model.segment(image)

            except Exception as exc:
                logger.warning(
                    "SAM2 segment() failed: %s",
                    exc,
                )

        # -------------------------------------------------------------
        # Alternative predict API
        # -------------------------------------------------------------

        if hasattr(model, "predict"):

            try:
                return model.predict(image)

            except Exception as exc:
                logger.warning(
                    "SAM2 predict() failed: %s",
                    exc,
                )

        logger.warning(
            "Provided SAM2 model does not expose "
            "segment() or predict()."
        )

        return None

    # -----------------------------------------------------------------
    # Embedding
    # -----------------------------------------------------------------

    @torch.no_grad()
    def extract_embedding(
        self,
        image: Image.Image,
    ) -> Optional[torch.Tensor]:
        """
        Extract DINOv2 embedding.

        Returns:
            Tensor with shape approximately:
                [1, embedding_dim]
        """

        if not self.config.use_embedding:
            return None

        if self.dinov2_model is None:
            logger.debug(
                "DINOv2 model not provided. Skipping embedding."
            )

            return None

        tensor = self.image_to_tensor(image)

        tensor = tensor.unsqueeze(0)

        tensor = tensor.to(self.device)

        model = self.dinov2_model

        # -------------------------------------------------------------
        # High-level embedding API
        # -------------------------------------------------------------

        if hasattr(model, "get_embedding"):

            try:
                embedding = model.get_embedding(tensor)

                if isinstance(embedding, np.ndarray):
                    embedding = torch.from_numpy(embedding)

                if not torch.is_tensor(embedding):
                    embedding = torch.tensor(embedding)

                return embedding.detach().cpu()

            except Exception as exc:
                logger.warning(
                    "DINOv2 get_embedding() failed: %s",
                    exc,
                )

        # -------------------------------------------------------------
        # Alternative encode API
        # -------------------------------------------------------------

        if hasattr(model, "encode"):

            try:
                embedding = model.encode(tensor)

                if isinstance(embedding, np.ndarray):
                    embedding = torch.from_numpy(embedding)

                if not torch.is_tensor(embedding):
                    embedding = torch.tensor(embedding)

                return embedding.detach().cpu()

            except Exception as exc:
                logger.warning(
                    "DINOv2 encode() failed: %s",
                    exc,
                )

        # -------------------------------------------------------------
        # Direct torch model
        # -------------------------------------------------------------

        if callable(model):

            try:
                embedding = model(tensor)

                if isinstance(embedding, dict):

                    for key in (
                        "embedding",
                        "embeddings",
                        "features",
                        "x_norm_clstoken",
                    ):
                        if key in embedding:
                            embedding = embedding[key]
                            break

                if not torch.is_tensor(embedding):
                    embedding = torch.tensor(embedding)

                return embedding.detach().cpu()

            except Exception as exc:
                logger.warning(
                    "DINOv2 callable inference failed: %s",
                    exc,
                )

        logger.warning(
            "Provided DINOv2 model does not expose a supported "
            "embedding interface."
        )

        return None

    # -----------------------------------------------------------------
    # Saving processed image
    # -----------------------------------------------------------------

    def save_processed_image(
        self,
        image: Image.Image,
        source_path: Optional[str],
        output_name: Optional[str] = None,
    ) -> Path:
        """
        Save processed image.
        """

        if output_name is not None:
            filename = Path(output_name).stem + ".png"

        elif source_path is not None:
            filename = Path(source_path).stem + ".png"

        else:
            filename = "processed_image.png"

        output_path = (
            self.output_images_dir /
            filename
        )

        image.save(output_path)

        return output_path

    # -----------------------------------------------------------------
    # Saving embedding
    # -----------------------------------------------------------------

    def save_embedding(
        self,
        embedding: torch.Tensor,
        source_path: Optional[str],
        output_name: Optional[str] = None,
    ) -> Path:
        """
        Save embedding as .pt file.
        """

        if output_name is not None:
            filename = Path(output_name).stem + ".pt"

        elif source_path is not None:
            filename = Path(source_path).stem + ".pt"

        else:
            filename = "embedding.pt"

        output_path = (
            self.output_embeddings_dir /
            filename
        )

        torch.save(
            embedding.cpu(),
            output_path,
        )

        return output_path

    # -----------------------------------------------------------------
    # Segmentation saving
    # -----------------------------------------------------------------

    def save_segmentation(
        self,
        segmentation: Any,
        source_path: Optional[str],
        output_name: Optional[str] = None,
    ) -> Path:
        """
        Save segmentation output.

        Supports:
            numpy arrays
            torch tensors
            dictionaries
            generic Python objects
        """

        if output_name is not None:
            filename = Path(output_name).stem + ".pt"

        elif source_path is not None:
            filename = Path(source_path).stem + ".pt"

        else:
            filename = "segmentation.pt"

        output_path = (
            self.output_segmentation_dir /
            filename
        )

        if torch.is_tensor(segmentation):

            torch.save(
                segmentation.cpu(),
                output_path,
            )

        elif isinstance(segmentation, np.ndarray):

            np.save(
                output_path.with_suffix(".npy"),
                segmentation,
            )

            return output_path.with_suffix(".npy")

        else:

            torch.save(
                segmentation,
                output_path,
            )

        return output_path

    # -----------------------------------------------------------------
    # Metadata
    # -----------------------------------------------------------------

    def build_metadata(
        self,
        source_path: Optional[str],
        original_image: Image.Image,
        processed_image: Image.Image,
        embedding: Optional[torch.Tensor],
        segmentation: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Create metadata dictionary for the processed image.
        """

        metadata: Dict[str, Any] = {
            "source_path": source_path,
            "original_size": list(
                original_image.size
            ),
            "processed_size": list(
                processed_image.size
            ),
            "device": str(self.device),
            "segmentation_available": (
                segmentation is not None
            ),
            "embedding_available": (
                embedding is not None
            ),
        }

        if embedding is not None:
            metadata["embedding_shape"] = list(
                embedding.shape
            )

        return metadata

    # -----------------------------------------------------------------
    # Save metadata
    # -----------------------------------------------------------------

    def save_metadata(
        self,
        metadata: Dict[str, Any],
        source_path: Optional[str],
        output_name: Optional[str] = None,
    ) -> Path:
        """
        Save JSON metadata.
        """

        if output_name is not None:
            filename = Path(output_name).stem + ".json"

        elif source_path is not None:
            filename = Path(source_path).stem + ".json"

        else:
            filename = "image_metadata.json"

        output_path = (
            self.output_images_dir /
            filename
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                indent=2,
                ensure_ascii=False,
            )

        return output_path

    # -----------------------------------------------------------------
    # Main process method
    # -----------------------------------------------------------------

    def process(
        self,
        image: ImageInput,
        output_name: Optional[str] = None,
    ) -> ImagePipelineResult:
        """
        Process one image through the complete pipeline.

        Flow:

            load
              ↓
            preprocess
              ↓
            segmentation
              ↓
            embedding
              ↓
            save
        """

        # -------------------------------------------------------------
        # Load
        # -------------------------------------------------------------

        original_image, source_path = self.load_image(image)

        original_shape = (
            np.asarray(original_image).shape
        )

        logger.info(
            "Processing image: %s",
            source_path or "<memory>",
        )

        # -------------------------------------------------------------
        # Preprocess
        # -------------------------------------------------------------

        processed_image = self.preprocess_image(
            original_image
        )

        processed_shape = (
            np.asarray(processed_image).shape
        )

        # -------------------------------------------------------------
        # Segmentation
        # -------------------------------------------------------------

        segmentation = self.segment(
            processed_image
        )

        # -------------------------------------------------------------
        # Embedding
        # -------------------------------------------------------------

        embedding = self.extract_embedding(
            processed_image
        )

        # -------------------------------------------------------------
        # Save processed image
        # -------------------------------------------------------------

        processed_image_path = None

        if self.config.save_processed_images:

            processed_image_path = str(
                self.save_processed_image(
                    processed_image,
                    source_path,
                    output_name,
                )
            )

        # -------------------------------------------------------------
        # Save segmentation
        # -------------------------------------------------------------

        segmentation_path = None

        if (
            self.config.save_segmentation
            and segmentation is not None
        ):

            segmentation_path = str(
                self.save_segmentation(
                    segmentation,
                    source_path,
                    output_name,
                )
            )

        # -------------------------------------------------------------
        # Save embedding
        # -------------------------------------------------------------

        embedding_path = None

        if (
            self.config.save_embeddings
            and embedding is not None
        ):

            embedding_path = str(
                self.save_embedding(
                    embedding,
                    source_path,
                    output_name,
                )
            )

        # -------------------------------------------------------------
        # Metadata
        # -------------------------------------------------------------

        metadata = self.build_metadata(
            source_path=source_path,
            original_image=original_image,
            processed_image=processed_image,
            embedding=embedding,
            segmentation=segmentation,
        )

        metadata_path = None

        if self.config.save_metadata:

            metadata_path = str(
                self.save_metadata(
                    metadata,
                    source_path,
                    output_name,
                )
            )

        # -------------------------------------------------------------
        # Result
        # -------------------------------------------------------------

        return ImagePipelineResult(
            source_path=source_path,
            image_shape=original_shape,
            processed_shape=processed_shape,
            embedding_shape=(
                tuple(embedding.shape)
                if embedding is not None
                else None
            ),
            segmentation_available=(
                segmentation is not None
            ),
            embedding_available=(
                embedding is not None
            ),
            embedding_path=embedding_path,
            processed_image_path=processed_image_path,
            segmentation_path=segmentation_path,
            metadata_path=metadata_path,
            metadata=metadata,
        )

    # -----------------------------------------------------------------
    # Batch processing
    # -----------------------------------------------------------------

    def discover_images(
        self,
        input_dir: PathLike,
        recursive: bool = True,
    ) -> List[Path]:
        """
        Find supported images in a directory.
        """

        input_dir = Path(input_dir)

        if not input_dir.exists():
            raise FileNotFoundError(
                f"Input directory does not exist: {input_dir}"
            )

        images: List[Path] = []

        if recursive:

            for path in input_dir.rglob("*"):

                if (
                    path.is_file()
                    and path.suffix.lower()
                    in self.config.image_extensions
                ):
                    images.append(path)

        else:

            for path in input_dir.iterdir():

                if (
                    path.is_file()
                    and path.suffix.lower()
                    in self.config.image_extensions
                ):
                    images.append(path)

        return sorted(images)

    def process_directory(
        self,
        input_dir: PathLike,
        recursive: bool = True,
    ) -> List[ImagePipelineResult]:
        """
        Process all supported images in a directory.
        """

        image_paths = self.discover_images(
            input_dir,
            recursive=recursive,
        )

        logger.info(
            "Found %d images.",
            len(image_paths),
        )

        results: List[ImagePipelineResult] = []

        for index, image_path in enumerate(
            image_paths,
            start=1,
        ):

            logger.info(
                "[%d/%d] Processing %s",
                index,
                len(image_paths),
                image_path.name,
            )

            try:

                result = self.process(
                    image_path
                )

                results.append(result)

            except Exception as exc:

                logger.exception(
                    "Failed to process %s: %s",
                    image_path,
                    exc,
                )

        return results


# ---------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------

def process_image(
    image: ImageInput,
    sam2_model: Optional[Any] = None,
    dinov2_model: Optional[Any] = None,
    config: Optional[ImagePipelineConfig] = None,
) -> ImagePipelineResult:
    """
    Convenience wrapper for processing one image.
    """

    pipeline = ImagePipeline(
        config=config,
        sam2_model=sam2_model,
        dinov2_model=dinov2_model,
    )

    return pipeline.process(image)


# ---------------------------------------------------------------------
# Example / smoke test
# ---------------------------------------------------------------------

def _demo() -> None:
    """
    Small smoke test.

    This does not require SAM2 or DINOv2.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    print()
    print("=" * 60)
    print("Image Pipeline")
    print("=" * 60)

    config = ImagePipelineConfig(
        image_size=224,
        use_segmentation=False,
        use_embedding=False,
    )

    pipeline = ImagePipeline(
        config=config
    )

    # Synthetic test image
    test_array = np.zeros(
        (
            512,
            512,
            3,
        ),
        dtype=np.uint8,
    )

    # Simple central structure
    test_array[
        128:384,
        128:384,
        :
    ] = 180

    result = pipeline.process(
        test_array,
        output_name="demo_image",
    )

    print()
    print("Source:", result.source_path)
    print("Original shape:", result.image_shape)
    print("Processed shape:", result.processed_shape)
    print(
        "Segmentation:",
        result.segmentation_available,
    )
    print(
        "Embedding:",
        result.embedding_available,
    )
    print(
        "Processed image:",
        result.processed_image_path,
    )
    print(
        "Metadata:",
        result.metadata_path,
    )

    print()
    print("Image pipeline ready.")


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    _demo()