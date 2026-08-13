
"""
cell_pipeline.py

Pipeline przetwarzania komórek skóry.

Odpowiedzialność:
    1. Wczytywanie obrazów.
    2. Segmentacja/detekcja komórek przez Cellpose.
    3. Czyszczenie i walidacja masek.
    4. Ekstrakcja podstawowych cech komórkowych.
    5. Zapis masek i metadanych do data/processed/cells/.
    6. Przygotowanie danych dla:
       - cell_analysis.py
       - morphology_analysis.py
       - aging_model.py
       - abnormality_model.py
       - fusion_model.py

Pipeline nie wykonuje treningu modelu.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

try:
    from models.cellpose_model import CellposeModel
except ImportError:
    CellposeModel = None


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------

@dataclass
class CellFeature:
    """Podstawowe cechy pojedynczej komórki."""

    cell_id: int

    area: float
    centroid_x: float
    centroid_y: float

    bbox_x_min: int
    bbox_y_min: int
    bbox_x_max: int
    bbox_y_max: int

    width: int
    height: int

    aspect_ratio: float
    perimeter: float
    circularity: float

    mean_intensity: float
    mean_r: float
    mean_g: float
    mean_b: float


@dataclass
class CellPipelineResult:
    """Wynik przetwarzania jednego obrazu."""

    image_path: str

    image_width: int
    image_height: int

    num_cells: int

    mask_path: Optional[str]
    features_path: Optional[str]
    metadata_path: Optional[str]

    features: List[CellFeature]


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def load_image(path: Path) -> np.ndarray:
    """
    Wczytuje obraz RGB.

    Parameters
    ----------
    path:
        Ścieżka do obrazu.

    Returns
    -------
    np.ndarray
        Obraz RGB w formacie H x W x 3.
    """

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    image = Image.open(path).convert("RGB")
    return np.asarray(image)


def save_mask(mask: np.ndarray, path: Path) -> None:
    """
    Zapisuje maskę komórek jako PNG.

    Każda komórka posiada osobny identyfikator:
        0 = tło
        1..N = kolejne komórki
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    mask_uint = mask.astype(np.uint16)

    Image.fromarray(mask_uint).save(path)


