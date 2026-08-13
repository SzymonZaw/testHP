"""
preprocessing.py

Wspólne funkcje preprocessingowe dla projektu Doktorat_Kod.

Odpowiedzialność modułu:
- walidacja plików wejściowych,
- bezpieczne tworzenie katalogów,
- podstawowe operacje na obrazach,
- normalizacja obrazów,
- konwersja obraz -> tensor,
- normalizacja tensorów,
- przygotowanie danych do dalszych pipeline'ów,
- podstawowa obsługa metadanych.

Moduł nie powinien:
- uruchamiać modeli AI,
- wykonywać segmentacji,
- wykonywać klasyfikacji,
- wykonywać analizy RNA,
- podejmować decyzji klinicznych.

Modele znajdują się w models/.
Pipeline'y wykorzystują funkcje z tego modułu.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import json
import hashlib
import logging
import shutil

import numpy as np

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import torch
except ImportError:
    torch = None


# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger(__name__)

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# ============================================================================
# TYPE ALIASES
# ============================================================================

PathLike = Union[str, Path]
ArrayLike = Union[np.ndarray, "torch.Tensor"]


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PreprocessingConfig:
    """
    Konfiguracja wspólnego preprocessingu.
    """

    image_size: Tuple[int, int] = (224, 224)

    normalize: bool = True

    # Standardowe wartości ImageNet.
    # Można je zmienić dla konkretnego datasetu/modelu.
    mean: Tuple[float, float, float] = (
        0.485,
        0.456,
        0.406,
    )

    std: Tuple[float, float, float] = (
        0.229,
        0.224,
        0.225,
    )

    convert_rgb: bool = True

    allowed_image_extensions: Tuple[str, ...] = (
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    )

    create_output_dirs: bool = True


# ============================================================================
# DATA CONTAINER
# ============================================================================

@dataclass
class PreprocessedImage:
    """
    Kontener na wynik preprocessingu pojedynczego obrazu.
    """

    image: np.ndarray
    source_path: Optional[Path] = None

    original_size: Optional[Tuple[int, int]] = None
    processed_size: Optional[Tuple[int, int]] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PATH UTILITIES
# ============================================================================

def ensure_directory(path: PathLike) -> Path:
    """
    Tworzy katalog, jeśli nie istnieje.

    Parameters
    ----------
    path:
        Ścieżka do katalogu.

    Returns
    -------
    Path
        Utworzona/istniejąca ścieżka.
    """

    path = Path(path)

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def validate_file(
    path: PathLike,
    allowed_extensions: Optional[Sequence[str]] = None,
) -> Path:
    """
    Sprawdza, czy plik istnieje i opcjonalnie czy posiada poprawne rozszerzenie.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {path}"
        )

    if allowed_extensions is not None:
        allowed = {
            ext.lower()
            for ext in allowed_extensions
        }

        if path.suffix.lower() not in allowed:
            raise ValueError(
                f"Unsupported file extension: {path.suffix}. "
                f"Allowed: {sorted(allowed)}"
            )

    return path


def list_files(
    directory: PathLike,
    extensions: Optional[Sequence[str]] = None,
    recursive: bool = True,
) -> List[Path]:
    """
    Zwraca listę plików w katalogu.
    """

    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(
            f"Directory does not exist: {directory}"
        )

    if not directory.is_dir():
        raise ValueError(
            f"Path is not a directory: {directory}"
        )

    if extensions is not None:
        normalized_extensions = {
            ext.lower()
            for ext in extensions
        }
    else:
        normalized_extensions = None

    pattern = "**/*" if recursive else "*"

    files = []

    for path in directory.glob(pattern):

        if not path.is_file():
            continue

        if normalized_extensions is not None:
            if path.suffix.lower() not in normalized_extensions:
                continue

        files.append(path)

    return sorted(files)


# ============================================================================
# IMAGE LOADING
# ============================================================================

