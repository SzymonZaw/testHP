"""
Morphology Analysis
===================

Morphological analysis of cells and segmented biological structures.

This module focuses on shape rather than classification.

It calculates:
- area
- perimeter approximation
- circularity
- aspect ratio
- eccentricity approximation
- solidity approximation
- size distribution
- morphology abnormality score
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class MorphologyFeature:
    object_id: int

    area: float
    perimeter: float

    circularity: float
    aspect_ratio: float
    eccentricity: float

    bbox_width: int
    bbox_height: int

    extent: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MorphologyAnalysisResult:
    object_count: int

    mean_area: float
    mean_circularity: float
    mean_aspect_ratio: float
    mean_eccentricity: float
    mean_extent: float

    size_variability: float
    shape_variability: float

    morphology_abnormality_score: float

    objects: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MorphologyAnalyzer:
    """Analyze morphological properties of instance masks."""

    def __init__(
        self,
        reference_area: Optional[float] = None,
        reference_circularity: float = 0.75,
    ):
        self.reference_area = reference_area
        self.reference_circularity = reference_circularity

    # ------------------------------------------------------------------
    # Individual object
    # ------------------------------------------------------------------

    @staticmethod
    def _analyze_object(
        mask: np.ndarray,
        object_id: int,
    ) -> MorphologyFeature:

        pixels = np.argwhere(
            mask == object_id
        )

        if len(pixels) == 0:
            raise ValueError(
                f"Object {object_id} does not exist."
            )

        y = pixels[:, 0]
        x = pixels[:, 1]

        area = float(len(pixels))

        min_x = int(x.min())
        max_x = int(x.max())

        min_y = int(y.min())
        max_y = int(y.max())

        width = max_x - min_x + 1
        height = max_y - min_y + 1

        # Bounding-box based perimeter approximation.
        perimeter = float(
            2 * (width + height)
        )

        circularity = float(
            4 * np.pi * area
            / (perimeter ** 2 + 1e-8)
        )

        long_axis = max(width, height)
        short_axis = min(width, height)

        aspect_ratio = float(
            long_axis
            / (short_axis + 1e-8)
        )

        eccentricity = float(
            np.sqrt(
                max(
                    0.0,
                    1.0
                    - (
                        short_axis
                        / (long_axis + 1e-8)
                    ) ** 2,
                )
            )
        )

        bbox_area = float(
            width * height
        )

        extent = float(
            area / (bbox_area + 1e-8)
        )

        return MorphologyFeature(
            object_id=int(object_id),
            area=area,
            perimeter=perimeter,
            circularity=circularity,
            aspect_ratio=aspect_ratio,
            eccentricity=eccentricity,
            bbox_width=width,
            bbox_height=height,
            extent=extent,
        )

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze(
        self,
        mask: np.ndarray,
    ) -> MorphologyAnalysisResult:

        mask = np.asarray(mask)

        if mask.ndim != 2:
            raise ValueError(
                "Mask must have shape (H, W)."
            )

        object_ids = np.unique(
            mask[mask > 0]
        )

        features = [
            self._analyze_object(
                mask,
                int(object_id),
            )
            for object_id in object_ids
        ]

        if not features:

            return MorphologyAnalysisResult(
                object_count=0,
                mean_area=0.0,
                mean_circularity=0.0,
                mean_aspect_ratio=0.0,
                mean_eccentricity=0.0,
                mean_extent=0.0,
                size_variability=0.0,
                shape_variability=0.0,
                morphology_abnormality_score=0.0,
                objects=[],
            )

        areas = np.asarray(
            [f.area for f in features],
            dtype=np.float32,
        )

        circularities = np.asarray(
            [f.circularity for f in features],
            dtype=np.float32,
        )

        aspect_ratios = np.asarray(
            [f.aspect_ratio for f in features],
            dtype=np.float32,
        )

        eccentricities = np.asarray(
            [f.eccentricity for f in features],
            dtype=np.float32,
        )

        extents = np.asarray(
            [f.extent for f in features],
            dtype=np.float32,
        )

        size_variability = float(
            np.std(areas)
            / (np.mean(areas) + 1e-8)
        )

        shape_variability = float(
            np.std(circularities)
        )

        # Simple research-oriented morphology score.
        circularity_deviation = abs(
            float(np.mean(circularities))
            - self.reference_circularity
        )

        if self.reference_area is not None:
            area_deviation = abs(
                float(np.mean(areas))
                - self.reference_area
            ) / (
                self.reference_area + 1e-8
            )
        else:
            area_deviation = size_variability

        morphology_score = float(
            np.clip(
                0.5 * circularity_deviation
                + 0.5 * area_deviation,
                0.0,
                1.0,
            )
        )

        return MorphologyAnalysisResult(
            object_count=len(features),
            mean_area=float(np.mean(areas)),
            mean_circularity=float(
                np.mean(circularities)
            ),
            mean_aspect_ratio=float(
                np.mean(aspect_ratios)
            ),
            mean_eccentricity=float(
                np.mean(eccentricities)
            ),
            mean_extent=float(
                np.mean(extents)
            ),
            size_variability=size_variability,
            shape_variability=shape_variability,
            morphology_abnormality_score=morphology_score,
            objects=[
                feature.to_dict()
                for feature in features
            ],
        )


def analyze_morphology(
    mask: np.ndarray,
) -> Dict[str, Any]:
    analyzer = MorphologyAnalyzer()

    return analyzer.analyze(mask).to_dict()


if __name__ == "__main__":
    print("Morphology Analysis")

    mask = np.zeros(
        (256, 256),
        dtype=np.int32,
    )

    mask[30:70, 30:80] = 1
    mask[100:150, 100:135] = 2
    mask[170:220, 40:70] = 3

    analyzer = MorphologyAnalyzer()

    result = analyzer.analyze(mask)

    print(
        f"Objects: {result.object_count}"
    )

    print(
        f"Mean area: "
        f"{result.mean_area:.2f}"
    )

    print(
        f"Mean circularity: "
        f"{result.mean_circularity:.4f}"
    )

    print(
        f"Mean aspect ratio: "
        f"{result.mean_aspect_ratio:.4f}"
    )

    print(
        f"Mean eccentricity: "
        f"{result.mean_eccentricity:.4f}"
    )

    print(
        f"Morphology abnormality: "
        f"{result.morphology_abnormality_score:.4f}"
    )

    print("\nMorphology analysis ready.")