def save_json(data: Dict[str, Any], path: Path) -> None:
    """Zapisuje dane JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ---------------------------------------------------------------------
# Mask processing
# ---------------------------------------------------------------------

def relabel_mask(mask: np.ndarray) -> np.ndarray:
    """
    Normalizuje identyfikatory obiektów w masce.

    Przykład:

        0 0 4 4 0
        0 7 7 0 0
        0 0 0 9 9

    zostanie przekształcone na:

        0 0 1 1 0
        0 2 2 0 0
        0 0 0 3 3
    """

    mask = np.asarray(mask)

    labels = np.unique(mask)
    labels = labels[labels > 0]

    new_mask = np.zeros_like(mask, dtype=np.int32)

    for new_id, old_id in enumerate(labels, start=1):
        new_mask[mask == old_id] = new_id

    return new_mask


def remove_small_objects(
    mask: np.ndarray,
    min_area: int = 20,
) -> np.ndarray:
    """
    Usuwa bardzo małe obiekty.

    Nie używamy tutaj ciężkich zależności zewnętrznych.
    Funkcja działa bezpośrednio na etykietach maski.
    """

    mask = np.asarray(mask)
    result = np.zeros_like(mask)

    labels, counts = np.unique(
        mask[mask > 0],
        return_counts=True,
    )

    for label, count in zip(labels, counts):
        if count >= min_area:
            result[mask == label] = label

    return relabel_mask(result)


# ---------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------

def calculate_perimeter(binary_mask: np.ndarray) -> float:
    """
    Przybliżony obwód obiektu na podstawie liczby przejść
    pomiędzy pikselami obiektu i tłem.
    """

    mask = binary_mask.astype(bool)

    if not mask.any():
        return 0.0

    padded = np.pad(mask, 1, mode="constant", constant_values=False)

    horizontal = np.sum(
        padded[1:-1, 1:-1] != padded[1:-1, :-2]
    )

    horizontal += np.sum(
        padded[1:-1, 1:-1] != padded[1:-1, 2:]
    )

    vertical = np.sum(
        padded[1:-1, 1:-1] != padded[:-2, 1:-1]
    )

    vertical += np.sum(
        padded[1:-1, 1:-1] != padded[2:, 1:-1]
    )

    return float((horizontal + vertical) / 2.0)


def calculate_circularity(
    area: float,
    perimeter: float,
) -> float:
    """
    Circularity:

        4πA / P²

    Wartość bliższa 1 oznacza kształt bardziej zbliżony
    do koła.
    """

    if perimeter <= 0:
        return 0.0

    return float(
        (4.0 * np.pi * area) /
        (perimeter ** 2)
    )


# ---------------------------------------------------------------------
# Cell feature extraction
# ---------------------------------------------------------------------

def extract_cell_features(
    image: np.ndarray,
    mask: np.ndarray,
) -> List[CellFeature]:
    """
    Ekstrahuje cechy wszystkich komórek.

    Parameters
    ----------
    image:
        Obraz RGB H x W x 3.

    mask:
        Maska instancji H x W.

    Returns
    -------
    list[CellFeature]
    """

    features: List[CellFeature] = []

    labels = np.unique(mask)
    labels = labels[labels > 0]

    for cell_id in labels:

        cell_pixels = mask == cell_id

        ys, xs = np.where(cell_pixels)

        if len(xs) == 0:
            continue

        area = float(len(xs))

        centroid_x = float(xs.mean())
        centroid_y = float(ys.mean())

        x_min = int(xs.min())
        x_max = int(xs.max())

        y_min = int(ys.min())
        y_max = int(ys.max())

        width = x_max - x_min + 1
        height = y_max - y_min + 1

        aspect_ratio = (
            float(width / height)
            if height > 0
            else 0.0
        )

        perimeter = calculate_perimeter(cell_pixels)

        circularity = calculate_circularity(
            area,
            perimeter,
        )

        pixels = image[cell_pixels]

        mean_rgb = pixels.mean(axis=0)

        mean_r = float(mean_rgb[0])
        mean_g = float(mean_rgb[1])
        mean_b = float(mean_rgb[2])

        mean_intensity = float(
            np.mean(mean_rgb)
        )

        features.append(
            CellFeature(
                cell_id=int(cell_id),

                area=area,

                centroid_x=centroid_x,
                centroid_y=centroid_y,

                bbox_x_min=x_min,
                bbox_y_min=y_min,
                bbox_x_max=x_max,
                bbox_y_max=y_max,

                width=width,
                height=height,

                aspect_ratio=aspect_ratio,
                perimeter=perimeter,
                circularity=circularity,

                mean_intensity=mean_intensity,
                mean_r=mean_r,
                mean_g=mean_g,
                mean_b=mean_b,
            )
        )

    return features


# ---------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------

class CellPipeline:
    """
    Główny pipeline komórkowy.

    Przepływ:

        image
          ↓
        Cellpose
          ↓
        instance mask
          ↓
        mask cleaning
          ↓
        cell features
          ↓
        processed/cells
    """

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff",
        ".bmp",
        ".webp",
    }

    def __init__(
        self,
        output_dir: str | Path = "data/processed/cells",
        cellpose_model: Optional[Any] = None,
        min_cell_area: int = 20,
    ) -> None:

        self.output_dir = Path(output_dir)

        self.min_cell_area = min_cell_area

        if cellpose_model is not None:
            self.cellpose = cellpose_model

        elif CellposeModel is not None:
            try:
                self.cellpose = CellposeModel()
            except Exception as exc:
                logger.warning(
                    "Could not initialize CellposeModel: %s",
                    exc,
                )
                self.cellpose = None

        else:
            self.cellpose = None

        logger.info(
            "CellPipeline initialized. output=%s",
            self.output_dir,
        )

    # -----------------------------------------------------------------
    # Segmentation
    # -----------------------------------------------------------------

    def segment(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Wykonuje segmentację komórek.

        Oczekuje, że CellposeModel posiada metodę:

            segment(image)

        Zwraca maskę instancji.
        """

        if self.cellpose is None:
            raise RuntimeError(
                "Cellpose model is not initialized."
            )

        if not hasattr(self.cellpose, "segment"):
            raise AttributeError(
                "Cellpose model must provide "
                "a 'segment(image)' method."
            )

        mask = self.cellpose.segment(image)

        mask = np.asarray(mask)

        if mask.ndim != 2:
            raise ValueError(
                f"Expected 2D instance mask, got shape {mask.shape}"
            )

        return mask.astype(np.int32)

    # -----------------------------------------------------------------
    # Process one image
    # -----------------------------------------------------------------

    def process_image(
        self,
        image_path: str | Path,
        save_outputs: bool = True,
    ) -> CellPipelineResult:
        """
        Przetwarza pojedynczy obraz.

        Parameters
        ----------
        image_path:
            Ścieżka do obrazu.

        save_outputs:
            Czy zapisywać maskę i metadane.

        Returns
        -------
        CellPipelineResult
        """

        image_path = Path(image_path)

        logger.info(
            "Processing image: %s",
            image_path,
        )

        image = load_image(image_path)

        height, width = image.shape[:2]

        # -------------------------------------------------------------
        # 1. Cell segmentation
        # -------------------------------------------------------------

        mask = self.segment(image)

        # -------------------------------------------------------------
        # 2. Cleaning
        # -------------------------------------------------------------

        mask = remove_small_objects(
            mask,
            min_area=self.min_cell_area,
        )

        # -------------------------------------------------------------
        # 3. Feature extraction
        # -------------------------------------------------------------

        features = extract_cell_features(
            image=image,
            mask=mask,
        )

        # -------------------------------------------------------------
        # 4. Output paths
        # -------------------------------------------------------------

        stem = image_path.stem

        mask_path = (
            self.output_dir /
            "masks" /
            f"{stem}_cells.png"
        )

        features_path = (
            self.output_dir /
            "features" /
            f"{stem}_cells.json"
        )

        metadata_path = (
            self.output_dir /
            "metadata" /
            f"{stem}.json"
        )

        # -------------------------------------------------------------
        # 5. Save
        # -------------------------------------------------------------

        if save_outputs:

            save_mask(
                mask,
                mask_path,
            )

            save_json(
                {
                    "image": str(image_path),
                    "num_cells": len(features),
                    "features": [
                        asdict(feature)
                        for feature in features
                    ],
                },
                features_path,
            )

            save_json(
                {
                    "image_path": str(image_path),
                    "image_width": width,
                    "image_height": height,
                    "num_cells": len(features),
                    "mask_path": str(mask_path),
                    "features_path": str(features_path),
                },
                metadata_path,
            )

        result = CellPipelineResult(
            image_path=str(image_path),

            image_width=width,
            image_height=height,

            num_cells=len(features),

            mask_path=(
                str(mask_path)
                if save_outputs
                else None
            ),

            features_path=(
                str(features_path)
                if save_outputs
                else None
            ),

            metadata_path=(
                str(metadata_path)
                if save_outputs
                else None
            ),

            features=features,
        )

        logger.info(
            "Detected %d cells in %s",
            len(features),
            image_path.name,
        )

        return result

    # -----------------------------------------------------------------
    # Directory processing
    # -----------------------------------------------------------------

    def find_images(
        self,
        input_dir: str | Path,
    ) -> List[Path]:
        """
        Znajduje obrazy w katalogu rekursywnie.
        """

        input_dir = Path(input_dir)

        if not input_dir.exists():
            raise FileNotFoundError(
                f"Input directory not found: {input_dir}"
            )

        images = [
            path
            for path in input_dir.rglob("*")
            if (
                path.is_file()
                and path.suffix.lower()
                in self.SUPPORTED_EXTENSIONS
            )
        ]

        return sorted(images)

    def process_directory(
        self,
        input_dir: str | Path,
        save_outputs: bool = True,
    ) -> List[CellPipelineResult]:
        """
        Przetwarza wszystkie obrazy w katalogu.
        """

        images = self.find_images(input_dir)

        logger.info(
            "Found %d images in %s",
            len(images),
            input_dir,
        )

        results: List[CellPipelineResult] = []

        for image_path in images:

            try:

                result = self.process_image(
                    image_path=image_path,
                    save_outputs=save_outputs,
                )

                results.append(result)

            except Exception as exc:

                logger.exception(
                    "Failed to process %s: %s",
                    image_path,
                    exc,
                )

        return results

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------

    @staticmethod
    def summarize(
        results: Sequence[CellPipelineResult],
    ) -> Dict[str, Any]:
        """
        Tworzy podsumowanie działania pipeline'u.
        """

        total_images = len(results)

        total_cells = sum(
            result.num_cells
            for result in results
        )

        mean_cells_per_image = (
            total_cells / total_images
            if total_images > 0
            else 0.0
        )

        return {
            "images_processed": total_images,
            "total_cells": total_cells,
            "mean_cells_per_image": mean_cells_per_image,
        }