def load_image(
    path: PathLike,
    convert_rgb: bool = True,
) -> np.ndarray:
    """
    Wczytuje obraz jako numpy array.

    Zwracany format:
        H x W x C

    Wartości:
        uint8 w zakresie 0-255.
    """

    if Image is None:
        raise ImportError(
            "Pillow is required for image loading. "
            "Install it with: pip install pillow"
        )

    path = validate_file(path)

    logger.debug(
        "Loading image: %s",
        path,
    )

    with Image.open(path) as img:

        if convert_rgb:
            img = img.convert("RGB")

        array = np.asarray(img)

    return array


def save_image(
    image: np.ndarray,
    path: PathLike,
) -> Path:
    """
    Zapisuje numpy array jako obraz.
    """

    if Image is None:
        raise ImportError(
            "Pillow is required for image saving."
        )

    path = Path(path)

    ensure_directory(path.parent)

    image = np.asarray(image)

    if image.dtype != np.uint8:

        if image.max() <= 1.0:
            image = image * 255.0

        image = np.clip(
            image,
            0,
            255,
        ).astype(np.uint8)

    Image.fromarray(image).save(path)

    return path


# ============================================================================
# IMAGE CONVERSION
# ============================================================================

def ensure_rgb(
    image: np.ndarray,
) -> np.ndarray:
    """
    Konwertuje obraz do RGB.

    Obsługiwane:
        H x W
        H x W x 1
        H x W x 3
        H x W x 4
    """

    image = np.asarray(image)

    if image.ndim == 2:

        image = np.stack(
            [image] * 3,
            axis=-1,
        )

    elif image.ndim == 3:

        if image.shape[-1] == 1:

            image = np.repeat(
                image,
                3,
                axis=-1,
            )

        elif image.shape[-1] == 4:

            image = image[..., :3]

        elif image.shape[-1] != 3:

            raise ValueError(
                f"Unsupported channel dimension: {image.shape}"
            )

    else:

        raise ValueError(
            f"Unsupported image shape: {image.shape}"
        )

    return image


def convert_to_float(
    image: np.ndarray,
) -> np.ndarray:
    """
    Konwertuje obraz do float32 w zakresie 0-1.
    """

    image = np.asarray(image)

    if image.dtype == np.uint8:

        return image.astype(
            np.float32
        ) / 255.0

    image = image.astype(
        np.float32
    )

    if image.max() > 1.0:

        image = image / 255.0

    return np.clip(
        image,
        0.0,
        1.0,
    )


# ============================================================================
# IMAGE NORMALIZATION
# ============================================================================

def normalize_image(
    image: np.ndarray,
    mean: Sequence[float],
    std: Sequence[float],
) -> np.ndarray:
    """
    Normalizuje obraz kanałowo:

        x_normalized = (x - mean) / std
    """

    image = convert_to_float(image)

    image = ensure_rgb(image)

    mean_array = np.asarray(
        mean,
        dtype=np.float32,
    ).reshape(1, 1, -1)

    std_array = np.asarray(
        std,
        dtype=np.float32,
    ).reshape(1, 1, -1)

    if np.any(std_array == 0):
        raise ValueError(
            "Standard deviation cannot contain zero."
        )

    return (
        image - mean_array
    ) / std_array


# ============================================================================
# RESIZING
# ============================================================================

def resize_image(
    image: np.ndarray,
    size: Tuple[int, int],
) -> np.ndarray:
    """
    Zmienia rozmiar obrazu.

    Parameters
    ----------
    image:
        H x W x C

    size:
        (width, height)
    """

    if Image is None:
        raise ImportError(
            "Pillow is required for image resizing."
        )

    image = ensure_rgb(image)

    image_float = image

    if image_float.dtype != np.uint8:

        if image_float.max() <= 1.0:

            image_float = (
                image_float * 255
            )

        image_float = np.clip(
            image_float,
            0,
            255,
        ).astype(np.uint8)

    pil_image = Image.fromarray(
        image_float
    )

    resized = pil_image.resize(
        size,
        resample=Image.Resampling.BILINEAR,
    )

    return np.asarray(
        resized
    )


