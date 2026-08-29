from __future__ import annotations

"""Registry for reusable external biology models and datasets.

The registry contains metadata and integration contracts, not model weights.
Weights remain outside the repository and are loaded by the corresponding
adapter at runtime. This keeps testHP small and makes models replaceable.
"""

from dataclasses import dataclass, field
from typing import Literal

IntegrationKind = Literal["dataset", "image_model", "foundation_model", "knowledge_base"]


@dataclass(frozen=True)
class ModelSpec:
    id: str
    name: str
    kind: IntegrationKind
    capability: str
    source_url: str
    license_note: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    optional_dependency: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)


MODEL_REGISTRY: dict[str, ModelSpec] = {
    "hca": ModelSpec(
        "hca", "Human Cell Atlas", "dataset", "single-cell / spatial reference data",
        "https://data.humancellatlas.org/", "data access/terms vary by dataset",
        ("dataset query",), ("dataset metadata", "download locations"), tags=("reference", "single-cell", "spatial"),
    ),
    "cellxgene": ModelSpec(
        "cellxgene", "CZ CELLxGENE", "dataset", "single-cell reference data",
        "https://cellxgene.cziscience.com/", "data access/terms vary by collection",
        ("collection/dataset query",), ("dataset metadata", "download locations"), tags=("reference", "single-cell"),
    ),
    "cellpose-sam": ModelSpec(
        "cellpose-sam", "Cellpose-SAM", "image_model", "cell segmentation",
        "https://github.com/MouseLand/cellpose", "BSD-3-Clause (verify upstream release)",
        ("2D/3D microscopy",), ("cell masks",), optional_dependency="cellpose", tags=("segmentation", "microscopy"),
    ),
    "uni2": ModelSpec(
        "uni2", "UNI2", "foundation_model", "histopathology WSI embeddings",
        "https://github.com/mahmoodlab/UNI", "see upstream model/repository license and weights terms",
        ("WSI/tissue image",), ("embeddings",), tags=("pathology", "wsi", "foundation-model"),
    ),
    "scgpt": ModelSpec(
        "scgpt", "scGPT", "foundation_model", "single-cell representation",
        "https://github.com/bowang-lab/scGPT", "see upstream repository/model terms",
        ("single-cell expression",), ("cell embeddings", "cell annotations"), tags=("single-cell", "foundation-model"),
    ),
    "geneformer": ModelSpec(
        "geneformer", "Geneformer", "foundation_model", "single-cell representation",
        "https://github.com/jkobject/geneformer", "see upstream repository/model terms",
        ("single-cell expression",), ("cell embeddings", "transfer-learning outputs"), tags=("single-cell", "foundation-model"),
    ),
    "scgpt-spatial": ModelSpec(
        "scgpt-spatial", "scGPT-spatial", "foundation_model", "spatial omics representation",
        "https://github.com/bowang-lab/scGPT-spatial", "see upstream repository/model terms",
        ("spatial expression",), ("spatial embeddings", "cell/spot annotations"), tags=("spatial", "single-cell"),
    ),
    "arc-virtual-cell-atlas": ModelSpec(
        "arc-virtual-cell-atlas", "Arc Virtual Cell Atlas", "dataset", "perturbation/reference cell data",
        "https://arcinstitute.org/tools/virtualcellatlas", "CC0 for Atlas data; verify individual linked datasets",
        ("cell-state query",), ("reference/perturbation observations",), tags=("reference", "perturbation", "virtual-cell"),
    ),
    "u-segment3d": ModelSpec(
        "u-segment3d", "u-Segment3D", "image_model", "3D cellular representation/segmentation",
        "https://github.com/DanuserLab/u-Segment3D", "see upstream repository license",
        ("2D segmentation stack",), ("3D cell labels",), tags=("segmentation", "3d", "microscopy"),
    ),
    "alphafold-db": ModelSpec(
        "alphafold-db", "AlphaFold DB", "knowledge_base", "protein structure knowledge",
        "https://alphafold.ebi.ac.uk/", "see AlphaFold DB terms for individual data",
        ("protein/gene identifier",), ("predicted protein structure",), tags=("molecular", "protein"),
    ),
}


def get_model_spec(integration_id: str) -> ModelSpec:
    try:
        return MODEL_REGISTRY[integration_id]
    except KeyError as exc:
        raise KeyError(f"unknown scientific integration: {integration_id}") from exc
