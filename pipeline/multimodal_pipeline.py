# multimodal_pipeline.py

"""
Multimodal Pipeline

Integruje dane pochodzące z różnych modalności:

- images       -> zdjęcia skóry
- WSI          -> whole-slide images / histopatologia
- cells        -> segmentacja i cechy komórkowe
- RNA          -> ekspresja genów / transcriptomics
- hand         -> landmarks / embedding dłoni

Pipeline odpowiada za:
1. zebranie wyników poszczególnych pipeline'ów,
2. walidację danych,
3. normalizację reprezentacji,
4. obsługę brakujących modalności,
5. przygotowanie wspólnego słownika cech,
6. opcjonalne połączenie embeddingów.

Nie wykonuje właściwego uczenia modelu fusion.
Za uczenie odpowiada fusion_model.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class MultimodalConfig:
    """
    Configuration for multimodal integration.
    """

    # Expected embedding dimensions.
    image_dim: Optional[int] = None
    wsi_dim: Optional[int] = None
    cell_dim: Optional[int] = None
    rna_dim: Optional[int] = None
    hand_dim: Optional[int] = None

    # Target dimension for individual modality embeddings.
    target_dim: Optional[int] = None

    # Missing-modality behaviour.
    allow_missing: bool = True
    fill_missing_with_zero: bool = True

    # Numerical stability.
    eps: float = 1e-8

    # Whether to normalize embeddings before fusion.
    normalize_embeddings: bool = True

    # Whether to keep metadata.
    keep_metadata: bool = True


# ============================================================
# DATA CONTAINERS
# ============================================================

@dataclass
class ModalityOutput:
    """
    Generic representation of one modality.
    """

    name: str

    embedding: Optional[np.ndarray] = None

    features: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    available: bool = True

    quality_score: Optional[float] = None


@dataclass
class MultimodalSample:
    """
    Complete multimodal sample.

    A sample may contain any combination of modalities.
    """

    sample_id: str

    image: Optional[ModalityOutput] = None
    wsi: Optional[ModalityOutput] = None
    cells: Optional[ModalityOutput] = None
    rna: Optional[ModalityOutput] = None
    hand: Optional[ModalityOutput] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FusionInput:
    """
    Final structure passed toward fusion_model.py.
    """

    sample_id: str

    embeddings: Dict[str, Optional[np.ndarray]]

    concatenated_embedding: Optional[np.ndarray]

    availability: Dict[str, bool]

    quality: Dict[str, Optional[float]]

    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def _to_numpy(
    value: Optional[Any],
    dtype: np.dtype = np.float32,
) -> Optional[np.ndarray]:
    """
    Convert input to numpy array.
    """

    if value is None:
        return None

    if isinstance(value, np.ndarray):
        return value.astype(dtype, copy=False)

    try:
        return np.asarray(value, dtype=dtype)
    except Exception as exc:
        raise TypeError(
            f"Cannot convert value to numpy array: {exc}"
        ) from exc


def _flatten_embedding(
    embedding: np.ndarray,
) -> np.ndarray:
    """
    Convert arbitrary embedding shape to 1D vector.
    """

    embedding = _to_numpy(embedding)

    if embedding is None:
        raise ValueError("Embedding cannot be None.")

    return embedding.reshape(-1)


def _l2_normalize(
    embedding: np.ndarray,
    eps: float = 1e-8,
) -> np.ndarray:
    """
    L2-normalize an embedding.
    """

    embedding = _flatten_embedding(embedding)

    norm = np.linalg.norm(embedding)

    if norm < eps:
        return embedding

    return embedding / norm


def _pad_or_trim(
    embedding: np.ndarray,
    target_dim: int,
) -> np.ndarray:
    """
    Adjust embedding to target dimensionality.

    If embedding is shorter:
        zero padding.

    If embedding is longer:
        trimming.
    """

    embedding = _flatten_embedding(embedding)

    current_dim = embedding.shape[0]

    if current_dim == target_dim:
        return embedding

    if current_dim < target_dim:
        result = np.zeros(
            target_dim,
            dtype=np.float32,
        )

        result[:current_dim] = embedding

        return result

    return embedding[:target_dim]


# ============================================================
# MULTIMODAL PIPELINE
# ============================================================

class MultimodalPipeline:
    """
    Main multimodal integration pipeline.
    """

    MODALITIES = (
        "image",
        "wsi",
        "cells",
        "rna",
        "hand",
    )

    def __init__(
        self,
        config: Optional[MultimodalConfig] = None,
    ):
        self.config = config or MultimodalConfig()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    def validate_sample(
        self,
        sample: MultimodalSample,
    ) -> Dict[str, Any]:
        """
        Validate a multimodal sample.
        """

        if not sample.sample_id:
            raise ValueError("sample_id cannot be empty.")

        result = {
            "sample_id": sample.sample_id,
            "valid": True,
            "available_modalities": [],
            "missing_modalities": [],
            "errors": [],
        }

        for modality_name in self.MODALITIES:

            modality = getattr(
                sample,
                modality_name,
                None,
            )

            if modality is None:
                result["missing_modalities"].append(
                    modality_name
                )
                continue

            if not modality.available:
                result["missing_modalities"].append(
                    modality_name
                )
                continue

            result["available_modalities"].append(
                modality_name
            )

            if modality.embedding is not None:

                try:
                    embedding = _flatten_embedding(
                        modality.embedding
                    )

                    if not np.all(
                        np.isfinite(embedding)
                    ):
                        result["errors"].append(
                            f"{modality_name}: "
                            "embedding contains NaN/Inf."
                        )

                except Exception as exc:

                    result["errors"].append(
                        f"{modality_name}: "
                        f"invalid embedding: {exc}"
                    )

        if result["errors"]:
            result["valid"] = False

        if (
            not self.config.allow_missing
            and result["missing_modalities"]
        ):
            result["valid"] = False

        return result

    # --------------------------------------------------------
    # EMBEDDING PREPARATION
    # --------------------------------------------------------

    def prepare_embedding(
        self,
        modality: ModalityOutput,
        target_dim: Optional[int] = None,
    ) -> Optional[np.ndarray]:
        """
        Prepare one modality embedding.
        """

        if modality is None:
            return None

        if not modality.available:
            return None

        if modality.embedding is None:
            return None

        embedding = _flatten_embedding(
            modality.embedding
        )

        # Replace invalid values.
        embedding = np.nan_to_num(
            embedding,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        # Normalize.
        if self.config.normalize_embeddings:
            embedding = _l2_normalize(
                embedding,
                eps=self.config.eps,
            )

        # Optional dimensionality adjustment.
        if target_dim is not None:
            embedding = _pad_or_trim(
                embedding,
                target_dim,
            )

        return embedding.astype(
            np.float32,
            copy=False,
        )

    # --------------------------------------------------------
    # MODALITY-SPECIFIC PREPARATION
    # --------------------------------------------------------

    def prepare_image(
        self,
        modality: Optional[ModalityOutput],
    ) -> Optional[np.ndarray]:

        return self.prepare_embedding(
            modality,
            self.config.image_dim,
        )

    def prepare_wsi(
        self,
        modality: Optional[ModalityOutput],
    ) -> Optional[np.ndarray]:

        return self.prepare_embedding(
            modality,
            self.config.wsi_dim,
        )

    def prepare_cells(
        self,
        modality: Optional[ModalityOutput],
    ) -> Optional[np.ndarray]:

        return self.prepare_embedding(
            modality,
            self.config.cell_dim,
        )

    def prepare_rna(
        self,
        modality: Optional[ModalityOutput],
    ) -> Optional[np.ndarray]:

        return self.prepare_embedding(
            modality,
            self.config.rna_dim,
        )

    def prepare_hand(
        self,
        modality: Optional[ModalityOutput],
    ) -> Optional[np.ndarray]:

        return self.prepare_embedding(
            modality,
            self.config.hand_dim,
        )

    # --------------------------------------------------------
    # PROCESS SAMPLE
    # --------------------------------------------------------

    def process_sample(
        self,
        sample: MultimodalSample,
    ) -> FusionInput:
        """
        Convert a MultimodalSample into FusionInput.
        """

        validation = self.validate_sample(
            sample
        )

        if not validation["valid"]:
            raise ValueError(
                "Invalid multimodal sample: "
                f"{validation['errors']}"
            )

        embeddings = {
            "image": self.prepare_image(
                sample.image
            ),
            "wsi": self.prepare_wsi(
                sample.wsi
            ),
            "cells": self.prepare_cells(
                sample.cells
            ),
            "rna": self.prepare_rna(
                sample.rna
            ),
            "hand": self.prepare_hand(
                sample.hand
            ),
        }

        availability = {
            name: embedding is not None
            for name, embedding
            in embeddings.items()
        }

        quality = {
            name: (
                getattr(
                    getattr(
                        sample,
                        name,
                        None
                    ),
                    "quality_score",
                    None,
                )
                if getattr(
                    sample,
                    name,
                    None,
                ) is not None
                else None
            )
            for name in self.MODALITIES
        }

        concatenated = self.concatenate_embeddings(
            embeddings
        )

        metadata = {}

        if self.config.keep_metadata:

            metadata = dict(
                sample.metadata
            )

            metadata[
                "available_modalities"
            ] = validation[
                "available_modalities"
            ]

            metadata[
                "missing_modalities"
            ] = validation[
                "missing_modalities"
            ]

        return FusionInput(
            sample_id=sample.sample_id,
            embeddings=embeddings,
            concatenated_embedding=concatenated,
            availability=availability,
            quality=quality,
            metadata=metadata,
        )

    # --------------------------------------------------------
    # CONCATENATION
    # --------------------------------------------------------

    def concatenate_embeddings(
        self,
        embeddings: Dict[
            str,
            Optional[np.ndarray]
        ],
    ) -> Optional[np.ndarray]:
        """
        Concatenate available modality embeddings.
        """

        vectors: List[np.ndarray] = []

        for modality_name in self.MODALITIES:

            embedding = embeddings.get(
                modality_name
            )

            if embedding is None:

                if (
                    self.config.fill_missing_with_zero
                ):

                    expected_dim = (
                        self._get_expected_dim(
                            modality_name
                        )
                    )

                    if expected_dim is not None:

                        vectors.append(
                            np.zeros(
                                expected_dim,
                                dtype=np.float32,
                            )
                        )

                continue

            vectors.append(
                _flatten_embedding(
                    embedding
                )
            )

        if not vectors:
            return None

        return np.concatenate(
            vectors,
            axis=0,
        ).astype(
            np.float32,
            copy=False,
        )

    # --------------------------------------------------------
    # EXPECTED DIMENSIONS
    # --------------------------------------------------------

    def _get_expected_dim(
        self,
        modality_name: str,
    ) -> Optional[int]:

        mapping = {
            "image": self.config.image_dim,
            "wsi": self.config.wsi_dim,
            "cells": self.config.cell_dim,
            "rna": self.config.rna_dim,
            "hand": self.config.hand_dim,
        }

        return mapping.get(
            modality_name
        )

    # --------------------------------------------------------
    # BATCH PROCESSING
    # --------------------------------------------------------

    def process_batch(
        self,
        samples: Sequence[
            MultimodalSample
        ],
    ) -> List[FusionInput]:
        """
        Process multiple multimodal samples.
        """

        results = []

        for sample in samples:

            result = self.process_sample(
                sample
            )

            results.append(result)

        return results

    # --------------------------------------------------------
    # STACK EMBEDDINGS
    # --------------------------------------------------------

    def stack_modality(
        self,
        fusion_inputs: Sequence[FusionInput],
        modality_name: str,
    ) -> Optional[np.ndarray]:
        """
        Stack one modality across samples.

        Missing modalities are represented by zeros
        if their expected dimension is known.
        """

        if modality_name not in self.MODALITIES:
            raise ValueError(
                f"Unknown modality: {modality_name}"
            )

        vectors = []

        expected_dim = self._get_expected_dim(
            modality_name
        )

        for item in fusion_inputs:

            embedding = item.embeddings.get(
                modality_name
            )

            if embedding is None:

                if (
                    self.config.fill_missing_with_zero
                    and expected_dim is not None
                ):

                    embedding = np.zeros(
                        expected_dim,
                        dtype=np.float32,
                    )

                else:
                    continue

            vectors.append(
                _flatten_embedding(
                    embedding
                )
            )

        if not vectors:
            return None

        return np.stack(
            vectors,
            axis=0,
        )

    # --------------------------------------------------------
    # FUSION MATRIX
    # --------------------------------------------------------

    def build_fusion_matrix(
        self,
        fusion_inputs: Sequence[FusionInput],
    ) -> Optional[np.ndarray]:
        """
        Build a matrix:

            samples x multimodal_features
        """

        vectors = []

        for item in fusion_inputs:

            if (
                item.concatenated_embedding
                is None
            ):
                continue

            vectors.append(
                item.concatenated_embedding
            )

        if not vectors:
            return None

        dimensions = {
            vector.shape[0]
            for vector in vectors
        }

        if len(dimensions) != 1:
            raise ValueError(
                "Cannot build fusion matrix: "
                "embedding dimensions differ."
            )

        return np.stack(
            vectors,
            axis=0,
        )

    # --------------------------------------------------------
    # MODALITY WEIGHTS
    # --------------------------------------------------------

    def calculate_modality_weights(
        self,
        fusion_input: FusionInput,
    ) -> Dict[str, float]:
        """
        Calculate simple modality weights.

        Weight is based on:
        - availability
        - optional quality score

        This is NOT learned attention.
        """

        weights = {}

        available = [
            name
            for name in self.MODALITIES
            if fusion_input.availability.get(
                name,
                False,
            )
        ]

        if not available:
            return {
                name: 0.0
                for name in self.MODALITIES
            }

        raw_weights = {}

        for name in self.MODALITIES:

            if not fusion_input.availability.get(
                name,
                False,
            ):
                raw_weights[name] = 0.0
                continue

            quality = fusion_input.quality.get(
                name
            )

            if quality is None:
                quality = 1.0

            quality = float(
                np.clip(
                    quality,
                    0.0,
                    1.0,
                )
            )

            raw_weights[name] = quality

        total = sum(
            raw_weights.values()
        )

        if total <= self.config.eps:

            equal_weight = (
                1.0 / len(available)
            )

            for name in self.MODALITIES:

                weights[name] = (
                    equal_weight
                    if name in available
                    else 0.0
                )

            return weights

        for name in self.MODALITIES:

            weights[name] = (
                raw_weights[name]
                / total
            )

        return weights

    # --------------------------------------------------------
    # WEIGHTED FUSION
    # --------------------------------------------------------

    def weighted_fusion(
        self,
        fusion_input: FusionInput,
    ) -> Optional[np.ndarray]:
        """
        Create weighted concatenation.

        This is a preprocessing-level fusion operation.
        """

        embeddings = fusion_input.embeddings

        weights = self.calculate_modality_weights(
            fusion_input
        )

        vectors = []

        for name in self.MODALITIES:

            embedding = embeddings.get(
                name
            )

            if embedding is None:
                continue

            weight = weights.get(
                name,
                0.0,
            )

            vectors.append(
                embedding * weight
            )

        if not vectors:
            return None

        return np.concatenate(
            vectors,
            axis=0,
        ).astype(
            np.float32,
            copy=False,
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    def summarize(
        self,
        fusion_input: FusionInput,
    ) -> Dict[str, Any]:
        """
        Generate human-readable summary.
        """

        summary = {
            "sample_id": fusion_input.sample_id,
            "modalities": {},
            "total_embedding_dim": None,
        }

        for name in self.MODALITIES:

            embedding = (
                fusion_input.embeddings.get(
                    name
                )
            )

            if embedding is None:

                summary["modalities"][name] = {
                    "available": False,
                    "dimension": None,
                    "quality": fusion_input.quality.get(
                        name
                    ),
                }

            else:

                summary["modalities"][name] = {
                    "available": True,
                    "dimension": int(
                        embedding.shape[0]
                    ),
                    "quality": fusion_input.quality.get(
                        name
                    ),
                }

        if (
            fusion_input.concatenated_embedding
            is not None
        ):

            summary[
                "total_embedding_dim"
            ] = int(
                fusion_input
                .concatenated_embedding
                .shape[0]
            )

        return summary


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def create_modality_output(
    name: str,
    embedding: Optional[Any] = None,
    features: Optional[
        Dict[str, Any]
    ] = None,
    metadata: Optional[
        Dict[str, Any]
    ] = None,
    quality_score: Optional[float] = None,
    available: bool = True,
) -> ModalityOutput:
    """
    Convenience constructor.
    """

    return ModalityOutput(
        name=name,
        embedding=_to_numpy(
            embedding
        ),
        features=features or {},
        metadata=metadata or {},
        quality_score=quality_score,
        available=available,
    )


def create_multimodal_sample(
    sample_id: str,
    image: Optional[ModalityOutput] = None,
    wsi: Optional[ModalityOutput] = None,
    cells: Optional[ModalityOutput] = None,
    rna: Optional[ModalityOutput] = None,
    hand: Optional[ModalityOutput] = None,
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> MultimodalSample:
    """
    Convenience constructor for multimodal sample.
    """

    return MultimodalSample(
        sample_id=sample_id,
        image=image,
        wsi=wsi,
        cells=cells,
        rna=rna,
        hand=hand,
        metadata=metadata or {},
    )


# ============================================================
# DEMONSTRATION
# ============================================================

def demo() -> None:
    """
    Small demonstration showing how the pipeline works.
    """

    print("=" * 60)
    print("Multimodal Pipeline")
    print("=" * 60)

    config = MultimodalConfig(
        image_dim=768,
        wsi_dim=768,
        cell_dim=256,
        rna_dim=512,
        hand_dim=256,
        normalize_embeddings=True,
        allow_missing=True,
        fill_missing_with_zero=True,
    )

    pipeline = MultimodalPipeline(
        config=config
    )

    # --------------------------------------------------------
    # Simulated outputs from individual pipelines
    # --------------------------------------------------------

    image_output = create_modality_output(
        name="image",
        embedding=np.random.randn(768),
        quality_score=0.95,
    )

    wsi_output = create_modality_output(
        name="wsi",
        embedding=np.random.randn(768),
        quality_score=0.90,
    )

    cell_output = create_modality_output(
        name="cells",
        embedding=np.random.randn(256),
        quality_score=0.85,
    )

    rna_output = create_modality_output(
        name="rna",
        embedding=np.random.randn(512),
        quality_score=0.92,
    )

    # Hand data intentionally missing.
    hand_output = None

    sample = create_multimodal_sample(
        sample_id="demo_001",
        image=image_output,
        wsi=wsi_output,
        cells=cell_output,
        rna=rna_output,
        hand=hand_output,
        metadata={
            "source": "demo",
            "timepoint": "T0",
        },
    )

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    fusion_input = pipeline.process_sample(
        sample
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = pipeline.summarize(
        fusion_input
    )

    print("\nSample:")
    print(
        fusion_input.sample_id
    )

    print("\nModalities:")

    for name, info in summary[
        "modalities"
    ].items():

        print(
            f"  {name:>6}: "
            f"available={info['available']} "
            f"dim={info['dimension']} "
            f"quality={info['quality']}"
        )

    print(
        "\nConcatenated embedding:",
        None
        if fusion_input.concatenated_embedding
        is None
        else fusion_input
        .concatenated_embedding
        .shape,
    )

    weights = pipeline.calculate_modality_weights(
        fusion_input
    )

    print("\nModality weights:")

    for name, weight in weights.items():

        print(
            f"  {name:>6}: "
            f"{weight:.4f}"
        )

    weighted = pipeline.weighted_fusion(
        fusion_input
    )

    print(
        "\nWeighted fusion shape:",
        None
        if weighted is None
        else weighted.shape,
    )

    print("\nModel input prepared.")

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    demo()