# ============================================================================
# CENTER CROP
# ============================================================================

def center_crop(
    image: np.ndarray,
    size: Tuple[int, int],
) -> np.ndarray:
    """
    Wykonuje centralny crop.

    Parameters
    ----------
    image:
        H x W x C

    size:
        (width, height)
    """

    image = ensure_rgb(image)

    target_width, target_height = size

    height, width = image.shape[:2]

    if (
        target_width > width
        or target_height > height
    ):
        raise ValueError(
            f"Crop size {size} is larger than "
            f"image size {(width, height)}."
        )

    left = (
        width - target_width
    ) // 2

    top = (
        height - target_height
    ) // 2

    right = (
        left + target_width
    )

    bottom = (
        top + target_height
    )

    return image[
        top:bottom,
        left:right,
    ]


# ============================================================================
# IMAGE PIPELINE
# ============================================================================

def preprocess_image(
    image: np.ndarray,
    config: Optional[PreprocessingConfig] = None,
) -> np.ndarray:
    """
    Wykonuje podstawowy preprocessing obrazu.

    Kolejność:

        RGB
        ↓
        resize
        ↓
        float
        ↓
        normalization
    """

    if config is None:
        config = PreprocessingConfig()

    image = ensure_rgb(image)

    image = resize_image(
        image,
        config.image_size,
    )

    image = convert_to_float(
        image
    )

    if config.normalize:

        image = normalize_image(
            image,
            config.mean,
            config.std,
        )

    return image.astype(
        np.float32
    )


def preprocess_image_file(
    path: PathLike,
    config: Optional[PreprocessingConfig] = None,
) -> PreprocessedImage:
    """
    Wczytuje i preprocessuje pojedynczy plik obrazu.
    """

    path = validate_file(path)

    if config is None:
        config = PreprocessingConfig()

    image = load_image(
        path,
        convert_rgb=config.convert_rgb,
    )

    original_size = (
        image.shape[1],
        image.shape[0],
    )

    processed = preprocess_image(
        image,
        config,
    )

    processed_size = (
        processed.shape[1],
        processed.shape[0],
    )

    return PreprocessedImage(
        image=processed,
        source_path=path,
        original_size=original_size,
        processed_size=processed_size,
    )


# ============================================================================
# TORCH CONVERSION
# ============================================================================

def image_to_tensor(
    image: np.ndarray,
    add_batch_dimension: bool = True,
) -> "torch.Tensor":
    """
    Konwertuje obraz:

        H x W x C

    na:

        C x H x W

    lub:

        1 x C x H x W
    """

    if torch is None:
        raise ImportError(
            "PyTorch is required for tensor conversion."
        )

    image = np.asarray(
        image,
        dtype=np.float32,
    )

    image = ensure_rgb(
        image
    )

    tensor = torch.from_numpy(
        image
    )

    tensor = tensor.permute(
        2,
        0,
        1,
    ).contiguous()

    if add_batch_dimension:

        tensor = tensor.unsqueeze(
            0
        )

    return tensor


def tensor_to_numpy(
    tensor: "torch.Tensor",
) -> np.ndarray:
    """
    Konwertuje tensor PyTorch do numpy.
    """

    if torch is None:
        raise ImportError(
            "PyTorch is required."
        )

    if not isinstance(
        tensor,
        torch.Tensor,
    ):
        raise TypeError(
            "Expected torch.Tensor."
        )

    return (
        tensor.detach()
        .cpu()
        .numpy()
    )


# ============================================================================
# BATCH PREPROCESSING
# ============================================================================