# ---------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------

def run_cell_pipeline(
    input_path: str | Path,
    output_dir: str | Path = "data/processed/cells",
    min_cell_area: int = 20,
) -> Dict[str, Any]:
    """
    Prosty interfejs do uruchomienia pipeline'u.

    input_path może być:
        - pojedynczym obrazem
        - katalogiem obrazów
    """

    pipeline = CellPipeline(
        output_dir=output_dir,
        min_cell_area=min_cell_area,
    )

    input_path = Path(input_path)

    if input_path.is_file():

        result = pipeline.process_image(
            input_path
        )

        return {
            "mode": "single_image",
            "summary": pipeline.summarize(
                [result]
            ),
            "results": [result],
        }

    if input_path.is_dir():

        results = pipeline.process_directory(
            input_path
        )

        return {
            "mode": "directory",
            "summary": pipeline.summarize(
                results
            ),
            "results": results,
        }

    raise FileNotFoundError(
        f"Input path does not exist: {input_path}"
    )


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> None:
    """
    Przykładowe uruchomienie:

        python pipeline/cell_pipeline.py \
            --input data/raw/images/lesions \
            --output data/processed/cells
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="Cell segmentation and feature extraction pipeline."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Input image or directory.",
    )

    parser.add_argument(
        "--output",
        default="data/processed/cells",
        help="Output directory.",
    )

    parser.add_argument(
        "--min-cell-area",
        type=int,
        default=20,
        help="Minimum cell area in pixels.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    summary = run_cell_pipeline(
        input_path=args.input,
        output_dir=args.output,
        min_cell_area=args.min_cell_area,
    )

    print("\nCell pipeline summary")
    print("---------------------")

    for key, value in summary["summary"].items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