def preprocess_directory(
    input_dir: PathLike,
    output_dir: PathLike,
    config: Optional[PreprocessingConfig] = None,
    recursive: bool = True,
) -> List[Path]:
    """
    Preprocessuje wszystkie obrazy znajdujące się w katalogu.

    Zachowuje strukturę podkatalogów.

    Przykład:

        input/
            patient_01/
                image.jpg

        output/
            patient_01/
                image.npy
    """

    if config is None:
        config = PreprocessingConfig()

    input_dir = Path(
        input_dir
    )

    output_dir = ensure_directory(
        output_dir
    )

    files = list_files(
        input_dir,
        extensions=config.allowed_image_extensions,
        recursive=recursive,
    )

    logger.info(
        "Found %d images in %s",
        len(files),
        input_dir,
    )

    processed_files = []

    for input_path in files:

        relative_path = (
            input_path.relative_to(
                input_dir
            )
        )

        output_path = (
            output_dir
            / relative_path
        )

        output_path = (
            output_path.with_suffix(
                ".npy"
            )
        )

        ensure_directory(
            output_path.parent
        )

        try:

            result = preprocess_image_file(
                input_path,
                config,
            )

            np.save(
                output_path,
                result.image,
            )

            processed_files.append(
                output_path
            )

        except Exception as exc:

            logger.exception(
                "Failed preprocessing %s: %s",
                input_path,
                exc,
            )

    logger.info(
        "Successfully processed %d/%d images.",
        len(processed_files),
        len(files),
    )

    return processed_files


# ============================================================================
# METADATA
# ============================================================================

def collect_file_metadata(
    path: PathLike,
) -> Dict[str, Any]:
    """
    Zbiera podstawowe metadane pliku.
    """

    path = validate_file(
        path
    )

    stat = path.stat()

    return {
        "file_name": path.name,
        "file_path": str(path),
        "suffix": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "modified_timestamp": stat.st_mtime,
    }


def calculate_file_hash(
    path: PathLike,
    algorithm: str = "sha256",
    chunk_size: int = 1024 * 1024,
) -> str:
    """
    Oblicza hash pliku.

    Przydatne do sprawdzania integralności datasetów.
    """

    path = validate_file(
        path
    )

    try:
        hash_function = hashlib.new(
            algorithm
        )
    except ValueError as exc:
        raise ValueError(
            f"Unsupported hash algorithm: {algorithm}"
        ) from exc

    with path.open(
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                chunk_size
            )

            if not chunk:
                break

            hash_function.update(
                chunk
            )

    return hash_function.hexdigest()


def save_metadata(
    metadata: Dict[str, Any],
    path: PathLike,
) -> Path:
    """
    Zapisuje metadane do JSON.
    """

    path = Path(path)

    ensure_directory(
        path.parent
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    return path


def load_metadata(
    path: PathLike,
) -> Dict[str, Any]:
    """
    Wczytuje metadane z JSON.
    """

    path = validate_file(
        path
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


# ============================================================================
# DATASET VALIDATION
# ============================================================================

def validate_dataset_directory(
    directory: PathLike,
    allowed_extensions: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Wykonuje podstawową walidację datasetu.

    Zwraca raport:
        {
            "directory": ...,
            "exists": ...,
            "num_files": ...,
            "extensions": ...,
            "total_size_bytes": ...
        }
    """

    directory = Path(
        directory
    )

    if not directory.exists():

        return {
            "directory": str(directory),
            "exists": False,
            "num_files": 0,
            "extensions": {},
            "total_size_bytes": 0,
        }

    files = list_files(
        directory,
        extensions=allowed_extensions,
        recursive=True,
    )

    extension_counts: Dict[str, int] = {}

    total_size = 0

    for path in files:

        extension = (
            path.suffix.lower()
        )

        extension_counts[
            extension
        ] = (
            extension_counts.get(
                extension,
                0,
            )
            + 1
        )

        total_size += (
            path.stat().st_size
        )

    return {
        "directory": str(directory),
        "exists": True,
        "num_files": len(files),
        "extensions": extension_counts,
        "total_size_bytes": total_size,
    }


# ============================================================================
# SAFE COPY
# ============================================================================

def copy_file(
    source: PathLike,
    destination: PathLike,
    overwrite: bool = False,
) -> Path:
    """
    Bezpiecznie kopiuje plik.
    """

    source = validate_file(
        source
    )

    destination = Path(
        destination
    )

    ensure_directory(
        destination.parent
    )

    if (
        destination.exists()
        and not overwrite
    ):
        raise FileExistsError(
            f"Destination already exists: {destination}"
        )

    shutil.copy2(
        source,
        destination,
    )

    return destination


# ============================================================================
# NORMALIZATION HELPERS
# ============================================================================

def min_max_normalize(
    array: np.ndarray,
    epsilon: float = 1e-8,
) -> np.ndarray:
    """
    Normalizacja min-max do [0, 1].
    """

    array = np.asarray(
        array,
        dtype=np.float32,
    )

    min_value = np.min(
        array
    )

    max_value = np.max(
        array
    )

    denominator = (
        max_value
        - min_value
    )

    if denominator < epsilon:

        return np.zeros_like(
            array,
            dtype=np.float32,
        )

    return (
        array - min_value
    ) / denominator


def z_score_normalize(
    array: np.ndarray,
    epsilon: float = 1e-8,
) -> np.ndarray:
    """
    Normalizacja z-score.
    """

    array = np.asarray(
        array,
        dtype=np.float32,
    )

    mean = np.mean(
        array
    )

    std = np.std(
        array
    )

    if std < epsilon:

        return np.zeros_like(
            array,
            dtype=np.float32,
        )

    return (
        array - mean
    ) / std


# ============================================================================
# RANDOM SEED
# ============================================================================

def set_random_seed(
    seed: int = 42,
) -> None:
    """
    Ustawia seed dla numpy i PyTorch.

    Używane w eksperymentach wymagających
    reprodukowalności.
    """

    import random

    random.seed(
        seed
    )

    np.random.seed(
        seed
    )

    if torch is not None:

        torch.manual_seed(
            seed
        )

        if torch.cuda.is_available():

            torch.cuda.manual_seed_all(
                seed
            )


# ============================================================================
# SIMPLE DATASET SUMMARY
# ============================================================================

def summarize_array(
    array: ArrayLike,
) -> Dict[str, Any]:
    """
    Tworzy podstawowe statystyki tablicy/tensora.
    """

    if torch is not None and isinstance(
        array,
        torch.Tensor,
    ):

        data = (
            array.detach()
            .cpu()
            .numpy()
        )

    else:

        data = np.asarray(
            array
        )

    return {
        "shape": tuple(
            data.shape
        ),
        "dtype": str(
            data.dtype
        ),
        "min": float(
            np.min(data)
        ),
        "max": float(
            np.max(data)
        ),
        "mean": float(
            np.mean(data)
        ),
        "std": float(
            np.std(data)
        ),
    }


# ============================================================================
# TEST / DEMO
# ============================================================================

def _demo() -> None:
    """
    Minimalny test modułu.

    Nie wymaga datasetu.
    """

    print("=" * 60)
    print("Preprocessing module")
    print("=" * 60)

    config = PreprocessingConfig()

    print(
        f"Image size: {config.image_size}"
    )

    print(
        f"Normalization: {config.normalize}"
    )

    print(
        f"Mean: {config.mean}"
    )

    print(
        f"Std: {config.std}"
    )

    # Sztuczny obraz testowy.
    image = np.random.randint(
        0,
        256,
        size=(512, 512, 3),
        dtype=np.uint8,
    )

    print(
        "\nOriginal:",
        summarize_array(image),
    )

    processed = preprocess_image(
        image,
        config,
    )

    print(
        "\nProcessed:",
        summarize_array(processed),
    )

    if torch is not None:

        tensor = image_to_tensor(
            processed
        )

        print(
            "\nTensor:",
            tuple(tensor.shape),
        )

    print(
        "\nPreprocessing module ready."
    )


if __name__ == "__main__":
    _demo()